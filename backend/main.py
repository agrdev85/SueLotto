import os
import sys
import time
import json
import secrets
import logging
import threading
from fastapi import FastAPI, Depends, Query, HTTPException, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from backend.logging_config import logger
from backend.database import init_db, get_db, SessionLocal
from backend.schemas import MatrizRequest, SecuenciaRequest, CompararRequest
from backend.auth import hash_password, verify_password, create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models import User, Bet, UserUsage
from backend.crud import (
    get_ultimos_resultados, get_resultados_historicos, get_frecuencias,
    get_atrasados, get_adivinanza_hoy, get_posibles_salir,
    get_charada_enriquecida, get_charada_frecuencias,
)
from backend.lottery_analyzer import generar_predicciones, calcular_numeros_calientes, obtener_posibles_salir
from backend.charada_engine import buscar_en_sueno
from backend.adivinanza_ai import analizar_adivinanza
from backend.matrix_engine import obtener_numeros_alrededor, procesar_secuencia, comparar_y_reducir
from backend.auto_updater import start as start_auto_updater, catch_up_if_stale
from backend.keepalive import start as start_keepalive
from backend.fl_scraper import scrape_other_games
from backend.rate_limit import RateLimitMiddleware
from backend.email_service import (
    send_verification_email, send_password_reset,
    send_welcome_email, send_payment_receipt, send_contact_message,
    send_expiry_reminder,
    is_configured as email_configured,
)
from backend.qvapay import create_payment_url, process_webhook, verify_webhook, is_configured as qvapay_configured, PLANS, get_promo_info, increment_promo_purchases
from backend.db_manager import (
    export_db, import_db, run_backup, list_backups, restore_backup,
    delete_backup, get_backup_status, start_backup_scheduler,
    get_tables_meta, get_records, create_record, update_record, delete_record,
)

app = FastAPI(title="SueñaLotto API", version="2.0.0")

_history_lock = threading.Lock()
_history_loaded = False
_history_importing = False

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXPIRY_EMAIL_FILE = os.path.join(_BASE_DIR, "data", "expiry_email_log.json")
_expiry_email_lock = threading.Lock()


def _maybe_send_expiry_email(user, days_remaining: int):
    if not email_configured() or days_remaining > 5 or days_remaining < 1:
        return
    key = f"{user.id}_{user.tier_expires}"
    with _expiry_email_lock:
        try:
            if os.path.exists(_EXPIRY_EMAIL_FILE):
                with open(_EXPIRY_EMAIL_FILE, "r") as f:
                    log = json.load(f)
            else:
                log = {}
        except Exception:
            log = {}
        if log.get(str(user.id)) == key:
            return
        sent = send_expiry_reminder(user.email, user.username, days_remaining)
        if sent:
            log[str(user.id)] = key
            try:
                os.makedirs(os.path.dirname(_EXPIRY_EMAIL_FILE), exist_ok=True)
                with open(_EXPIRY_EMAIL_FILE, "w") as f:
                    json.dump(log, f)
            except Exception:
                pass

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Intenta de nuevo."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ─── Startup ───────────────────────────────────────────────────────

# Estado persistente de la última repoblación manual (para la UI del admin)
_POPULATE_STATUS_FILE = os.path.join(_BASE_DIR, "data", "populate_status.json")
_populate_lock = threading.Lock()


