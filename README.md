# PokerFX Web — Infrastructure Guide

## Architecture Overview

```
Phil's Browser
    │
    │ HTTPS
    ▼
Next.js (Vercel or Railway)
    │  ← frontend pokerfx-web
    │
    │ /api/* proxy or direct
    ▼
FastAPI (Railway/Render)
    │
    ├─► S3 (video + thumbnails)
    ├─► DynamoDB (videos + hands)
    └─► AWS Batch (card detection jobs)
```

## AWS Resources Needed

### S3
- **Bucket**: `pokerfx-uploads` (or configurable via `S3_BUCKET`)
  - `uploads/{video_id}/{filename}` — original videos
  - `thumbnails/{video_id}/{hand_id}.jpg` — card reveal thumbnails
- Lifecycle: transition thumbnails to S3-IA after 30 days

### DynamoDB
- **Table**: `pokerfx`
  - PK: `video_id` (String)
  - SK: `hand_id` (String) — only present for hand items
  - Attributes: `filename`, `status`, `clip_count`, `detected_count`, `verified_count`, `s3_key`, `created_at`
  - GSI: `status-index` on `status` (optional, for filtering)

### AWS Batch
- **Compute environment**: managed, On-Demand (or Spot for cheaper)
- **Job queue**: `pokerfx-queue`
- **Job definition**: `pokerfx-card-detect:1`
  - Container image: ECR repo `pokerfx/card-detect-worker`
  - vCPU: 2, Memory: 4GB
  - Timeout: 15 min
  - Environment: `VIDEO_ID`, `S3_KEY`, `DYNAMODB_TABLE`, `AWS_REGION`

### IAM Role (Batch worker)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::pokerfx-uploads/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:*:*:table/pokerfx"
    }
  ]
}
```

### ECR Repository
```bash
aws ecr create-repository --repository-name pokerfx/card-detect-worker
docker push <account>.dkr.ecr.<region>.amazonaws.com/pokerfx/card-detect-worker:latest
```

### FastAPI Deployment
Railway or Render recommended for simplicity:
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `AWS_*`, `S3_BUCKET`, `DYNAMODB_TABLE`, `BATCH_JOB_*`

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS key (or use instance role) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS secret | — |
| `S3_BUCKET` | S3 bucket name | `pokerfx-uploads` |
| `DYNAMODB_TABLE` | DynamoDB table name | `pokerfx` |
| `BATCH_JOB_QUEUE` | Batch job queue name | `pokerfx-queue` |
| `BATCH_JOB_DEFINITION` | Batch job definition | `pokerfx-card-detect:1` |

## Local Development

```bash
# 1. Start local DynamoDB
docker compose up dynamodb-local

# 2. Create DynamoDB table (one-time)
aws dynamodb create-table \
  --endpoint-url http://localhost:8001 \
  --table-name pokerfx \
  --attribute-definitions AttributeName=video_id,AttributeType=S \
  --key-schema AttributeName=video_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 3. Start API
cd backend && pip install -r requirements.txt
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
  DYNAMODB_ENDPOINT=http://localhost:8001 \
  uvicorn backend.main:app --reload

# 4. Frontend (already has mock data with VITE_USE_MOCK=true)
cd frontend && npm run dev
```

## DynamoDB Table Schema

```bash
aws dynamodb create-table \
  --table-name pokerfx \
  --attribute-definitions \
    AttributeName=video_id,AttributeType=S \
    AttributeName=hand_id,AttributeType=S \
  --key-schema \
    AttributeName=video_id,KeyType=HASH \
    AttributeName=hand_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

> Note: `hand_id` is only present for hand items, not video items.
> Video items use `video_id` as both PK and SK (effectively).
