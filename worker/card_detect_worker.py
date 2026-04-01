"""
Simplified card detection for AWS Batch workers.

Wraps the core detection logic from card_detect.py for programmatic use.
Called by worker.py with a local video path and returns structured results.
"""
import os
import sys
import re
import glob
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

SCAN_FPS = 2
DETAIL_FPS = 15
DETAIL_WINDOW_SEC = 4
DETAIL_FRAMES_TO_SEND = 7
JPEG_QUALITY = 1

CROP_TOP_FRAC = 0.50
CROP_LEFT_FRAC = 0.33
CROP_RIGHT_FRAC = 0.33

VISION_PROVIDER = os.getenv("VISION_PROVIDER", "anthropic")
VISION_MODEL = os.getenv("VISION_MODEL", None)  # defaults in call_vision


# ── Detection prompt ─────────────────────────────────────────────────────────

PRESENCE_PROMPT = """You are scanning frames from a poker vlog to find which frames show playing card faces.
The frames are numbered sequentially. The player occasionally holds two hole cards up toward a chest-mounted camera.

For each frame, briefly state whether card faces are visible or not.
Then provide your answer as: REVEAL_FRAMES: 5, 8, 12
(comma-separated frame numbers where card faces are clearly visible)

If NO frames show card faces, respond with: REVEAL_FRAMES: NONE

Only count frames where you can actually see the front face of at least one playing card (rank and suit visible).
Do NOT count frames showing card backs, chips, the table, or hands without visible card faces."""

DETECTION_PROMPT = """You are analyzing cropped and rotated frames from a poker vlog to identify two hole cards.
These frames have been cropped to the card region and rotated 90° clockwise so that card ranks
and suits should appear roughly upright. The two cards are fanned open.

CRITICAL RULES:
1. If you cannot CLEARLY see both the rank AND suit of a card, report it as "?" — do NOT guess.
2. It is far better to say UNKNOWN than to guess incorrectly.
3. For each card, rate your confidence: CERTAIN / LIKELY / UNSURE

Use ranks: A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2
Use suits: h (hearts), s (spades), d (diamonds), c (clubs)

Format the final answer EXACTLY as one of:
  CARDS: XxYy (e.g., CARDS: AsKh) — both cards identified with CERTAIN or LIKELY confidence
  CARDS: Xx?? (e.g., CARDS: As??) — only one card identified confidently
  CARDS: UNCERTAIN — you can see cards but cannot confidently identify them
  CARDS: XX — no card faces visible in any frame"""


# ── Frame extraction ─────────────────────────────────────────────────────────

def get_video_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
           "default=noprint_wrappers=1:nokey=1", path]
    try:
        return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
    except Exception:
        return 60.0


def batch_crop_with_ffmpeg(video_path: str, output_dir: str, start: float, end: float,
                           fps: float, rotate: bool = True) -> list[Path]:
    os.makedirs(output_dir, exist_ok=True)

    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
           "stream=width,height", "-of", "csv=p=0:s=x", video_path]
    try:
        w, h = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split("x")
        width, height = int(w), int(h)
    except Exception:
        width, height = 1920, 1088

    crop_x = int(width * CROP_LEFT_FRAC)
    crop_y = int(height * CROP_TOP_FRAC)
    crop_w = int(width * (1 - CROP_LEFT_FRAC - CROP_RIGHT_FRAC))
    crop_h = int(height * (1 - CROP_TOP_FRAC))

    vf = f"fps={fps},crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
    if rotate:
        vf += ",transpose=1"  # 90° CW

    out_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", str(start), "-to", str(end),
           "-vf", vf, "-q:v", str(JPEG_QUALITY), out_pattern]
    subprocess.run(cmd, capture_output=True)

    return sorted(Path(output_dir).glob("frame_*.jpg"))


def encode_image_base64(path: Path) -> str:
    import base64
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def call_vision_anthropic(frame_paths: list[Path], prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encode_image_base64(p)}}
        for p in frame_paths
    ]
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(
        model=VISION_MODEL or "claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text


def call_vision_openai(frame_paths: list[Path], prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_base64(p)}", "detail": "high"}}
        for p in frame_paths
    ]
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model=VISION_MODEL or "gpt-4o",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    return resp.choices[0].message.content


