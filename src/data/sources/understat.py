"""
Vir 2: understat.com (preko paketa `penaltyblog`)

POMEMBNA OPOMBA (dopolnjeno po tvojem testu):
Prvotna implementacija je surovo parsala vgrajen JSON iz <script> tagov na
understat strani (regex na `var datesData = JSON.parse('...')`). To je
prenehalo delovati - najverjetneje se je spremenila struktura strani ali
zaščita pred boti. Namesto da vzdržujeva krhek regex, uporabljava
`penaltyblog`, ki isto stran scrapa robustneje in jo aktivno vzdržuje ekipa,
ki spremlja spremembe na understat.com.

Bonus: penaltyblog že normalizira imena ekip (isti standard kot pri
football-data.co.uk scraperju), kar bistveno poenostavi merge v scrape.py.

Namestitev: pip install penaltyblog (glej requirements.txt)
Dokumentacija: https://penaltyblog.readthedocs.io/en/latest/scrapers/understat.html
"""

from pathlib import Path

import pandas as pd
import penaltyblog as pb

# understat pokriva samo 5 od "top" lig (brez RUS Premier League, ki nas ne zanima)
LEAGUE_TO_PENALTYBLOG = {
    "premier-league": "ENG Premier League",
    "la-liga": "ESP La Liga",
    "serie-a": "ITA Serie A",
    "bundesliga": "DEU Bundesliga 1",
    "ligue-1": "FRA Ligue 1",
}


def _season_strings(start_year: int, end_year: int) -> list[str]:
    return [f"{y}-{y + 1}" for y in range(start_year, end_year)]


def fetch_season_matches(league: str, season: str) -> pd.DataFrame:
    """Prenese vse tekme (z xG) za eno ligo in eno sezono."""
    if league not in LEAGUE_TO_PENALTYBLOG:
        raise ValueError(f"Neznana liga '{league}'. Razpoložljive: {list(LEAGUE_TO_PENALTYBLOG)}")

    competition = LEAGUE_TO_PENALTYBLOG[league]
    try:
        scraper = pb.scrapers.Understat(competition, season)
        df = scraper.get_fixtures().reset_index()
    except Exception as e:
        print(f"  [opozorilo] {league} {season}: {e}")
        return pd.DataFrame()

    df["league"] = league
    df["source"] = "understat.com"
    return df


def fetch_league_range(league: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Prenese in združi več zaporednih sezon."""
    frames = []
    for season in _season_strings(start_year, end_year):
        df = fetch_season_matches(league, season)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def save_raw(df: pd.DataFrame, league: str, output_dir: str = "data/raw/understat") -> Path:
    out_path = Path(output_dir) / f"{league}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    df = fetch_league_range("premier-league", 2015, 2024)
    if not df.empty:
        path = save_raw(df, "premier-league")
        print(f"Shranjeno: {path} ({len(df)} vrstic)")
