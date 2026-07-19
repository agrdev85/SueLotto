#!/usr/bin/env bash
cd /root/Documents/SueñaLotto
exec ./venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info
