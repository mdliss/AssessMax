#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TARGET_SCRIPT="${REPO_ROOT}/backend/scripts/deploy-lambdas.sh"

if [[ ! -f "${TARGET_SCRIPT}" ]]; then
  echo "Unable to locate backend/scripts/deploy-lambdas.sh from ${REPO_ROOT}" >&2
  exit 1
fi

exec "${TARGET_SCRIPT}" "$@"
