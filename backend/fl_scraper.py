"""
Obtención de resultados de la Florida Lottery desde la API oficial
del sitio floridalottery.com (APIM: /drawgamesapp/getLatestDrawGames).

Reemplaza el scraping HTML antiguo (selectores obsoletos de flalottery.com)
por la misma fuente JSON que usa la web oficial.
"""

from datetime import date
from typing import Optional

from backend.fl_api import (
    get_latest_by_game,
    GAME_ORDER,
)

# Juegos que se muestran en la sección "Otros Juegos" de la app.
# Pick 3 / Pick 4 se muestran en su propia sección principal y eZMatch
# no tiene números ganadores, así que se omiten aquí.
OTHER_GAMES = [
    name for name in GAME_ORDER
    if name not in {"Pick 3", "Pick 4", "eZMatch Lotto", "eZMatch Fantasy 5"}
]


def scrape_other_games():
    """Resultados más recientes por juego desde la API oficial.

    Devuelve una lista de dicts con la forma histórica:
        {"name", "date", "numbers", "extra"}
    """
    results = []
    latest = get_latest_by_game()
    for name in OTHER_GAMES:
        d = latest.get(name)
        if not d:
            continue
        results.append({
            "name": name,
            "date": d["date"].strftime("%m/%d/%Y") if d["date"] else "",
            "numbers": d["numbers"],
            "extra": d["bonus"],
        })
    return results


def scrape_and_store_other_games(db, batch_date: Optional[date] = None):
    """Guarda en other_games los resultados más recientes por juego.

    `fecha` guarda la fecha real del sorteo. Para juegos con varios
    sorteos al día (Pick 2/3/4/5, Cash Pop) se conserva el último sorteo
    de cada fecha (la API los devuelve todos).
    """
    from backend.crud import bulk_insert_other_games

    if batch_date is None:
        batch_date = date.today()

    latest = get_latest_by_game()
    games_to_store = []
    for name in OTHER_GAMES:
        d = latest.get(name)
        if not d or d["date"] is None:
            continue
        games_to_store.append({
            "game_name": name,
            "fecha": d["date"],
            "numbers": ",".join(d["numbers"]),
            "extra": ",".join(d["bonus"]),
            "drawing_date": d["date"].strftime("%m/%d/%Y"),
        })

    # Refresco total: la tabla solo alimenta la sección "últimos resultados
    # por juego", así que se reemplaza con los datos oficiales actuales
    # (descarta la basura que dejaba el scraper HTML antiguo).
    from backend.models import OtherGameResult
    try:
        db.query(OtherGameResult).delete()
        db.commit()
    except Exception:
        db.rollback()

    if not games_to_store:
        return 0

    bulk_insert_other_games(db, games_to_store)
    return len(games_to_store)
