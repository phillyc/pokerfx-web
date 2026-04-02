# PokerFX Backend — Railway Deployment

## What was added

- `railway.json` — Railway deployment config (build from root, use `Dockerfile.api`)
- `pokerfx/` — stub package directory (satisfies Dockerfile COPY; card_detect.py lives in a separate `phillyc/pokerfx` repo — TODO: wire up as pip package or submodule)

## Railway Setup (Phil's steps)

1. Go to [railway.app](https://railway.app) → Sign up / Log in
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `phillyc/pokerfx-web`
4. Branch to deploy: `main` (after PR #4 is merged)
5. Railway auto-detects `railway.json` and `Dockerfile.api` from the repo root

## Environment Variables (set in Railway dashboard)

| Variable | Value | Notes |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | _(your AWS key)_ | For S3 + DynamoDB |
| `AWS_SECRET_ACCESS_KEY` | _(your AWS secret)_ | |
| `AWS_REGION` | `us-east-1` | Or your preferred region |
| `S3_BUCKET` | `pokerfx-uploads` | Or your bucket name |
| `DYNAMODB_TABLE` | `pokerfx` | Or your table name |
| `BATCH_JOB_QUEUE` | `pokerfx-queue` | Optional — only needed for `/api/videos/{id}/process` |
| `BATCH_JOB_DEFINITION` | `pokerfx-card-detect:1` | Optional — same |

**For the smoke test (`/health`):** Only `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` are needed for Railway to start the container. The health endpoint doesn't call AWS.

**For full API (upload/list/export):** DynamoDB + S3 must be accessible (real AWS credentials, or `DYNAMODB_ENDPOINT` pointing to LocalStack).

## DynamoDB Options

### Option A: Real AWS DynamoDB (recommended for production)
Create a table named `pokerfx` (or whatever you set `DYNAMODB_TABLE` to) with:
- Partition key: `video_id` (String)
- Sort key: `hand_id` (String) — for hand items

### Option B: LocalStack (for local dev / smoke test)
Set `DYNAMODB_ENDPOINT=http://localhost:8000` and run LocalStack:
```bash
docker run --rm -p 4566:4566 localstack/localstack
```

## Verifying the Deployment

```bash
# Get Railway deployment URL
curl https://<your-railway-app>.up.railway.app/health
# Expected: {"status":"ok","timestamp":"..."}
```

## S3 Bucket

Create an S3 bucket (e.g., `pokerfx-uploads`) with default settings. The backend only needs put/get/delete permissions for the bucket.

## Troubleshooting

**Build fails on `pokerfx/` not found:** The stub `pokerfx/` package was added to satisfy the Dockerfile COPY. The real `card_detect.py` lives in `phillyc/pokerfx` — wire it up as a pip package or git submodule when ready.

**DynamoDB errors on `/api/videos`:** Check that `DYNAMODB_TABLE` matches your table name and credentials are valid.

**Railway health check fails:** Railway does a `GET /` by default. The health endpoint is at `/health` — this is handled by Railway's `HTTPEndpoint` health check if configured, or you can add a redirect in FastAPI.
