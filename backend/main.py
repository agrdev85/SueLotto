import os
import secrets
import logging
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
from backend.auth import hash_password, verify_password, create_access_token, decode_token
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
from backend.auto_updater import start as start_auto_updater
from backend.fl_scraper import scrape_other_games
from backend.rate_limit import RateLimitMiddleware
from backend.email_service import (
    send_verification_email, send_password_reset,
    send_welcome_email, send_payment_receipt, is_configured as email_configured,
)
from backend.qvapay import create_payment_url, process_webhook, verify_webhook, is_configured as qvapay_configured, PLANS, get_promo_info, increment_promo_purchases

app = FastAPI(title="SueñaLotto API", version="2.0.0")

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

def _import_historical_resultados():
    logger.info("Historical results import started (background)")
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import actualizar_resultados
    for juego in ["Pick 3", "Pick 4"]:
        try:
            nuevos = actualizar_resultados.actualizar_juego(juego)
            logger.info("Historical import %s: %d records", juego, nuevos)
        except Exception as e:
            logger.error("Historical import %s failed: %s", juego, e)
    logger.info("Historical results import completed")


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
            if db.query(Resultado).count() == 0:
                logger.info("Resultados table empty — starting background import from Florida PDFs")
                t = threading.Thread(target=_import_historical_resultados, daemon=True)
                t.start()
        finally:
            db.close()
        start_auto_updater()
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
    db.commit()
    logger.info("Admin set tier: %s -> %s", username, new_tier)
    return {"status": "ok", "username": username, "tier": new_tier}


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
    games = get_other_games(db, limit=10)
    if games:
        return [
            {
                "name": g.game_name,
                "date": g.drawing_date or "",
                "numbers": g.numbers.split(",") if g.numbers else [],
                "extra": g.extra.split(",") if g.extra else [],
            }
            for g in games
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
    return get_frecuencias(db, juego, sorteo, dias)


@app.get("/api/estadisticas/atrasados")
def api_atrasados(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    db: Session = Depends(get_db),
):
    return get_atrasados(db, juego, sorteo)


@app.get("/api/predicciones")
def api_predicciones(
    juego: Optional[str] = Query(None),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    db: Session = Depends(get_db),
):
    return generar_predicciones(db, juego, sorteo)


@app.get("/api/estadisticas/calientes")
def api_calientes(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    limite: int = Query(20, ge=1, le=100),
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return calcular_numeros_calientes(db, juego, sorteo, limite, dias)


@app.get("/api/estadisticas/posibles-salir")
def api_posibles_salir(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    fecha: Optional[date] = None,
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    use_ml: bool = Query(True),
    db: Session = Depends(get_db),
):
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
    }


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
        turno=data.get("turno"),
        juego=data.get("juego"),
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
