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


def es_desactualizado(dias: int = 1) -> bool:
    """Devuelve True si alguno de los juegos principales tiene resultados
    atrasados más de `dias` respecto a hoy (p. ej. un día completo)."""
    from backend.crud import get_rango_fechas
    db = SessionLocal()
    try:
        for juego in ["Pick 3", "Pick 4"]:
            _, max_fecha = get_rango_fechas(db, juego)
            if max_fecha is None or (date.today() - max_fecha).days >= dias:
                return True
        return False
    except Exception as e:
        _log(f"[ERROR] verificando desactualización: {e}")
        return True
    finally:
        db.close()


def catch_up_if_stale(dias: int = 1) -> bool:
    """Si los históricos están atrasados y no hay una actualización en curso,
    ejecuta run_update(). Devuelve True si se ejecutó la actualización."""
    if _running.is_set():
        _log("Actualización ya en curso — omitiendo recuperación")
        return False
    if not es_desactualizado(dias):
        _log("Históricos al día — no hace falta recuperación")
        return False
    _log("Históricos desactualizados — ejecutando recuperación")
    run_update()
    return True


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


# Horas (hora local del servidor; en Render = UTC) en que se ejecuta una
# actualización completa. Cada 3 horas para capturar el sorteo MIDDAY
# (~17:30–18:30 UTC) el mismo día y el EVENING (~00:57 UTC) a la madrugada.
# Horas UTC para captura robusta:
# - 01, 02, 03: ventana crítica EVENING (9pm ET = 01-02 UTC según DST)
# - 07, 10, 13: captura MIDDAY (1:30pm ET ≈ 17:30-18:30 UTC) al día siguiente
# - 16, 19, 22: refuerzo diario
UPDATE_HOURS = [1, 2, 3, 7, 10, 13, 16, 19, 22]


def _scheduler_loop():
    _log("Scheduler iniciado — actualización cada 3 h " + str(UPDATE_HOURS) + " + chequeo horario de recuperación")
    global _last_run_hour
    _last_run_hour = -1
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute

            if minute == 0 and hour != _last_run_hour:
                _last_run_hour = hour
                if hour in UPDATE_HOURS:
                    _log(f"Ejecutando actualización programada — {hour}:00")
                    run_update()
                else:
                    _log(f"Comprobando desactualización — {hour}:00")
                    catch_up_if_stale()

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
