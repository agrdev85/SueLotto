from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.models import Resultado
from backend.crud import get_frecuencias, get_atrasados
import json


def get_resultados_df(db: Session, juego: str, sorteo: str = None, dias: int = 365):
    import pandas as pd

    query = db.query(Resultado).filter(
        Resultado.juego == juego,
        Resultado.fecha >= date.today() - timedelta(days=dias),
    )
    if sorteo:
        query = query.filter(Resultado.sorteo == sorteo)
    resultados = query.order_by(Resultado.fecha).all()

    rows = []
    for r in resultados:
        row = {
            "fecha": r.fecha,
            "sorteo": r.sorteo,
            "n1": r.n1,
            "n2": r.n2,
            "n3": r.n3,
        }
        if r.n4 is not None:
            row["n4"] = r.n4
        rows.append(row)

    return pd.DataFrame(rows)


def calcular_frecuencias(db: Session, juego: str, sorteo: str = None, dias: int = 30):
    return get_frecuencias(db, juego, sorteo, dias)


def calcular_atrasados(db: Session, juego: str, sorteo: str = None):
    return get_atrasados(db, juego, sorteo)


def _build_features(df, pos: str):
    import numpy as np
    import pandas as pd

    features = []
    targets = []
    for i in range(30, len(df)):
        window = df.iloc[i - 30 : i]
        row = df.iloc[i]
        feat = {
            "sorteo_e": 1 if row["sorteo"] == "E" else 0,
            "dia_semana": row["fecha"].weekday(),
            "mes": row["fecha"].month,
        }
        for p in ["n1", "n2", "n3"]:
            series = window[p]
            feat[f"{p}_mean"] = series.mean()
            feat[f"{p}_std"] = series.std()
            feat[f"{p}_last"] = series.iloc[-1]
            feat[f"{p}_min"] = series.min()
            feat[f"{p}_max"] = series.max()
        features.append(feat)
        targets.append(row[pos])
    return pd.DataFrame(features), np.array(targets)


def _get_recency_weighted_frequencies(db: Session, juego: str, sorteo: str = None) -> dict:
    """Calcula frecuencias ponderadas por recencia: últimos 7d peso 3x, 30d peso 2x, 90d peso 1x."""
    from collections import Counter
    today = date.today()

    weight_schemes = [
        (7, 3.0),
        (30, 2.0),
        (90, 1.0),
    ]

    combined = Counter()
    total_weight = 0
    for dias, weight in weight_schemes:
        q = db.query(Resultado).filter(
            Resultado.juego == juego,
            Resultado.fecha >= today - timedelta(days=dias),
        )
        if sorteo:
            q = q.filter(Resultado.sorteo == sorteo)
        for r in q.all():
            for par in _extraer_todos_pares(r):
                combined[par] += weight
        total_weight += weight

    max_count = max(combined.values()) if combined else 1
    return {num: count / max_count for num, count in combined.items()}


def _get_trend_scores(db: Session, juego: str, sorteo: str = None) -> dict:
    """Calcula tendencia: diferencia de frecuencia entre últimos 15d y los 15d anteriores."""
    from collections import Counter
    today = date.today()

    recent = Counter()
    q = db.query(Resultado).filter(
        Resultado.juego == juego,
        Resultado.fecha >= today - timedelta(days=15),
    )
    if sorteo:
        q = q.filter(Resultado.sorteo == sorteo)
    for r in q.all():
        for par in _extraer_todos_pares(r):
            recent[par] += 1

    previous = Counter()
    q = db.query(Resultado).filter(
        Resultado.juego == juego,
        Resultado.fecha.between(today - timedelta(days=30), today - timedelta(days=15)),
    )
    if sorteo:
        q = q.filter(Resultado.sorteo == sorteo)
    for r in q.all():
        for par in _extraer_todos_pares(r):
            previous[par] += 1

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


def _extraer_todos_pares(r) -> list[int]:
    """Extrae TODAS las combinaciones de pares posibles de un resultado."""
    pares = []
    digitos = [r.n1, r.n2, r.n3]
    if r.n4 is not None:
        digitos.append(r.n4)
    for i in range(len(digitos)):
        for j in range(i + 1, len(digitos)):
            pares.append(digitos[i] * 10 + digitos[j])
            pares.append(digitos[j] * 10 + digitos[i])
    return pares


def _extraer_digitos_individuales(r) -> list[int]:
    """Extrae los dígitos individuales de un resultado."""
    digitos = [r.n1, r.n2, r.n3]
    if r.n4 is not None:
        digitos.append(r.n4)
    return digitos


