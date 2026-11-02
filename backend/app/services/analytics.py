"""Connect the analysis module and Arham's monthly forecast to the API."""
import numpy as np
import pandas as pd

from business_analysis import analyze_business_data
from backend.app.schemas.common import AnalysisResponse, Baseline, ForecastResponse
from backend.app.core.store import DATASETS, DATASET_METADATA

_ANALYSES = {}


def compute_analysis(df, dataset_id):
    stored = DATASETS.get(dataset_id) is df
    if stored and dataset_id in _ANALYSES:
        return _ANALYSES[dataset_id]
    result = analyze_business_data(df, dataset_id)
    metadata = DATASET_METADATA.get(dataset_id, {})
    for key in result["quality"]:
        if key in metadata:
            result["quality"][key] = metadata[key]
    response = AnalysisResponse(**result)
    if stored:
        _ANALYSES[dataset_id] = response
    return response


def compute_forecast(df, dataset_id, periods=3):
    result = analyze_business_data(df, dataset_id)
    if result["dataset_kind"] != "sales" or len(result["trend"]) < 3:
        raise ValueError("A sales forecast needs at least three observed months of sales history.")
    trend = result["trend"]
    dates = pd.PeriodIndex([r["period"] for r in trend], freq="M")
    if len(pd.period_range(dates.min(), dates.max(), freq="M")) != len(dates):
        raise ValueError("Monthly history has gaps. Missing months cannot be assumed to have zero sales.")
    values = np.array([r["revenue"] for r in trend])
    slope, intercept = np.polyfit(np.arange(len(values)), values, 1)
    future = [{"period": str(dates[-1] + i), "revenue": round(max(0, float(slope * (len(values) + i - 1) + intercept)), 2)}
              for i in range(1, periods + 1)]
    return ForecastResponse(dataset_id=dataset_id, method="linear_trend", forecast=future,
                            recommendation="A basic trend estimate from observed monthly totals. Partial months and seasonality can distort it; it is not guaranteed.", source="calculated")


def extract_baseline(df):
    result = analyze_business_data(df)
    t = result["totals"]
    if result["dataset_kind"] != "sales" or t["profit"] is None or t["units"] <= 0:
        raise ValueError("Simulation requires sales with positive net units and complete unit_cost, marketing_spend and expenses. Missing costs cannot be assumed.")
    return Baseline(units=t["units"], price=t["revenue"] / t["units"],
                    unit_cost=t["cogs"] / t["units"], marketing=t["marketing"], expenses=t["expenses"])
