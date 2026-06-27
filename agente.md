# PROYECTO: SueñaLotto - App Integral de Lotería con Charada y Adivinanzas Cubanas

## OBJETIVO PRINCIPAL
Crear una aplicación web completa para el análisis de la lotería Florida (Pick 3 y Pick 4), que integre:
1. Datos históricos y actualizados en tiempo real.
2. Análisis estadístico avanzado (números calientes, fríos, atrasados, predicciones).
3. Búsqueda por sueños (Charada Cubana) con extracción de números en orden de aparición.
4. Interpretación de Adivinanzas diarias con ayuda de IA (API Gemini gratuita).
5. Una interfaz amigable, moderna, minimalista y fácil de usar.

## STACK TECNOLÓGICO
- **Backend**: Python 3.9+ con FastAPI
- **Frontend**: Streamlit (para rapidez y visualización)
- **Base de Datos**: SQLAlchemy ORM con soporte para SQLite (desarrollo) y PostgreSQL (producción)
- **Procesamiento de Datos**: Pandas, NumPy
- **Machine Learning**: Scikit-learn
- **IA**: Google Gemini API (u otra gratuita)
- **Despliegue**: Render.com

## ESTRUCTURA DEL PROYECTO
SueñaLotto/
??? app/
? ??? main.py
? ??? pages/
? ??? estadisticas.py
? ??? busqueda_suenos.py
? ??? adivinanzas.py
??? backend/
? ??? main.py
? ??? models.py
? ??? schemas.py
? ??? crud.py
? ??? database.py
? ??? lottery_analyzer.py
? ??? charada_engine.py
? ??? adivinanza_ai.py
??? data/
? ??? charada.json
? ??? adivinanzas_ejemplo.txt
??? scripts/
? ??? importar_historicos.py
? ??? actualizar_resultados.py
??? requirements.txt
??? Procfile
??? .env
??? README.md


## INSTRUCCIONES DETALLADAS DE IMPLEMENTACIÓN

### 1. Modelos de Base de Datos (backend/models.py)
Crear las siguientes tablas usando SQLAlchemy:

**Tabla `resultados`**:
- `id`: Integer, Primary Key
- `fecha`: Date
- `juego`: String (Pick 3 o Pick 4)
- `sorteo`: String (E para Evening, M para Midday)
- `n1`: Integer
- `n2`: Integer
- `n3`: Integer
- `n4`: Integer (opcional, solo para Pick 4)

**Tabla `charada`**:
- `id`: Integer, Primary Key
- `numero`: Integer
- `significado`: String
- `categoria`: String (opcional)

**Tabla `adivinanzas`**:
- `id`: Integer, Primary Key
- `fecha`: Date, único
- `texto`: String

### 2. Script de Importación de Históricos (scripts/importar_historicos.py)

**Este es el script más crítico. Debe parsear correctamente los PDFs o las URLs.**

#### Lógica de Parseo:

1. **Obtener el contenido**: Descargar de `https://files.floridalottery.com/exptkt/p3.htm` y `https://files.floridalottery.com/exptkt/p4.htm`.

2. **Identificar el bloque de datos**: Buscar la frase "E: Evening and M: Midday drawing results".

3. **Extraer con Expresiones Regulares**:
   - Para Pick 3: `(\d{2}/\d{2}/\d{2})\s+([EM])\s+(\d)\s*-\s*(\d)\s*-\s*(\d)`
   - Para Pick 4: `(\d{2}/\d{2}/\d{2})\s+([EM])\s+(\d)\s*-\s*(\d)\s*-\s*(\d)\s*-\s*(\d)`

4. **Procesar cada coincidencia**:
   - Convertir fecha de `MM/DD/YY` a `YYYY-MM-DD`.
   - Determinar el juego (Pick 3 o Pick 4) según la URL.
   - Crear un diccionario con: fecha, juego, sorteo (E/M), n1, n2, n3, n4 (si existe).

5. **Manejo de errores**:
   - Saltar líneas que no coincidan con el patrón.
   - Si hay fechas duplicadas, conservar la primera o la más completa.
   - Intentar corregir años si están mal formateados (ej: `04/05` ? `04/05/19`).

6. **Población de la BD**: Usar `bulk_insert_mappings` para inserción masiva.

