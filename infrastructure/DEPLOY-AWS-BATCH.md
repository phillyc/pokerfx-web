# Deploy AWS Batch Infrastructure for PokerFX

> **Issue #5** — CloudFormation stack: ECR, Batch compute env, job queue, job definition, IAM roles

## What Gets Created

| Resource | Name | Purpose |
|----------|------|---------|
| ECR Repository | `pokerfx/card-detect-worker` | Worker Docker image |
| IAM: Batch Service Role | `pokerfx-batch-service-production` | AWS Batch service permissions |
| IAM: Job Execution Role | `pokerfx-batch-execution-production` | ECS task execution (pull image, logs) |
| IAM: Job Role | `pokerfx-batch-job-production` | S3 read/write, DynamoDB CRUD, Secrets Manager |
| IAM: Instance Role | `pokerfx-batch-instance-production` | EC2 compute instance role (+ SSM access) |
| Security Group | `pokerfx-batch-sg-production` | Outbound-only access for workers |
| CloudWatch Log Group | `/aws/batch/job/pokerfx-production` | 14-day retention |
| Batch Compute Env | `pokerfx-compute-production` | Spot instances, c6i.xlarge, 0–16 vCPUs, scales to zero |
| Batch Job Queue | `pokerfx-queue-production` | FIFO, priority 1 |
| Batch Job Definition | `pokerfx-detect-v1-production` | 4 vCPU, 8 GB, 15-min timeout, 2 retries |

**Cost estimate:** ~$0.03–$0.05 per spot hour on c6i.xlarge. Scales to zero when idle — you only pay when jobs run. ECR storage is ~pennies/month.

---

## Prerequisites Checklist

- [ ] AWS CLI installed and configured with admin/poweruser credentials
- [ ] Region: `us-east-1` (N. Virginia) — all existing resources (S3, DynamoDB) are here
- [ ] S3 bucket `pokerfx-uploads` exists with `uploads/` and `thumbnails/` prefixes writable
- [ ] DynamoDB table `pokerfx` exists
- [ ] Docker installed locally (for building the worker image)

---

## Step 1: Gather VPC/Subnet IDs

The Batch compute environment needs to know where to launch EC2 instances.

```bash
# Get your default VPC ID
aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[*].VpcId" --output text --region us-east-1

# Get your default VPC subnets (need at least 2 in different AZs)
aws ec2 describe-subnets \
  --filters "Name=default-for-az,Values=true" \
  --query "Subnets[*].SubnetId" --output text --region us-east-1
```

Write these down — you'll need them in Step 2.

---

## Step 2: Update parameters.json

Edit `infrastructure/parameters.json` with real values:

```json
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "subnet-xxxxxxxxx,subnet-yyyyyyyyy"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "vpc-xxxxxxxxx"
  },
  {
    "ParameterKey": "S3BucketName",
    "ParameterValue": "pokerfx-uploads"
  },
  {
    "ParameterKey": "DynamoDBTableName",
    "ParameterValue": "pokerfx"
  }
]
```

---

## Step 3: Create Secrets Manager Secrets

The worker container needs API keys for vision calls. The CloudFormation template references these secrets by exact ARN.

```bash
# Anthropic API key (required — primary vision provider)
aws secretsmanager create-secret \
  --name pokerfx/anthropic \
  --secret-string '{"ANTHROPIC_API_KEY": "sk-ant-api..."}' \
  --region us-east-1

# OpenAI API key (optional backup — only needed if switching VISION_PROVIDER)
aws secretsmanager create-secret \
  --name pokerfx/openai \
  --secret-string '{"OPENAI_API_KEY": "sk-proj-..."}' \
  --region us-east-1
```

> **Note:** The secret values must be valid JSON objects with the keys shown above (`ANTHROPIC_API_KEY` for the Anthropic secret, `OPENAI_API_KEY` for the OpenAI secret). The Batch job definition references these via `Secrets` in the container config.

> **OpenAI secret is optional** — if you're using Anthropic only, you can skip it. The job definition will still work (the secret just needs to exist to prevent a CFN deploy error). If you haven't created it, comment out the OpenAI secret in `template.yaml` temporarily or create a dummy one.

Alternative: create a dummy secret to avoid template edit:
```bash
aws secretsmanager create-secret \
  --name pokerfx/openai \
  --secret-string '{"OPENAI_API_KEY": "placeholder"}' \
  --region us-east-1
```

---

## Step 4: Deploy CloudFormation Stack

```bash
cd infrastructure/
./deploy.sh
```

This runs:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name pokerfx-infra \
  --parameter-overrides file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Stack takes ~5–10 minutes (EC2 instance role and Batch compute environment need provisioning).

When done, get the outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs" --output json --region us-east-1
```

Key outputs:
- **ECRRepositoryUri** — the repo you'll push the worker image to
- **JobQueueArn** — the queue ID for job submission
- **JobDefinitionArn** — the job definition for Batch submits

---

## Step 5: Build and Push the Worker Image

```bash
# Get the ECR URI
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryUri'].OutputValue" \
  --output text --region us-east-1)

