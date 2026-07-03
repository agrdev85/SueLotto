import os
from fastapi import FastAPI, Depends, Query, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from backend.database import init_db, get_db
from backend.schemas import MatrizRequest, SecuenciaRequest, CompararRequest
from backend.auth import hash_password, verify_password, create_access_token, decode_token
from backend.models import User, Bet, UserUsage
from backend.crud import (
    get_ultimos_resultados,
    get_resultados_historicos,
    get_frecuencias,
    get_atrasados,
    get_adivinanza_hoy,
    get_posibles_salir,
    get_charada_enriquecida,
    get_charada_frecuencias,
)
from backend.lottery_analyzer import generar_predicciones, calcular_numeros_calientes, obtener_posibles_salir
from backend.charada_engine import buscar_en_sueno
from backend.adivinanza_ai import analizar_adivinanza
from backend.matrix_engine import obtener_numeros_alrededor, procesar_secuencia, comparar_y_reducir
from backend.auto_updater import start as start_auto_updater

app = FastAPI(title="SueñaLotto API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        start_auto_updater()
    except Exception as e:
        print(f"[WARN] Startup error (non-fatal): {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


# ─── Auto-Update Status ────────────────────────────────────────────


from backend.auto_updater import get_status as get_auto_update_status


@app.post("/api/admin/update")
def api_trigger_update():
    from backend.auto_updater import run_update
    run_update()
    return {"status": "ok", "detail": "Actualización ejecutada"}


@app.get("/api/admin/update-status")
def api_update_status():
    return get_auto_update_status()


@app.post("/api/admin/set-tier")
def api_admin_set_tier(data: dict = Body(...), db: Session = Depends(get_db)):
    username = data.get("username", "").strip()
    new_tier = data.get("tier", "free").strip().lower()
    if new_tier not in ("free", "pro", "lifetime"):
        raise HTTPException(400, "Plan inválido: free, pro, lifetime")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    user.tier = new_tier
    db.commit()
    return {"status": "ok", "username": username, "tier": new_tier}


@app.get("/api/resultados/ultimos")
def api_ultimos_resultados(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_ultimos_resultados(db, juego, sorteo, limit)


@app.get("/api/resultados/por-fecha")
def api_resultados_por_fecha(
    fecha: date,
    db: Session = Depends(get_db),
):
    from backend.models import Resultado
    resultados = db.query(Resultado).filter(Resultado.fecha == fecha).order_by(Resultado.juego, Resultado.sorteo).all()
    return resultados


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
        "data": results,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total else 0,
    }


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


@app.post("/api/charada/buscar")
def api_charada_buscar(texto: str = Body(..., embed=True), db: Session = Depends(get_db)):
    if not texto or not texto.strip():
        raise HTTPException(status_code=400, detail="Texto de sueño requerido")
    resultados = buscar_en_sueno(db, texto)
    return {
        "texto_original": texto,
        "resultados": resultados,
    }


@app.get("/api/adivinanza/hoy")
def api_adivinanza_hoy(db: Session = Depends(get_db)):
    adivinanza = get_adivinanza_hoy(db)
    if not adivinanza:
        return {
            "fecha": date.today().isoformat(),
            "texto": "Hoy no hay adivinanza disponible. ¡Vuelve mañana!",
        }
    return adivinanza


@app.post("/api/adivinanza/analizar")
def api_adivinanza_analizar(
    adivinanza: str = Body(...),
    interpretacion: str = Body(...),
):
    if not adivinanza or not interpretacion:
        raise HTTPException(status_code=400, detail="Adivinanza e interpretación requeridas")
    return analizar_adivinanza(adivinanza, interpretacion)


# ─── Matriz Endpoints ─────────────────────────────────────────────

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


# ─── Calientes & Posibles a Salir ─────────────────────────────────

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


# ─── Charada Frecuencias (análisis 0-99) ──────────────────────────
@app.get("/api/estadisticas/charada-frecuencias")
def api_charada_frecuencias(
    juego: str = Query("Pick 3", pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    dias: int = 90,
    db: Session = Depends(get_db),
):
    return get_charada_frecuencias(db, juego, sorteo, dias)


# ─── IA Status ────────────────────────────────────────────────────
@app.get("/api/ia/status")
def api_ia_status():
    from backend.adivinanza_ai import gemini_activo
    return {
        "gemini_disponible": gemini_activo(),
        "gemini_api_key_configurada": bool(os.getenv("GEMINI_API_KEY", "")),
    }


# ─── Charada Enriquecida ──────────────────────────────────────────

@app.get("/api/charada/enriquecida")
def api_charada_enriquecida(
    numero: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_charada_enriquecida(db, numero)


# ─── Auth Endpoints ────────────────────────────────────────────────

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
    if len(password) < 4:
        raise HTTPException(400, "La contraseña debe tener al menos 4 caracteres")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "El nombre de usuario ya existe")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "El email ya está registrado")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        tier=tier,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tier": user.tier,
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
            "tier_expires": user.tier_expires.isoformat() if user.tier_expires else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@app.get("/api/auth/profile")
def api_profile(current_user: Optional[User] = Depends(_get_user_from_token)):
    if not current_user:
        raise HTTPException(401, "No autenticado")
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "tier": current_user.tier,
        "tier_expires": current_user.tier_expires.isoformat() if current_user.tier_expires else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@app.get("/api/auth/tier")
def api_check_tier(
    current_user: Optional[User] = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
):
    tier = current_user.tier if current_user else "free"

    # Free: sorteos, estadísticas, histórica, sueños (3/día cada uno)
    can_use_historica = tier in ("free", "trial", "pro", "lifetime")
    can_use_suenos = tier in ("free", "trial", "pro", "lifetime")
    can_use_adivinanzas = tier in ("pro", "lifetime")
    can_use_matriz = tier in ("pro", "lifetime")

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


@app.post("/api/usage/busqueda")
def api_increment_busqueda_usage(current_user: Optional[User] = Depends(_get_user_from_token), db: Session = Depends(get_db)):
    """Incrementa contador de búsquedas de sueños (charada)."""
    if not current_user:
        raise HTTPException(401, "No autenticado")
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == current_user.id,
        UserUsage.fecha == date.today(),
    ).first()
    if not usage:
        usage = UserUsage(user_id=current_user.id, fecha=date.today(), charada_count=1)
        db.add(usage)
    else:
        usage.charada_count += 1
    db.commit()
    return {"suenos_today": usage.charada_count}


@app.post("/api/usage/historica")
def api_increment_historica_usage(current_user: Optional[User] = Depends(_get_user_from_token), db: Session = Depends(get_db)):
    """Incrementa contador de búsquedas históricas."""
    if not current_user:
        raise HTTPException(401, "No autenticado")
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == current_user.id,
        UserUsage.fecha == date.today(),
    ).first()
    if not usage:
        usage = UserUsage(user_id=current_user.id, fecha=date.today(), historica_count=1)
        db.add(usage)
    else:
        usage.historica_count += 1
    db.commit()
    return {"historica_today": usage.historica_count}


# ─── Bet Endpoints ─────────────────────────────────────────────────

@app.get("/api/bets")
def api_get_bets(current_user: Optional[User] = Depends(_get_user_from_token), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(401, "No autenticado")
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
def api_create_bet(data: dict = Body(...), current_user: Optional[User] = Depends(_get_user_from_token), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(401, "No autenticado")
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
def api_delete_bet(bet_id: int, current_user: Optional[User] = Depends(_get_user_from_token), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(401, "No autenticado")
    bet = db.query(Bet).filter(Bet.id == bet_id, Bet.user_id == current_user.id).first()
    if not bet:
        raise HTTPException(404, "Apuesta no encontrada")
    db.delete(bet)
    db.commit()
    return {"status": "ok"}
