
from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "online_retail_II.xlsx"

def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name="Year 2009-2010")
    return df

if __name__ == "__main__":
    data = load_data()

    print("Dataset loaded successfully!")
    print("Number of rows:", len(data))
    print("Number of columns:", len(data.columns))
    print("\nColumn names:")
    print(data.columns.tolist())
    print("\nFirst five records:")
    print(data.head().to_string(index=False))
