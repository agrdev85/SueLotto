"""
Script de actualización diaria desde PDFs.
Descarga PDFs, extrae solo resultados posteriores a la última fecha registrada.
Programar como Cron Job en Render.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db
from backend.crud import bulk_insert_resultados
from scripts.importar_historicos import (
    PDF_URLS, PDF_PATHS, descargar_pdf, extraer_resultados_pdf,
    DATA_DIR
)
from datetime import date, datetime


def get_ultima_fecha(db, juego: str) -> date:
    from backend.models import Resultado
    from sqlalchemy import desc

    result = (
        db.query(Resultado.fecha)
        .filter(Resultado.juego == juego)
        .order_by(desc(Resultado.fecha))
        .first()
    )
    return result[0] if result else None


def actualizar_desde_pdf(juego: str):
    """Vía antigua: descarga el PDF de historial y extrae los resultados."""
    # Descargar PDF actualizado
    pdf_path = PDF_PATHS[juego]
    if not descargar_pdf(PDF_URLS[juego], pdf_path):
        return 0

    # Extraer resultados
    resultados = extraer_resultados_pdf(pdf_path, juego)
    print(f"  Extraídos {len(resultados)} resultados del PDF")

    db = SessionLocal()
    try:
        ultima_fecha = get_ultima_fecha(db, juego)
    finally:
        db.close()

    if ultima_fecha:
        nuevos = [r for r in resultados if r["fecha"] >= ultima_fecha]
    else:
        nuevos = resultados

    print(f"  Nuevos desde última fecha: {len(nuevos)}")

    if not nuevos:
        return 0

    db = SessionLocal()
    try:
        bulk_insert_resultados(db, nuevos)
        print(f"  Insertados/actualizados {len(nuevos)} registros")
    except Exception as e:
        db.rollback()
        print(f"  ERROR en BD: {e}")
        return 0
    finally:
        db.close()

    return len(nuevos)


def actualizar_desde_api(juego: str):
    """Vía oficial: toma los sorteos MIDDAY/EVENING de la API de floridalottery.com.

    Devuelve la cantidad de registros nuevos insertados, o 0 si la API
    no aportó nada nuevo (o no estaba disponible)."""
    from backend.fl_api import fetch_latest_draws, normalize_draws, GAME_NAMES

    try:
        draws = normalize_draws(fetch_latest_draws())
    except Exception as e:
        print(f"  [WARN] API oficial no disponible: {e}")
        return 0

    juego_api = {v: k for k, v in GAME_NAMES.items()}.get(juego)
    if not juego_api:
        return 0

    sorteos = []
    for d in draws:
        if d["raw_name"] != juego_api or d["date"] is None:
            continue
        if d["draw_type"] not in ("MIDDAY", "EVENING"):
            continue
        if len(d["numbers"]) not in (3, 4):
            continue
        sorteos.append({
            "fecha": d["date"],
            "juego": juego,
            "sorteo": "M" if d["draw_type"] == "MIDDAY" else "E",
            "n1": int(d["numbers"][0]),
            "n2": int(d["numbers"][1]),
            "n3": int(d["numbers"][2]),
        })
        if len(d["numbers"]) == 4:
            sorteos[-1]["n4"] = int(d["numbers"][3])

    db = SessionLocal()
    try:
        ultima_fecha = get_ultima_fecha(db, juego)
    finally:
        db.close()
    print(f"  Sorteos en API: {len(sorteos)} | Última fecha en BD: {ultima_fecha}")

    if ultima_fecha:
        nuevos = [r for r in sorteos if r["fecha"] >= ultima_fecha]
    else:
        nuevos = sorteos

    if not nuevos:
        return 0

    db = SessionLocal()
    try:
        bulk_insert_resultados(db, nuevos)
        print(f"  Insertados/actualizados {len(nuevos)} registros (API oficial)")
    except Exception as e:
        db.rollback()
        print(f"  ERROR en BD: {e}")
        return 0
    finally:
        db.close()

    return len(nuevos)


def actualizar_juego(juego: str):
    print(f"\n=== Actualizando {juego} ===")

    # Primero la API oficial (resultados del mismo día, con Fireball).
    nuevos = actualizar_desde_api(juego)
    if nuevos:
        return nuevos

    # Si la API no aporta nada nuevo (o falló), usar el PDF de historial,
    # que cubre también huecos de varios días.
    return actualizar_desde_pdf(juego)


def main():
    print(f"=== Actualizador Florida Lottery (PDF) - {date.today()} ===")
    init_db()
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    total = 0
    for juego in ["Pick 3", "Pick 4"]:
        total += actualizar_juego(juego)
    
    print(f"\nOK - Actualizacion completa. Total nuevos: {total}")


if __name__ == "__main__":
    main()