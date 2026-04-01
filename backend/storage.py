"""S3 storage helpers for PokerFX."""
import boto3
import os
from typing import Optional

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
BUCKET = os.getenv("S3_BUCKET", "pokerfx-uploads")

# Keys follow: uploads/{video_id}/{filename}
# thumbnails/: {video_id}/{hand_id}.jpg


def get_presigned_upload_url(video_id: str, filename: str, content_type: str, expires: int = 3600) -> str:
    key = f"uploads/{video_id}/{filename}"
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def get_presigned_thumbnail_url(thumbnail_key: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": thumbnail_key},
        ExpiresIn=expires,
    )


def get_video_url(video_id: str, filename: str, expires: int = 3600) -> str:
    key = f"uploads/{video_id}/{filename}"
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def thumbnail_key(video_id: str, hand_id: str) -> str:
    return f"thumbnails/{video_id}/{hand_id}.jpg"


def video_key(video_id: str, filename: str) -> str:
    return f"uploads/{video_id}/{filename}"
