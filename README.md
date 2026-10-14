# DecisionAI — Main website pages

Four connected pages for the AI Decision Intelligence & What-If Simulator.

## Run it
Open `index.html` in a browser (needs internet once for Chart.js and the Excel reader, loaded from cdnjs).
Or serve the folder: `python3 -m http.server 8000` and visit http://localhost:8000.

## Pages
| Page | File | What it does |
|---|---|---|
| Dashboard | `index.html` | KPI cards, revenue/profit trend chart, revenue by product chart, product table, latest scenario, data quality |
| Upload Data | `upload.html` | CSV/Excel upload, column matching, quality checks, 10-row preview, "use this data" |
| What-If | `whatif.html` | Sliders for price, cost, marketing, expenses; elasticity assumptions; live result cards, chart, table, risks; save scenarios |
| Compare Scenarios | `compare.html` | Select saved scenarios, profit chart, side-by-side table, inputs and risks |

## Shared style and logic
- `css/style.css` — one stylesheet (colors, cards, forms, tables, buttons).
- `js/app.js` — shared script: storage, CSV/Excel parsing, cleaning, aggregation, scenario engine, formatting, navigation.
- `js/sample.js` + `data/sample_sales.csv` — built-in sample dataset (48 rows, 4 products, 12 months).

## How pages are connected
Pages share data through the browser's localStorage: the dataset chosen on Upload feeds the Dashboard and What-If; scenarios saved on What-If feed Compare and the Dashboard's latest-scenario card.

## Scenario formulas
- new units = units × (1 + elasticity × price change) × (1 + marketing lift × marketing change)
- revenue = new units × price × (1 + price change)
- COGS = new units × unit cost × (1 + cost change)
- marketing and expenses = original × (1 + their change)
- profit = revenue − COGS − marketing − expenses

Defaults: elasticity −1.2, marketing lift 0.15. Best/expected/worst cases vary these two assumptions (−0.6/0.25, −1.2/0.15, −1.8/0.05).
Results are estimates, not guaranteed outcomes.

## Checked
Calculation tests against hand-computed values pass, as do cleaning tests (duplicates, missing values, invalid numbers, bad dates, quoted commas).

## Next steps (from the full project)
Replace localStorage with FastAPI + PostgreSQL, add authentication, the LLM assistant, forecasting, and PDF/CSV export. `DIS.simulate` is the function to port to the backend.
