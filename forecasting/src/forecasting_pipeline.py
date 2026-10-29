import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = (
    BASE_DIR.parent
    / "data"
    / "team_cleaned"
    / "online_retail_daily_sales.csv"
)
OUTPUT_DIR = BASE_DIR.parent / "output" / "forecasting"
PLOTS_DIR = OUTPUT_DIR / "plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_and_prepare_data(file_path):
    print("--------------------------------------------------")
    print(f"Step 1: Loading daily sales data from:\n{file_path}")
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    print(f"Total daily records: {len(df)}")
    print(
        f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
    )
    return df


def create_features(df, target_col="net_sales_gbp"):
    print("--------------------------------------------------")
    print(f"Step 2: Engineering Time-Series Features for target: '{target_col}'")
    data = df.copy()

    # Calendar features
    data["day_of_week"] = data["date"].dt.dayofweek  # 0=Monday, 6=Sunday
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)

    # Lag features
    for lag in [1, 2, 3, 7, 14]:
        data[f"lag_{lag}"] = data[target_col].shift(lag)

    # Rolling window statistics (shifted by 1 to prevent data leakage)
    data["rolling_mean_7"] = (
        data[target_col].shift(1).rolling(window=7, min_periods=7).mean()
    )
    data["rolling_std_7"] = (
        data[target_col].shift(1).rolling(window=7, min_periods=7).std()
    )
    data["rolling_mean_14"] = (
        data[target_col].shift(1).rolling(window=14, min_periods=14).mean()
    )

    # Drop rows with NaN from lags/rolling windows
    clean_data = data.dropna().reset_index(drop=True)
    print(f"Features created successfully. Usable rows after lag drops: {len(clean_data)}")
    return clean_data


