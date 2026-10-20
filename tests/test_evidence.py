import io,json,hashlib
from PIL import Image
from fastapi.testclient import TestClient
from tests.test_flows import env,client,campaign
from backend import app as a,evidence

def png():
    raw=io.BytesIO();Image.new('RGB',(80,40),'white').save(raw,format='PNG');return raw.getvalue()
def test_invoice_api_failure_warnings_and_immutable_report(env,monkeypatch):
    m,p,d=client('manager'),client('approver'),client('donor')
    cid=campaign(m)
    did=d.post(f'/api/campaigns/{cid}/donations',json={'amount':1000000,'reference':'invoice-test'}).json()['id']
    m.post(f'/api/donations/{did}/confirm',json={})
    body={'amount':300000,'purpose':'Mua nước và gạo','vendor':'Nhà cung cấp A'}
    eid=m.post(f'/api/campaigns/{cid}/expenses',json=body).json()['id']
    decision={'status':'approved','reason':'Đã kiểm tra nguồn chứng từ'}
    assert p.post(f'/api/expenses/{eid}/decision',json=decision).status_code==409
    assert d.post(f'/api/expenses/{eid}/document',files={'file':('test.png',png())}).status_code==403
    assert m.post(f'/api/expenses/{eid}/document',files={'file':('test.png',b'fake')}).status_code==422
    assert m.post(f'/api/expenses/{eid}/document',files={'file':('test.png',png())}).status_code==201
    assert d.get(f'/api/expenses/{eid}/document').status_code==403
    assert TestClient(a.app).get(f'/api/expenses/{eid}/document').status_code==401
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    assert m.post(f'/api/expenses/{eid}/analyze',json={}).status_code==503
    assert m.get('/api/workspace').json()['expenses'][0]['document']['ai_status']=='failed'
    # Tests stub only the provider boundary; production always makes the real API request.
    invoice={'vendor':'Nhà cung cấp A','invoice_number':'SAME-001','date':'2026-10-16','currency':'VND','total':280000,'readable':True,'notes':'TEST ONLY'}
    monkeypatch.setattr(evidence,'extract_invoice',lambda *args:(invoice,'unit-test-provider'))
    result=m.post(f'/api/expenses/{eid}/analyze',json={})
    assert result.status_code==200,result.text
    assert any('Chênh lệch' in x for x in result.json()['warnings'])
    second=m.post(f'/api/campaigns/{cid}/expenses',json=body).json()['id']
    m.post(f'/api/expenses/{second}/document',files={'file':('duplicate.png',png())})
    result=m.post(f'/api/expenses/{second}/analyze',json={}).json()
    assert any('Trùng nội dung' in x for x in result['warnings'])
    assert any('Trùng số hóa đơn' in x for x in result['warnings'])
    assert p.post(f'/api/expenses/{eid}/decision',json=decision).status_code==200
    assert m.post(f'/api/expenses/{eid}/document',files={'file':('changed.png',png())}).status_code==409
    assert m.post(f'/api/expenses/{eid}/analyze',json={}).status_code==409
    att=m.get(f'/api/public/attestations/{eid}').json()
    assert att['integrity_valid'] and att['status']=='pending' and att['tx_hash'] is None
    monkeypatch.delenv('BLOCKCHAIN_PRIVATE_KEY',raising=False)
    assert m.post(f'/api/attestations/{eid}/anchor',json={}).status_code==503
    report=m.post(f'/api/campaigns/{cid}/reports',json={})
    assert report.status_code==201,report.text
    rid=report.json()['id']
    pdf=m.get(f'/api/public/reports/{rid}/pdf')
    assert pdf.content.startswith(b'%PDF')
    att=m.get(f'/api/public/attestations/{rid}').json()
    assert hashlib.sha256(pdf.content).hexdigest()==att['payload']['pdf_sha256']
    assert att['payload']['report']['campaign']['spent']==300000
    assert 'invoice-test' not in json.dumps(att)
    did=d.post(f'/api/campaigns/{cid}/donations',json={'amount':200000,'reference':'later-donation'}).json()['id']
    m.post(f'/api/donations/{did}/confirm',json={})
    assert m.get('/api/public/dashboard').json()['raised']==1200000
    assert m.get(f'/api/public/attestations/{rid}').json()['payload']['report']['campaign']['raised']==1000000
    assert m.get(f'/api/public/reports/{rid}/pdf').content==pdf.content
    from pathlib import Path
    Path('work').mkdir(exist_ok=True);Path('work/report-qa.pdf').write_bytes(pdf.content)
    with a.connect(write=True) as db:db.execute('UPDATE attestations SET payload=? WHERE entity_id=?',('{}',rid))
    assert not m.get(f'/api/public/attestations/{rid}').json()['integrity_valid']

def test_postgres_integer_totals_are_canonical_json():
    from decimal import Decimal
    from backend.postgres import Row
    row=Row({'raised':Decimal('1000000'),'spent':Decimal('300000')})
    assert evidence.canonical(row)=='{"raised":1000000,"spent":300000}'
