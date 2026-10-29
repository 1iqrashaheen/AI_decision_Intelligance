# Validation record

Setup, current ownership, API usage, and deployment instructions are in the
[main README](../README.md). Earlier checks below are historical evidence,
not a claim that production or shared database storage is complete.

## Documentation consolidation - 2026-10-29

- Reviewed all ten project README files and the older API contract. Moved
  useful setup, module, dataset, model, report, and provenance information
  into one root README; removed nine redundant READMEs and the stale contract.
  Changes are limited to documentation and three ownership docstrings; no
  application behavior, UI, styles, business logic, or original commits changed.
- The project owner confirmed Iqra's current responsibility for modules 01,
  05, and 09. The two previous module owners remain in historical attribution.
  Other responsibilities were checked against source notes and Git branches.
- Checked all 26 relative Markdown links/anchors, both JSON request examples
  against current schemas, and every full source commit ID. No application
  code reads the removed documentation files.
- Re-ran 85 Python tests, 11 JavaScript tests, the standalone What-If checks,
  the offline assistant example, and sample CLI analysis. The documented
  Python import example and sample revenue/profit were verified.
- Ran the documented dataset fetch/extraction. It produced retail, expenses,
  products, daily-sales, and preprocessing-summary CSVs; Online Retail II was
  absent, as the revised guide states. Generated files remain outside commits.
- Started the documented Uvicorn entrypoint and checked PowerShell health,
  frontend/docs/sample routes, upload, analysis, forecast, baseline, simulation,
  comparison, chat, and both scenario report formats over actual HTTP.
- `pip check` reported no broken requirements. These commands used the existing
  Python 3.14.2 environment; fresh Python 3.12 setup, optional model retraining,
  the separately supplied Online Retail II Excel workflow, live Groq access,
  and database setup remain unverified/manual steps.
- Found a separate-service packaging mismatch on `Saud_Masood_Task`:
  package scripts expect `src/server.js`, but files are flat at the root and
  server imports expect absent subdirectories. The README documents this
  unfinished work rather than claiming that adding database variables fixes it.
- The production merge still depends on shared storage integration and its
  verification; this documentation change does not resolve that blocker.

## Integration and deployment review - 2026-10-29

- The application suite passed **85 Python tests and 11 JavaScript tests**.
  Local tests used the existing Python 3.14.2 environment; the declared Vercel
  runtime is Python 3.12. A fresh local Python 3.12 install was not exercised.
- Actual local HTTP checks passed for health (both URL forms), public/static
  pages, upload, analysis, forecast, baseline, simulation, comparison, chat,
  PDF/CSV exports, invalid upload types, and missing dataset errors.
- Browser sample checks showed revenue 191,080.00, profit 61,560.00, and
  Desk Lamp as the lowest known margin product (45.71%).
- Preview startup was repaired by selecting FastAPI, declaring the entrypoint
  and dependencies, and using same-origin API URLs. The earlier runtime log
  reported `No module named 'dotenv'`.
- Live preview checks passed for health, sample upload/analysis, price +10%
  chat estimates (revenue 184,965.44; profit 66,722.92), and the 48-row CSV download.
- Commit `ffb455d67d33bd5bdf0d128b2944203aec76f15c` was authored/committed as
  `1iqrashaheen`. Preview deployment `HwMiZcgtsw5fmFM9y9qn4QKd2xRv` showed
  Created `1iqrashaheen`, Ready, and healthy JSON from its health route.
- A separate Python process could not read a dataset saved in another process.
  Shared storage is a known production blocker. Health checks process
  availability only.
- At that review, `main` remained at `9ae9d22` and production health returned
  HTTP 404. Production merge/deployment verification was not completed.
- Automated tests use offline/mocked assistant selection. No live Groq request,
  new training run, Node/PostgreSQL deployment, or database migration was
  performed in this deployment review.

## Historical module checks - 2026-10-28

### Phase 1: Business data analysis

- Twelve deterministic calculation and input-validation tests passed before
  phase 2 began; committed on `codex/fazeela-business-analysis` at `cf6a740`.
- Ran the module on all actual cleaned transaction, expense and inventory
  datasets available in Samad's published ZIP.
- Analyzed 536,641 retail rows, 220 expense rows and 160 inventory rows.
- Retail net revenue GBP 9,726,006.95 and positive sales GBP 10,642,110.80
  independently matched the sums in the published daily-sales CSV.
- No product costs, operating expenses or profits were fabricated for retail.
  Findings and limitations are now in the main README's Business data analysis
  and Datasets and preprocessing sections.

### Phase 2: Iqra's assistant integration

- Root command: `python -m pytest -q`: **56 tests passed**. Covers both modules and the imported
  backend suite. Automated tests make no live model calls.
- A separate live Groq request in required mode selected the correct evidence
  for an invented demo with revenue 200.00. The response was `groq_grounded`
  with no fallback warning. No raw retail rows or customer IDs were transmitted.
- Browser walkthrough: opened `/assistant.html`, clicked **Try sample sales**,
  verified the 48-row analysis and asked the lowest-margin question. The model
  selected Desk Lamp, gross margin 45.71%, with evidence shown in the page.
- Browser saved-scenario walkthrough: loaded shared dashboard data, saved a
  price +10% scenario, selected it in chat, and verified recalculated revenue
  184,965.44 and net profit 66,722.92 against baseline revenue 191,080.00 and
  profit 61,560.00. The Groq-grounded answer displayed its assumptions.
- Ahsan's published 30 daily forecast rows matched the exact UCI daily series
  signature and summed to GBP 1,000,422.79. Changing an input price caused the
  published-forecast match to fail, preventing use for the changed dataset.
- JSON outputs were checked for strict JSON serialization; JavaScript syntax
  was checked with Node. The original standalone what-if examples are also
  checked with `python whatif/whatif.py`.

### Scenario comparison and reports

- The updated suite passes 70 Python tests and 7 JavaScript tests.
- Report checks cover actual analysis, best/expected/worst cases, changed
  browser totals, missing costs, baseline-only exports, invalid requests,
  expense and inventory files, forecast availability, escaped PDF text and
  spreadsheet formula prefixes in CSV cells.
- The sample report was rendered and reviewed on all three pages. A report
  with 12 long scenario names was also rendered and reviewed on all six pages.
- The sample's original profit is 61,560.00. Price +10% gives best/expected/worst
  profit estimates of 73,695.46, 66,722.92 and 59,750.38 using the existing
  simulator's assumptions.
- Browser download checks cover the selected dataset and saved scenario.
- Module comments and docstrings were shortened into plain explanations.

### Material limits at the historical review

- This is completion of members 05, 01 and 09 with their required integrations,
  not a claim that all nine members' final application is integrated.
- The imported backend's storage is in memory and has no connected account
  access layer here. Saud's separate PostgreSQL/login branch is not merged.
- The assistant intentionally supports a bounded set of question types, and
  individual questions should state their product or period explicitly.
- Forecasting outputs are estimates tied to their recorded dates and model
  assumptions. The Random Forest was imported, not retrained during this work.
- Default upload limit is 10 MB; use the documented configuration for the
  complete cleaned retail CSV. Command-line analysis was run on the full file.
- The installed FastAPI/Starlette test client emits an upstream deprecation
  warning about its httpx transport; it does not cause test failures.
