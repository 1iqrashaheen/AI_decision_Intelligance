# AI Decision Intelligence & What-If Simulator

This project helps users understand business data, try changes to their business, and ask questions about the results.

This branch brings together three parts of the project:

- **Business analysis (Fazeela's part):** calculates totals, product performance, trends and unusual values.
- **AI business assistant (Iqra's part):** answers questions using those results and the selected scenario.
- **Scenario comparison and reports (Ayesha's part):** compares saved scenarios and downloads the results as PDF or CSV.

The backend and supporting code come from the team's existing branches. The notes below explain how to run these parts and connect them to the rest of the project.

## 1. Set up the project

Open a terminal in the main project folder. This is the folder containing `main.py` and `requirements.txt`. Run all commands below from this folder, not from inside `backend`.

These commands are for Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the `.venv` folder already exists, skip the first command.

If PowerShell will not let you activate the environment, use `.\.venv\Scripts\python.exe` in place of `python` in the commands below. You can use it to install the requirements too.

## 2. Start the website

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Keep this terminal open while using the website.

Open [the assistant page](http://127.0.0.1:8001/assistant.html). Click **Try sample sales** to check that everything is working. You can then upload your own file.

To stop the server, press **Ctrl+C** in the terminal.

The [dashboard](http://127.0.0.1:8001/index.html) and [API documentation](http://127.0.0.1:8001/docs) use the same server.

## 3. Add your Groq API key

You can try the supported questions without a key. The page will tell you when it is using the local answer method.

To use the AI model:

1. If there is no `.env` file, copy `.env.example` and rename the copy to `.env`.
2. Open `.env` and replace `your_api_key_here` with your own Groq API key.
3. Restart the server.

If `.env` already exists, edit it instead of replacing it. Do not share this file or upload it to GitHub.

The settings look like this:

```dotenv
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
ASSISTANT_MODE=auto
```

Leave `ASSISTANT_MODE=auto` for normal use. Use `off` to turn off model requests, or `required` if you want an error when the AI service cannot answer.

The model receives the question and summary facts. The app checks its choice of facts and uses the calculated figures in the reply.

## 4. Try your own data

On the assistant page, choose a CSV or Excel file. Upload one sales, expense or inventory file at a time. For Excel, the app reads the first worksheet.

You can ask questions such as:

- What is our total revenue?
- What is our net profit?
- Which product has the lowest profit margin?
- What was revenue in 2025-03?
- What unusual values should I review?
- What happens if prices increase by 10%?

Use the actual month or product name from your file. Each question should include the details it needs; the assistant does not use previous messages to resolve words such as "it" or "that product."

If the file does not contain costs or expenses, profit may show as **unavailable**. This is expected. Sales alone are not enough to calculate profit.

### Use a saved scenario

1. Load data on the **Upload Data** page.
2. Open **What-If**, enter your changes, and save the scenario.
3. Open **AI Assistant** and click **Use dashboard data**.
4. Choose the saved scenario under **Question context**.
5. Ask a question such as "What is revenue in the selected scenario?"

The scenario must belong to the same dataset. Older scenarios saved without a dataset link need to be saved again.

For changes to more than one variable, use the What-If page. Simple chat questions can calculate one percentage change at a time.

## 5. Get Abdul Samad's cleaned datasets

```powershell
git fetch origin Abdul_Samad_Task
python scripts/fetch_team_data.py
```

The files will be placed in `data/team_cleaned/`. The shared ZIP contains Online Retail, expenses, inventory, and the daily sales summary. It does not contain a cleaned Online Retail II file.

These are separate datasets from different sources. Do not combine the expense or inventory sample with retail sales to calculate profit unless the team has confirmed how the records are related.

The full cleaned retail CSV is about 65 MB. The website normally accepts files up to 10 MB. To allow that larger file, stop the server and run:

```powershell
$env:MAX_UPLOAD_MB="100"
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

## Notes for team members

| If you are working on... | Where to start |
|---|---|
| Dashboard or charts | Use the analysis results: `kpis`, `trend`, `by_product` and `findings`. |
| Backend connections | Upload a file first, keep its `dataset_id`, and use that ID for analysis and chat requests. |
| Forecasts or recommendations | Pass results for the same dataset. See the [assistant notes](assistant/README.md) and [forecast notes](forecasting/README.md). |
| Scenario comparison or reports | Use the returned totals and findings. Keep actual figures and scenario estimates clearly labeled. |
| Database and login | Connect storage and account access to the backend. Uploaded datasets are currently kept in memory. |

For Python examples and file details, read the [business analysis README](business_analysis/README.md), [assistant README](assistant/README.md), [comparison and reports README](reports/README.md), or [backend README](backend/README.md).

## Download a comparison report

Open **Compare Scenarios**, choose the saved scenarios for the current file, and click **Download PDF** or **Download CSV**. The downloads include the original business results, selected scenarios, findings, points to review, assumptions and risks.

Use **Clear selection** to download only the business results. The page also works when there are no saved scenarios yet. The backend must be running for downloads.

Only scenarios from the selected dataset are compared. See [Ayesha's README](reports/README.md) for the steps and the export request format.

## Run the checks

```powershell
python -m pytest -q
python whatif/whatif.py
```

The test suite currently has 70 passing Python tests. It does not call the live AI API. If Node.js is installed, run the 7 comparison checks too:

```powershell
node --test tests/js/comparison.test.js
```

More details are in [the validation notes](docs/VALIDATION.md).

For a small assistant example without an API call, run:

```powershell
python -m assistant.test_assistant
```

## Common problems

| Problem | What to do |
|---|---|
| The page says the backend is unavailable | Start the server from the main project folder and keep its terminal open. |
| Your uploaded dataset is missing after a restart | Upload it again. Permanent database storage is not connected yet. |
| The AI service is unavailable | Check your own key in `.env`, then restart. With `auto`, supported questions can still use the local answer method. |
| Profit or a scenario is unavailable | Check that the file includes unit costs, marketing spend and expenses. Enter zero only when the actual value is zero. |
| A forecast is unavailable | Check that there is enough sales history and no missing months. Ahsan's saved forecast is only used for its matching dataset. |
| The file is too large | Follow the upload-limit command above, or use command-line analysis. |

## Branches

`codex/fazeela-business-analysis` contains the analysis work on its own. `codex/iqra-ai-assistant` includes that work plus the assistant and its connections. `codex/ayesha-comparison-reports` adds the comparison page, downloads and simpler code comments.

The branches are currently local. The shared `main` branch has not been changed. See [the source notes](team_sources/README.md) for the team branches used.

Database/login connections and deployment still need to be brought together with the rest of the team's work.
