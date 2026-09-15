"""
Vir 3: API-Football (RapidAPI / api-sports.io)

Plačljiv (obstaja brezplačen tier z omejitvijo klicev), a strukturiran API -
uporaben za podatke, ki jih football-data.co.uk in understat NIMATA:
    - lineup-i in poškodbe (pozor: uporabi jih samo, če so bili znani PRED
      tekmo, sicer feature leakage)
    - podrobne statistike tekme (posest, koti, kartoni)
    - dodatne lige/pokali izven top 5 lig

Potreben je API ključ - shrani ga v .env kot API_FOOTBALL_KEY (glej .env.example).
Ta modul je ogrodje - endpoint klici se dopolnijo glede na to, kateri
podatki se izkažejo za potrebne po prvi iteraciji feature engineeringa.
"""

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://v3.football.api-sports.io"


def _headers() -> dict:
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        raise EnvironmentError(
            "API_FOOTBALL_KEY ni nastavljen. Dodaj ga v .env datoteko "
            "(glej .env.example)."
        )
    return {"x-apisports-key": api_key}


def fetch_fixtures(league_id: int, season: int) -> pd.DataFrame:
    """
    Pridobi seznam tekem za ligo (API-Football ima svoje numerične league_id-je,
    npr. 39 = Premier League, 140 = La Liga - preveri v dokumentaciji API-ja).
    """
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": season}

    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("response", [])

    rows = []
    for item in data:
        fixture = item["fixture"]
        teams = item["teams"]
        goals = item["goals"]
        rows.append({
            "fixture_id": fixture["id"],
            "date": fixture["date"],
            "home_team": teams["home"]["name"],
            "away_team": teams["away"]["name"],
            "home_goals": goals["home"],
            "away_goals": goals["away"],
            "status": fixture["status"]["short"],
            "source": "api-football",
        })

    return pd.DataFrame(rows)


def fetch_lineups(fixture_id: int) -> dict:
    """
    Pridobi postave za posamezno tekmo. POZOR: uradne postave se objavijo
    ~60 min pred tekmo - uporabno samo, če to časovno ujemanje upoštevaš
    v feature pipeline-u (sicer feature leakage pri backtestu).
    """
    url = f"{BASE_URL}/fixtures/lineups"
    resp = requests.get(url, headers=_headers(), params={"fixture": fixture_id}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("response", [])


def save_raw(df: pd.DataFrame, name: str, output_dir: str = "data/raw/api-football") -> Path:
    out_path = Path(output_dir) / f"{name}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    # Primer: Premier League (league_id=39), sezona 2023
    df = fetch_fixtures(league_id=39, season=2023)
    if not df.empty:
        path = save_raw(df, "premier-league")
        print(f"Shranjeno: {path} ({len(df)} vrstic)")
