"""
Vir 1: football-data.co.uk (preko paketa `penaltyblog`)

Prvotno smo CSV-je prenašali neposredno z `requests`, a je bolje uporabiti
`penaltyblog`, ker:
    - vrača že očiščen, standardiziran DataFrame (enotna imena stolpcev)
    - normalizira imena ekip, kar je ključno za združevanje z understat.com
      (glej opombo v scrape.py)
    - je aktivno vzdrževan, torej se prilagaja spremembam na strani namesto
      da se pipeline tiho pokvari

Namestitev: pip install penaltyblog (glej requirements.txt)
Dokumentacija: https://penaltyblog.readthedocs.io/en/latest/scrapers/footballdata.html
"""

from pathlib import Path

import pandas as pd
import penaltyblog as pb

# Mapping iz najinih internih imen lig (configs/config.yaml) v imena,
# ki jih pričakuje penaltyblog.
LEAGUE_TO_PENALTYBLOG = {
    "premier-league": "ENG Premier League",
    "la-liga": "ESP La Liga",
    "serie-a": "ITA Serie A",
    "bundesliga": "DEU Bundesliga 1",
    "ligue-1": "FRA Ligue 1",
}


def _season_strings(start_year: int, end_year: int) -> list[str]:
    """npr. 2015 -> 2023 vrne ['2015-2016', '2016-2017', ..., '2023-2024']."""
    return [f"{y}-{y + 1}" for y in range(start_year, end_year)]


def fetch_league_season(league: str, season: str) -> pd.DataFrame:
    """Prenese eno sezono ene lige. Vrne prazen DataFrame, če sezona ni na voljo."""
    if league not in LEAGUE_TO_PENALTYBLOG:
        raise ValueError(f"Neznana liga '{league}'. Razpoložljive: {list(LEAGUE_TO_PENALTYBLOG)}")

    competition = LEAGUE_TO_PENALTYBLOG[league]
    try:
        scraper = pb.scrapers.FootballData(competition, season)
        df = scraper.get_fixtures().reset_index()
    except Exception as e:
        print(f"  [opozorilo] ni podatkov za {league} sezona {season}: {e}")
        return pd.DataFrame()

    df["league"] = league
    df["source"] = "football-data.co.uk"
    return df


def fetch_league_range(league: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Prenese in združi vse sezone za eno ligo znotraj podanega razpona let."""
    frames = []
    for season in _season_strings(start_year, end_year):
        df = fetch_league_season(league, season)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def save_raw(df: pd.DataFrame, league: str, output_dir: str = "data/raw/football-data") -> Path:
    out_path = Path(output_dir) / f"{league}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    # Primer: prenesi Premier League od sezone 2015/16 do 2023/24
    df = fetch_league_range("premier-league", 2015, 2024)
    if not df.empty:
        path = save_raw(df, "premier-league")
        print(f"Shranjeno: {path} ({len(df)} vrstic)")
