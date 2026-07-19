import subprocess, sys, os
VENV_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python3')
p = subprocess.Popen(
    [VENV_PY, '-m', 'streamlit', 'run', 'app/main.py', '--server.port', '8501', '--server.address', '0.0.0.0', '--server.headless', 'true'],
    stdout=open('/tmp/fe_final.out', 'w'),
    stderr=open('/tmp/fe_final.err', 'w'),
    start_new_session=True,
)
print(p.pid)
