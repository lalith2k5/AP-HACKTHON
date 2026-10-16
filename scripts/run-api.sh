#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
[ -f .env ] && source .env
set +a
exec .venv/bin/uvicorn storesignal.api:app --port 8790 --reload
