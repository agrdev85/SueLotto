import os
import time
import logging
import threading
import httpx
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger("suenalotto.keepalive")

_keepalive_thread = None
_lock = threading.Lock()

LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "keepalive.log",
)


def _log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    logger.info("Keepalive: %s", msg)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _ping(url: str) -> bool:
    try:
        r = httpx.get(url, timeout=10)
        return r.status_code < 500
    except Exception:
        return False


def _keepalive_loop():
    interval = int(os.getenv("KEEPALIVE_INTERVAL", "600"))
    if interval < 120:
        interval = 120

    backend_port = os.getenv("BACKEND_PORT", "8000")
    local_url = f"http://localhost:{backend_port}/health"
    public_url = os.getenv("PUBLIC_URL", "").rstrip("/")

    if public_url:
        _log(f"Keepalive iniciado — ping local cada {interval}s y público {public_url}")
    else:
        _log(f"Keepalive iniciado — ping local cada {interval}s (PUBLIC_URL no configurada)")

    while True:
        try:
            ok_local = _ping(local_url)
            ok_public = True
            detail = f"local={'OK' if ok_local else 'FALLO'}"
            if public_url:
                ok_public = _ping(f"{public_url}/_stcore/health")
                detail += f" | público={'OK' if ok_public else 'FALLO'}"
            if ok_local and ok_public:
                _log(f"Ping OK — {detail}")
            else:
                _log(f"Ping con fallos — {detail}")
        except Exception as e:
            _log(f"[ERROR] en loop keepalive: {e}")
        time.sleep(interval)


def start():
    global _keepalive_thread
    with _lock:
        if _keepalive_thread is not None and _keepalive_thread.is_alive():
            return
        try:
            _keepalive_thread = threading.Thread(target=_keepalive_loop, daemon=True)
            _keepalive_thread.start()
            _log("Thread keepalive iniciado")
        except Exception as e:
            _log(f"Error iniciando thread keepalive: {e}")
