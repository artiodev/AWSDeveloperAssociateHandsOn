#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE:?AWS_PROFILE must be set explicitly — never use default credentials}"
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

STACK_NAME="${1:?Usage: teardown.sh <stack-name> <region>}"
REGION="${2:?Usage: teardown.sh <stack-name> <region>}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ARTIFACTS_BUCKET="${STACK_NAME}-cfn-artifacts-${ACCOUNT_ID}"

echo "==> Deleting CloudFormation stack: $STACK_NAME"
echo "    (S3Cleanup custom resource will empty the data lake bucket)"
aws cloudformation delete-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo "==> Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"
echo "    Stack deleted."

echo "==> Emptying and deleting artifacts bucket: $ARTIFACTS_BUCKET"
aws s3 rm "s3://${ARTIFACTS_BUCKET}" --recursive --region "$REGION" 2>/dev/null || true
aws s3api delete-bucket --bucket "$ARTIFACTS_BUCKET" --region "$REGION" 2>/dev/null || true

echo ""
echo "Done! All resources removed."
