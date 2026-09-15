from pathlib import Path
import pandas as pd

# Pot do mape z združenimi CSV datotekami
DATA_DIR = Path("data/raw/combined")


def inspect_dataset(file_path: Path) -> None:
    """Naredi kratek pregled posamezne CSV datoteke z ligami."""
    print("=" * 70)
    print(f" LIGA: {file_path.stem.upper()}")
    print("=" * 70)

    df = pd.read_csv(file_path, low_memory=False)

    # 1. Osnovne dimenzije in časovni razpon
    print(f"Vseh tekem (vrstic): {len(df)}")
    print(f"Število stolpcev:     {len(df.columns)}")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        print(
            f"Obdobje tekem:       {df['date'].min().strftime('%Y-%m-%d')} do {df['date'].max().strftime('%Y-%m-%d')}"
        )

    if "season" in df.columns:
        seasons = sorted(df["season"].dropna().unique())
        print(f"Zajete sezone ({len(seasons)}):  {', '.join(map(str, seasons))}")

    print("-" * 70)

    # 2. Preverjanje manjkajočih vrednosti po ključnih skupinah
    print("MANJKAJOČE VREDNOSTI PO KLJUČNIH STOLPCI:]")

    # Osnovni podatki tekme
    core_cols = [
        "date",
        "home_team",
        "away_team",
        "goals_home",
        "goals_away",
        "result",
    ]
    core_present = [c for c in core_cols if c in df.columns]
    core_missing = df[core_present].isnull().sum().to_dict()
    print(f"  • Osnovni podatki tekem: {core_missing}")

    # xG Podatki
    xg_cols = [c for c in df.columns if "xg" in c.lower()]
    if xg_cols:
        xg_missing = df[xg_cols].isnull().sum().to_dict()
        print(f"  • xG Podatki:           {xg_missing}")
    else:
        print("  • xG Podatki:           [Ni stolpcev z xG]")

    # Kvote (Stavni podatki - npr. B365H, B365D, B365A ali pb kvote)
    odds_cols = [
        c
        for c in df.columns
        if any(k in c.lower() for k in ["b365", "odds", "psh", "psd", "psa"])
    ]
    if odds_cols:
        odds_null_avg = (
            df[odds_cols].isnull().mean().mean() * 100
        )  # Povprečno % manjkajočih kvot
        print(
            f"  • Stavne kvote ({len(odds_cols)} stolpcev): ~{odds_null_avg:.1f}% manjkajočih vrednosti"
        )

    print("-" * 70)

    # 3. Pregled razdelitve izidov (Domov / Neodločeno / Gostje)
    if "result" in df.columns:
        res_counts = df["result"].value_counts(normalize=True) * 100
        print("PORAZDELITEV REZULTATOV (1X2):")
        for res, pct in res_counts.items():
            print(f"  • {res}: {pct:.1f}%")

    # 4. Povprečno število golov na tekmo
    if "goals_home" in df.columns and "goals_away" in df.columns:
        avg_home = df["goals_home"].mean()
        avg_away = df["goals_away"].mean()
        print("POVPREČJE GOLOV NA TEKMO:")
        print(
            f"  • Domači: {avg_home:.2f} | Gostje: {avg_away:.2f} | Skupaj: {avg_home + avg_away:.2f}"
        )

    print("\n")


def main():
    if not DATA_DIR.exists():
        print(f"Napaka: Mapa '{DATA_DIR}' ne obstaja.")
        return

    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"V mapi '{DATA_DIR}' ni bilo najdenih CSV datotek.")
        return

    print(f"Začenjam pregled {len(csv_files)} CSV datotek...\n")
    for file in sorted(csv_files):
        inspect_dataset(file)


if __name__ == "__main__":
    main()