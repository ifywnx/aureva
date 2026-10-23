from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Literal
import hashlib, hmac, os, secrets, sqlite3, time, json
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg import IntegrityError as PostgresIntegrityError
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.presentation import push_schema, pop_schema
from backend import presentation

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv('AUREVA_DB', str(ROOT / 'data/aureva.db')))

def init_db():
    if os.getenv('DATABASE_URL') and not os.getenv('AUREVA_DB'):
        with connect() as db: db.execute('SELECT id FROM users LIMIT 1')
        return
    if os.getenv('VERCEL'):
        raise RuntimeError('Production requires persistent DATABASE_URL; SQLite fallback disabled')
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('donor','manager','approver')));
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS campaigns(id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL, target INTEGER NOT NULL CHECK(target>0), owner_id TEXT NOT NULL REFERENCES users(id), created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS donations(id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id), donor_id TEXT NOT NULL REFERENCES users(id), amount INTEGER NOT NULL CHECK(amount>0), reference TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created TEXT NOT NULL, UNIQUE(campaign_id,reference));
        CREATE TABLE IF NOT EXISTS expenses(id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id), creator_id TEXT NOT NULL REFERENCES users(id), amount INTEGER NOT NULL CHECK(amount>0), purpose TEXT NOT NULL, vendor TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reason TEXT, reviewer_id TEXT REFERENCES users(id), created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES users(id), action TEXT NOT NULL, entity_id TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);
        PRAGMA user_version=1;
        ''')
        from backend.evidence import init_schema
        init_schema(db)
        from backend.campaign_media import init_sqlite
        init_sqlite(db)

@contextmanager
def connect(write=False):
    postgres=bool(os.getenv('DATABASE_URL')) and not os.getenv('AUREVA_DB')
    if postgres:
        from backend.postgres import Connection
        db=Connection(os.environ['DATABASE_URL'],write=write)
    else:
        db = sqlite3.connect(DB_PATH, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
    try:
        if write and not postgres: db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()

def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def uid(): return secrets.token_hex(12)
def digest(token): return hashlib.sha256(token.encode()).hexdigest()
def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
def check_password(password, stored): return hmac.compare_digest(password_hash(password, stored.split(':')[0]), stored)
def audit(db, user, action, entity, detail): db.execute('INSERT INTO audit(actor_id,action,entity_id,detail,created) VALUES(?,?,?,?,?)', (user['id'], action, entity, json.dumps(detail, ensure_ascii=False), now()))
def public_user(row): return {k: row[k] for k in ('id','name','email','role')}

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
app = FastAPI(title='AUREVA API', version='0.1.0', lifespan=lifespan)

@app.middleware('http')
async def guard(request: Request, call_next):
    presentation_token = push_schema(request)
    try:
        if request.url.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
            if request.headers.get('X-Aureva-Request') != '1':
                return JSONResponse({'detail':'Yêu cầu không hợp lệ.'}, status_code=403)
            origin = request.headers.get('origin')
            allowed = os.getenv('AUREVA_ORIGIN', 'http://127.0.0.1:8001')
            if origin and origin not in (allowed, 'http://localhost:8001'):
                # Preview builds have unique URLs. Allow same-host HTTPS origins only on
                # Vercel preview and only when the isolated preview DB schema is active.
                host=request.headers.get('host','').lower()
                same_host_preview=(
                    os.getenv('AUREVA_DB_SCHEMA')=='aureva_preview'
                    and host.endswith('.vercel.app')
                    and origin=='https://'+host
                )
                # The PIN-gated classroom page can also be opened from an
                # immutable Production deployment URL on the same Vercel host.
                same_host_presentation = (
                    request.headers.get('host','').lower().endswith('.vercel.app')
                    and origin == 'https://' + request.headers.get('host','').lower()
                    and (request.url.path in ('/api/demo/unlock', '/api/demo/lock', '/api/demo/enter')
                         or presentation.is_presentation_request())
                    and os.getenv('VERCEL_ENV') == 'production'
                )
                if not (same_host_preview or same_host_presentation):
                    return JSONResponse({'detail':'Nguồn yêu cầu không được phép.'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    finally:
        pop_schema(presentation_token)

def current_user(request: Request):
    token = request.cookies.get('aureva_session', '')
    with connect() as db:
        user = db.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?', (digest(token), int(time.time()))).fetchone()
    if not user: raise HTTPException(401, 'Vui lòng đăng nhập.')
    if user['id'] in ('aureva_demo_donor_v1', 'aureva_demo_manager_v1', 'aureva_demo_approver_v1'):
        from backend.demo import enabled as demo_enabled
        if not demo_enabled():
            raise HTTPException(401, 'Phiên trình diễn đã kết thúc.')
    return dict(user)

def require(user, *roles):
    if user['role'] not in roles: raise HTTPException(403, 'Bạn không có quyền thực hiện thao tác này.')

def campaign_access(db, campaign_id, user):
    campaign = db.execute('SELECT * FROM campaigns WHERE id=?', (campaign_id,)).fetchone()
    if not campaign: raise HTTPException(404, 'Không tìm thấy chiến dịch.')
    if user['id'] == 'aureva_demo_approver_v1' and campaign['owner_id'] != 'aureva_demo_manager_v1':
        raise HTTPException(403, 'Tài khoản trình diễn chỉ truy cập được chiến dịch demo.')
    if user['role'] != 'approver' and campaign['owner_id'] != user['id']:
        raise HTTPException(403, 'Bạn không phụ trách chiến dịch này.')
    return campaign

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
class Login(Input):
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=10,max_length=128)
    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        value=value.lower()
        if '@' not in value or '.' not in value.split('@')[-1] or ' ' in value: raise ValueError('Email không hợp lệ')
        return value
class Register(Login):
    name: str = Field(min_length=2,max_length=100)
class CampaignInput(Input):
    title: str = Field(min_length=5,max_length=160)
    description: str = Field(min_length=10,max_length=3000)
    location: str = Field(min_length=2,max_length=160)
    target: int = Field(strict=True,gt=0,le=1_000_000_000_000)
class DonationInput(Input):
    amount: int = Field(strict=True,gt=0,le=1_000_000_000_000)
    reference: str = Field(min_length=3,max_length=100)
class ExpenseInput(Input):
    amount: int = Field(strict=True,gt=0,le=1_000_000_000_000)
    purpose: str = Field(min_length=5,max_length=1000)
    vendor: str = Field(min_length=2,max_length=200)
class DonationRejection(Input):
    reason: str = Field(min_length=5,max_length=1000)
class Decision(Input):
    status: Literal['approved','rejected']
    reason: str = Field(min_length=5,max_length=1000)
    warnings_acknowledged: bool = False

@app.post('/api/auth/register', status_code=201)
def register(payload: Register):
    with connect(write=True) as db:
        try:
            db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid(),payload.name,payload.email,password_hash(payload.password),'donor'))
        except (sqlite3.IntegrityError,PostgresIntegrityError): raise HTTPException(409,'Email đã được sử dụng.')
    return {'message':'Đã tạo tài khoản đóng góp. Bạn có thể đăng nhập.'}

@app.post('/api/auth/login')
def login(payload: Login, request: Request, response: Response):
    key = digest((request.client.host if request.client else 'local') + ':' + payload.email)
    timestamp = int(time.time())
    with connect(write=True) as db:
        attempt = db.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
        if attempt and attempt['expires'] > timestamp and attempt['count'] >= 10:
            raise HTTPException(429,'Thử lại sau 15 phút.')
        user = db.execute('SELECT * FROM users WHERE email=?',(payload.email,)).fetchone()
        valid = check_password(payload.password, user['password']) if user else check_password(payload.password,password_hash('not-a-real-password'))
        if not user or not valid:
            count = attempt['count']+1 if attempt and attempt['expires']>timestamp else 1
            db.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires',(key,count,timestamp+900))
            # Return rather than raise so the failed-attempt counter is committed.
            return JSONResponse({'detail':'Email hoặc mật khẩu không đúng.'},status_code=401)
        db.execute('DELETE FROM attempts WHERE key=?',(key,))
        token=secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(token),user['id'],timestamp+28800))
        result=public_user(user)
    response.set_cookie('aureva_session', token, httponly=True, samesite='strict', secure=os.getenv('AUREVA_SECURE_COOKIE')=='1', max_age=28800)
    return result

class QuickLogin(Input):
    role: Literal['donor', 'manager', 'approver']
    team_code: str = Field(min_length=1, max_length=128)

@app.post('/api/auth/quick-login')
def quick_login(payload: QuickLogin, request: Request, response: Response):
    """Sign in to an existing production account; never create or impersonate a role."""
    expected = os.getenv('AUREVA_TEAM_ACCESS_CODE', '')
    if len(expected) < 16:
        raise HTTPException(503, 'Đăng nhập nhanh chưa được quản trị viên cấu hình.')
    ip = request.client.host if request.client else 'unknown'
    key = 'team-quick:' + digest(ip)
    timestamp = int(time.time())
    with connect(write=True) as db:
        attempt = db.execute('SELECT count,expires FROM attempts WHERE key=?', (key,)).fetchone()
        if attempt and attempt['expires'] > timestamp and attempt['count'] >= 5:
            return JSONResponse({'detail':'Quá nhiều lần thử. Vui lòng thử lại sau 15 phút.'}, status_code=429)
        if not hmac.compare_digest(payload.team_code, expected):
            count = attempt['count']+1 if attempt and attempt['expires'] > timestamp else 1
            db.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires', (key,count,timestamp+900))
            return JSONResponse({'detail':'Mã truy cập nhóm không đúng.'}, status_code=401)
        email = os.getenv('AUREVA_QUICK_'+payload.role.upper()+'_EMAIL', '').strip().lower()
        if not email:
            raise HTTPException(503, 'Chưa cấu hình tài khoản cho vai trò này.')
        user = db.execute('SELECT * FROM users WHERE email=? AND role=?', (email,payload.role)).fetchone()
        if not user or user['id'].startswith('aureva_demo_'):
            raise HTTPException(503, 'Tài khoản thật chưa được tạo hoặc vai trò chưa đúng.')
        db.execute('DELETE FROM attempts WHERE key=?', (key,))
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions VALUES(?,?,?)', (digest(token),user['id'],timestamp+28800))
        result = public_user(user)
    response.set_cookie('aureva_session',token,httponly=True,samesite='strict',secure=os.getenv('AUREVA_SECURE_COOKIE')=='1' or bool(os.getenv('VERCEL')),max_age=28800)
    return result

@app.get('/api/auth/me')
def me(user=Depends(current_user)): return public_user(user)
@app.post('/api/auth/logout')
def logout(request: Request,response: Response):
    with connect(write=True) as db: db.execute('DELETE FROM sessions WHERE token=?',(digest(request.cookies.get('aureva_session','')),))
    response.delete_cookie('aureva_session')
    return {'ok':True}

CAMPAIGN_SQL='''SELECT c.*, u.name AS manager_name,
COALESCE((SELECT SUM(amount) FROM donations WHERE campaign_id=c.id AND status='confirmed'),0) AS raised,
COALESCE((SELECT SUM(amount) FROM expenses WHERE campaign_id=c.id AND status='approved'),0) AS spent,
(SELECT COUNT(*) FROM donations WHERE campaign_id=c.id AND status='confirmed') AS contribution_count,
EXISTS(SELECT 1 FROM audit a WHERE a.entity_id=c.id AND a.action='campaign.closed') AS is_closed,
CASE WHEN cover.campaign_id IS NOT NULL
     THEN '/api/public/campaigns/' || c.id || '/cover?v=' || substr(cover.sha256,1,12)
     ELSE NULL END AS cover_url
