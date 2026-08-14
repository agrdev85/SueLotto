#!/bin/bash
set -e

PORT=${PORT:-8501}
BACKEND_PORT=${BACKEND_PORT:-8000}
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$DIR/venv/bin/python3"

# Render no crea venv (instala con pip global): detectar e intentar con el
# intérprete del PATH (python3) para que funcione en cualquier entorno.
if [ -x "$VENV_PYTHON" ]; then
    PYTHON_BIN="$VENV_PYTHON"
    echo "Usando venv local: $PYTHON_BIN"
else
    PYTHON_BIN="$(command -v python3 || echo python3)"
    echo "venv no encontrado — usando python3 del PATH: $PYTHON_BIN"
fi

echo "=== SueñaLotto Startup ==="
echo "Backend port: $BACKEND_PORT"
echo "Frontend port: $PORT"
echo "Python: $PYTHON_BIN"
echo ""

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Start backend with nohup to survive shell.
# Logs a consola y a data/backend.log (para ver el arranque del scheduler).
mkdir -p "$DIR/data"
echo "=== backend boot $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$DIR/data/backend.log"
nohup "$PYTHON_BIN" -m uvicorn backend.main:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" \
    --log-level info > >(tee -a "$DIR/data/backend.log") 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend in foreground (main process)
echo "Starting frontend..."
exec "$PYTHON_BIN" -m streamlit run app/main.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true
