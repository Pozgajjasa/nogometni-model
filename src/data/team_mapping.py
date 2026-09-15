"""
Normalizacija imen ekip med viri.

Vsak vir poimenuje ekipe drugače, npr. za isti klub:
    football-data.co.uk : "Man United"
    understat.com        : "Manchester United"
    api-football          : "Manchester United"

Brez normalizacije se tekme med viri ne bodo pravilno združile (join po
[date, home_team, away_team] bo spodletel na desetinah primerov).

Pristop: preslikamo VSE variante na en kanoničen naziv (canonical_name).
Slovar je treba dopolnjevati sproti, ko naletiš na neujemanja pri merge-u
(glej find_unmapped_teams spodaj - uporabi jo po vsakem novem scrapingu).
"""

import pandas as pd

# Kanoničen naziv -> seznam znanih variant iz različnih virov
# (football-data.co.uk in understat.com imata dosledno različna imena za
# precej klubov - spodaj so variante, kot se dejansko pojavljajo v obeh
# virih, za vseh pet lig, ki jih ima projekt v configs/config.yaml).
#
# Pokriti so klubi, ki so bili v top ligi kadarkoli od sezone 2015/16 naprej
# (vključno s tistimi, ki so bili le kratek čas noter - promocije/izpadi).
# Ob morebitnih novih promocijah v prihodnjih sezonah uporabi
# find_unmapped_teams() po scrapingu in dopolni spodnji slovar.
TEAM_ALIASES: dict[str, list[str]] = {
    # ---------------- Premier League ----------------
    "Manchester United": ["Man United", "Man Utd", "Manchester Utd"],
    "Manchester City": ["Man City"],
    "Tottenham Hotspur": ["Tottenham", "Spurs"],
    "Wolverhampton Wanderers": ["Wolves", "Wolverhampton"],
    "Newcastle United": ["Newcastle"],
    "Brighton & Hove Albion": ["Brighton"],
    "West Ham United": ["West Ham"],
    "Leicester City": ["Leicester"],
    "Coventry City": ["Coventry"],
    "Nottingham Forest": ["Nott'm Forest", "Forest"],
    "Sheffield United": ["Sheffield Utd"],
    "Sheffield Wednesday": ["Sheffield Weds"],
    "West Bromwich Albion": ["West Brom"],
    "Queens Park Rangers": ["QPR"],
    "Brentford": [],
    "Bournemouth": ["AFC Bournemouth"],
    "Huddersfield Town": ["Huddersfield"],
    "Cardiff City": ["Cardiff"],
    "Swansea City": ["Swansea"],
    "Stoke City": ["Stoke"],
    "Hull City": ["Hull"],
    "Norwich City": ["Norwich"],
    "Watford": [],
    "Fulham": [],
    "Crystal Palace": [],
    "Everton": [],
    "Burnley": [],
    "Aston Villa": [],
    "Southampton": [],
    "Leeds United": ["Leeds"],
    "Luton Town": ["Luton"],
    "Ipswich Town": ["Ipswich"],
    "Arsenal": [],
    "Chelsea": [],
    "Liverpool": [],
    "Middlesbrough": [],
    "Sunderland": [],

    # ---------------- La Liga ----------------
    "Athletic Club": ["Ath Bilbao", "Athletic Bilbao"],
    "Atletico Madrid": ["Ath Madrid", "Atletico"],
    "Barcelona": [],
    "Real Betis": ["Betis"],
    "Cadiz": [],
    "Celta Vigo": ["Celta"],
    "Deportivo Alaves": ["Alaves"],
    "Almeria": [],
    "Cordoba": [],
    "Elche": [],
    "Espanyol": ["Espanol"],
    "Getafe": [],
    "Girona": [],
    "Granada": [],
    "SD Huesca": ["Huesca"],
    "Las Palmas": [],
    "Leganes": [],
    "Levante": [],
    "Malaga": [],
    "Mallorca": [],
    "Osasuna": [],
    "Real Madrid": [],
    "Sevilla": [],
    "Real Sociedad": ["Sociedad"],
    "Sporting Gijon": ["Sp Gijon"],
    "Valencia": [],
    "Real Valladolid": ["Valladolid"],
    "Rayo Vallecano": ["Vallecano"],
    "Villarreal": [],
    "Eibar": [],
    "Deportivo La Coruna": ["La Coruna", "Deportivo"],
    "Real Zaragoza": ["Zaragoza"],
    "Racing Santander": ["Santander"],
    "Real Oviedo": ["Oviedo"],

    # ---------------- Serie A ----------------
    "Atalanta": [],
    "Bologna": [],
    "Cagliari": [],
    "Chievo": ["Chievo Verona"],
    "Empoli": [],
    "Fiorentina": [],
    "Frosinone": [],
    "Genoa": [],
    "Inter": ["Inter Milan", "Internazionale"],
    "Juventus": [],
    "Lazio": [],
    "Lecce": [],
    "AC Milan": ["Milan"],
    "Napoli": [],
    "Parma Calcio 1913": ["Parma"],
    "Roma": ["AS Roma"],
    "Sampdoria": [],
    "Sassuolo": [],
    "SPAL 2013": ["Spal"],
    "Torino": [],
    "Udinese": [],
    "Hellas Verona": ["Verona"],
    "Crotone": [],
    "Benevento": [],
    "Brescia": [],
    "Cremonese": [],
    "Salernitana": [],
    "Monza": [],
    "Como": [],
    "Venezia": [],
    "Pisa": [],
    "Pescara": [],
    "Palermo": [],
    "Spezia": [],
    "Carpi": [],

    # ---------------- Bundesliga ----------------
    "Bayern Munich": ["FC Bayern Munich"],
    "Borussia Dortmund": ["Dortmund"],
    "Bayer Leverkusen": ["Leverkusen"],
    "RasenBallsport Leipzig": ["RB Leipzig"],
    "Wolfsburg": ["VfL Wolfsburg"],
    "Borussia M.Gladbach": ["M'gladbach", "Monchengladbach", "Borussia Monchengladbach"],
    "Eintracht Frankfurt": ["Ein Frankfurt"],
    "TSG Hoffenheim": ["Hoffenheim"],
    "Schalke 04": ["Schalke"],
    "FC Koln": ["FC Cologne", "1. FC Koln"],
    "Hertha Berlin": ["Hertha"],
    "Mainz 05": ["Mainz"],
    "SC Freiburg": ["Freiburg"],
    "Augsburg": ["FC Augsburg"],
    "VfB Stuttgart": ["Stuttgart"],
    "Hannover 96": ["Hannover"],
    "Werder Bremen": [],
    "Hamburger SV": ["Hamburg"],
    "1. FC Nurnberg": ["Nurnberg", "Nuernberg"],
    "Fortuna Dusseldorf": ["Dusseldorf", "Fortuna Duesseldorf"],
    "SC Paderborn": ["Paderborn"],
    "Union Berlin": [],
    "Arminia Bielefeld": ["Bielefeld"],
    "Greuther Furth": ["Greuther Fuerth"],
    "VfL Bochum": ["Bochum"],
    "Darmstadt": ["SV Darmstadt 98"],
    "1. FC Heidenheim": ["Heidenheim", "FC Heidenheim", "1.FC Heidenheim"],
    "FC St. Pauli": ["St Pauli", "St. Pauli"],
    "Holstein Kiel": [],
    "Ingolstadt": ["FC Ingolstadt 04"],
    "SV Elversberg": ["Elversberg"],

    # ---------------- Ligue 1 ----------------
    "Paris Saint Germain": ["Paris SG", "PSG"],
    "Marseille": ["Olympique Marseille"],
    "Lyon": ["Olympique Lyonnais"],
    "Monaco": ["AS Monaco"],
    "Lille": [],
    "Rennes": [],
    "Nice": [],
    "Nantes": [],
    "Bordeaux": [],
    "Saint-Etienne": ["St Etienne"],
    "Montpellier": [],
    "Toulouse": [],
    "Strasbourg": [],
    "Reims": [],
    "Angers": [],
    "Brest": [],
    "Metz": [],
    "Lorient": [],
    "Troyes": [],
    "Clermont Foot": ["Clermont"],
    "Lens": [],
    "Auxerre": [],
    "Le Havre": [],
    "Amiens": [],
    "Caen": [],
    "Dijon": [],
    "Nimes": [],
    "Guingamp": [],
    "GFC Ajaccio": ["Ajaccio GFCO", "Ajaccio", "GFCO Ajaccio"],
    "Bastia": ["SC Bastia"],
    "Paris FC": [],
    "Nancy": ["AS Nancy Lorraine"],
    "Le Mans": ["Le Mans FC"],
}


