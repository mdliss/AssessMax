NLP Pipeline Batch Processing Infrastructure
===========================================

This directory contains AWS infrastructure configurations for the batch processing
pipeline using Lambda, SQS, and Step Functions.

Architecture Overview:
---------------------

1. API Endpoint triggers Step Functions execution
2. Step Functions orchestrates:
   - Input validation
   - Transcript normalization (Lambda)
   - NLP scoring (Lambda + SQS)
   - Result aggregation (Lambda)
   - Publishing to RDS/S3
3. SQS queues for fan-out and error handling
4. DynamoDB for job metadata tracking
5. S3 for file storage (raw, normalized, outputs)

Directory Structure:
-------------------

infra/
├── step_functions/
│   └── nlp_pipeline_state_machine.json  # State machine definition
├── sqs/
│   └── queues.yaml                      # CloudFormation for SQS queues
└── README.txt                           # This file

backend/lambdas/
├── normalization/
│   ├── handler.py                       # Normalization Lambda
│   └── requirements.txt
├── scoring/
│   ├── handler.py                       # Scoring Lambda
│   └── requirements.txt
└── aggregation/                         # TODO: Create aggregation handler
    ├── handler.py
    └── requirements.txt

Deployment Steps:
----------------

1. Deploy SQS Queues:
   ```
   aws cloudformation deploy \
     --template-file infra/sqs/queues.yaml \
     --stack-name assessmax-queues-dev \
     --parameter-overrides Environment=dev
   ```

2. Package Lambda Functions:
   ```
   cd backend/lambdas/normalization
   pip install -r requirements.txt -t package/
   cd package && zip -r ../normalization.zip .
   cd .. && zip -g normalization.zip handler.py

   cd ../scoring
   pip install -r requirements.txt -t package/
   cd package && zip -r ../scoring.zip .
   cd .. && zip -g scoring.zip handler.py
   ```

3. Deploy Lambda Functions:
   ```
   aws lambda create-function \
     --function-name assessmax-normalization-dev \
     --runtime python3.11 \
     --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
     --handler handler.handler \
     --zip-file fileb://normalization.zip \
     --timeout 300 \
     --memory-size 512 \
     --environment Variables="{
       DYNAMODB_JOBS_TABLE=assessmax-jobs-dev,
       S3_RAW_BUCKET=assessmax-raw-dev,
       S3_NORMALIZED_BUCKET=assessmax-normalized-dev,
       SCORING_QUEUE_URL=<from stack outputs>
     }"

   aws lambda create-function \
     --function-name assessmax-scoring-dev \
     --runtime python3.11 \
     --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
     --handler handler.handler \
     --zip-file fileb://scoring.zip \
     --timeout 900 \
     --memory-size 2048 \
     --environment Variables="{
       DYNAMODB_JOBS_TABLE=assessmax-jobs-dev,
       S3_NORMALIZED_BUCKET=assessmax-normalized-dev,
       S3_OUTPUTS_BUCKET=assessmax-outputs-dev,
       AGGREGATION_QUEUE_URL=<from stack outputs>
     }"

   # Configure SQS trigger for scoring Lambda
   aws lambda create-event-source-mapping \
     --function-name assessmax-scoring-dev \
     --batch-size 5 \
     --event-source-arn <scoring-queue-arn> \
     --enabled
   ```

4. Create Step Functions State Machine:
   ```
   # First, replace placeholders in state machine JSON:
   # - ${ValidateLambdaArn}
   # - ${NormalizationLambdaArn}
   # - ${ScoringQueueUrl}
   # - ${AggregationLambdaArn}
   # - ${PublishLambdaArn}
   # - ${JobsTableName}

   aws stepfunctions create-state-machine \
     --name assessmax-nlp-pipeline-dev \
     --definition file://infra/step_functions/nlp_pipeline_state_machine.json \
     --role-arn arn:aws:iam::ACCOUNT:role/step-functions-execution-role
   ```

