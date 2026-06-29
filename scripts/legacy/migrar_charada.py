"""
Migra la tabla Charada al nuevo esquema con columnas Text para JSON.
DROP + recreate con datos del charada.json.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import Charada


def main():
    print("=== Migrando Charada DB ===")

    Charada.__table__.drop(engine, checkfirst=True)
    print("[OK] Tabla charada eliminada")

    Base.metadata.create_all(bind=engine)
    print("[OK] Tabla charada recreada con nuevo esquema (significados Text, palabras_clave Text)")


if __name__ == "__main__":
    main()
