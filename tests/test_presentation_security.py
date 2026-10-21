"""Security regression tests: public users must never switch demo roles on live data."""
import pytest
from starlette.requests import Request

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