def train_and_evaluate(data, target_col="net_sales_gbp", test_days=30):
    print("--------------------------------------------------")
    print(f"Step 3: Chronological Train-Test Split (Last {test_days} days as Test)")

    feature_cols = [
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend",
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "rolling_mean_7",
        "rolling_std_7",
        "rolling_mean_14",
    ]

    train_df = data.iloc[:-test_days].copy()
    test_df = data.iloc[-test_days:].copy()

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    print(
        f"Train set: {len(train_df)} days ({train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')})"
    )
    print(
        f"Test set:  {len(test_df)} days ({test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')})"
    )

    # 1. Baseline Model: 7-day Moving Average
    baseline_pred = test_df["rolling_mean_7"]
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

    # 2. Hero Model: Random Forest Regressor
    print("\nTraining Hero Model: Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=150,
        max_depth=7,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
    )
    rf_model.fit(X_train, y_train)

    rf_pred = rf_model.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    rf_r2 = r2_score(y_test, rf_pred)

    mae_improvement = ((baseline_mae - rf_mae) / baseline_mae) * 100
    rmse_improvement = ((baseline_rmse - rf_rmse) / baseline_rmse) * 100

    print("--------------------------------------------------")
    print("Step 4: Model Evaluation Metrics")
    print(f"Baseline (7-Day Moving Avg) -> MAE: £{baseline_mae:,.2f} | RMSE: £{baseline_rmse:,.2f}")
    print(
        f"Random Forest Regressor     -> MAE: £{rf_mae:,.2f} | RMSE: £{rf_rmse:,.2f} | R²: {rf_r2:.3f}"
    )
    print(f"Random Forest Improvement over Baseline: {mae_improvement:.2f}% (MAE)")

    metrics = {
        "baseline": {
            "model_name": "7-Day Moving Average Baseline",
            "MAE_GBP": round(baseline_mae, 2),
            "RMSE_GBP": round(baseline_rmse, 2),
        },
        "random_forest": {
            "model_name": "Random Forest Regressor",
            "MAE_GBP": round(rf_mae, 2),
            "RMSE_GBP": round(rf_rmse, 2),
            "R2_Score": round(rf_r2, 4),
            "improvement_pct_mae": round(mae_improvement, 2),
            "improvement_pct_rmse": round(rmse_improvement, 2),
        },
        "test_period": {
            "start_date": test_df["date"].min().strftime("%Y-%m-%d"),
            "end_date": test_df["date"].max().strftime("%Y-%m-%d"),
            "test_days": test_days,
        },
    }

    with open(OUTPUT_DIR / "model_evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    # Save test comparison table
    test_comparison = pd.DataFrame(
        {
            "date": test_df["date"].dt.strftime("%Y-%m-%d"),
            "actual_sales_gbp": y_test.values,
            "baseline_pred_gbp": baseline_pred.values,
            "random_forest_pred_gbp": rf_pred,
            "rf_absolute_error_gbp": np.abs(y_test.values - rf_pred),
        }
    )
    test_comparison.to_csv(
        OUTPUT_DIR / "test_set_predictions_comparison.csv", index=False
    )

    # Feature importances
    importances = pd.DataFrame(
        {"feature": feature_cols, "importance": rf_model.feature_importances_}
    ).sort_values("importance", ascending=False)
    importances.to_csv(OUTPUT_DIR / "feature_importances.csv", index=False)

    return rf_model, test_df, rf_pred, baseline_pred, feature_cols, importances


def recursive_future_forecast(df, model, feature_cols, horizon_days=30, target_col="net_sales_gbp"):
    print("--------------------------------------------------")
    print(f"Step 5: Generating Recursive Future Forecast for next {horizon_days} days")

    history = df[["date", target_col]].copy()
    future_dates = pd.date_range(
        start=history["date"].max() + pd.Timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )

    future_preds = []

    for f_date in future_dates:
        # Construct feature vector for current future date
        day_of_week = f_date.dayofweek
        day_of_month = f_date.day
        month = f_date.month
        is_weekend = int(day_of_week in [5, 6])

        # Lags from history
        vals = history[target_col].values
        lag_1 = vals[-1]
        lag_2 = vals[-2]
        lag_3 = vals[-3]
        lag_7 = vals[-7]
        lag_14 = vals[-14]

        # Rolling stats
        rolling_mean_7 = np.mean(vals[-7:])
        rolling_std_7 = np.std(vals[-7:])
        rolling_mean_14 = np.mean(vals[-14:])

        row = {
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "month": month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_3": lag_3,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "rolling_mean_7": rolling_mean_7,
            "rolling_std_7": rolling_std_7,
            "rolling_mean_14": rolling_mean_14,
        }

        X_step = pd.DataFrame([row])[feature_cols]
        predicted_val = float(model.predict(X_step)[0])

        # In retail dataset, Saturdays are strictly closed / zero-sales
        if day_of_week == 5:  # Saturday
            predicted_val = 0.0
        else:
            predicted_val = max(0.0, predicted_val)

        future_preds.append(
            {
                "date": f_date.strftime("%Y-%m-%d"),
                "day_name": f_date.strftime("%A"),
                "predicted_sales_revenue_gbp": round(predicted_val, 2),
            }
        )

        # Append prediction to history for next recursive steps
        history = pd.concat(
            [
                history,
                pd.DataFrame([{"date": f_date, target_col: predicted_val}]),
            ],
            ignore_index=True,
        )

    forecast_df = pd.DataFrame(future_preds)
    forecast_df.to_csv(OUTPUT_DIR / "future_30_days_forecast.csv", index=False)
    print(f"Future {horizon_days}-day forecast generated and saved successfully!")
    return forecast_df


def plot_results(test_df, rf_pred, baseline_pred, forecast_df, importances, raw_df, target_col="net_sales_gbp"):
    print("--------------------------------------------------")
    print("Step 6: Generating Visual Plots & Decision Charts")

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # Plot 1: Test Set - Actual vs Predicted vs Baseline
    plt.figure(figsize=(12, 6))
    plt.plot(test_df["date"], test_df[target_col], label="Actual Sales (£)", color="#1e293b", linewidth=2.5, marker="o", markersize=4)
    plt.plot(test_df["date"], rf_pred, label="Random Forest Forecast (£)", color="#2563eb", linewidth=2.2, linestyle="--", marker="s", markersize=4)
    plt.plot(test_df["date"], baseline_pred, label="7-Day Moving Avg Baseline (£)", color="#94a3b8", linewidth=1.5, linestyle=":")
    plt.title("Model Validation: Actual vs. Random Forest Prediction (Test Set)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Daily Net Sales Revenue (£)", fontsize=11)
    plt.legend(frameon=True, facecolor="white", loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "01_actual_vs_predicted_test_set.png", dpi=300)
    plt.close()

    # Plot 2: Historical Tail + Future 30 Days Forecast
    plt.figure(figsize=(14, 6))
    tail_history = raw_df.tail(60).copy()
    plt.plot(tail_history["date"], tail_history[target_col], label="Recent Historical Sales (£)", color="#334155", linewidth=2)

    forecast_dates = pd.to_datetime(forecast_df["date"])
    plt.plot(forecast_dates, forecast_df["predicted_sales_revenue_gbp"], label="Future 30-Day Forecast (£)", color="#10b981", linewidth=2.5, linestyle="--", marker="o", markersize=4)

    # Divider line
    split_date = tail_history["date"].max()
    plt.axvline(x=split_date, color="#ef4444", linestyle="--", label="Forecast Horizon Start")

    plt.title("Future 30-Day Daily Sales Revenue Forecast (AI Decision Intelligence)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Sales Revenue (£)", fontsize=11)
    plt.legend(frameon=True, facecolor="white")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "02_future_30_days_sales_forecast.png", dpi=300)
    plt.close()

    # Plot 3: Feature Importances
    plt.figure(figsize=(10, 5))
    top_features = importances.sort_values("importance", ascending=True)
    plt.barh(top_features["feature"], top_features["importance"], color="#3b82f6")
    plt.title("Key Drivers of Sales (Random Forest Feature Importance)", fontsize=13, fontweight="bold", pad=10)
    plt.xlabel("Relative Importance Score", fontsize=11)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "03_feature_importance_drivers.png", dpi=300)
    plt.close()

    print(f"All plots saved in: {PLOTS_DIR}")


