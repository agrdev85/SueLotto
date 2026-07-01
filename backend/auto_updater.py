import os
import sys
import json
import threading
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from backend.database import SessionLocal, init_db
from backend.crud import bulk_insert_resultados, bulk_insert_posibles_salir
from backend.lottery_analyzer import obtener_posibles_salir
import importar_historicos
import actualizar_resultados

_scheduler = None
_lock = threading.Lock()
STATUS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "auto_update_status.json",
)
LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "auto_update.log",
)


def _log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _save_status(status: dict):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, default=str)


def _update_posibles_salir():
    _log("  Actualizando posible_salir...")
    db = SessionLocal()
    try:
        for juego in ["Pick 3", "Pick 4"]:
            for sorteo in ["E", "M"]:
                try:
                    resultado = obtener_posibles_salir(db, juego, date.today(), sorteo, use_ml=True)
                    if resultado["numeros"]:
                        registro = {
                            "fecha": date.today(),
                            "sorteo": sorteo,
                            "numeros": ",".join(str(n) for n in resultado["numeros"]),
                        }
                        bulk_insert_posibles_salir(db, [registro])
                        _log(f"    {juego} {sorteo}: {len(resultado['numeros'])} numeros guardados")
                    else:
                        _log(f"    {juego} {sorteo}: sin resultados")
                except Exception as e:
                    _log(f"    [ERROR] {juego} {sorteo}: {e}")
        _log("  [OK] posible_salir actualizado")
    except Exception as e:
        _log(f"  [ERROR] actualizar posible_salir: {e}")
    finally:
        db.close()


def run_update():
    _log("=== Auto-update iniciado ===")
    try:
        init_db()
        os.makedirs(importar_historicos.DATA_DIR, exist_ok=True)

        total = 0
        for juego in ["Pick 3", "Pick 4"]:
            nuevos = actualizar_resultados.actualizar_juego(juego)
            total += nuevos
            _log(f"  {juego}: {nuevos} nuevos registros")

        _update_posibles_salir()

        _save_status({
            "last_run": datetime.now().isoformat(),
            "total_new": total,
            "success": True,
        })
        _log(f"[OK] Auto-update completado. Total nuevos: {total}")
    except Exception as e:
        _log(f"[ERROR] Auto-update: {e}")
        _save_status({
            "last_run": datetime.now().isoformat(),
            "total_new": 0,
            "success": False,
            "error": str(e),
        })


def start():
    global _scheduler
    with _lock:
        if _scheduler is not None and _scheduler.running:
            _log("Scheduler ya está corriendo")
            return

        try:
            _scheduler = BackgroundScheduler()
            _scheduler.add_job(run_update, "date", run_date=datetime.now(), id="startup_update")
            for hour in [6, 12, 18, 23]:
                _scheduler.add_job(
                    run_update,
                    CronTrigger(hour=hour, minute=0),
                    id=f"daily_update_{hour}h",
                    replace_existing=True,
                )
            _scheduler.start()
            _log("Scheduler iniciado — actualización inmediata + diaria a las 06:00, 12:00, 18:00, 23:00")
        except Exception as e:
            _log(f"Error iniciando scheduler: {e}")


def get_status() -> dict:
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_run": None, "total_new": 0, "success": None}
