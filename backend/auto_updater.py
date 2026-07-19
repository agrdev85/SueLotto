import os
import sys
import json
import time
import threading
import logging
from datetime import datetime, date

scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from backend.database import SessionLocal, init_db
from backend.crud import bulk_insert_resultados, bulk_insert_posibles_salir
from backend.lottery_analyzer import obtener_posibles_salir
import importar_historicos
import actualizar_resultados

logger = logging.getLogger("suenalotto.autoupdater")

_scheduler_thread = None
_last_run_hour = -1
_lock = threading.Lock()
_running = threading.Event()

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
    logger.info("Auto-updater: %s", msg)
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
    if _running.is_set():
        _log("Actualización ya en curso — ignorando solicitud")
        return

    _running.set()
    _log("=== Auto-update iniciado ===")
    from backend.fl_scraper import scrape_and_store_other_games

    try:
        init_db()
        os.makedirs(importar_historicos.DATA_DIR, exist_ok=True)

        total = 0
        for juego in ["Pick 3", "Pick 4"]:
            nuevos = actualizar_resultados.actualizar_juego(juego)
            total += nuevos
            _log(f"  {juego}: {nuevos} nuevos registros")

        _update_posibles_salir()

        db = SessionLocal()
        try:
            games_count = scrape_and_store_other_games(db)
            _log(f"  Otros juegos: {games_count} actualizados")
        except Exception as e:
            _log(f"  [WARN] Otros juegos: {e}")
        finally:
            db.close()

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
    finally:
        _running.clear()


def _scheduler_loop():
    _log("Scheduler iniciado — esperando hora de ejecución (05:00–08:00)")
    global _last_run_hour
    _last_run_hour = -1
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            is_update_hour = hour in (5, 6, 7, 8)

            if is_update_hour and minute == 0:
                if hour != _last_run_hour:
                    _log(f"Ejecutando actualización programada — {hour}:00")
                    run_update()
                    _last_run_hour = hour

            if not is_update_hour:
                _last_run_hour = -1

        except Exception as e:
            _log(f"[ERROR] en loop scheduler: {e}")
        time.sleep(60)


def start():
    global _scheduler_thread
    with _lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            _log("Scheduler ya está corriendo")
            return
        try:
            _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
            _scheduler_thread.start()
            _log("Thread scheduler iniciado")
        except Exception as e:
            _log(f"Error iniciando thread scheduler: {e}")


def get_status() -> dict:
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_run": None, "total_new": 0, "success": None}