def _build_lookup() -> dict[str, str]:
    """Zgradi obratni slovar: vsaka varianta (in kanonično ime samo) -> kanonično ime."""
    lookup = {}
    for canonical, aliases in TEAM_ALIASES.items():
        lookup[canonical.lower()] = canonical
        for alias in aliases:
            lookup[alias.lower()] = canonical
    return lookup


_LOOKUP = _build_lookup()


def normalize_team(name: str) -> str:
    """Vrne kanonično ime ekipe. Če ni najdeno v slovarju, vrne originalno ime nespremenjeno."""
    if not isinstance(name, str):
        return name
    return _LOOKUP.get(name.strip().lower(), name.strip())


def normalize_columns(df: pd.DataFrame, columns: list[str] = None) -> pd.DataFrame:
    """Normalizira imena ekip v podanih stolpcih (privzeto: team_home, team_away)."""
    columns = columns or ["team_home", "team_away"]
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_team)
    return df


def find_unmapped_teams(df: pd.DataFrame, columns: list[str] = None) -> set[str]:
    """
    Vrne ekipe, ki NISO v TEAM_ALIASES (torej se bodo prenesle nespremenjene).
    Uporabi po vsakem scrapingu novega vira/lige, da odkriješ manjkajoče aliase.
    """
    columns = columns or ["team_home", "team_away"]
    known = set(_LOOKUP.values()) | set(_LOOKUP.keys())
    found_unmapped = set()
    for col in columns:
        if col in df.columns:
            for name in df[col].dropna().unique():
                if name.lower() not in known:
                    found_unmapped.add(name)
    return found_unmapped
