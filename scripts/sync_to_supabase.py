"""
Migrate data from local SQLite to a remote PostgreSQL database
(Render, Supabase, etc.).

Usage:
    python scripts/sync_to_supabase.py

The remote connection string is read from:
  1. The PG_TARGET_URL environment variable, or
  2. A temporary change of DATABASE_URL in .env

Example (Render):
    export PG_TARGET_URL="postgresql://user:pass@dpg-xxxx-a.onrender.com:5432/suenalotto?sslmode=require"
    python scripts/sync_to_supabase.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

TARGET_URL = os.getenv("PG_TARGET_URL") or os.getenv("DATABASE_URL", "")
if not TARGET_URL or "postgresql" not in TARGET_URL:
    print("ERROR: PG_TARGET_URL no está configurado.")
    print("Exporta la URL de PostgreSQL del servidor de producción, por ejemplo:")
    print('  export PG_TARGET_URL="postgresql://user:pass@host:5432/dbname?sslmode=require"')
    sys.exit(1)


def main():
    from backend.database import SessionLocal
    from sqlalchemy import create_engine
    from backend.models import Resultado, Charada, Adivinanza, PosibleSalir, User, Bet, UserUsage, OtherGameResult

    local_db = SessionLocal()
    remote_engine = create_engine(TARGET_URL, pool_pre_ping=True)
    remote_db = SessionLocal(bind=remote_engine)
    remote_db.commit()  # test connection

    print("Conectado a la base remota. Verificando esquema...")

    import subprocess
    env = os.environ.copy()
    env["DATABASE_URL"] = TARGET_URL
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
    )
    print(result.stdout)
    if result.returncode != 0:
        print("Migración Alembic falló:", result.stderr)
        remote_db.close()
        local_db.close()
        return

    tables = [
        ("resultados", Resultado, ["fecha", "juego", "sorteo"]),
        ("charada", Charada, ["numero"]),
        ("adivinanzas", Adivinanza, ["fecha"]),
        ("posible_salir", PosibleSalir, ["fecha", "sorteo"]),
        ("users", User, ["username"]),
        ("bets", Bet, []),
        ("user_usage", UserUsage, ["user_id", "fecha"]),
        ("other_games", OtherGameResult, ["game_name", "fecha"]),
    ]

    for table_name, model, unique_on in tables:
        print(f"\nSincronizando {table_name}...")
        rows = local_db.query(model).all()
        print(f"  Local: {len(rows)} filas")

        if not rows:
            continue

        existing_count = remote_db.query(model).count()
        print(f"  Remoto antes: {existing_count} filas")

        inserted = 0
        skipped = 0
        for row in rows:
            try:
                remote_db.merge(row)
                inserted += 1
            except Exception as e:
                print(f"  Error en {table_name} id={row.id}: {e}")
                skipped += 1

        remote_db.commit()
        after_count = remote_db.query(model).count()
        print(f"  Remoto después: {after_count} filas (insertadas={inserted}, omitidas={skipped})")

    remote_db.close()
    local_db.close()
    print("\n✅ Sincronización completada!")


if __name__ == "__main__":
    main()
