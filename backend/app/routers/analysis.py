from fastapi import APIRouter

from app.core.errors import APIError
from app.core.store import DATASETS
from app.schemas.common import AnalysisResponse, ForecastRequest, ForecastResponse

router = APIRouter(tags=["analysis"])


def _require(dataset_id: str):
    if dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{dataset_id}'.")


@router.get("/analysis/{dataset_id}", response_model=AnalysisResponse)
def analysis(dataset_id: str):
    _require(dataset_id)
    # MOCK: replace with Ahsan's analysis module
    return AnalysisResponse(
        dataset_id=dataset_id,
        kpis=[{"label": "Revenue", "value": 100000}, {"label": "Profit", "value": 25000}],
        trend=[{"period": "2025-01", "revenue": 8000, "profit": 2000}, {"period": "2025-02", "revenue": 8500, "profit": 2200}],
        by_product=[{"product": "A", "revenue": 60000, "margin_pct": 30}, {"product": "B", "revenue": 40000, "margin_pct": 18}],
        findings=["Product B has the lowest margin (mock)."],
    )


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    _require(req.dataset_id)
    # MOCK: replace with Fazeela's forecasting module
    return ForecastResponse(
        dataset_id=req.dataset_id, method="mock-linear",
        forecast=[{"period": f"+{i}", "revenue": 9000 + i * 300} for i in range(1, req.periods + 1)],
    )
