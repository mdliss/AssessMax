#!/bin/bash
# Complete deployment script for persistence pipeline
# This script:
# 1. Deploys the persistence Lambda function
# 2. Updates Step Functions to include persistence step
# 3. Tests the complete pipeline

set -e

echo "=========================================="
echo "AssessMax Persistence Pipeline Deployment"
echo "=========================================="
echo ""

# Check for DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "Please get your DATABASE_URL from Railway:"
    echo "  1. Go to Railway dashboard"
    echo "  2. Select your PostgreSQL service"
    echo "  3. Copy the DATABASE_URL"
    echo "  4. Run: export DATABASE_URL='postgresql://...'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✓ DATABASE_URL is set"
echo ""

# Deploy persistence Lambda
echo "Step 1: Deploying persistence Lambda function..."
cd "$(dirname "$0")/lambdas/persistence"
bash deploy.sh
cd -
echo "✓ Persistence Lambda deployed"
echo ""

# Update Step Functions
echo "Step 2: Updating Step Functions workflow..."
aws stepfunctions update-state-machine \
  --state-machine-arn "arn:aws:states:us-east-2:971422717446:stateMachine:dev-TranscriptProcessing" \
  --definition file:///tmp/stepfunctions-definition-with-persistence.json \
  --region us-east-2

echo "✓ Step Functions workflow updated"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your pipeline now:"
echo "  1. Uploads files to S3"
echo "  2. Normalizes transcripts (Lambda)"
echo "  3. Scores students (Lambda)"
echo "  4. Persists to PostgreSQL (Lambda) ← NEW!"
echo "  5. Frontend displays results ← WILL NOW WORK!"
echo ""
echo "Next steps:"
echo "  1. Upload a file through your frontend"
echo "  2. Wait ~10-15 seconds"
echo "  3. Refresh the class dashboard"
echo "  4. You should see the scored results!"
echo ""
