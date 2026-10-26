# Backend Integration Layer (FastAPI) — Muhammad Arham

**Module:** 07 — Backend connections  
**Developer:** Muhammad Arham  
**Framework:** FastAPI, Uvicorn, Pandas, ReportLab, Pytest  

---

## Overview

This module serves as the central backend integration hub for the **AI Decision Intelligence & What-If Simulator**. It connects data upload, cleaning, business analysis, time-series forecasting, what-if simulations, AI chat assistant, and PDF/CSV report generation, linking teammate contributions to the frontend web application.

---

## Quickstart

### 1. Run the Backend API Server
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8001
```

- **Interactive Swagger Documentation:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Alternative Redoc Documentation:** [http://localhost:8001/redoc](http://localhost:8001/redoc)
- **API Health Check:** [http://localhost:8001/api/health](http://localhost:8001/api/health)

### 2. Run the Full Pytest Test Suite
```bash
cd backend
python -m pytest -v tests/test_api.py
```
*(All 15 automated test cases validate health, uploads, retail dataset handling, analysis, forecasting, simulations, comparison cases, AI chat, and PDF/CSV exports).*

---

## Inter-Module API Endpoints (all prefixed with `/api`)

| Method | Endpoint | Connected Module & Owner | Status & Capabilities |
|---|---|---|---|
| `GET` | `/health` | Core Meta (Muhammad Arham) | Returns status, module info, and author. |
| `POST` | `/upload` | 03 Datasets & Data Cleaning (Abdul Samad) | Cleans and normalizes CSV/Excel files; supports **UCI Online Retail II** and standard sales files; auto-detects columns, filters returns, computes quality reports. |
| `GET` | `/analysis/{dataset_id}` | 05 Business Data Analysis (Fazeela Manzoor) | Computes real revenue, profit, margins, monthly trends, top products, and data-backed business findings from the active dataset. |
| `POST` | `/forecast` | 04 Forecasting & Recommendations (Ahsan Rafique) | Generates future monthly revenue projections using historical trend analysis. |
| `GET` | `/simulate/baseline/{dataset_id}` | 06 What-If Calculations (Arayash Noor) | Pre-extracts aggregate baseline values (`units, price, cost, marketing, expenses`) from any uploaded dataset to pre-fill simulator forms. |
| `POST` | `/simulate` | 06 What-If Calculations (Arayash Noor) | Computes what-if scenario revenue, COGS, expenses, and profit using elasticity and marketing lift assumptions; generates risk alerts. |
| `POST` | `/simulate/compare` | 06 What-If Calculations (Arayash Noor) | Simultaneously simulates Best Case, Expected Case, and Worst Case scenarios. |
| `POST` | `/chat` | 01 AI Business Assistant (Iqra Shaheen) | Answers user questions with context injected directly from the active dataset and scenarios. Connects to OpenAI/LLM when API key is provided, with an intelligent built-in analytical engine as fallback. |
| `POST` | `/export?format=pdf\|csv` | 09 Scenario Comparison & Reports (Ayesha Hussain) | Generates and streams publication-ready PDF reports (built with ReportLab) and CSV exports. |

---

## Dataset Integration: UCI Online Retail II

The backend includes native support for the team's primary benchmark dataset, **UCI Online Retail II** (`Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country`):
- Automatically removes cancellation invoices (invoices starting with `C`) and negative return quantities.
- Converts `InvoiceDate` timestamps into ISO dates and monthly periods (`YYYY-MM`).
- Derives baseline unit costs, operating overhead, and sales metrics.
- A 100-row representative sample is included at `backend/data/online_retail_sample.csv` for immediate testing.

---

## Frontend Integration

The frontend client library is located at `js/api.js`:
- Automatically detects if the FastAPI server is running on `http://localhost:8001`.
- Renders a live connection badge on the website topbar (`FastAPI Connected` vs `Offline Mode`).
- Enables one-click PDF and CSV report downloads directly from the scenario comparison page (`compare.html`).

---

## Detailed Specifications

For the comprehensive data interchange format and schemas across all 9 modules, see [`API_CONTRACT.md`](./API_CONTRACT.md).
