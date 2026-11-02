"""
dataset_loader.py - connects the Online Retail II dataset to whatif.py

Two jobs:
  1. prepare : read the big Excel file once, clean it, save a small CSV.
  2. baseline: read the clean CSV and build the Baseline numbers
               (for the whole business, or for one product).

Run from the project folder:
  python whatif/dataset_loader.py prepare C:\\path\\to\\online_retail_II.xlsx
  python whatif/dataset_loader.py demo
  python whatif/dataset_loader.py demo 85123A
"""

import os
import sys

import pandas as pd

from whatif import Baseline, Changes, calculate

CLEAN_CSV = os.path.join(os.path.dirname(__file__), "local_data", "retail_clean.csv")

# The dataset has sales only. These numbers are NOT in the data, so they are
# assumptions (the user can type their own values on the what-if page).
DEFAULTS = {
    "unit_cost_ratio": 0.60,          # cost of one unit = 60% of its price
    "operating_expense_ratio": 0.15,  # operating expenses = 15% of revenue
    "marketing_ratio": 0.05,          # marketing budget = 5% of revenue
}
# Inventory is not in the data either. It stays empty (no stock limit) unless
# the caller passes inventory_units in overrides.

# Rows that are fees or adjustments, not real products
NON_PRODUCT_CODES = {"POST", "D", "M", "DOT", "BANK CHARGES", "CRUK", "S", "AMAZONFEE", "B"}


# ---------------------------------------------------------------------------
# 1. CLEANING
# ---------------------------------------------------------------------------

def clean(df):
    """Remove duplicates, cancellations, bad prices and non-product rows."""
    df = df.drop_duplicates()
    df = df[~df["Invoice"].astype(str).str.startswith("C")]   # cancelled orders
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
    df = df[~df["StockCode"].astype(str).str.upper().isin(NON_PRODUCT_CODES)]
    df = df.copy()
    df["Revenue"] = df["Quantity"] * df["Price"]
    return df


def prepare(xlsx_path):
    """Read the Excel file (slow, about 2 minutes), clean it, save a CSV."""
    print("Reading Excel file. This takes about 2 minutes...")
    sheets = pd.read_excel(xlsx_path, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True)
    print("Rows before cleaning:", len(df))
    df = clean(df)
    print("Rows after cleaning:", len(df))
    os.makedirs(os.path.dirname(CLEAN_CSV), exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False)
    print("Saved:", CLEAN_CSV)


# ---------------------------------------------------------------------------
# 2. BUILD THE BASELINE
# ---------------------------------------------------------------------------

def load_clean():
    df = pd.read_csv(CLEAN_CSV, parse_dates=["InvoiceDate"])
    return df


def make_baseline(df, stock_code=None, overrides=None):
    """
    Build a Baseline from cleaned data.
    - Uses the 12 months before the last month (the last month may be incomplete).
    - stock_code=None means the whole business; otherwise one product.
    - overrides: dict to replace any default, e.g. {"unit_cost": 1.5}
    """
    overrides = overrides or {}
    months = df["InvoiceDate"].dt.to_period("M")
    last_12 = sorted(months.unique())[-13:-1]
    df = df[months.isin(last_12)]
    if stock_code is not None:
        df = df[df["StockCode"].astype(str) == str(stock_code)]
    if df.empty:
        raise ValueError("No sales found for this selection")

    units = float(df["Quantity"].sum())
    revenue = float(df["Revenue"].sum())
    price = revenue / units
    d = {**DEFAULTS}

    baseline = Baseline(
        price=round(price, 4),
        units_sold=units,
        unit_cost=round(overrides.get("unit_cost", price * d["unit_cost_ratio"]), 4),
        operating_expenses=overrides.get("operating_expenses", revenue * d["operating_expense_ratio"]),
        marketing_budget=overrides.get("marketing_budget", revenue * d["marketing_ratio"]),
        inventory_units=overrides.get("inventory_units"),
        holding_cost_per_unit=overrides.get("holding_cost_per_unit", 0.0),
    )
    info = {
        "period": f"{last_12[0]} to {last_12[-1]}",
        "selection": "whole business" if stock_code is None else f"product {stock_code}",
    }
    return baseline, info


# ---------------------------------------------------------------------------
# 3. DEMO
# ---------------------------------------------------------------------------

def demo(stock_code=None):
    df = load_clean()
    baseline, info = make_baseline(df, stock_code)
    print("Selection:", info["selection"], "| Period:", info["period"])
    print("Baseline:", baseline)
    result = calculate(baseline, Changes(price=0.10, marketing=0.20))
    print("\nWhat if price +10% and marketing +20%?")
    for key in ("units_sold", "revenue", "total_expenses", "net_profit"):
        print(f"  {key:15s} original {result['original'][key]:>14,.2f}"
              f"   estimated {result['estimated'][key]:>14,.2f}"
              f"   change {result['difference'][key]:>12,.2f}")
    for n in result["notes"]:
        print("Note:", n)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "prepare":
        prepare(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == "demo":
        demo(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(__doc__)