def _predecir_pares_por_posicion(db: Session, juego: str, sorteo: str = None) -> list:
    """Predice los pares (corridos 00-99) más probables combinando análisis por posición."""
    import pandas as pd
    today = date.today()

    posiciones = ["n1", "n2", "n3", "n4"] if juego == "Pick 4" else ["n1", "n2", "n3"]
    freq_por_pos = {}
    for pos in posiciones:
        q = db.query(
            getattr(Resultado, pos),
            func.count(Resultado.id),
        ).filter(
            Resultado.juego == juego,
            Resultado.fecha >= today - timedelta(days=90),
        )
        if sorteo:
            q = q.filter(Resultado.sorteo == sorteo)
        q = q.group_by(getattr(Resultado, pos)).order_by(func.count(Resultado.id).desc()).limit(10)
        freq_por_pos[pos] = {row[0]: row[1] for row in q.all()}

    predicciones = []
    for i, pos_a in enumerate(posiciones):
        for pos_b in posiciones[i + 1:]:
            for dig_a, freq_a in freq_por_pos[pos_a].items():
                for dig_b, freq_b in freq_por_pos[pos_b].items():
                    par = dig_a * 10 + dig_b
                    prob = (freq_a + freq_b) / 180.0
                    predicciones.append({"numero": par, "probabilidad": round(prob, 4), "tipo": "par_posicional"})

    if not predicciones:
        return []

    df_pred = pd.DataFrame(predicciones)
    df_pred = df_pred.groupby("numero", as_index=False)["probabilidad"].mean()
    max_prob = df_pred["probabilidad"].max()
    if max_prob > 0:
        df_pred["probabilidad"] = df_pred["probabilidad"] / max_prob
    df_pred = df_pred.sort_values("probabilidad", ascending=False)
    return df_pred.head(20).to_dict("records")


def _fallback_prediction_mejorado(frecuencias: list, atrasados: list, db: Session = None, juego: str = None, sorteo: str = None):
    """Versión mejorada: combina frecuencia ponderada, tendencia, atraso y factor de recencia."""
    from collections import Counter

    freq_map = {f["numero"]: f["frecuencia"] for f in frecuencias}
    atraso_map = {a["numero"]: a["dias_sin_salir"] for a in atrasados}

    max_freq = max(freq_map.values()) if freq_map else 1
    max_atraso = max(atraso_map.values()) if atraso_map else 1

    recency_scores = {}
    trend_scores = {}
    if db and juego:
        recency_scores = _get_recency_weighted_frequencies(db, juego, sorteo)
        trend_scores = _get_trend_scores(db, juego, sorteo)

    predicciones = []
    for num in range(100):
        freq_score = freq_map.get(num, 0) / max_freq
        atraso_score = atraso_map.get(num, 0) / max(max_atraso, 1)

        recency_score = recency_scores.get(num, 0)
        trend_score = trend_scores.get(num, 0)

        prob = (
            0.30 * freq_score +
            0.25 * atraso_score +
            0.25 * recency_score +
            0.20 * trend_score
        )
        if prob > 0:
            predicciones.append({"numero": num, "probabilidad": round(prob, 4), "tipo": "hibrida"})

    return sorted(predicciones, key=lambda x: x["probabilidad"], reverse=True)


def generar_predicciones(db: Session, juego: Optional[str] = None, sorteo: str = None, use_llm: bool = True):
    if not juego:
        return []
    import pandas as pd

    frecuencias = calcular_frecuencias(db, juego, sorteo, 90)
    atrasados = calcular_atrasados(db, juego, sorteo)

    digit_preds = _fallback_prediction_mejorado(frecuencias, atrasados, db, juego, sorteo)
    pair_preds = _predecir_pares_por_posicion(db, juego, sorteo)

    result = {
        "digitos": digit_preds[:20] if digit_preds else [],
        "pares": pair_preds if pair_preds else [],
        "metadata": {
            "juego": juego,
            "sorteo": sorteo or "ambos",
            "fecha": date.today().isoformat(),
            "total_analizados": len(frecuencias),
        },
    }
    return result


def calcular_numeros_calientes(
    db: Session, juego: str, sorteo: str = None, limite: int = 20, dias: int = 30
) -> dict:
    frecuencias = get_frecuencias(db, juego, sorteo, dias)
    numeros = [f["numero"] for f in frecuencias[:limite]]
    freq_dict = {str(f["numero"]): f["frecuencia"] for f in frecuencias[:limite]}
    return {
        "juego": juego,
        "sorteo": sorteo,
        "limite": limite,
        "dias": dias,
        "numeros": numeros,
        "frecuencias": freq_dict,
    }


def obtener_posibles_salir(
    db: Session, juego: str = "Pick 3", fecha: date = None, sorteo: str = None, use_ml: bool = True
) -> dict:
    from datetime import datetime

    if fecha is None:
        ultimo = db.query(Resultado).filter(Resultado.juego == juego).order_by(desc(Resultado.fecha)).first()
        if not ultimo:
            return {"fecha": date.today().isoformat(), "numeros": [], "sorteo": sorteo or "E"}
        fecha = ultimo.fecha

    frecuencias = get_frecuencias(db, juego, sorteo, 90)
    atrasados = get_atrasados(db, juego, sorteo)

    freq_map = {f["numero"]: f["frecuencia"] for f in frecuencias}
    atraso_map = {a["numero"]: a["dias_sin_salir"] for a in atrasados}

    max_freq = max(freq_map.values()) if freq_map else 1
    max_atraso = max(atraso_map.values()) if atraso_map else 1

    scores = {}
    for num in range(100):
        freq_score = freq_map.get(num, 0) / max_freq
        atraso_score = atraso_map.get(num, 0) / max_atraso
        scores[num] = 0.6 * freq_score + 0.4 * atraso_score

    sorted_nums = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    numeros = [n for n, s in sorted_nums[:30] if s > 0]

    return {
        "fecha": fecha.isoformat() if isinstance(fecha, date) else fecha,
        "numeros": numeros,
        "sorteo": sorteo or "E",
    }
