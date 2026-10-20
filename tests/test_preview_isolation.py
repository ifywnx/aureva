"""Verify production schema isolation and preview-specific CSRF policy."""
from fastapi.testclient import TestClient
import pytest

from backend import app as a
from backend import postgres


class FakeConnection:
    def __init__(self):
        self.calls=[]
        self.closed=False

    def execute(self, statement, params=()):
        self.calls.append((statement,params))
        return self

    def close(self):
        self.closed=True


def test_default_production_schema_is_unchanged(monkeypatch):
    monkeypatch.delenv('AUREVA_DB_SCHEMA',raising=False)
    fake=FakeConnection()
    monkeypatch.setattr(postgres.psycopg,'connect',lambda *args,**kwargs:fake)
    db=postgres.Connection('postgresql://example',write=True)
    assert ("SELECT pg_catalog.set_config('search_path', %s, true)",('aureva',)) in fake.calls
    assert ('SELECT pg_advisory_xact_lock(%s)',(724201028,)) in fake.calls
    db.close()


def test_preview_schema_and_lock_are_independent(monkeypatch):
    monkeypatch.setenv('AUREVA_DB_SCHEMA','aureva_preview')
    fake=FakeConnection()
    monkeypatch.setattr(postgres.psycopg,'connect',lambda *args,**kwargs:fake)
    db=postgres.Connection('postgresql://example',write=True)
    assert ("SELECT pg_catalog.set_config('search_path', %s, true)",('aureva_preview',)) in fake.calls
    assert ('SELECT pg_advisory_xact_lock(%s)',(724201029,)) in fake.calls
    db.close()


def test_invalid_postgresql_schema_is_rejected(monkeypatch):
    monkeypatch.setenv('AUREVA_DB_SCHEMA','aureva; DROP SCHEMA aureva CASCADE;')
    fake=FakeConnection()
    monkeypatch.setattr(postgres.psycopg,'connect',lambda *args,**kwargs:fake)
    with pytest.raises(ValueError):
        postgres.Connection('postgresql://example')
    assert fake.closed
    assert fake.calls==[]


def test_same_host_preview_origin_allowed_only_with_preview_schema(monkeypatch,tmp_path):
    monkeypatch.setenv('AUREVA_DB',str(tmp_path/'preview-tests.sqlite'))
    monkeypatch.setattr(a,'DB_PATH',tmp_path/'preview-tests.sqlite')
    monkeypatch.setenv('AUREVA_DB_SCHEMA','aureva_preview')
    monkeypatch.setenv('AUREVA_ORIGIN','http://127.0.0.1:8001')
    a.init_db()
    app=TestClient(a.app,base_url='https://aureva-preview-example.vercel.app',
                   headers={'X-Aureva-Request':'1'})
    assert app.post('/api/auth/register',json={},
        headers={'Origin':'https://aureva-preview-example.vercel.app'}).status_code==422
    assert app.post('/api/auth/register',json={},
        headers={'Origin':'https://external.example'}).status_code==403
    monkeypatch.setenv('AUREVA_DB_SCHEMA','aureva')
    assert app.post('/api/auth/register',json={},
        headers={'Origin':'https://aureva-preview-example.vercel.app'}).status_code==403
