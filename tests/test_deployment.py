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


@pytest.mark.parametrize("path", ["/.env", "/.git/config", "/requirements.txt", "/backend/app/core/config.py"])
def test_sources_and_secrets_are_not_served(path):
    assert client.get(path).status_code == 404
