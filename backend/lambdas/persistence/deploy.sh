#!/bin/bash
set -e

# Configuration
FUNCTION_NAME="dev-assessmax-persistence"
REGION="us-east-2"
ROLE_ARN="arn:aws:iam::971422717446:role/dev-assessmax-lambda-execution"

# Get DATABASE_URL from Railway or environment
DATABASE_URL="${DATABASE_URL:-$(echo $DATABASE_URL)}"

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    echo "Please set it to your Railway PostgreSQL connection string"
    exit 1
fi

echo "Building Lambda deployment package..."

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
cd "$(dirname "$0")"

# Copy handler
cp handler.py "$BUILD_DIR/"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t "$BUILD_DIR/" --quiet

# Create ZIP
cd "$BUILD_DIR"
zip -r9 /tmp/persistence-lambda.zip . > /dev/null

echo "Deployment package created: /tmp/persistence-lambda.zip"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb:///tmp/persistence-lambda.zip \
        --region "$REGION"

    # Update environment variables
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment "Variables={DATABASE_URL=$DATABASE_URL,S3_OUTPUTS_BUCKET=dev-assessmax-outputs-971422717446}" \
        --region "$REGION"
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler handler.lambda_handler \
        --zip-file fileb:///tmp/persistence-lambda.zip \
        --timeout 60 \
        --memory-size 512 \
        --environment "Variables={DATABASE_URL=$DATABASE_URL,S3_OUTPUTS_BUCKET=dev-assessmax-outputs-971422717446}" \
        --region "$REGION"
fi

# Cleanup
rm -rf "$BUILD_DIR"
rm /tmp/persistence-lambda.zip

echo "Lambda function deployed successfully: $FUNCTION_NAME"