5. Test Execution:
   ```
   aws stepfunctions start-execution \
     --state-machine-arn <state-machine-arn> \
     --input '{
       "job_id": "test-job-123",
       "input_key": "raw/class-101/2024-01-15/transcript.txt",
       "format": "txt",
       "class_id": "class-101",
       "date": "2024-01-15",
       "metadata": {}
     }'
   ```

Environment Variables Required:
------------------------------

Normalization Lambda:
- DYNAMODB_JOBS_TABLE: DynamoDB table name for jobs
- S3_RAW_BUCKET: S3 bucket for raw uploads
- S3_NORMALIZED_BUCKET: S3 bucket for normalized transcripts
- SCORING_QUEUE_URL: SQS queue URL for scoring

Scoring Lambda:
- DYNAMODB_JOBS_TABLE: DynamoDB table name for jobs
- S3_NORMALIZED_BUCKET: S3 bucket for normalized transcripts
- S3_OUTPUTS_BUCKET: S3 bucket for scoring outputs
- AGGREGATION_QUEUE_URL: SQS queue URL for aggregation (optional)
- RDS_DATABASE_ARN: RDS Data API database ARN (optional)
- RDS_SECRET_ARN: RDS Data API secret ARN (optional)

IAM Permissions Required:
-------------------------

Lambda Execution Role needs:
- S3: GetObject, PutObject
- DynamoDB: GetItem, UpdateItem, PutItem
- SQS: SendMessage, ReceiveMessage, DeleteMessage
- CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents
- RDS Data API: ExecuteStatement (if using RDS)

Step Functions Execution Role needs:
- Lambda: InvokeFunction
- DynamoDB: UpdateItem
- SQS: SendMessage
- CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents

Monitoring and Observability:
-----------------------------

1. CloudWatch Logs:
   - /aws/lambda/assessmax-normalization-dev
   - /aws/lambda/assessmax-scoring-dev
   - /aws/stepfunctions/assessmax-nlp-pipeline-dev

2. CloudWatch Metrics:
   - Lambda duration, errors, throttles
   - SQS message counts, age, DLQ messages
   - Step Functions execution success/failure rates

3. DynamoDB Job Tracking:
   - Query jobs by status
   - Monitor job duration
   - Track error rates

4. Alarms:
   - DLQ message count > 0
   - Lambda error rate > 1%
   - Step Function execution failures
   - Job processing time > threshold

Scaling Considerations:
----------------------

1. Lambda Concurrency:
   - Normalization: Reserved concurrency 10-50
   - Scoring: Reserved concurrency 5-20 (more memory intensive)

2. SQS Queue Configuration:
   - Visibility timeout matches Lambda timeout
   - Message retention 4 days
   - DLQ for failed messages

3. Cost Optimization:
   - Use Lambda layers for shared dependencies
   - Consider ECS/EKS for heavy NLP processing
   - Batch processing for cost efficiency
   - S3 lifecycle policies for old data

Production Deployment Checklist:
--------------------------------

- [ ] Set up separate dev/staging/prod environments
- [ ] Configure proper IAM roles with least privilege
- [ ] Enable CloudWatch alarms and SNS notifications
- [ ] Set up DLQ monitoring and alerting
- [ ] Implement retry strategies with exponential backoff
- [ ] Add request IDs for tracing
- [ ] Configure VPC endpoints for S3/DynamoDB
- [ ] Enable encryption at rest (S3, DynamoDB, SQS)
- [ ] Set up backup and disaster recovery
- [ ] Document runbook for common issues
- [ ] Load test with realistic data volumes
- [ ] Set up cost monitoring and budgets

Next Steps:
-----------

1. Create aggregation Lambda handler
2. Create publishing Lambda handler
3. Add validation Lambda for input checking
4. Implement comprehensive error handling
5. Add integration tests for pipeline
6. Set up CI/CD for Lambda deployments
7. Configure monitoring dashboards
8. Document operational procedures
