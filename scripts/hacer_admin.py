"""Convierte a un usuario en administrador (para ver el Gestor de BD).

Uso:
    python scripts/hacer_admin.py TU_USUARIO

Conecta al servidor que esté corriendo en FASTAPI_URL (por defecto
http://localhost:8000). Para producción, pon la URL en la variable:

    FASTAPI_URL=https://tu-app.onrender.com python scripts/hacer_admin.py TU_USUARIO

El ADMIN_API_TOKEN se toma del archivo .env (o de la variable de entorno).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    print("Falta 'httpx'. Instálalo con:  pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    username = sys.argv[1].strip()

    db_url = os.getenv("DATABASE_URL", "").strip()
    if db_url.startswith("postgres"):
        # ── Modo directo a la BD (producción en Render) ──────────────
        # Actualiza la tabla users directamente, sin pasar por la API
        # pública (que en Render solo expone el frontend).
        from backend.database import SessionLocal
        from backend.models import User

        try:
            db = SessionLocal()
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"El usuario '{username}' no existe. Revisa el nombre exacto.")
                sys.exit(1)
            user.tier = "admin"
            db.commit()
            print(f"OK: el usuario '{username}' ahora es admin.")
            print("Cierra y vuelve a abrir la app, e inicia sesión con ese usuario.")
            print("Verás el menú 🗄️ Gestor BD en la barra lateral.")
        except Exception as e:
            print(f"Error conectando a la BD: {e}")
            print("Revisa que DATABASE_URL apunte al Postgres de producción.")
            sys.exit(1)
        finally:
            db.close()
        return

    # ── Modo API (desarrollo local) ────────────────────────────────
    token = os.getenv("ADMIN_API_TOKEN", "").strip()
    if not token:
        print("No encuentro ADMIN_API_TOKEN. ¿Está en .env?")
        sys.exit(1)

    url = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")
    r = httpx.post(
        f"{url}/api/admin/set-tier",
        json={"username": username, "tier": "admin"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )

    if r.status_code == 200:
        print(f"OK: el usuario '{username}' ahora es admin.")
        print("Cierra y vuelve a abrir la app, e inicia sesión con ese usuario.")
        print("Verás el menú 🗄️ Gestor BD en la barra lateral.")
    elif r.status_code == 404:
        print(f"El usuario '{username}' no existe. Revisa el nombre exacto.")
    else:
        print(f"Error ({r.status_code}): {r.text[:200]}")
        sys.exit(1)


if __name__ == "__main__":
    main()