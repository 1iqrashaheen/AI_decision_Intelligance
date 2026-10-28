from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_data(path=None):
    file = Path(path) if path else ROOT / "data/team_cleaned/online_retail_cleaned.csv"
    if not file.exists():
        raise FileNotFoundError("Dataset unavailable. Run python scripts/fetch_team_data.py, or upload a CSV/Excel file in the website.")
    return pd.read_csv(file, low_memory=False) if file.suffix.lower() == ".csv" else pd.read_excel(file)
