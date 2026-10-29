"""
whatif.py - What-if calculation module (Module 06)

Takes the current ("original") business numbers plus a set of proposed
changes (price, expenses, marketing, inventory) and returns the original
figures, the estimated figures, the difference, and the assumptions used.

Percent inputs are plain numbers: 10 means +10%, -5 means -5%.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1. INPUTS (agree these names with the team first)
# ---------------------------------------------------------------------------

@dataclass
class Baseline:
    """Current numbers for one product (or one business) over one period."""
    price: float                      # selling price per unit
    units_sold: float                 # units sold in the period
    unit_cost: float                  # cost of one unit (buy/make cost)
    operating_expenses: float         # rent, salaries, utilities, etc.
    marketing_budget: float           # money spent on marketing
    inventory_units: float            # units available to sell in the period
    holding_cost_per_unit: float = 0  # cost of keeping one unsold unit


@dataclass
class Changes:
    """What the user wants to try. All values are percentages."""
    price_pct: float = 0.0
    expenses_pct: float = 0.0
    marketing_pct: float = 0.0
    inventory_pct: float = 0.0


# Rules of thumb. The user (or team) can override these.
DEFAULT_ASSUMPTIONS = {
    # -1.0 means: raising price by 10% lowers units sold by 10%
    "price_elasticity": -1.0,
    # 0.1 means: doubling marketing raises units sold by about 7%
    # (small, because extra marketing has diminishing returns)
    "marketing_elasticity": 0.1,
}


# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------

def _validate(b, c):
    if b.price <= 0:
        raise ValueError("price must be greater than 0")
    if b.units_sold < 0 or b.unit_cost < 0 or b.operating_expenses < 0:
        raise ValueError("units, cost and expenses cannot be negative")
    if b.marketing_budget < 0 or b.inventory_units < 0:
        raise ValueError("marketing and inventory cannot be negative")
    if b.units_sold > b.inventory_units:
        raise ValueError("units_sold cannot be more than inventory_units")
    for name in ("price_pct", "expenses_pct", "marketing_pct", "inventory_pct"):
        if getattr(c, name) <= -100:
            raise ValueError(f"{name} must be greater than -100")


def _financials(price, units, unit_cost, opex, marketing, stock, holding):
    revenue = price * units
    cogs = unit_cost * units
    gross_profit = revenue - cogs
    leftover = max(stock - units, 0)
    holding_cost = holding * leftover
    total_expenses = opex + marketing + holding_cost
    net_profit = gross_profit - total_expenses
    margin = (net_profit / revenue * 100) if revenue else 0.0
    return {
        "price": round(price, 2),
        "units_sold": round(units, 2),
        "revenue": round(revenue, 2),
        "cost_of_goods": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "operating_expenses": round(opex, 2),
        "marketing_budget": round(marketing, 2),
        "holding_cost": round(holding_cost, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_pct": round(margin, 2),
        "inventory_units": round(stock, 2),
        "unsold_units": round(leftover, 2),
    }


# ---------------------------------------------------------------------------
# 3. MAIN FUNCTION
# ---------------------------------------------------------------------------

def calculate(baseline, changes, assumptions=None):
    a = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    _validate(baseline, changes)

    original = _financials(
        baseline.price, baseline.units_sold, baseline.unit_cost,
        baseline.operating_expenses, baseline.marketing_budget,
        baseline.inventory_units, baseline.holding_cost_per_unit,
    )

    # New input values
    new_price = baseline.price * (1 + changes.price_pct / 100)
    new_opex = baseline.operating_expenses * (1 + changes.expenses_pct / 100)
    new_marketing = baseline.marketing_budget * (1 + changes.marketing_pct / 100)
    new_stock = baseline.inventory_units * (1 + changes.inventory_pct / 100)

    # Demand: price effect, then marketing effect
    demand = baseline.units_sold * (1 + a["price_elasticity"] * changes.price_pct / 100)
    if baseline.marketing_budget > 0:
        demand *= (new_marketing / baseline.marketing_budget) ** a["marketing_elasticity"]
    demand = max(demand, 0)

    # Cannot sell more than we have in stock
    units = min(demand, new_stock)
    notes = []
    if demand > new_stock:
        notes.append(
            f"Demand ({demand:.0f} units) is higher than stock ({new_stock:.0f}), "
            "so sales are limited by inventory."
        )

    estimated = _financials(
        new_price, units, baseline.unit_cost, new_opex, new_marketing,
        new_stock, baseline.holding_cost_per_unit,
    )

    difference = {k: round(estimated[k] - original[k], 2) for k in original}

    assumptions_text = [
        f"Price elasticity = {a['price_elasticity']}: a 1% price rise changes units sold by {a['price_elasticity']}%.",
        f"Marketing elasticity = {a['marketing_elasticity']}: extra marketing lifts sales with diminishing returns.",
        "Unit cost stays the same.",
        "Expense changes do not affect sales by themselves.",
        "Units sold cannot exceed available inventory.",
        "Holding cost applies to unsold units only.",
        "Results are estimates, not guarantees.",
    ]

    return {
        "original": original,
        "estimated": estimated,
        "difference": difference,
        "assumptions": assumptions_text,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# 4. CHECKED EXAMPLES (run: python whatif.py)
# Every expected number below was worked out by hand first.
# ---------------------------------------------------------------------------

def _run_checks():
    base = Baseline(
        price=100, units_sold=1000, unit_cost=60,
        operating_expenses=20000, marketing_budget=5000,
        inventory_units=1200, holding_cost_per_unit=1,
    )

    # Original: revenue 100000, cogs 60000, holding 200, expenses 25200, net 14800
    r = calculate(base, Changes())
    assert r["original"]["net_profit"] == 14800
    assert r["estimated"]["net_profit"] == 14800  # no change -> same result

    # Price +10%: units 900, revenue 99000, cogs 54000, holding 300, net 19700
    r = calculate(base, Changes(price_pct=10))
    assert r["estimated"]["units_sold"] == 900
    assert r["estimated"]["revenue"] == 99000
    assert r["estimated"]["net_profit"] == 19700

    # Operating expenses +10%: opex 22000, net 100000-60000-27200 = 12800
    r = calculate(base, Changes(expenses_pct=10))
    assert r["estimated"]["net_profit"] == 12800

    # Inventory -20%: stock 960, sales capped at 960, net 96000-57600-25000 = 13400
    r = calculate(base, Changes(inventory_pct=-20))
    assert r["estimated"]["units_sold"] == 960
    assert r["estimated"]["net_profit"] == 13400
    assert len(r["notes"]) == 1

    print("All checks passed.")


if __name__ == "__main__":
    _run_checks()
