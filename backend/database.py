"""DynamoDB CRUD operations for PokerFX."""
import boto3
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.storage import get_presigned_thumbnail_url, thumbnail_key as storage_thumbnail_key

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "pokerfx")
table = dynamodb.Table(TABLE_NAME)


# ---- Video CRUD ----

def create_video(filename: str, s3_key: str) -> dict:
    video_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "video_id": video_id,
        "filename": filename,
        "status": "pending",
        "clip_count": 0,
        "detected_count": 0,
        "verified_count": 0,
        "created_at": now,
        "s3_key": s3_key,
        "batch_job_id": None,
    }
    table.put_item(Item=item)
    return item


def get_video(video_id: str) -> Optional[dict]:
    resp = table.get_item(Key={"video_id": video_id})
    return resp.get("Item")


def list_videos(limit: int = 50) -> list[dict]:
    resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], Limit=limit)
        items.extend(resp.get("Items", []))
    # Filter to only video items (not hand items)
    videos = [i for i in items if "clip_number" not in i]
    videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return videos[:limit]


def update_video_status(video_id: str, status: str) -> None:
    table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET #st = :s",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": status},
    )


def update_video_batch_job_id(video_id: str, batch_job_id: str) -> None:
    table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET #bjid = :bjid",
        ExpressionAttributeNames={"#bjid": "batch_job_id"},
        ExpressionAttributeValues={":bjid": batch_job_id},
    )


def update_video_counts(video_id: str, clip_count: int, detected_count: int) -> None:
    table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET clip_count = :c, detected_count = :d",
        ExpressionAttributeValues={":c": clip_count, ":d": detected_count},
    )


def increment_verified_count(video_id: str, delta: int = 1) -> None:
    table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET verified_count = verified_count + :d",
        ExpressionAttributeValues={":d": delta},
    )


# ---- DetectedHand CRUD ----

def create_hand(
    video_id: str,
    clip_number: int,
    cards: str,
    confidence: str,
    thumbnail_key: Optional[str] = None,
    frame_timestamp: Optional[float] = None,
) -> dict:
    hand_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "video_id": video_id,
        "hand_id": hand_id,
        "clip_number": clip_number,
        "cards": cards,
        "confidence": confidence,
        "status": "pending",
        "thumbnail_key": thumbnail_key,
        "frame_timestamp": frame_timestamp,
        "detected_at": now,
    }
    table.put_item(Item=item)
    return item


def get_hand(hand_id: str, video_id: str) -> Optional[dict]:
    resp = table.get_item(Key={"video_id": video_id, "hand_id": hand_id})
    return resp.get("Item")


def list_hands(video_id: str) -> list[dict]:
    resp = table.query(
        KeyConditionExpression="video_id = :vid",
        ExpressionAttributeValues={":vid": video_id},
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression="video_id = :vid",
            ExclusiveStartKey=resp["LastEvaluatedKey"],
            ExpressionAttributeValues={":vid": video_id},
        )
        items.extend(resp.get("Items", []))
    items.sort(key=lambda x: x.get("clip_number", 0))
    return items


def update_hand_status(hand_id: str, video_id: str, status: str) -> None:
    table.update_item(
        Key={"video_id": video_id, "hand_id": hand_id},
        UpdateExpression="SET #st = :s",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": status},
    )


def serialize_hand(item: dict) -> dict:
    """Add thumbnail URL and map keys to camelCase for API response."""
    video_id = item["video_id"]
    hand_id = item["hand_id"]
    thumb_key = item.get("thumbnail_key")
    thumb_url = get_presigned_thumbnail_url(thumb_key) if thumb_key else None
    return {
        "id": hand_id,
        "videoId": video_id,
        "clipNumber": item["clip_number"],
        "cards": item["cards"],
        "confidence": item["confidence"],
        "status": item["status"],
        "frameThumbnailUrl": thumb_url,
        "frameTimestamp": item.get("frame_timestamp"),
        "detectedAt": item["detected_at"],
    }


def serialize_video(item: dict) -> dict:
    return {
        "id": item["video_id"],
        "filename": item["filename"],
        "status": item["status"],
        "clipCount": item.get("clip_count", 0),
        "detectedCount": item.get("detected_count", 0),
        "verifiedCount": item.get("verified_count", 0),
        "createdAt": item["created_at"],
        "batchJobId": item.get("batch_job_id"),
    }
