"""Verify the actual deployment entrypoint, including its frontend routes."""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.mark.parametrize("path", ["/api/health", "/api/health/"])
def test_deployed_health(path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize("path", ["/", "/index.html", "/upload.html", "/whatif.html", "/compare.html", "/assistant.html", "/css/style.css", "/js/api.js"])
def test_deployed_frontend(path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content


def test_public_sample_download():
    response = client.get("/data/sample_sales.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert b"date,product" in response.content
    assert client.get("/data/private.csv").status_code == 404


@pytest.mark.parametrize("path", ["/.env", "/.git/config", "/requirements.txt", "/backend/app/core/config.py"])
def test_sources_and_secrets_are_not_served(path):
    assert client.get(path).status_code == 404