### 3. Script de Actualización Diaria (scripts/actualizar_resultados.py)
- Similar al de importación, pero solo descarga y procesa fechas posteriores a la última registrada.
- Se programará como Cron Job en Render.

### 4. Módulo de Análisis (backend/lottery_analyzer.py)
Implementar estas funciones:
- `calcular_frecuencias(juego, dias=30)`: Devuelve los números más frecuentes en los últimos N días.
- `calcular_atrasados(juego)`: Devuelve los números que más tiempo llevan sin salir.
- `generar_predicciones(juego)`: Usa un modelo simple de Scikit-learn (ej: Random Forest) para predecir probabilidades basadas en frecuencia y atraso.

### 5. Motor de Búsqueda por Sueños (backend/charada_engine.py)
- Cargar la tabla `charada` en un diccionario al iniciar.
- Función `buscar_en_sueno(texto)`:
  1. Limpiar texto (minúsculas, sin puntuación).
  2. Tokenizar en palabras.
  3. Buscar cada palabra en el diccionario.
  4. Devolver los números en el orden de aparición.

### 6. Módulo de IA para Adivinanzas (backend/adivinanza_ai.py)
- Usar Gemini API (gratuita) o similar.
- Función `analizar_adivinanza(texto_adivinanza, interpretacion_usuario)`:
  - Crear un prompt que pida a la IA que actúe como experto en charada cubana.
  - El prompt debe incluir ejemplos de cómo se relacionan palabras clave con números (ej: "perro" ? 15, "dinero" ? 10, 21, 22).
  - La IA debe devolver una lista de números sugeridos y su razonamiento.

### 7. Interfaz de Usuario (Streamlit)

**Página Principal (app/main.py)**:
- Mostrar los últimos resultados de Pick 3 y Pick 4.
- Gráficos de barras con los números más frecuentes.
- Tabla con los números más atrasados.

**Página de Estadísticas (app/pages/estadisticas.py)**:
- Selector para elegir el juego (Pick 3 o Pick 4).
- Selector para el período (7, 15, 30 días).
- Mostrar todas las estadísticas calculadas.

**Página de Búsqueda de Sueños (app/pages/busqueda_suenos.py)**:
- Un `st.text_area` para que el usuario describa su sueño.
- Un botón "Buscar".
- Mostrar los números encontrados en orden de aparición.
- Opcional: Mostrar el texto del sueño con los números resaltados.

**Página de Adivinanzas (app/pages/adivinanzas.py)**:
- Mostrar la adivinanza del día (desde la tabla `adivinanzas`).
- Un `st.text_area` para que el usuario escriba su interpretación.
- Un botón "Obtener Sugerencias con IA".
- Mostrar el resultado de la IA.

### 8. Despliegue en Render
- Conectar el repositorio de GitHub.
- Configurar variables de entorno: `DATABASE_URL`, `GEMINI_API_KEY`, `ENVIRONMENT`.
- Comando de inicio: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`

### 9. Archivos Adicionales

**requirements.txt**:

fastapi==0.100.1
uvicorn==0.23.2
streamlit==1.25.0
sqlalchemy==2.0.19
psycopg2-binary==2.9.7
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
plotly==5.15.0
requests==2.31.0
beautifulsoup4==4.12.2
pdfplumber==0.10.3
python-dotenv==1.0.0
google-generativeai==0.3.0


.env
DATABASE_URL=sqlite:///./suelotto.db
GEMINI_API_KEY=tu_api_key_aqui
ENVIRONMENT=development


## ENTREGABLE FINAL
El asistente debe generar el código completo de la aplicación con todas las funcionalidades descritas, listo para ejecutarse y desplegarse.

## NOTAS ADICIONALES PARA LA IA
- Asegurarse de que el parser de datos históricos maneje correctamente las fechas en formato MM/DD/YY.
- La lógica de búsqueda por sueños debe ser precisa y rápida.
- El prompt para la IA en la sección de adivinanzas debe ser detallado y culturalmente relevante para el contexto cubano.
- La interfaz debe ser intuitiva y atractiva, con un diseño limpio.


Las url de los historicos son estas
pick3 - https://files.floridalottery.com/exptkt/p3.htm?_gl
pick4 - https://files.floridalottery.com/exptkt/p4.htm?_gl

