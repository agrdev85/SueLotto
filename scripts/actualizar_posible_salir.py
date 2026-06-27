"""
Actualiza la tabla posible_salir con los cálculos del día actual.
Ejecutar diariamente (cron job).
Uso: python scripts/actualizar_posible_salir.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.lottery_analyzer import obtener_posibles_salir
from backend.crud import bulk_insert_posibles_salir


def actualizar(db: Session, juego: str):
    print(f"🔄 Actualizando {juego}...")
    for sorteo in ["E", "M"]:
        try:
            resultado = obtener_posibles_salir(db, juego, date.today(), sorteo, use_ml=True)
            if resultado["numeros"]:
                registro = {
                    "fecha": date.today(),
                    "sorteo": sorteo,
                    "numeros": ",".join(str(n) for n in resultado["numeros"]),
                }
                bulk_insert_posibles_salir(db, [registro])
                print(f"  ✅ {juego} {sorteo}: {len(resultado['numeros'])} números guardados")
            else:
                print(f"  ⚠️ {juego} {sorteo}: sin resultados")
        except Exception as e:
            print(f"  ❌ {juego} {sorteo}: {e}")

    db.commit()


def main():
    init_db()
    db = SessionLocal()
    try:
        print(f"🚀 Actualizando posible_salir para {date.today()}...")
        actualizar(db, "Pick 3")
        actualizar(db, "Pick 4")
        print("🎉 Actualización completada!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
