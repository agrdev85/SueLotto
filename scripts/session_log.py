"""
Utilidad para crear y gestionar logs de sesion en history/.

Uso:
  python scripts/session_log.py init "Objetivo de la sesion"
  python scripts/session_log.py step "Descripcion del paso"
  python scripts/session_log.py done "Resumen final"

Genera archivos en history/YYYY-MM-DD_HHMMSS_<session-id>.md
"""

import sys
import os
import uuid
from datetime import datetime

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "history")
SESSION_FILE = None
SESSION_ID = None


def _get_session_id():
    return uuid.uuid4().hex[:12]


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _filename(session_id):
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return os.path.join(HISTORY_DIR, f"{ts}_{session_id}.md")


def cmd_init(goal: str):
    global SESSION_FILE, SESSION_ID
    SESSION_ID = _get_session_id()
    path = _filename(SESSION_ID)
    content = f"""# Sesion: {SESSION_ID}
- Fecha: {_timestamp()}
- Objetivo: {goal}

## Pasos realizados

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    SESSION_FILE = path
    print(f"[OK] Sesion iniciada: {path}")


def cmd_step(description: str):
    if not SESSION_FILE:
        # Try to find latest session
        if not os.path.exists(HISTORY_DIR):
            print("[ERROR] No hay sesion activa. Usa 'init' primero.")
            return
        files = sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith(".md") and f != "README.md"])
        if not files:
            print("[ERROR] No hay sesion activa. Usa 'init' primero.")
            return
        global SESSION_FILE, SESSION_ID
        SESSION_FILE = os.path.join(HISTORY_DIR, files[-1])
        SESSION_ID = files[-1].split("_", 2)[-1].replace(".md", "")
        print(f"[INFO] Continuando sesion: {SESSION_FILE}")

    with open(SESSION_FILE, "a", encoding="utf-8") as f:
        f.write(f"### {_timestamp()}\n{description}\n\n")
    print(f"[OK] Paso registrado")


def cmd_done(summary: str):
    if not SESSION_FILE:
        print("[ERROR] No hay sesion activa.")
        return
    with open(SESSION_FILE, "a", encoding="utf-8") as f:
        f.write(f"---\n**Completado:** {_timestamp()}\n{summary}\n")
    print(f"[OK] Sesion finalizada: {SESSION_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if cmd == "init":
        cmd_init(args or "Sin objetivo definido")
    elif cmd == "step":
        cmd_step(args or "Paso sin descripcion")
    elif cmd == "done":
        cmd_done(args or "Sin resumen")
    else:
        print(f"[ERROR] Comando desconocido: {cmd}")
        print(__doc__)
