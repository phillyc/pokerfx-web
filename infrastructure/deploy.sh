#!/usr/bin/env bash
# Deploy PokerFX AWS Batch infrastructure via CloudFormation.
# Must be run from the infrastructure/ directory.
#
# Usage: ./deploy.sh [--environment staging|production] [--dry-run]
set -euo pipefail

REGION="us-east-1"
STACK_NAME="pokerfx-infra"
ENVIRONMENT="production"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/template.yaml"
PARAMS="${SCRIPT_DIR}/parameters.json"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "❌ Template not found: $TEMPLATE"
  exit 1
fi

if [[ ! -f "$PARAMS" ]]; then
  echo "❌ Parameters file not found: $PARAMS"
  echo "   Copy parameters.json.example → parameters.json and fill in your values."
  exit 1
fi

# Validate that user has filled in the subnet/vpc placeholders
if grep -q "CHANGE_ME" "$PARAMS"; then
  echo "❌ parameters.json still contains CHANGE_ME placeholders."
  echo "   Edit it to add your actual VPC ID and subnet IDs."
  exit 1
fi

echo "🚀 Deploying PokerFX infrastructure..."
echo "   Stack:     $STACK_NAME"
echo "   Region:    $REGION"
echo "   Template:  $TEMPLATE"
echo "   Parameters: $PARAMS"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "🔍 Dry run — validating template only..."
  aws cloudformation validate-template \
    --template-body "file://$TEMPLATE" \
    --region "$REGION"
  echo "✅ Template is valid."
  exit 0
fi

aws cloudformation deploy \
  --template-file "$TEMPLATE" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides file://"$PARAMS" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"

echo ""
echo "✅ Stack deployed. Outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output table \
  --region "$REGION"
