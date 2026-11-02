# What-If Calculations Module

Part of the AI Decision Intelligence & What-If Simulator project.
Owner: Arayash Noor (module 06).

## Purpose

Estimates what would happen to a business if one or more of these change:
product price, unit cost, marketing budget, other expenses, and (optionally)
inventory. It shows the original figures, the estimated figures, the
difference, and the assumptions used.

The calculation rules are the same as the website simulator
(`js/app.js`, function `simulate`), so the website and the backend give the
same numbers.

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

Expected output: `All checks passed.` This runs the hand-checked examples and
compares 500 random cases against the website formula.

To try it on the real dataset:

```
python whatif/dataset_loader.py prepare <path to online_retail_II.xlsx>
python whatif/dataset_loader.py demo
python whatif/dataset_loader.py demo 85123A
```

`prepare` is run once (about 2 minutes). It saves a cleaned CSV in
`whatif/local_data/`, which is not uploaded to GitHub. `demo` uses the last 12
full months, for the whole business or for one product code.

## Percent format

All changes are decimals: `0.10` means +10% and `-0.05` means -5%. This is the
same as the website and the backend. Values above 5 (500%) are rejected as a
likely mistake, for example passing `10` instead of `0.10`. The profit margin
in the output is also a decimal (`0.19` means 19%).

## Inputs

`Baseline` (current numbers for one period):

| Field | Meaning |
|---|---|
| `price` | Selling price per unit |
| `units_sold` | Units sold in the period |
| `unit_cost` | Cost of one unit |
| `operating_expenses` | Rent, salaries, utilities, etc. (website name: `expenses`) |
| `marketing_budget` | Marketing spend (website name: `marketing_spend`) |
| `inventory_units` | Units available to sell. Optional. Leave empty to match the website exactly. |
| `holding_cost_per_unit` | Cost of keeping one unsold unit. Optional, default 0. Used only with `inventory_units`. |

`Changes` (decimals, all optional, default 0):

| Field | Meaning |
|---|---|
| `price` | Change in selling price |
| `cost` | Change in unit cost |
| `marketing` | Change in marketing budget |
| `expenses` | Change in operating expenses |
| `inventory` | Change in inventory available. Needs `inventory_units`. |

The names `price`, `cost`, `marketing` and `expenses` are the same as the
website's slider names.

Optional `assumptions` dictionary: `elasticity` (default -1.2) and
`marketing_lift` (default 0.15). These are the website defaults.

## Output

`calculate(baseline, changes)` returns a dictionary with:

- `original`: figures before the change
- `estimated`: figures after the change
- `difference`: estimated minus original
- `assumptions`: list of assumptions in plain English
- `notes`: warnings, for example when sales are limited by stock

Each of `original` and `estimated` contains: `price`, `unit_cost`,
`units_sold`, `revenue`, `cost_of_goods`, `gross_profit`, `operating_expenses`,
`marketing_budget`, `holding_cost`, `total_expenses`, `net_profit`,
`profit_margin`, `inventory_units`, `unsold_units`, `volume_factor`.

Names compared with the website's `simulate` result: `units_sold` = `units`,
`cost_of_goods` = `cogs`, `marketing_budget` = `marketing`,
`operating_expenses` = `expenses`, `total_expenses` = `totalCosts`,
`net_profit` = `profit`, `profit_margin` = `margin`,
`volume_factor` = `volumeFactor`.

## Example

```python
from whatif import Baseline, Changes, calculate

baseline = Baseline(price=100, units_sold=1000, unit_cost=60,
                    operating_expenses=20000, marketing_budget=5000,
                    inventory_units=1200, holding_cost_per_unit=1)

result = calculate(baseline, Changes(price=0.10))
print(result["original"]["net_profit"])    # 14800
print(result["estimated"]["net_profit"])   # 18680
```

## Calculation rules

```
volume factor = max(0, (1 + elasticity x price change) x (1 + marketing_lift x marketing change))
units         = units sold x volume factor
revenue       = units x price x (1 + price change)
cost of goods = units x unit cost x (1 + cost change)
marketing     = marketing budget x (1 + marketing change)
expenses      = operating expenses x (1 + expenses change)
net profit    = revenue - cost of goods - marketing - expenses
```

Extra, only when `inventory_units` is given: units sold cannot exceed available
inventory, and unsold units carry a holding cost, which is included in expenses.

## Assumptions

- Price elasticity is -1.2: a 10% price rise lowers units sold by about 12%.
- Marketing sales lift is 0.15: +100% marketing raises units sold by 15%.
- Marketing and expenses scale directly with their percentage change.
- Unit cost changes only if a cost change is entered.
- The Online Retail II dataset contains sales only. Unit cost, operating
  expenses and marketing budget are not in the data, so `dataset_loader.py`
  fills them with default ratios (unit cost 60% of price, operating expenses
  15% of revenue, marketing 5% of revenue). Inventory is left empty. These can
  be replaced with values entered by the user.
- Results are estimates, not guarantees.

## Checked examples

Base case: price 100, 1000 units, unit cost 60, operating expenses 20000,
marketing 5000, stock 1200, holding cost 1 per unsold unit.

| Scenario | Net profit |
|---|---|
| No change | 14,800 |
| Price +10% (880 units sold) | 18,680 |
| Unit cost +10% | 8,800 |
| Marketing +20% (1,030 units sold) | 15,030 |
| Operating expenses +10% | 12,800 |
| Inventory -20% (sales limited to 960 units) | 13,400 |

Without inventory data (as on the website), price +10% gives a net profit of
19,000.

## Requirements

Python 3.9 or newer, with `pandas` and `openpyxl` installed
(`pip install pandas openpyxl`).
