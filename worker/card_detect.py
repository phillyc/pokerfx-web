#!/usr/bin/env python3
"""
card_detect.py — Detect hole cards from poker vlog clips and rename files.

v2: Full-clip scan with card region cropping and two-pass detection.

Downloads clips from S3, scans the full clip to find the card reveal moment,
crops to the card region, sends frames to a vision LLM for identification,
and uploads renamed copies to a labeled/ folder.

Usage:
    # Process all clips in an S3 folder
    python card_detect.py s3://vlog-nofacespoker/11.26.24/

    # Process specific clips by clip number
    python card_detect.py s3://vlog-nofacespoker/11.26.24/ --clips 160,165,169,171

    # Process a single local clip
    python card_detect.py /path/to/VID_20241126_151024_10_212.mp4

    # Dry run (detect cards but don't rename/upload)
    python card_detect.py s3://vlog-nofacespoker/11.26.24/ --dry-run

    # Use a specific model
    python card_detect.py s3://vlog-nofacespoker/11.26.24/ --model gpt-4o

Requires:
    - ffmpeg (for frame extraction)
    - anthropic or openai Python package (for vision API)
    - boto3 (for S3 access, only needed for S3 paths)
"""

import argparse
import base64
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# --- Pass 1: Full-clip scan (find the reveal) ---
SCAN_FPS = 2              # Low fps for presence scan across full clip
JPEG_QUALITY = 1          # ffmpeg quality (1=best, 31=worst)

# --- Pass 2: Detail extraction (read the cards) ---
DETAIL_FPS = 15           # High fps around the reveal moment
DETAIL_WINDOW_SEC = 4     # ±2 seconds around detected reveal
DETAIL_FRAMES_TO_SEND = 7 # Best frames to send for card identification

# --- Crop region ---
# Cards appear in the bottom half, middle third of the frame.
# On 1920x1088: crops to ~640x544
CROP_TOP_FRAC = 0.50      # Remove top 50% of frame
CROP_LEFT_FRAC = 0.33     # Remove left 33%
CROP_RIGHT_FRAC = 0.33    # Remove right 33%

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

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
and suits should appear roughly upright. The two cards are fanned open. Look for the RANK in the 
top-left corner of each card, displayed ABOVE the suit symbol.

CRITICAL RULES:
1. If you cannot CLEARLY see both the rank AND suit of a card, report it as "?" — do NOT guess.
2. It is far better to say UNKNOWN than to guess incorrectly.
3. For each card, rate your confidence: CERTAIN / LIKELY / UNSURE

COMMON MISREADS to avoid:
- 6 vs 9: a 9 has a stem going UP from the circle, a 6 has a stem going DOWN
- T (10) vs K: 10 shows "10" (two characters), K shows a single letter "K"  
- Q vs O: Q has a tail at the bottom
- J vs T: J has a hook at the bottom
- A vs 4: A has a pointed top, 4 has an angular cross

Use ranks: A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2
Use suits: h (hearts ♥), s (spades ♠), d (diamonds ♦), c (clubs ♣)

For each frame, report what you see and your confidence per card.
Then give a FINAL CONSENSUS answer.

