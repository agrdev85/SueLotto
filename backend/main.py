from fastapi import FastAPI, Depends, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from backend.database import init_db, get_db
from backend.schemas import MatrizRequest, SecuenciaRequest, CompararRequest
from backend.crud import (
    get_ultimos_resultados,
    get_resultados_historicos,
    get_frecuencias,
    get_atrasados,
    get_adivinanza_hoy,
    get_posibles_salir,
    get_charada_enriquecida,
)
from backend.lottery_analyzer import generar_predicciones, calcular_numeros_calientes, obtener_posibles_salir
from backend.charada_engine import buscar_en_sueno
from backend.adivinanza_ai import analizar_adivinanza
from backend.matrix_engine import obtener_numeros_alrededor, procesar_secuencia, comparar_y_reducir

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
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/resultados/ultimos")
def api_ultimos_resultados(
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
    sorteo: Optional[str] = Query(None, pattern="^(E|M)$"),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_ultimos_resultados(db, juego, sorteo, limit)


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
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
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
    juego: str = Query(..., pattern="^(Pick 3|Pick 4)$"),
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
        resultado = comparar_y_reducir(req.secuencia, req.tipo_matriz, req.calientes, req.posibles)
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


# ─── Charada Enriquecida ──────────────────────────────────────────

@app.get("/api/charada/enriquecida")
def api_charada_enriquecida(
    numero: Optional[int] = Query(None, ge=0, le=99),
    db: Session = Depends(get_db),
):
    return get_charada_enriquecida(db, numero)
