import os
import sys
import logging
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


def gemini_activo() -> bool:
    return _gemini_disponible


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


def analizar_adivinanza(adivinanza: str, interpretacion: str, api_key: str = None) -> dict:
    key = api_key or GEMINI_API_KEY

    if not key:
        return _fallback_analysis(adivinanza, interpretacion)

    try:
        from google import genai as genai_client

        client = genai_client.Client(api_key=key)

        prompt = PROMPT_TEMPLATE.format(
            adivinanza=adivinanza,
            interpretacion=interpretacion,
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        import json
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


def _fallback_analysis(adivinanza: str, interpretacion: str) -> dict:
    texto_combinado = (adivinanza + " " + interpretacion).lower()

    keywords = {
        "agua": 7, "mar": 7, "lluvia": 7, "rio": 7,
        "fuego": 3, "sol": 3, "calor": 3, "lumbre": 3,
        "gallo": 9, "pollo": 9, "ave": 9, "pajaro": 9,
        "muerto": 4, "muerte": 4, "sepulcro": 4, "fantasma": 4,
        "dinero": 5, "plata": 5, "oro": 5, "rico": 5,
        "amor": 1, "corazon": 1, "beso": 1, "pareja": 1,
        "viaje": 8, "camino": 8, "vuelo": 8, "carro": 8,
        "casa": 2, "hogar": 2, "familia": 2, "madre": 2,
        "tristeza": 6, "llanto": 6, "lagrima": 6, "dolor": 6,
        "caballo": 1, "jinete": 1, "montar": 1,
        "mariposa": 2, "oruga": 2,
        "caracol": 7, "concha": 7,
    }

    sugerencias = []
    for palabra, numero in keywords.items():
        if palabra in texto_combinado:
            sugerencias.append({
                "numero": numero,
                "razon": f"La palabra '{palabra}' aparece en el texto y está asociada al número {numero} en la tabla.",
            })

    sugerencias = sugerencias[:5]
    if not sugerencias:
        sugerencias = [
            {"numero": 1, "razon": "Número de la suerte por defecto (Caballo)."},
            {"numero": 7, "razon": "Número de la suerte por defecto (Agua/Caracol)."},
        ]

    return {
        "sugerencias": sugerencias,
        "razonamiento": "Análisis local basado en palabras clave. Conecta con Gemini API para un análisis más profundo.",
    }
