import json
import math
import os
from collections import Counter
from typing import Optional
from sqlalchemy.orm import Session
from datetime import date, timedelta
from backend.crud import get_frecuencias, get_atrasados, get_frecuencia_digitos
from backend.models import Resultado

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

MATRIZ_NUEVA = [
    [1, 100, 2, 99, 3, 98, 4, 97, 5, 96],
    [6, 95, 7, 94, 8, 93, 9, 92, 10, 91],
    [11, 90, 12, 89, 13, 88, 14, 87, 15, 86],
    [16, 85, 17, 84, 18, 83, 19, 82, 20, 81],
    [21, 80, 22, 79, 23, 78, 24, 77, 25, 76],
    [26, 75, 27, 74, 28, 73, 29, 72, 30, 71],
    [31, 70, 32, 69, 33, 68, 34, 67, 35, 66],
    [36, 65, 37, 64, 38, 63, 39, 62, 40, 61],
    [41, 60, 42, 59, 43, 58, 44, 57, 45, 56],
    [46, 55, 47, 54, 48, 53, 49, 52, 50, 51],
]

MATRIZ_VIEJA = [
    [14, 46, 69, 1, 0, 62, 89, 28, 0, 57, 97],
    [66, 37, 99, 13, 79, 78, 0, 17, 90, 70, 0],
    [33, 60, 12, 98, 61, 0, 71, 80, 10, 0, 27],
    [100, 21, 2, 32, 91, 72, 0, 77, 96, 54, 81],
    [47, 82, 53, 31, 56, 0, 9, 0, 35, 92, 4],
    [25, 58, 0, 36, 87, 49, 83, 16, 0, 59, 0],
    [74, 0, 40, 0, 64, 11, 3, 45, 41, 84, 75],
    [0, 76, 24, 68, 93, 20, 73, 15, 85, 8, 0],
    [19, 7, 48, 50, 38, 0, 30, 51, 63, 0, 39],
    [29, 42, 0, 34, 52, 43, 94, 0, 5, 55, 86],
    [95, 65, 44, 88, 6, 22, 67, 0, 18, 23, 26],
]

with open(os.path.join(DATA_DIR, "arrastrados_tn.json"), "r") as f:
    _ARRASTRADOS_TN = {int(k): v for k, v in json.load(f).items()}

with open(os.path.join(DATA_DIR, "arrastrados_tv.json"), "r") as f:
    _ARRASTRADOS_TV = {int(k): v for k, v in json.load(f).items()}

MATRICES = {
    "nueva": MATRIZ_NUEVA,
    "vieja": MATRIZ_VIEJA,
}

_ALREDEDOR = {
    "nueva": _ARRASTRADOS_TN,
    "vieja": _ARRASTRADOS_TV,
}


def obtener_numeros_alrededor(numero: int, tipo_matriz: str = "nueva") -> list[int]:
    if not (1 <= numero <= 100):
        raise ValueError(f"Número {numero} fuera de rango (1-100)")
    arrastrados = _ALREDEDOR.get(tipo_matriz)
    if arrastrados is None:
        raise ValueError(f"Tipo de matriz inválido: {tipo_matriz}")
    if numero not in arrastrados:
        raise ValueError(f"Número {numero} no tiene datos de arrastrados para matriz {tipo_matriz}")
    return list(arrastrados[numero])


def procesar_secuencia(secuencia: list[int], tipo_matriz: str = "nueva") -> list[int]:
    if not 1 <= len(secuencia) <= 3:
        raise ValueError("La secuencia debe tener entre 1 y 3 números")
    for n in secuencia:
        if not (1 <= n <= 100):
            raise ValueError(f"Número {n} fuera de rango (1-100)")

    vistos = set()
    resultado = []
    for n in secuencia:
        for alrededor in obtener_numeros_alrededor(n, tipo_matriz):
            if alrededor not in vistos:
                vistos.add(alrededor)
                resultado.append(alrededor)

    return resultado


SCORE_W_FREQ_MULTI = float(os.getenv("SCORE_W_FREQ_MULTI", os.getenv("SCORE_W_FREQ_90D", "0.15")))
SCORE_W_REC_MULTI = float(os.getenv("SCORE_W_REC_MULTI", os.getenv("SCORE_W_RECENCIA", "0.30")))
SCORE_W_FREQ_7D_MULTI = float(os.getenv("SCORE_W_FREQ_7D_MULTI", os.getenv("SCORE_W_FREQ_7D", "0.15")))
SCORE_W_FREQ_DIGITOS = float(os.getenv("SCORE_W_FREQ_DIGITOS", "0.15"))
SCORE_W_TREND = float(os.getenv("SCORE_W_TREND", "0.25"))
SCORE_W_ML = float(os.getenv("SCORE_W_ML", "0.00"))
SCORE_MIN_FREQ = int(os.getenv("SCORE_MIN_FREQ", "0"))
SCORE_MAX_DAYS = int(os.getenv("SCORE_MAX_DAYS", "365"))


