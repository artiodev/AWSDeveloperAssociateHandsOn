#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE:?AWS_PROFILE must be set explicitly — never use default credentials}"
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

STACK_NAME="${1:?Usage: deploy.sh <stack-name> <region>}"
REGION="${2:?Usage: deploy.sh <stack-name> <region>}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ARTIFACTS_BUCKET="${STACK_NAME}-cfn-artifacts-${ACCOUNT_ID}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Creating artifacts bucket: $ARTIFACTS_BUCKET"
aws s3api create-bucket \
  --bucket "$ARTIFACTS_BUCKET" \
  --region "$REGION" \
  $([ "$REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$REGION" || echo "") \
  2>/dev/null || echo "Bucket already exists, continuing."

package_lambda() {
  local name="$1"
  local dir="$ROOT_DIR/lambda/$name"
  local zip_file="$ROOT_DIR/lambda/${name}.zip"

  echo "==> Packaging $name"
  rm -rf "$dir/package" "$zip_file"
  mkdir -p "$dir/package"

  if [ -f "$dir/requirements.txt" ]; then
    pip install -r "$dir/requirements.txt" -t "$dir/package" --quiet
  fi

  cp "$dir/handler.py" "$dir/package/"
  (cd "$dir/package" && zip -r "$zip_file" . -x "*.pyc" -x "*/__pycache__/*" > /dev/null)
  aws s3 cp "$zip_file" "s3://${ARTIFACTS_BUCKET}/${name}.zip" --region "$REGION"
  rm -rf "$dir/package" "$zip_file"
}

package_lambda producer
package_lambda topic_creator
package_lambda consumer
package_lambda s3_cleanup

echo "==> Running cfn-lint on template"
if command -v cfn-lint &> /dev/null; then
  cfn-lint "$ROOT_DIR/template.yaml" --include-checks W
else
  echo "WARNING: cfn-lint not found, skipping lint. Install with: pip install cfn-lint"
fi

echo "==> Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
  --template-file "$ROOT_DIR/template.yaml" \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ArtifactsBucket="$ARTIFACTS_BUCKET" \
  --no-fail-on-empty-changeset

echo ""
echo "==> Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs" \
  --output table

echo ""
echo "Done! Pipeline is running. Producer fires every minute."
