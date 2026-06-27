import re
import json
import os
from sqlalchemy.orm import Session
from backend.models import Charada


def cargar_charada_json(path: str = "data/charada.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def poblar_charada_db(db: Session, path: str = "data/charada.json"):
    data = cargar_charada_json(path)
    for entry in data:
        existing = db.query(Charada).filter(Charada.numero == entry["numero"]).first()
        if not existing:
            db.add(Charada(**entry))
    db.commit()
    return len(data)


STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "con", "en", "de",
    "del", "y", "que", "es", "por", "para", "se", "su", "al", "lo", "como",
    "mas", "pero", "sus", "le", "ya", "este", "entre", "porque", "donde",
    "cuando", "muy", "sin", "sobre", "todo", "tan", "era", "son", "fue",
    "ser", "han", "hay", "aquel", "esa", "eso", "eso", "mis", "nos", "les",
}


def buscar_en_sueno(db: Session, texto: str) -> list[dict]:
    texto_limpio = re.sub(r"[^\w\sáéíóúñ]", " ", texto.lower())
    palabras = texto_limpio.split()

    all_entries = db.query(Charada).all()

    word_to_entry = {}
    for c in all_entries:
        for word in c.significado.lower().split():
            if word not in STOPWORDS and word not in word_to_entry:
                word_to_entry[word] = c

    resultados = []
    palabras_vistas = set()
    for i, palabra in enumerate(palabras):
        if palabra in word_to_entry and palabra not in palabras_vistas:
            c = word_to_entry[palabra]
            resultados.append({
                "palabra": palabra,
                "numero": c.numero,
                "significado": c.significado,
                "categoria": c.categoria,
                "posicion": i,
            })
            palabras_vistas.add(palabra)

    return resultados


def generar_combinacion_por_orden(resultados: list[dict]) -> str:
    numeros = [str(r["numero"]) for r in resultados]
    if len(numeros) >= 3:
        return "-".join(numeros[:3])
    elif len(numeros) == 2:
        return "-".join(numeros) + "-" + numeros[0]
    elif len(numeros) == 1:
        return numeros[0] + "-" + numeros[0] + "-" + numeros[0]
    return ""
