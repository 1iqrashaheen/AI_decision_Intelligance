import pytest
import os
import secrets
import tempfile
from pathlib import Path

# Tests must never create accounts or datasets in the developer's real database.
_test_database = tempfile.TemporaryDirectory(prefix='decisionai-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_test_database.name) / 'test.db').as_posix()
os.environ['JWT_SECRET'] = secrets.token_urlsafe(48)
os.environ['APP_ENV'] = 'development'


def pytest_sessionfinish(session, exitstatus):
    from backend.app.core.database import engine
    engine.dispose()
    _test_database.cleanup()


@pytest.fixture(autouse=True)
def offline_api(monkeypatch):
    monkeypatch.setenv("ASSISTANT_MODE", "off")
