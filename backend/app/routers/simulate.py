from fastapi import APIRouter

from backend.app.core.errors import APIError
from backend.app.core.store import DATASETS
from backend.app.schemas.common import Baseline, CaseResult, CompareResponse, SimulateRequest, SimulateResponse
from backend.app.services.analytics import extract_baseline
from backend.app.services.simulator import CASES, simulate

router = APIRouter(tags=["simulate"])


@router.get("/simulate/baseline/{dataset_id}", response_model=Baseline)
def get_baseline(dataset_id: str):
    """Extracts baseline metrics (units, price, cost, marketing, expenses) directly from uploaded dataset."""
    if dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{dataset_id}'.")
    df = DATASETS[dataset_id]
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