FROM campaigns c JOIN users u ON c.owner_id=u.id
LEFT JOIN campaign_covers cover ON cover.campaign_id=c.id'''
@app.get('/api/public/dashboard')
def dashboard():
    with connect() as db:
        campaigns=[dict(r) for r in db.execute(CAMPAIGN_SQL+' ORDER BY c.created DESC')]
    return {'campaigns':campaigns,'raised':sum(c['raised'] for c in campaigns),'spent':sum(c['spent'] for c in campaigns),'contribution_count':sum(c['contribution_count'] for c in campaigns),'integrations':{'ai':'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured','blockchain':'configured' if all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','AUREVA_CONTRACT_ADDRESS')) else 'not_configured'}}

@app.post('/api/campaigns',status_code=201)
def create_campaign(payload: CampaignInput,user=Depends(current_user)):
    require(user,'manager')
    id=uid()
    is_demo_manager = user['id'] == 'aureva_demo_manager_v1' and user['email'] == 'preview-manager@aureva.invalid'
    title = '[DEMO] ' + payload.title[:153] if is_demo_manager else payload.title
    with connect(write=True) as db:
        db.execute('INSERT INTO campaigns VALUES(?,?,?,?,?,?,?)',(id,title,payload.description,payload.location,payload.target,user['id'],now()))
        audit(db,user,'campaign.created',id,{**payload.model_dump(),'is_demo':is_demo_manager})
    return {'id':id}

def ensure_campaign_active(db,id):
    """Lifecycle events are append-only in audit: no production schema migration."""
    if db.execute("SELECT 1 FROM audit WHERE entity_id=? AND action='campaign.closed' LIMIT 1",(id,)).fetchone():
        raise HTTPException(409,'Chiến dịch đã kết thúc, không nhận thêm đóng góp hoặc đề xuất chi.')

@app.post('/api/campaigns/{id}/close')
def close_campaign(id:str,user=Depends(current_user)):
    require(user,'manager')
    with connect(write=True) as db:
        campaign_access(db,id,user)
        ensure_campaign_active(db,id)
        pending=db.execute("""SELECT
            (SELECT COUNT(*) FROM donations WHERE campaign_id=? AND status='pending')+
            (SELECT COUNT(*) FROM expenses WHERE campaign_id=? AND status='pending')""",(id,id)).fetchone()[0]
        if pending:
            raise HTTPException(409,'Cần đối soát hoặc xử lý tất cả đóng góp và khoản chi đang chờ trước khi kết thúc.')
        audit(db,user,'campaign.closed',id,{'status':'closed'})
    return {'id':id,'status':'closed'}

@app.get('/api/public/campaigns/{id}')
def campaign_detail(id:str):
    with connect() as db:
        row=db.execute(CAMPAIGN_SQL+' WHERE c.id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Không tìm thấy chiến dịch.')
        # No donor names, emails, or bank references in public reports.
        donations=[dict(r) for r in db.execute("SELECT id,amount,created FROM donations WHERE campaign_id=? AND status='confirmed' ORDER BY created DESC",(id,))]
        expenses=[dict(r) for r in db.execute("SELECT id,amount,purpose,status,reason,created FROM expenses WHERE campaign_id=? AND status IN ('approved','rejected') ORDER BY created DESC",(id,))]
    return {'campaign':dict(row),'donations':donations,'expenses':expenses}

@app.post('/api/campaigns/{id}/donations',status_code=201)
def donate(id:str,payload:DonationInput,user=Depends(current_user)):
    require(user,'donor')
    donation_id=uid()
    with connect(write=True) as db:
        campaign=db.execute('SELECT id,owner_id FROM campaigns WHERE id=?',(id,)).fetchone()
        if not campaign: raise HTTPException(404,'Không tìm thấy chiến dịch.')
        # Never let a classroom demo identity create a claim in a real campaign.
        if user['id']=='aureva_demo_donor_v1' and campaign['owner_id']!='aureva_demo_manager_v1':
            raise HTTPException(403,'Tài khoản trình diễn chỉ được ghi nhận trong chiến dịch DEMO.')
        ensure_campaign_active(db,id)
        try: db.execute('INSERT INTO donations(id,campaign_id,donor_id,amount,reference,created) VALUES(?,?,?,?,?,?)',(donation_id,id,user['id'],payload.amount,payload.reference,now()))
        except (sqlite3.IntegrityError,PostgresIntegrityError): raise HTTPException(409,'Mã tham chiếu đã tồn tại trong chiến dịch.')
        audit(db,user,'donation.submitted',donation_id,{'amount':payload.amount})
    return {'id':donation_id,'status':'pending'}

@app.get('/api/workspace')
def workspace(user=Depends(current_user)):
    with connect() as db:
        if user['role']=='donor':
            donations=db.execute('SELECT d.*, c.title AS campaign_title FROM donations d JOIN campaigns c ON c.id=d.campaign_id WHERE d.donor_id=? ORDER BY d.created DESC',(user['id'],)).fetchall()
            expenses=[]
        else:
            demo_approver = user['id'] == 'aureva_demo_approver_v1'
            where = ' WHERE c.owner_id=?' if (user['role']=='manager' or demo_approver) else ''
            args = ('aureva_demo_manager_v1',) if demo_approver else (user['id'],) if user['role']=='manager' else ()
            # Approvers inspect expense evidence only. Donor bank references and
            # identities must never enter the approver workspace API response.
            donations=(db.execute('SELECT d.*, c.title AS campaign_title FROM donations d JOIN campaigns c ON c.id=d.campaign_id'+where+' ORDER BY d.created DESC',args).fetchall()
                if user['role']=='manager' else [])
            expenses=db.execute('SELECT e.*, c.title AS campaign_title FROM expenses e JOIN campaigns c ON c.id=e.campaign_id'+where+' ORDER BY e.created DESC',args).fetchall()
    from backend.evidence import doc_public
    with connect() as db:
        detailed=[]
        for r in expenses:
            item=dict(r)
            item['document']=doc_public(db,r)
            a=db.execute('SELECT digest,status,tx_hash FROM attestations WHERE entity_id=?',(r['id'],)).fetchone()
            item['attestation']=dict(a) if a else None
            detailed.append(item)
    return {'donations':[dict(r) for r in donations],'expenses':detailed}

@app.post('/api/donations/{id}/confirm')
def confirm_donation(id:str,user=Depends(current_user)):
    require(user,'manager')
    with connect(write=True) as db:
        row=db.execute('SELECT * FROM donations WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Không tìm thấy khoản đóng góp.')
        campaign_access(db,row['campaign_id'],user)
        if row['status']!='pending': raise HTTPException(409,'Khoản đóng góp đã được đối soát.')
        db.execute("UPDATE donations SET status='confirmed' WHERE id=?",(id,))
        audit(db,user,'donation.confirmed',id,{'amount':row['amount']})
    return {'ok':True}

@app.post('/api/donations/{id}/reject')
def reject_donation(id:str,payload:DonationRejection,user=Depends(current_user)):
    """Manual reconciliation can decline an unsupported transfer claim."""
    require(user,'manager')
    with connect(write=True) as db:
        row=db.execute('SELECT * FROM donations WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Không tìm thấy khoản đóng góp.')
        campaign_access(db,row['campaign_id'],user)
        if row['status']!='pending':
            raise HTTPException(409,'Khoản đóng góp đã được xử lý, không thể từ chối lại.')
        db.execute("UPDATE donations SET status='rejected' WHERE id=?",(id,))
        audit(db,user,'donation.rejected',id,{'reason':payload.reason})
    return {'id':id,'status':'rejected'}

@app.post('/api/campaigns/{id}/expenses',status_code=201)
def expense(id:str,payload:ExpenseInput,user=Depends(current_user)):
    require(user,'manager')
    expense_id=uid()
    with connect(write=True) as db:
        campaign_access(db,id,user)
        ensure_campaign_active(db,id)
        db.execute('INSERT INTO expenses(id,campaign_id,creator_id,amount,purpose,vendor,created) VALUES(?,?,?,?,?,?,?)',(expense_id,id,user['id'],payload.amount,payload.purpose,payload.vendor,now()))
        audit(db,user,'expense.submitted',expense_id,payload.model_dump())
    return {'id':expense_id,'status':'pending'}

@app.post('/api/expenses/{id}/decision')
def decide(id:str,payload:Decision,user=Depends(current_user)):
    require(user,'approver')
    with connect(write=True) as db:
        row=db.execute('SELECT * FROM expenses WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Không tìm thấy khoản chi.')
        if user['id']=='aureva_demo_approver_v1':
            demo_campaign=db.execute('SELECT owner_id FROM campaigns WHERE id=?',(row['campaign_id'],)).fetchone()
            if not demo_campaign or demo_campaign['owner_id']!='aureva_demo_manager_v1':
                raise HTTPException(403,'Tài khoản trình diễn chỉ được duyệt chiến dịch demo.')
        if row['creator_id']==user['id']: raise HTTPException(403,'Không được tự duyệt khoản chi.')
        if row['status']!='pending': raise HTTPException(409,'Khoản chi đã có quyết định.')
        if payload.status=='approved':
            available=db.execute("SELECT COALESCE((SELECT SUM(amount) FROM donations WHERE campaign_id=? AND status='confirmed'),0)-COALESCE((SELECT SUM(amount) FROM expenses WHERE campaign_id=? AND status='approved'),0)",(row['campaign_id'],row['campaign_id'])).fetchone()[0]
            if row['amount']>available: raise HTTPException(409,'Khoản chi vượt số dư đã đối soát của chiến dịch.')
        from backend.evidence import decision_evidence
        alerts = decision_evidence(db,row,user,payload)
        db.execute('UPDATE expenses SET status=?,reason=?,reviewer_id=? WHERE id=?',(payload.status,payload.reason,user['id'],id))
        audit(db,user,'expense.'+payload.status,id,{
            'amount':row['amount'],'reason':payload.reason,
            'warnings_count':len(alerts),'warnings_acknowledged':payload.status=='approved' and payload.warnings_acknowledged,
            'blockchain':'pending'
        })
    return {'status':payload.status,'blockchain':'pending','warnings_count':len(alerts)}

@app.get('/api/health')
def health():
    with connect() as db: db.execute('SELECT 1')
    return {'status':'ok','database':'postgresql' if os.getenv('DATABASE_URL') and not os.getenv('AUREVA_DB') else 'sqlite','ai':'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured','blockchain':'configured' if all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','AUREVA_CONTRACT_ADDRESS')) else 'not_configured'}

from backend.evidence import register as register_evidence
register_evidence(app)
from backend.chain import register as register_chain
register_chain(app)
from backend.campaign_media import register as register_campaign_media
register_campaign_media(app)
from backend.activity import register as register_activity
register_activity(app)
from backend.assistant import register as register_assistant
register_assistant(app)
from backend.demo import register as register_demo
register_demo(app)

dist=ROOT/'frontend/dist'
if dist.exists():
    app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/{path:path}')
    def frontend(path:str):
        if path.startswith('api/'): raise HTTPException(404,'Not found')
        # Only reviewed public static artifacts may be served by the API process.
        # No user-controlled filesystem paths or private configuration files.
        if path in ('deploy-sepolia.html','aureva-registry-artifact.json'):
            return FileResponse(dist/path, media_type='text/html' if path.endswith('.html') else 'application/json')
        return FileResponse(dist/'index.html')
