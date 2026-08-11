from datetime import date, timedelta
from typing import Optional
import os
import threading
import time
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Resultado
from backend.crud import get_frecuencias, get_atrasados

ML_CACHE_TTL = int(os.getenv("ML_CACHE_TTL_SECONDS", "900"))
_ML_CACHE = {}
_ML_CACHE_LOCK = threading.Lock()


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


def generar_predicciones(db: Session, juego: Optional[str] = None, sorteo: str = None, use_llm: bool = True):
    key = (juego, sorteo, use_llm)
    now = time.time()
    with _ML_CACHE_LOCK:
        hit = _ML_CACHE.get(key)
        if hit and now - hit[0] < ML_CACHE_TTL:
            return hit[1]

    result = _generar_predicciones(db, juego, sorteo, use_llm)

    with _ML_CACHE_LOCK:
        _ML_CACHE[key] = (time.time(), result)
    return result


def _generar_predicciones(db: Session, juego: Optional[str] = None, sorteo: str = None, use_llm: bool = True):
    if not juego:
        raw = _fallback_prediction([], [])
        return _build_prediction_response(raw, juego, sorteo, db)

    min_count = db.query(Resultado).filter(
        Resultado.juego == juego,
        Resultado.fecha >= date.today() - timedelta(days=365),
    ).count()

    frecuencias = calcular_frecuencias(db, juego, sorteo, 90)
    atrasados = calcular_atrasados(db, juego, sorteo)

    if use_llm and min_count >= 20:
        llm_preds = _generar_predicciones_llm(db, juego, sorteo, frecuencias, atrasados)
        if llm_preds:
            return _build_prediction_response(llm_preds, juego, sorteo, db)

    if min_count < 60:
        raw = _fallback_prediction(frecuencias, atrasados)
        return _build_prediction_response(raw, juego, sorteo, db)

    try:
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
    except ImportError:
        raw = _fallback_prediction(frecuencias, atrasados)
        return _build_prediction_response(raw, juego, sorteo, db)

    df = get_resultados_df(db, juego, sorteo, dias=365)

    predicciones_totales = []
    for pos in ["n1", "n2", "n3"]:
        X, y = _build_features(df, pos)
        if len(X) < 10:
            continue

        model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
        model.fit(X, y)

        ultimo = df.iloc[-1]
        last_feat = {
            "sorteo_e": 1 if ultimo["sorteo"] == "E" else 0,
            "dia_semana": date.today().weekday(),
            "mes": date.today().month,
        }
        for p in ["n1", "n2", "n3"]:
            window = df[p].iloc[-30:]
            last_feat[f"{p}_mean"] = window.mean()
            last_feat[f"{p}_std"] = window.std()
            last_feat[f"{p}_last"] = window.iloc[-1]
            last_feat[f"{p}_min"] = window.min()
            last_feat[f"{p}_max"] = window.max()

        X_pred = pd.DataFrame([last_feat])
        probs = model.predict_proba(X_pred)[0]

        for num, prob in enumerate(probs):
            if prob > 0:
                predicciones_totales.append({"numero": num, "probabilidad": round(float(prob), 4)})

    if not predicciones_totales:
        raw = _fallback_prediction(frecuencias, atrasados)
        return _build_prediction_response(raw, juego, sorteo, db)

    df_pred = pd.DataFrame(predicciones_totales)
    df_pred = df_pred.groupby("numero", as_index=False)["probabilidad"].mean()
    df_pred = df_pred.sort_values("probabilidad", ascending=False)

    raw = df_pred.to_dict("records")
    return _build_prediction_response(raw, juego, sorteo, db)


def _build_prediction_response(raw_preds: list, juego: str, sorteo: str, db: Session = None) -> dict:
    """Wrap raw predictions list into frontend-expected {digitos, pares, metadata} format."""
    digitos = sorted(
        [p for p in raw_preds if p.get("numero", 0) < 10],
        key=lambda x: x.get("probabilidad", 0),
        reverse=True,
    )
    pares = [p for p in raw_preds if p.get("numero", 0) >= 10]
    if db and juego:
        frecuencias = calcular_frecuencias(db, juego, sorteo, 90)
        atrasados = calcular_atrasados(db, juego, sorteo)
        if frecuencias or atrasados:
            pares = _fallback_prediction(frecuencias, atrasados)
    if not pares:
        pares = sorted(
            [p for p in raw_preds if p.get("numero", 0) < 100],
            key=lambda x: x.get("probabilidad", 0),
            reverse=True,
        )
    return {
        "digitos": digitos,
        "pares": pares,
        "metadata": {
            "juego": juego or "",
            "sorteo": sorteo or "",
            "fecha": str(date.today()),
            "total_analizados": len(raw_preds),
        },
    }


def _generar_predicciones_llm(db: Session, juego: str, sorteo: str, frecuencias: list, atrasados: list) -> list:
    import pandas as pd
    from backend.llm_client import build_prediction_prompt, consultar_json, parse_predicciones_llm

    historicos = get_resultados_df(db, juego, sorteo, dias=90)
    if len(historicos) < 10:
        return []

    historicos_dict = []
    for _, row in historicos.tail(60).iterrows():
        h = {
            "fecha": row["fecha"].isoformat() if hasattr(row["fecha"], "isoformat") else str(row["fecha"]),
            "n1": int(row["n1"]),
            "n2": int(row["n2"]),
            "n3": int(row["n3"]),
        }
        if "n4" in row.index and pd.notna(row["n4"]):
            h["n4"] = int(row["n4"])
        historicos_dict.append(h)

    prompt = build_prediction_prompt(juego, historicos_dict, frecuencias, atrasados)
    response = consultar_json(prompt)
    return parse_predicciones_llm(response)


def _fallback_prediction(frecuencias: list, atrasados: list):
    freq_map = {f["numero"]: f["frecuencia"] for f in frecuencias}
    atraso_map = {a["numero"]: a["dias_sin_salir"] for a in atrasados}

    max_freq = max(freq_map.values()) if freq_map else 1
    max_atraso = max(atraso_map.values()) if atraso_map else 1

    predicciones = []
    for num in range(100):
        freq_score = freq_map.get(num, 0) / max_freq
        atraso_score = atraso_map.get(num, 0) / max_atraso
        prob = 0.5 * freq_score + 0.5 * atraso_score
        if prob > 0:
            predicciones.append({"numero": num, "probabilidad": round(prob, 4)})

    return sorted(predicciones, key=lambda x: x["probabilidad"], reverse=True)


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
