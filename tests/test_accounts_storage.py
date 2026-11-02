"""Account isolation and real database read-back, beyond the in-process cache."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from sqlalchemy.exc import OperationalError

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from backend.app.core import auth, store
from backend.app.core.database import SessionLocal, User

ROOT = Path(__file__).resolve().parents[1]
SALES = (ROOT / 'samples/sales.csv').read_bytes()


@pytest.fixture
def owner():
    with TestClient(app) as client:
        email = f'{uuid.uuid4().hex}@example.com'
        result = client.post('/api/auth/register', json={'email':email, 'password':'Test-password-2026'})
        assert result.status_code == 200
        yield client, email, result.json()


def upload(client, content=SALES, name='sales.csv'):
    response = client.post('/api/upload', files={'file':(name, content, 'text/csv')})
    assert response.status_code == 200, response.text
    return response.json()['dataset_id']


def cold_cache():
    store.DATASETS.clear()
    store.DATASET_METADATA.clear()
    store.DATASET_OWNERS.clear()


def test_registration_login_logout_and_password_storage(owner):
    client, email, registration = owner
    assert client.get('/api/auth/me').json()['email'] == email
    assert 'HttpOnly' in registration_cookie(client)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user.password_hash != 'Test-password-2026'
        assert auth.verify_password('Test-password-2026', user.password_hash)
    assert client.post('/api/auth/register', json={'email':email,'password':'Test-password-2026'}).status_code == 409
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/auth/me').status_code == 401
    assert client.post('/api/auth/login', json={'email':email,'password':'wrong-password'}).status_code == 401
    login = client.post('/api/auth/login', json={'email':email,'password':'Test-password-2026'})
    assert login.status_code == 200
    assert client.get('/api/auth/me').status_code == 200
    with TestClient(app) as api:
        assert api.get('/api/auth/me', headers={'Authorization':'Bearer ' + login.json()['access_token']}).status_code == 200


def registration_cookie(client):
    # Verify response flags, rather than just the presence of a cookie in memory.
    response = client.post('/api/auth/login', json={'email':client.get('/api/auth/me').json()['email'], 'password':'Test-password-2026'})
    cookie = response.headers['set-cookie']
    assert 'SameSite=strict' in cookie
    return cookie


@pytest.mark.parametrize('authorization', ['Basic test', 'Bearer invalid', 'Bearer '])
def test_invalid_tokens(authorization):
    with TestClient(app) as client:
        assert client.get('/api/auth/me', headers={'Authorization':authorization}).status_code == 401


def test_expired_token(owner, monkeypatch):
    client, _, result = owner
    monkeypatch.setattr(auth.time, 'time', lambda: 9999999999)
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer ' + result['access_token']}).status_code == 401


@pytest.mark.parametrize('cold', [False, True])
def test_owned_data_is_private_including_reports(owner, cold):
    owner_client, _, _ = owner
    did = upload(owner_client)
    with TestClient(app) as outsider:
        for authenticated in (False, True):
            if authenticated:
                outsider.post('/api/auth/register', json={'email':f'{uuid.uuid4().hex}@example.com','password':'Different-pass-2026'})
            if cold:
                cold_cache()
            assert outsider.get('/api/analysis/' + did).status_code == 404
            assert outsider.get('/api/simulate/baseline/' + did).status_code == 404
            assert outsider.get('/api/saved/datasets/' + did).status_code in (401, 404)
            assert outsider.post('/api/chat', json={'dataset_id':did,'question':'What is the revenue?'}).status_code == 404
            for format in ('csv', 'pdf'):
                response = outsider.post('/api/export?format=' + format, json={'dataset_id':did,'title':'Private report'})
                assert response.status_code == 404
            assert all(row['id'] != did for row in outsider.get('/api/saved/datasets').json()) if authenticated else True


def test_database_readback_after_cache_clear_and_fresh_process(owner):
    client, _, result = owner
    did = upload(client)
    cold_cache()
    analysis = client.get('/api/analysis/' + did)
    assert analysis.status_code == 200, analysis.text
    assert analysis.json()['totals']['revenue'] == 191080
    assert analysis.json()['totals']['profit'] == 61560
    assert client.get('/api/simulate/baseline/' + did).status_code == 200
    assert client.post('/api/chat', json={'dataset_id':did, 'question':'What is the revenue?'}).status_code == 200
    for format in ('pdf', 'csv'):
        cold_cache()
        response = client.post('/api/export?format=' + format, json={'dataset_id':did,'title':'Restored report'})
        assert response.status_code == 200, response.text
    # A new process has no shared caches and must use the database and same secret.
    code = """
