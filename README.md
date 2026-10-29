# AI Decision Intelligence & What-If Simulator

DecisionAI helps users upload business data, view results, compare what-if scenarios, ask business questions, and download PDF or CSV reports.

The frontend uses HTML, CSS, and JavaScript. The backend uses Python, FastAPI, pandas, and NumPy. Groq is optional for AI-assisted answers.

## Team and modules

| Team member | Modules and responsibilities |
|---|---|
| **Iqra Shaheen** | **01 — AI Business Assistant; 05 — Business Data Analysis; 09 — Scenario Comparison & Reports.** Business questions, sales/expense/inventory analysis, scenario comparisons, and PDF/CSV reports. |
| **Muhammad Waleed Ansari** | **02 — Website Frontend.** Dashboard, upload pages, What-If interface, charts, and styling. |
| **Abdul Samad** | **03 — Dataset Sourcing & Cleaning.** Source datasets, preprocessing, and cleaned business data. |
| **Ahsan Rafique** | **04 — Sales Forecasting & Recommendations.** Forecasting pipeline, saved forecasts, and model evaluation. |
| **Arayash Noor** | **06 — What-If Calculations.** Standalone price, expense, marketing, and inventory calculations. |
| **Muhammad Arham** | **07 — Backend Connections.** API routes and connections between uploads, analysis, simulation, chat, and reports. |
| **Saud Masood** | **08 — Database & Authentication.** PostgreSQL storage, user accounts, and saved records; integration is pending. |

## Setup

Install **Git** and **Python 3.12**. Install **Node.js** only if you want to run the JavaScript tests.

```powershell
git clone --branch integration-branch https://github.com/1iqrashaheen/AI_decision_Intelligance.git
cd AI_decision_Intelligance
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you already have the project and `.venv`, open the existing project folder and skip cloning and environment creation. Run all commands from the folder containing `main.py`.

On Linux/macOS, create the environment with `python3.12 -m venv .venv`, activate it with `source .venv/bin/activate`, and use `python` instead of `.\.venv\Scripts\python.exe` below.

## Run the project

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

This starts both the website and backend. Keep the terminal open, then visit:

- [Website](http://127.0.0.1:8001/)
- [AI Assistant](http://127.0.0.1:8001/assistant.html)
- [API documentation](http://127.0.0.1:8001/docs)
- [API health](http://127.0.0.1:8001/api/health)

Load the sample data or upload a CSV/Excel file. Review the dashboard, save a What-If scenario, compare results, or ask the assistant a question. Reports can be downloaded from **Compare Scenarios**. Stop the server with **Ctrl+C**.

**No login or Arham's credentials are needed to run the current local backend.**

## Optional AI configuration

The sample workflow works without an API key. To enable Groq, copy the root `.env.example` to `.env` only if `.env` does not already exist, and enter your own server-side key:

```dotenv
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
ASSISTANT_MODE=auto
```

Restart the backend after changing settings. Leave the key unset for local answers, or use `ASSISTANT_MODE=off` to disable model calls. Never commit `.env` or real keys. The default upload limit is 10 MiB; `MAX_UPLOAD_MB` changes the application limit, but hosting limits still apply.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/js/api.test.js tests/js/comparison.test.js
.\.venv\Scripts\python.exe whatif/whatif.py
.\.venv\Scripts\python.exe -m assistant.test_assistant
```

The latest checks passed **85 Python tests and 11 JavaScript tests**. Skip the Node.js command if Node.js is not installed.

With the backend running, check health in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

The response should contain `"status": "ok"`.

