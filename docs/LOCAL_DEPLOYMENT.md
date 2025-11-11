# AssessMax Local Deployment Guide

This guide walks through spinning up a fully functional AssessMax environment using Docker Compose, LocalStack, and the new synthetic data seeding tooling.

## 1. Prerequisites

- Docker Desktop 4.0+ with Compose v2
- Python 3.11+
- `make` (optional, for convenience)

## 2. Project Bootstrap

```bash
git clone <repo-url>
cd AssessMax
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e backend/[dev]
pip install -e dashboard
```

### Download NLP assets (backend requirement)

```bash
python -m spacy download en_core_web_sm
```

## 3. Start Infrastructure

Launch Postgres, LocalStack, backend API, and the dashboard in one command:

```bash
docker compose up --build
```

Services exposed locally:

| Service      | URL / Port              |
|--------------|-------------------------|
| Backend API  | http://localhost:8000   |
| Dashboard    | http://localhost:8501   |
| LocalStack   | http://localhost:4566   |
| Postgres     | localhost:5432          |

## 4. Seed Synthetic Data

Once the containers are healthy, seed the Postgres database with a realistic dataset:

```bash
python -m backend.scripts.generate_synthetic_data --classes 2 --weeks 12 --drop-existing
```

This script creates classes, students, weekly assessments, evidence spans, and class aggregates in line with the rubric expectations.

## 5. Provision LocalStack Resources

The backend expects S3 buckets and DynamoDB tables. Bootstrapping commands (run once):

```bash
aws --endpoint-url http://localhost:4566 s3 mb s3://assessmax-raw
aws --endpoint-url http://localhost:4566 s3 mb s3://assessmax-normalized
aws --endpoint-url http://localhost:4566 s3 mb s3://assessmax-outputs

aws --endpoint-url http://localhost:4566 dynamodb create-table \
  --table-name assessmax-jobs \
  --attribute-definitions AttributeName=job_id,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws --endpoint-url http://localhost:4566 dynamodb create-table \
  --table-name assessmax-artifacts \
  --attribute-definitions AttributeName=artifact_id,AttributeType=S \
  --key-schema AttributeName=artifact_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

> Tip: install `awscli-local` (`pip install awscli-local`) for shorter commands (`awslocal ...`).

## 6. Access the Dashboard

Visit http://localhost:8501. Demo mode provides synthetic data if the API is offline; with the backend running and seeded, the UI surfaces live results.

- **Class Overview** shows real averages, evidence-ready student summaries, and export links.
- **Student Detail** renders individual trajectories, confidence metrics, and evidence spans.
- **Trends** analyzes 4/8/12-week windows with PulseMax visual styling.
- **Uploads & Jobs** exposes pipeline health, upload forms, and sample job telemetry. Hook up Cognito and real S3/DynamoDB to make uploads live.

## 7. Useful Commands

- Tail backend logs: `docker compose logs -f backend`
- Restart backend only: `docker compose up backend --build`
- Tear down environment: `docker compose down`

## 8. Next Steps

- Wire AWS Cognito into LocalStack (or a real AWS account) for end-to-end auth.
- Update GitHub Actions to run the synthetic seeding script post-deploy for staging environments.
- Extend `backend/scripts/generate_synthetic_data.py` with scenario flags (e.g., low-performing cohorts) for richer demos.

With these assets, you now have a reproducible environment that mirrors production architecture, complete with realistic data for demos, QA, and educator feedback sessions.
