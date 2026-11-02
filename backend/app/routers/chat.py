import re

from fastapi import APIRouter, Depends
from backend.app.core.auth import get_optional_user

from assistant.ai_assistant import answer_question
from assistant.data_connection import prepare_business_data
from backend.app.core.errors import APIError
from backend.app.core.store import DATASETS, get_dataset, owns_dataset
from backend.app.schemas.common import ChatRequest, ChatResponse, Changes, Assumptions
from backend.app.services.analytics import compute_analysis, compute_forecast, extract_baseline
from backend.app.services.simulator import simulate
from forecasting.integration import published_forecast

router = APIRouter(tags=["chat"])


def _scenario_from_question(question, df):
    q = question.lower()
    if not any(w in q for w in ["what if", "what happens if", "what-if", "increase", "raise", "decrease", "reduce", "cut"]):
        return None
    percents = re.findall(r"(?<!\w)([+-]?\d+(?:\.\d+)?)\s*%", q)
    fields = [field for field, words in [("price_pct", ["price", "prices"]), ("cost_pct", ["unit cost"]),
              ("expenses_pct", ["expense", "expenses"]), ("marketing_pct", ["marketing"])] if any(w in q for w in words)]
    if len(percents) != 1 or len(fields) != 1:
        return None
    change = float(percents[0]) / 100
    if any(w in q for w in ["decrease", "reduce", "cut", "lower"]):
        change = -abs(change)
    if not -1 <= change <= 5:
        raise ValueError("Scenario changes must be between -100% and +500%.")
    return simulate(extract_baseline(df), Changes(**{fields[0]: change}), Assumptions())


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user=Depends(get_optional_user)):
    df = get_dataset(req.dataset_id)
    if df is None or (not owns_dataset(req.dataset_id, user["id"] if user else None)):
        raise APIError(404, "dataset_not_found", "Selected dataset is unavailable. Upload it again after a server restart.")
    analysis = compute_analysis(df, req.dataset_id).model_dump()
    scenario = req.scenario
    if scenario is not None:
        if req.scenario_dataset_id != req.dataset_id:
            raise APIError(422, "scenario_dataset_mismatch", "A selected scenario must include its matching scenario_dataset_id.")
        t = analysis["totals"]
        if analysis["dataset_kind"] != "sales" or any(t.get(k) is None or abs(getattr(scenario.original, k) - t[k]) > 0.02 for k in ["revenue", "profit", "units", "cogs", "marketing", "expenses"]):
            raise APIError(422, "scenario_dataset_mismatch", "The selected scenario baseline does not match this dataset.")
        for m in [scenario.original, scenario.scenario]:
            expected_profit = m.revenue - m.cogs - m.marketing - m.expenses
            if abs(expected_profit - m.profit) > 0.03:
                raise APIError(422, "invalid_scenario", "Scenario profit does not match its revenue and costs.")
    warning = None
    try:
        calculated = _scenario_from_question(req.question, df)
        if calculated is not None:
            scenario = calculated
    except ValueError as exc:
        scenario = None
        warning = str(exc)
    forecasting = None
    if any(w in req.question.lower() for w in ["forecast", "predict", "next month", "next year", "future", "tomorrow"]):
        try:
            forecasting = published_forecast(df, req.dataset_id) or compute_forecast(df, req.dataset_id).model_dump()
        except ValueError:
            pass
    scenario_dict = {**scenario.model_dump(), "dataset_id": req.dataset_id} if scenario else None
    context = prepare_business_data(analysis, simulation=scenario_dict, forecasting=forecasting)
    try:
        result = answer_question(req.question, context)
    except ValueError as exc:
        raise APIError(422, "invalid_question", str(exc)) from exc
    except RuntimeError as exc:
        raise APIError(503, "assistant_unavailable", str(exc)) from exc
    if warning:
        result["warnings"].append(warning)
    return ChatResponse(**result)
