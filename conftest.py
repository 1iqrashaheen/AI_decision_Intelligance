import pytest


@pytest.fixture(autouse=True)
def offline_api(monkeypatch):
    monkeypatch.setenv("ASSISTANT_MODE", "off")
