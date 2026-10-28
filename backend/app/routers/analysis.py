from fastapi import APIRouter

from backend.app.core.errors import APIError
from backend.app.core.store import DATASETS
from backend.app.schemas.common import AnalysisResponse, ForecastRequest, ForecastResponse
from backend.app.services.analytics import compute_analysis, compute_forecast

router = APIRouter(tags=["analysis"])


def _require(dataset_id):
    if dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{dataset_id}'. Upload the file again after a server restart.")
    return DATASETS[dataset_id]


@router.get("/analysis/{dataset_id}", response_model=AnalysisResponse)
def analysis(dataset_id: str):
    return compute_analysis(_require(dataset_id), dataset_id)


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    try:
        return compute_forecast(_require(req.dataset_id), req.dataset_id, req.periods)
    except ValueError as exc:
        raise APIError(422, "insufficient_history", str(exc)) from exc
