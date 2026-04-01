import os
import zipfile
import io
import boto3
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, UploadFile, File, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend import storage, database, batch
from backend.schemas import (
    VideoResponse,
    UploadResponse,
    ProcessResponse,
    HandStatusUpdate,
    DetectedHandResponse,
)

app = FastAPI(title="PokerFX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
BUCKET = os.getenv("S3_BUCKET", "pokerfx-uploads")
TABLE = os.getenv("DYNAMODB_TABLE", "pokerfx")


# ---- Health ----

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---- Videos ----

@app.get("/api/videos", response_model=list[VideoResponse])
def list_videos():
    """List all uploaded videos, newest first."""
    videos = database.list_videos()
    return [database.serialize_video(v) for v in videos]


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
