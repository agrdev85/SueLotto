import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-2.0-flash"


def consultar(prompt: str, model: str = None) -> str:
    key = GEMINI_API_KEY
    if not key:
        return ""

    model_name = model or DEFAULT_MODEL
    try:
        from google import genai as genai_client
        client = genai_client.Client(api_key=key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return ""


def consultar_json(prompt: str, model: str = None) -> dict:
    text = consultar(prompt, model)
    if not text:
        return {}
    try:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


def build_prediction_prompt(
    juego: str,
    historicos: list[dict],
    frecuencias: list[dict],
    atrasados: list[dict],
) -> str:
    historicos_str = "\n".join(
        f"  {h['fecha']}: {h['n1']}-{h['n2']}-{h['n3']}" + (f"-{h['n4']}" if h.get('n4') is not None else "")
        for h in historicos[-60:]
    )

    frecuencias_str = "\n".join(
        f"  #{f['numero']}: {f['frecuencia']} veces"
        for f in frecuencias[:15]
    )

    atrasados_str = "\n".join(
        f"  #{a['numero']}: {a['dias_sin_salir']} días sin salir"
        for a in atrasados[:15]
    )

    return f"""Eres un analista experto en la lotería {juego} de la Florida Lottery.

Basándote en los siguientes datos históricos, frecuencias y atrasos,
predice los 10 números más probables para el próximo sorteo.
Los números van del 0 al 9 (dígitos individuales).

Últimos {min(len(historicos), 60)} resultados:
{historicos_str}

Frecuencias (últimos 30 días):
{frecuencias_str}

Atrasos (días desde última aparición):
{atrasados_str}

Analiza los patrones: números calientes (alta frecuencia), números fríos (atrasados),
secuencias repetidas, dígitos que tienden a salir juntos.

Responde en formato JSON:
{{
  "predicciones": [
    {{"numero": 4, "probabilidad": 0.15, "razon": "Alta frecuencia y patrón de repetición"}},
    ...
  ],
  "analisis": "Texto con el análisis completo del patrón"
}}
Asegúrate de incluir exactamente 10 predicciones ordenadas por probabilidad descendente.
"""


def parse_predicciones_llm(response: dict) -> list[dict]:
    if not response:
        return []
    predicciones = response.get("predicciones", [])
    if not predicciones or not isinstance(predicciones, list):
        return []
    for p in predicciones:
        p["probabilidad"] = float(p.get("probabilidad", 0))
    return sorted(predicciones, key=lambda x: x["probabilidad"], reverse=True)[:10]
