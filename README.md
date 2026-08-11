# SueñaLotto — App Integral de Lotería con Charada Cubana

Análisis de la Florida Lottery (Pick 3, Pick 4 y otros juegos) con búsqueda por sueños, adivinanzas con IA, predicciones estadísticas y matriz de números. Frontend, API y mantenimiento automático de datos en un solo proceso.

## Stack Tecnológico

- **Backend**: FastAPI + SQLAlchemy ORM
- **Frontend**: Streamlit
- **BD**: SQLite en local (dev) / PostgreSQL vía `DATABASE_URL` (producción)
- **ML/IA**: Scikit-learn (Random Forest) + Google Gemini API (adivinanzas)
- **Pagos**: Qvapay
- **Despliegue**: Render.com (Web Service único: `web: bash start.sh`)

## Estructura

```
SueñaLotto/
├── app/                      # Frontend Streamlit
│   ├── main.py              # Página principal
│   └── pages/               # 1..8: jugadas, estadísticas, búsquedas, adivinanzas,
│                            #       matriz charada, gestor BD, soporte
├── backend/                  # API FastAPI
│   ├── main.py              # Endpoints + arranque de tareas programadas
│   ├── auto_updater.py      # Actualización automática diaria (cada 3 h) + catch-up
│   ├── keepalive.py         # Ping de mantenimiento interno
│   ├── db_manager.py        # Backups/restauraciones automáticas de la BD
│   ├── fl_api.py            # API oficial de la Florida Lottery
│   ├── fl_scraper.py        # Scraper de otros juegos (Lucky Money, etc.)
│   └── ...                  # auth, crud, models, schemas, analítica, email
├── scripts/                  # Utilidades (ver sección Scripts)
├── data/                     # Datos seed (charada.json, arrastrados) — el resto
│                             # (logs, PDFs, backups) se regenera en runtime
├── requirements.txt
├── Procfile                  # web: bash start.sh
└── start.sh                  # Arranca backend + frontend
```

## Instalación y Ejecución Local

```bash
git clone <repo> && cd SueñaLotto
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env            # llena las claves según tus servicios
./start.sh                      # lanza backend (8000) + frontend (8501)
```

`start.sh` arranca ambos procesos y registra los logs del backend en consola y en `data/backend.log`.

En el primer arranque la app inicializa la BD, importa la Charada desde `data/charada.json` y los resultados históricos desde la API/PDFs de floridalottery.com en segundo plano (no requiere intervención).

## Tareas Automáticas (sin intervención)

Todas se inician al arrancar el backend:

- **Auto-update diario**: cada 3 h (01:00, 04:00, 07:00, 10:00, 13:00, 16:00, 19:00, 22:00 hora del servidor) descarga los sorteos MIDDAY/EVENING de Pick 3 y Pick 4 (API oficial, con respaldo PDF) y actualiza otros juegos. Si la app estuvo dormida y los históricos están atrasados, un catch-up la recupera 20 s después de cada arranque.
- **Backups automáticos** de la BD en `data/backups/` (retención de 30).
- **Keepalive** interno (ping a `/health`).

Estado y logs: `data/auto_update_status.json`, `data/auto_update.log`, `data/backups/`.

## Scripts

| Script | Uso |
|--------|-----|
| `scripts/actualizar_resultados.py` | Actualización manual de resultados (API + PDF) |
| `scripts/hacer_admin.py` | Convierte un usuario en administrador |
| `scripts/sync_to_supabase.py` | Migra la BD local SQLite a PostgreSQL remoto |
| `scripts/importar_historicos.py` | Importa/extrae resultados desde los PDFs |

## API Endpoints (resumen)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check (puede usarse como ping externo) |
| `/api/resultados/ultimos` | GET | Últimos resultados por juego |
| `/api/resultados/historicos` | GET | Historial con filtros |
| `/api/estadisticas/frecuencias`, `/api/estadisticas/atrasados` | GET | Frecuencias y atrasos |
| `/api/predicciones` | GET | Predicciones ML |
| `/api/charada/buscar` | POST | Números por sueño |
| `/api/adivinanza/analizar` | POST | Análisis con IA |
| `/api/admin/...` | * | Gestión admin (usuarios, BD, backups) |

## Despliegue en Render.com

1. Sube el repositorio a GitHub y crea un **Web Service** desde Render apuntando al repo.
2. Build: `pip install -r requirements.txt`. Start command: lo toma del `Procfile` (`web: bash start.sh`).
3. Variables de entorno:
   - `DATABASE_URL` — PostgreSQL (Render incluye uno gratuito). **Importante:** en el tier gratuito el disco es efímero; sin Postgres los datos se perderían en cada redeploy.
   - `PUBLIC_URL` — URL pública de la app (`https://tu-app.onrender.com`), para el keepalive.
   - Opcionales: `GEMINI_API_KEY`, `SMTP_*`, `QVAPAY_*`, `ADMIN_API_TOKEN`, `KEEPALIVE_INTERVAL`.
4. **Anti-sleep**: el tier gratuito duerme la instancia sin tráfico externo. Configura un monitor gratuito (cron-job.org, UptimeRobot) que haga GET a `https://tu-app.onrender.com/health` cada 10–15 min. Al despertar, el catch-up automático actualiza los históricos.
5. El backend escucha en `BACKEND_PORT` (8000) y el frontend en `PORT` (Render inyecta `$PORT`).

## Notas

- Datos oficiales: https://www.floridalottery.com (API + PDFs `p3.pdf`/`p4.pdf`)
- La Charada Cubana contiene 100 números con significados tradicionales (`data/charada.json`)
- Sin API key de Gemini, el análisis de adivinanzas usa un fallback local