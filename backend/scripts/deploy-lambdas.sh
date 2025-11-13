#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAMBDA_SRC_DIR="${PROJECT_ROOT}/lambdas"
INFRA_DIR="${PROJECT_ROOT}/infra"
ENVIRONMENT=${1:-dev}

if [[ ! -d "${LAMBDA_SRC_DIR}" ]]; then
  echo "Unable to locate Lambda source directory at ${LAMBDA_SRC_DIR}" >&2
  exit 1
fi

if [[ ! -f "${INFRA_DIR}/lambda/functions.yaml" ]]; then
  echo "Unable to locate Lambda CloudFormation template at ${INFRA_DIR}/lambda/functions.yaml" >&2
  exit 1
fi

create_zip_package() {
  local src_dir="$1"
  local output_zip="$2"

  if command -v zip >/dev/null 2>&1; then
    (cd "${src_dir}" && zip -r "${output_zip}" . >/dev/null)
  else
    python3 - "$src_dir" "$output_zip" >/dev/null <<'PY'
import os
import sys
import zipfile

src = sys.argv[1]
output = sys.argv[2]

with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(src):
        for fname in files:
            full_path = os.path.join(root, fname)
            arcname = os.path.relpath(full_path, src)
            zf.write(full_path, arcname)
PY
  fi
}

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_BUCKET="${ENVIRONMENT}-assessmax-lambdas-${AWS_ACCOUNT_ID}"
REGION=$(aws configure get region)
REGION=${REGION:-us-east-2}

echo "🚀 Deploying Lambda functions for environment: ${ENVIRONMENT}"
echo "   AWS Account: ${AWS_ACCOUNT_ID}"
echo "   Region: ${REGION}"

echo "📦 Ensuring Lambda code bucket exists..."
if ! aws s3 ls "s3://${LAMBDA_BUCKET}" 2>/dev/null; then
    echo "   Creating bucket: ${LAMBDA_BUCKET}"
    aws s3 mb "s3://${LAMBDA_BUCKET}" --region "${REGION}"

    aws s3api put-bucket-versioning \
        --bucket "${LAMBDA_BUCKET}" \
        --versioning-configuration Status=Enabled

    aws s3api put-public-access-block \
        --bucket "${LAMBDA_BUCKET}" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
else
    echo "   Bucket already exists: ${LAMBDA_BUCKET}"
fi

TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: ${TEMP_DIR}"

echo ""
echo "📦 Packaging Normalization Lambda..."
NORM_DIR="${TEMP_DIR}/normalization"
mkdir -p "${NORM_DIR}"
cp -r "${LAMBDA_SRC_DIR}/normalization"/* "${NORM_DIR}/"

NORMALIZATION_ZIP="${NORM_DIR}/normalization.zip"
create_zip_package "${NORM_DIR}" "${NORMALIZATION_ZIP}"
aws s3 cp "${NORMALIZATION_ZIP}" "s3://${LAMBDA_BUCKET}/normalization.zip"
echo "   ✅ Uploaded normalization.zip"

echo ""
echo "📦 Packaging Scoring Lambda..."
SCORING_DIR="${TEMP_DIR}/scoring"
mkdir -p "${SCORING_DIR}"
cp -r "${LAMBDA_SRC_DIR}/scoring"/* "${SCORING_DIR}/"

SCORING_ZIP="${SCORING_DIR}/scoring.zip"
create_zip_package "${SCORING_DIR}" "${SCORING_ZIP}"
aws s3 cp "${SCORING_ZIP}" "s3://${LAMBDA_BUCKET}/scoring.zip"
echo "   ✅ Uploaded scoring.zip"

echo ""
echo "🔧 Deploying Lambda CloudFormation stack..."
aws cloudformation deploy \
    --template-file "${INFRA_DIR}/lambda/functions.yaml" \
    --stack-name "${ENVIRONMENT}-assessmax-lambda" \
    --parameter-overrides Environment="${ENVIRONMENT}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${REGION}"

echo "   ✅ Lambda stack deployed"

rm -rf "${TEMP_DIR}"
echo ""
echo "✅ Lambda deployment complete!"
