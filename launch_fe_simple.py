import subprocess, os, sys
VENV_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python3')
with open('/tmp/fe_simple.out', 'w') as out, open('/tmp/fe_simple.err', 'w') as err:
    p = subprocess.Popen(
        [VENV_PY, '-m', 'streamlit', 'run', 'app/main.py', '--server.port', '8501', '--server.address', '0.0.0.0', '--server.headless', 'true'],
        stdout=out, stderr=err, start_new_session=True,
    )
    sys.stdout.write(str(p.pid) + '\n')
    sys.stdout.flush()
