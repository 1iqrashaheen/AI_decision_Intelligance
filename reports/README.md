# Scenario comparison and reports - Ayesha's part

This part compares saved scenarios and downloads the business results as PDF or CSV. It uses the existing analysis and What-If modules, so the calculations stay consistent across the project.

## Try it on the website

Follow the setup steps in the [main README](../README.md), then start the server from the main project folder:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

1. Load your data on **Upload Data**, or load the sample from the dashboard.
2. Open **What-If** and enter a change, such as a 10% price increase.
3. Enter a scenario name and click **Save scenario**. Use **Save best / expected / worst** if you want all three cases.
4. Open [Compare Scenarios](http://127.0.0.1:8001/compare.html).
5. Tick the scenarios you want. The table and chart update when you change the selection.
6. Enter a report title, then click **Download PDF** or **Download CSV**.

The page only shows scenarios saved for the current file. Older scenarios without a dataset link need to be saved again. Scenarios from other files stay saved but are left out of this comparison.

You can download the original business results without selecting a scenario. Use **Clear selection** to do that. Choose up to 12 scenarios for one report.

## What the downloads contain

- The selected file's name, dates, currency information and business totals.
- Original results beside the selected scenario estimates.
- Product or expense results, monthly figures and findings from the analysis module.
- Points to review, scenario inputs, assumptions and risks.
- Data-quality notes and an explanation when costs or profit are unavailable.
- A forecast when you tick the forecast option and one is available for the selected data.

The PDF shows up to 10 products or categories and the first 12 recorded months to keep it readable. The CSV contains the full product, category and monthly results. PDF comparison tables are split into groups of three scenarios when needed.

Percentages in the report are written as percentages: `25` means 25%. A percentage change from a zero starting value is unavailable, rather than shown as zero.

The page needs the backend for downloads. Uploaded data is still kept in memory, so it must be uploaded again after restarting the server. Downloads from the comparison page do this automatically for the current browser dataset.

## How the parts connect

| File | What it does |
|---|---|
| `compare.html` | Comparison page and download controls |
| `js/compare.js` | Page selection, chart, table and download requests |
| `js/comparison.js` | Checks which scenarios belong to the selected file and prepares their inputs |
| `backend/app/services/reports.py` | Collects the existing results and creates the PDF or CSV |
| `backend/app/routers/export.py` | The `/api/export` endpoint |
| `tests/test_reports.py` | Export and report checks |
| `tests/js/comparison.test.js` | Dataset, selection and comparison checks |

The browser sends scenario changes, not just saved totals. The backend gets the selected dataset's actual analysis and calls the existing simulator again. This prevents old or edited browser totals from becoming the report's figures.

Points to review use the assistant's existing analysis-based suggestions. This does not make an AI API request. The report also keeps the simulator's risk notes.

## Request a report from another page

First upload the file through `/api/upload` and keep its `dataset_id`. Send a request to `POST /api/export?format=pdf` or `POST /api/export?format=csv` with a body like this:

```json
{
  "dataset_id": "the-id-returned-by-upload",
  "title": "Price change comparison",
  "include_forecast": false,
  "scenarios": [
    {
      "name": "Price +10%",
      "case": "expected",
      "changes": {"price_pct": 0.10},
      "assumptions": {"elasticity": -1.2, "marketing_lift": 0.15}
    }
  ]
}
```

For a report without scenarios, send an empty `scenarios` list. Backend percentage inputs are fractions: `0.10` means 10%.

Missing cost data can still be exported as business results. It cannot be used to invent a profit scenario. The retail, expense and inventory samples remain separate.

The older request format with supplied KPI and scenario figures still works for other pages. Such a report is clearly labeled as supplied figures that were not checked against an uploaded file. A request with no dataset or figures returns an error; it no longer downloads a sample report by mistake.

## Run the checks

From the main project folder, with the virtual environment active:

```powershell
python -m pytest -q
```

If Node.js is installed, also run:

```powershell
node --test tests/js/comparison.test.js
```

The current suite has 70 Python tests and 7 JavaScript tests. The PDF was also checked visually using a three-case sample and a longer report with 12 scenarios.

For the sample file, the original profit is 61,560.00. With prices increased by 10%, the best, expected and worst cases give estimated profits of 73,695.46, 66,722.92 and 59,750.38. These figures depend on the different demand assumptions; they are not guaranteed results.
