import importlib
import pytest
from fastapi.testclient import TestClient
from backend import app as a

@pytest.fixture
def env(tmp_path,monkeypatch):
    monkeypatch.delenv('DATABASE_URL',raising=False)
    monkeypatch.setenv('AUREVA_DB',str(tmp_path/'test.db'))
    monkeypatch.setattr(a,'DB_PATH',tmp_path/'test.db')
    a.init_db()
    with a.connect(write=True) as db:
        for role in ('donor','manager','approver','other'):
            db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(role,role,role+'@test.vn',a.password_hash('test-password-123'),role if role!='other' else 'manager'))
    return a

def client(role):
    c=TestClient(a.app,headers={'X-Aureva-Request':'1'})
    assert c.post('/api/auth/login',json={'email':role+'@test.vn','password':'test-password-123'}).status_code==200
    return c

def campaign(c):
    r=c.post('/api/campaigns',json={'title':'Cứu trợ miền Trung','description':'Hỗ trợ nhu yếu phẩm cho người dân','location':'Quảng Trị','target':1000000})
    assert r.status_code==201,r.text
    return r.json()['id']

def test_complete_flow_and_persistence(env):
    manager,donor,approver=client('manager'),client('donor'),client('approver')
    cid=campaign(manager)
    did=donor.post(f'/api/campaigns/{cid}/donations',json={'amount':500000,'reference':'bank-001'}).json()['id']
    assert donor.get('/api/public/dashboard').json()['raised']==0
    assert donor.post(f'/api/donations/{did}/confirm',json={}).status_code==403
    assert client('other').post(f'/api/donations/{did}/confirm',json={}).status_code==403
    assert manager.post(f'/api/donations/{did}/confirm',json={}).status_code==200
    assert manager.post(f'/api/donations/{did}/confirm',json={}).status_code==409
    eid=manager.post(f'/api/campaigns/{cid}/expenses',json={'amount':300000,'purpose':'Mua nước sạch','vendor':'Nhà cung cấp A'}).json()['id']
    from backend import evidence
    from unittest.mock import patch
    import io
    from PIL import Image
    out=io.BytesIO();Image.new('RGB',(40,40),'white').save(out,format='PNG')
    assert manager.post(f'/api/expenses/{eid}/document',files={'file':('invoice.png',out.getvalue(),'image/png')}).status_code==201
    with patch.object(evidence,'extract_invoice',return_value=({'vendor':'Nhà cung cấp A','invoice_number':'TEST','date':'2026-10-16','currency':'VND','total':300000,'readable':True,'notes':'Unit test provider stub'},'test-only')):
        assert manager.post(f'/api/expenses/{eid}/analyze',json={}).status_code==200
    decision={'status':'approved','reason':'Đã đối chiếu khoản chi'}
    assert manager.post(f'/api/expenses/{eid}/decision',json=decision).status_code==403
    assert approver.post(f'/api/expenses/{eid}/decision',json=decision).status_code==200
    assert approver.post(f'/api/expenses/{eid}/decision',json=decision).status_code==409
    a.init_db()  # Reinitialize storage without reseeding or clearing records.
    fresh=TestClient(a.app)
    d=fresh.get('/api/public/dashboard').json()
    assert (d['raised'],d['spent'],d['contribution_count'])==(500000,300000,1)
    public=fresh.get(f'/api/public/campaigns/{cid}').text
    assert 'bank-001' not in public and 'donor@test.vn' not in public
    assert 'not_configured' in fresh.get('/api/health').text
    # New connection still resolves the persistent session.
    assert donor.get('/api/auth/me').status_code==200
    donor.post('/api/auth/logout',json={})
    assert donor.get('/api/auth/me').status_code==401

def test_validation_and_overspend(env):
    m,d,p=client('manager'),client('donor'),client('approver')
    cid=campaign(m)
    for amount in (-1,0,1.5,True):
        assert d.post(f'/api/campaigns/{cid}/donations',json={'amount':amount,'reference':'abc'}).status_code==422
    body={'amount':10,'reference':'unique-code'}
    assert d.post(f'/api/campaigns/{cid}/donations',json=body).status_code==201
    assert d.post(f'/api/campaigns/{cid}/donations',json=body).status_code==409
    eid=m.post(f'/api/campaigns/{cid}/expenses',json={'amount':20,'purpose':'Mua thực phẩm','vendor':'Cửa hàng'}).json()['id']
    assert p.post(f'/api/expenses/{eid}/decision',json={'status':'approved','reason':'Kiểm tra số dư'}).status_code==409
    assert p.post(f'/api/expenses/{eid}/decision',json={'status':'rejected','reason':'Chưa đủ nguồn tiền'}).status_code==200

def test_auth_and_csrf(env):
    c=TestClient(a.app)
    assert c.get('/api/workspace').status_code==401
    assert c.post('/api/auth/register',json={}).status_code==403
    c.headers['X-Aureva-Request']='1'
    b={'name':'Test User','email':'new@test.vn','password':'secure-password'}
    assert c.post('/api/auth/register',json={**b,'role':'approver'}).status_code==422
    assert c.post('/api/auth/register',json=b).status_code==201
    assert c.post('/api/auth/login',json={'email':b['email'],'password':b['password']}).json()['role']=='donor'
    assert c.post('/api/campaigns',json={'title':'Test campaign','description':'A valid description','location':'Hà Nội','target':100}).status_code==403
    assert c.post('/api/auth/logout',json={},headers={'Origin':'https://evil.example'}).status_code==403
    bad={'email':'new@test.vn','password':'incorrect-password'}
    for _ in range(10): assert c.post('/api/auth/login',json=bad).status_code==401
    assert c.post('/api/auth/login',json=bad).status_code==429

