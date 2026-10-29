# AI Decision Intelligence & What-If Simulator
## Module: Daily Sales Forecasting & Business Recommendations

**Contributor:** Ahsan Rafique
**Role:** AI Engineer (Internship at Codecelix)
**Project:** AI Decision Intelligence & What-If Simulator
**Dataset:** UCI Online Retail (Preprocessed Daily Time-Series)
**Methodology:** PACE Framework (Plan ➔ Analyze ➔ Construct ➔ Execute)

---

## 1. Executive Summary

This module implements a production-grade **Sales Forecasting Pipeline** using machine learning to predict future daily net sales revenue and provide evidence-backed business recommendations for executive decision-making.

### Key Results
* **Primary Model:** **Random Forest Regressor** (with 12 engineered lag, rolling, and calendar features).
* **Baseline Benchmark:** **7-Day Moving Average**.
* **MAE Improvement:** **+47.12% reduction in error** over the baseline.
* **Random Forest MAE:** **£11,029.04** vs. Baseline MAE: **£20,857.05**.
* **$R^2$ Score:** **0.549** on the chronological test set (out-of-sample).
* **30-Day Forecast Generated:** Next 30 operational days forecasted recursively with explicit Saturday zero-order rules and weekly seasonality capture.

---

## 2. Directory Structure

```text
Sales_Forecasting_and_Recommendations/
├── notebooks/
│   └── 01_Sales_Forecasting_Pipeline.ipynb     # Interactive Jupyter notebook for analysis
├── src/
│   ├── forecasting_pipeline.py                 # Core production Python pipeline
│   └── generate_notebook.py                    # Helper to build notebook structure
├── outputs/
│   ├── future_30_days_forecast.csv             # Day-by-day 30-day sales forecast (£)
│   ├── model_evaluation_metrics.json           # Evaluation metrics (MAE, RMSE, R2, % gain)
│   ├── test_set_predictions_comparison.csv     # Actual vs Predicted comparison on test set
│   ├── feature_importances.csv                 # Ranking of key drivers of sales
│   ├── business_recommendations.md             # Actionable business insights for decision-makers
│   └── plots/
│       ├── 01_actual_vs_predicted_test_set.png # Model validation curve
│       ├── 02_future_30_days_sales_forecast.png# Future sales horizon visualization
│       └── 03_feature_importance_drivers.png   # Bar chart of sales drivers
└── README.md                                   # Comprehensive documentation (this file)
```

---

## 3. Methodology & PACE Implementation

### P — Plan
* Identified the business requirement: Estimate future sales revenue from historical retail transactions.
* Established the target variable: `net_sales_gbp` (Net daily revenue accounting for order returns and cancellations).
* Set evaluation criteria: Chronological out-of-sample testing (no random date shuffling) with Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).

### A — Analyze
* Examined daily sales series (`online_retail_daily_sales.csv`) spanning 374 days (`2010-12-01` to `2011-12-09`).
* Identified strong **weekly seasonality**:
  - Saturdays have consistently £0.0 in retail order processing.
  - Mid-week (Wednesday & Thursday) consistently records the highest weekly sales volume.
  - Sunday operations resume with moderate volume.

### C — Construct
* **Feature Engineering:**
  - **Lags:** $t-1, t-2, t-3, t-7, t-14$ (Capturing recent momentum and weekly repeats).
  - **Rolling Statistics:** 7-day and 14-day rolling means and standard deviations (shifted to avoid data leakage).
  - **Calendar Features:** `day_of_week`, `day_of_month`, `month`, `is_weekend`.
* **Chronological Split:**
  - Training Period: `2010-12-15` to `2011-11-09` (330 days).
  - Test Period: `2011-11-10` to `2011-12-09` (30 days).
* **Model Training:**
  - Trained `RandomForestRegressor(n_estimators=150, max_depth=7, min_samples_split=4, random_state=42)`.
  - Feature importance revealed `lag_7` (39.5%), `rolling_mean_7` (12.6%), and `day_of_week` (11.1%) as the top 3 drivers.

### E — Execute
* Generated recursive 30-day forward predictions (`2011-12-10` to `2012-01-08`).
* Compiled visual decision charts in `outputs/plots/`.
* Authored executive business recommendations addressing inventory replenishment, promotional scheduling, and return reserves.

---

## 4. Evaluation Benchmark Summary

| Metric | 7-Day Moving Average Baseline | Random Forest Regressor | Improvement |
| :--- | :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | £20,857.05 | **£11,029.04** | **+47.12% Better** |
| **Root Mean Squared Error (RMSE)** | £26,637.56 | **£17,439.71** | **+34.53% Better** |
| **$R^2$ Score** | N/A | **0.549** | Positive explanatory power |

---

## 5. How to Run the Pipeline

To re-run the pipeline from scratch and regenerate all plots, metrics, and forecasts:

```powershell
python "Sales_Forecasting_and_Recommendations/src/forecasting_pipeline.py"
```

To view or edit the interactive Jupyter Notebook:
Open `Sales_Forecasting_and_Recommendations/notebooks/01_Sales_Forecasting_Pipeline.ipynb` in VS Code or Jupyter Lab.
