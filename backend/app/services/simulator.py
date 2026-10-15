"""PLACEHOLDER what-if engine using the formulas from the frontend README.
Arayash's module replaces this; keep the function signature the same."""
from app.schemas.common import Assumptions, Baseline, Changes, Metrics, SimulateResponse

NOTES = ["Estimates based on stated assumptions, not guaranteed outcomes."]


def _metrics(units, price, unit_cost, marketing, expenses) -> Metrics:
    revenue = units * price
    cogs = units * unit_cost
    profit = revenue - cogs - marketing - expenses
    margin = (profit / revenue * 100) if revenue else 0.0
    return Metrics(
        units=round(units, 2), revenue=round(revenue, 2), cogs=round(cogs, 2),
        marketing=round(marketing, 2), expenses=round(expenses, 2),
        profit=round(profit, 2), margin_pct=round(margin, 2),
    )


def simulate(b: Baseline, c: Changes, a: Assumptions) -> SimulateResponse:
    original = _metrics(b.units, b.price, b.unit_cost, b.marketing, b.expenses)
    new_units = b.units * (1 + a.elasticity * c.price_pct) * (1 + a.marketing_lift * c.marketing_pct)
    new_units = max(new_units, 0)
    scenario = _metrics(
        new_units,
        b.price * (1 + c.price_pct),
        b.unit_cost * (1 + c.cost_pct),
        b.marketing * (1 + c.marketing_pct),
        b.expenses * (1 + c.expenses_pct),
    )
    delta = {k: round(getattr(scenario, k) - getattr(original, k), 2) for k in Metrics.model_fields}
    return SimulateResponse(original=original, scenario=scenario, delta=delta, assumptions=a, notes=NOTES)


CASES = {
    "best": Assumptions(elasticity=-0.6, marketing_lift=0.25),
    "expected": Assumptions(elasticity=-1.2, marketing_lift=0.15),
    "worst": Assumptions(elasticity=-1.8, marketing_lift=0.05),
}