def test_database_survives_new_python_process(env):
    import subprocess,sys,os
    m=client('manager')
    cid=campaign(m)
    result=subprocess.run([sys.executable,'-c',"from backend.app import init_db,connect; init_db();\nwith connect() as db: print(db.execute('SELECT id FROM campaigns').fetchone()[0])"],env={**os.environ,'AUREVA_DB':str(a.DB_PATH)},capture_output=True,text=True,check=True)
    assert result.stdout.strip()==cid


def test_campaign_closure_is_audited_and_stops_new_money_operations(env):
    manager, donor, approver, other = client('manager'), client('donor'), client('approver'), client('other')
    cid=campaign(manager)
    assert donor.post(f'/api/campaigns/{cid}/close',json={}).status_code==403
    assert other.post(f'/api/campaigns/{cid}/close',json={}).status_code==403
    d=donor.post(f'/api/campaigns/{cid}/donations',json={'amount':500000,'reference':'closure-001'})
    assert d.status_code==201
    assert manager.post(f'/api/campaigns/{cid}/close',json={}).status_code==409
    assert manager.post(f'/api/donations/{d.json()["id"]}/confirm',json={}).status_code==200
    e=manager.post(f'/api/campaigns/{cid}/expenses',json={'amount':100000,'purpose':'Mua nước cứu trợ','vendor':'Nhà phân phối'})
    assert e.status_code==201
    assert manager.post(f'/api/campaigns/{cid}/close',json={}).status_code==409
    assert approver.post(f'/api/expenses/{e.json()["id"]}/decision',json={'status':'rejected','reason':'Thiếu chứng từ gốc'}).status_code==200
    closed=manager.post(f'/api/campaigns/{cid}/close',json={})
    assert closed.status_code==200,closed.text
    assert closed.json()['status']=='closed'
    assert manager.post(f'/api/campaigns/{cid}/close',json={}).status_code==409
    data=donor.get('/api/public/dashboard').json()
    assert data['campaigns'][0]['is_closed']
    assert donor.get(f'/api/public/campaigns/{cid}').json()['campaign']['is_closed']
    assert donor.post(f'/api/campaigns/{cid}/donations',json={'amount':1000,'reference':'closure-002'}).status_code==409
    assert manager.post(f'/api/campaigns/{cid}/expenses',json={'amount':1000,'purpose':'Hỗ trợ mới','vendor':'Nhà cung cấp'}).status_code==409
    # Public evidence stays available after closing. No storage migration required.
    assert manager.post(f'/api/campaigns/{cid}/reports',json={}).status_code==201
    with env.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM audit WHERE entity_id=? AND action='campaign.closed'",(cid,)).fetchone()[0]==1


def test_manager_can_reject_unverified_donation_without_inflating_ledger(env):
    m,d,p,other=client('manager'),client('donor'),client('approver'),client('other')
    cid=campaign(m)
    item=d.post(f'/api/campaigns/{cid}/donations',json={'amount':150000,'reference':'bank-unverified-001'})
    assert item.status_code==201
    did=item.json()['id']
    assert d.post(f'/api/donations/{did}/reject',json={'reason':'Chưa thấy chuyển tiền'}).status_code==403
    assert p.post(f'/api/donations/{did}/reject',json={'reason':'Chưa thấy chuyển tiền'}).status_code==403
    assert other.post(f'/api/donations/{did}/reject',json={'reason':'Chưa thấy chuyển tiền'}).status_code==403
    assert m.post(f'/api/donations/{did}/reject',json={'reason':'x'}).status_code==422
    rejected=m.post(f'/api/donations/{did}/reject',json={'reason':'Không tìm thấy giao dịch tương ứng'})
    assert rejected.status_code==200,rejected.text
    assert rejected.json()['status']=='rejected'
    assert m.post(f'/api/donations/{did}/reject',json={'reason':'Kiểm tra lại'}).status_code==409
    assert m.post(f'/api/donations/{did}/confirm',json={}).status_code==409
    assert d.get('/api/public/dashboard').json()['raised']==0
    donor_view=d.get('/api/workspace').json()['donations']
    assert donor_view[0]['status']=='rejected'
    with env.connect() as db:
        history=db.execute("SELECT action,detail FROM audit WHERE entity_id=? ORDER BY id DESC",(did,)).fetchone()
    assert history['action']=='donation.rejected'
    assert 'Không tìm thấy giao dịch' in history['detail']
    # Closing a campaign remains possible after its outstanding claim is rejected.
    assert m.post(f'/api/campaigns/{cid}/close',json={}).status_code==200


def test_approver_does_not_receive_private_donation_references(env):
    m,d,p=client('manager'),client('donor'),client('approver')
    cid=campaign(m)
    secret_ref='DONOR-PRIVATE-BANK-REF'
    item=d.post(f'/api/campaigns/{cid}/donations',json={'amount':75000,'reference':secret_ref})
    assert item.status_code==201
    approver_response=p.get('/api/workspace')
    assert approver_response.status_code==200
    assert approver_response.json()['donations']==[]
    assert secret_ref not in approver_response.text
    manager_response=m.get('/api/workspace')
    assert manager_response.status_code==200
    assert secret_ref in manager_response.text
