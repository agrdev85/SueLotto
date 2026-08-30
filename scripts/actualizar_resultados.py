"""
Actualización diaria de resultados desde la API oficial y los PDFs.
- La API oficial solo trae el sorteo más reciente (rápida, para el mismo día).
- El PDF histórico trae TODOS los sorteos (MIDDAY y EVENING) desde 1988;
  se descarga/parsea solo cuando se detectan huecos y rellena todo lo que
  falte por clave (fecha, juego, sorteo), sin depender de rangos de fecha.
Ejecutado automáticamente por el scheduler (backend/auto_updater.py).
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db
from backend.crud import bulk_insert_resultados
from scripts.importar_historicos import (
    PDF_URLS, PDF_PATHS, descargar_pdf, extraer_resultados_pdf,
    importar_juego, DATA_DIR
)
from datetime import date, datetime, timedelta

# Serializa la importación masiva del histórico (evita que el hilo lazy de
# arranque y catch_up/auto-updater inserten simultáneamente los mismos
# registros al levantar el servidor con una BD vacía, p. ej. en Neon/Postgres).
_hist_lock = threading.Lock()


def falta_historial(db, juego: str) -> bool:
    """True si la tabla de resultados no tiene el histórico completo
    (BD recién creada o importación parcial). El histórico oficial de
    Pick 3 llega a 1988 y el de Pick 4 a 1991, así que si la fecha
    mínima es posterior a esos años (o hay muy pocos registros) falta
    el import completo."""
    from backend.crud import get_rango_fechas
    from backend.models import Resultado

    # Año máximo de inicio legítimo por juego (primer sorteo oficial):
    # Pick 3 → abril 1988, Pick 4 → julio 1991.
    inicio_por_juego = {"Pick 3": 1990, "Pick 4": 1992}

    min_fecha, _ = get_rango_fechas(db, juego)
    if min_fecha is None or min_fecha.year > inicio_por_juego.get(juego, 1992):
        return True
    count = db.query(Resultado).filter(Resultado.juego == juego).count()
    return count < 1000


def falta_historial_alguna() -> bool:
    db = SessionLocal()
    try:
        return any(falta_historial(db, juego) for juego in ("Pick 3", "Pick 4"))
    finally:
        db.close()


def importar_historial_si_falta(juego: str):
    """Si la tabla no tiene el histórico completo, importa TODO desde el
    PDF oficial (desde 1988). Es idempotente: bulk_insert deduplica."""
    with _hist_lock:
        db = SessionLocal()
        try:
            falta = falta_historial(db, juego)
        finally:
            db.close()

        if not falta:
            return False

        print(f"  Historial incompleto para {juego} — importando histórico completo desde PDF")
        importar_juego(juego)
        return True


def _stats_juego(juego: str) -> dict:
    """Conteo y rango de fechas de un juego en la BD (para reportes)."""
    from backend.models import Resultado
    from backend.crud import get_rango_fechas

    db = SessionLocal()
    try:
        min_f, max_f = get_rango_fechas(db, juego)
        count = db.query(Resultado).filter(Resultado.juego == juego).count()
        return {
            "count": count,
            "min_fecha": min_f.isoformat() if min_f else None,
            "max_fecha": max_f.isoformat() if max_f else None,
            "completo": not falta_historial(db, juego),
        }
    finally:
        db.close()


def repoblar_historial(juego: str = None, fuerza: bool = False) -> dict:
    """Repobla el histórico de Pick 3 / Pick 4 desde el PDF oficial.

    - juego=None → ambos juegos. fuerza=False → solo si falta el histórico
      completo. fuerza=True → siempre descarga/parsa/reinserta (deduplica).
    Devuelve un reporte con conteos y rangos de fechas por juego.
    Usado por el admin (UI Gestor BD) cuando la carga automática falló."""
    juegos = ["Pick 3", "Pick 4"] if not juego else [juego]
    reporte = {"status": "ok", "juego": juego, "fuerza": fuerza, "juegos": {}}
    with _hist_lock:
        for j in juegos:
            antes = _stats_juego(j)["count"]
            if not fuerza and antes and _stats_juego(j)["completo"]:
                reporte["juegos"][j] = {"salteado": True, "insertados": 0, **_stats_juego(j)}
                continue
            nuevos = importar_juego(j)
            reporte["juegos"][j] = {"salteado": False, "insertados": nuevos, **_stats_juego(j)}
    return reporte


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


def _claves_existentes(db, juego: str) -> set:
    """Devuelve el conjunto de claves (fecha, sorteo) ya presentes en la BD
    para un juego. Se usa para rellenar solo lo que falta, sin depender de
    rangos de fecha (que dejan huecos, p. ej. sábados sin datos)."""
    from backend.models import Resultado

    rows = db.query(Resultado.fecha, Resultado.sorteo).filter(Resultado.juego == juego).all()
    return {(r.fecha, r.sorteo) for r in rows}


def actualizar_desde_pdf(juego: str):
    """Vía oficial de historial: el PDF trae TODOS los sorteos (MIDDAY y
    EVENING) desde 1988. Inserta cualquier registro que falte en la BD
    comparando por clave (fecha, juego, sorteo), rellenando así cualquier
    hueco, sea anterior o posterior a la última fecha registrada."""
    # Descargar PDF actualizado
    pdf_path = PDF_PATHS[juego]
    if not descargar_pdf(PDF_URLS[juego], pdf_path):
        return 0

    # Extraer resultados
    resultados = extraer_resultados_pdf(pdf_path, juego)
    print(f"  Extraídos {len(resultados)} resultados del PDF")

    if not resultados:
        return 0

    db = SessionLocal()
    try:
        existentes = _claves_existentes(db, juego)
        nuevos = [r for r in resultados if (r["fecha"], r["sorteo"]) not in existentes]
        print(f"  Ya existentes: {len(existentes)} | Faltan: {len(nuevos)}")

        if not nuevos:
            return 0

        bulk_insert_resultados(db, nuevos)
        print(f"  Insertados/actualizados {len(nuevos)} registros (PDF)")
    except Exception as e:
        db.rollback()
        print(f"  ERROR en BD: {e}")
        return 0
    finally:
        db.close()

    return len(nuevos)


def detectar_huecos(juego: str, dias: int = 30) -> bool:
    """True si faltan sorteos (M/E) en los últimos `dias` días respecto a la
    última fecha registrada, o si la BD está atrasada más de 3 días.

    El día más reciente se excluye de la exigencia M+E porque puede estar
    aún en curso (el mismo día lo cubre la API)."""
    from backend.models import Resultado

    db = SessionLocal()
    try:
        max_fecha = get_ultima_fecha(db, juego)
        if max_fecha is None:
            return True
        if (date.today() - max_fecha).days > 3:
            print(f"  BD atrasada: última fecha {max_fecha}")
            return True

        desde = max_fecha - timedelta(days=dias)
        keys = {
            (r.fecha, r.sorteo)
            for r in db.query(Resultado.fecha, Resultado.sorteo)
            .filter(Resultado.juego == juego, Resultado.fecha >= desde)
        }
        for i in range(1, dias + 1):
            d = max_fecha - timedelta(days=i)
            for s in ("M", "E"):
                if (d, s) not in keys:
                    print(f"  Hueco detectado: {d} {s}")
                    return True
        return False
    finally:
        db.close()


def actualizar_desde_api(juego: str, ultima_fecha: date = None):
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

    print(f"  Sorteos en API: {len(sorteos)} | Última fecha base: {ultima_fecha}")

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

    # Si la tabla no tiene el histórico completo (BD nueva o import parcial),
    # importar TODO desde el PDF oficial ANTES de la actualización diaria.
    importar_historial_si_falta(juego)

    # Capturar la fecha base UNA VEZ (antes de cualquier inserción).
    db = SessionLocal()
    try:
        ultima_fecha = get_ultima_fecha(db, juego)
    finally:
        db.close()

    # 1) API oficial: trae los sorteos del mismo día (rápida y barata).
    nuevos_api = actualizar_desde_api(juego, ultima_fecha)

    # 2) PDF histórico: solo se descarga/parsea si hay huecos (faltan
    #    sorteos M/E de algún día reciente). Si hay, rellena TODO lo
    #    que falte comparando por clave (fecha, sorteo), sin importar
    #    si el hueco es anterior o posterior a la última fecha.
    nuevos_pdf = 0
    if detectar_huecos(juego):
        print("  Huecos detectados — sincronizando con el PDF histórico")
        nuevos_pdf = actualizar_desde_pdf(juego)
    else:
        print("  Sin huecos — PDF no necesario")

    total = (nuevos_api or 0) + (nuevos_pdf or 0)
    print(f"  Total nuevos {juego}: {total} (API: {nuevos_api or 0}, PDF: {nuevos_pdf or 0})")
    return total


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