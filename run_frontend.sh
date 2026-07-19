#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT=${PORT:-8501}
exec ./venv/bin/python3 -m streamlit run app/main.py --server.port "$PORT" --server.address 0.0.0.0