def _extraer_todos_pares(r) -> list[int]:
    digitos = [r.n1, r.n2, r.n3]
    if r.n4 is not None:
        digitos.append(r.n4)
    pares = []
    for i in range(len(digitos)):
        for j in range(i + 1, len(digitos)):
            pares.append(digitos[i] * 10 + digitos[j])
            pares.append(digitos[j] * 10 + digitos[i])
    return pares


def _get_trend_scores_multi(db: Session, juego: Optional[str], sorteo: Optional[str]) -> dict:
    """Tendencia: cambio de frecuencia entre últimos 15d y los 15d anteriores (soporta multi-juego).
    Usa SQL COUNT para evitar cargar filas."""
    today = date.today()
    from sqlalchemy import func as sqlfunc

    def _count_pairs(desde, hasta=None):
        q = db.query(Resultado.n1, Resultado.n2, Resultado.n3, Resultado.n4)
        if hasta:
            q = q.filter(Resultado.fecha.between(desde, hasta))
        else:
            q = q.filter(Resultado.fecha >= desde)
        if juego:
            q = q.filter(Resultado.juego == juego)
        if sorteo:
            q = q.filter(Resultado.sorteo == sorteo)
        counter = Counter()
        for r in q.all():
            digits = [r.n1, r.n2, r.n3]
            if r.n4 is not None:
                digits.append(r.n4)
            for i in range(len(digits)):
                for j in range(i + 1, len(digits)):
                    counter[digits[i] * 10 + digits[j]] += 1
                    counter[digits[j] * 10 + digits[i]] += 1
        return counter

    recent = _count_pairs(today - timedelta(days=15))
    previous = _count_pairs(today - timedelta(days=30), today - timedelta(days=15))

    scores = {}
    for num in range(100):
        r = recent.get(num, 0)
        p = previous.get(num, 0)
        if p > 0:
            scores[num] = (r - p) / (r + p) if r + p > 0 else 0
        elif r > 0:
            scores[num] = 1.0
        else:
            scores[num] = 0
    return scores


def _get_recency_weighted_multi(db: Session, juego: Optional[str], sorteo: Optional[str]) -> dict:
    """Frecuencia multi-ventana con pesos de recencia: 7d×3, 30d×2, 90d×1. Soporta multi-juego.
    Usa SQL para evitar cargar filas innecesarias."""
    today = date.today()
    combined = Counter()

    def _accumulate(desde, weight):
        q = db.query(Resultado.n1, Resultado.n2, Resultado.n3, Resultado.n4).filter(
            Resultado.fecha >= desde)
        if juego:
            q = q.filter(Resultado.juego == juego)
        if sorteo:
            q = q.filter(Resultado.sorteo == sorteo)
        for r in q.all():
            digits = [r.n1, r.n2, r.n3]
            if r.n4 is not None:
                digits.append(r.n4)
            for i in range(len(digits)):
                for j in range(i + 1, len(digits)):
                    combined[digits[i] * 10 + digits[j]] += weight
                    combined[digits[j] * 10 + digits[i]] += weight

    _accumulate(today - timedelta(days=7), 3.0)
    _accumulate(today - timedelta(days=30), 2.0)
    _accumulate(today - timedelta(days=90), 1.0)

    max_c = max(combined.values()) if combined else 1
    return {num: c / max_c for num, c in combined.items()}


