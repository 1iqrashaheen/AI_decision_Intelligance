# API Contract & Inter-Module Communication Specification

Report update: `POST /api/export?format=pdf|csv` now accepts a selected
`dataset_id` and scenario inputs (`name`, `changes`, `assumptions`, `case`).
It gets actual analysis results and recalculates the requested scenarios with
the existing simulator. Empty requests no longer return sample figures.
The older supplied-figures format is labeled as unverified. See
[`reports/README.md`](../reports/README.md) for the current download workflow.

Integration update for the analysis/assistant branches (2026-10-28):
`backend/app/schemas/common.py` and `/docs` are the authoritative current
schemas. Analysis adds `totals`, `quality`, `anomalies`, `limitations`,
`dataset_kind` and currency metadata. Missing financial metrics are JSON
`null`, not estimated costs. All products are available to analysis and chat.
Returns/cancellations are retained. Selected chat scenarios also require
`scenario_dataset_id`. Groq selects validated evidence; fallback answers
are labeled. Forecasts require sufficient history, and chat only reuses
Ahsan's published daily forecast for its matching source series. Examples
below illustrate the original interface, not results for an arbitrary upload.

**Author:** Muhammad Arham (Module 07 — Backend connections)
**Project:** AI Decision Intelligence & What-If Simulator
**Version:** 1.0.0

---

## 1. Overview & Architecture

This document defines the formal communication contract between all 9 project modules. The backend (built with FastAPI) acts as the central integration hub connecting the frontend web pages, data cleaning pipeline, data analysis, what-if simulations, forecasting, AI assistant, and report exports.

```
                  +--------------------------------------------------+
                  |               Website Frontend                   |
                  |  (Waleed - 02) Dashboard, Upload, What-If,       |
                  |  (Ayesha - 09) Compare & Report Downloads        |
                  +-------------------------+------------------------+
                                            |
                                            | REST APIs (JSON / Multipart)
                                            v
+------------------------------------------------------------------------------------+
|                         Backend Integration Hub (Arham - 07)                       |
|                                     FastAPI                                        |
+---------+-----------------+-----------------+-------------------+------------------+
          |                 |                 |                   |
          v                 v                 v                   v
   +--------------+  +--------------+  +---------------+  +---------------+
   | Data Store & |  |   Analysis   |  | Forecasting & |  |    What-If    |
   |   Cleaning   |  |   (Fazeela   |  |Recommendations|  |  Simulator   |
   |   (Abdul -   |  |   - 05)      |  |  (Ahsan - 04) |  | (Arayash - 06)|
   |     03)      |  +--------------+  +---------------+  +---------------+
   +--------------+         |                 |                   |
                            +--------+--------+                   |
                                     |                            v
                                     v                   +-----------------+
                              +---------------+          |   Reports &     |
                              |  AI Business  |          |   PDF / CSV     |
                              |   Assistant   |          |  (Ayesha - 09)  |
                              |  (Iqra - 01)  |          +-----------------+
                              +---------------+
```

---

## 2. Global Conventions

- **Base URL:** `http://localhost:8001/api`
- **Content-Type:** `application/json` (except `/api/upload` which is `multipart/form-data` and `/api/export` which returns binary `application/pdf` or `text/csv`).
- **Percentage Inputs:** All percentage changes are expressed as decimals (e.g., `0.10` = `+10%`, `-0.05` = `-5%`).
- **Currency Values:** Handled as floating point numbers rounded to 2 decimal places in calculations.
- **Error Response Format:**
  ```json
  {
    "error": {
      "code": "error_code_string",
      "message": "Human readable message",
      "details": [
        {"field": "baseline.price", "message": "Price must be >= 0"}
      ]
    }
  }
  ```

---

## 3. Module Specifications & Endpoints

### 3.1 Data Upload & Cleaning (Abdul Samad & Muhammad Arham)
- **Endpoint:** `POST /api/upload`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request:**
  - `file`: CSV or Excel file (`.csv`, `.xlsx`, `.xls`), max 10MB.
  - Supports standard business files (`date, product, units, price, unit_cost, marketing_spend, expenses`) AND **UCI Online Retail II** transactions (`Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country`).
- **Response (200 OK):**
  ```json
  {
    "dataset_id": "a1b2c3d4e5f6",
    "filename": "online_retail_sample.csv",
    "quality": {
      "rows": 1000,
      "columns": 8,
      "duplicate_rows": 12,
      "missing_cells": 4,
      "columns_info": [
        {"name": "date", "dtype": "object", "missing": 0},
        {"name": "product", "dtype": "object", "missing": 0},
        {"name": "units", "dtype": "int64", "missing": 0},
        {"name": "price", "dtype": "float64", "missing": 0}
      ]
    },
    "preview": [
      {
        "date": "2025-01-15",
        "product": "WHITE HANGING HEART T-LIGHT HOLDER",
        "units": 6,
        "price": 2.55,
        "invoice_no": "example-invoice",
        "stock_code": "example-stock-code"
      }
    ]
  }
  ```

---

