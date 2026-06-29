"""
Pobla la tabla Charada desde data/charada_cruda.sql (formato crudo).
Cada línea: (id, numero_ch, 'significado1, significado2, ...')
Los significados vienen separados por coma en un solo string.
"""

import sys
import os
import re
import json
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Charada
from backend.charada_engine import inferir_categoria, extraer_palabras_clave


def parse_sql_crudo(path: str) -> dict[int, list[str]]:
    """Parsea el SQL crudo y devuelve {numero: [significados_deduplicados]}."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    data = {}
    pattern = re.compile(r"\((\d+),\s*(\d+),\s*'(.+?)'\)[,;]?", re.DOTALL)
    for match in pattern.finditer(text):
        numero = int(match.group(2))
        significado_raw = match.group(3).strip()

        significados = [
            s.strip() for s in re.split(r",\s*", significado_raw) if s.strip()
        ]

        vistos = set()
        unicos = []
        for s in significados:
            s_lower = s.lower()
            if s_lower not in vistos and len(s) > 1:
                vistos.add(s_lower)
                unicos.append(s)

        if numero in data:
            existentes = {e.lower() for e in data[numero]}
            for s in unicos:
                if s.lower() not in existentes:
                    existentes.add(s.lower())
                    data[numero].append(s)
        else:
            data[numero] = unicos

    return data


def main():
    print("=== Poblando Charada desde SQL Crudo ===")

    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "charada_cruda.sql",
    )

    if not os.path.exists(sql_path):
        print(f"[ERROR] No se encuentra {sql_path}")
        sys.exit(1)

    data = parse_sql_crudo(sql_path)
    print(f"[OK] Parseados {len(data)} números")

    total_sigs = sum(len(sigs) for sigs in data.values())
    print(f"     Total significados (únicos): {total_sigs}")

    db = SessionLocal()
    try:
        count = 0
        for numero in sorted(data.keys()):
            significados = data[numero]
            categoria = inferir_categoria(significados)
            palabras_clave = extraer_palabras_clave(significados, top_n=15)

            existing = db.query(Charada).filter(Charada.numero == numero).first()
            if existing:
                existing.significados = json.dumps(significados, ensure_ascii=False)
                existing.categoria = categoria
                existing.palabras_clave = json.dumps(palabras_clave, ensure_ascii=False)
            else:
                db.add(Charada(
                    numero=numero,
                    significados=json.dumps(significados, ensure_ascii=False),
                    categoria=categoria,
                    palabras_clave=json.dumps(palabras_clave, ensure_ascii=False),
                ))
            count += 1

        db.commit()
        print(f"[OK] Insertados/actualizados {count} registros")

        for num in [0, 1, 5, 23]:
            entry = db.query(Charada).filter(Charada.numero == num).first()
            if entry:
                sigs = json.loads(entry.significados)
                kws = json.loads(entry.palabras_clave) if entry.palabras_clave else []
                print(f"     Número {num}: {len(sigs)} significados, cat={entry.categoria}, {len(kws)} keywords")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
