#!/usr/bin/env python3
"""
AWS Batch worker for PokerFX card detection.

Receives: VIDEO_ID, S3_KEY, DYNAMODB_TABLE, AWS_REGION
Downloads video from S3 → runs card_detect → uploads thumbnails → writes to DynamoDB.
"""
import os
import sys
import tempfile
import boto3
import json
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))

import card_detect_worker as card_detect

# ── S3 helpers (self-contained — no backend/storage.py dependency) ──────────
S3_BUCKET = os.getenv("S3_BUCKET", "pokerfx-uploads")


def thumbnail_key(video_id: str, hand_id: str) -> str:
    return f"thumbnails/{video_id}/{hand_id}.jpg"


def log(msg: str):
    print(msg, flush=True)


def download_video(s3_key: str, dest: Path) -> Path:
    s3 = boto3.client("s3")
    s3.download_file(S3_BUCKET, s3_key, str(dest))
    return dest


def upload_thumbnail(frame_jpg: Path, video_id: str, hand_id: str) -> str:
    s3 = boto3.client("s3")
    key = thumbnail_key(video_id, hand_id)
    s3.upload_file(str(frame_jpg), S3_BUCKET, key, ExtraArgs={"ContentType": "image/jpeg"})
    return key


def main():
    video_id = os.environ["VIDEO_ID"]
    s3_key = os.environ["S3_KEY"]
    table_name = os.environ["DYNAMODB_TABLE"]
    region = os.environ.get("AWS_REGION", "us-east-1")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    log(f"[Worker] Starting job for video {video_id}")
    log(f"[Worker] S3 key: {s3_key}")

    # Update status → processing
    table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET #st = :s",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": "processing"},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        video_path = download_video(s3_key, tmpdir / "input.mp4")

        try:
            # Run detection
            log("[Worker] Running card_detect...")
            results = card_detect.detect(str(video_path), video_id)

            log(f"[Worker] Detected {len(results)} hand(s)")

            clip_count = len(results)
            detected_count = 0

            for result in results:
                cards = result.get("cards", "??")
                confidence = result.get("confidence", "none")
                frame_path = result.get("frame_path")
                frame_timestamp = result.get("timestamp")

                import uuid
                hand_id = str(uuid.uuid4())
                thumb_key = None

                if frame_path and Path(frame_path).exists():
                    thumb_key = upload_thumbnail(Path(frame_path), video_id, hand_id)

                # Write to DynamoDB
                table.put_item(Item={
                    "video_id": video_id,
                    "hand_id": hand_id,
                    "clip_number": result.get("clip_number", 1),
                    "cards": cards,
                    "confidence": confidence,
                    "status": "pending",
                    "thumbnail_key": thumb_key,
                    "frame_timestamp": frame_timestamp,
                    "detected_at": result.get("detected_at", ""),
                })
                detected_count += 1

            # Update video counts
            table.update_item(
                Key={"video_id": video_id},
                UpdateExpression="SET clip_count = :c, detected_count = :d, #st = :done",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":c": clip_count,
                    ":d": detected_count,
                    ":done": "done",
                },
            )
            log(f"[Worker] Done. {detected_count} hands written to DynamoDB.")

        except Exception as e:
            log(f"[Worker] ERROR: {e}")
            table.update_item(
                Key={"video_id": video_id},
                UpdateExpression="SET #st = :s",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":s": "error"},
            )
            raise


if __name__ == "__main__":
    main()