def call_vision(frame_paths: list[Path], prompt: str) -> str:
    if VISION_PROVIDER == "openai":
        return call_vision_openai(frame_paths, prompt)
    return call_vision_anthropic(frame_paths, prompt)


# ── Response parsing ──────────────────────────────────────────────────────────

def parse_reveal_frames(response: str) -> list[int]:
    match = re.search(r"REVEAL_FRAMES:\s*(.+)", response, re.IGNORECASE)
    if not match:
        return []
    val = match.group(1).strip()
    if val.upper() == "NONE":
        return []
    return [int(x.strip()) for x in val.split(",") if x.strip().isdigit()]


def parse_cards(response: str) -> tuple[str, str]:
    """Returns (cards, confidence)."""
    match = re.search(r"CARDS:\s*(\S+)", response, re.IGNORECASE)
    if not match:
        return "XX", "none"
    cards = match.group(1).strip()
    if cards == "XX":
        return "XX", "none"
    if cards == "UNCERTAIN":
        return "UNCERTAIN", "uncertain"
    if "?" in cards:
        return cards, "partial"

    resp_lower = response.lower()
    if "certain" in resp_lower and "unsure" not in resp_lower:
        return cards, "high"
    if "likely" in resp_lower:
        return cards, "medium"
    if "unsure" in resp_lower:
        return cards, "low"
    return cards, "medium"


# ── Main detection ────────────────────────────────────────────────────────────

def detect(video_path: str, video_id: str) -> list[dict]:
    """
    Run card detection on a local video file.

    Returns a list of dicts, one per detected hand:
      {
        "clip_number": 1,
        "cards": "AsKh",
        "confidence": "high",
        "frame_path": "/tmp/.../frame_0012.jpg",
        "timestamp": 8.5,
        "detected_at": "2026-04-01T...",
      }
    """
    work_dir = tempfile.mkdtemp(prefix="pokerfx_worker_")
    try:
        duration = get_video_duration(video_path)

        # ── Pass 1: Presence scan ──────────────────────────────────────────
        scan_dir = os.path.join(work_dir, "scan")
        scan_frames = batch_crop_with_ffmpeg(video_path, scan_dir, 0, duration, SCAN_FPS, rotate=False)

        if not scan_frames:
            return []

        # Batch scan in groups of 20
        presence_frames = []
        for i in range(0, len(scan_frames), 20):
            batch_frames = scan_frames[i:i + 20]
            resp = call_vision(batch_frames, PRESENCE_PROMPT)
            revealed = parse_reveal_frames(resp)
            presence_frames.extend(revealed)

        if not presence_frames:
            return []

        # Convert frame indices back to timestamps
        fps = SCAN_FPS
        timestamps = [idx / fps for idx in presence_frames]

        # ── Pass 2: Detail extraction + card ID ─────────────────────────────
        # Use midpoint of detected frames
        mid_t = timestamps[len(timestamps) // 2]
        start = max(0, mid_t - DETAIL_WINDOW_SEC / 2)
        end = min(duration, mid_t + DETAIL_WINDOW_SEC / 2)

        detail_dir = os.path.join(work_dir, "detail")
        detail_frames = batch_crop_with_ffmpeg(video_path, detail_dir, start, end, DETAIL_FPS, rotate=True)

        if not detail_frames:
            return []

        # Take evenly spaced frames
        step = max(1, len(detail_frames) // DETAIL_FRAMES_TO_SEND)
        selected = detail_frames[::step][:DETAIL_FRAMES_TO_SEND]

        resp = call_vision(selected, DETECTION_PROMPT)
        cards, confidence = parse_cards(resp)

        # Pick best frame as thumbnail (middle frame often clearest)
        best_frame = selected[len(selected) // 2] if selected else None

        return [{
            "clip_number": 1,
            "cards": cards,
            "confidence": confidence,
            "frame_path": str(best_frame) if best_frame else None,
            "timestamp": mid_t,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }]

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
