#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TIMESTAMP=$(date +%s)
LAMBDA_BUCKET="${ENVIRONMENT}-assessmax-lambdas-${AWS_ACCOUNT_ID}"
REGION=$(aws configure get region)
REGION=${REGION:-us-east-2}

echo "🚀 Deploying Lambda functions for environment: ${ENVIRONMENT}"
echo "   AWS Account: ${AWS_ACCOUNT_ID}"
echo "   Region: ${REGION}"

# Create Lambda code bucket if it doesn't exist
echo "📦 Ensuring Lambda code bucket exists..."
if ! aws s3 ls "s3://${LAMBDA_BUCKET}" 2>/dev/null; then
    echo "   Creating bucket: ${LAMBDA_BUCKET}"
    aws s3 mb "s3://${LAMBDA_BUCKET}" --region "${REGION}"

    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "${LAMBDA_BUCKET}" \
        --versioning-configuration Status=Enabled

    # Block public access
    aws s3api put-public-access-block \
        --bucket "${LAMBDA_BUCKET}" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
else
    echo "   Bucket already exists: ${LAMBDA_BUCKET}"
fi

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: ${TEMP_DIR}"

# Package Normalization Lambda
echo ""
echo "📦 Packaging Normalization Lambda..."
NORM_DIR="${TEMP_DIR}/normalization"
mkdir -p "${NORM_DIR}"
cp -r backend/lambdas/normalization/* "${NORM_DIR}/"

cd "${NORM_DIR}"
zip -r normalization.zip . >/dev/null
aws s3 cp normalization.zip "s3://${LAMBDA_BUCKET}/normalization.zip"
echo "   ✅ Uploaded normalization.zip"
cd - >/dev/null

# Package Scoring Lambda
echo ""
echo "📦 Packaging Scoring Lambda..."
SCORING_DIR="${TEMP_DIR}/scoring"
mkdir -p "${SCORING_DIR}"
cp -r backend/lambdas/scoring/* "${SCORING_DIR}/"

cd "${SCORING_DIR}"
zip -r scoring.zip . >/dev/null
aws s3 cp scoring.zip "s3://${LAMBDA_BUCKET}/scoring.zip"
echo "   ✅ Uploaded scoring.zip"
cd - >/dev/null

# Deploy Lambda CloudFormation stack
echo ""
echo "🔧 Deploying Lambda CloudFormation stack..."
aws cloudformation deploy \
    --template-file infra/lambda/functions.yaml \
    --stack-name "${ENVIRONMENT}-assessmax-lambda" \
    --parameter-overrides Environment="${ENVIRONMENT}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${REGION}"

echo "   ✅ Lambda stack deployed"

# Cleanup
rm -rf "${TEMP_DIR}"
echo ""
echo "✅ Lambda deployment complete!"
