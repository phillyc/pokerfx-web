from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class HandConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class HandStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ---- Request bodies ----

class HandStatusUpdate(BaseModel):
    status: HandStatus


# ---- Response models ----

class VideoResponse(BaseModel):
    id: str
    filename: str
    status: VideoStatus
    clipCount: int = 0
    detectedCount: int = 0
    verifiedCount: int = 0
    createdAt: str

    class Config:
        from_attributes = True


class DetectedHandResponse(BaseModel):
    id: str
    videoId: str
    clipNumber: int
    cards: str
    confidence: HandConfidence
    status: HandStatus
    frameThumbnailUrl: Optional[str] = None
    frameTimestamp: Optional[float] = None  # seconds into video
    detectedAt: str

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    videoId: str


class ProcessResponse(BaseModel):
    message: str
    jobId: Optional[str] = None
