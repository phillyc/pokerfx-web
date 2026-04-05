import os
import time
import zipfile
import io
import boto3
import threading
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, UploadFile, File, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse

from backend import storage, database, batch
from backend.schemas import (
    VideoResponse,
    UploadResponse,
    ProcessResponse,
    HandStatusUpdate,
    DetectedHandResponse,
)

app = FastAPI(title="PokerFX API", version="1.0.0")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://pokerfx.net,https://www.pokerfx.net",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
BUCKET = os.getenv("S3_BUCKET", "pokerfx-uploads")
TABLE = os.getenv("DYNAMODB_TABLE", "pokerfx")

# In-memory cache for Batch polling to avoid rate-limiting the AWS API.
# Key: video_id, Value: {"batch_status": ..., "video_status": ..., "timestamp": ...,
#                          "reason": ...}
_batch_poll_cache: dict = {}
_batch_poll_lock = threading.Lock()
BATCH_POLL_CACHE_TTL = 10  # seconds — don't poll the same video more often than this


def _maybe_poll_batch(video: dict) -> dict:
    """If the video is processing, check AWS Batch for the real job status.

    Returns an updated video dict (only the status field may change).
    Results are cached for BATCH_POLL_CACHE_TTL seconds.
    """
    video_id = video["video_id"]
    if video["status"] != "processing":
        return video

    # If we have no batch_job_id yet, there's nothing to poll
    batch_job_id = video.get("batch_job_id")
    if not batch_job_id:
        return video

    # Check cache
    with _batch_poll_lock:
        cached = _batch_poll_cache.get(video_id)
        if cached and (time.time() - cached["timestamp"]) < BATCH_POLL_CACHE_TTL:
            if cached["video_status"] != video["status"]:
                video = {**video, "status": cached["video_status"]}
                database.update_video_status(video_id, cached["video_status"])
            return video

    # Poll AWS Batch
    result = batch.get_job_status(batch_job_id)

    # Don't update on transient API errors (status_code 500)
    if result["status_code"] == 500:
        return video

    # If the DB status changed, update it
    if result["video_status"] != video["status"]:
        with _batch_poll_lock:
            _batch_poll_cache[video_id] = {
                "batch_status": result["batch_status"],
                "video_status": result["video_status"],
                "timestamp": time.time(),
                "reason": result.get("reason"),
            }
        # Update DynamoDB so future reads without the cache get the right status
        database.update_video_status(video_id, result["video_status"])
        if result.get("reason") and result["batch_status"] == "FAILED":
            # Log failure reason (could be expanded to store in DB later)
            print(f"Batch job {batch_job_id} failed: {result['reason']}")
        video = {**video, "status": result["video_status"]}

    return video


# ---- Health ----

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---- Videos ----

@app.get("/api/videos", response_model=list[VideoResponse])
def list_videos():
    """List all uploaded videos, newest first."""
    videos = database.list_videos()
    return [database.serialize_video(_maybe_poll_batch(v)) for v in videos]


@app.post("/api/videos/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file. Returns the video ID."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")

    import uuid
    video_id = str(uuid.uuid4())
    s3_key = f"uploads/{video_id}/{file.filename}"

    # Upload directly to S3
    try:
        content = await file.read()
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=content, ContentType=file.content_type)
    except Exception as e:
        raise HTTPException(500, f"Failed to upload to S3: {e}")

    # Create DB record
    database.create_video(filename=file.filename, s3_key=s3_key)

    return UploadResponse(videoId=video_id)


@app.get("/api/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: str = Path(...)):
    video = database.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Poll AWS Batch if the job is still processing
    video = _maybe_poll_batch(video)
    return database.serialize_video(video)


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: str = Path(...)):
    video = database.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    # Delete from S3
    try:
        s3.delete_object(Bucket=BUCKET, Key=video["s3_key"])
    except Exception:
        pass  # best effort

    # Delete hands
    hands = database.list_hands(video_id)
    for hand in hands:
        if hand.get("thumbnail_key"):
            try:
                s3.delete_object(Bucket=BUCKET, Key=hand["thumbnail_key"])
            except Exception:
                pass

    # Delete DB record (hands are deleted via cascade in dynamodb or manually)
    table = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1")).Table(TABLE)
    hands = database.list_hands(video_id)
    with table.batch_writer() as batch_writer:
        for hand in hands:
            batch_writer.delete_item(Key={"video_id": video_id, "hand_id": hand["hand_id"]})
    table.delete_item(Key={"video_id": video_id})

    return {"deleted": video_id}


# ---- Processing ----

@app.post("/api/videos/{video_id}/process", response_model=ProcessResponse)
def process_video(video_id: str = Path(...)):
    """Queue a video for card detection via AWS Batch."""
    video = database.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    if video["status"] not in ("pending", "error"):
        raise HTTPException(400, f"Video is already {video['status']}")

    database.update_video_status(video_id, "processing")

    try:
        job_id = batch.submit_detection_job(video_id, video["s3_key"], TABLE)
        # Store the job ID so GET can poll it later
        database.update_video_batch_job_id(video_id, job_id)
    except Exception as e:
        database.update_video_status(video_id, "error")
        raise HTTPException(500, f"Failed to submit Batch job: {e}")

    return ProcessResponse(message="Processing queued", jobId=job_id)


# ---- Hands ----

@app.get("/api/hands/{video_id}", response_model=list[DetectedHandResponse])
def list_hands(video_id: str = Path(...)):
    """List all detected hands for a video."""
    video = database.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    hands = database.list_hands(video_id)
    return [database.serialize_hand(h) for h in hands]


@app.patch("/api/hands/{hand_id}", response_model=DetectedHandResponse)
def update_hand(
    hand_id: str,
    body: HandStatusUpdate,
    video_id: str = Path(...),
):
    """Update hand status (accept/reject)."""
    hand = database.get_hand(hand_id, video_id)
    if not hand:
        raise HTTPException(404, "Hand not found")

    old_status = hand["status"]
    database.update_hand_status(hand_id, video_id, body.status.value)

    # Update verified count on video
    if old_status != body.status.value:
        delta = 1 if body.status.value in ("accepted", "rejected") else -1
        if delta != 0:
            database.increment_verified_count(video_id, delta)

    updated = database.get_hand(hand_id, video_id)
    return database.serialize_hand(updated)


# ---- Export ----

@app.get("/api/videos/{video_id}/export")
def export_video(video_id: str = Path(...)):
    """
    Export verified + renamed video files as a ZIP.
    Only includes hands marked as 'accepted'.
    """
    video = database.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    hands = database.list_hands(video_id)
    accepted = [h for h in hands if h["status"] == "accepted"]

    if not accepted:
        raise HTTPException(400, "No accepted hands to export")

    # Generate ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for hand in accepted:
            # Download original video from S3
            try:
                video_obj = s3.get_object(Bucket=BUCKET, Key=video["s3_key"])["Body"].read()
            except Exception as e:
                continue  # skip if S3 read fails

            original_ext = os.path.splitext(video["filename"])[1]
            new_filename = f"{hand['cards']}{original_ext}"
            zf.writestr(new_filename, video_obj)

    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{video_id}_verified.zip"'},
    )


# ---- Frontend SPA (mounts last, after all /api routes) ----

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    # Serve index.html for root path
    @app.get("/")
    def frontend_root():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    # Serve static assets (JS, CSS, images) and SPA fallback for client-side routing
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        from pathlib import Path

        file_path = Path(FRONTEND_DIST) / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # SPA fallback — any non-file path serves index.html
        return FileResponse(str(Path(FRONTEND_DIST) / "index.html"))
