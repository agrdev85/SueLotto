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