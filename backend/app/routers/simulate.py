from fastapi import APIRouter

from app.schemas.common import CaseResult, CompareResponse, SimulateRequest, SimulateResponse
from app.services.simulator import CASES, simulate

router = APIRouter(tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
def run(req: SimulateRequest):
    return simulate(req.baseline, req.changes, req.assumptions)


@router.post("/simulate/compare", response_model=CompareResponse)
def compare(req: SimulateRequest):
    """Runs best / expected / worst assumption sets on the same inputs."""
    return CompareResponse(cases=[
        CaseResult(case=name, assumptions=a, result=simulate(req.baseline, req.changes, a))
        for name, a in CASES.items()
    ])
