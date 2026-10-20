"""One-tap demo accounts: server sessions, role restrictions, and fail-closed production gate."""
from fastapi.testclient import TestClient
from backend import app as a
from backend import demo
from tests.test_flows import env, client, campaign

BASE = 'https://classroom.aureva.vercel.app'


def test_demo_closed_in_production_even_with_flag(env, monkeypatch):
    monkeypatch.setenv('AUREVA_DEMO_SWITCH', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
    # sqlite fixture intentionally prevents opening this feature.
    assert demo.enabled() is False
    web = TestClient(a.app, base_url=BASE, headers={'Origin': BASE, 'X-Aureva-Request': '1'})
    assert web.get('/api/demo/status').json() == {'enabled': False}
    assert web.post('/api/demo/switch', json={'role': 'manager'}).status_code == 404


def test_demo_one_tap_change_role_without_credentials(env, monkeypatch):
    monkeypatch.setattr(demo, 'enabled', lambda: True)
    web = TestClient(a.app, base_url=BASE, headers={'Origin': BASE, 'X-Aureva-Request': '1'})
    assert web.get('/api/demo/status').json()['enabled'] is True

    manager = web.post('/api/demo/switch', json={'role': 'manager'})
    assert manager.status_code == 200, manager.text
    assert manager.json()['role'] == 'manager'
    assert manager.json()['demo'] is True
    assert manager.cookies.get('aureva_session')
    assert 'httponly' in manager.headers['set-cookie'].lower()
    assert 'secure' in manager.headers['set-cookie'].lower()
    assert web.get('/api/auth/me').json()['id'] == 'aureva_demo_manager_v1'

    made = web.post('/api/campaigns', json={
        'title': 'Kiểm thử cứu trợ', 'description': 'Chiến dịch minh họa trong lớp',
        'location': 'Hà Nội', 'target': 1000000,
    })
    assert made.status_code == 201, made.text
    cid = made.json()['id']
    detail = web.get(f'/api/public/campaigns/{cid}').json()['campaign']
    assert detail['title'].startswith('[DEMO] ')

    donor = web.post('/api/demo/switch', json={'role': 'donor'})
    assert donor.status_code == 200, donor.text
    assert donor.json()['id'] == 'aureva_demo_donor_v1'
    assert web.get('/api/auth/me').json()['role'] == 'donor'
    assert web.post('/api/campaigns', json={
        'title': 'Bị từ chối', 'description': 'Không có quyền quản lý',
        'location': 'Hà Nội', 'target': 1000,
    }).status_code == 403
    created = web.post(f'/api/campaigns/{cid}/donations',json={
        'amount': 100000, 'reference': 'DEMO-TEST-001',
    })
    assert created.status_code == 201, created.text

    approver = web.post('/api/demo/switch', json={'role': 'approver'})
    assert approver.status_code == 200, approver.text
    assert approver.json()['role'] == 'approver'
    assert web.get('/api/auth/me').json()['role'] == 'approver'

    again = web.post('/api/demo/switch', json={'role': 'manager'})
    assert again.status_code == 200
    assert web.get('/api/auth/me').json()['id'] == 'aureva_demo_manager_v1'
    result = web.post('/api/donations/'+created.json()['id']+'/confirm',json={})
    assert result.status_code == 200, result.text
    with a.connect() as db:
        for role in ('donor','manager','approver'):
            assert db.execute('SELECT count(*) FROM users WHERE id=?',
                 ('aureva_demo_'+role+'_v1',)).fetchone()[0] == 1


def test_demo_approver_cannot_touch_normal_campaigns(env, monkeypatch):
    real_manager = client('manager')
    cid = campaign(real_manager)
    expense = real_manager.post(f'/api/campaigns/{cid}/expenses',json={
        'amount':1000,'purpose':'Test approval restrictions','vendor':'Normal manager',
    })
    assert expense.status_code == 201
    monkeypatch.setattr(demo, 'enabled', lambda: True)
    web = TestClient(a.app, base_url=BASE, headers={'Origin': BASE, 'X-Aureva-Request':'1'})
    assert web.post('/api/demo/switch',json={'role':'approver'}).status_code == 200
    decision = web.post(f"/api/expenses/{expense.json()['id']}/decision",
        json={'status':'rejected','reason':'Tài khoản demo không được tác động'})
    assert decision.status_code == 403


def test_demo_switch_rejects_cross_site_and_invalid_role(env, monkeypatch):
    monkeypatch.setattr(demo, 'enabled', lambda: True)
    web = TestClient(a.app,base_url=BASE,headers={'X-Aureva-Request':'1'})
    assert web.post('/api/demo/switch', json={'role':'manager'}).status_code == 403
    fake = TestClient(a.app,base_url=BASE,headers={
        'X-Aureva-Request':'1','Origin':'https://evil.example',
    })
    assert fake.post('/api/demo/switch', json={'role':'manager'}).status_code == 403
    ok = TestClient(a.app,base_url=BASE,headers={
        'X-Aureva-Request':'1','Origin': BASE,
    })
    assert ok.post('/api/demo/switch',json={'role':'admin'}).status_code == 422
    assert ok.post('/api/demo/switch',json={'role':'manager','email':'admin@example.com'}).status_code == 422
