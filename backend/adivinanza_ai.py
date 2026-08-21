import os
import sys
import logging
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
logger = logging.getLogger("adivinanza_ai")

# Quick self-test on import
_gemini_disponible = False
if GEMINI_API_KEY:
    try:
        from google import genai as genai_client
        client = genai_client.Client(api_key=GEMINI_API_KEY)
        # Just check the API key format is plausible
        if GEMINI_API_KEY.startswith("AIza") or len(GEMINI_API_KEY) > 20:
            _gemini_disponible = True
        else:
            logger.warning("GEMINI_API_KEY tiene formato inesperado, se usará fallback local")
    except Exception as e:
        logger.warning(f"Error al inicializar Gemini: {e}")
else:
    logger.warning("GEMINI_API_KEY no configurada, se usará análisis local")

# Cargar la tabla Charada 1-100 DESDE EL JSON local (sin necesidad de IA)
_CHARADA_DATA = None
try:
    CHARADA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "charada.json")
    with open(CHARADA_PATH, "r", encoding="utf-8") as f:
        _CHARADA_DATA = json.load(f)
    # Indexar por número y por palabras clave para búsquedas rápidas
    _num_to_entry = {e["numero"]: e for e in _CHARADA_DATA}
    _keyword_map = {}  # palabra_lower -> list of (numero, significado)
    for entry in _CHARADA_DATA:
        for sig in entry.get("significados", []):
            sig_lower = sig.lower()
            # Agregar cada palabra significativa
            for word in sig_lower.split():
                if len(word) > 2:
                    if word not in _keyword_map:
                        _keyword_map[word] = []
                    _keyword_map[word].append((entry["numero"], sig))
    # También indexar las palabras_clave
    for entry in _CHARADA_DATA:
        for kw in entry.get("palabras_clave", []):
            kw_lower = kw.lower()
            if kw_lower not in _keyword_map:
                _keyword_map[kw_lower] = []
            _keyword_map[kw_lower].append((entry["numero"], kw))
except Exception as e:
    logger.error(f"No se pudo cargar la tabla Charada: {e}")
    _CHARADA_DATA = None
    _num_to_entry = {}
    _keyword_map = {}


def gemini_activo() -> bool:
    return _gemini_disponible


def _buscar_en_charada(texto: str) -> list[dict]:
    """Busca números de la charada relacionados con el texto dado.
    Revisa tanto los 'significados' como las 'palabras_clave' de los 100 números.
    Devuelve una lista de {numero, significado} únicos ordenados por relevancia."""
    if not texto or not _keyword_map:
        return []

    texto_lower = texto.lower()
    encontrados: dict[int, str] = {}  # numero -> mejor significado

    # 1. Buscar por palabras clave directas en el texto
    for palabra, matches in _keyword_map.items():
        if palabra in texto_lower:
            for numero, significado in matches:
                if numero not in encontrados:
                    encontrados[numero] = significado

    # 2. Buscar por superposición de palabras: contar cuántas palabras del texto
    #    aparecen en los significados de cada número
    if not encontrados:
        # Contar coincidencias por número
        contador_numeros: dict[int, int] = {}
        for palabra in texto_lower.split():
            if palabra in _keyword_map:
                for numero, significado in _keyword_map[palabra]:
                    contador_numeros[numero] = contador_numeros.get(numero, 0) + 1
        # Ordenar por número de coincidencias
        for numero, count in sorted(contador_numeros.items(), key=lambda x: x[1], reverse=True):
            if numero not in encontrados and count >= 1:
                # Obtener un significado para este número
                matches = _keyword_map.get(palabra, [])
                if matches:
                    encontrados[numero] = matches[0][1]

    # 3. Si aún no hay resultados, buscar en los significados completos
    if not encontrados and _CHARADA_DATA:
        for entry in _CHARADA_DATA:
            sigs_lower = [s.lower() for s in entry.get("significados", [])]
            # Verificar si alguna palabra del texto está en los significados
            for palabra in texto_lower.split():
                if any(palabra in sig for sig in sigs_lower):
                    if entry["numero"] not in encontrados:
                        encontrados[entry["numero"]] = entry["significados"][0]
                    break

    # Ordenar: primeros los que tienen más coincidencias, luego por número
    resultados = list(encontrados.items())
    resultados.sort(key=lambda x: (x[1] is not None, x[0]))
    return [{"numero": num, "razon": sig} for num, sig in resultados]