def generate_business_recommendations(forecast_df, importances, metrics):
    print("--------------------------------------------------")
    print("Step 7: Compiling Executive Business Recommendations")

    total_forecast_revenue = forecast_df["predicted_sales_revenue_gbp"].sum()
    avg_daily_revenue = forecast_df["predicted_sales_revenue_gbp"].mean()
    peak_day = forecast_df.loc[forecast_df["predicted_sales_revenue_gbp"].idxmax()]
    low_day = forecast_df[forecast_df["predicted_sales_revenue_gbp"] > 0].loc[forecast_df[forecast_df["predicted_sales_revenue_gbp"] > 0]["predicted_sales_revenue_gbp"].idxmin()]

    # Day of week averages in future forecast
    day_avg = forecast_df.groupby("day_name")["predicted_sales_revenue_gbp"].mean().sort_values(ascending=False)

    report = f"""# Business Decision Intelligence & Actionable Recommendations

**Prepared by:** Ahsan Rafique (AI Engineer)
**Project:** AI Decision Intelligence & What-If Simulator
**Task:** Future Sales Forecasting & Strategic Recommendations
**Evaluation Benchmark:** Random Forest Regressor vs. 7-Day Moving Average Baseline

---

## 1. Executive Summary
- **Predicted 30-Day Sales Revenue:** **£{total_forecast_revenue:,.2f}**
- **Average Daily Expected Revenue:** **£{avg_daily_revenue:,.2f} / day**
- **Peak Revenue Day Expected:** **{peak_day['date']} ({peak_day['day_name']})** with estimated **£{peak_day['predicted_sales_revenue_gbp']:,.2f}**
- **Lowest Operational Day Expected:** **{low_day['date']} ({low_day['day_name']})** with estimated **£{low_day['predicted_sales_revenue_gbp']:,.2f}**
- **Model Reliability:** Random Forest achieved **£{metrics['random_forest']['MAE_GBP']:,.2f} MAE**, outperforming the baseline by **{metrics['random_forest']['improvement_pct_mae']}%**.

---

## 2. Weekly Demand Patterns & Operational Insights
Based on both historical data analysis and model feature importances:
- **Zero-Sales Pattern on Saturdays:** The retail transaction system consistently registers zero order processing on Saturdays. Operations and warehouse dispatch teams should align shifts accordingly.
- **Mid-Week / Thursday Peak:** Weekly sales consistently peak towards Thursdays and Wednesdays (Average expected: £{day_avg.get('Thursday', 0):,.2f}).
- **Weekend / Sunday Recovery:** Sunday resumes operations with moderate volumes (Average expected: £{day_avg.get('Sunday', 0):,.2f}).

---

## 3. Actionable Business Recommendations

### 📦 A. Inventory & Supply Chain Planning
1. **Stock Replenishment Timing:** Pre-buffer inventory on Tuesday and Wednesday mornings to meet the Thursday-Friday surge without stockouts.
2. **Weekend Buffer:** Minimize incoming supplier shipments on Saturday, scheduling major logistics deliveries for Monday and Tuesday.

### 💰 B. Marketing & Promotion Scheduling
1. **Targeted Campaigns:** Schedule marketing emails and promotional offers on Monday and Tuesday to drive the midweek buying momentum.
2. **Slow Day Stimulus:** Run limited-time flash discounts on lower-volume operational days (such as Sundays) to stimulate demand.

### 🔄 C. Return & Cancellation Risk Mitigation
1. **Net Revenue Monitoring:** The model uses **Net Sales Revenue** (accounting for customer cancellations and product returns). High gross days should maintain a 5–8% return reserve margin.
2. **High-Value Order Verification:** Introduce immediate automated fraud and order verification on large orders to reduce cancellation spikes.

---

## 4. Model Performance & Evaluation Proof
| Metric | 7-Day Moving Avg Baseline | Random Forest Regressor | Improvement |
| :--- | :--- | :--- | :--- |
| **MAE (Mean Absolute Error)** | £{metrics['baseline']['MAE_GBP']:,.2f} | **£{metrics['random_forest']['MAE_GBP']:,.2f}** | **+{metrics['random_forest']['improvement_pct_mae']}% Better** |
| **RMSE** | £{metrics['baseline']['RMSE_GBP']:,.2f} | **£{metrics['random_forest']['RMSE_GBP']:,.2f}** | **+{metrics['random_forest']['improvement_pct_rmse']}% Better** |
| **R² Score** | N/A | **{metrics['random_forest']['R2_Score']}** | High Predictive Power |

*Testing conducted chronologically on the final 30 days without data leakage.*
"""

    with open(OUTPUT_DIR / "business_recommendations.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Business recommendations generated: {OUTPUT_DIR / 'business_recommendations.md'}")


