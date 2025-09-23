#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[deploy_frontend] Missing .env file at ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${WEB_ROOT:-}" ]]; then
  echo "[deploy_frontend] WEB_ROOT is not defined in .env" >&2
  exit 1
fi

FRONTEND_DIR="${ROOT_DIR}/frontend"
if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "[deploy_frontend] frontend directory not found" >&2
  exit 1
fi

pushd "${FRONTEND_DIR}" >/dev/null

if ! command -v npm >/dev/null 2>&1; then
  echo "[deploy_frontend] npm is not available" >&2
  exit 1
fi

if [[ ! -d node_modules ]]; then
  echo "[deploy_frontend] Installing dependencies" >&2
  npm install
fi

npm run build

popd >/dev/null

TARGET_DIR="${WEB_ROOT%/}"
mkdir -p "${TARGET_DIR}"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "${FRONTEND_DIR}/dist/" "${TARGET_DIR}/"
else
  rm -rf "${TARGET_DIR:?}"/*
  cp -r "${FRONTEND_DIR}/dist"/* "${TARGET_DIR}/"
fi

echo "[deploy_frontend] Deployed build to ${TARGET_DIR}"
