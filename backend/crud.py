import json
import re
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_, cast, String
from typing import Optional
from datetime import date, timedelta
from backend.models import Resultado, Charada, Adivinanza, PosibleSalir


def bulk_insert_resultados(db: Session, resultados: list[dict]):
    for r in resultados:
        existing = db.query(Resultado).filter(
            Resultado.fecha == r["fecha"],
            Resultado.juego == r["juego"],
            Resultado.sorteo == r["sorteo"],
        ).first()
        if not existing:
            db.add(Resultado(**r))
    db.commit()


def get_ultimos_resultados(db: Session, juego: str, sorteo: Optional[str] = None, limit: int = 20):
    query = db.query(Resultado).filter(Resultado.juego == juego)
    if sorteo:
        query = query.filter(Resultado.sorteo == sorteo)
    return query.order_by(desc(Resultado.fecha)).limit(limit).all()


def get_resultados_historicos(
    db: Session,
    juego: Optional[str] = None,
    sorteo: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    contienen_digitos: Optional[str] = None,
    page: int = 1,
    size: int = 50,
):
    query = db.query(Resultado)
    filters = []
    if juego:
        filters.append(Resultado.juego == juego)
    if sorteo:
        filters.append(Resultado.sorteo == sorteo)
    if fecha_inicio:
        filters.append(Resultado.fecha >= fecha_inicio)
    if fecha_fin:
        filters.append(Resultado.fecha <= fecha_fin)
    if contienen_digitos:
        digitos = contienen_digitos.strip()
        num_conditions = []
        for d in digitos:
            num_conditions.append(
                or_(
                    cast(Resultado.n1, String).like(f"%{d}%"),
                    cast(Resultado.n2, String).like(f"%{d}%"),
                    cast(Resultado.n3, String).like(f"%{d}%"),
                )
            )
        if num_conditions:
            filters.append(and_(*num_conditions))

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    results = query.order_by(desc(Resultado.fecha)).offset((page - 1) * size).limit(size).all()
    return results, total


def get_rango_fechas(db: Session, juego: str):
    result = db.query(
        func.min(Resultado.fecha).label("min_fecha"),
        func.max(Resultado.fecha).label("max_fecha"),
    ).filter(Resultado.juego == juego).first()
    return result.min_fecha, result.max_fecha


def get_frecuencias(db: Session, juego: str, sorteo: Optional[str] = None, dias: int = 30):
    desde = date.today() - timedelta(days=dias)
    query = db.query(Resultado).filter(
        Resultado.juego == juego,
        Resultado.fecha >= desde,
    )
    if sorteo:
        query = query.filter(Resultado.sorteo == sorteo)

    resultados = query.all()

    conteos = {}
    total = 0
    for r in resultados:
        for n in [r.n1, r.n2, r.n3]:
            conteos[n] = conteos.get(n, 0) + 1
            total += 1
        if r.n4 is not None:
            conteos[r.n4] = conteos.get(r.n4, 0) + 1
            total += 1

    frecuencias = [
        {"numero": n, "frecuencia": f, "porcentaje": round(f / total * 100, 1) if total else 0}
        for n, f in sorted(conteos.items(), key=lambda x: x[1], reverse=True)
    ]
    return frecuencias


def get_atrasados(db: Session, juego: str, sorteo: Optional[str] = None):
    query = db.query(Resultado).filter(Resultado.juego == juego)
    if sorteo:
        query = query.filter(Resultado.sorteo == sorteo)

    resultados = query.order_by(Resultado.fecha).all()

    ultima_fecha_por_numero = {}
    for r in resultados:
        for n in [r.n1, r.n2, r.n3]:
            if n not in ultima_fecha_por_numero or r.fecha > ultima_fecha_por_numero[n]:
                ultima_fecha_por_numero[n] = r.fecha
        if r.n4 is not None:
            if r.n4 not in ultima_fecha_por_numero or r.fecha > ultima_fecha_por_numero[r.n4]:
                ultima_fecha_por_numero[r.n4] = r.fecha

    rango = get_rango_fechas(db, juego)
    hoy = rango[1] if rango[1] else date.today()

    max_num = 9
    atrasados = []
    for n in range(0, max_num + 1):
        ultima = ultima_fecha_por_numero.get(n)
        if ultima:
            dias = (hoy - ultima).days
        else:
            dias = 999
        atrasados.append({"numero": n, "dias_sin_salir": dias})

    return sorted(atrasados, key=lambda x: x["dias_sin_salir"], reverse=True)


def search_charada(db: Session, texto: str):
    texto_limpio = re.sub(r"[^\w\sáéíóúñ]", " ", texto.lower())
    palabras = texto_limpio.split()

    all_entries = db.query(Charada).all()
    significado_map = {}
    for c in all_entries:
        sigs = json.loads(c.significados)
        for sig in sigs:
            sig_lower = sig.lower()
            if sig_lower not in significado_map:
                significado_map[sig_lower] = c

    resultados = []
    for i, palabra in enumerate(palabras):
        if palabra in significado_map:
            c = significado_map[palabra]
            resultados.append({
                "palabra": palabra,
                "numero": c.numero,
                "significado": json.loads(c.significados)[0],
                "posicion": i,
            })
    return resultados


def get_adivinanza_hoy(db: Session):
    from datetime import date
    hoy = date.today()
    return db.query(Adivinanza).filter(Adivinanza.fecha == hoy).first()


def bulk_insert_posibles_salir(db: Session, registros: list[dict]):
    for r in registros:
        existing = db.query(PosibleSalir).filter(
            PosibleSalir.fecha == r["fecha"],
            PosibleSalir.sorteo == r["sorteo"],
        ).first()
        if existing:
            existing.numeros = r["numeros"]
        else:
            db.add(PosibleSalir(**r))
    db.commit()


def get_posibles_salir(db: Session, fecha: Optional[date] = None, sorteo: Optional[str] = None):
    query = db.query(PosibleSalir)
    if fecha:
        query = query.filter(PosibleSalir.fecha == fecha)
    if sorteo:
        query = query.filter(PosibleSalir.sorteo == sorteo)
    results = query.order_by(desc(PosibleSalir.fecha)).all()
    parsed = []
    for r in results:
        nums = [int(x.strip()) for x in r.numeros.split(",") if x.strip()]
        parsed.append({
            "fecha": r.fecha.isoformat(),
            "sorteo": r.sorteo,
            "numeros": nums,
        })
    return parsed


def get_charada_enriquecida(db: Session, numero: Optional[int] = None):
    query = db.query(Charada)
    if numero is not None:
        query = query.filter(Charada.numero == numero)
    entries = query.order_by(Charada.numero).all()
    result = []
    for e in entries:
        significados = json.loads(e.significados) if e.significados else []
        palabras_clave = json.loads(e.palabras_clave) if e.palabras_clave else []
        result.append({
            "numero": e.numero,
            "significados": significados,
            "categoria": e.categoria or "general",
            "palabras_clave": palabras_clave,
        })
    return result
