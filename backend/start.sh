#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONUNBUFFERED=1

AUTO_DEPLOY="${AUTO_DEPLOY_LAMBDAS:-true}"
# Auto-detect Railway environment
if [[ -n "${RAILWAY_ENVIRONMENT:-}" ]] || [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  ENVIRONMENT="${ENVIRONMENT:-production}"
else
  ENVIRONMENT="${ENVIRONMENT:-dev}"
fi
LAMBDA_ENVIRONMENT="${LAMBDA_ENVIRONMENT:-${ENVIRONMENT}}"

run_lambda_deploy() {
  # Default to false in production to avoid startup timeouts
  if [[ "${ENVIRONMENT}" == "production" ]] && [[ "${AUTO_DEPLOY,,}" != "true" ]]; then
    echo "Skipping Lambda deployment in production (set AUTO_DEPLOY_LAMBDAS=true to override)"
    return 0
  fi

  if [[ "${AUTO_DEPLOY,,}" == "false" ]]; then
    echo "Skipping Lambda deployment: AUTO_DEPLOY_LAMBDAS=false"
    return 0
  fi

  if ! command -v aws >/dev/null 2>&1; then
    echo "Skipping Lambda deployment: aws CLI not available"
    return 0
  fi


  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "Skipping Lambda deployment: AWS credentials not configured"
    return 0
  fi

  echo "Running automated Lambda deployment for environment '${LAMBDA_ENVIRONMENT}'..."
  if ! "${APP_ROOT}/scripts/deploy-lambdas.sh" "${LAMBDA_ENVIRONMENT}"; then
    echo "Lambda deployment failed; continuing startup. Check logs for details." >&2
  fi
}

run_migrations() {
  echo "Applying database migrations..."
  alembic upgrade head
}

seed_reference_data() {
  echo "Seeding reference data..."
  python populate_data.py
}

run_lambda_deploy
run_migrations
seed_reference_data

echo "Starting FastAPI service..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
