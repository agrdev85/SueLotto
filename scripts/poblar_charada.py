"""
Script para poblar la tabla Charada desde data/charada.json.
Ejecutar una sola vez al iniciar el proyecto.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db
from backend.charada_engine import poblar_charada_db


def main():
    print("=== Poblando Charada Cubana ===")
    init_db()

    charada_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "charada.json",
    )

    db = SessionLocal()
    try:
        total = poblar_charada_db(db, charada_path)
        print(f"✅ Insertados {total} registros de Charada Cubana")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
