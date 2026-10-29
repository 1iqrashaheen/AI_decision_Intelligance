# Forecasting - Ahsan's part

This folder contains Ahsan's forecasting code and the results he shared. The [original README](SOURCE_README.md) has his model details and evaluation results.

## How the assistant uses these results

Ahsan's saved forecast is for the UCI daily sales data. It covers **10 December 2011 to 8 January 2012**.

Before using it, the assistant checks whether the selected file produces the same daily sales totals as the data used for that forecast. If the data differs, that saved forecast is not used.

These dates are historical. The saved results should not be described as a forecast for the current month.

For other sales files, the backend can make a basic monthly trend estimate. It needs at least three observed months with no gaps. If there is not enough history, the assistant says the forecast is unavailable.

## Files in this folder

| File or folder | What it contains |
|---|---|
| `src/forecasting_pipeline.py` | Ahsan's model training and forecasting code |
| `outputs/future_30_days_forecast.csv` | The daily forecast he shared |
| `outputs/model_evaluation_metrics.json` | His saved test results |
| `outputs/business_recommendations.md` | His original recommendations |
| `training_manifest.json` | The dates and data check used to identify the matching sales history |
| `integration.py` | The function that checks the selected data before returning the saved forecast |

The original recommendation document is kept for reference. Its advice is not automatically applied to every uploaded file. The model has not been retrained as part of connecting this folder to chat.

## Run the forecasting code again

You do not need to train a model just to use the assistant. If you want to rerun Ahsan's pipeline, first get the cleaned data using the steps in the main README.

Then run these commands from the main project folder:

```powershell
python -m pip install -r forecasting/requirements.txt
python forecasting/src/forecasting_pipeline.py
```

The input file is `data/team_cleaned/online_retail_daily_sales.csv`.

New results are saved in `output/forecasting/`. The original shared results in `forecasting/outputs/` are kept unchanged.

The saved forecast assumes no Saturday sales and no negative future revenue. Keep those assumptions with the figures when using them in a page or report.
