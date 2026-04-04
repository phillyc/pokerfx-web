# PokerFX Infrastructure

AWS CloudFormation template for the card detection pipeline.

## What This Creates

- **ECR Repository** — `pokerfx/card-detect-worker` (with lifecycle policy to prune old images)
- **IAM Roles** — Batch service role, job execution role, job role (S3 + DynamoDB access), and EC2 instance role
- **Security Group** — Allows all outbound, no inbound (workers don't need inbound access)
- **CloudWatch Log Group** — 14-day retention for Batch job logs (`/aws/batch/job/pokerfx-{env}`)
- **Batch Compute Environment** — Managed Spot, `c6i.xlarge` (prod) or `c6i.large` (staging), 0–16 vCPUs, scales to zero when idle
- **Batch Job Queue** — `pokerfx-queue-{env}`, priority 1
- **Batch Job Definition** — `pokerfx-detect-v1-{env}`, 4 vCPU, 8 GB RAM, 15-min timeout, 2 retries

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Subnet IDs from your default VPC (or a custom VPC)
3. S3 bucket `pokerfx-uploads` already exists
4. DynamoDB table `pokerfx` already exists

## Initial Setup

### 1. Update parameters

Edit `infrastructure/parameters.json` with your actual subnet IDs and VPC ID:

```bash
# Find your default VPC subnets
aws ec2 describe-subnets \
  --filters "Name=default-for-az,Values=true" \
  --query "Subnets[*].SubnetId" --output text

# Find your default VPC ID
aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[*].VpcId" --output text
```

### 2. Create Secrets Manager secrets

The worker needs API keys for Anthropic and OpenAI vision calls. Store them in Secrets Manager:

```bash
# Anthropic API key
aws secretsmanager create-secret \
  --name pokerfx/anthropic \
  --secret-string '{"ANTHROPIC_API_KEY": "sk-ant-..."}'

# OpenAI API key (optional, if using OpenAI as vision provider)
aws secretsmanager create-secret \
  --name pokerfx/openai \
  --secret-string '{"OPENAI_API_KEY": "sk-..."}'
```

### 3. Deploy

```bash
cd infrastructure
./deploy.sh
```

Or manually:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name pokerfx-infra \
  --parameter-overrides file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### 4. Build and push the worker image

```bash
# Get the ECR URI from the stack outputs
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryUri'].OutputValue" \
  --output text)

# Login and push
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URI

docker build -t pokerfx-worker ../worker/ --platform linux/amd64
docker tag pokerfx-worker:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

### 5. Test with a manual job

```bash
QUEUE_ARN=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='JobQueueArn'].OutputValue" \
  --output text)

JOB_DEF=$(aws cloudformation describe-stacks \
  --stack-name pokerfx-infra \
  --query "Stacks[0].Outputs[?OutputKey=='JobDefinitionArn'].OutputValue" \
  --output text)

aws batch submit-job \
  --job-name pokerfx-test \
  --job-queue "$QUEUE_ARN" \
  --job-definition "$JOB_DEF" \
  --container-overrides '{
    "environment": [
      {"name": "VIDEO_ID", "value": "test-video-001"},
      {"name": "S3_KEY", "value": "uploads/test-video-001/test.mp4"},
      {"name": "DYNAMODB_TABLE", "value": "pokerfx"},
      {"name": "AWS_REGION", "value": "us-east-1"}
    ]
  }'
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Environment | production | `production` or `staging` (affects instance types and naming) |
| S3BucketName | pokerfx-uploads | S3 bucket for video uploads |
| DynamoDBTableName | pokerfx | DynamoDB table for video/hand data |
| SubnetIds | (required) | Subnets for compute environment |
| VpcId | (required) | VPC for the compute environment |

## Updating the Stack

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name pokerfx-infra \
  --parameter-overrides file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM
```

## Tear Down

```bash
aws cloudformation delete-stack --stack-name pokerfx-infra
```