### 3.2 Business Data Analysis (Fazeela Manzoor & Ahsan Rafique)
- **Endpoint:** `GET /api/analysis/{dataset_id}`
- **Method:** `GET`
- **Parameters:** `dataset_id` (string, path parameter)
- **Response (200 OK):**
  ```json
  {
    "dataset_id": "a1b2c3d4e5f6",
    "kpis": [
      {"label": "Total Revenue", "value": 154230.50},
      {"label": "Total Units Sold", "value": 52400.0},
      {"label": "Gross Profit", "value": 61692.20},
      {"label": "Profit Margin", "value": 40.0}
    ],
    "trend": [
      {"period": "2024-01", "revenue": 12400.0, "profit": 4960.0, "units": 4200},
      {"period": "2024-02", "revenue": 14100.0, "profit": 5640.0, "units": 4800}
    ],
    "by_product": [
      {
        "product": "Product A",
        "units": 12000,
        "revenue": 45000.0,
        "gross_margin": 45.2,
        "share_pct": 29.2
      }
    ],
    "findings": [
      "Product A generates the highest revenue (29.2% of total).",
      "Sales increased by 13.7% between 2024-01 and 2024-02.",
      "Overall gross margin is healthy at 40.0%."
    ],
    "source": "calculated"
  }
  ```

---

### 3.3 Sales Forecasting (Ahsan Rafique)
- **Endpoint:** `POST /api/forecast`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "dataset_id": "a1b2c3d4e5f6",
    "periods": 3
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "dataset_id": "a1b2c3d4e5f6",
    "method": "linear_trend_seasonality",
    "forecast": [
      {"period": "2024-13", "revenue": 15200.0, "lower": 13800.0, "upper": 16600.0},
      {"period": "2024-14", "revenue": 15850.0, "lower": 14200.0, "upper": 17500.0},
      {"period": "2024-15", "revenue": 16400.0, "lower": 14500.0, "upper": 18300.0}
    ],
    "recommendation": "Sales trajectory is upward (+4.1% monthly trend). Maintain inventory to support projected volume.",
    "source": "calculated"
  }
  ```

---

### 3.4 What-If Simulator & Scenarios (Arayash Noor)
- **Endpoint 1:** `GET /api/simulate/baseline/{dataset_id}`
  - Pre-extracts aggregate baseline values from any uploaded dataset.
- **Endpoint 2:** `POST /api/simulate`
  - Runs a single scenario calculation.
  - **Request Body:**
    ```json
    {
      "baseline": {
        "units": 1000,
        "price": 100,
        "unit_cost": 60,
        "marketing": 5000,
        "expenses": 10000
      },
      "changes": {
        "price_pct": 0.10,
        "cost_pct": 0.0,
        "marketing_pct": 0.15,
        "expenses_pct": 0.0
      },
      "assumptions": {
        "elasticity": -1.2,
        "marketing_lift": 0.15
      }
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "original": {
        "units": 1000.0,
        "revenue": 100000.0,
        "cogs": 60000.0,
        "marketing": 5000.0,
        "expenses": 10000.0,
        "profit": 25000.0,
        "margin_pct": 25.0
      },
      "scenario": {
        "units": 899.8,
        "revenue": 98978.0,
        "cogs": 53988.0,
        "marketing": 5750.0,
        "expenses": 10000.0,
        "profit": 29240.0,
        "margin_pct": 29.54
      },
      "delta": {
        "units": -100.2,
        "revenue": -1022.0,
        "profit": 4240.0,
        "margin_pct": 4.54
      },
      "assumptions": {
        "elasticity": -1.2,
        "marketing_lift": 0.15
      },
      "notes": [
        "Price rise of 10% increases estimated profit by $4,240 despite volume decrease."
      ]
    }
    ```
- **Endpoint 3:** `POST /api/simulate/compare`
  - Runs Best Case, Expected Case, and Worst Case on the same scenario inputs.

---

### 3.5 AI Business Assistant (Iqra Shaheen)
- **Endpoint:** `POST /api/chat`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "dataset_id": "a1b2c3d4e5f6",
    "question": "Which product has the highest profit margin and what happens if we raise its price by 10%?",
    "scenario": null
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "answer": "Based on your uploaded dataset, Product A has the highest gross margin at 45.2%. If you increase its price by 10%, estimated profit increases by ~16.9% assuming standard price elasticity (-1.2).",
    "context_used": [
      "by_product.gross_margin",
      "totals.revenue",
      "simulate.price_pct=+0.10"
    ],
    "source": "grounded_assistant"
  }
  ```

---

### 3.6 Reports & PDF/CSV Export (Ayesha Hussain)
- **Endpoint:** `POST /api/export?format=pdf` or `POST /api/export?format=csv`
- **Method:** `POST`
- **Request Body (optional):**
  ```json
  {
    "title": "Quarterly Business Decision Report",
    "kpis": [
      {"label": "Total Revenue", "value": 154230.50},
      {"label": "Total Profit", "value": 61692.20}
    ],
    "scenarios": [
      {"name": "Current Baseline", "revenue": 154230.50, "cogs": 92538.30, "profit": 61692.20},
      {"name": "Price +10%", "revenue": 162400.0, "cogs": 86200.0, "profit": 76200.0}
    ],
    "assumptions": [
      "Price elasticity: -1.2",
      "Marketing lift: 0.15"
    ]
  }
  ```
- **Response (200 OK):**
  - Binary PDF file (`application/pdf`) with formatted tables, headers, and disclaimers.
  - Or CSV file (`text/csv`) with structured sections for Excel import.

---

## 4. Integration Verification Summary

All modules can verify compliance using:
```bash
cd backend
python -m pytest -q
```
Every endpoint validates request schemas, handles negative or missing values gracefully, and returns uniform HTTP error codes (`400`, `404`, `413`, `422`).
