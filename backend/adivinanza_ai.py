import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PROMPT_TEMPLATE = """Eres un experto en la Charada Cubana y la interpretación de adivinanzas para la lotería.

Tu tarea es analizar la siguiente adivinanza y la interpretación que el usuario ha dado,
y sugerir números de lotería (0-9) que podrían estar relacionados.

Contexto cultural cubano:
- "agua" → 7
- "fuego" → 3
- "gallo" → 9
- "muerto" → 4
- "dinero" → 5
- "amor" → 1
- "viaje" → 8
- "casa" → 2
- "tristeza" → 6
- "suerte" → 0

ADIVINANZA: {adivinanza}

INTERPRETACIÓN DEL USUARIO: {interpretacion}

Por favor, proporciona:
1. Una lista de 3-5 números sugeridos (0-9) ordenados por relevancia
2. Una breve explicación de por qué cada número es relevante

Responde en formato JSON:
{{
  "sugerencias": [
    {{"numero": 7, "razon": "El agua en la adivinanza sugiere el número 7"}},
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
        return _fallback_analysis(adivinanza, interpretacion)
    except Exception:
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
        "suerte": 0, "ganar": 0, "loteria": 0, "premio": 0,
    }

    sugerencias = []
    for palabra, numero in keywords.items():
        if palabra in texto_combinado:
            sugerencias.append({
                "numero": numero,
                "razon": f"La palabra '{palabra}' aparece en el texto y está asociada al número {numero} en la Charada Cubana.",
            })

    sugerencias = sugerencias[:5]
    if not sugerencias:
        sugerencias = [
            {"numero": 7, "razon": "Número de la suerte por defecto."},
            {"numero": 3, "razon": "Número de la suerte por defecto."},
        ]

    return {
        "sugerencias": sugerencias,
        "razonamiento": "Análisis local basado en palabras clave de la Charada Cubana. Conecta con Gemini API para un análisis más profundo.",
    }
