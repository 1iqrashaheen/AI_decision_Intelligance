"""What-If calculation engine connecting baseline metrics, proposed changes, and elasticity assumptions.
"""
from typing import List
from app.schemas.common import Assumptions, Baseline, Changes, Metrics, SimulateResponse


def _metrics(units: float, price: float, unit_cost: float, marketing: float, expenses: float) -> Metrics:
    revenue = units * price
    cogs = units * unit_cost
    profit = revenue - cogs - marketing - expenses
    margin = (profit / revenue * 100) if revenue else 0.0
    return Metrics(
        units=round(units, 2),
        revenue=round(revenue, 2),
        cogs=round(cogs, 2),
        marketing=round(marketing, 2),
        expenses=round(expenses, 2),
        profit=round(profit, 2),
        margin_pct=round(margin, 2),
    )


def _generate_notes(b: Baseline, c: Changes, a: Assumptions, original: Metrics, scenario: Metrics) -> List[str]:
    notes = []
    if c.price_pct >= 0.10:
        notes.append(f"Price rise of {c.price_pct*100:.0f}%: volume reduced by price elasticity ({a.elasticity}).")
    elif c.price_pct <= -0.10:
        notes.append(f"Price cut of {abs(c.price_pct)*100:.0f}%: profits depend on volume compensating for lower margin.")

    if c.marketing_pct >= 0.20:
        notes.append(f"Marketing spend increased by {c.marketing_pct*100:.0f}%: volume lift factor ({a.marketing_lift}).")

    if c.cost_pct >= 0.10:
        notes.append(f"Unit cost increase of {c.cost_pct*100:.0f}% directly impacts gross margins.")

    if c.expenses_pct >= 0.15:
        notes.append(f"Operating expense increase of {c.expenses_pct*100:.0f}% reduces bottom-line net profit.")

    if scenario.profit < original.profit:
        notes.append("Projected profit is lower than the baseline.")

    if scenario.profit < 0:
        notes.append("Warning: This scenario is projected to operate at a net loss.")

    if not notes:
        notes.append("No critical risk flags detected. Estimates based on stated assumptions, not guaranteed outcomes.")

    return notes


def simulate(b: Baseline, c: Changes, a: Assumptions) -> SimulateResponse:
    original = _metrics(b.units, b.price, b.unit_cost, b.marketing, b.expenses)

    # Elasticity demand model matching both frontend formulas and Arayash's module
    volume_factor = (1 + a.elasticity * c.price_pct) * (1 + a.marketing_lift * c.marketing_pct)
    new_units = max(b.units * volume_factor, 0.0)

    new_price = max(b.price * (1 + c.price_pct), 0.0)
    new_cost = max(b.unit_cost * (1 + c.cost_pct), 0.0)
    new_marketing = max(b.marketing * (1 + c.marketing_pct), 0.0)
    new_expenses = max(b.expenses * (1 + c.expenses_pct), 0.0)

    scenario = _metrics(new_units, new_price, new_cost, new_marketing, new_expenses)
    delta = {k: round(getattr(scenario, k) - getattr(original, k), 2) for k in Metrics.model_fields}
    notes = _generate_notes(b, c, a, original, scenario)

    return SimulateResponse(original=original, scenario=scenario, delta=delta, assumptions=a, notes=notes)


CASES = {
    "best": Assumptions(elasticity=-0.6, marketing_lift=0.25),
    "expected": Assumptions(elasticity=-1.2, marketing_lift=0.15),
    "worst": Assumptions(elasticity=-1.8, marketing_lift=0.05),
}
