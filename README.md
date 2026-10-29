# AI Decision Intelligence & What-If Simulator

DecisionAI helps users understand business data, explore possible changes, and ask questions about the results. It combines a browser dashboard with a Python API for analysis, forecasting, simulations, business questions, and PDF/CSV reports.

This is the complete project guide. Run commands from the repository root: the folder containing `main.py`, `requirements.txt`, and this README.

## Project status

The working branch is **`integration-branch`**, not `integration`. Vercel production tracks **`main`**. Deployment fixes and documentation are being validated on the integration branch before the production merge.

The FastAPI preview has been deployed under GitHub **`1iqrashaheen`** in Iqra's Vercel account. Preview health, sample upload, analysis, scenario chat, and sample download have been checked. Local checks cover the remaining API routes and reports. There are still unfinished integrations:

- Uploaded datasets live in Python process memory. They disappear on restart and cannot be shared between Vercel workers. Shared storage is required for a reliable deployment.
- Database/login code exists on `Saud_Masood_Task`, but is not connected to this FastAPI application.
- Groq-powered answers require a server-side key. Without it, supported questions use a clearly labeled local answer method.
- The production merge and deployment remain pending until storage can be configured and verified.

## Contents

- [Features](#features)
- [Team and modules](#team-and-modules)
- [Architecture and technology](#architecture-and-technology)
- [Project structure](#project-structure)
- [Installation and local setup](#installation-and-local-setup)
- [Environment variables](#environment-variables)
- [Authentication and login prompts](#authentication-and-login-prompts)
- [Using the application](#using-the-application)
- [Business data analysis](#business-data-analysis)
- [Iqra's Assistant](#iqras-assistant)
- [Scenario comparison and reports](#scenario-comparison-and-reports)
- [API reference](#api-reference)
- [Datasets and preprocessing](#datasets-and-preprocessing)
- [Forecasting](#forecasting)
- [Standalone What-If module](#standalone-what-if-module)
- [Database and external services](#database-and-external-services)
- [Tests and API health](#tests-and-api-health)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Source history and attribution](#source-history-and-attribution)

## Features

The project aims to explain business figures, compare decisions using stated assumptions, and keep actual results separate from estimates.

| Feature | What is implemented |
|---|---|
| Dashboard | Revenue, units, available costs/profit, product results, monthly charts, and quality information. |
| Upload | CSV, XLSX, and XLS input, column matching, duplicate/invalid-row checks, and a preview. The assistant/API reads the first Excel worksheet. |
| Analysis | Separate sales, expense, and inventory results, findings, unusual-value checks, and missing-data notes. |
| What-If | Changes to price, unit cost, marketing, and expenses; best/expected/worst cases; saved scenarios tied to their source dataset. |
| Iqra's Assistant | Questions answered from calculated facts, with evidence fields and a labeled AI or local source. |
| Forecasting | Monthly trend estimates for suitable uploads and historical daily forecasts for a matching source dataset. |
| Comparison and reports | Original results beside selected scenarios, server-recalculated PDF/CSV exports, assumptions, and risks. |

## Team and modules

The project owner confirmed on **29 October 2026** that Iqra owns modules **01, 05, and 09**. The remaining assignments come from the existing source documents and branches. Historical attribution is preserved below and in Git.

| Team member | Module | Responsibilities and current status |
|---|---|---|
| **Iqra Shaheen** | **01 — AI Business Assistant; 05 — Business Data Analysis; 09 — Scenario Comparison & Reports** | Owns the integrated assistant, sales/expense/inventory analysis, dataset-linked comparisons, and PDF/CSV reporting. Implemented in `assistant/`, `business_analysis/`, `js/assistant.js`, `js/comparison.js`, `js/compare.js`, and `backend/app/services/reports.py`. |
| **Muhammad Waleed Ansari** | **02 — Website Frontend** | Dashboard, upload and What-If pages, shared styling, browser data handling, charts, and the original comparison page. The integrated comparison/report work is now maintained under module 09. |
| **Abdul Samad** | **03 — Dataset Sourcing, Preprocessing & Data Cleaning** | Source datasets, preprocessing notebook, and cleaned retail, expense, inventory, and daily-sales files. The published bundle is fetched separately. |
| **Ahsan Rafique** | **04 — Sales Forecasting & Business Recommendations** | Random Forest pipeline, saved forecasts, evaluation metrics, and recommendations. The forecast integration checks uploads against the original daily series. |
| **Arayash Noor** | **06 — What-If Calculations** | Separate inventory-aware calculations in `whatif/`, including demand and holding costs. Its inputs/assumptions differ from the current web/API simulator. |
| **Muhammad Arham** | **07 — Backend Connections** | FastAPI routes, schemas, API client, upload integration, basic monthly forecast, and simulation/chat/report connections. |
| **Saud Masood** | **08 — Database & Authentication** | Separate Express/Prisma/PostgreSQL service for users, file metadata, analysis history, and scenarios. Reviewed on `Saud_Masood_Task`; not connected to FastAPI here. |

### Historical attribution

Earlier documents listed **Fazeela Manzoor** for module 05, Business Data Analysis, and **Ayesha Hussain** for module 09, Scenario Comparison & Reports. These responsibilities are now assigned to Iqra. This documentation update does not change original authors, commits, or contributor history. No complete original assignment brief beyond the existing source documents and branches was available; additional members or responsibilities have not been invented.

## Architecture and technology

The frontend uses HTML, CSS, and plain JavaScript. Chart.js supplies charts, and the browser XLSX library reads spreadsheets. These libraries load from a CDN and need internet access.

The dashboard, upload, What-If, and comparison pages share their current data and saved scenarios through browser `localStorage` and perform browser-side calculations. Assistant analysis/chat and report downloads call FastAPI through `js/api.js`. The assistant remembers its selected backend dataset in `sessionStorage`.

`main.py` serves the website, public CSS/JavaScript, sample CSV, and API on one origin. API uploads pass through cleaning into the temporary dataset store, then analysis, forecasting, chat, or reporting. Reports recalculate scenarios from inputs rather than trusting saved browser totals.

| Layer | Technology |
|---|---|
| API | Python 3.12 deployment target, FastAPI, Pydantic, Uvicorn, python-multipart |
| Data and Excel | pandas, NumPy, openpyxl, xlrd |
| Assistant | Groq SDK, optional model selection, local fact-based router, python-dotenv |
| Reports | ReportLab and Python CSV output |
| Optional training | scikit-learn and Matplotlib |
| Checks | pytest, httpx, pypdf, Node.js built-in test runner |
| Hosting | Vercel Python/FastAPI; shared dataset storage still pending |

The optional Express/Prisma/PostgreSQL service is separate team work, not a dependency of the current local app.

## Project structure

```text
AI_decision_Intelligance/
  README.md                    Complete project guide
  main.py                      Website and API entrypoint
  pyproject.toml               Runtime, dependencies, Vercel entrypoint
  requirements.txt             Local dependencies
  vercel.json                  FastAPI framework configuration
  .env.example                 Local configuration template
  index.html                   Dashboard
  upload.html                  Upload and preview
  whatif.html                  Web simulator
  compare.html                 Comparison and downloads
  assistant.html               Assistant interface
  css/                         Page styles
  js/                          Page logic, API client, sample data
  assistant/                   Evidence preparation and question answering
  business_analysis/           Cleaning, analysis, CLI
  backend/
    app/core/                  Settings, errors, temporary storage
    app/routers/               Upload, analysis, simulation, chat, export
    app/schemas/               Request and response models
    app/services/              Analytics, simulation, PDF/CSV generation
    data/online_retail_sample.csv
    tests/                     API tests
  forecasting/
    src/                       Optional training pipeline
    outputs/                   Original shared forecast and evaluation files
    training_manifest.json     Source-data fingerprint and forecast dates
    integration.py             Saved-forecast matching
  whatif/                      Standalone calculator and dataset loader
  team_sources/datasets/       Preprocessing notebook
  scripts/fetch_team_data.py    Extracts the published cleaned CSV bundle
  data/sample_sales.csv        Tracked public example
  docs/VALIDATION.md            Historical and current validation evidence
  tests/                       Analysis, assistant, report, deployment, JS checks
```

Downloaded team files go in `data/team_cleaned/`. New analysis/training results go in `output/`. These directories are ignored by Git, apart from the already tracked public sample. Reporting code lives in `backend/app/services/reports.py`; the former `reports/` folder held only its consolidated README.

## Installation and local setup

Install **Git** and **Python 3.12**. Node.js is optional, for JavaScript checks. No Groq key or database is needed for the local sample workflow.

```powershell
git clone https://github.com/1iqrashaheen/AI_decision_Intelligance.git
cd AI_decision_Intelligance
git switch integration-branch
```

If you already have a checkout, open it instead of cloning again. Confirm the branch with `git status --short --branch` and preserve local work.

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux or macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For the remaining commands, `python` means the environment's Python. On Windows, activate with `.\.venv\Scripts\Activate.ps1`, or use `.\.venv\Scripts\python.exe` directly if activation is blocked. Check `python --version`; an existing environment on another version is not the declared Vercel runtime.

Start both frontend and backend from the repository root:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Keep the terminal open. Visit the [dashboard](http://127.0.0.1:8001/), [assistant](http://127.0.0.1:8001/assistant.html), [interactive API documentation](http://127.0.0.1:8001/docs), or [health endpoint](http://127.0.0.1:8001/api/health). Stop with Ctrl+C.

Opening HTML directly is not enough for assistant requests or reports. Local static previews call `http://localhost:8001/api`; the combined server and deployed site use their own origin.

## Environment variables

The application loads **the root `.env`**. If it does not exist, create it with `Copy-Item .env.example .env` in PowerShell, or `cp .env.example .env` on Linux/macOS. Edit existing configuration instead of overwriting it. Never commit keys, tokens, passwords, `.env`, or user-uploaded data.

| Variable | Default / placeholder | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Unset; `your_api_key_here` is only a placeholder | Optional server-side key. Remove the placeholder or leave unset for local answers. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model requested by the current integration; availability depends on the configured Groq account. |
| `ASSISTANT_MODE` | `auto` | `auto`: try configured Groq and label fallback; `off`: no model calls; `required`: error if the AI service cannot answer. |
| `MAX_UPLOAD_MB` | `10` | Application upload limit in MiB; hosting limits still apply. |
| `CORS_ORIGINS` | `http://localhost:8000,http://127.0.0.1:5500,http://localhost:3000` | Comma-separated allowed origins for a separately served frontend. Same-origin deployment needs no override. |

Example with placeholders only:

```dotenv
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
ASSISTANT_MODE=auto
MAX_UPLOAD_MB=10
```

Use the root `.env.example` for this application. `backend/.env.example` is only a settings reference; `main.py` does not load `backend/.env`. FastAPI does **not** use `DATABASE_URL` or `JWT_SECRET` to store datasets or authenticate users. Adding those variables alone does not connect a database. The separate service's settings are explained under [Database and external services](#database-and-external-services).

## Authentication and login prompts

**The current local FastAPI backend does not ask you to log in. You do not need Arham's account or password.** Start it from the root with the Uvicorn command above and visit `http://127.0.0.1:8001/docs` or `/api/health`. Both respond without credentials. There are no `/api/auth/register`, `/api/auth/login`, or `/api/auth/me` routes in this integration; those paths return 404.

The health response's `"author": "Muhammad Arham"` and the frontend badge's author tooltip credit the original backend contributor. They do not identify a signed-in user or require that person's credentials.

If another screen asks for an account, check its address and the command that opened it:

| Prompt | What it means and what to do |
|---|---|
| A `vercel.com` sign-in or preview SSO screen | Hosting/deployment access, not application login. Use Iqra's Vercel account (`iqrashaheen271@gmail.com`) linked with `1iqrashaheen`. Ask the Vercel project owner for access if your account is refused. |
| Git Credential Manager or a GitHub sign-in during `git push` | Repository access, not the running backend. Select `1iqrashaheen`; do not select another saved account. |
| A PostgreSQL or pgAdmin login | Database administration, not FastAPI login. It uses the database role/password set by the database owner. A running PostgreSQL service does not connect it to this project. |
| A login form on a separate teammate-hosted URL | Its access rules cannot be inferred from this local code. Confirm the exact URL and service with its owner before using any credentials. |

For this review, neither root `.env` nor `backend/.env` existed, and the terminal environment had no database, JWT, or Groq key configured. No personal credentials were printed or requested. The reported different-user prompt has not been identified because its URL/message has not yet been supplied.

### Creating your own application account later

Saud's separate branch implements registration and login. Once that service is repaired, configured, and connected, its intended flow is:

1. Send `POST /api/auth/register` with your own `name`, `email`, and `password`. Names must be 2–80 characters and passwords 8–128 characters. Email is normalized to lowercase; an existing email returns 409.
2. Registration hashes the password with bcrypt and returns user details plus a JWT. `POST /api/auth/login` accepts your own email/password and issues another token valid for two hours.
3. Send `Authorization: Bearer <token>` for `/api/auth/me`, files, analysis history, and saved scenarios. Invalid/expired tokens return 401. Do not publish or commit the token.

There is no Arham-only account restriction in that source. You should create your own account once the service is available; registration is not currently available on the FastAPI/Vercel application. There is also no integrated registration/login page, password-reset flow, or deployed database proof. Do not use the Vercel/GitHub password as an API credential.

If you are trying to use an API hosted by Arham, ask him for its exact base URL, current source branch/commit, health/docs URLs, and whether the prompt is Vercel protection or app authentication. Ask for an invitation for your own account or a documented registration URL, not his personal password. Database implementation belongs to Saud, as described below.

## Using the application

1. Load the built-in sample on the dashboard, or choose your file on **Upload Data**.
2. Review totals, products, monthly trends, and quality notes.
3. Open **What-If**, change inputs, enter a scenario name, and save it. **Save best / expected / worst** saves all three cases.
4. Open **Compare Scenarios**, choose matching scenarios, and download a report.
5. Open **AI Assistant** and choose **Use dashboard data**, or upload the original file directly. Choose a saved scenario under **Question context** when needed.

The built-in sample has 48 rows and four products: revenue **191,080.00**, net profit **61,560.00**, currency unspecified. Price +10% gives the API expected-case estimates of revenue **184,965.44** and profit **66,722.92**. These are sample checks, not figures to assume for another file.

Keep sales, expense, and inventory files separate; their business identifiers/currencies are not confirmed to match. Resave older scenarios without dataset links. When the dashboard has filled missing expenses with zero, the assistant treats those imported costs as unknown; upload the original file directly for clearer missing-data information.

## Business data analysis

Iqra's module supports these normalized columns and results:

| Kind | Required columns | Results |
|---|---|---|
| Sales | `date`, `product`, `units`, `price` | Revenue, units, available gross/net profit and margins, monthly/product results, invoice/country results when provided. |
| Expenses | `date`, `amount`, `category` | Recorded requests by category/status. Pending/rejected requests are not described as cash paid. |
| Inventory | `product`, `price`, `unit_cost`, `stock` | Units, stock cost, potential retail value/margins, out-of-stock records. These are not realized sales/profit. |

Common aliases such as `InvoiceNo`, `StockCode`, `Quantity`, `InvoiceDate`, and `UnitPrice` are normalized. Stock codes identify products when present. Profit needs complete actual `unit_cost`, `marketing_spend`, and `expenses`; missing metrics remain unavailable (`null`).

Revenue sums units × price. Cost of goods sums units × unit cost. Gross profit subtracts cost of goods; net profit also subtracts marketing/expenses. Returns stay in net revenue, with positive sales and negative transaction values reported separately. Duplicate/invalid rows are counted; missing months remain missing. The 1.5 IQR rule flags unusual values without silently removing them. Margin/share values are percentages: `25` means 25%.

Results include `dataset_id`, `dataset_kind`, `currency`, `totals`, `kpis`, `trend`, `by_product`, `findings`, `quality`, `anomalies`, `limitations`, and relevant country/category/status tables. All products are available to analysis/chat, even if the page displays only a few rows.

Analyze a file without the website:

```powershell
python -m business_analysis data/sample_sales.csv --output output/analysis/sample_sales.json
```

Replace the CSV with your CSV/Excel path. Optional flags are `--kind sales|expenses|inventory` and `--currency GBP`; kind is detected by default. After fetching the team data, use `data/team_cleaned/online_retail_cleaned.csv`, `expenses_cleaned.csv`, or `products_cleaned.csv` as separate inputs.

Other Python modules can call `analyze_business_data(dataframe, dataset_id="your-id")` from `business_analysis`. Reuse that dataset ID when connecting results.

## Iqra's Assistant

The assistant exists in `assistant/`, with its interface in `assistant.html`. It answers from the selected file's analysis, available forecast, and calculated scenario. Each question is handled independently; name the product or month again in follow-up questions.

Try **What is our total revenue?**, **Which product has the lowest profit margin?**, **What was revenue in 2025-03?**, **What unusual values should I review?**, or **What if prices increase by 10%?** Other supported topics include units, invoice counts, countries, trends, recommendations from findings, expenses, inventory, and forecasts. Unsupported/missing facts are identified as unavailable.

Chat can calculate one percentage change at a time. Use the What-If page for multiple changes. Saved-scenario questions require the same dataset and matching baseline figures; the backend recalculates the scenario.

Python computes the amounts first. Groq selects prepared evidence IDs; the app validates the selection before displaying calculated facts. Responses contain `answer`, `context_used`, `source` (`groq_grounded` or `grounded_assistant`), and `warnings`. The model receives the question and summary evidence, not the raw uploaded table. Current advice uses analysis findings; supplied recommendation text is reserved for a future connection.

Run the offline example, or an interactive session:

```powershell
python -m assistant.test_assistant
python -m assistant.ai_assistant --file data/sample_sales.csv --offline
```

Type `exit` to finish. Omit `--offline` to use configured AI settings. Python callers use `prepare_business_data(analysis=..., simulation=..., forecasting=...)` from `assistant.data_connection`, then `answer_question(question, context, mode="off")` from `assistant.ai_assistant`. Extra results must carry the same dataset ID. `ask_assistant()` returns only answer text.

## Scenario comparison and reports

Iqra's module compares scenarios for the current dataset. Select up to 12, enter a report title, and download PDF or CSV. **Clear selection** produces an original-results-only report.

Exports include the file name/period/currency, actual totals beside estimates, product/expense/monthly results, findings, quality notes, assumptions, risks, and an optional available forecast. The backend recalculates scenario inputs with the existing simulator. Empty requests return an error. The older supplied-figures format remains supported, with an explicit unverified-figures label.

PDF detail tables show up to 10 products/categories and 12 months; scenario tables are grouped by three. CSV contains full product/category/monthly results. PDF text and CSV formula prefixes are escaped. Percentage change from a zero baseline is unavailable. The comparison page can re-upload its browser dataset for a download after a local backend restart; this does not solve cross-worker storage.

Main files: `compare.html`, `js/compare.js`, `js/comparison.js`, `backend/app/services/reports.py`, and `backend/app/routers/export.py`. No separate runtime module is missing when the former `reports/README.md` is removed.

## API reference

Use `/api` on the application origin, or `http://127.0.0.1:8001/api` locally. The running `/docs` page and [schemas](backend/app/schemas/common.py) define all fields.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Process health/version, not database or Groq availability. |
| POST | `/api/upload` | Multipart field `file`; returns dataset ID, filename, quality, preview. |
| GET | `/api/analysis/{dataset_id}` | Calculated results for an uploaded file. |
| POST | `/api/forecast` | `dataset_id`, optional `periods` (1–24, default 3). |
| GET | `/api/simulate/baseline/{dataset_id}` | Starting sales figures; needs positive net units and complete costs. |
| POST | `/api/simulate` | Scenario from `baseline`, `changes`, optional `assumptions`. |
| POST | `/api/simulate/compare` | Best, expected, and worst cases. |
| POST | `/api/chat` | `dataset_id`, `question`, optional matching scenario and context ID. |
| POST | `/api/export?format=pdf` | PDF for a selected dataset/scenarios or labeled supplied figures. |
| POST | `/api/export?format=csv` | Same report as CSV. |

Upload first and reuse its ID. IDs remain temporary until shared storage is connected. Requests use JSON except multipart upload; exports return `application/pdf` or `text/csv`.

Example simulation body (demo inputs):

```json
{
  "baseline": {"units": 1000, "price": 100, "unit_cost": 60, "marketing": 5000, "expenses": 10000},
  "changes": {"price_pct": 0.10},
  "assumptions": {"elasticity": -1.2, "marketing_lift": 0.15}
}
```

API changes are fractions: `0.10` means +10%. Fields are `price_pct`, `cost_pct`, `marketing_pct`, and `expenses_pct`, from -1 to 5. Demand uses units × (1 + elasticity × price change) × (1 + marketing lift × marketing change), clamped to nonnegative demand. Changed prices/costs, marketing, and expenses then determine profit. Results contain `original`, `scenario`, `delta`, `assumptions`, and `notes`.

Example export body after upload:

```json
{
  "dataset_id": "replace-with-uploaded-dataset-id",
  "title": "Price change comparison",
  "include_forecast": false,
  "scenarios": [
    {"name": "Price +10%", "case": "expected", "changes": {"price_pct": 0.10},
     "assumptions": {"elasticity": -1.2, "marketing_lift": 0.15}}
  ]
}
```

Use `"scenarios": []` for a baseline-only export. Chat sends `{"dataset_id":"replace-with-uploaded-dataset-id","question":"What is our revenue?","scenario":null}`. Selected scenarios also require a matching `scenario_dataset_id` and consistent original financial figures.

Handled errors use `{"error":{"code":"...","message":"..."}}`, with optional validation details. Common statuses: 400 unsupported upload type, 404 missing dataset, 413 application size limit, 422 invalid/insufficient inputs, and 503 failed required AI selection. Unmatched routes and platform errors can use another format.

## Datasets and preprocessing

Abdul Samad's [preprocessing notebook](team_sources/datasets/preprocessing.ipynb) covers loading, column names/types, missing/duplicate values, dataset-specific cleaning, derived fields, and daily retail summaries. Use Jupyter or Google Colab to reproduce it and review its actual outputs.

Original sources: [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), [HowToCSV expenses](https://howtocsv.com/sample-expenses-csv/), [HowToCSV products/inventory](https://howtocsv.com/sample-products-csv/), and [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii). Keep source attribution and check applicable licenses before redistribution.

Fetch the published cleaned bundle without rerunning preprocessing:

```powershell
git fetch origin Abdul_Samad_Task
python scripts/fetch_team_data.py
```

The script reads a pinned Git object and writes CSVs to `data/team_cleaned/`. The actual bundle contains retail, expenses, products/inventory, and daily sales. **Cleaned Online Retail II is absent**, although the old notes listed it as expected. Supply that Excel file separately for its standalone demo.

Historical full-data checks recorded:

| Dataset | Rows analyzed | Result |
|---|---:|---|
| Online Retail | 536,641 | Net revenue GBP 9,726,006.95; positive sales GBP 10,642,110.80. Profit unavailable without costs. |
| Expenses | 220 | Recorded amounts 280,096.64 across all statuses; currency unspecified. |
| Inventory | 160 | 40,517 units; stock cost 9,933,254.72; potential retail value 19,552,921.45; currency unspecified. |

Retail totals matched the published daily summary. Some codes represent fees/postage: DOT's GBP 206,245.48 net revenue must not automatically be called sales of a physical product. These are previous validation results, not a fresh full-data run for this documentation update. Do not combine unrelated datasets to invent profit.

The full retail CSV is roughly 65 MB. Prefer CLI analysis for large files. A local server can use a larger `MAX_UPLOAD_MB` set before starting Uvicorn, but that does not override Vercel's request limit.

## Forecasting

The backend's `linear_trend` method needs at least three consecutive observed sales months. Missing months are not filled with zero sales. Partial months and seasonality can distort estimates.

Ahsan's saved Random Forest forecast covers **10 December 2011–8 January 2012**. Chat/reports reuse it only when daily history matches `forecasting/training_manifest.json`; it is not a forecast for the current month.

The original pipeline uses chronological testing, a seven-day moving-average benchmark, 12 lag/rolling/calendar features, and `RandomForestRegressor(n_estimators=150, max_depth=7, min_samples_split=4, random_state=42)`. [Saved evaluation results](forecasting/outputs/model_evaluation_metrics.json) are:

| Metric | Moving-average baseline | Random Forest |
|---|---:|---:|
| MAE (GBP) | 20,857.05 | 11,029.04 |
| RMSE (GBP) | 26,637.56 | 17,439.71 |
| R² | Not recorded | 0.549 |

The saved MAE reduction is 47.12%, with testing on 10 November–9 December 2011. These are imported metrics, not retraining results from this integration. Forecast assumptions include zero Saturday sales and nonnegative future revenue. The [original recommendations](forecasting/outputs/business_recommendations.md) remain a historical output, not advice automatically applied to other uploads.

Optional retraining, after fetching team data:

```powershell
python -m pip install -r forecasting/requirements.txt
python forecasting/src/forecasting_pipeline.py
```

Input is `data/team_cleaned/online_retail_daily_sales.csv`; new outputs/plots go to `output/forecasting/`, preserving `forecasting/outputs/`. The notebook and `generate_notebook.py` mentioned by the old forecasting README are not in this checkout and are not setup requirements.

## Standalone What-If module

Arayash's inventory-aware calculator is separate from the web/API simulator. Run its four checked examples:

```powershell
python whatif/whatif.py
```

Expected final output: `All checks passed.` From the repository root, Python callers import `Baseline`, `Changes`, and `calculate` from `whatif.whatif`.

Baseline fields are `price`, `units_sold`, `unit_cost`, `operating_expenses`, `marketing_budget`, `inventory_units`, and optional `holding_cost_per_unit`. Changes use **whole percentages** (`10` means +10%): `price_pct`, `expenses_pct`, `marketing_pct`, `inventory_pct`. Defaults are price elasticity -1.0 and marketing elasticity 0.1. Marketing uses diminishing returns, sales cannot exceed stock, and holding costs apply to unsold units. Outputs are `original`, `estimated`, `difference`, `assumptions`, and `notes`.

For the example baseline (price 100, units 1,000, unit cost 60, expenses 20,000, marketing 5,000, stock 1,200, holding cost 1), net profit is 14,800 unchanged, 19,700 for price +10%, 12,800 for expenses +10%, and 13,400 for inventory -20%.

With a separately supplied Online Retail II file:

```powershell
python whatif/dataset_loader.py prepare "C:\path\to\online_retail_II.xlsx"
python whatif/dataset_loader.py demo
python whatif/dataset_loader.py demo 85123A
```

The loader writes `whatif/local_data/retail_clean.csv` and uses the last 12 full months, optionally for one product. That generated directory is **not currently ignored by `.gitignore`**; keep it out of commits. It removes cancellations/non-product adjustments and assumes cost 60% of price, expenses 15% of revenue, marketing 5%, stock 120% of units, and holding cost 2% of unit cost unless overridden. These are demo assumptions. Integrated analysis instead keeps returns and missing costs. Do not mix the percentage conventions or claim both calculators use identical logic.

## Database and external services

### What is connected now

**No database is connected to the current backend.** `backend/app/core/store.py` stores pandas DataFrames and metadata in two Python dictionaries. The Python requirements contain no PostgreSQL client/ORM, the app has no database queries or migrations, and there is no call to Saud's service. Browser `localStorage`/`sessionStorage` do not provide shared server storage or user isolation.

A local `postgresql-x64-18` Windows service was running during the review, but the app had no `DATABASE_URL`. This proves PostgreSQL is installed/running, not that the project database, tables, roles, or connection work. No connection was attempted using guessed credentials.

### What Saud's module implements

The database contribution uses **PostgreSQL**, **Prisma 6**, **Express**, bcrypt, and JWT on `Saud_Masood_Task` at `667e156`. These files are not imported into the integration branch.

| Files / area | Implemented in the separate source | Missing or unverified |
|---|---|---|
| `schema.prisma` | `User`, `UploadedFile`, `AnalysisHistory`, `Scenario`; ownership relations and indexes. | No committed migration directory or proof that these tables exist in a configured database. |
| `prisma.js` | Creates a Prisma client. | No verified connection, generated-client setup, or environment for the integrated app. |
| `auth.routes.js`, `auth.js` | Register/login/me, hashed passwords, two-hour JWTs, Bearer-token middleware. | Not running here or connected to a frontend login flow. |
| `files.routes.js` | Create/list/detail for user-owned file metadata. | It explicitly does not store CSV/Excel bytes or parsed dataset rows; metadata alone cannot restore a DataFrame. No update/delete routes in this file. |
| `analyses.routes.js` | Create/list/detail/delete for user-owned saved results; checks file ownership. | No update route; FastAPI does not call these queries. |
| `scenarios.routes.js` | Create/list/detail/update/delete with user ownership filters. | Not connected to browser scenarios or FastAPI; the dataset-ID/ownership contract still needs agreement. |
| `server.js` | Protected route mounting; `/api/health` runs `SELECT 1`. | Startup/import paths are broken; no published service URL or test results. |

Absent CRUD methods are listed accurately; they should be added only if required by the agreed feature scope, not invented as part of documentation work.

### Confirmed blockers and configuration

`package.json` starts `src/server.js`, but that file does not exist. Published files are flat at the root, while `server.js` expects `./config/prisma`, `./middleware/auth`, and `./routes/...`. Route files expect `../config/prisma` and `../utils/asyncHandler`. A source-tree check found **15 unresolved relative imports**. Fixing only the start command would not fix the service.

The root `schema.prisma` location itself is valid: [Prisma 6 checks both root and `prisma/` schema locations](https://www.prisma.io/docs/orm/v6/prisma-schema/overview/location). The earlier README suggestion that its root location necessarily needed repair was incorrect. Migration generation/application and a successful database query remain unverified. There are no committed database-module tests or migration files in the reviewed branch.

After Saud repairs the service, its owner needs to supply/configure the following privately in that service's environment:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Authorized PostgreSQL connection string for the intended database/role; use the provider's TLS/connection settings. |
| `JWT_SECRET` | Random server-side signing secret, at least 32 characters; not a user password or frontend setting. |
| `CLIENT_ORIGIN` | Comma-separated frontend origins allowed by the Express service. This is distinct from FastAPI's `CORS_ORIGINS`. |
| `PORT` | Service port; defaults to 4000. |
| `NODE_ENV` | Optional Prisma logging mode. |

Example placeholders for **the repaired Node service only**, not the current FastAPI `.env`:

```dotenv
DATABASE_URL=postgresql://app_user:replace_me@db-host:5432/decision_ai
JWT_SECRET=replace_with_a_random_secret_at_least_32_characters
CLIENT_ORIGIN=http://127.0.0.1:8001
PORT=4000
```

Do not use these placeholders as real credentials. Before claiming a connection, verify a migrated database and the Node health response `{"status":"ok","database":"connected"}`. FastAPI's `{"status":"ok",...}` does not perform that database check.

Saud should provide working installation, client-generation, and migration instructions for his repaired layout, including production migration handling. The currently published `npm start` cannot work, so this guide does not present it as a working setup step. A host/connection string and an authorized database role are still needed; no personal database password from Arham is necessary to run FastAPI locally.

Before production, agree whether FastAPI will access shared storage directly or through Saud's service. Persist **actual uploaded content/rows and cleaning metadata**, not only file names or result summaries. Replace/connect `backend/app/core/store.py` and the analysis, baseline, chat, and reporting consumers. Define user ownership, dataset IDs, and token handling before enabling protected routes. Verify the same uploaded dataset can be read by different workers and after restart. A separately hosted memory-only process still loses data; local SQLite or Vercel temporary files are not shared persistence.

### Ready-to-send message for Saud

> Hi Saud, I reviewed Module 08 on `Saud_Masood_Task` (`667e156`). PostgreSQL/Prisma models, register/login/me, JWT middleware, and several user-scoped file/history/scenario routes are present, but the module is not connected to our FastAPI integration.
>
> Please publish an integration-ready commit that fixes `package.json` pointing to missing `src/server.js` and the 15 relative imports expecting `config/`, `middleware/`, `routes/`, and `utils/` folders while files are flat. Root `schema.prisma` is a valid Prisma 6 location; please include the actual migrations and verified generate/migrate/start instructions, a safe environment template, and a database-backed health check.
>
> `files.routes.js` currently saves metadata only. Please complete or agree a durable store for the actual uploaded CSV/Excel content or parsed rows plus cleaning metadata, and define its dataset-ID/user-ownership interface with Arham so FastAPI's `backend/app/core/store.py`, analysis, baseline, chat, and reports can retrieve the same dataset across workers/restarts. Wire or document the connection rather than leaving two separate backends.
>
> Please verify registration with my own account, login/me, expired/missing-token rejection, cross-user access rejection, the agreed file/history/scenario operations, and persistence after restart/from another worker. Send the verified commit, service/health URLs, environment variable names, and setup/test results. Configure any connection string or signing secret privately; do not send personal passwords or commit secrets. Let us know which remaining CRUD actions are actually in scope. We will merge into `main` after these checks pass.

Groq is the assistant's optional external service. Configure its key on the server and confirm a `groq_grounded` response if model access is required. Automated offline/mocked tests do not establish live service availability.

## Tests and API health

With the environment active, run from the root:

```powershell
python -m pytest -q
node --test tests/js/api.test.js tests/js/comparison.test.js
python whatif/whatif.py
python -m assistant.test_assistant
```

The latest application checks passed **85 Python tests and 11 JavaScript tests**. They cover calculations, returns/missing costs, dataset matching, routes/errors, evidence selection, exports, origin selection, public pages, and private-file protection. An upstream FastAPI/Starlette test-client deprecation warning does not fail the suite. See [validation notes](docs/VALIDATION.md) for dates, environment, and limits.

With Uvicorn running, check health in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

Expect HTTP 200 and JSON containing `"status": "ok"`. `/api/health/` redirects to `/api/health`. The response's `author` credits the original backend author, not the deployment account.

Use `/docs` to upload a file, copy its ID, and test analysis, forecast, baseline, simulation, comparison, chat, and both exports. Check actual figures and invalid inputs. A successful build/health response does not verify storage: the cross-worker dataset check currently fails and prevents claiming complete production integration.

## Deployment

### Vercel preview

Use the existing [repository](https://github.com/1iqrashaheen/AI_decision_Intelligance) and [Vercel project](https://vercel.com/iqras-projects-1121dd52/ai-decision-intelligence) in Iqra's account: `iqrashaheen271@gmail.com`, linked with GitHub `1iqrashaheen`.

Configuration follows [Vercel's FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi): repository root as Root Directory, `"framework": "fastapi"` in `vercel.json`, and `main:app` plus Python `>=3.12,<3.13` and dependencies in `pyproject.toml`. Do not use a static-only output directory or an override that bypasses the Python app.

Vercel installs from `pyproject.toml`; declaring only a Python version can lead to a successful build followed by missing-import startup failures. Keep dependencies consistent with local requirements. Set optional AI/configuration variables privately for Preview and Production, never in frontend code. The API client uses the deployed origin.

Push reviewed changes to `integration-branch`. Verify the source commit, Ready status, frontend, health JSON, upload/analysis, simulation, chat, forecast, PDF/CSV, and persistence across workers. Preview URLs may require Vercel sign-in; an SSO redirect is not an application health response.

- [Integration preview](https://ai-decision-intelligence-git-int-f48f79-iqras-projects-1121dd52.vercel.app/)
- [Preview health](https://ai-decision-intelligence-git-int-f48f79-iqras-projects-1121dd52.vercel.app/api/health)
- [Production](https://ai-decision-intelligence-delta.vercel.app/) and [production health](https://ai-decision-intelligence-delta.vercel.app/api/health)

Preview aliases change with each deployment. Production still tracks `main`; its health returned 404 at this review. Preview success is not a production fix. Platform request-body limits apply before FastAPI; raising `MAX_UPLOAD_MB` cannot bypass them. Use small files and plan suitable storage/uploads for larger datasets.

### Production merge

The merge is **pending**. After storage and integration checks pass, open a pull request with **base `main`, compare `integration-branch`**. Review any newer `main` work, validate the resulting integration, and use a merge commit to preserve history. Do not force-push or overwrite unrelated changes. Vercel should deploy the resulting `main` commit.

Then verify the production source commit, environment, frontend, health, upload → analysis → chat/report flow, and persistence. Include the production URL and verified limitations in the submission report.

### Separately hosted backend

If an appropriate host is selected, install the same dependencies, configure its secrets and shared storage, and start Uvicorn on the host's `PORT`. On a PowerShell host:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port $env:PORT
```

On Linux use `--port "$PORT"`. Set `PORT` to the platform-provided value; this alternative is not configured yet. Verify health and persistence before connecting it.

For a frontend kept on Vercel, configure `/api/:path*` to rewrite to the verified HTTPS backend URL, preserving `/api`. That keeps the existing same-origin client working. Direct cross-origin requests instead need an intentional client change and exact `CORS_ORIGINS`; adding an environment variable alone does not change the current browser client. Do not configure a guessed backend address.

## Troubleshooting

| Problem | What to check |
|---|---|
| Vercel health is 404 | Source branch/commit, root directory, FastAPI preset/entrypoint, routing. A static-only site does not run Python. |
| Function returns 500 | Runtime logs, dependencies, Python version. Missing `dotenv` previously came from an empty dependency list in `pyproject.toml`. |
| Deployed page calls localhost | Check the deployed `js/api.js`; it should use the website origin plus `/api`. |
| Dataset disappears | Memory-only workers cannot share uploads. Re-upload locally; connect shared storage for reliable deployment. |
| Local backend unavailable | Run Uvicorn from the root on port 8001; check the environment and port conflicts. |
| Separate frontend is blocked | Prefer the combined server, or allow its exact origin in `CORS_ORIGINS` and restart. |
| AI selection unavailable | Server key/model/mode. `auto` labels fallback; `required` returns an error. Keep keys server-side. |
| Profit/scenario unavailable | Complete actual unit costs, marketing, and expenses are needed; missing costs are not inferred. |
| No forecast | Three consecutive observed months are needed; the saved daily forecast needs its exact historical series. |
| Upload rejected | Valid CSV/XLSX/XLS, usable rows, application/platform size limits. Use CLI for large data. |
| Saved scenario missing | Only scenarios for the current dataset are used; resave older ones without a dataset link. |
| Download fails | Matching backend dataset, nonempty report body, no more than 12 scenarios; inspect API errors. |
| Charts fail | Check CDN access; comparison tables/downloads can still be available. |
| Database variables do nothing | Database integration is not implemented in FastAPI; copied Node settings do not connect it. |
| Different deployment creator | Verify commit author/committer and linked GitHub account. Older attribution remains historical. |
| Asked to log in as Arham | Local FastAPI has no login. Check whether this is an author credit, hosting/GitHub prompt, database tool, or another service URL; see Authentication and login prompts. |

## Source history and attribution

These versions identify imported team work. Current ownership is listed above; original history remains intact.

| Source | Recorded commit | Contribution |
|---|---|---|
| `Abdul_Samad_Task` | `c6b934cd0fa8c0877f8b3985d96fe3d9bdabc967` | Preprocessing notebook, notes, cleaned ZIP used by the extractor. |
| `arham-work` | `6f06f51818ff3ed13ed86d1138b29d9b92d34463` | Original FastAPI backend and API client. |
| `Ahsan-Rafique-Task` | `3d9f77e787b2bb0ea82eb7abaa0e913f0abe9193` | Forecasting source and saved outputs. |
| `whatif-calculations` | `60542e6c023a97119c3b9fe907edb3dba17d14b7` | Standalone calculations. |
| Website baseline | `9ae9d22ebbb54710ab9cf49e79e8b58e63b87593` | Website pages present before integration. |
| `Saud_Masood_Task` | `667e1563b0098675e0a28214a63f96db56c58855` | Database/auth source reviewed separately; not imported into FastAPI. |

Integration adjusted imports for root startup, connected analysis/chat/report functions, retained missing-cost information, added dataset-linked scenarios, and checked saved forecasts against their input history. New forecasting outputs are separate from originals. The notebook retains its source with saved outputs cleared. [docs/VALIDATION.md](docs/VALIDATION.md) records supporting checks.
