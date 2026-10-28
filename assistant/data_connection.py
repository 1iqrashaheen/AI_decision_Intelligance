"""Collect results for one dataset before passing them to the assistant."""
from assistant.business_context import get_business_context


def prepare_business_data(analysis=None, simulation=None, forecasting=None, recommendations=None):
    analysis = get_business_context() if analysis is None else analysis
    if hasattr(analysis, "model_dump"):
        analysis = analysis.model_dump()
    if not isinstance(analysis, dict) or "totals" not in analysis:
        raise ValueError("Pass structured business_analysis output, not an unverified prose summary.")
    result = {"analysis": analysis}
    for name, value in [("simulation", simulation), ("forecasting", forecasting), ("recommendations", recommendations)]:
        if value is None:
            continue
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be a structured result with a dataset_id.")
        if value.get("dataset_id") != analysis.get("dataset_id") or not value.get("dataset_id"):
            raise ValueError(f"{name} belongs to another dataset or has no dataset_id.")
        result[name] = value
    return result
