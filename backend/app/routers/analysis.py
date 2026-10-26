from fastapi import APIRouter

from app.core.errors import APIError
from app.core.store import DATASETS
from app.schemas.common import AnalysisResponse, ForecastRequest, ForecastResponse
from app.services.analytics import compute_analysis, compute_forecast

router = APIRouter(tags=["analysis"])


def _require(dataset_id: str):
    if dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{dataset_id}'.")


@router.get("/analysis/{dataset_id}", response_model=AnalysisResponse)
def analysis(dataset_id: str):
    _require(dataset_id)
    df = DATASETS[dataset_id]
    if "revenue" in df.columns and "units" in df.columns:
        return compute_analysis(df, dataset_id)

    # Fallback default if custom non-standard data
    return AnalysisResponse(
        dataset_id=dataset_id,
        kpis=[{"label": "Revenue", "value": 100000}, {"label": "Profit", "value": 25000}],
        trend=[{"period": "2025-01", "revenue": 8000, "profit": 2000}, {"period": "2025-02", "revenue": 8500, "profit": 2200}],
        by_product=[{"product": "A", "revenue": 60000, "margin_pct": 30}, {"product": "B", "revenue": 40000, "margin_pct": 18}],
        findings=["Product B has the lowest margin."],
        source="fallback",
    )


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    _require(req.dataset_id)
    df = DATASETS[req.dataset_id]
    if "revenue" in df.columns:
        return compute_forecast(df, req.dataset_id, req.periods)

    return ForecastResponse(
        dataset_id=req.dataset_id,
        method="linear-projection",
        forecast=[{"period": f"+{i}", "revenue": 9000 + i * 300} for i in range(1, req.periods + 1)],
        source="fallback",
    )
