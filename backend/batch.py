"""AWS Batch job submission for card detection."""
import boto3
import os

batch = boto3.client("batch", region_name=os.getenv("AWS_REGION", "us-east-1"))
JOB_QUEUE = os.getenv("BATCH_JOB_QUEUE", "pokerfx-queue")
JOB_DEFINITION = os.getenv("BATCH_JOB_DEFINITION", "pokerfx-card-detect:1")


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
