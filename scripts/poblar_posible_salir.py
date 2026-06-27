"""
Pobla la tabla posible_salir con datos históricos calculados.
Uso: python scripts/poblar_posible_salir.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Resultado
from backend.lottery_analyzer import obtener_posibles_salir
from backend.crud import bulk_insert_posibles_salir


def poblar_historicos(db: Session, juego: str = "Pick 3"):
    fechas = db.query(Resultado.fecha).filter(
        Resultado.juego == juego
    ).distinct().order_by(Resultado.fecha).all()

    fechas = [f[0] for f in fechas]
    print(f"📅 {len(fechas)} fechas únicas para {juego}")

    for i, fecha in enumerate(fechas):
        for sorteo in ["E", "M"]:
            try:
                resultado = obtener_posibles_salir(db, juego, fecha, sorteo, use_ml=False)
                if resultado["numeros"]:
                    registro = {
                        "fecha": fecha,
                        "sorteo": sorteo,
                        "numeros": ",".join(str(n) for n in resultado["numeros"]),
                    }
                    bulk_insert_posibles_salir(db, [registro])
            except Exception as e:
                print(f"  ⚠️ Error {juego} {fecha} {sorteo}: {e}")

        if (i + 1) % 200 == 0:
            print(f"  ✅ Procesadas {i + 1}/{len(fechas)} fechas...")
            db.commit()

    db.commit()
    print(f"✅ {juego} completado")


def main():
    init_db()
    db = SessionLocal()
    try:
        print("🚀 Poblando posible_salir histórica...")
        poblar_historicos(db, "Pick 3")
        poblar_historicos(db, "Pick 4")
        print("🎉 ¡Población completada!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