def _save_populate_status(data: dict):
    try:
        os.makedirs(os.path.dirname(_POPULATE_STATUS_FILE), exist_ok=True)
        with open(_POPULATE_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning("No se pudo guardar populate_status: %s", e)


def _load_populate_status() -> dict:
    try:
        if os.path.exists(_POPULATE_STATUS_FILE):
            with open(_POPULATE_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("No se pudo leer populate_status: %s", e)
    return {}


# ─── Lazy history import ─────────────────────────────────────────────

_LAZY_RETRIES = 3
_LAZY_RETRY_DELAY = 5


def _lazy_import_history():
    global _history_importing
    try:
        logger.info("Lazy import: starting historical PDF import")
        _history_importing = True
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import actualizar_resultados
        for juego in ["Pick 3", "Pick 4"]:
            for intento in range(1, _LAZY_RETRIES + 1):
                try:
                    completado = actualizar_resultados.importar_historial_si_falta(juego)
                    logger.info("Lazy import %s: completo=%s (intento %s)", juego, completado, intento)
                    if not completado or not actualizar_resultados.falta_historial_alguna():
                        break
                except Exception as e:
                    logger.error("Lazy import %s failed (intento %s/%s): %s",
                                 juego, intento, _LAZY_RETRIES, e, exc_info=True)
                time.sleep(_LAZY_RETRY_DELAY)
        logger.info("Lazy import: historical results import completed")
    except Exception as e:
        logger.error("Lazy import failed: %s", e, exc_info=True)
    finally:
        global _history_loaded
        _history_loaded = True
        _history_importing = False


def _ensure_history_loaded():
    """Llamar en endpoints que necesitan datos históricos.
    Si no se ha cargado aún, lanza la importación en background."""
    global _history_importing
    if _history_loaded:
        return
    with _history_lock:
        if _history_loaded:
            return
        if not _history_importing:
            _history_importing = True
            t = threading.Thread(target=_lazy_import_history, daemon=True)
            t.start()


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        from backend.models import Charada, Resultado
        db = SessionLocal()
        try:
            if db.query(Charada).count() == 0:
                logger.info("Charada table empty — importing from data/charada.json")
                from backend.charada_engine import poblar_charada_db
                try:
                    count = poblar_charada_db(db)
                    logger.info("Charada imported: %d records", count)
                except Exception as e:
                    logger.error("Charada import failed: %s", e)
        finally:
            db.close()
        start_auto_updater()
        start_keepalive()
        start_backup_scheduler()
        threading.Thread(target=_ensure_history_loaded, daemon=True).start()
        def _delayed_catch_up():
            time.sleep(20)
            try:
                catch_up_if_stale()
            except Exception as e:
                logger.error("Catch-up de históricos falló: %s", e)
        threading.Thread(target=_delayed_catch_up, daemon=True).start()
        logger.info("SueñaLotto API started")
        if not email_configured():
            logger.warning("SMTP not configured — emails disabled")
        if not qvapay_configured():
            logger.warning("Qvapay not configured — payments disabled")
    except Exception as e:
        logger.error("Startup error: %s", e)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/api/system/history-status")
def api_history_status():
    """Estado del histórico con conteos y rangos de fechas reales por juego.
    Usado por el Gestor BD para verificar que la carga desde PDF quedó completa."""
    juegos = {}
    try:
        import actualizar_resultados
        for j in ("Pick 3", "Pick 4"):
            try:
                juegos[j] = actualizar_resultados._stats_juego(j)
            except Exception as e:
                logger.warning("history-status %s falló: %s", j, e)
                juegos[j] = {"count": 0, "min_fecha": None, "max_fecha": None, "completo": False, "error": str(e)}
    except Exception as e:
        logger.warning("history-status: %s", e)
    return {
        "loaded": _history_loaded,
        "importing": _history_importing,
        "juegos": juegos,
        "last_populate": _load_populate_status(),
    }


# ─── Admin Endpoints (authenticated) ────────────────────────────────

def _require_admin(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    admin_token = os.getenv("ADMIN_API_TOKEN", "")
    if admin_token and authorization == f"Bearer {admin_token}":
        return None
    if not authorization:
        raise HTTPException(401, "Se requiere autenticación")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Token inválido")
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(401, "Token inválido o expirado")
        user = db.query(User).filter(User.username == payload.get("sub")).first()
        if not user or user.tier != "admin":
            raise HTTPException(403, "No tienes permisos de administrador")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Error de autenticación")


@app.get("/api/admin/update-status")
def api_update_status(admin: User = Depends(_require_admin)):
    from backend.auto_updater import get_status
    return get_status()


@app.post("/api/admin/update")
def api_trigger_update(admin: User = Depends(_require_admin)):
    from backend.auto_updater import run_update
    run_update()
    return {"status": "ok", "detail": "Actualización ejecutada"}


@app.post("/api/admin/set-tier")
def api_admin_set_tier(
    data: dict = Body(...),
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    username = data.get("username", "").strip()
    new_tier = data.get("tier", "free").strip().lower()
    if new_tier not in ("free", "pro", "lifetime", "admin"):
        raise HTTPException(400, "Plan inválido: free, pro, lifetime, admin")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    user.tier = new_tier
    if new_tier == "pro":
        user.tier_expires = date.today() + timedelta(days=30)
    elif new_tier in ("lifetime", "admin", "free"):
        user.tier_expires = None
    db.commit()
    logger.info("Admin set tier: %s -> %s (expires=%s)", username, new_tier, user.tier_expires)
    return {"status": "ok", "username": username, "tier": new_tier, "tier_expires": user.tier_expires.isoformat() if user.tier_expires else None}


# ─── Admin: Gestor de Base de Datos ─────────────────────────────────

@app.get("/api/admin/db/tables")
def api_db_tables(admin: User = Depends(_require_admin)):
    return get_tables_meta()


@app.get("/api/admin/db/{table}/records")
def api_db_records(
    table: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    try:
        return get_records(db, table, page, size)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/api/admin/db/{table}/records")
def api_db_create_record(
    table: str,
    data: dict = Body(...),
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    try:
        return create_record(db, table, data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.put("/api/admin/db/{table}/records/{record_id}")
def api_db_update_record(
    table: str,
    record_id: int,
    data: dict = Body(...),
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    try:
        return update_record(db, table, record_id, data)
    except ValueError as e:
        raise HTTPException(404 if "no encontrado" in str(e) else 400, str(e))


@app.delete("/api/admin/db/{table}/records/{record_id}")
def api_db_delete_record(
    table: str,
    record_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    try:
        return delete_record(db, table, record_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/api/admin/db/export")
def api_db_export(admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    return export_db(db)


@app.post("/api/admin/db/import")
def api_db_import(
    data: dict = Body(...),
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    mode = data.get("mode", "replace")
    payload = data.get("data") or data
    try:
        return import_db(payload, mode=mode, db=db)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error("Import de BD falló: %s", e)
        raise HTTPException(400, f"Error al importar: {e}")


@app.post("/api/admin/db/populate-historical")
def api_db_populate_historical(
    data: dict = Body(default={}),
    admin: User = Depends(_require_admin),
):
    """Repobla el histórico (Pick 3/Pick 4) desde el PDF oficial.
    - juego: "Pick 3" | "Pick 4" | null → ambos
    - fuerza: True fuerza la descarga/inserción aunque el histórico exista.
    Devuelve un reporte con conteos y rangos de fechas por juego."""
    juego = data.get("juego") or None
    fuerza = bool(data.get("fuerza", False))
    if juego and juego not in ("Pick 3", "Pick 4"):
        raise HTTPException(400, "juego debe ser 'Pick 3' o 'Pick 4'")
    if not _populate_lock.acquire(blocking=False):
        raise HTTPException(409, "Ya hay una repoblación en curso. Intenta en unos minutos.")
    try:
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import actualizar_resultados
        reporte = actualizar_resultados.repoblar_historial(juego=juego, fuerza=fuerza)
        reporte["ejecutado"] = datetime.now().isoformat()
        _save_populate_status(reporte)
        return reporte
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Repoblación histórica falló: %s", e, exc_info=True)
        raise HTTPException(500, f"Error al repoblar históricos: {e}")
    finally:
        _populate_lock.release()


@app.get("/api/admin/db/populate-historical/status")
def api_db_populate_status(admin: User = Depends(_require_admin)):
    """Último resultado de la repoblación histórica (sin volver a ejecutarla)."""
    return _load_populate_status()


@app.get("/api/admin/db/backups")
def api_db_list_backups(admin: User = Depends(_require_admin)):
    return list_backups()


@app.post("/api/admin/db/backups/run")
def api_db_backup_now(admin: User = Depends(_require_admin)):
    return run_backup(manual=True)


@app.get("/api/admin/db/backup-status")
def api_db_backup_status(admin: User = Depends(_require_admin)):
    return get_backup_status()


@app.post("/api/admin/db/backups/{filename}/restore")
def api_db_restore_backup(
    filename: str,
    admin: User = Depends(_require_admin),
):
    try:
        return restore_backup(filename)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.delete("/api/admin/db/backups/{filename}")
def api_db_delete_backup(
    filename: str,
    admin: User = Depends(_require_admin),
):
    try:
        return delete_backup(filename)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ─── Results ────────────────────────────────────────────────────────

@app.get("/api/resultados/ultimos")
def api_ultimos_resultados(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_ultimos_resultados(db, juego, sorteo, limit)


@app.get("/api/resultados/por-fecha")
def api_resultados_por_fecha(fecha: date, db: Session = Depends(get_db)):
    from backend.models import Resultado
    resultados = db.query(Resultado).filter(Resultado.fecha == fecha).order_by(Resultado.juego, Resultado.sorteo).all()
    return [
        {
            "id": r.id,
            "fecha": r.fecha.isoformat(),
            "juego": r.juego,
            "sorteo": r.sorteo,
            "n1": r.n1,
            "n2": r.n2,
            "n3": r.n3,
            "n4": r.n4,
        }
        for r in resultados
    ]


@app.get("/api/resultados/ultima-fecha")
def api_ultima_fecha(db: Session = Depends(get_db)):
    from backend.models import Resultado
    ultimo = db.query(Resultado).order_by(Resultado.fecha.desc()).first()
    if ultimo:
        return {"fecha": ultimo.fecha.isoformat()}
    return {"fecha": date.today().isoformat()}


@app.get("/api/resultados/otros-juegos")
def api_otros_juegos(db: Session = Depends(get_db)):
    from backend.crud import get_other_games
    from backend.fl_api import GAME_ORDER

    games = get_other_games(db, limit=100)
    if games:
        latest_by_game = {}
        for g in games:
            cur = latest_by_game.get(g.game_name)
            if cur is None or (g.fecha and cur.fecha and g.fecha > cur.fecha):
                latest_by_game[g.game_name] = g
        order = {name: i for i, name in enumerate(GAME_ORDER)}
        ordered = sorted(
            latest_by_game.values(),
            key=lambda g: order.get(g.game_name, 99),
        )
        return [
            {
                "name": g.game_name,
                "date": g.drawing_date or "",
                "numbers": g.numbers.split(",") if g.numbers else [],
                "extra": g.extra.split(",") if g.extra else [],
            }
            for g in ordered
        ]
    return scrape_other_games()


@app.get("/api/resultados/historicos")
def api_historicos(
    juego: Optional[str] = Query(None, pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    contienen_digitos: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    results, total = get_resultados_historicos(
        db, juego, sorteo, fecha_inicio, fecha_fin, contienen_digitos, page, size
    )
    return {
        "data": [
            {
                "id": r.id,
                "fecha": r.fecha.isoformat(),
                "juego": r.juego,
                "sorteo": r.sorteo,
                "n1": r.n1,
                "n2": r.n2,
                "n3": r.n3,
                "n4": r.n4,
            }
            for r in results
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total else 0,
    }


# ─── Statistics ─────────────────────────────────────────────────────

@app.get("/api/estadisticas/frecuencias")
def api_frecuencias(
    juego: Optional[str] = Query(None),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    dias: int = 30,
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    return get_frecuencias(db, juego, sorteo, dias)


@app.get("/api/estadisticas/atrasados")
def api_atrasados(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    return get_atrasados(db, juego, sorteo)


@app.get("/api/predicciones")
def api_predicciones(
    juego: Optional[str] = Query(None),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    return generar_predicciones(db, juego, sorteo)


@app.get("/api/estadisticas/calientes")
def api_calientes(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    limite: int = Query(20, ge=1, le=100),
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    return calcular_numeros_calientes(db, juego, sorteo, limite, dias)


@app.get("/api/estadisticas/posibles-salir")
def api_posibles_salir(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    fecha: Optional[date] = None,
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    use_ml: bool = Query(True),
    db: Session = Depends(get_db),
):
    _ensure_history_loaded()
    return obtener_posibles_salir(db, juego, fecha, sorteo, use_ml)


@app.get("/api/estadisticas/predicciones")
def api_estadisticas_predicciones(
    juego: Optional[str] = Query(None),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    db: Session = Depends(get_db),
):
    return generar_predicciones(db, juego, sorteo)


@app.get("/api/estadisticas/charada-frecuencias")
def api_charada_frecuencias(
    juego: str = Query("Pick 3", pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    dias: int = 90,
    db: Session = Depends(get_db),
):
    return get_charada_frecuencias(db, juego, sorteo, dias)


# ─── Charada & Adivinanza ──────────────────────────────────────────

@app.post("/api/charada/buscar")
def api_charada_buscar(texto: str = Body(..., embed=True), db: Session = Depends(get_db)):
    if not texto or not texto.strip():
        raise HTTPException(status_code=400, detail="Texto de sueño requerido")
    resultados = buscar_en_sueno(db, texto)
    return {"texto_original": texto, "resultados": resultados}


@app.get("/api/adivinanza/hoy")
def api_adivinanza_hoy(db: Session = Depends(get_db)):
    adivinanza = get_adivinanza_hoy(db)
    if not adivinanza:
        return {"fecha": date.today().isoformat(), "texto": "Hoy no hay adivinanza disponible. ¡Vuelve mañana!"}
    return adivinanza


@app.post("/api/adivinanza/analizar")
def api_adivinanza_analizar(adivinanza: str = Body(...), interpretacion: str = Body(...)):
    if not adivinanza or not interpretacion:
        raise HTTPException(status_code=400, detail="Adivinanza e interpretación requeridas")
    return analizar_adivinanza(adivinanza, interpretacion)


@app.get("/api/ia/status")
def api_ia_status():
    from backend.adivinanza_ai import gemini_activo
    return {
        "gemini_disponible": gemini_activo(),
        "gemini_api_key_configurada": bool(os.getenv("GEMINI_API_KEY", "")),
    }


@app.get("/api/charada/enriquecida")
def api_charada_enriquecida(numero: Optional[int] = Query(None, ge=1, le=100), db: Session = Depends(get_db)):
    return get_charada_enriquecida(db, numero)


# ─── Matriz ─────────────────────────────────────────────────────────

@app.post("/api/matriz/alrededor")
def api_matriz_alrededor(req: MatrizRequest, db: Session = Depends(get_db)):
    try:
        numeros = obtener_numeros_alrededor(req.numero, req.tipo_matriz)
        return {"numero": req.numero, "tipo_matriz": req.tipo_matriz, "numeros": numeros, "total": len(numeros)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/matriz/secuencia")
def api_matriz_secuencia(req: SecuenciaRequest, db: Session = Depends(get_db)):
    try:
        numeros = procesar_secuencia(req.secuencia, req.tipo_matriz)
        return {"secuencia": req.secuencia, "tipo_matriz": req.tipo_matriz, "numeros": numeros, "total": len(numeros)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/matriz/comparar")
def api_matriz_comparar(req: CompararRequest, db: Session = Depends(get_db)):
    try:
        resultado = comparar_y_reducir(
            req.secuencia, req.tipo_matriz, req.calientes, req.posibles,
            db=db, juego=req.juego, sorteo=req.sorteo, limite=req.limite,
            modo=req.modo,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Auth ───────────────────────────────────────────────────────────

PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))


def _get_user_from_token(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        payload = decode_token(token)
        if payload is None:
            return None
        return db.query(User).filter(User.username == payload.get("sub")).first()
    except Exception:
        return None


def _require_user(current_user: Optional[User] = Depends(_get_user_from_token)):
    if not current_user:
        raise HTTPException(401, "No autenticado")
    return current_user


@app.post("/api/auth/register")
def api_register(data: dict = Body(...), db: Session = Depends(get_db)):
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    tier = data.get("tier", "free").strip().lower()

    if tier not in ("free", "pro", "lifetime"):
        tier = "free"

    if not username or not email or not password:
        raise HTTPException(400, "Todos los campos son requeridos")
    if len(username) < 3:
        raise HTTPException(400, "El usuario debe tener al menos 3 caracteres")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(400, f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres")
    if "@" not in email or "." not in email:
        raise HTTPException(400, "Email inválido")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "El nombre de usuario ya existe")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "El email ya está registrado")

    email_token = secrets.token_urlsafe(32)
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        tier=tier,
        tier_expires=date.today() + timedelta(days=30) if tier == "pro" else None,
        email_verified=False,
        email_verification_token=email_token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_verification_email(email, email_token)
    send_welcome_email(email, username)

    token = create_access_token({"sub": user.username})
    logger.info("New user registered: %s (%s, %s)", username, email, tier)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tier": user.tier,
            "email_verified": user.email_verified,
        },
    }


@app.post("/api/auth/login")
def api_login(data: dict = Body(...), db: Session = Depends(get_db)):
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(400, "Usuario y contraseña requeridos")

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for: %s", username)
        raise HTTPException(401, "Usuario o contraseña incorrectos")

    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tier": user.tier,
            "email_verified": user.email_verified,
            "tier_expires": user.tier_expires.isoformat() if user.tier_expires else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@app.post("/api/auth/refresh")
def api_refresh_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization:
        raise HTTPException(401, "Token requerido")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Scheme inválido")
    except ValueError:
        raise HTTPException(401, "Formato de autorización inválido")

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(401, "Token inválido o expirado")

    username = payload.get("sub")
    if not username:
        raise HTTPException(401, "Token inválido")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(401, "Usuario no encontrado")

    new_token = create_access_token({"sub": user.username})
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/api/auth/profile")
def api_profile(current_user: User = Depends(_require_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "tier": current_user.tier,
        "email_verified": current_user.email_verified,
        "tier_expires": current_user.tier_expires.isoformat() if current_user.tier_expires else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@app.get("/api/auth/tier")
def api_check_tier(
    current_user: Optional[User] = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
):
    tier = current_user.tier if current_user else "free"

    now = date.today()
    if tier == "pro" and current_user and current_user.tier_expires and current_user.tier_expires < now:
        tier = "free"
        current_user.tier = "free"
        db.commit()

    days_remaining = None
    expiring_soon = False
    if current_user and current_user.tier_expires and tier in ("pro",):
        delta = (current_user.tier_expires - now).days
        days_remaining = max(delta, 0)
        expiring_soon = 0 < delta <= 5
        if expiring_soon:
            _maybe_send_expiry_email(current_user, days_remaining)

    can_use_historica = tier in ("free", "trial", "pro", "lifetime", "admin")
    can_use_suenos = tier in ("free", "trial", "pro", "lifetime", "admin")
    can_use_adivinanzas = tier in ("pro", "lifetime", "admin")
    can_use_matriz = tier in ("pro", "lifetime", "admin")

    suenos_today = 0
    suenos_limit = 999
    historica_today = 0
    historica_limit = 999
    if tier in ("free", "trial"):
        suenos_limit = 1
        historica_limit = 3
        if current_user:
            usage = db.query(UserUsage).filter(
                UserUsage.user_id == current_user.id,
                UserUsage.fecha == date.today(),
            ).first()
            if usage:
                suenos_today = usage.charada_count
                historica_today = usage.historica_count

    return {
        "tier": tier,
        "can_use_historica": can_use_historica,
        "can_use_suenos": can_use_suenos,
        "can_use_adivinanzas": can_use_adivinanzas,
        "can_use_matriz": can_use_matriz,
        "suenos_today": suenos_today,
        "suenos_limit": suenos_limit,
        "historica_today": historica_today,
        "historica_limit": historica_limit,
        "tier_expires": current_user.tier_expires.isoformat() if current_user and current_user.tier_expires else None,
        "days_remaining": days_remaining,
        "expiring_soon": expiring_soon,
    }


# ─── Soporte / Contacto ────────────────────────────────────────────

@app.post("/api/support/contact")
def api_support_contact(
    data: dict = Body(...),
    current_user: Optional[User] = Depends(_get_user_from_token),
):
    name = str(data.get("name", "")).strip()[:100]
    contact = str(data.get("contact", "")).strip()[:200]
    subject = str(data.get("subject", "Consulta general")).strip()[:200]
    message = str(data.get("message", "")).strip()[:4000]

    if not message:
        raise HTTPException(400, "El mensaje no puede estar vacío")
    if not contact:
        raise HTTPException(400, "Indica un medio de contacto (email, WhatsApp, Telegram, etc.)")
    if not email_configured():
        raise HTTPException(503, "El canal de soporte por email no está configurado aún. Intenta más tarde.")

    ok = send_contact_message(
        name or "Anónimo",
        contact,
        subject,
        message,
        username=current_user.username if current_user else "",
    )
    if not ok:
        raise HTTPException(503, "No se pudo enviar el mensaje. Intenta de nuevo.")
    logger.info("Support contact received from %s (%s): %s", name, contact, subject)
    return {"status": "sent", "message": "Mensaje enviado. Te responderemos pronto."}


# ─── Email Verification ────────────────────────────────────────────

@app.get("/api/auth/verify-email")
def api_verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(404, "Token de verificación inválido o expirado")
    user.email_verified = True
    user.email_verification_token = None
    db.commit()
    logger.info("Email verified for user: %s", user.username)
    return {"status": "ok", "message": "Email verificado correctamente"}


@app.post("/api/auth/resend-verification")
def api_resend_verification(current_user: User = Depends(_require_user)):
    if current_user.email_verified:
        return {"status": "ok", "message": "Email ya verificado"}
    if not current_user.email_verification_token:
        current_user.email_verification_token = secrets.token_urlsafe(32)
        from backend.database import SessionLocal
        sess = SessionLocal()
        sess.add(current_user)
        sess.commit()
        sess.close()
    send_verification_email(current_user.email, current_user.email_verification_token)
    return {"status": "ok", "message": "Email de verificación reenviado"}


# ─── Password Reset ────────────────────────────────────────────────

@app.post("/api/auth/forgot-password")
def api_forgot_password(data: dict = Body(...), db: Session = Depends(get_db)):
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "Email requerido")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "ok", "message": "Si el email existe, recibirás instrucciones"}
    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    send_password_reset(email, reset_token)
    logger.info("Password reset sent for: %s", email)
    return {"status": "ok", "message": "Si el email existe, recibirás instrucciones"}


@app.post("/api/auth/reset-password")
def api_reset_password(data: dict = Body(...), db: Session = Depends(get_db)):
    token = data.get("token", "").strip()
    new_password = data.get("password", "")
    if not token or not new_password:
        raise HTTPException(400, "Token y nueva contraseña requeridos")
    if len(new_password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(400, f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres")
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        raise HTTPException(404, "Token inválido")
    if user.password_reset_expires and datetime.utcnow() > user.password_reset_expires:
        raise HTTPException(400, "Token expirado. Solicita uno nuevo.")
    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    logger.info("Password reset completed for: %s", user.username)
    return {"status": "ok", "message": "Contraseña actualizada correctamente"}


# ─── Usage ─────────────────────────────────────────────────────────

@app.post("/api/usage/busqueda")
def api_increment_busqueda_usage(current_user: User = Depends(_require_user), db: Session = Depends(get_db)):
    today = date.today()
    tier_info = api_check_tier(current_user, db)
    if tier_info["suenos_today"] >= tier_info["suenos_limit"]:
        raise HTTPException(429, "Límite diario alcanzado para búsquedas de sueños")
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == current_user.id,
        UserUsage.fecha == today,
    ).first()
    if not usage:
        usage = UserUsage(user_id=current_user.id, fecha=today, charada_count=1)
        db.add(usage)
    else:
        usage.charada_count += 1
    db.commit()
    return {"suenos_today": usage.charada_count}


@app.post("/api/usage/historica")
def api_increment_historica_usage(current_user: User = Depends(_require_user), db: Session = Depends(get_db)):
    today = date.today()
    tier_info = api_check_tier(current_user, db)
    if tier_info["historica_today"] >= tier_info["historica_limit"]:
        raise HTTPException(429, "Límite diario alcanzado para búsquedas históricas")
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == current_user.id,
        UserUsage.fecha == today,
    ).first()
    if not usage:
        usage = UserUsage(user_id=current_user.id, fecha=today, historica_count=1)
        db.add(usage)
    else:
        usage.historica_count += 1
    db.commit()
    return {"historica_today": usage.historica_count}


# ─── Payments ─────────────────────────────────────────────────────

@app.get("/api/payments/plans")
def api_get_plans():
    promo = get_promo_info()
    return {
        "plans": {
            pid: {
                "name": p["name"],
                "amount": promo["price"] if pid == "lifetime" and promo["active"] else p["amount"],
                "currency": p["currency"],
                "days": p["days"],
            }
            for pid, p in PLANS.items()
        },
        "qvapay_configured": qvapay_configured(),
        "promo": promo,
    }


@app.post("/api/payments/create")
def api_create_payment(
    data: dict = Body(...),
    current_user: User = Depends(_require_user),
):
    plan_id = data.get("plan", "").strip().lower()
    if plan_id not in PLANS:
        raise HTTPException(400, "Plan inválido")
    if current_user.tier == "lifetime":
        raise HTTPException(400, "Ya tienes el plan De por Vida")
    if current_user.tier == "pro" and plan_id == "pro":
        raise HTTPException(400, "Ya tienes el plan Pro")

    result = create_payment_url(
        plan_id=plan_id,
        username=current_user.username,
        email=current_user.email,
        user_id=current_user.id,
    )
    if not result:
        raise HTTPException(503, "No se pudo crear el pago. Intenta de nuevo más tarde.")
    return result


@app.post("/api/payments/webhook")
async def api_payments_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Qvapay-Signature", "")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    is_prod = os.getenv("ENVIRONMENT", "").lower() == "production"
    if is_prod and not signature:
        logger.warning("Qvapay webhook missing signature in production")
        raise HTTPException(401, "Missing signature")
    if signature and not verify_webhook(data, signature):
        logger.warning("Qvapay webhook invalid signature")
        raise HTTPException(401, "Invalid signature")

    result = process_webhook(data)
    if result and result.get("action") == "activate":
        from backend.database import SessionLocal
        sess = SessionLocal()
        try:
            user = sess.query(User).filter(User.id == result["user_id"]).first()
            if user:
                plan = PLANS.get(result["plan_id"])
                if plan:
                    user.tier = result["plan_id"]
                    user.tier_expires = date.today() + timedelta(days=plan["days"])
                    sess.commit()
                    logger.info(
                        "Payment activated: user=%s plan=%s expires=%s",
                        user.username, result["plan_id"], user.tier_expires,
                    )
                    send_payment_receipt(
                        user.email, user.username,
                        plan["name"], f"${plan['amount']:.2f}",
                        result.get("payment_id", ""),
                    )
                    if result["plan_id"] == "lifetime":
                        total = increment_promo_purchases()
                        logger.info("Lifetime promo counter: %d", total)
        except Exception as e:
            logger.error("Webhook activation error: %s", e)
            sess.rollback()
        finally:
            sess.close()

    return {"status": "ok"}


# ─── Bets ─────────────────────────────────────────────────────────

@app.get("/api/bets")
def api_get_bets(current_user: User = Depends(_require_user), db: Session = Depends(get_db)):
    bets = db.query(Bet).filter(Bet.user_id == current_user.id).order_by(Bet.fecha.desc()).all()
    return [
        {
            "id": b.id,
            "fecha": b.fecha.isoformat(),
            "turno": b.turno,
            "juego": b.juego,
            "numeros": b.numeros,
            "fijo": b.fijo,
            "corrido": b.corrido,
            "parle": b.parle,
            "candado": b.candado,
            "precio": b.precio,
            "descripcion": b.descripcion,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bets
    ]


@app.post("/api/bets")
def api_create_bet(
    data: dict = Body(...),
    current_user: User = Depends(_require_user),
    db: Session = Depends(get_db),
):
    bet = Bet(
        user_id=current_user.id,
        fecha=datetime.strptime(data["fecha"], "%Y-%m-%d").date(),
        turno=data.get("turno") or "Noche",
        juego=data.get("juego") or "Pick3",
        numeros=data["numeros"],
        fijo=data.get("fijo"),
        corrido=data.get("corrido"),
        parle=data.get("parle"),
        candado=data.get("candado"),
        precio=data.get("precio"),
        descripcion=data.get("descripcion"),
    )
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return {"id": bet.id, "status": "ok"}


@app.post("/api/bets/{bet_id}/delete")
def api_delete_bet(
    bet_id: int,
    current_user: User = Depends(_require_user),
    db: Session = Depends(get_db),
):
    bet = db.query(Bet).filter(Bet.id == bet_id, Bet.user_id == current_user.id).first()
    if not bet:
        raise HTTPException(404, "Apuesta no encontrada")
    db.delete(bet)
    db.commit()
    return {"status": "ok"}
