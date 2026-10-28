# Business data analysis - Fazeela's part

This module turns clean business data into totals, product results, monthly trends and short findings. The dashboard, assistant and recommendation module can all use its output.

It works with sales, expenses and inventory as separate datasets. It does not need an AI API key.

## Run it on the team's data

Open the terminal in the main project folder and activate your virtual environment. If you have not downloaded the cleaned data yet, run:

```powershell
git fetch origin Abdul_Samad_Task
python scripts/fetch_team_data.py
```

Then choose the file you want to analyze:

```powershell
python -m business_analysis data/team_cleaned/online_retail_cleaned.csv --output output/analysis/online_retail.json
python -m business_analysis data/team_cleaned/expenses_cleaned.csv --output output/analysis/expenses.json
python -m business_analysis data/team_cleaned/products_cleaned.csv --output output/analysis/inventory.json
```

You can run these commands one at a time. Each one saves a separate JSON results file in `output/analysis/`.

You can also provide another CSV or Excel file. The module usually identifies the file type from its columns. If needed, add `--kind sales`, `--kind expenses`, or `--kind inventory`. Add `--currency GBP` when you know the currency and it is not already identified.

## Use it in another module

This example runs on a small sales table:

```python
import pandas as pd
from business_analysis import analyze_business_data

data = pd.DataFrame([
    {
        "date": "2025-01-01",
        "product": "Example product",
        "units": 10,
        "price": 20,
        "unit_cost": 8,
        "marketing_spend": 5,
        "expenses": 15,
    }
])

result = analyze_business_data(data, dataset_id="example-sales")
print(result["totals"])
print(result["findings"])
```

Replace `data` with the cleaned DataFrame from your own module. Use the uploaded file's `dataset_id` when connecting it to the backend.

The result is a Python dictionary that can also be sent as JSON:

| Key | What it contains |
|---|---|
| `totals` | Business totals such as revenue, units and available profit figures |
| `kpis` | Labeled totals for dashboard cards |
| `trend` | Monthly results |
| `by_product` | Product results; includes all products |
| `findings` | Short explanations supported by the numbers |
| `quality` | Rows used, duplicates removed and invalid rows excluded |
| `anomalies` | Unusual values to review |
| `limitations` | Missing information and notes about interpreting the results |

Expenses also have `by_category` and `by_status`. Sales include `by_country` when country data is available.

## Columns and calculations

For a basic sales file, use `date`, `product`, `units` and `price`. The module also reads the team's UCI retail columns, including `invoice_no`, `stock_code`, `quantity`, `invoice_date` and `unit_price`. When a stock code is available, it is used to group products.

The calculations are:

- Revenue = units × selling price, added across the rows.
- Cost of goods = units × unit cost, added across the rows.
- Gross profit = revenue − cost of goods.
- Net profit = gross profit − marketing spend − other expenses.

Profit calculations need the relevant cost columns. Missing or incomplete costs return `null` in JSON, which means **unavailable**. The module does not guess costs. Zero is used only when zero is supplied in the data.

Margin and share values are percentages: `25` means 25%.

## How to read the results

Returns and adjustments stay in net revenue. Positive sales and negative transaction values are also reported separately.

Missing months are left missing. The module does not assume that the business made no sales during those months. The first or last month may cover only part of a month.

Unusual values are flagged using the 1.5 IQR rule, a way of finding values far outside the middle range. They are kept in the totals so someone can review them before deciding whether they are errors.

Expense totals include every recorded status, including pending or rejected entries. They do not mean that every amount was paid. Inventory values show what the stock costs or could sell for; they are not sales already made.

Keep the retail, expense and inventory samples separate. They do not have confirmed matching product IDs, currencies or business records.

## Results checked on the shared data

| Dataset | Rows used | Main results |
|---|---:|---|
| Online Retail | 536,641 | Net revenue GBP 9,726,006.95; positive sales GBP 10,642,110.80 |
| Expenses | 220 | Recorded expense amounts 280,096.64 across all statuses; currency unspecified |
| Inventory | 160 | 40,517 units; stock cost 9,933,254.72; possible retail value 19,552,921.45; currency unspecified |

The retail totals match Abdul Samad's daily sales summary. Retail profit is unavailable because the dataset does not include costs.

Some stock codes are postage or fees. For example, the highest net-revenue code is DOT at GBP 206,245.48. Do not automatically describe every code as a physical product.

The shared ZIP does not include cleaned Online Retail II data.

## Check this module

```powershell
python -m unittest discover -s tests -p test_business_analysis.py -v
```

These 12 tests check calculations, returns, missing costs, invalid rows, product rankings, month gaps, expense and inventory results, and unusual values.
