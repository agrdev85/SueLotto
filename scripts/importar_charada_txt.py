import re
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Charada
from backend.charada_engine import inferir_categoria, extraer_palabras_clave


def parse_charada_txt(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    entries = []
    pattern = re.compile(r"\((\d+),\s*(\d+),\s*'([^']+)'\)")
    for match in pattern.finditer(text):
        _, numero_ch, significado_str = match.groups()
        numero = int(numero_ch)
        significados_raw = significado_str.strip()
        significados = [s.strip() for s in re.split(r",\s*|;\s*", significados_raw) if s.strip()]
        entries.append({
            "numero": numero,
            "significados": significados,
        })

    entries.sort(key=lambda e: e["numero"])
    return entries


def populate_db(db: Session, entries: list[dict]):
    db.query(Charada).delete()

    count = 0
    for entry in entries:
        significados = entry["significados"]
        db.add(Charada(
            numero=entry["numero"],
            significados=json.dumps(significados, ensure_ascii=False),
            categoria=inferir_categoria(significados),
            palabras_clave=json.dumps(
                extraer_palabras_clave(significados),
                ensure_ascii=False
            ),
        ))
        count += 1

    db.commit()
    return count


def save_to_json(entries: list[dict], path: str):
    output = []
    for entry in entries:
        output.append({
            "numero": entry["numero"],
            "significados": entry["significados"],
            "categoria": inferir_categoria(entry["significados"]),
            "palabras_clave": extraer_palabras_clave(entry["significados"]),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return len(output)


if __name__ == "__main__":
    source = os.path.join(os.path.dirname(__file__), "..", "..", "Desktop", "charada.txt")
    json_out = os.path.join(os.path.dirname(__file__), "..", "data", "charada.json")

    if not os.path.exists(source):
        source = os.path.expanduser("~/Desktop/charada.txt")

    if not os.path.exists(source):
        print(f"No se encuentra charada.txt en: {source}")
        sys.exit(1)

    print(f"Leyendo {source}...")
    entries = parse_charada_txt(source)
    print(f"Parseadas {len(entries)} entries ({entries[0]['numero']}-{entries[-1]['numero']})")

    init_db()
    db = SessionLocal()
    try:
        count = populate_db(db, entries)
        print(f"Insertados {count} registros en BD")
    finally:
        db.close()

    count_json = save_to_json(entries, json_out)
    print(f"Guardado {count_json} entries en {json_out}")
    print("OK")
