from fastapi import APIRouter, Depends
from backend.app.core.auth import get_optional_user

from backend.app.core.errors import APIError
from backend.app.core.store import DATASETS, get_dataset, owns_dataset
from backend.app.schemas.common import Baseline, CaseResult, CompareResponse, SimulateRequest, SimulateResponse
from backend.app.services.analytics import extract_baseline
from backend.app.services.simulator import CASES, simulate

router = APIRouter(tags=["simulate"])


@router.get("/simulate/baseline/{dataset_id}", response_model=Baseline)
def get_baseline(dataset_id: str, user=Depends(get_optional_user)):
    """Extracts baseline metrics (units, price, cost, marketing, expenses) directly from uploaded dataset."""
    df = get_dataset(dataset_id)
    if df is None or (not owns_dataset(dataset_id, user["id"] if user else None)):
        raise APIError(404, "dataset_not_found", "Dataset not found or you do not have access to it.")
    try:
        return extract_baseline(df)
    except ValueError as exc:
        raise APIError(422, "missing_simulation_inputs", str(exc)) from exc


@router.post("/simulate", response_model=SimulateResponse)
def run(req: SimulateRequest):
    """Calculates what-if scenario figures and comparisons against baseline."""
    return simulate(req.baseline, req.changes, req.assumptions)


@router.post("/simulate/compare", response_model=CompareResponse)
def compare(req: SimulateRequest):
    """Runs best / expected / worst assumption sets on the same inputs."""
    return CompareResponse(cases=[
        CaseResult(case=name, assumptions=a, result=simulate(req.baseline, req.changes, a))
        for name, a in CASES.items()
    ])
