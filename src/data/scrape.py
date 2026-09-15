"""
Orkestrator za scraping - združi vse tri vire podatkov v en pipeline.

Viri:
    1. football-data.co.uk (preko penaltyblog) -> rezultati + bookmakerske kvote (osnova)
    2. understat.com (preko penaltyblog)        -> xG podatki (dodatni feature)
    3. api-football                              -> opcijsko, dodatne statistike/lineup-i

Strategija združevanja:
    - football-data.co.uk je osnova (že ima kvote, ki jih rabimo v koraku 5)
    - understat xG se pripne z LEFT JOIN po [date, team_home, team_away]
    - ker oba vira gresta preko penaltyblog, sta imeni ekip ŽE normalizirani
      (penaltyblog interno poenoti "Man United" -> "Manchester United" ipd.),
      zato src/data/team_mapping.py potrebujeva le kot varovalko za robne
      primere in za morebitno kombiniranje z api-football
    - api-football po potrebi enako, ko/če ga vključimo

Rezultat gre v data/raw/combined/<league>.csv - to je vhod za naslednji
korak (feature engineering), NE za neposredno modeliranje.
"""

from pathlib import Path
import sys

import pandas as pd
import yaml

# Omogoči "from src...." importe tudi če skripto poženeš neposredno
# (npr. z VS Code Run gumbom), ne samo iz korena projekta.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.sources import football_data, understat
from src.data.team_mapping import normalize_columns, find_unmapped_teams


def _load_config(config_path: str = "configs/config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def scrape_league(league: str, start_year: int, end_year: int, include_api_football: bool = False) -> pd.DataFrame:
    """
    Pridobi in združi podatke iz vseh virov za eno ligo.

    Parameters
    ----------
    league : str
        Ime lige (mora obstajati v LEAGUE_TO_PENALTYBLOG v obeh source modulih).
    start_year, end_year : int
        Razpon sezon (začetna leta, npr. 2015, 2024 pokrije sezone 2015/16 .. 2023/24).
    include_api_football : bool
        Če True, poskusi pridobiti tudi API-Football podatke (zahteva API ključ v .env).

    Returns
    -------
    pd.DataFrame
        Združeni surovi podatki, pripravljeni za feature engineering.
    """
    print(f"[1/3] football-data.co.uk: {league} ({start_year}-{end_year})")
    fd_df = football_data.fetch_league_range(league, start_year, end_year)
    if fd_df.empty:
        print(f"  [opozorilo] ni podatkov iz football-data.co.uk za {league}")
        return pd.DataFrame()

    print(f"[2/3] understat.com: {league} ({start_year}-{end_year})")
    us_df = understat.fetch_league_range(league, start_year, end_year)

    if not us_df.empty:
        # penaltyblog normalizira imena ekip na obeh straneh, ampak team_mapping.py
        # uporabiva kot dodatno varovalko (nikoli ne škodi, lahko samo pomaga)
        fd_df = normalize_columns(fd_df, columns=["team_home", "team_away"])
        us_df = normalize_columns(us_df, columns=["team_home", "team_away"])

        # oba vira imata stolpec "date", ampak z različnim dtype-om (eden object/str,
        # drugi datetime64) - pandas merge zato odpove, dokler ju ne poenotiva
        fd_df["date"] = pd.to_datetime(fd_df["date"]).dt.normalize()
        us_df["date"] = pd.to_datetime(us_df["date"]).dt.normalize()

        unmapped = find_unmapped_teams(
            pd.concat([fd_df[["team_home", "team_away"]], us_df[["team_home", "team_away"]]]),
            columns=["team_home", "team_away"],
        )
        if unmapped:
            print(f"  [opozorilo] nenormalizirana imena ekip - preveri team_mapping.py: {unmapped}")

        merged = fd_df.merge(
            us_df[["date", "team_home", "team_away", "xg_home", "xg_away"]],
            on=["date", "team_home", "team_away"],
            how="left",
        )

        missing_xg = merged["xg_home"].isna().sum()
        if missing_xg > 0:
            print(f"  [opozorilo] {missing_xg}/{len(merged)} tekem brez xG (merge ni uspel) - preveri ročno")
    else:
        print("  [opozorilo] ni understat podatkov - nadaljujem brez xG")
        merged = fd_df
        merged["xg_home"] = None
        merged["xg_away"] = None

    if include_api_football:
        print("[3/3] api-football: preskočeno v tej fazi (dodaj po potrebi v naslednji iteraciji)")
    else:
        print("[3/3] api-football: izklopljeno (include_api_football=False)")

    return merged


def save_combined(df: pd.DataFrame, league: str, output_dir: str = "data/raw/combined") -> Path:
    out_path = Path(output_dir) / f"{league}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def run(config_path: str = "configs/config.yaml") -> None:
    """Požene scraping za vse lige, definirane v config.yaml."""
    config = _load_config(config_path)
    leagues = config["leagues"]
    start_year = int(config["data"]["date_range"]["start"][:4])
    end_year = pd.Timestamp.now().year + 1  # do trenutne sezone

    for league in leagues:
        df = scrape_league(league, start_year, end_year)
        if not df.empty:
            path = save_combined(df, league)
            print(f"  -> shranjeno: {path} ({len(df)} vrstic)\n")
        else:
            print(f"  -> preskočeno (ni podatkov): {league}\n")


if __name__ == "__main__":
    run()
