import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CSV = (
    b"date,product,units,price,unit_cost,marketing_spend,expenses\n"
    b"2024-01-01,Product Alpha,100,50,30,500,1000\n"
    b"2024-01-15,Product Beta,80,40,20,300,500\n"
    b"2024-02-01,Product Alpha,120,50,30,600,1000\n"
    b"2024-02-15,Product Beta,90,40,20,300,500\n"
)

ONLINE_RETAIL_CSV = (
    b"Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
    b"489434,85048,15CM CHRISTMAS GLASS BALL,12,2024-01-01 07:45:00,6.95,13085,United Kingdom\n"
    b"489434,79323P,PINK CHERRY BLOSSOM CUP,8,2024-01-01 07:45:00,1.95,13085,United Kingdom\n"
    b"C489435,22350,CANCELLED ORDER,-5,2024-01-02 09:12:00,2.55,13085,United Kingdom\n"
    b"489436,85123A,WHITE HANGING HEART T-LIGHT,20,2024-02-01 10:20:00,2.95,13078,United Kingdom\n"
)


def _upload(content=SAMPLE_CSV, name="sales.csv"):
    return client.post("/api/upload", files={"file": (name, io.BytesIO(content), "text/csv")})


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["author"] == "Muhammad Arham"


def test_upload_standard_csv():
    res = _upload()
    assert res.status_code == 200
    data = res.json()
    assert "dataset_id" in data
    assert data["filename"] == "sales.csv"
    assert len(data["preview"]) == 4
    q = data["quality"]
    assert q["rows"] == 4
    assert q["columns"] == 7


def test_upload_online_retail_ii_dataset():
    res = _upload(ONLINE_RETAIL_CSV, "online_retail.csv")
    assert res.status_code == 200
    data = res.json()
    assert "dataset_id" in data
    # Notice: C489435 has negative qty and 'C' prefix, so it is filtered out, leaving 3 clean rows
    assert len(data["preview"]) == 3
    assert data["quality"]["rows"] == 3


def test_upload_rejects_bad_extension():
    res = _upload(b"test,data\n1,2\n", "data.txt")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_file_type"


def test_upload_rejects_empty_file():
    res = _upload(b"", "empty.csv")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "empty_file"


def test_analysis_computes_real_metrics():
    up = _upload()
    did = up.json()["dataset_id"]
    res = client.get(f"/api/analysis/{did}")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_id"] == did
    kpi_map = {k["label"]: k["value"] for k in data["kpis"]}
    # Revenue = 100*50 + 80*40 + 120*50 + 90*40 = 5000 + 3200 + 6000 + 3600 = 17800
    assert kpi_map["Total Revenue"] == 17800.0
    assert len(data["trend"]) == 2  # 2024-01 and 2024-02
    assert len(data["by_product"]) == 2
    assert len(data["findings"]) > 0


def test_forecast_generates_future_periods():
    up = _upload()
    did = up.json()["dataset_id"]
    res = client.post("/api/forecast", json={"dataset_id": did, "periods": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data["forecast"]) == 3
    assert data["forecast"][0]["period"] == "2024-03"


def test_simulate_baseline_extraction():
    up = _upload()
    did = up.json()["dataset_id"]
    res = client.get(f"/api/simulate/baseline/{did}")
    assert res.status_code == 200
    b = res.json()
    # Total units = 100 + 80 + 120 + 90 = 390
    assert b["units"] == 390.0
    assert b["price"] > 0
    assert b["unit_cost"] > 0


BASE = {"units": 1000, "price": 100, "unit_cost": 60, "marketing": 5000, "expenses": 10000}


def test_simulate_matches_hand_calculation():
    res = client.post("/api/simulate", json={"baseline": BASE, "changes": {"price_pct": 0.10}})
    assert res.status_code == 200
    r = res.json()
    assert r["original"]["profit"] == 25000.0
    assert r["scenario"]["units"] == 880.0       # 1000 * (1 - 1.2*0.10)
    assert r["scenario"]["revenue"] == 96800.0   # 880 * 110
    assert r["scenario"]["profit"] == 29000.0    # 96800 - 52800 - 5000 - 10000
    assert len(r["notes"]) > 0


def test_simulate_compare_cases_ordering():
    res = client.post("/api/simulate/compare", json={"baseline": BASE, "changes": {"price_pct": 0.10}})
    assert res.status_code == 200
    cases = res.json()["cases"]
    p = {c["case"]: c["result"]["scenario"]["profit"] for c in cases}
    assert p["best"] > p["expected"] > p["worst"]


def test_chat_grounded_in_dataset():
    up = _upload()
    did = up.json()["dataset_id"]
    res = client.post("/api/chat", json={"dataset_id": did, "question": "What is our total revenue?"})
    assert res.status_code == 200
    data = res.json()
    assert "17,800" in data["answer"]
    assert "kpis.total_revenue" in data["context_used"]


def test_validation_error_shape():
    res = client.post("/api/simulate", json={"baseline": {"units": -1, "price": 1, "unit_cost": 1}, "changes": {}})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize("fmt,magic", [("csv", b"Quarterly"), ("pdf", b"%PDF")])
def test_export_pdf_and_csv(fmt, magic):
    payload = {
        "title": "Quarterly Report",
        "kpis": [{"label": "Revenue", "value": 17800.0}],
        "scenarios": [{"name": "Original", "revenue": 17800.0, "cogs": 10400.0, "profit": 4500.0}],
        "assumptions": ["Elasticity: -1.2"],
    }
    res = client.post(f"/api/export?format={fmt}", json=payload)
    assert res.status_code == 200
    assert res.content.startswith(magic)


def test_export_rejects_bad_format():
    res = client.post("/api/export?format=docx")
    assert res.status_code == 422
