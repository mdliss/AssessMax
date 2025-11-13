#!/bin/bash
# Script to update Lambda environment variables

set -e

# Check if required arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./update-lambda-env.sh <DATABASE_URL> <OPENAI_API_KEY>"
    echo ""
    echo "Example:"
    echo "  ./update-lambda-env.sh 'postgresql://user:pass@host:5432/db' 'sk-xxxxx'"
    echo ""
    echo "To get your Railway DATABASE_URL:"
    echo "  1. Go to Railway dashboard"
    echo "  2. Click on Postgres service"
    echo "  3. Go to Variables tab"
    echo "  4. Copy the DATABASE_URL value"
    exit 1
fi

DATABASE_URL="$1"
OPENAI_API_KEY="$2"

echo "Updating Lambda function: dev-assessmax-scoring"
echo ""

aws lambda update-function-configuration \
  --function-name dev-assessmax-scoring \
  --environment "Variables={
    ENVIRONMENT=dev,
    S3_NORMALIZED_BUCKET=dev-assessmax-normalized-971422717446,
    S3_OUTPUTS_BUCKET=dev-assessmax-outputs-971422717446,
    DYNAMODB_JOBS_TABLE=dev-assessmax-jobs,
    AGGREGATION_QUEUE_URL=https://sqs.us-east-2.amazonaws.com/971422717446/dev-aggregation-queue,
    DATABASE_URL=$DATABASE_URL,
    OPENAI_API_KEY=$OPENAI_API_KEY
  }" \
  --query "Environment.Variables" \
  --output table

echo ""
echo "✅ Lambda environment variables updated successfully!"
echo ""
echo "Now test by uploading a transcript - it should reach 'succeeded' status."
