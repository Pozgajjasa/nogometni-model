# Nogometni napovedovalni model

ML sistem za napovedovanje izidov nogometnih tekem (XGBoost + Elo + Poisson) in iskanje
pozitivnega EV proti bookmakerskim kvotam, z Kelly staking strategijo.

## Pipeline (koraki projekta)

1. **Scraping / pridobivanje podatkov** → `src/data/`
2. **Feature engineering** → `src/features/`
3. **Elo rating model** → `src/elo/`
4. **Poisson model** → `src/poisson/`
5. **XGBoost model (glavni model)** → `src/models/`
6. **Primerjava z bookmakerskimi kvotami, EV, Kelly** → `src/betting/`
7. **Backtest in Monte Carlo simulacija** → `src/backtest/`

## Struktura direktorijev

```
nogometni-model/
├── data/
│   ├── raw/          # surovi podatki, kot pridobljeni s scrapingom (nikoli ročno urejati)
│   ├── interim/       # delno očiščeni/preoblikovani podatki
│   ├── processed/     # končni feature setti, pripravljeni za modeliranje
│   └── external/      # zunanji podatki (npr. bookmakerske kvote, referenčne tabele)
├── notebooks/          # eksploracija, prototipiranje (Jupyter)
├── src/
│   ├── data/           # scraping in nalaganje podatkov
│   ├── features/       # feature engineering
│   ├── elo/             # Elo rating implementacija
│   ├── poisson/         # Poisson model (samostojni benchmark + featurji)
│   ├── models/           # XGBoost trening, kalibracija, evalvacija
│   ├── betting/           # odstranjevanje vig-a, EV izračun, Kelly staking
│   ├── backtest/           # walk-forward backtest, Monte Carlo simulacija
│   └── utils/               # pomožne funkcije (logging, IO, config loader)
├── configs/                  # YAML/JSON konfiguracije (ligue, parametri, poti)
├── tests/                     # unit testi
├── reports/
│   └── figures/                # grafi, calibration curves, backtest rezultati
└── scripts/                     # izvršljive skripte (npr. run_scraping.py, run_backtest.py)
```

## Scraping - viri podatkov

Projekt kombinira tri vire (glej `src/data/`):

| Vir | Kaj daje | Modul |
|---|---|---|
| football-data.co.uk | rezultati + bookmakerske kvote (osnova) | `src/data/sources/football_data.py` |
| understat.com | xG (expected goals) | `src/data/sources/understat.py` |
| API-Football | lineup-i, podrobne statistike (opcijsko, potreben ključ) | `src/data/sources/api_football.py` |

Prva dva vira gresta preko paketa [`penaltyblog`](https://penaltyblog.readthedocs.io/) namesto
ročnega scrapinga - understat.com občasno spreminja HTML strukturo/zaščito pred boti, zato se
raje zanašamo na aktivno vzdrževano knjižnico kot na krhek regex. `penaltyblog` že normalizira
imena ekip med viri (npr. "Man United" -> "Manchester United"), kar bistveno olajša merge.

`src/data/scrape.py` je orkestrator, ki podatke iz vseh virov pridobi in združi po
`[date, team_home, team_away]`. `src/data/team_mapping.py` (157 klubov iz vseh petih lig)
služi kot dodatna varovalka za robne primere in za morebitno kombiniranje z API-Football -
po vsakem scrapingu preveri opozorila iz `find_unmapped_teams()`.

Zagon:
```bash
cp .env.example .env          # vnesi API_FOOTBALL_KEY, če uporabljaš API-Football
python scripts/run_scraping.py
```

Rezultat: `data/raw/combined/<league>.csv` - to je vhod za feature engineering (korak 2).

## Namestitev

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Konvencije

- **Nobenega ročnega urejanja v `data/raw/`** — surovi podatki so "source of truth".
- Vsak modul v `src/` naj bo neodvisen in testabilen (glej `tests/`).
- Konfiguracije (poti, parametri, seznami lig) gredo v `configs/`, ne hardcodane v kodo.
- Naključna semena (`random_state`) so fiksirana povsod, kjer je mogoče, za ponovljivost.
