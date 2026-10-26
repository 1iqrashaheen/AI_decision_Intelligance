"""Business analysis, trend calculations, and forecasting logic.
Computes real business totals, product performance, and future sales projections from cleaned data.
"""
from typing import Any, Dict, List
import numpy as np
import pandas as pd

from app.schemas.common import AnalysisResponse, Baseline, ForecastResponse, Kpi


def compute_analysis(df: pd.DataFrame, dataset_id: str) -> AnalysisResponse:
    """Computes comprehensive business totals, trends, product breakdown and findings."""
    total_rev = float(df["revenue"].sum())
    total_units = float(df["units"].sum())
    total_cogs = float(df["cogs"].sum())
    total_mkt = float(df["marketing_spend"].sum()) if "marketing_spend" in df.columns else 0.0
    total_exp = float(df["expenses"].sum()) if "expenses" in df.columns else 0.0

    total_costs = total_cogs + total_mkt + total_exp
    total_profit = total_rev - total_costs
    margin_pct = (total_profit / total_rev * 100) if total_rev > 0 else 0.0

    kpis = [
        Kpi(label="Total Revenue", value=round(total_rev, 2)),
        Kpi(label="Total Units Sold", value=round(total_units, 2)),
        Kpi(label="Total Costs", value=round(total_costs, 2)),
        Kpi(label="Net Profit", value=round(total_profit, 2)),
        Kpi(label="Profit Margin (%)", value=round(margin_pct, 2)),
    ]

    # Monthly Trend
    trend: List[Dict[str, Any]] = []
    if "month" in df.columns and len(df["month"].dropna().unique()) > 0:
        grouped_m = df.groupby("month")
        for m, grp in sorted(grouped_m):
            rev_m = float(grp["revenue"].sum())
            cogs_m = float(grp["cogs"].sum())
            mkt_m = float(grp["marketing_spend"].sum()) if "marketing_spend" in grp.columns else 0.0
            exp_m = float(grp["expenses"].sum()) if "expenses" in grp.columns else 0.0
            profit_m = rev_m - (cogs_m + mkt_m + exp_m)
            trend.append({
                "period": str(m),
                "revenue": round(rev_m, 2),
                "profit": round(profit_m, 2),
                "units": round(float(grp["units"].sum()), 2),
            })
    else:
        trend = [{"period": "Overall", "revenue": round(total_rev, 2), "profit": round(total_profit, 2)}]

    # Product Performance
    by_product: List[Dict[str, Any]] = []
    if "product" in df.columns:
        p_grp = df.groupby("product")
        p_data = []
        for p, grp in p_grp:
            p_rev = float(grp["revenue"].sum())
            p_units = float(grp["units"].sum())
            p_cogs = float(grp["cogs"].sum())
            p_gross = p_rev - p_cogs
            p_margin = (p_gross / p_rev * 100) if p_rev > 0 else 0.0
            p_share = (p_rev / total_rev * 100) if total_rev > 0 else 0.0
            p_data.append({
                "product": str(p),
                "units": round(p_units, 2),
                "revenue": round(p_rev, 2),
                "gross_margin": round(p_margin, 2),
                "margin_pct": round(p_margin, 2),
                "share_pct": round(p_share, 2),
            })
        p_data.sort(key=lambda x: x["revenue"], reverse=True)
        by_product = p_data[:15]

    # Automated Business Findings
    findings: List[str] = []
    if by_product:
        top_p = by_product[0]
        findings.append(f"Top performing product is '{top_p['product']}' with ${top_p['revenue']:,.2f} in sales ({top_p['share_pct']}% of total).")
        low_margin = min(by_product, key=lambda x: x["gross_margin"])
        findings.append(f"Lowest gross margin is '{low_margin['product']}' at {low_margin['gross_margin']}%.")

    if len(trend) >= 2:
        first_m, last_m = trend[0], trend[-1]
        pct_change = ((last_m["revenue"] - first_m["revenue"]) / first_m["revenue"] * 100) if first_m["revenue"] > 0 else 0.0
        direction = "increased" if pct_change >= 0 else "decreased"
        findings.append(f"Sales {direction} by {abs(pct_change):.1f}% from {first_m['period']} to {last_m['period']}.")

    if not findings:
        findings.append("Baseline performance calculated successfully from uploaded data.")

    return AnalysisResponse(
        dataset_id=dataset_id,
        kpis=kpis,
        trend=trend,
        by_product=by_product,
        findings=findings,
        source="calculated",
    )


def compute_forecast(df: pd.DataFrame, dataset_id: str, periods: int = 3) -> ForecastResponse:
    """Estimates future monthly sales using historical trend linear projection."""
    if "month" not in df.columns:
        return ForecastResponse(
            dataset_id=dataset_id,
            method="linear_extrapolation",
            forecast=[{"period": f"+{i}", "revenue": 10000.0} for i in range(1, periods + 1)],
            source="mock",
        )

    monthly_rev = df.groupby("month")["revenue"].sum().sort_index()
    if len(monthly_rev) < 2:
        avg = float(monthly_rev.mean()) if len(monthly_rev) else 10000.0
        forecast = [{"period": f"+{i}", "revenue": round(avg, 2)} for i in range(1, periods + 1)]
        return ForecastResponse(
            dataset_id=dataset_id,
            method="historical_average",
            forecast=forecast,
            source="calculated",
        )

    y = monthly_rev.values.astype(float)
    x = np.arange(len(y), dtype=float)

    # Ordinary Least Squares slope and intercept
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    slope = np.sum((x - x_mean) * (y - y_mean)) / (np.sum((x - x_mean) ** 2) or 1.0)
    intercept = y_mean - slope * x_mean

    last_period_str = str(monthly_rev.index[-1])
    # Parse last year and month
    try:
        y_int, m_int = map(int, last_period_str.split("-"))
    except Exception:
        y_int, m_int = 2025, 12

    forecast = []
    for step in range(1, periods + 1):
        future_idx = len(y) + step - 1
        predicted_rev = max(float(slope * future_idx + intercept), 0.0)

        # Increment month
        cur_m = m_int + step
        cur_y = y_int + (cur_m - 1) // 12
        cur_m = ((cur_m - 1) % 12) + 1
        period_str = f"{cur_y:04d}-{cur_m:02d}"

        forecast.append({
            "period": period_str,
            "revenue": round(predicted_rev, 2),
            "step": step,
        })

    return ForecastResponse(
        dataset_id=dataset_id,
        method="linear_trend",
        forecast=forecast,
        source="calculated",
    )


def extract_baseline(df: pd.DataFrame) -> Baseline:
    """Extracts aggregate baseline business metrics for what-if simulation from clean data."""
    total_rev = float(df["revenue"].sum())
    total_units = float(df["units"].sum())
    total_cogs = float(df["cogs"].sum())
    total_mkt = float(df["marketing_spend"].sum()) if "marketing_spend" in df.columns else 0.0
    total_exp = float(df["expenses"].sum()) if "expenses" in df.columns else 0.0

    avg_price = (total_rev / total_units) if total_units > 0 else 0.0
    avg_cost = (total_cogs / total_units) if total_units > 0 else 0.0

    return Baseline(
        units=round(total_units, 2),
        price=round(avg_price, 2),
        unit_cost=round(avg_cost, 2),
        marketing=round(total_mkt, 2),
        expenses=round(total_exp, 2),
    )
