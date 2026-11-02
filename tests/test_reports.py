import csv
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from main import app

client = TestClient(app)
SALES = "date,product,units,price,unit_cost,marketing_spend,expenses\n2024-01-01,Alpha,10,20,8,5,15\n2024-02-01,Beta,5,10,7,2,3\n"


def upload(text=SALES, filename="sales.csv"):
    response = client.post("/api/upload", files={"file":(filename,text,"text/csv")})
    assert response.status_code == 200, response.text
    return response.json()["dataset_id"]


def request(dataset_id, **kwargs):
    return {"dataset_id":dataset_id,"title":"Team decision report",**kwargs}


def scenario(name="Price +10%", elasticity=-1.2, case="expected"):
    return {"name":name,"changes":{"price_pct":.10},"assumptions":{"elasticity":elasticity,"marketing_lift":.15},"case":case}


def export(payload, format="csv"):
    return client.post(f"/api/export?format={format}",json=payload)


def rows(response):
    assert response.status_code == 200, response.text
    return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))


def test_csv_uses_real_analysis_and_checked_scenario():
    did = upload()
    p = request(did, scenarios=[{**scenario(),"revenue":999999,"profit":999999}],kpis=[{"label":"Fake metric","value":999999}])
    result = rows(export(p))
    assert ["Total Revenue","250.0"] in result
    assert ["Net Profit","110.0"] in result
    line = next(r for r in result if r and r[0] == "Price +10%" and r[1] == "Estimate")
    assert float(line[3]) == 242
    assert float(line[8]) == 115.8
    assert "999999" not in str(result)
    assert any("Highest net revenue product" in str(r) for r in result)
    assert ["Price elasticity","-1.2"] in result
    assert any("not guaranteed" in str(r) for r in result)


def test_best_expected_worst_use_existing_simulator():
    did = upload()
    result = rows(export(request(did,scenarios=[scenario("Best",-.6,"best"),scenario("Expected",-1.2),scenario("Worst",-1.8,"worst")])))
    profits = {r[0]:float(r[8]) for r in result if len(r)>8 and r[1] == "Estimate"}
    assert profits["Best"] > profits["Expected"] > profits["Worst"]


def test_selected_scenarios_only_and_baseline_only():
    did = upload()
    result = rows(export(request(did,scenarios=[scenario("Selected one")])))
    assert any(r and r[0] == "Selected one" for r in result)
    result = rows(export(request(did)))
    assert any(r[:2] == ["Original (actual)","Actual"] for r in result)
    assert not any(len(r)>1 and r[1] == "Estimate" for r in result)


def test_unknown_costs_export_as_unavailable():
    did = upload("InvoiceNo,StockCode,Quantity,InvoiceDate,UnitPrice\n1,X,4,2024-01-01,10\nC2,X,-1,2024-02-01,10\n")
    result = rows(export(request(did)))
    assert ["Total Revenue","30.0"] in result
    assert ["Net Profit","Unavailable"] in result
    response = export(request(did),"pdf")
    assert response.status_code == 200
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)
    assert "Unavailable" in text and "30.00" in text
    assert export(request(did,scenarios=[scenario()])).status_code == 422


def test_pdf_contains_actuals_assumptions_risks_and_findings():
    did = upload()
    response = export(request(did,scenarios=[scenario()]),"pdf")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert "attachment" in response.headers["content-disposition"]
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)
    for expected in ["Team decision report","250.00","242.00","115.80","Findings","Points to review","Scenario inputs and risks","Data coverage","Price elasticity","not guaranteed"]:
        assert expected in text


def test_long_titles_and_many_scenarios_paginate():
    did = upload()
    response = export(request(did,title="Detailed comparison " * 7,scenarios=[scenario(f"Scenario {i}: " + "long product description " * 3) for i in range(12)]),"pdf")
    assert response.status_code == 200, response.text
    pages = PdfReader(io.BytesIO(response.content)).pages
    assert len(pages) >= 3
    text = "\n".join(p.extract_text() for p in pages)
    assert "Scenario 11" in text
    assert "Assumptions and notes" in text


def test_pdf_text_is_escaped_and_unicode_names_work():
    did = upload()
    response = export(request(did,title="Café <b>Team & costs</b>",scenarios=[scenario("Review <budget> & café")]),"pdf")
    assert response.status_code == 200
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)
    assert "Café <b>Team & costs</b>" in text
    assert "<budget> & café" in text


def test_csv_formula_text_is_not_executable():
    did = upload(SALES.replace("Alpha","=1+1"))
    result = rows(export(request(did,title="=HYPERLINK(\"https://example.invalid\")",scenarios=[scenario("@SUM(1+1)")])))
    assert result[0][0].startswith("'=")
    assert any(r and r[0] == "'@SUM(1+1)" for r in result)
    assert any(r and r[0] == "'=1+1" for r in result)


def test_unknown_dataset_no_sample_fallback():
    assert export(request("missing")).status_code == 404
    assert client.post("/api/export?format=pdf").status_code == 422
    assert export({}).status_code == 422


def test_report_validation():
    did = upload()
    assert export(request(did,title="   ")).status_code == 422
    assert export(request(did,scenarios=[scenario("   ")])).status_code == 422
    assert export(request(did,scenarios=[scenario()]*13)).status_code == 422
    assert export(request(did,scenarios=[{"name":"Old saved totals","revenue":250,"cogs":100,"profit":100}])).status_code == 422
    assert export(request(did),"docx").status_code == 422
    assert export({"kpis":[{"label":"Bad","value":"NaN"}]}).status_code == 422


def test_supplied_legacy_reports_are_labeled():
    response = export({"title":"Supplied report","kpis":[{"label":"Revenue","value":100}],"scenarios":[{"name":"Example","revenue":100,"cogs":60,"profit":20}]})
    result = rows(response)
    assert ["Source","Supplied report figures"] in result
    assert any("not checked" in str(r) for r in result)


@pytest.mark.parametrize("content,expected",[
    ("date,category,amount,status\n2026-01-01,Travel,100,Pending\n","Expense categories"),
    ("name,price,cost,stock\nItem,20,10,5\n","Product results"),
])
def test_expense_and_inventory_reports(content,expected):
    did=upload(content)
    assert any(r and r[0] == expected for r in rows(export(request(did))))
    assert export(request(did),"pdf").status_code == 200


def test_forecast_is_labeled_or_unavailable():
    did=upload()
    result=rows(export(request(did,include_forecast=True)))
    assert any("at least three" in str(r) for r in result)
    did=upload(SALES + "2024-03-01,Alpha,12,20,8,5,15\n")
    result=rows(export(request(did,include_forecast=True)))
    assert any(r and r[0] == "Forecast estimates" for r in result)
    assert any(r and r[0] == "2024-04" for r in result)
