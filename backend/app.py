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
    if request.url.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
        if request.headers.get('X-Aureva-Request') != '1':
            return JSONResponse({'detail':'Yêu cầu không hợp lệ.'}, status_code=403)
        origin = request.headers.get('origin')
        allowed = os.getenv('AUREVA_ORIGIN', 'http://127.0.0.1:8001')
        if origin and origin not in (allowed, 'http://localhost:8001'):
            return JSONResponse({'detail':'Nguồn yêu cầu không được phép.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

def current_user(request: Request):
    token = request.cookies.get('aureva_session', '')
    with connect() as db:
        user = db.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?', (digest(token), int(time.time()))).fetchone()
    if not user: raise HTTPException(401, 'Vui lòng đăng nhập.')
    return dict(user)

def require(user, *roles):
    if user['role'] not in roles: raise HTTPException(403, 'Bạn không có quyền thực hiện thao tác này.')

def campaign_access(db, campaign_id, user):
    campaign = db.execute('SELECT * FROM campaigns WHERE id=?', (campaign_id,)).fetchone()
    if not campaign: raise HTTPException(404, 'Không tìm thấy chiến dịch.')
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
class Decision(Input):
    status: Literal['approved','rejected']
    reason: str = Field(min_length=5,max_length=1000)

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
CASE WHEN cover.campaign_id IS NOT NULL
     THEN '/api/public/campaigns/' || c.id || '/cover?v=' || substr(cover.sha256,1,12)
     ELSE NULL END AS cover_url
FROM campaigns c JOIN users u ON c.owner_id=u.id
LEFT JOIN campaign_covers cover ON cover.campaign_id=c.id'''
@app.get('/api/public/dashboard')
def dashboard():
    with connect() as db:
        campaigns=[dict(r) for r in db.execute(CAMPAIGN_SQL+' ORDER BY c.created DESC')]
    return {'campaigns':campaigns,'raised':sum(c['raised'] for c in campaigns),'spent':sum(c['spent'] for c in campaigns),'contribution_count':sum(c['contribution_count'] for c in campaigns),'integrations':{'ai':'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured','blockchain':'configured' if all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','BLOCKCHAIN_PRIVATE_KEY','AUREVA_CONTRACT_ADDRESS')) else 'not_configured'}}

@app.post('/api/campaigns',status_code=201)
def create_campaign(payload: CampaignInput,user=Depends(current_user)):
    require(user,'manager')
    id=uid()
    with connect(write=True) as db:
        db.execute('INSERT INTO campaigns VALUES(?,?,?,?,?,?,?)',(id,payload.title,payload.description,payload.location,payload.target,user['id'],now()))
        audit(db,user,'campaign.created',id,payload.model_dump())
    return {'id':id}

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
        if not db.execute('SELECT id FROM campaigns WHERE id=?',(id,)).fetchone(): raise HTTPException(404,'Không tìm thấy chiến dịch.')
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
            where=' WHERE c.owner_id=?' if user['role']=='manager' else ''
            args=(user['id'],) if user['role']=='manager' else ()
            donations=db.execute('SELECT d.*, c.title AS campaign_title FROM donations d JOIN campaigns c ON c.id=d.campaign_id'+where+' ORDER BY d.created DESC',args).fetchall()
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

@app.post('/api/campaigns/{id}/expenses',status_code=201)
def expense(id:str,payload:ExpenseInput,user=Depends(current_user)):
    require(user,'manager')
    expense_id=uid()
    with connect(write=True) as db:
        campaign_access(db,id,user)
        db.execute('INSERT INTO expenses(id,campaign_id,creator_id,amount,purpose,vendor,created) VALUES(?,?,?,?,?,?,?)',(expense_id,id,user['id'],payload.amount,payload.purpose,payload.vendor,now()))
        audit(db,user,'expense.submitted',expense_id,payload.model_dump())
    return {'id':expense_id,'status':'pending'}

@app.post('/api/expenses/{id}/decision')
def decide(id:str,payload:Decision,user=Depends(current_user)):
    require(user,'approver')
    with connect(write=True) as db:
        row=db.execute('SELECT * FROM expenses WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Không tìm thấy khoản chi.')
        if row['creator_id']==user['id']: raise HTTPException(403,'Không được tự duyệt khoản chi.')
        if row['status']!='pending': raise HTTPException(409,'Khoản chi đã có quyết định.')
        if payload.status=='approved':
            available=db.execute("SELECT COALESCE((SELECT SUM(amount) FROM donations WHERE campaign_id=? AND status='confirmed'),0)-COALESCE((SELECT SUM(amount) FROM expenses WHERE campaign_id=? AND status='approved'),0)",(row['campaign_id'],row['campaign_id'])).fetchone()[0]
            if row['amount']>available: raise HTTPException(409,'Khoản chi vượt số dư đã đối soát của chiến dịch.')
        from backend.evidence import decision_evidence
        decision_evidence(db,row,user,payload)
        db.execute('UPDATE expenses SET status=?,reason=?,reviewer_id=? WHERE id=?',(payload.status,payload.reason,user['id'],id))
        audit(db,user,'expense.'+payload.status,id,{'amount':row['amount'],'reason':payload.reason,'blockchain':'not_configured'})
    return {'status':payload.status,'blockchain':'not_configured'}

@app.get('/api/health')
def health():
    with connect() as db: db.execute('SELECT 1')
    return {'status':'ok','database':'postgresql' if os.getenv('DATABASE_URL') and not os.getenv('AUREVA_DB') else 'sqlite','ai':'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured','blockchain':'configured' if all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','BLOCKCHAIN_PRIVATE_KEY','AUREVA_CONTRACT_ADDRESS')) else 'not_configured'}

from backend.evidence import register as register_evidence
register_evidence(app)
from backend.chain import register as register_chain
register_chain(app)
from backend.campaign_media import register as register_campaign_media
register_campaign_media(app)
from backend.activity import register as register_activity
register_activity(app)

dist=ROOT/'frontend/dist'
if dist.exists():
    app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/{path:path}')
    def frontend(path:str):
        if path.startswith('api/'): raise HTTPException(404,'Not found')
        return FileResponse(dist/'index.html')