Format the final answer EXACTLY as one of:
  CARDS: XxYy (e.g., CARDS: AsKh) — both cards identified with CERTAIN or LIKELY confidence
  CARDS: Xx?? (e.g., CARDS: As??) — only one card identified confidently  
  CARDS: UNCERTAIN — you can see cards but cannot confidently identify them
  CARDS: XX — no card faces visible in any frame"""


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

def parse_insta360_filename(filename: str) -> dict:
    """Parse an Insta360 filename into components.

    Handles both original (VID_20241126_132348_10_145.mp4) and
    already-labeled (20241126_132348_145_XxYy.mp4) formats.
    """
    stem = Path(filename).stem
    ext = Path(filename).suffix

    # Try original Insta360 format first
    pattern = r'^VID_(\d{8})_(\d{6})_(\d+)_(\d+)$'
    match = re.match(pattern, stem)
    if match:
        return {
            'date': match.group(1),
            'time': match.group(2),
            'lens': match.group(3),
            'clip_num': match.group(4),
            'ext': ext,
        }

    # Try already-labeled format
    pattern = r'^(\d{8})_(\d{6})_(\d+)_(.+)$'
    match = re.match(pattern, stem)
    if match:
        return {
            'date': match.group(1),
            'time': match.group(2),
            'lens': None,
            'clip_num': match.group(3),
            'ext': ext,
        }

    return None


def build_labeled_filename(parsed: dict, cards: str) -> str:
    """Build the renamed filename: 20241126_132348_145_KhTh.mp4"""
    return f"{parsed['date']}_{parsed['time']}_{parsed['clip_num']}_{cards}{parsed['ext']}"


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 60.0  # fallback assumption


def extract_frames_full_clip(video_path: str, output_dir: str, fps: float = SCAN_FPS) -> int:
    """Extract frames from the ENTIRE clip at a given fps.

    Returns the number of frames extracted.
    """
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', f'fps={fps}',
        '-q:v', str(JPEG_QUALITY),
        os.path.join(output_dir, 'frame_%04d.jpg'),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  ffmpeg warning: {result.stderr[-200:]}", file=sys.stderr)

    frames = glob.glob(os.path.join(output_dir, 'frame_*.jpg'))
    return len(frames)


def extract_frames_window(video_path: str, output_dir: str, start_sec: float, end_sec: float, fps: float = DETAIL_FPS) -> int:
    """Extract frames from a specific time window at high fps.

    Returns the number of frames extracted.
    """
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-vf', f'fps={fps}',
        '-q:v', str(JPEG_QUALITY),
        os.path.join(output_dir, 'detail_%04d.jpg'),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  ffmpeg warning: {result.stderr[-200:]}", file=sys.stderr)

    frames = glob.glob(os.path.join(output_dir, 'detail_*.jpg'))
    return len(frames)


def crop_frame(input_path: str, output_path: str, width: int, height: int) -> bool:
    """Crop a frame to the card region (bottom 50%, middle third).

    Returns True if successful.
    """
    crop_x = int(width * CROP_LEFT_FRAC)
    crop_y = int(height * CROP_TOP_FRAC)
    crop_w = int(width * (1 - CROP_LEFT_FRAC - CROP_RIGHT_FRAC))
    crop_h = int(height * (1 - CROP_TOP_FRAC))

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', f'crop={crop_w}:{crop_h}:{crop_x}:{crop_y}',
        '-q:v', '1',
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def crop_frames_in_dir(frame_dir: str, cropped_dir: str, video_path: str) -> int:
    """Crop all frames in a directory to the card region.

    Returns number of cropped frames.
    """
    os.makedirs(cropped_dir, exist_ok=True)

    # Get video dimensions
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0:s=x',
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        dims = result.stdout.strip().split('x')
        width, height = int(dims[0]), int(dims[1])
    except (ValueError, IndexError):
        width, height = 1920, 1088  # fallback

    frames = sorted(glob.glob(os.path.join(frame_dir, '*.jpg')))
    count = 0
    for frame_path in frames:
        fname = os.path.basename(frame_path)
        cropped_path = os.path.join(cropped_dir, f'crop_{fname}')
        if crop_frame(frame_path, cropped_path, width, height):
            count += 1

    return count


def batch_crop_with_ffmpeg(video_path: str, output_dir: str, start_sec: float, end_sec: float, fps: float) -> int:
    """Extract, crop, and rotate frames in a single ffmpeg pass.

    Extracts frames from the given time window, cropped to the card region,
    then rotated 90° clockwise (cards are held with top pointing left,
    so rotation puts rank/suit upright for better recognition).
    Returns number of frames extracted.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get video dimensions
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0:s=x',
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        dims = result.stdout.strip().split('x')
        width, height = int(dims[0]), int(dims[1])
    except (ValueError, IndexError):
        width, height = 1920, 1088

    crop_x = int(width * CROP_LEFT_FRAC)
    crop_y = int(height * CROP_TOP_FRAC)
    crop_w = int(width * (1 - CROP_LEFT_FRAC - CROP_RIGHT_FRAC))
    crop_h = int(height * (1 - CROP_TOP_FRAC))

    # Crop then rotate 90° clockwise (transpose=1)
    # Cards are held with top pointing left, so CW rotation puts ranks upright
    vf = f'fps={fps},crop={crop_w}:{crop_h}:{crop_x}:{crop_y},transpose=1'

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-vf', vf,
        '-q:v', str(JPEG_QUALITY),
        os.path.join(output_dir, 'frame_%04d.jpg'),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  ffmpeg warning: {result.stderr[-200:]}", file=sys.stderr)

    frames = glob.glob(os.path.join(output_dir, 'frame_*.jpg'))
    return len(frames)


# ---------------------------------------------------------------------------
# Vision API
# ---------------------------------------------------------------------------

