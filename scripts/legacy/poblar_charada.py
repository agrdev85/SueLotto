"""
Pobla la tabla Charada desde data/charada.json con el nuevo esquema.
Almacena significados[] como JSON Text y palabras_clave[] como JSON Text.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.charada_engine import poblar_charada_db


def main():
    print("=== Poblando Charada Cubana (nuevo esquema) ===")

    charada_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "charada.json",
    )

    db = SessionLocal()
    try:
        total = poblar_charada_db(db, charada_path)
        print(f"[OK] Insertados {total} registros de Charada Cubana con JSON arrays")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
