# Module validation - 2026-10-28

## Phase 1: Fazeela's business analysis

- Twelve deterministic calculation and input-validation tests passed before
  phase 2 began; committed on `codex/fazeela-business-analysis` at `cf6a740`.
- Ran the module on all actual cleaned transaction, expense and inventory
  datasets available in Samad's published ZIP.
- Analyzed 536,641 retail rows, 220 expense rows and 160 inventory rows.
- Retail net revenue GBP 9,726,006.95 and positive sales GBP 10,642,110.80
  independently matched the sums in the published daily-sales CSV.
- No product costs, operating expenses or profits were fabricated for retail.
  Findings and limitations are in `business_analysis/README.md`.

## Phase 2: Iqra's assistant integration

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

## Ayesha's comparison and reports

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

## Material limits

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
