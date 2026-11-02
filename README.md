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
| **Saud Masood** | **08 — Database & Authentication.** Database storage, user accounts, and saved scenarios. |

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

Choose **Sign In → Create account** to register with your own email and password (at least 8 characters). You do not need Arham's or Saud's account. The name shown by API health is a module credit, not a login requirement.

While signed in, uploads and saved What-If scenarios are stored under your account. Open **My Account → Open saved data and scenarios** to retrieve them after signing in again. Sign out from **My Account**. Guest demo data stays in this browser and is separate from account data. Sessions last 24 hours; sign in again when one expires.

Three small predefined datasets are included in `samples/`: `sales.csv`, `expenses.csv`, and `inventory.csv`. Analyze all three in the **AI Assistant**; the dashboard and What-If pages use sales data.

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
node --test tests/js/*.test.js
.\.venv\Scripts\python.exe whatif/whatif.py
.\.venv\Scripts\python.exe -m assistant.test_assistant
```

Tests cover calculations, invalid and missing data, dataset-grounded answers, PDF/CSV reports, account isolation, saved scenarios, and database read-back in a fresh Python process. Tests use a separate temporary SQLite database. Skip the Node.js command if Node.js is not installed.

With the backend running, check health in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

The response should contain `"status": "ok"` and `"database": "connected"`.



## Database and authentication

The backend creates `users`, `datasets`, and `saved_scenarios` tables on startup. It saves uploaded rows and cleaning metadata, so dataset IDs remain available after restarting. An unset or blank `DATABASE_URL` uses SQLite at `backend/data/decisionai.db`. Keep this private file to keep your local accounts and data.

For PostgreSQL, create a database named `decisionai` and a user allowed to create its tables. Set `DATABASE_URL` in the root `.env`, install the requirements, and restart the backend. Your own PostgreSQL credentials or a connection string from the database owner are needed; another person's personal password is not needed. Confirm the connection through `/api/health`.

Example root `.env` settings (never commit real secrets):

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/decisionai
JWT_SECRET=YOUR_PRIVATE_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
```

### Authentication API

- `POST /api/auth/register` JSON: `{"email":"you@example.com","password":"a-strong-password"}`
- `POST /api/auth/login` uses the same JSON shape and returns an access token.
- Send `Authorization: Bearer YOUR_ACCESS_TOKEN` on requests to associate uploads with your account.
- `GET /api/auth/me` checks the token.
- `POST /api/auth/logout` clears the browser session.
- `POST /api/saved/scenarios` saves a scenario for the signed-in user; `GET /api/saved/scenarios` lists only that user's scenarios; `GET /api/saved/scenarios/{id}` opens a saved scenario only if it belongs to that user.
- `DELETE /api/saved/scenarios/{id}` deletes your saved scenario. `GET /api/saved/datasets` lists your uploads; `GET /api/saved/datasets/{id}` retrieves their rows.

Passwords use salted PBKDF2 hashes. The website uses an HttpOnly session cookie; API clients can use the returned signed bearer token. Local development creates a private signing secret at `backend/data/.auth-secret` when `JWT_SECRET` is empty. Keep that ignored file so sessions survive restarts. Before production, set `APP_ENV=production` and a private random `JWT_SECRET` of at least 32 characters, use HTTPS and a persistent database. Do not commit `.env`, passwords, database files, signing secrets, or API keys.

If Git says **not a git repository**, open the cloned folder containing `.git`; activating a Python environment does not fix Git commands. If an import is missing, rerun dependency installation with the same `.venv` Python used to start the server. If Groq rejects its key, replace `GROQ_API_KEY` privately and restart, or use `ASSISTANT_MODE=off` for local answers. Refresh the page after pulling updated website files.