def encode_image_base64(path: str) -> str:
    """Read an image file and return base64-encoded string."""
    with open(path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8')


def call_vision_anthropic(frame_paths: list[str], prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Send frames to Anthropic's vision API with a given prompt."""
    try:
        import anthropic
    except ImportError:
        print("Error: 'anthropic' package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()

    content = []
    for path in frame_paths:
        b64 = encode_image_base64(path)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64,
            }
        })

    content.append({"type": "text", "text": prompt})

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )

    return response.content[0].text


def call_vision_openai(frame_paths: list[str], prompt: str, model: str = "gpt-4o") -> str:
    """Send frames to OpenAI's vision API with a given prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: 'openai' package not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()

    content = []
    for path in frame_paths:
        b64 = encode_image_base64(path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}",
                "detail": "high",
            }
        })

    content.append({"type": "text", "text": prompt})

    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )

    return response.choices[0].message.content


def call_vision(frame_paths: list[str], prompt: str, provider: str = "anthropic", model: str = None) -> str:
    """Send frames to the configured vision API."""
    if provider == "anthropic":
        return call_vision_anthropic(frame_paths, prompt, model or "claude-sonnet-4-20250514")
    elif provider == "openai":
        return call_vision_openai(frame_paths, prompt, model or "gpt-4o")
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# Two-pass detection
# ---------------------------------------------------------------------------

def parse_reveal_frames(response: str) -> list[int]:
    """Parse REVEAL_FRAMES from the presence scan response.

    Returns list of 1-indexed frame numbers, or empty list if none found.
    """
    match = re.search(r'REVEAL_FRAMES:\s*(.+)', response)
    if not match:
        return []

    value = match.group(1).strip()
    if value.upper() == 'NONE':
        return []

    frames = []
    for part in value.split(','):
        part = part.strip()
        try:
            frames.append(int(part))
        except ValueError:
            continue

    return frames


def parse_cards_from_response(response: str) -> tuple[str, str]:
    """Extract card notation and confidence from the detection response.

    Returns (cards, confidence) tuple.
    Cards can be: 'AsKh', 'As??', 'UNCERTAIN', or 'XX'
    """
    pattern = r'CARDS:\s*(\S+)'
    match = re.search(pattern, response)
    if not match:
        return 'XX', 'none'

    cards = match.group(1).strip()

    if cards == 'XX':
        return 'XX', 'none'
    if cards == 'UNCERTAIN':
        return 'UNCERTAIN', 'uncertain'
    if '?' in cards:
        return cards, 'partial'

    # Check if it looks like valid card notation (2-6 chars, alphanumeric)
    if re.match(r'^[A-Za-z0-9]{2,6}$', cards):
        # Try to gauge confidence from the response text
        response_lower = response.lower()
        if 'certain' in response_lower and 'uncertain' not in response_lower:
            return cards, 'high'
        elif 'likely' in response_lower:
            return cards, 'medium'
        else:
            return cards, 'medium'

    return 'XX', 'none'


def pass1_find_reveal(video_path: str, work_dir: str, provider: str, model: str) -> list[float]:
    """Pass 1: Scan full clip at low fps to find card reveal timestamps.

    Returns list of timestamps (in seconds) where cards were detected.
    """
    scan_dir = os.path.join(work_dir, 'scan')
    duration = get_video_duration(video_path)

    print(f"  📹 Pass 1: Scanning full clip ({duration:.1f}s) at {SCAN_FPS}fps...")
    num_frames = batch_crop_with_ffmpeg(video_path, scan_dir, 0, duration, SCAN_FPS)
    print(f"  📹 Extracted {num_frames} cropped scan frames")

    if num_frames == 0:
        return []

    # Send frames in batches (max ~20 frames per API call to stay reasonable)
    all_frames = sorted(glob.glob(os.path.join(scan_dir, 'frame_*.jpg')))
    reveal_timestamps = []

    batch_size = 20
    for batch_start in range(0, len(all_frames), batch_size):
        batch = all_frames[batch_start:batch_start + batch_size]
        batch_offset = batch_start  # frame index offset for this batch

        print(f"  🔍 Scanning frames {batch_start + 1}-{batch_start + len(batch)} of {len(all_frames)}...")

        response = call_vision(batch, PRESENCE_PROMPT, provider, model)
        frame_nums = parse_reveal_frames(response)

        # Convert frame numbers (1-indexed within batch) to timestamps
        for fnum in frame_nums:
            # Frame number is 1-indexed within the batch
            global_frame_idx = batch_offset + fnum - 1
            timestamp = global_frame_idx / SCAN_FPS
            reveal_timestamps.append(timestamp)

    # Cleanup scan frames
    shutil.rmtree(scan_dir, ignore_errors=True)

    return reveal_timestamps


def cluster_timestamps(timestamps: list[float], max_gap: float = 5.0) -> list[list[float]]:
    """Group timestamps into clusters where consecutive values are within max_gap seconds.

    Returns clusters sorted by size (largest first).
    """
    if not timestamps:
        return []

    sorted_ts = sorted(timestamps)
    clusters = [[sorted_ts[0]]]

    for ts in sorted_ts[1:]:
        if ts - clusters[-1][-1] <= max_gap:
            clusters[-1].append(ts)
        else:
            clusters.append([ts])

    # Sort by cluster size (largest first), then by earliest timestamp
    clusters.sort(key=lambda c: (-len(c), c[0]))
    return clusters


def try_identify_at_timestamp(video_path: str, center_sec: float, work_dir: str, attempt: int, provider: str, model: str) -> tuple[str, str, str]:
    """Try to identify cards at a specific timestamp.

    Returns (cards, confidence, raw_response) tuple.
    """
    start_sec = max(0, center_sec - DETAIL_WINDOW_SEC / 2)
    end_sec = center_sec + DETAIL_WINDOW_SEC / 2

    detail_dir = os.path.join(work_dir, f'detail_{attempt}')
    print(f"  📹 Pass 2 (attempt {attempt}): Detail frames ({start_sec:.1f}s - {end_sec:.1f}s) at {DETAIL_FPS}fps...")
    num_frames = batch_crop_with_ffmpeg(video_path, detail_dir, start_sec, end_sec, DETAIL_FPS)
    print(f"  📹 Extracted {num_frames} cropped+rotated detail frames")

    if num_frames == 0:
        shutil.rmtree(detail_dir, ignore_errors=True)
        return 'XX', 'none', ''

    # Select evenly-spaced frames to send
    all_frames = sorted(glob.glob(os.path.join(detail_dir, 'frame_*.jpg')))
    if len(all_frames) <= DETAIL_FRAMES_TO_SEND:
        selected = all_frames
    else:
        step = len(all_frames) / DETAIL_FRAMES_TO_SEND
        indices = [int(i * step) for i in range(DETAIL_FRAMES_TO_SEND)]
        selected = [all_frames[i] for i in indices if i < len(all_frames)]

    print(f"  🔍 Identifying cards from {len(selected)} detail frames...")
    response = call_vision(selected, DETECTION_PROMPT, provider, model)
    cards, confidence = parse_cards_from_response(response)

    # Cleanup detail frames
    shutil.rmtree(detail_dir, ignore_errors=True)

    return cards, confidence, response


def pass2_identify_cards(video_path: str, reveal_timestamps: list[float], work_dir: str, provider: str, model: str) -> tuple[str, str, str]:
    """Pass 2: Extract high-quality cropped+rotated frames around reveal and identify cards.

    Clusters timestamps, then tries each cluster (largest first) until cards are identified.
    Returns (cards, confidence, raw_response) tuple.
    """
    if not reveal_timestamps:
        return 'XX', 'none', ''

    clusters = cluster_timestamps(reveal_timestamps)
    print(f"  📊 Found {len(clusters)} reveal cluster(s): {[f'{sum(c)/len(c):.1f}s ({len(c)} frames)' for c in clusters]}")

    # Try each cluster until we get a confident detection
    fallback_result = None
    for attempt, cluster in enumerate(clusters, 1):
        center = sum(cluster) / len(cluster)
        cards, confidence, response = try_identify_at_timestamp(
            video_path, center, work_dir, attempt, provider, model
        )

        if cards not in ('XX', 'UNCERTAIN') and '?' not in cards:
            print(f"  ✅ Got confident result from cluster {attempt}")
            return cards, confidence, response

        if cards == 'UNCERTAIN' or '?' in cards:
            print(f"  ⚠️  Uncertain result from cluster {attempt}, trying next...")
            if not fallback_result:
                fallback_result = (cards, confidence, response)
            continue

        print(f"  ❌ No detection from cluster {attempt}, trying next...")

    # If we had an uncertain result, return that rather than XX
    if fallback_result:
        return fallback_result

    return 'XX', 'none', ''


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

# (already defined above)


# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------

def s3_parse_path(s3_path: str) -> tuple[str, str]:
    """Parse s3://bucket/prefix into (bucket, prefix)."""
    path = s3_path.replace('s3://', '')
    parts = path.split('/', 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    return bucket, prefix


def s3_list_clips(s3_path: str) -> list[str]:
    """List .mp4 files in an S3 path."""
    bucket, prefix = s3_parse_path(s3_path)

    cmd = ['aws', 's3', 'ls', f's3://{bucket}/{prefix}']
    result = subprocess.run(cmd, capture_output=True, text=True)

    clips = []
    for line in result.stdout.strip().split('\n'):
        if line.strip() and line.strip().endswith('.mp4'):
            filename = line.strip().split()[-1]
            if filename.startswith('VID_'):
                clips.append(filename)

    return sorted(clips)


def s3_download(s3_path: str, local_path: str):
    """Download a file from S3."""
    cmd = ['aws', 's3', 'cp', s3_path, local_path]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def s3_upload(local_path: str, s3_path: str):
    """Upload a file to S3."""
    cmd = ['aws', 's3', 'cp', local_path, s3_path]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_clip(video_path: str, provider: str, model: str, work_dir: str) -> dict:
    """Process a single clip through the v2 two-pass detection pipeline.

    Returns a result dict.
    """
    filename = os.path.basename(video_path)
    parsed = parse_insta360_filename(filename)

    if not parsed:
        print(f"  ⚠️  Could not parse filename: {filename}")
        return {
            'original': filename,
            'cards': 'XX',
            'renamed': filename,
            'confidence': 'none',
            'error': 'unparseable filename',
        }

    # Pass 1: Find the reveal
    clip_work_dir = os.path.join(work_dir, Path(filename).stem)
    os.makedirs(clip_work_dir, exist_ok=True)

    reveal_timestamps = pass1_find_reveal(video_path, clip_work_dir, provider, model)

    if not reveal_timestamps:
        print(f"  ⚠️  No card reveal detected in any frame")
        renamed = build_labeled_filename(parsed, 'XX')
        shutil.rmtree(clip_work_dir, ignore_errors=True)
        return {
            'original': filename,
            'cards': 'XX',
            'renamed': renamed,
            'confidence': 'none',
            'reveal_timestamps': [],
        }

    print(f"  ✅ Card reveal found at {[f'{t:.1f}s' for t in reveal_timestamps]}")

    # Pass 2: Identify cards
    cards, confidence, raw_response = pass2_identify_cards(
        video_path, reveal_timestamps, clip_work_dir, provider, model
    )

    renamed = build_labeled_filename(parsed, cards)

    print(f"  🃏 Detected: {cards} (confidence: {confidence})")
    print(f"  📝 Renamed: {renamed}")

    # Cleanup
    shutil.rmtree(clip_work_dir, ignore_errors=True)

    return {
        'original': filename,
        'cards': cards,
        'renamed': renamed,
        'confidence': confidence,
        'reveal_timestamps': reveal_timestamps,
    }


def process_s3_folder(s3_path: str, provider: str, model: str, dry_run: bool = False, clip_filter: list[str] = None):
    """Process clips in an S3 folder."""
    bucket, prefix = s3_parse_path(s3_path)
    base_s3 = f"s3://{bucket}/{prefix}"

    if not base_s3.endswith('/'):
        base_s3 += '/'

    print(f"📂 Listing clips in {base_s3}")
    clips = s3_list_clips(base_s3)

    # Filter to specific clip numbers if requested
    if clip_filter:
        clips = [c for c in clips if any(f"_{num}." in c or c.endswith(f"_{num}") for num in clip_filter)]

    print(f"📂 Found {len(clips)} clips to process\n")

    results = []
    work_dir = tempfile.mkdtemp(prefix='pokerfx_')

    try:
        for i, clip in enumerate(clips, 1):
            print(f"{'='*60}")
            print(f"[{i}/{len(clips)}] {clip}")
            print(f"{'='*60}")

            # Download
            local_path = os.path.join(work_dir, clip)
            print(f"  ⬇️  Downloading from S3...")
            s3_download(f"{base_s3}{clip}", local_path)

            # Process
            result = process_clip(local_path, provider, model, work_dir)
            results.append(result)

            # Upload renamed copy to labeled/
            if not dry_run and result['cards'] not in ('XX', 'UNCERTAIN') and '?' not in result.get('cards', ''):
                labeled_s3 = f"{base_s3}labeled/{result['renamed']}"
                print(f"  ⬆️  Uploading to {labeled_s3}")
                s3_upload(local_path, labeled_s3)
            elif dry_run:
                print(f"  🏃 Dry run — skipping upload")
            elif result['confidence'] in ('uncertain', 'partial'):
                print(f"  ⚠️  Uncertain result — skipping upload (needs manual review)")
            else:
                print(f"  ⏭️  Skipping upload (no cards detected)")

            # Cleanup local clip
            os.remove(local_path)
            print()

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    # Print summary
    print_summary(results)

    # Save results
    results_path = os.path.join(os.path.dirname(__file__), 'detection_results.json')
    with open(results_path, 'w') as f:
        json.dump({
            'source': base_s3,
            'processed_at': datetime.utcnow().isoformat(),
            'provider': provider,
            'model': model or 'default',
            'version': 'v2',
            'clips': results,
        }, f, indent=2)
    print(f"\n💾 Results saved to {results_path}")

    return results


def process_local_file(video_path: str, provider: str, model: str, dry_run: bool = False):
    """Process a single local video file."""
    print(f"📂 Processing local file: {video_path}\n")

    work_dir = tempfile.mkdtemp(prefix='pokerfx_')
    try:
        result = process_clip(video_path, provider, model, work_dir)

        if not dry_run and result['cards'] not in ('XX', 'UNCERTAIN') and '?' not in result.get('cards', ''):
            new_path = os.path.join(os.path.dirname(video_path), result['renamed'])
            print(f"\n  📝 Would rename to: {new_path}")
            print(f"  ℹ️  Use --rename to actually rename the file")

        print_summary([result])
        return [result]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def print_summary(results: list[dict]):
    """Print a summary table of results."""
    print(f"\n{'='*70}")
    print("DETECTION RESULTS SUMMARY (v2)")
    print(f"{'='*70}")

    confident = [r for r in results if r['confidence'] in ('high', 'medium')]
    uncertain = [r for r in results if r['confidence'] in ('uncertain', 'partial')]
    failed = [r for r in results if r['confidence'] == 'none']

    print(f"Total clips: {len(results)}")
    print(f"Confident detections: {len(confident)}")
    print(f"Needs review: {len(uncertain)}")
    print(f"No detection: {len(failed)}")
    print()

    for r in results:
        if r['confidence'] in ('high', 'medium'):
            status = '✅'
        elif r['confidence'] in ('uncertain', 'partial'):
            status = '⚠️'
        else:
            status = '❌'

        timestamps = r.get('reveal_timestamps', [])
        ts_str = f" (reveal @ {timestamps[0]:.1f}s)" if timestamps else ""

        print(f"  {status} {r['original']}")
        print(f"     → {r['cards']} [{r['confidence']}]{ts_str}")

    if uncertain:
        print(f"\n⚠️  {len(uncertain)} clips need manual review (uncertain detection)")
    if failed:
        print(f"❌ {len(failed)} clips had no card detection (may be b-roll)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Detect hole cards from poker vlog clips (v2 — full-clip scan + crop)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s s3://vlog-nofacespoker/11.26.24/
  %(prog)s s3://vlog-nofacespoker/11.26.24/ --clips 160,165,169,171
  %(prog)s s3://vlog-nofacespoker/11.26.24/ --dry-run
  %(prog)s /path/to/clip.mp4
  %(prog)s s3://bucket/path/ --provider openai --model gpt-4o
        """,
    )
    parser.add_argument('input', help='S3 path (s3://bucket/prefix/) or local video file')
    parser.add_argument('--provider', choices=['anthropic', 'openai'], default='anthropic',
                        help='Vision API provider (default: anthropic)')
    parser.add_argument('--model', default=None,
                        help='Model to use (default: claude-sonnet-4-20250514 for anthropic, gpt-4o for openai)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Detect cards but do not upload/rename')
    parser.add_argument('--rename', action='store_true',
                        help='Actually rename local files (only for local processing)')
    parser.add_argument('--clips', default=None,
                        help='Comma-separated clip numbers to process (e.g., 160,165,169)')

    args = parser.parse_args()

    if not shutil.which('ffmpeg'):
        print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    clip_filter = args.clips.split(',') if args.clips else None

    if args.input.startswith('s3://'):
        process_s3_folder(args.input, args.provider, args.model, args.dry_run, clip_filter)
    else:
        if not os.path.isfile(args.input):
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        process_local_file(args.input, args.provider, args.model, args.dry_run)


if __name__ == '__main__':
    main()
