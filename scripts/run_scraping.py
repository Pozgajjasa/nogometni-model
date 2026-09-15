"""
Zaženi scraping za vse lige, definirane v configs/config.yaml.

Uporaba:
    python scripts/run_scraping.py
"""

import sys
from pathlib import Path

# Omogoči import iz src/, ko skripto poganjaš iz korena projekta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.scrape import run

if __name__ == "__main__":
    run()
