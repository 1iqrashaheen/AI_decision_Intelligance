"""
whatif.py - What-if calculation module (Module 06)

Uses the SAME rules as the website simulator (js/app.js, function simulate):

  volume factor = max(0, (1 + elasticity x price change)
                         x (1 + marketing_lift x marketing change))
  units     = units sold x volume factor
  revenue   = units x price x (1 + price change)
  cost      = units x unit cost x (1 + cost change)
  marketing = marketing budget x (1 + marketing change)
  expenses  = operating expenses x (1 + expenses change)
  profit    = revenue - cost - marketing - expenses

All changes are decimals: 0.10 means +10%, -0.05 means -5%.

Inventory is an optional extra that the website does not have. It is used only
when Baseline.inventory_units is given: sales are then limited by stock and
unsold units carry a holding cost. If inventory_units is left as None, the
results match the website exactly.
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# 1. INPUTS
# ---------------------------------------------------------------------------

@dataclass
class Baseline:
    """Current numbers for one product (or one business) over one period."""
    price: float                      # selling price per unit
    units_sold: float                 # units sold in the period
    unit_cost: float                  # cost of one unit (buy/make cost)
    operating_expenses: float         # rent, salaries, utilities, etc.
    marketing_budget: float           # money spent on marketing
    inventory_units: Optional[float] = None  # units available to sell (optional)
    holding_cost_per_unit: float = 0.0       # cost of keeping one unsold unit


@dataclass
class Changes:
    """What the user wants to try. All values are decimals: 0.10 = +10%."""
    price: float = 0.0
    cost: float = 0.0
    marketing: float = 0.0
    expenses: float = 0.0
    inventory: float = 0.0            # needs Baseline.inventory_units


# Same defaults as the website (js/app.js, DEFAULT_ASSUMPTIONS)
DEFAULT_ASSUMPTIONS = {
    # -1.2 means: a 10% price rise cuts units sold by about 12%
    "elasticity": -1.2,
    # 0.15 means: +100% marketing gives +15% units sold
    "marketing_lift": 0.15,
}

CHANGE_NAMES = ("price", "cost", "marketing", "expenses", "inventory")


# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------

def _validate(b, c, a):
    if b.price <= 0:
        raise ValueError("price must be greater than 0")
    if b.units_sold < 0 or b.unit_cost < 0 or b.operating_expenses < 0:
        raise ValueError("units, cost and expenses cannot be negative")
    if b.marketing_budget < 0 or b.holding_cost_per_unit < 0:
        raise ValueError("marketing and holding cost cannot be negative")
    if b.inventory_units is not None:
        if b.inventory_units < 0:
            raise ValueError("inventory cannot be negative")
        if b.units_sold > b.inventory_units:
            raise ValueError("units_sold cannot be more than inventory_units")
    elif c.inventory != 0:
        raise ValueError("an inventory change needs Baseline.inventory_units")
    for name in CHANGE_NAMES:
        value = getattr(c, name)
        if value <= -1:
            raise ValueError(f"{name} must be greater than -1 (that is -100%)")
        if value > 5:
            raise ValueError(
                f"{name}={value} looks like a percent number. "
                "Use a decimal instead (0.10 means +10%)."
            )
    if a["elasticity"] > 0:
        raise ValueError("elasticity must be 0 or negative")
    if a["marketing_lift"] < 0:
        raise ValueError("marketing_lift cannot be negative")


def _financials(price, units, unit_cost, opex, marketing, stock, holding):
    revenue = price * units
    cogs = unit_cost * units
    gross_profit = revenue - cogs
    if stock is None:
        unsold, holding_cost = None, 0.0
    else:
        unsold = max(stock - units, 0)
        holding_cost = holding * unsold
    total_expenses = opex + marketing + holding_cost
    net_profit = gross_profit - total_expenses
    margin = net_profit / revenue if revenue else 0.0
    return {
        "price": price,
        "unit_cost": unit_cost,
        "units_sold": units,
        "revenue": revenue,
        "cost_of_goods": cogs,
        "gross_profit": gross_profit,
        "operating_expenses": opex,
        "marketing_budget": marketing,
        "holding_cost": holding_cost,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": margin,          # decimal: 0.19 = 19%
        "inventory_units": stock,
        "unsold_units": unsold,
    }


def _round(d):
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = None
        elif k in ("profit_margin", "volume_factor"):
            out[k] = round(v, 4)
        else:
            out[k] = round(v, 2)
    return out


# ---------------------------------------------------------------------------
# 3. MAIN FUNCTION
# ---------------------------------------------------------------------------

def calculate(baseline, changes, assumptions=None):
    a = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    _validate(baseline, changes, a)

    original = _financials(
        baseline.price, baseline.units_sold, baseline.unit_cost,
        baseline.operating_expenses, baseline.marketing_budget,
        baseline.inventory_units, baseline.holding_cost_per_unit,
    )
    original["volume_factor"] = 1.0

    # New input values
    new_price = baseline.price * (1 + changes.price)
    new_cost = baseline.unit_cost * (1 + changes.cost)
    new_marketing = baseline.marketing_budget * (1 + changes.marketing)
    new_opex = baseline.operating_expenses * (1 + changes.expenses)

    # Demand: same rule as the website
    volume_factor = max(
        0.0,
        (1 + a["elasticity"] * changes.price)
        * (1 + a["marketing_lift"] * changes.marketing),
    )
    units = baseline.units_sold * volume_factor

    # Optional inventory limit (not in the website)
    notes = []
    new_stock = None
    if baseline.inventory_units is not None:
        new_stock = baseline.inventory_units * (1 + changes.inventory)
        if units > new_stock:
            notes.append(
                f"Demand ({units:.0f} units) is higher than stock ({new_stock:.0f}), "
                "so sales are limited by inventory."
            )
            units = new_stock

    estimated = _financials(
        new_price, units, new_cost, new_opex, new_marketing,
        new_stock, baseline.holding_cost_per_unit,
    )
    estimated["volume_factor"] = volume_factor

    difference = {
        k: estimated[k] - original[k]
        for k in original
        if original[k] is not None and estimated[k] is not None
    }

    assumptions_text = [
        f"Price elasticity = {a['elasticity']}: a 10% price rise changes units sold by about {a['elasticity'] * 10:.0f}%.",
        f"Marketing sales lift = {a['marketing_lift']}: +100% marketing gives +{a['marketing_lift'] * 100:.0f}% units sold.",
        "Marketing and expenses scale directly with their percentage change.",
        "Unit cost changes only if a cost change is entered.",
    ]
    if baseline.inventory_units is not None:
        assumptions_text.append("Units sold cannot exceed available inventory.")
        assumptions_text.append("Holding cost applies to unsold units only.")
    assumptions_text.append("Results are estimates, not guarantees.")

    return {
        "original": _round(original),
        "estimated": _round(estimated),
        "difference": _round(difference),
        "assumptions": assumptions_text,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# 4. CHECKED EXAMPLES (run: python whatif.py)
# Every expected number below was worked out by hand first.
# ---------------------------------------------------------------------------

def _website_net_profit(b, ch, a):
    """Direct copy of the website formula (js/app.js, simulate), for comparison."""
    vf = max(0, (1 + a["elasticity"] * ch["price"]) * (1 + a["marketing_lift"] * ch["marketing"]))
    u = b.units_sold * vf
    revenue = u * b.price * (1 + ch["price"])
    cogs = u * b.unit_cost * (1 + ch["cost"])
    return (revenue - cogs
            - b.marketing_budget * (1 + ch["marketing"])
            - b.operating_expenses * (1 + ch["expenses"]))


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

    # Price +10%: factor 1 + (-1.2 x 0.10) = 0.88, units 880, revenue 96800,
    # cogs 52800, holding 320, net 96800 - 52800 - 25320 = 18680
    r = calculate(base, Changes(price=0.10))
    assert r["estimated"]["units_sold"] == 880
    assert r["estimated"]["revenue"] == 96800
    assert r["estimated"]["net_profit"] == 18680

    # Unit cost +10%: cost 66, cogs 66000, net 100000 - 66000 - 25200 = 8800
    r = calculate(base, Changes(cost=0.10))
    assert r["estimated"]["net_profit"] == 8800

    # Marketing +20%: factor 1.03, units 1030, revenue 103000, cogs 61800,
    # marketing 6000, holding 170, net 103000 - 61800 - 26170 = 15030
    r = calculate(base, Changes(marketing=0.20))
    assert r["estimated"]["units_sold"] == 1030
    assert r["estimated"]["net_profit"] == 15030

    # Operating expenses +10%: opex 22000, net 100000 - 60000 - 27200 = 12800
    r = calculate(base, Changes(expenses=0.10))
    assert r["estimated"]["net_profit"] == 12800

    # Inventory -20%: stock 960, sales limited to 960, net 96000 - 57600 - 25000 = 13400
    r = calculate(base, Changes(inventory=-0.20))
    assert r["estimated"]["units_sold"] == 960
    assert r["estimated"]["net_profit"] == 13400
    assert len(r["notes"]) == 1

    # Without inventory (as on the website): price +10%, net 96800 - 52800 - 25000 = 19000
    no_stock = Baseline(price=100, units_sold=1000, unit_cost=60,
                        operating_expenses=20000, marketing_budget=5000)
    r = calculate(no_stock, Changes(price=0.10))
    assert r["estimated"]["net_profit"] == 19000

    # An inventory change without inventory data must be rejected
    try:
        calculate(no_stock, Changes(inventory=0.10))
        raise AssertionError("inventory change without stock should be rejected")
    except ValueError:
        pass

    # Passing 10 instead of 0.10 must be rejected, not silently accepted
    try:
        calculate(base, Changes(price=10))
        raise AssertionError("price=10 should have been rejected")
    except ValueError:
        pass

    # 500 random cases must match the website formula
    import random
    random.seed(1)
    for _ in range(500):
        price = random.uniform(0.5, 50)
        b = Baseline(price=price, units_sold=random.uniform(10, 10000),
                     unit_cost=random.uniform(0.1, price),
                     operating_expenses=random.uniform(0, 50000),
                     marketing_budget=random.uniform(0, 20000))
        ch = {"price": random.uniform(-0.3, 0.3), "cost": random.uniform(-0.3, 0.3),
              "marketing": random.uniform(-0.5, 1.0), "expenses": random.uniform(-0.3, 0.5)}
        got = calculate(b, Changes(**ch))["estimated"]["net_profit"]
        want = _website_net_profit(b, ch, DEFAULT_ASSUMPTIONS)
        assert abs(got - want) < 0.01, (got, want)

    print("All checks passed.")


if __name__ == "__main__":
    _run_checks()
