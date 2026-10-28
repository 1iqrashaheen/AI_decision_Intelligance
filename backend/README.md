# Backend connections - Arham's part

The backend connects file uploads, analysis, chat, forecasts, scenarios and report downloads. It uses FastAPI.

This copy includes the connections to Fazeela's analysis and Iqra's assistant. For installation, follow the [main README](../README.md).

## Start it

Run this from the main project folder, not from inside `backend`:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

The same command starts the API and serves the website.

- [Assistant page](http://127.0.0.1:8001/assistant.html)
- [API documentation and request forms](http://127.0.0.1:8001/docs)
- [Health check](http://127.0.0.1:8001/api/health)

## Main requests

Every path below starts with `/api`.

| Method and path | What it does |
|---|---|
| `POST /upload` | Reads a CSV or Excel file and returns its `dataset_id`, a preview and data-quality notes |
| `GET /analysis/{dataset_id}` | Returns totals, monthly results, products, findings and missing-data notes |
| `POST /forecast` | Makes a basic monthly sales estimate when there is enough history |
| `GET /simulate/baseline/{dataset_id}` | Returns the starting figures for a simulation when all needed costs are available |
| `POST /simulate` | Calculates one scenario from supplied starting figures and changes |
| `POST /simulate/compare` | Calculates best, expected and worst cases |
| `POST /chat` | Answers a question about the selected dataset and optional scenario |
| `POST /export?format=pdf` | Creates a PDF from the supplied report details |
| `POST /export?format=csv` | Creates a CSV from the supplied report details |

For downloads, send the selected `dataset_id` and any scenario changes. The backend uses that file's analysis and the existing simulator to prepare the report. An empty request returns an error instead of a sample report. The older format with supplied figures still works, but its report is labeled as unverified supplied figures. See [Ayesha's README](../reports/README.md) for examples.

## Connect your page or module

1. Upload the file using `POST /api/upload`. The form field is named `file`.
2. Save the returned `dataset_id`.
3. Use that ID in analysis, forecast or chat requests.
4. Read the response and display the returned results.

The browser helper functions are in [js/api.js](../js/api.js). You can also try requests in [the API documentation](http://127.0.0.1:8001/docs).

The simulation endpoint accepts starting figures directly. If those figures come from a dataset, get them from `/api/simulate/baseline/{dataset_id}` first.

## Details to keep consistent

- Upload sales, expense and inventory files separately.
- Returns stay in the sales data so net revenue includes them.
- Missing costs remain unavailable. They are not filled with an assumed share of revenue.
- For backend scenario inputs, `0.10` means a 10% change. Arayash's separate `whatif/` module uses `10` for the same percentage.
- A selected chat scenario must include a matching `scenario_dataset_id`.
- The basic monthly forecast needs at least three consecutive observed months. Ahsan's saved daily forecast is a separate connection used by chat only when its input data matches.

Uploaded datasets are currently kept in memory. They disappear when the server restarts. Saud's database and login service still needs to be connected.

## Files you may need

| File | Use it for |
|---|---|
| `app/schemas/common.py` | Current request and response fields |
| `app/routers/` | Endpoint code |
| `app/services/` | Analysis, simulation and report functions |
| `app/core/store.py` | Current temporary dataset storage |
| `data/online_retail_sample.csv` | A small retail file for trying uploads |

[API_CONTRACT.md](API_CONTRACT.md) also has examples. If an older example differs, use the current schemas or the running `/docs` page.

## Run the tests

From the main project folder:

```powershell
python -m pytest -q
```
