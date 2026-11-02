"""Use Ahsan's saved forecast only when the daily sales data matches."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def published_forecast(df, dataset_id):
    if not {"date", "units", "price", "invoice_no", "stock_code"} <= set(df):
        return None
    manifest = json.loads((ROOT / "training_manifest.json").read_text(encoding="utf-8"))
    dates = pd.to_datetime(df.date, utc=True).dt.strftime("%Y-%m-%d")
    daily = (df.units * df.price).groupby(dates).sum()
    if daily.index.min() != manifest["start"] or daily.index.max() != manifest["end"]:
        return None
    index = pd.date_range(manifest["start"], manifest["end"]).strftime("%Y-%m-%d")
    daily = daily.reindex(index, fill_value=0)
    records = [[str(day), f"{value:.2f}"] for day, value in daily.items()]
    signature = hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()
    if signature != manifest["daily_series_sha256"]:
        return None
    estimates = pd.read_csv(ROOT / "outputs/future_30_days_forecast.csv")
    return {"dataset_id": dataset_id, "method": "Ahsan's published Random Forest, recursive daily forecast",
            "forecast": [{"period": str(r.date), "revenue": float(r.predicted_sales_revenue_gbp)} for r in estimates.itertuples()],
            "recommendation": "Historical forecast for the dates shown, based on the matching UCI daily net-sales series. Assumes zero Saturday sales and nonnegative future revenue. It is not a forecast for the current calendar month.",
            "source": "team_published", "source_commit": manifest["source_commit"]}
