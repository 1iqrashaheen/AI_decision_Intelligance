import json
import unittest

import pandas as pd

from business_analysis import analyze_business_data


def sales():
    return pd.DataFrame([
        {"date": "2024-01-01", "product": "A", "units": 10, "price": 20, "unit_cost": 8, "marketing_spend": 5, "expenses": 15},
        {"date": "2024-02-01", "product": "B", "units": 5, "price": 10, "unit_cost": 7, "marketing_spend": 2, "expenses": 3},
    ])


class AnalysisTests(unittest.TestCase):
    def test_hand_calculated_totals(self):
        result = analyze_business_data(sales())
        t = result["totals"]
        self.assertEqual(t["revenue"], 250)
        self.assertEqual(t["cogs"], 115)
        self.assertEqual(t["gross_profit"], 135)
        self.assertEqual(t["total_costs"], 140)
        self.assertEqual(t["profit"], 110)
        self.assertEqual(t["margin_pct"], 44)
        self.assertEqual(result["by_product"][1]["gross_margin"], 30)
        self.assertEqual(result["trend"][1]["revenue_change_pct"], -75)
        json.dumps(result, allow_nan=False)

    def test_missing_costs_never_become_profit(self):
        result = analyze_business_data(sales().drop(columns=["unit_cost", "expenses"]))
        self.assertIsNone(result["totals"]["profit"])
        self.assertIsNone(result["totals"]["gross_profit"])
        self.assertTrue(all(p["gross_margin"] is None for p in result["by_product"]))

    def test_incomplete_costs_not_summed_as_complete(self):
        df = sales(); df.loc[0, "unit_cost"] = float("nan")
        result = analyze_business_data(df)
        self.assertIsNone(result["totals"]["cogs"])
        self.assertIsNone(result["totals"]["profit"])

    def test_retail_aliases_returns_and_stable_product_ids(self):
        df = pd.DataFrame([
            {"InvoiceNo": "1", "StockCode": "X", "Description": "Original", "Quantity": 4, "InvoiceDate": "2024-01-01", "UnitPrice": 10},
            {"InvoiceNo": "C2", "StockCode": "X", "Description": "Renamed", "Quantity": -1, "InvoiceDate": "2024-02-01", "UnitPrice": 10},
        ])
        result = analyze_business_data(df)
        self.assertEqual(result["currency"], "GBP")
        self.assertEqual(result["totals"]["revenue"], 30)
        self.assertEqual(result["totals"]["positive_sales_revenue"], 40)
        self.assertEqual(result["totals"]["negative_transaction_value"], 10)
        self.assertEqual(result["totals"]["products"], 1)
        self.assertEqual(result["anomalies"]["cancellation_rows"], 1)

    def test_duplicate_invalid_dates_and_infinity_reported(self):
        df = sales()
        bad = df.iloc[[0]].copy(); bad["date"] = "invalid"
        infinite = df.iloc[[1]].copy(); infinite["units"] = float("inf")
        result = analyze_business_data(pd.concat([df, df.iloc[[0]], bad, infinite]))
        self.assertEqual(result["quality"]["duplicate_rows_removed"], 1)
        self.assertEqual(result["quality"]["invalid_rows_excluded"], 2)
        self.assertEqual(result["totals"]["revenue"], 250)

    def test_all_products_considered_for_lowest_margin(self):
        df = pd.DataFrame([{"date": "2024-01-01", "product": str(i), "units": 1, "price": 100-i,
                            "unit_cost": 1 if i < 19 else 80} for i in range(20)])
        result = analyze_business_data(df)
        self.assertEqual(len(result["by_product"]), 20)
        self.assertIn("19", next(f for f in result["findings"] if "Lowest" in f))

    def test_missing_month_not_reported_as_monthly_growth(self):
        df = sales(); df.loc[1, "date"] = "2024-03-01"
        result = analyze_business_data(df)
        self.assertIsNone(result["trend"][1]["revenue_change_pct"])

    def test_zero_revenue_margin_unavailable(self):
        df = sales(); df["price"] = 0
        result = analyze_business_data(df)
        self.assertIsNone(result["totals"]["margin_pct"])
        json.dumps(result, allow_nan=False)

    def test_expenses_separate_by_status(self):
        df = pd.DataFrame([{"date": "2026-01-01", "category": "Travel", "amount": 100, "status": "Approved"},
                           {"date": "2026-01-02", "category": "Travel", "amount": -20, "status": "Pending"}])
        result = analyze_business_data(df)
        self.assertEqual(result["dataset_kind"], "expenses")
        self.assertEqual(result["totals"]["recorded_expenses"], 80)
        self.assertEqual(len(result["by_status"]), 2)
        self.assertNotIn("profit", result["totals"])

    def test_inventory_is_potential_value(self):
        df = pd.DataFrame([{"product_id": "P1", "name": "Item", "price": 10, "cost": 6, "stock": 5},
                           {"product_id": "P2", "name": "Other", "price": 0, "cost": 1, "stock": 0}])
        result = analyze_business_data(df)
        self.assertEqual(result["totals"]["inventory_cost_value"], 30)
        self.assertEqual(result["totals"]["inventory_retail_value"], 50)
        self.assertEqual(result["totals"]["out_of_stock_products"], 1)
        self.assertIsNone(result["by_product"][1]["gross_margin"])

    def test_outliers_kept(self):
        df = pd.DataFrame([{"date": f"2024-01-{i+1:02}", "product": "A", "units": 1, "price": x}
                           for i, x in enumerate([10,10,10,10,10,1000])])
        result = analyze_business_data(df)
        self.assertEqual(result["anomalies"]["count"], 1)
        self.assertEqual(result["totals"]["revenue"], 1050)

    def test_unknown_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            analyze_business_data(pd.DataFrame({"arbitrary": [1]}))


if __name__ == "__main__":
    unittest.main()
