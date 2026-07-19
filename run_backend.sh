#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT=${BACKEND_PORT:-8000}
exec ./venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --log-level info