def _score_numbers(
    db: Session, juego: str, sorteo: Optional[str],
    numeros: list[int], limite: int = 15,
    set_calientes: Optional[set] = None,
    set_posibles: Optional[set] = None,
) -> list[dict]:
    """
    Score matrix numbers using multi-game Florida lottery stats:
      - Multi-game pair frequency (90 days across ALL Florida games)
      - Multi-game recency (last appearance in ANY game)
      - Multi-game 7-day frequency burst
      - Digit-level frequency (0-9) across ALL games (orthogonal signal)
      - ML probability (game-specific, default weight 0)
    """
    frec_multi = get_frecuencias(db, None, None, 90)
    frec_7d_multi = get_frecuencias(db, None, None, 7)
    atraso_multi = get_atrasados(db, None, None)
    frec_digitos = get_frecuencia_digitos(db, 90)
    trend_scores = _get_trend_scores_multi(db, juego, sorteo)
    recency_weighted = _get_recency_weighted_multi(db, juego, sorteo)

    freq_multi_map = {f["numero"]: f["frecuencia"] for f in frec_multi}
    freq_7d_multi_map = {f["numero"]: f["frecuencia"] for f in frec_7d_multi}
    atraso_multi_map = {a["numero"]: a["dias_sin_salir"] for a in atraso_multi}
    digito_map = {d["digito"]: d["frecuencia"] for d in frec_digitos}

    max_freq_multi = max(freq_multi_map.values()) if freq_multi_map else 1
    max_freq_7d_multi = max(freq_7d_multi_map.values()) if freq_7d_multi_map else 1
    max_digitos = max(digito_map.values()) if digito_map else 1

    ml_map = {}
    max_ml = 1
    if SCORE_W_ML > 0:
        from backend.lottery_analyzer import generar_predicciones
        preds = generar_predicciones(db, juego, sorteo) or {}
        ml_map = {p["numero"]: p["probabilidad"] for p in preds.get("digitos", [])}
        max_ml = max(ml_map.values()) if ml_map else 1

    cal_set = set_calientes or set()
    pos_set = set_posibles or set()

    scored = []
    for n in numeros:
        c = n % 100

        freq_multi = freq_multi_map.get(c, 0)
        freq_7d_multi = freq_7d_multi_map.get(c, 0)
        dias = atraso_multi_map.get(c, 999)
        ml_prob = ml_map.get(c, 0)
        trend_score = trend_scores.get(c, 0)
        recency_weighted_score = recency_weighted.get(c, 0)

        if freq_multi < SCORE_MIN_FREQ and dias > SCORE_MAX_DAYS:
            continue

        d1, d2 = c // 10, c % 10
        digito_score = (digito_map.get(d1, 0) + digito_map.get(d2, 0)) / (2 * max_digitos) if max_digitos else 0

        freq_multi_norm = freq_multi / max_freq_multi if max_freq_multi else 0
        freq_7d_norm = freq_7d_multi / max_freq_7d_multi if max_freq_7d_multi else 0
        recencia_score = 1 / max(math.sqrt(1 + dias), 1)
        ml_score = ml_prob / max_ml if max_ml else 0

        composite = (
            SCORE_W_FREQ_MULTI * freq_multi_norm
            + SCORE_W_REC_MULTI * recencia_score
            + SCORE_W_FREQ_7D_MULTI * freq_7d_norm
            + SCORE_W_FREQ_DIGITOS * digito_score
            + SCORE_W_TREND * trend_score
            + SCORE_W_ML * ml_score
        )

        es_caliente = n in cal_set
        es_posible = n in pos_set
        if es_caliente and es_posible:
            categoria = "ambos"
            composite += 0.45
        elif es_caliente:
            categoria = "caliente"
            composite += 0.35
        elif es_posible:
            categoria = "posible"
            composite += 0.34
        else:
            categoria = "discriminante"

        scored.append({
            "numero": n,
            "score": round(composite, 4),
            "frecuencia": freq_multi,
            "frecuencia_7d": freq_7d_multi,
            "dias_sin_salir": dias,
            "tendencia": round(trend_score, 4),
            "recencia_ponderada": round(recency_weighted_score, 4),
            "digito_score": round(digito_score, 4),
            "probabilidad_ml": round(ml_prob, 4),
            "categoria": categoria,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limite]


def _charada_a_matriz(nums: list[int]) -> set[int]:
    """Convert charada numbers (0-99) to matrix numbers (1-100)."""
    return {n if n > 0 else 100 for n in nums}


def comparar_y_reducir(
    secuencia: list[int],
    tipo_matriz: str = "nueva",
    calientes: list[int] = None,
    posibles: list[int] = None,
    db: Optional[Session] = None,
    juego: Optional[str] = None,
    sorteo: Optional[str] = None,
    limite: int = 15,
) -> dict:
    alrededor = procesar_secuencia(secuencia, tipo_matriz)
    calientes = calientes or []
    posibles = posibles or []

    set_calientes = _charada_a_matriz(calientes)
    set_posibles = _charada_a_matriz(posibles)
    set_ambos = set_calientes & set_posibles
    set_alrededor = set(alrededor)

    interseccion_calientes = sorted(set_alrededor & set_calientes, key=lambda x: alrededor.index(x))
    interseccion_posibles = sorted(set_alrededor & set_posibles, key=lambda x: alrededor.index(x))
    interseccion_ambos = sorted(set_alrededor & set_ambos, key=lambda x: alrededor.index(x))
    discriminante = sorted(set_alrededor - set_calientes - set_posibles, key=lambda x: alrededor.index(x))

    result = {
        "alrededor": alrededor,
        "calientes": calientes,
        "posibles": posibles,
        "interseccion_calientes": interseccion_calientes,
        "interseccion_posibles": interseccion_posibles,
        "interseccion_ambos": interseccion_ambos,
        "discriminante": discriminante,
        "scored_final": [],
        "total_alrededor": len(alrededor),
        "total_interseccion_calientes": len(interseccion_calientes),
        "total_interseccion_posibles": len(interseccion_posibles),
        "total_interseccion_ambos": len(interseccion_ambos),
        "total_discriminante": len(discriminante),
    }

    if db and juego:
        result["scored_final"] = _score_numbers(
            db, juego, sorteo, alrededor, limite,
            set_calientes=set_calientes,
            set_posibles=set_posibles,
        )

    return result
