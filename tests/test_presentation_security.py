"""Security regression tests: public users must never switch demo roles on live data."""
import pytest
from starlette.requests import Request

from backend import app as app_module  # Load FastAPI first; it registers backend.demo.
from backend import presentation
from backend import demo


@pytest.fixture
def production(monkeypatch):
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://not-connected.example/db')
    monkeypatch.delenv('AUREVA_DB', raising=False)
    monkeypatch.setenv('AUREVA_PRESENTATION_CODE', 'example-classroom-secret-123')
    monkeypatch.setenv('AUREVA_PRESENTATION_SIGNING_KEY', 'example-signing-key-keep-it-at-least-32-bytes')


def make_request(ticket=''):
    headers=[(b'host',b'aureva-sigma.vercel.app'),
             (b'origin',b'https://aureva-sigma.vercel.app')]
    if ticket:
        headers.append((b'cookie', ('aureva_presentation='+ticket).encode()))
    return Request({'type':'http','method':'GET','path':'/api/demo/status','headers':headers})


def test_public_production_remains_regular_auth(production):
    assert presentation.presentation_enabled()
    token=presentation.push_schema(make_request())
    try:
        assert presentation.selected_schema() is None
        assert demo.enabled() is False
    finally:
        presentation.pop_schema(token)


def test_correct_presentation_ticket_selects_only_isolated_schema(production):
    ticket=presentation.issue_ticket()
    assert presentation.valid_ticket(ticket)
    token=presentation.push_schema(make_request(ticket))
    try:
        assert presentation.selected_schema()=='aureva_presentation'
        assert demo.enabled() is True
    finally:
        presentation.pop_schema(token)
    assert presentation.selected_schema() is None


def test_forged_or_expired_tickets_do_not_enable_roles(production,monkeypatch):
    ticket=presentation.issue_ticket()
    monkeypatch.setattr(presentation.time,'time',lambda:0)
    assert not presentation.valid_ticket(ticket)  # future expiry exceeds 6h
    monkeypatch.undo()


def test_tampering_or_disabled_config_fails_closed(production,monkeypatch):
    ticket=presentation.issue_ticket()
    assert not presentation.valid_ticket(ticket[:-1]+('0' if ticket[-1]!='0' else '1'))
    assert not presentation.code_matches('incorrect-code')
    assert presentation.code_matches('example-classroom-secret-123')
    monkeypatch.delenv('AUREVA_PRESENTATION_SIGNING_KEY')
    assert not presentation.presentation_enabled()
    assert not presentation.valid_ticket(ticket)


def test_strict_same_origin_for_presentation(production):
    req=make_request()
    assert presentation.same_origin(req)
    missing=Request({'type':'http','method':'POST','path':'/api/demo/unlock',
                     'headers':[(b'host',b'aureva-sigma.vercel.app')]})
    assert not presentation.same_origin(missing)


def test_preview_keeps_original_isolated_role_switch(monkeypatch):
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    monkeypatch.setenv('AUREVA_DEMO_SWITCH', '1')
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
    monkeypatch.setenv('DATABASE_URL','postgresql://not-connected.example/db')
    monkeypatch.delenv('AUREVA_DB',raising=False)
    assert demo.enabled()
    assert not presentation.presentation_enabled()


def test_public_demo_ticket_is_scoped_and_can_be_revoked(production,monkeypatch):
    monkeypatch.setenv('AUREVA_PUBLIC_DEMO','1')
    assert presentation.public_demo_enabled()
    public_ticket=presentation.issue_ticket(public=True)
    assert presentation.valid_ticket(public_ticket)
    token=presentation.push_schema(make_request(public_ticket))
    try:
        assert presentation.selected_schema()=='aureva_presentation'
        assert demo.enabled()
    finally:
        presentation.pop_schema(token)
    monkeypatch.delenv('AUREVA_PUBLIC_DEMO')
    assert not presentation.public_demo_enabled()
    assert not presentation.valid_ticket(public_ticket)
    token=presentation.push_schema(make_request(public_ticket))
    try:
        assert presentation.selected_schema() is None
        assert not demo.enabled()
    finally:
        presentation.pop_schema(token)


def test_public_demo_entry_requires_same_origin_without_database(production,monkeypatch):
    from fastapi.testclient import TestClient
    monkeypatch.setenv('AUREVA_PUBLIC_DEMO','1')
    base='https://aureva-sigma.vercel.app'
    web=TestClient(app_module.app,base_url=base)
    try:
        result=web.get('/api/demo/config')
        assert result.status_code==200
        assert result.json()['public_demo'] is True
        # An Origin-less or cross-site request must not mint a demo session.
        missing=web.post('/api/demo/enter',headers={'X-Aureva-Request':'1'},json={})
        assert missing.status_code==403
        evil=web.post('/api/demo/enter',headers={
            'Origin':'https://evil.example','X-Aureva-Request':'1'},json={})
        assert evil.status_code==403
        good=web.post('/api/demo/enter',headers={
            'Origin':base,'X-Aureva-Request':'1'},json={})
        assert good.status_code==200,good.text
        assert good.json()['mode']=='presentation'
        assert 'httponly' in good.headers.get('set-cookie','').lower()
        assert 'secure' in good.headers.get('set-cookie','').lower()
        assert web.get('/api/demo/status').json()['enabled'] is True
    finally:
        web.close()
    monkeypatch.delenv('AUREVA_PUBLIC_DEMO')


def test_global_public_ai_quota_fails_closed(production,monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setenv('AUREVA_PUBLIC_DEMO','1')
    token=presentation.push_schema(make_request(presentation.issue_ticket(public=True)))
    try:
        class FakeDB:
            def __init__(self):self.row=None
            def execute(self,sql,args):
                if sql.startswith('SELECT'):
                    class C:
                        def __init__(self,row):self.row=row
                        def fetchone(self):return self.row
                    return C(self.row)
                self.row={'count':args[1]}
                return None
        db=FakeDB()
        presentation.reserve_public_ai_quota(db,'invoice',daily_limit=2)
        presentation.reserve_public_ai_quota(db,'invoice',daily_limit=2)
        with pytest.raises(HTTPException) as error:
            presentation.reserve_public_ai_quota(db,'invoice',daily_limit=2)
        assert error.value.status_code==429
    finally:
        presentation.pop_schema(token)
