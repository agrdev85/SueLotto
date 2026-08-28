"""
Cliente de la API oficial de la Florida Lottery.

El sitio floridalottery.com (y su versión en español) carga sus resultados
desde una API pública de Azure API Management:

    GET https://apim-website-prod-eastus.azure-api.net/drawgamesapp/getLatestDrawGames
    Header: x-partner: web

Devuelve los resultados más recientes de TODOS los juegos de sorteo
(Pick 2/3/4/5, Fantasy 5, Lotto, Cash4Life, Powerball, Mega Millions,
Cash Pop, Jackpot Triple Play, Double Plays, etc.) en una sola llamada,
con números, bola extra (Fireball/Powerball/Mega Ball/Cash Ball), fecha
de sorteo y tipo de sorteo (MIDDAY/EVENING, etc.).
"""

import httpx
from datetime import datetime, date
from typing import Optional

APIM_URL = "https://apim-website-prod-eastus.azure-api.net"
LATEST_ENDPOINT = f"{APIM_URL}/drawgamesapp/getLatestDrawGames"
HEADERS = {
    "x-partner": "web",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
TIMEOUT = 20

# Nombres legibles de los juegos que muestra la app.
GAME_NAMES = {
    "PICK 2": "Pick 2",
    "PICK 3": "Pick 3",
    "PICK 4": "Pick 4",
    "PICK 5": "Pick 5",
    "FANTASY 5": "Fantasy 5",
    "LOTTO": "Lotto",
    "JACKPOT TRIPLE PLAY": "Jackpot Triple Play",
    "CASH4LIFE": "Cash4Life",
    "MEGA MILLIONS": "Mega Millions",
    "POWER BALL": "Powerball",
    "POWER BALL DP": "Powerball Double Play",
    "LOTTO DP": "Lotto Double Play",
    "CASH POP": "Cash Pop",
    "EZMATCH LOTTO": "eZMatch Lotto",
    "EZMATCH FANTASY 5": "eZMatch Fantasy 5",
}

# Orden canónico de visualización (mismo espíritu que la página draw-games).
GAME_ORDER = [
    "Pick 2",
    "Pick 3",
    "Pick 4",
    "Pick 5",
    "Cash4Life",
    "Fantasy 5",
    "Jackpot Triple Play",
    "Lotto",
    "Cash Pop",
    "Mega Millions",
    "Powerball",
    "Powerball Double Play",
    "Lotto Double Play",
    "eZMatch Lotto",
    "eZMatch Fantasy 5",
]

# Juegos sin bola extra propia.
SIMPLE_GAMES = {"Pick 2", "Pick 3", "Pick 4", "Pick 5", "Cash Pop"}

# Etiqueta legible para cada bola extra.
BONUS_LABELS = {
    "fb": "Fireball",
    "pb": "Powerball",
    "mb": "Mega Ball",
    "cb": "Cash Ball",
}

# Etiqueta legible por tipo de sorteo.
TURNO_LABELS = {
    "MIDDAY": "Mediodía",
    "EVENING": "Noche",
    "MOR": "Mañana",
    "MAT": "Mediodía",
    "AFT": "Tarde",
    "EVE": "Noche",
    "LAT": "Noche",
}


def _parse_draw_date(raw: str) -> Optional[date]:
    """Convierte '08/05/2026 12:00:00 AM' a date."""
    if not raw:
        return None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def fetch_latest_draws() -> list[dict]:
    """Devuelve la lista cruda de sorteos más recientes de todos los juegos."""
    resp = httpx.get(LATEST_ENDPOINT, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"Respuesta inesperada de la API oficial: {type(data)}")
    return data


def normalize_draws(raw: list[dict]) -> list[dict]:
    """Convierte la respuesta cruda en registros normalizados:

    {
        "game_id": int,
        "name": "Powerball",
        "raw_name": "POWER BALL",
        "date": date,
        "draw_type": "MIDDAY" | "EVENING" | "" | ...,
        "turno": "Mediodía" | "Noche" | "",
        "numbers": ["14", "20", ...],   # números principales
        "bonus": ["25"],                 # bola extra (puede estar vacía)
        "bonus_label": "Powerball",
        "jackpot": "$325 Million" | "",
    }
    """
    out = []
    for item in raw:
        raw_name = (item.get("GameName") or "").strip()
        name = GAME_NAMES.get(raw_name, raw_name.title())
        ddate = _parse_draw_date(item.get("DrawDate") or "")
        draw_type = (item.get("DrawType") or "").strip()
        numbers, bonus = [], []
        for dn in item.get("DrawNumbers") or []:
            ntype = (dn.get("NumberType") or "").strip().lower()
            val = str(dn.get("NumberPick", "")).strip()
            if not val or not val.isdigit():
                continue
            if ntype in BONUS_LABELS:
                bonus.append(val)
            else:
                numbers.append(val)
        if not numbers and not bonus:
            continue
        bonus_label = ""
        if bonus:
            if draw_type and name in SIMPLE_GAMES:
                bonus_label = "Fireball"
            else:
                for nt in item.get("DrawNumbers") or []:
                    k = (nt.get("NumberType") or "").strip().lower()
                    if k in BONUS_LABELS and k != "fb":
                        bonus_label = BONUS_LABELS[k]
                        break
                if not bonus_label:
                    bonus_label = "Fireball"
        out.append({
            "game_id": item.get("Id"),
            "name": name,
            "raw_name": raw_name,
            "date": ddate,
            "draw_type": draw_type,
            "turno": TURNO_LABELS.get(draw_type, ""),
            "numbers": numbers,
            "bonus": bonus,
            "bonus_label": bonus_label,
            "jackpot": (item.get("NextJackpotAmount") or "").strip(),
        })
    return out


def get_latest_draws() -> list[dict]:
    """Resultados normalizados de todos los juegos (una llamada a la API oficial)."""
    return normalize_draws(fetch_latest_draws())


def get_latest_by_game() -> dict:
    """Resultado más reciente por juego (dict name -> draw)."""
    by_game = {}
    for d in get_latest_draws():
        if d["date"] is None:
            continue
        cur = by_game.get(d["name"])
        if cur is None or d["date"] > cur["date"]:
            by_game[d["name"]] = d
    return by_game
