# Middle School Non-Academic Skills Measurement Engine — MVP Development Task List

## Repository Layout (Monorepo)
ms-nonacademic-engine/
- backend/ (FastAPI service)
- dashboard/ (Streamlit app)
- infra/ (env, CI/CD)
- docs/

## PR #1: Bootstrap and Foundations (branch: setup/boot)
Goal: Working FastAPI skeleton, CI, Docker, and basic health endpoint.
Tasks:
- Init Python project (poetry or uv) with FastAPI.
- Add uvicorn[standard], fastapi, pydantic-settings, sqlalchemy, psycopg, boto3, aiohttp, python-jose, pyjwt.
- /healthz route and OpenAPI docs.
- Dockerfile multi-stage build, non-root, pinned deps.
- GitHub Actions: lint, type-check, unit tests, build image, push to ECR.
Acceptance:
- GET /healthz returns 200 in container.
- CI green on PR.

## PR #2: Auth via Cognito (branch: feature/auth-cognito)
Goal: Secure endpoints with JWT validation.
Tasks:
- Configure Cognito User Pool and App Client.
- JWKS fetch and caching; FastAPI dependency for JWT verify.
- Roles: educator, admin, read_only via Cognito groups.
- Session cookies for dashboard; CORS policy.
Acceptance:
- 401 without token, 200 with educator token.
- Group changes reflected within 5 minutes.

## PR #3: Storage and Metadata (branch: feature/storage-metadata)
Goal: Ingest to S3 with metadata registry in DynamoDB.
Tasks:
- S3 buckets raw/ normalized/ outputs/ with KMS and policies.
- DynamoDB jobs and artifacts tables; TTL for temp items.
- Presigned URL endpoint with size/type checks.
- sha256 hashing and duplicate detection.
Acceptance:
- Upload via presigned URL creates Dynamo row.
- Duplicate upload returns existing key (idempotent).

## PR #4: RDS Schema and ORM (branch: feature/rds-schema)
Goal: Core relational schema and access layer.
Tasks:
- Alembic migrations for students, assessments, evidence, class_aggregates.
- SQLAlchemy models and repos.
- Seed/fixtures for dev.
Acceptance:
- Migration runs; CRUD passes tests; indices validated.

## PR #5: Normalization Pipeline (branch: feature/normalization)
Goal: Convert uploads to canonical transcript JSONL.
Tasks:
- Parsers for TXT, CSV, JSONL; basic PDF/DOCX text extraction for page mapping.
- Validation of speakers, timestamps, student linkage.
- Store normalized output in S3; link to job_id in DynamoDB.
Acceptance:
- Invalid rows flagged; job continues with warnings.
- Canonical schema passes pydantic validation.

## PR #6: NLP Scoring (branch: feature/nlp-scoring)
Goal: Skills model ensemble and evidence span extraction.
Tasks:
- spaCy sentence splitting.
- Transformers for classification; calibration layer.
- Evidence span mining with offsets; constraints.
- Determinism via seeds; record model_version and config_hash.
Acceptance:
- Unit tests pass with stable outputs.
- Evidence spans resolve in >=95% of test cases.

## PR #7: Orchestration (branch: feature/orchestration)
Goal: Step Functions + Lambda for batch jobs; SQS for fan-out.
Tasks:
- State machine ingest -> normalize -> score -> aggregate -> publish.
- Retry/backoff; DLQs.
- Job API to trigger by class_id/date; status endpoint.
Acceptance:
- Happy flow green; retries and DLQ observable in logs.

## PR #8: Educator Dashboard (Streamlit) (branch: feature/dashboard)
Goal: Class Overview, Student Detail, Trends, Uploads and Jobs.
Tasks:
- OAuth with Cognito hosted UI; token persistence.
- Pages: Overview, Student, Trends (4-12 weeks), Uploads, Jobs.
- Exports: CSV and PDF; accessibility styles.
Acceptance:
- Find latest student assessment in <10s.
- Weekly export in <5s for class size 30.

## PR #9: Observability and Security (branch: feature/observability-security)
Goal: Logging, metrics, hardening.
Tasks:
- Structured logs with request IDs; CloudWatch dashboards.
- RDS and S3 encryption; VPC endpoints; Secrets in SSM/Secrets Manager.
- Audit tables for reads/writes on sensitive routes.
Acceptance:
- Audit trail complete; alarms for job failure and p95 latency.

## PR #10: QA, Datasets, Calibration (branch: feature/qa-calibration)
Goal: Quality bar and teacher review loop.
Tasks:
- Synthetic dataset generator with known cues.
- Calibration notebooks; thresholds in config.
- Teacher review page: mark reasonable/needs review.
Acceptance:
- >=70% reasonable on MVP set.
- Threshold updates without deploy.

## PR #11: Deployment (branch: deploy/prod)
Goal: Production push and smoke tests.
Tasks:
- GitHub Actions envs for dev/staging/prod with approvals.
- Blue/green or rolling deployments.
- Smoke tests and synthetic transactions.
Acceptance:
- Zero-downtime deploy.
- 50 concurrent educator sessions sustained.

## Environment and Secrets
.env.example (backend):
AWS_REGION=us-east-1
RDS_HOST=
RDS_DB=
RDS_USER=
RDS_PASSWORD=
DYNAMO_JOBS_TABLE=
DYNAMO_ARTIFACTS_TABLE=
S3_RAW_BUCKET=
S3_NORMALIZED_BUCKET=
S3_OUTPUTS_BUCKET=
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_JWKS_URL=
JWT_AUDIENCE=

GitHub Actions secrets:
AWS_ACCOUNT_ID, AWS_OIDC_ROLE, AWS_REGION, ECR_REPO_BACKEND, ECR_REPO_DASHBOARD, RDS_SECRET_ARN, PARAMETER_STORE_PREFIX

## Testing Matrix
Unit: parsers, validators, scoring functions, evidence span locator.
Integration: end-to-end job run on synthetic class day.
Load: 8 class-days/hour, 30 students/class, 3k utterances.
Security: JWT validation, role checks, S3 presign policy, SQL injection tests.
Accessibility: contrast and keyboard navigation.

## Done Criteria (MVP)
- API, pipeline, dashboard deployed to prod.
- Teacher blind review >=70% reasonable.
- Evidence spans resolvable to sources.
- Weekly exports and class trendlines operational.
- Runbook and on-call procedures documented.