#!/bin/bash
# Starts both FastAPI (internal) and Streamlit (public on $PORT)

# FastAPI on internal port 8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info &

# Streamlit on Render's public port
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
