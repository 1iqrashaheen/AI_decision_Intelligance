import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
CSV = b"date,product,units,price\n2025-01-01,A,10,5\n2025-01-01,A,10,5\n2025-02-01,B,,7\n"


def _upload(content=CSV, name="s.csv"):
    return client.post("/api/upload", files={"file": (name, io.BytesIO(content), "text/csv")})


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_quality_report():
    r = _upload()
    assert r.status_code == 200
    q = r.json()["quality"]
    assert q["rows"] == 3 and q["duplicate_rows"] == 1 and q["missing_cells"] == 1
    assert len(r.json()["preview"]) == 3


def test_upload_rejects_bad_extension():
    assert _upload(b"x", "a.txt").status_code == 400


def test_upload_rejects_empty_and_garbage():
    assert _upload(b"date,product\n", "e.csv").status_code == 422
    assert _upload(b"\x00\x01\x02", "g.xlsx").status_code == 422


def test_analysis_and_chat_need_dataset():
    assert client.get("/api/analysis/nope").status_code == 404
    assert client.post("/api/chat", json={"dataset_id": "nope", "question": "hi"}).status_code == 404
    did = _upload().json()["dataset_id"]
    assert client.get(f"/api/analysis/{did}").status_code == 200
    assert client.post("/api/forecast", json={"dataset_id": did, "periods": 3}).json()["forecast"][2]["period"] == "+3"


BASE = {"units": 1000, "price": 100, "unit_cost": 60, "marketing": 5000, "expenses": 10000}


def test_simulate_matches_hand_calculation():
    r = client.post("/api/simulate", json={"baseline": BASE, "changes": {"price_pct": 0.10}}).json()
    assert r["original"]["profit"] == 25000
    assert r["scenario"]["units"] == 880          # 1000 * (1 - 1.2*0.10)
    assert r["scenario"]["revenue"] == 96800      # 880 * 110
    assert r["scenario"]["profit"] == 29000       # 96800 - 52800 - 5000 - 10000


def test_simulate_compare_three_cases_ordered():
    cases = client.post("/api/simulate/compare", json={"baseline": BASE, "changes": {"price_pct": 0.10}}).json()["cases"]
    p = {c["case"]: c["result"]["scenario"]["profit"] for c in cases}
    assert p["best"] > p["expected"] > p["worst"]


def test_validation_error_shape():
    r = client.post("/api/simulate", json={"baseline": {"units": -1, "price": 1, "unit_cost": 1}, "changes": {}})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize("fmt,magic", [("csv", b"Sample"), ("pdf", b"%PDF")])
def test_export_sample(fmt, magic):
    r = client.post(f"/api/export?format={fmt}")
    assert r.status_code == 200 and r.content.startswith(magic)


def test_export_rejects_bad_format():
    assert client.post("/api/export?format=docx").status_code == 422