def _fallback_analysis(adivinanza: str, interpretacion: str) -> dict:
    """Análisis usando la tabla Charada 1-100 cargada localmente."""
    texto_combinado = (adivinanza + " " + interpretacion).lower()

    sugerencias = _buscar_en_charada(texto_combinado)

    # Si no encuentra nada con el análisis de palabras, intentar con categorías
    if not sugerencias and _CHARADA_DATA:
        # Buscar por categorías generales
        categorias_prioridad = ["animales", "naturaleza", "elementos", "sentimientos", "conceptos"]
        texto_words = set(texto_combinado.split())
        for entry in _CHARADA_DATA:
            cat = entry.get("categoria", "")
            if cat in categorias_prioridad:
                sigs_lower = [s.lower() for s in entry.get("significados", [])]
                if any(w in texto_words for w in sigs_lower):
                    # Evitar duplicados
                    if entry["numero"] not in [s["numero"] for s in sugerencias]:
                        sugerencias.append({
                            "numero": entry["numero"],
                            "razon": f"Se detectó la categoría '{cat}' en tu adivinanza. Significado principal: {entry['significados'][0]}",
                        })

    # Si aún no hay sugerencias, usar números por defecto de la charada
    if not sugerencias:
        sugerencias = [
            {"numero": 1, "razon": "Asociado al caballo y a la iniciación en la charada cubana."},
            {"numero": 7, "razon": "Asociado al agua, el caracol y a la suerte popular."},
            {"numero": 21, "razon": "Asociado a la maja y a la mujer en la tradición."},
        ]

    # Quitar duplicados por número
    seen_nums = set()
    unique_sugerencias = []
    for s in sugerencias:
        if s["numero"] not in seen_nums:
            seen_nums.add(s["numero"])
            unique_sugerencias.append(s)

    return {
        "sugerencias": unique_sugerencias[:5],
        "razonamiento": "",
    }


def analizar_adivinanza(adivinanza: str, interpretacion: str, api_key: str = None) -> dict:
    key = api_key or GEMINI_API_KEY

    # Intentar con Gemini API si está disponible
    if _gemini_disponible and key:
        try:
            from google import genai as genai_client

            client = genai_client.Client(api_key=key)

            PROMPT_TEMPLATE = """Eres un experto en la interpretación de sueños y adivinanzas (números 1-100) y su relación con la lotería.

            Tu tarea es analizar la siguiente adivinanza y la interpretación que el usuario ha dado,
            y sugerir números de la charada (1-100) que podrían estar relacionados.

            Usa la tabla charada como referencia: cada número 1-100 tiene significados asociados.
            Por ejemplo:
            - 1 = caballo
            - 2 = mariposa
            - 7 = caracol, agua
            - 21 = maja
            - 100 = inodoro

            ADIVINANZA: {adivinanza}

            INTERPRETACIÓN DEL USUARIO: {interpretacion}

            Por favor, proporciona:
            1. Una lista de 3-5 números sugeridos (1-100) ordenados por relevancia
            2. Una breve explicación de por qué cada número es relevante

            Responde en formato JSON:
            {{
              "sugerencias": [
                {{"numero": 1, "razon": "El caballo aparece en la adivinanza"}},
                ...
              ],
              "razonamiento": "Texto explicando el análisis completo"
            }}
            """

            prompt = PROMPT_TEMPLATE.format(
                adivinanza=adivinanza,
                interpretacion=interpretacion,
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            import re
            text = response.text
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            logger.warning("Gemini respondió sin JSON válido, usando fallback local")
            return _fallback_analysis(adivinanza, interpretacion)
        except Exception as e:
            logger.error(f"Error en Gemini API: {e}", exc_info=True)
            return _fallback_analysis(adivinanza, interpretacion)

    # Fallback: usar la tabla Charada local
    return _fallback_analysis(adivinanza, interpretacion)