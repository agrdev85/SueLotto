import json
import os
from typing import Optional
from sqlalchemy.orm import Session
from datetime import date, timedelta
from backend.crud import get_frecuencias, get_atrasados

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


def _score_numbers(db: Session, juego: str, sorteo: Optional[str], numeros: list[int]) -> list[dict]:
    """Score a list of numbers using frequency, recency, and ML predictions."""
    frecuencias = get_frecuencias(db, juego, sorteo, 90)
    atrasados = get_atrasados(db, juego, sorteo)

    freq_map = {f["numero"]: f["frecuencia"] for f in frecuencias}
    atraso_map = {a["numero"]: a["dias_sin_salir"] for a in atrasados}

    max_freq = max(freq_map.values()) if freq_map else 1
    max_atraso = max(atraso_map.values()) if atraso_map else 1

    from backend.lottery_analyzer import generar_predicciones
    ml_preds = generar_predicciones(db, juego, sorteo)
    ml_map = {p["numero"]: p["probabilidad"] for p in ml_preds} if ml_preds else {}
    max_ml = max(ml_map.values()) if ml_map else 1

    scored = []
    for n in numeros:
        freq = freq_map.get(n, 0)
        dias = atraso_map.get(n, 999)
        ml_prob = ml_map.get(n, 0)

        freq_score = freq / max_freq
        atraso_score = dias / max_atraso
        ml_score = ml_prob / max_ml if max_ml else 0

        if freq == 0 and dias > 365:
            continue

        composite = 0.25 * freq_score + 0.35 * atraso_score + 0.40 * ml_score

        scored.append({
            "numero": n,
            "score": round(composite, 4),
            "frecuencia": freq,
            "dias_sin_salir": dias,
            "probabilidad_ml": round(ml_prob, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:15]


def comparar_y_reducir(
    secuencia: list[int],
    tipo_matriz: str = "nueva",
    calientes: list[int] = None,
    posibles: list[int] = None,
    db: Optional[Session] = None,
    juego: Optional[str] = None,
    sorteo: Optional[str] = None,
) -> dict:
    alrededor = procesar_secuencia(secuencia, tipo_matriz)
    calientes = calientes or []
    posibles = posibles or []

    set_calientes = set(calientes)
    set_posibles = set(posibles)
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
        "discriminante_scored": [],
        "total_alrededor": len(alrededor),
        "total_interseccion_calientes": len(interseccion_calientes),
        "total_interseccion_posibles": len(interseccion_posibles),
        "total_interseccion_ambos": len(interseccion_ambos),
        "total_discriminante": len(discriminante),
    }

    if db and juego and discriminante:
        result["discriminante_scored"] = _score_numbers(db, juego, sorteo, discriminante)

    return result
