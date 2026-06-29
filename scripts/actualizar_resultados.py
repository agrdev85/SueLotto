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
from datetime import date


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


def actualizar_juego(juego: str):
    print(f"\n=== Actualizando {juego} ===")
    
    db = SessionLocal()
    try:
        ultima_fecha = get_ultima_fecha(db, juego)
        print(f"  Última fecha en BD: {ultima_fecha}")
    finally:
        db.close()
    
    # Descargar PDF actualizado
    pdf_path = PDF_PATHS[juego]
    if not descargar_pdf(PDF_URLS[juego], pdf_path):
        return 0
    
    # Extraer resultados
    resultados = extraer_resultados_pdf(pdf_path, juego)
    print(f"  Extraídos {len(resultados)} resultados del PDF")
    
    if ultima_fecha:
        nuevos = [r for r in resultados if r["fecha"] > ultima_fecha]
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