import os
from backend.app.core.store import get_dataset, get_metadata
from backend.app.core.auth import token_user_id
df = get_dataset(os.environ['TEST_DATASET'], owner_id=int(os.environ['TEST_OWNER']), enforce_owner=True)
assert df is not None and len(df) == 48
assert get_metadata(os.environ['TEST_DATASET'])['filename'] == 'sales.csv'
assert token_user_id(os.environ['TEST_TOKEN']) == int(os.environ['TEST_OWNER'])
print('fresh-process persistence passed')
"""
    env = {**os.environ, 'TEST_DATASET':did, 'TEST_OWNER':str(result['user']['id']), 'TEST_TOKEN':result['access_token']}
    process = subprocess.run([sys.executable,'-c',code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert process.returncode == 0, process.stderr


def test_saved_scenarios_crud_and_isolation(owner):
    client, _, _ = owner
    did = upload(client)
    payload = {'name':'Price increase','dataset_id':did,'scenario':{'params':{'price':0.1}}}
    saved = client.post('/api/saved/scenarios', json=payload)
    assert saved.status_code == 200
    sid = saved.json()['id']
    cold_cache()
    assert any(row['id'] == did for row in client.get('/api/saved/datasets').json())
    assert len(client.get('/api/saved/datasets/' + did).json()['rows']) == 48
    assert any(row['id'] == sid for row in client.get('/api/saved/scenarios').json())
    assert client.get(f'/api/saved/scenarios/{sid}').json()['scenario'] == payload['scenario']
    assert client.post('/api/saved/scenarios', json={**payload,'name':'   '}).status_code == 422
    with TestClient(app) as other:
        other.post('/api/auth/register', json={'email':f'{uuid.uuid4().hex}@example.com','password':'Different-pass-2026'})
        assert other.get(f'/api/saved/scenarios/{sid}').status_code == 404
        assert other.delete(f'/api/saved/scenarios/{sid}').status_code == 404
        assert other.post('/api/saved/scenarios', json=payload).status_code == 404
    assert client.delete(f'/api/saved/scenarios/{sid}').status_code == 200
    assert client.get(f'/api/saved/scenarios/{sid}').status_code == 404


@pytest.mark.parametrize('filename,kind,total_key,expected', [
    ('sales.csv','sales','revenue',191080),
    ('expenses.csv','expenses','recorded_expenses',3750),
    ('inventory.csv','inventory','stock_units',78),
])
def test_shipped_samples_and_readback(filename, kind, total_key, expected):
    with TestClient(app) as client:
        response = client.get('/samples/' + filename)
        assert response.status_code == 200
        did = upload(client, response.content, filename)
        cold_cache()
        analysis = client.get('/api/analysis/' + did)
        assert analysis.status_code == 200, analysis.text
        data = analysis.json()
        assert data['dataset_kind'] == kind
        assert data['totals'][total_key] == expected


def test_health_checks_database():
    with TestClient(app) as client:
        assert client.get('/api/health').json()['database'] == 'connected'


def test_health_fails_when_database_is_unavailable(monkeypatch):
    from backend.app.core.database import engine
    def unavailable(*args, **kwargs):
        raise OperationalError('SELECT 1', {}, Exception('unavailable'))
    monkeypatch.setattr(engine, 'connect', unavailable)
    with TestClient(app) as client:
        result = client.get('/api/health')
        assert result.status_code == 503
        assert result.json()['error']['code'] == 'database_unavailable'


def test_blank_database_and_placeholder_secret_work_locally():
    env = {**os.environ, 'DATABASE_URL':' ', 'JWT_SECRET':'replace-with-a-long-random-secret-before-deployment', 'APP_ENV':'development'}
    env.pop('VERCEL', None)
    code = "from backend.app.core.database import DATABASE_URL; from backend.app.core.auth import SECRET; assert DATABASE_URL.startswith('sqlite:///'); assert len(SECRET) >= 32 and not SECRET.startswith('replace-')"
    process = subprocess.run([sys.executable,'-c',code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert process.returncode == 0, process.stderr


def test_production_rejects_placeholder_secret():
    env = {**os.environ, 'JWT_SECRET':'replace-with-a-long-random-secret-before-deployment', 'APP_ENV':'production'}
    result = subprocess.run([sys.executable,'-c','import backend.app.core.auth'], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    assert 'Configure a private, random JWT_SECRET' in result.stderr
