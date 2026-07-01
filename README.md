# SueñaLotto - App Integral de Lotería con Charada Cubana

Análisis inteligente de la Florida Lottery (Pick 3 & Pick 4) con búsqueda por sueños, adivinanzas con IA y predicciones estadísticas.

## Stack Tecnológico

- **Backend API**: FastAPI (Python 3.9+)
- **Frontend**: Streamlit
- **Base de Datos**: SQLAlchemy ORM (SQLite dev / PostgreSQL prod)
- **ML**: Scikit-learn (Random Forest)
- **IA**: Google Gemini API (análisis de adivinanzas)
- **Despliegue**: Render.com

## Estructura del Proyecto

```
SueñaLotto/
├── app/                    # Frontend Streamlit
│   ├── main.py            # Página principal (Dashboard)
│   └── pages/
│       ├── 1_estadisticas.py     # Estadísticas detalladas
│       ├── 2_busqueda_historica.py  # Buscador histórico inteligente
│       ├── 3_busqueda_suenos.py     # Búsqueda en Charada Cubana
│       └── 4_adivinanzas.py        # Adivinanzas con IA
├── backend/                # Backend FastAPI
│   ├── main.py            # API endpoints
│   ├── database.py        # Conexión a BD
│   ├── models.py          # Modelos SQLAlchemy
│   ├── schemas.py         # Schemas Pydantic
│   ├── crud.py            # Operaciones de base de datos
│   ├── lottery_analyzer.py # Análisis estadístico y ML
│   ├── charada_engine.py  # Motor de búsqueda en Charada
│   └── adivinanza_ai.py   # Integración con Gemini AI
├── scripts/               # Scripts de utilidad
│   ├── importar_historicos.py  # Importación inicial de datos
│   ├── actualizar_resultados.py # Actualización diaria
│   └── poblar_charada.py  # Poblar tabla Charada
├── data/                  # Datos estáticos
│   ├── charada.json       # 100 números de la Charada Cubana
│   └── adivinanzas_ejemplo.txt  # Adivinanzas de ejemplo
├── requirements.txt
├── Procfile
├── .env
└── README.md
```

## Instalación y Ejecución Local

### 1. Clonar y configurar entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tu API key de Gemini (opcional)
```

### 3. Inicializar base de datos y poblar Charada

```bash
python scripts/poblar_charada.py
```

### 4. Importar datos históricos

```bash
python scripts/importar_historicos.py
```

### 5. Iniciar la API

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 6. Iniciar el frontend (en otra terminal)

```bash
streamlit run app/main.py
```

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/resultados/ultimos` | GET | Últimos resultados |
| `/api/resultados/historicos` | GET | Búsqueda histórica con filtros |
| `/api/estadisticas/frecuencias` | GET | Números más frecuentes |
| `/api/estadisticas/atrasados` | GET | Números más atrasados |
| `/api/predicciones` | GET | Predicciones ML |
| `/api/charada/buscar` | POST | Buscar números por sueño |
| `/api/adivinanza/hoy` | GET | Adivinanza del día |
| `/api/adivinanza/analizar` | POST | Analizar adivinanza con IA |

## Despliegue en Render

1. Conectar repositorio de GitHub
2. Crear Web Service para la API: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Crear Web Service para Frontend: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`
4. Configurar Cron Job: `python scripts/actualizar_resultados.py` (diario 3:00 AM)
5. Variables de entorno: `DATABASE_URL`, `GEMINI_API_KEY`, `ENVIRONMENT`, `FASTAPI_URL`

## Notas

- Los datos históricos se obtienen de: https://files.floridalottery.com/exptkt/p3.htm y p4.htm
- La Charada Cubana contiene 100 números con sus significados tradicionales
- Las predicciones ML usan Random Forest con features de frecuencia y atraso
- Sin API key de Gemini, el análisis de adivinanzas funciona con fallback local
