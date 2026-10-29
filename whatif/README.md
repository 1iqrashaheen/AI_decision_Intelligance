# What-If Calculations Module

Part of the AI Decision Intelligence & What-If Simulator project.
Owner: Arayash Noor (module 06).

## Purpose

Estimates what would happen to a business if one or more of these change:
product price, operating expenses, marketing budget, and inventory.
It shows the original figures, the estimated figures, the difference, and the
assumptions used.

## Files

| File | What it does |
|---|---|
| `whatif.py` | The calculation module. Contains `Baseline`, `Changes` and `calculate()`. |
| `dataset_loader.py` | Cleans the Online Retail II dataset and builds baseline numbers from it. |

## How to run

From the project folder, with the virtual environment active:

```
python whatif/whatif.py
```

Expected output: `All checks passed.` (four hand-checked examples).

To try it on the real dataset:

```
python whatif/dataset_loader.py prepare <path to online_retail_II.xlsx>
python whatif/dataset_loader.py demo
python whatif/dataset_loader.py demo 85123A
```

`prepare` is run once (about 2 minutes). It saves a cleaned CSV in
`whatif/local_data/`, which is not uploaded to GitHub. `demo` uses the last 12
full months, for the whole business or for one product code.

## Inputs

`Baseline` (current numbers for one period):

| Field | Meaning |
|---|---|
| `price` | Selling price per unit |
| `units_sold` | Units sold in the period |
| `unit_cost` | Cost of one unit |
| `operating_expenses` | Rent, salaries, utilities, etc. for the period |
| `marketing_budget` | Marketing spend for the period |
| `inventory_units` | Units available to sell (must be at least `units_sold`) |
| `holding_cost_per_unit` | Cost of keeping one unsold unit (optional, default 0) |

`Changes` (percentages: 10 means +10%, -5 means -5%):

| Field | Meaning |
|---|---|
| `price_pct` | Change in selling price |
| `expenses_pct` | Change in operating expenses |
| `marketing_pct` | Change in marketing budget |
| `inventory_pct` | Change in inventory available |

Optional `assumptions` dictionary: `price_elasticity` (default -1.0) and
`marketing_elasticity` (default 0.1).

## Output

`calculate(baseline, changes)` returns a dictionary with:

- `original`: figures before the change
- `estimated`: figures after the change
- `difference`: estimated minus original
- `assumptions`: list of assumptions in plain English
- `notes`: warnings, for example when sales are limited by stock

Each of `original` and `estimated` contains: `price`, `units_sold`, `revenue`,
`cost_of_goods`, `gross_profit`, `operating_expenses`, `marketing_budget`,
`holding_cost`, `total_expenses`, `net_profit`, `profit_margin_pct`,
`inventory_units`, `unsold_units`.

## Example

```python
from whatif import Baseline, Changes, calculate

baseline = Baseline(price=100, units_sold=1000, unit_cost=60,
                    operating_expenses=20000, marketing_budget=5000,
                    inventory_units=1200, holding_cost_per_unit=1)

result = calculate(baseline, Changes(price_pct=10))
print(result["original"]["net_profit"])    # 14800
print(result["estimated"]["net_profit"])   # 19700
```

## Calculation rules

- Revenue = price x units sold.
- Net profit = revenue - cost of goods - operating expenses - marketing - holding cost.
- A price change affects demand: new units = old units x (1 + price elasticity x price change).
- A marketing change affects demand with diminishing returns:
  units x (new marketing / old marketing) ^ marketing elasticity.
- Units sold cannot exceed available inventory.
- Holding cost applies to unsold units only.

## Assumptions

- Price elasticity is -1.0: a 1% price rise lowers units sold by 1%.
- Marketing elasticity is 0.1: doubling marketing raises units sold by about 7%.
- Unit cost stays the same. Expense changes do not affect sales by themselves.
- The Online Retail II dataset contains sales only. Unit cost, operating
  expenses, marketing budget, inventory and holding cost are not in the data, so
  `dataset_loader.py` fills them with default ratios of sales (unit cost 60% of
  price, operating expenses 15% of revenue, marketing 5% of revenue, stock 120%
  of units sold, holding cost 2% of unit cost). These can be replaced with values
  entered by the user.
- Results are estimates, not guarantees.

## Checked examples

Base case: price 100, 1000 units, unit cost 60, operating expenses 20000,
marketing 5000, stock 1200, holding cost 1 per unsold unit.

| Scenario | Net profit |
|---|---|
| No change | 14,800 |
| Price +10% (900 units sold) | 19,700 |
| Operating expenses +10% | 12,800 |
| Inventory -20% (sales limited to 960 units) | 13,400 |

## Requirements

Python 3.9 or newer, with `pandas` and `openpyxl` installed
(`pip install pandas openpyxl`).
