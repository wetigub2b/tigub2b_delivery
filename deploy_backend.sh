#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE="${ROOT_DIR}/.env"
LOG_DIR="${ROOT_DIR}/logs"
BFF_DIR="${ROOT_DIR}/bff"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[deploy_backend] Missing .env file at ${ENV_FILE}" >&2
  exit 1
fi

if [[ ! -d "${BFF_DIR}" ]]; then
  echo "[deploy_backend] bff directory not found" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${ENV_FILE}"
set +a

PYTHON_BIN=${PYTHON_BIN:-python3}
HOST=${BFF_HOST:-0.0.0.0}
PORT=${BFF_PORT:-8000}
WORKERS=${BFF_WORKERS:-1}

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[deploy_backend] Python interpreter not found: ${PYTHON_BIN}" >&2
  exit 1
fi

VENV_DIR="${BFF_DIR}/.venv"
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[deploy_backend] Creating virtualenv at ${VENV_DIR}" >&2
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

PIP_BIN="${VENV_DIR}/bin/pip"
UVICORN_BIN="${VENV_DIR}/bin/uvicorn"

if [[ ! -x "${PIP_BIN}" ]]; then
  echo "[deploy_backend] pip not found inside ${VENV_DIR}" >&2
  exit 1
fi

REQUIREMENTS_FILE="${BFF_DIR}/requirements.txt"
STAMP_FILE="${VENV_DIR}/.deps-installed"
INSTALL_DEPS=false

if [[ ! -f "${STAMP_FILE}" ]]; then
  INSTALL_DEPS=true
elif [[ "${REQUIREMENTS_FILE}" -nt "${STAMP_FILE}" ]]; then
  INSTALL_DEPS=true
fi

if [[ "${INSTALL_DEPS}" == true ]]; then
  echo "[deploy_backend] Installing backend dependencies" >&2
  "${PIP_BIN}" install --upgrade pip >/dev/null || true
  if ! "${PIP_BIN}" install -r "${REQUIREMENTS_FILE}"; then
    echo "[deploy_backend] Failed to install dependencies. Check network access or package index." >&2
    exit 1
  fi
  touch "${STAMP_FILE}"
fi

if [[ ! -x "${UVICORN_BIN}" ]]; then
  echo "[deploy_backend] uvicorn not available in virtualenv (expected at ${UVICORN_BIN})" >&2
  exit 1
fi

if ! [[ "${WORKERS}" =~ ^[0-9]+$ ]]; then
  WORKERS=1
fi

EXISTING_PIDS=$(pgrep -f "uvicorn app.main:app.*--port ${PORT}" || true)
if [[ -n "${EXISTING_PIDS}" ]]; then
  echo "[deploy_backend] Stopping existing FastAPI process: ${EXISTING_PIDS}" >&2
  pkill -9 -f "uvicorn app.main:app.*--port ${PORT}" || true
  sleep 2
fi

mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/bff.log"
PID_FILE="${LOG_DIR}/bff.pid"

pushd "${BFF_DIR}" >/dev/null
CMD=("${UVICORN_BIN}" "app.main:app" "--host" "${HOST}" "--port" "${PORT}")
if [[ "${WORKERS}" -gt 1 ]]; then
  CMD+=("--workers" "${WORKERS}")
fi

nohup "${CMD[@]}" >"${LOG_FILE}" 2>&1 &
NEW_PID=$!

echo "${NEW_PID}" >"${PID_FILE}"

popd >/dev/null

echo "[deploy_backend] FastAPI running (PID ${NEW_PID}) on ${HOST}:${PORT}. Logs: ${LOG_FILE}"
