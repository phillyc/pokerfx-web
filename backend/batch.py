"""AWS Batch job submission and status polling for card detection."""
import boto3
import os

batch = boto3.client("batch", region_name=os.getenv("AWS_REGION", "us-east-1"))
JOB_QUEUE = os.getenv("BATCH_JOB_QUEUE", "pokerfx-queue")
JOB_DEFINITION = os.getenv("BATCH_JOB_DEFINITION", "pokerfx-card-detect:1")


STATUS_MAP = {
    # Transient states — video is still "processing"
    "SUBMITTED": "processing",
    "PENDING": "processing",
    "RUNNABLE": "processing",
    "STARTING": "processing",
    "RUNNING": "processing",
    # Terminal states
    "SUCCEEDED": "done",
    "FAILED": "error",
}


def submit_detection_job(video_id: str, s3_key: str, dynamodb_table: str) -> str:
    """Submit a card detection job to AWS Batch. Returns the job ID."""
    job_name = f"pokerfx-{video_id[:8]}"
    response = batch.submit_job(
        jobName=job_name,
        jobQueue=JOB_QUEUE,
        jobDefinition=JOB_DEFINITION,
        containerOverrides={
            "environment": [
                {"name": "VIDEO_ID", "value": video_id},
                {"name": "S3_KEY", "value": s3_key},
                {"name": "DYNAMODB_TABLE", "value": dynamodb_table},
                {"name": "AWS_REGION", "value": os.getenv("AWS_REGION", "us-east-1")},
            ],
        },
    )
    return response["jobId"]


def get_job_status(job_id: str) -> dict:
    """Poll AWS Batch for a job's current status.

    Returns:
        {
            "batch_status": "RUNNING" | "SUCCEEDED" | "FAILED" | ...,
            "video_status": "processing" | "done" | "error",
            "status_code": 200 | 404 | 500,
            "reason": str | None,  # failure reason if applicable
        }
    """
    try:
        response = batch.describe_jobs(jobs=[job_id])
    except Exception as e:
        return {
            "batch_status": "UNKNOWN",
            "video_status": "error",
            "status_code": 500,
            "reason": str(e),
        }

    jobs = response.get("jobs", [])
    if not jobs:
        return {
            "batch_status": "UNKNOWN",
            "video_status": "error",
            "status_code": 404,
            "reason": f"Batch job {job_id} not found",
        }

    job = jobs[0]
    batch_status = job.get("status", "UNKNOWN")
    video_status = STATUS_MAP.get(batch_status, "error")

    reason = None
    if batch_status == "FAILED":
        attempts = job.get("attempts", [])
        if attempts:
            reason = attempts[-1].get("statusReason", "Unknown failure")
        else:
            reason = job.get("statusReason", "Unknown failure")

    return {
        "batch_status": batch_status,
        "video_status": video_status,
        "status_code": 200,
        "reason": reason,
    }
