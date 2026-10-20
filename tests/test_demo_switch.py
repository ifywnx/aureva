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
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
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
    # Stopping the demo flag immediately invalidates every issued demo cookie.
    monkeypatch.setattr(demo, 'enabled', lambda: False)
    assert web.get('/api/auth/me').status_code == 401
    assert web.post('/api/demo/switch',json={'role':'manager'}).status_code == 404


def test_demo_approver_cannot_touch_normal_campaigns(env, monkeypatch):
    real_manager = client('manager')
    cid = campaign(real_manager)
    expense = real_manager.post(f'/api/campaigns/{cid}/expenses',json={
        'amount':1000,'purpose':'Test approval restrictions','vendor':'Normal manager',
    })
    assert expense.status_code == 201
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
    monkeypatch.setattr(demo, 'enabled', lambda: True)
    web = TestClient(a.app, base_url=BASE, headers={'Origin': BASE, 'X-Aureva-Request':'1'})
    assert web.post('/api/demo/switch',json={'role':'approver'}).status_code == 200
    decision = web.post(f"/api/expenses/{expense.json()['id']}/decision",
        json={'status':'rejected','reason':'Tài khoản demo không được tác động'})
    assert decision.status_code == 403


def test_demo_switch_rejects_cross_site_and_invalid_role(env, monkeypatch):
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
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


def test_demo_donation_simulates_without_payment_and_cannot_reach_real_campaigns(env, monkeypatch):
    # Even in a preview, a simulated donor must not write to normal campaigns.
    real = client('manager')
    normal_cid = campaign(real)
    monkeypatch.setenv('AUREVA_DB_SCHEMA', 'aureva_preview')
    monkeypatch.setattr(demo, 'enabled', lambda: True)
    web = TestClient(a.app, base_url=BASE, headers={
        'Origin': BASE, 'X-Aureva-Request': '1',
    })
    assert web.post('/api/demo/switch', json={'role':'manager'}).status_code==200
    created=web.post('/api/campaigns',json={
        'title':'Cứu trợ bài tập cuối kỳ',
        'location':'Quảng Trị',
        'description':'Chiến dịch mô phỏng phục vụ môn học',
        'target':1000000,
    })
    assert created.status_code==201,created.text
    demo_cid=created.json()['id']
    assert web.post('/api/demo/switch',json={'role':'donor'}).status_code==200
    # This endpoint deliberately has NO bank reference or payment fields.
    payload={'campaign_id':demo_cid,'amount':350000}
    first=web.post('/api/demo/donations',json=payload)
    assert first.status_code==201,first.text
    assert first.json()['simulated'] is True
    assert first.json()['payment_processed'] is False
    assert first.json()['status']=='pending'
    assert web.get('/api/public/dashboard').json()['raised']==0
    assert web.post('/api/demo/donations',json={**payload,'payment_card':'4111111111111111'}).status_code==422
    assert web.post('/api/demo/donations',json={'campaign_id':normal_cid,'amount':1000}).status_code==403
    assert web.post(f'/api/campaigns/{normal_cid}/donations',
        json={'amount':1000,'reference':'DEMO-CROSS-CAMPAIGN'}).status_code==403
    assert web.post('/api/demo/donations',json={'campaign_id':'not-an-id','amount':1}).status_code==422
    assert web.post('/api/demo/donations',json={'campaign_id':demo_cid,'amount':-1}).status_code==422
    with a.connect() as db:
        donation=db.execute('SELECT * FROM donations WHERE id=?',(first.json()['id'],)).fetchone()
        assert donation['reference'].startswith('DEMO-')
        assert donation['status']=='pending'
        assert donation['donor_id']=='aureva_demo_donor_v1'
        assert db.execute('SELECT COUNT(*) FROM donations WHERE campaign_id=?',(normal_cid,)).fetchone()[0]==0
    # Origin is essential for this sensitive preview-only convenience endpoint.
    without_origin=TestClient(a.app,base_url=BASE,headers={'X-Aureva-Request':'1'})
    assert without_origin.post('/api/demo/donations',json=payload).status_code==403
    assert web.post('/api/demo/switch',json={'role':'approver'}).status_code==200
    assert web.post('/api/demo/donations',json=payload).status_code==403
    assert web.post('/api/demo/switch',json={'role':'manager'}).status_code==200
    assert web.post('/api/donations/'+first.json()['id']+'/confirm',json={}).status_code==200
    assert web.get('/api/public/dashboard').json()['raised']==350000


def test_demo_payment_endpoint_is_disabled_outside_preview(env,monkeypatch):
    monkeypatch.setenv('AUREVA_DEMO_SWITCH','1')
    monkeypatch.setenv('VERCEL_ENV','production')
    monkeypatch.setenv('AUREVA_DB_SCHEMA','aureva_preview')
    browser=TestClient(a.app,base_url=BASE,headers={'Origin':BASE,'X-Aureva-Request':'1'})
    assert browser.post('/api/demo/donations',json={
        'campaign_id':'a'*24,'amount':100000,
    }).status_code==404