echo "ECR_URI=$ECR_URI"
# Should look like: 123456789012.dkr.ecr.us-east-1.amazonaws.com/pokerfx/card-detect-worker

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URI

# Build the worker image (from the worker/ directory)
cd worker/
docker build -t pokerfx-worker . --platform linux/amd64
cd ..

# Tag and push
docker tag pokerfx-worker:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

---

## Step 6: Verify with a Test Job

### Pre-requisite: have a test video in S3

Either upload a real video via the API, or put a test `.mp4` in place:

```bash
# Upload a short test clip
aws s3 cp test-clip.mp4 \
  s3://pokerfx-uploads/uploads/test-001/test-clip.mp4 \
  --region us-east-1

# Create a test video record in DynamoDB
aws dynamodb put-item \
  --table-name pokerfx \
  --item '{
    "video_id": {"S": "test-001"},
    "filename": {"S": "test-clip.mp4"},
    "status": {"S": "pending"},
    "clip_count": {"N": "0"},
    "detected_count": {"N": "0"},
    "verified_count": {"N": "0"},
    "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
    "s3_key": {"S": "uploads/test-001/test-clip.mp4"}
  }' \
  --region us-east-1
```

### Submit a Batch job manually

```bash
QUEUE=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='JobQueueArn'].OutputValue" \
  --output text --region us-east-1)

JOB_DEF=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='JobDefinitionArn'].OutputValue" \
  --output text --region us-east-1)

aws batch submit-job \
  --job-name pokerfx-test-001 \
  --job-queue "$QUEUE" \
  --job-definition "$JOB_DEF" \
  --container-overrides '{
    "environment": [
      {"name": "VIDEO_ID", "value": "test-001"},
      {"name": "S3_KEY", "value": "uploads/test-001/test-clip.mp4"},
      {"name": "DYNAMODB_TABLE", "value": "pokerfx"},
      {"name": "AWS_REGION", "value": "us-east-1"}
    ]
  }' \
  --region us-east-1
```

### Watch the job

```bash
# Check job status (replace JOB_ID from the submit response)
aws batch describe-jobs --jobs JOB_ID --query "jobs[0].status" --region us-east-1

# Expected progression: SUBMITTED → PENDING → RUNNABLE → STARTING → RUNNING → SUCCEEDED
```

### Verify results in DynamoDB

```bash
# Check video status
aws dynamodb get-item \
  --table-name pokerfx \
  --key '{"video_id": {"S": "test-001"}}' \
  --region us-east-1

# Check detected hands
aws dynamodb query \
  --table-name pokerfx \
  --key-condition-expression "video_id = :vid" \
  --expression-attribute-values '{":vid": {"S": "test-001"}}' \
  --region us-east-1
```

### Check job logs in CloudWatch

```bash
# Navigate to CloudWatch → Log Groups → /aws/batch/job/pokerfx-production
# Look for the stream matching your job name
```

---

## Update the Worker Image (Re-deploy)

After updating `worker/` code:

```bash
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryUri'].OutputValue" \
  --output text --region us-east-1)

cd worker/
docker build -t pokerfx-worker . --platform linux/amd64
docker tag pokerfx-worker:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

New jobs will automatically pull `:latest`. Running jobs are unaffected.

---

## Clean Up (Tear Down)

```bash
# Delete the CloudFormation stack (this removes everything it created)
aws cloudformation delete-stack --stack-name pokerfx-infra --region us-east-1

# Verify it's gone
aws cloudformation describe-stacks --stack-name pokerfx-infra --region us-east-1
# Should return "Stack with id pokerfx-infra does not exist"
```

> ⚠️ The CloudFormation stack doesn't manage the ECR images themselves — deleting the stack leaves the ECR repo. Clean those manually if needed:
> ```bash
> aws ecr delete-repository --repository-name pokerfx/card-detect-worker --force --region us-east-1
> ```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `CAPABILITY_NAMED_IAM` not specified | Add `--capabilities CAPABILITY_NAMED_IAM` to deploy command |
| Stack stuck in CREATE_FAILED | Check CloudFormation events for the failing resource — usually a naming conflict or missing subnet/VPC |
| Job stuck in RUNNABLE | Check compute environment health, EC2 service quotas (spot instance limits), and that subnets have route-to-internet |
| Job FAILED — can't pull image | Verify the worker image was pushed to ECR and the execution role has ECR pull permissions |
| Job FAILED — can't write to DynamoDB | Check `BatchJobRole` IAM policy allows DynamoDB PutItem to the `pokerfx` table |
| Job FAILED — API key not found | Verify Secrets Manager secrets exist with exact names `pokerfx/anthropic` and `pokerfx/openai` |
| Subnet has no route to the internet | Workers need outbound internet for Anthropic/OpenAI API calls. Ensure a NAT gateway or IGW route exists. |
