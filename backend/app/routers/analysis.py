from fastapi import APIRouter, Depends
from backend.app.core.auth import get_optional_user

from backend.app.core.errors import APIError
from backend.app.core.store import DATASETS, get_dataset, owns_dataset
from backend.app.schemas.common import AnalysisResponse, ForecastRequest, ForecastResponse
from backend.app.services.analytics import compute_analysis, compute_forecast

router = APIRouter(tags=["analysis"])


def _require(dataset_id, user=None):
    df = get_dataset(dataset_id)
    if df is None or (not owns_dataset(dataset_id, user["id"] if user else None)):
        raise APIError(404, "dataset_not_found", f"No dataset with id '{dataset_id}'. Upload the file again after a server restart.")
    return df


@router.get("/analysis/{dataset_id}", response_model=AnalysisResponse)
def analysis(dataset_id: str, user=Depends(get_optional_user)):
    return compute_analysis(_require(dataset_id, user), dataset_id)


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest, user=Depends(get_optional_user)):
    try:
        return compute_forecast(_require(req.dataset_id, user), req.dataset_id, req.periods)
    except ValueError as exc:
        raise APIError(422, "insufficient_history", str(exc)) from exc
