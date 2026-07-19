import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import re
from typing import Optional
from sqlalchemy.orm import Session

FL_LOTTERY_URL = "https://www.flalottery.com"


def scrape_other_games():
    results = []
    games = [
        ("Pick 3", f"{FL_LOTTERY_URL}/pick3"),
        ("Pick 4", f"{FL_LOTTERY_URL}/pick4"),
        ("Cash4Life", f"{FL_LOTTERY_URL}/cash4life"),
        ("Lotto", f"{FL_LOTTERY_URL}/lotto"),
        ("Fantasy 5", f"{FL_LOTTERY_URL}/fantasy5"),
        ("Mega Millions", f"{FL_LOTTERY_URL}/megamillions"),
        ("Powerball", f"{FL_LOTTERY_URL}/powerball"),
    ]

    for name, url in games:
        try:
            game_data = _scrape_game(name, url)
            if game_data:
                results.append(game_data)
        except Exception as e:
            print(f"[WARN] Failed to scrape {name}: {e}")

    return results


def _scrape_game(name: str, url: str) -> Optional[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    numbers = []
    extra = []
    game_date = date.today().strftime("%m/%d/%Y")

    date_tag = soup.find(class_=re.compile(r"date|drawDate|gameDate|Date", re.I))
    if date_tag:
        txt = date_tag.get_text(strip=True)
        if txt:
            game_date = txt

    if name == "Pick 3":
        balls = soup.select(".pick3-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                if "fireball" in " ".join(b.get("class", [])).lower():
                    extra.append(txt)
                else:
                    numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 3:
                numbers = nums[:3]
                if len(nums) > 3:
                    extra = [nums[3]]

    elif name == "Pick 4":
        balls = soup.select(".pick4-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                if "fireball" in " ".join(b.get("class", [])).lower():
                    extra.append(txt)
                else:
                    numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 4:
                numbers = nums[:4]
                if len(nums) > 4:
                    extra = [nums[4]]

    elif name == "Cash4Life":
        balls = soup.select(".balls-ball, .cash4life-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                if "cash-ball" in b.get("class", []) or "cash" in b.get("class", []):
                    extra.append(txt)
                else:
                    numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 5:
                numbers = nums[:5]
                if len(nums) > 5:
                    extra = [nums[5]]

    elif name == "Lotto":
        balls = soup.select(".lotto-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 6:
                numbers = nums[:6]

    elif name == "Fantasy 5":
        balls = soup.select(".fantasy-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 5:
                numbers = nums[:5]

    elif name == "Mega Millions":
        balls = soup.select(".megamillions-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                if "megaball" in " ".join(b.get("class", [])) or "mega" in " ".join(b.get("class", [])):
                    extra.append(txt)
                else:
                    numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 5:
                numbers = nums[:5]
                if len(nums) > 5:
                    extra = [nums[5]]

    elif name == "Powerball":
        balls = soup.select(".powerball-ball, [class*=ball]")
        for b in balls:
            txt = b.get_text(strip=True)
            if txt and txt.isdigit():
                if "powerball" in " ".join(b.get("class", [])):
                    extra.append(txt)
                else:
                    numbers.append(txt)
        if not numbers:
            text = soup.get_text()
            nums = re.findall(r"\b(\d{1,2})\b", text)
            if len(nums) >= 5:
                numbers = nums[:5]
                if len(nums) > 5:
                    extra = [nums[5]]

    if not numbers:
        return None

    return {
        "name": name,
        "date": game_date,
        "numbers": numbers,
        "extra": extra,
    }


def scrape_and_store_other_games(db: Session, batch_date: Optional[date] = None):
    from backend.crud import bulk_insert_other_games

    if batch_date is None:
        batch_date = date.today()

    results = scrape_other_games()
    if not results:
        return 0

    games_to_store = []
    for g in results:
        games_to_store.append({
            "game_name": g["name"],
            "fecha": batch_date,
            "numbers": ",".join(g.get("numbers", [])),
            "extra": ",".join(g.get("extra", [])),
            "drawing_date": g.get("date", ""),
        })

    bulk_insert_other_games(db, games_to_store)
    return len(games_to_store)