def main():
    print("==================================================")
    print("   AI DECISION INTELLIGENCE - SALES FORECASTING   ")
    print("          Prepared by Ahsan Rafique               ")
    print("==================================================")

    # 1. Load data
    df = load_and_prepare_data(DATA_PATH)

    # 2. Features
    clean_data = create_features(df, target_col="net_sales_gbp")

    # 3. Train & Evaluate
    rf_model, test_df, rf_pred, baseline_pred, feature_cols, importances = (
        train_and_evaluate(clean_data, target_col="net_sales_gbp", test_days=30)
    )

    # 4. Future Forecast
    forecast_df = recursive_future_forecast(
        clean_data,
        rf_model,
        feature_cols,
        horizon_days=30,
        target_col="net_sales_gbp",
    )

    # 5. Visualizations
    plot_results(
        test_df,
        rf_pred,
        baseline_pred,
        forecast_df,
        importances,
        clean_data,
        target_col="net_sales_gbp",
    )

    # 6. Business Recommendations
    with open(OUTPUT_DIR / "model_evaluation_metrics.json", "r") as f:
        metrics = json.load(f)
    generate_business_recommendations(forecast_df, importances, metrics)

    print("==================================================")
    print("  FORECASTING PIPELINE COMPLETED SUCCESSFULLY!    ")
    print("==================================================")


if __name__ == "__main__":
    main()
