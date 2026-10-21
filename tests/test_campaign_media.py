import io
from PIL import Image
from fastapi.testclient import TestClient
from tests.test_flows import env,client,campaign
from backend import app as a

def picture():
    buf=io.BytesIO()
    Image.new('RGB',(720,480),'#377ade').save(buf,format='PNG')
    return buf.getvalue()

def test_campaign_covers_authorization_persistence_and_public_activity(env):
    manager, donor, approver = client('manager'),client('donor'),client('approver')
    cid=campaign(manager)
    img=picture()
    assert donor.post(f'/api/campaigns/{cid}/cover',files={'file':('cover.png',img,'image/png')}).status_code==403
    assert approver.post(f'/api/campaigns/{cid}/cover',files={'file':('cover.png',img,'image/png')}).status_code==403
    assert manager.post(f'/api/campaigns/{cid}/cover',files={'file':('cover.png',b'fake','image/png')}).status_code==422
    assert manager.post(f'/api/campaigns/{cid}/cover',files={'file':('cover.svg',b'<svg/>','image/svg+xml')}).status_code==422
    uploaded=manager.post(f'/api/campaigns/{cid}/cover',files={'file':('cover.png',img,'image/png')})
    assert uploaded.status_code==200,uploaded.text
    url=uploaded.json()['cover_url']
    fresh=TestClient(a.app)
    assert fresh.get(url).headers['content-type']=='image/webp'
    assert fresh.get(url).content.startswith(b'RIFF')
    assert fresh.get('/api/public/dashboard').json()['campaigns'][0]['cover_url']==url
    a.init_db()
    assert fresh.get(url).content==fresh.get('/api/public/campaigns/'+cid+'/cover').content
    assert fresh.get('/api/public/activity').json()['events']==[]
    did=donor.post(f'/api/campaigns/{cid}/donations',json={'amount':250000,'reference':'cover-01'}).json()['id']
    manager.post(f'/api/donations/{did}/confirm',json={})
    cid2=campaign(client('other'))
    second=donor.post(f'/api/campaigns/{cid2}/donations',json={'amount':90000,'reference':'cover-02'}).json()['id']
    client('other').post(f'/api/donations/{second}/confirm',json={})
    all_events=fresh.get('/api/public/activity').json()
    assert len(all_events['events'])==2
    assert sum(day['confirmed'] for day in all_events['trend'])==340000
    scoped=fresh.get('/api/public/activity',params={'campaign_id':cid}).json()
    assert len(scoped['events'])==1 and scoped['trend'][0]['confirmed']==250000
    assert 'cover-01' not in str(scoped) and 'donor@test.vn' not in str(scoped)
    assert fresh.get('/api/public/activity',params={'campaign_id':'missing'}).status_code==404
