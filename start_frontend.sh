#!/usr/bin/env bash
cd /root/Documents/SueñaLotto
exec ./venv/bin/python3 -m streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
