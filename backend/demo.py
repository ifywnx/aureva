"""Role switch inside isolated Preview or signed-ticket Production presentation mode.

The Production gate routes every request to a separate PostgreSQL schema.
The three identities are synthetic, never real account impersonation.
Protected Vercel Preview remains supported unchanged.
"""
import os
import secrets
import time
from typing import Literal

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from backend import presentation
from pydantic import BaseModel, ConfigDict, Field

from backend.app import connect, digest, password_hash, public_user

DEMO_ACCOUNTS = {
    'donor': ('aureva_demo_donor_v1', 'DEMO · Người đóng góp', 'preview-donor@aureva.invalid'),
    'manager': ('aureva_demo_manager_v1', 'DEMO · Người phụ trách', 'preview-manager@aureva.invalid'),
    'approver': ('aureva_demo_approver_v1', 'DEMO · Người phê duyệt', 'preview-approver@aureva.invalid'),
}


def enabled():
    """Only isolated Preview or an authorized production presentation session."""
    if presentation.is_presentation_request():
        return True
    return all((
        os.getenv('AUREVA_DEMO_SWITCH') == '1',
        os.getenv('VERCEL_ENV') == 'preview',
        os.getenv('AUREVA_DB_SCHEMA') == 'aureva_preview',
        bool(os.getenv('DATABASE_URL')),
        not os.getenv('AUREVA_DB'),
    ))


class DemoDonationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campaign_id: str = Field(min_length=24,max_length=24,pattern=r'^[0-9a-f]{24}$')
    amount: int = Field(strict=True,gt=0,le=1_000_000_000_000)


class DemoSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['donor', 'manager', 'approver']


class PresentationCode(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1, max_length=128)


def register(app):
    @app.get('/api/demo/config')
    def public_config():
        # No cookie is issued by a GET. Switching roles still requires a
        # same-origin POST and a short-lived signed presentation ticket.
        return {'public_demo': presentation.public_demo_enabled()}

    @app.post('/api/demo/enter')
    def public_enter(request: Request, response: Response):
        if not presentation.public_demo_enabled():
            raise HTTPException(404, 'Chế độ DEMO công khai chưa được bật.')
        if not presentation.same_origin(request):
            raise HTTPException(403, 'Chỉ được vào DEMO từ chính website AUREVA.')
        response.set_cookie(
            presentation.COOKIE, presentation.issue_ticket(public=True),
            httponly=True, samesite='strict', secure=True,
            max_age=presentation.LIFETIME,
        )
        response.delete_cookie('aureva_session', path='/')
        return {'enabled':True,'mode':'presentation'}

    @app.get('/api/demo/status')
    def status():
        # Preserve the stable disabled response for existing clients and tests.
        if not enabled():
            return {'enabled': False}
        mode = 'presentation' if presentation.is_presentation_request() else 'preview'
        return {'enabled': True, 'mode': mode}

    @app.post('/api/demo/unlock')
    def unlock(payload: PresentationCode, request: Request, response: Response):
        if not presentation.presentation_enabled():
            raise HTTPException(503, 'Chế độ thuyết trình chưa được cấu hình.')
        if not presentation.same_origin(request):
            raise HTTPException(403, 'Chế độ thuyết trình chỉ chấp nhận trình duyệt cùng nguồn.')
        from backend.app import digest
        ip = request.client.host if request.client else 'unknown'
        abuse_key = 'presentation-pin:' + digest(ip)
        now = int(time.time())
        correct = presentation.code_matches(payload.code)
        with connect(write=True) as db:
            attempt = db.execute('SELECT count,expires FROM attempts WHERE key=?', (abuse_key,)).fetchone()
            active = bool(attempt and attempt['expires'] > now)
            count = int(attempt['count']) if active else 0
            if count >= 10:
                return JSONResponse({'detail':'Đã nhập sai quá nhiều lần. Thử lại sau 15 phút.'}, status_code=429)
            if not correct:
                db.execute(
                    'INSERT INTO attempts(key,count,expires) VALUES(?,?,?) '
                    'ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires',
                    (abuse_key, count + 1, int(attempt['expires']) if active else now + 900),
                )
            else:
                db.execute('DELETE FROM attempts WHERE key=?', (abuse_key,))
        if not correct:
            return JSONResponse({'detail':'Mã truy cập thuyết trình không đúng.'}, status_code=403)
        response.set_cookie(presentation.COOKIE, presentation.issue_ticket(),
                            httponly=True, secure=True, samesite='strict',
                            max_age=presentation.LIFETIME)
        # Do not send a production login session into the demo schema.
        response.delete_cookie('aureva_session', path='/')
        return {'enabled':True,'mode':'presentation'}

    @app.post('/api/demo/lock')
    def lock(request: Request, response: Response):
        if not presentation.is_presentation_request() or not presentation.same_origin(request):
            raise HTTPException(403, 'Không có phiên thuyết trình hợp lệ.')
        old = request.cookies.get('aureva_session', '')
        if old:
            with connect(write=True) as db:
                db.execute('DELETE FROM sessions WHERE token=?', (digest(old),))
        response.delete_cookie(presentation.COOKIE, path='/')
        response.delete_cookie('aureva_session', path='/')
        return {'enabled':False}

    @app.post('/api/demo/donations', status_code=201)
    def demo_donation(payload: DemoDonationInput, request: Request):
        """Create a simulated pledge; NEVER contact a bank or charge a wallet."""
        if not enabled():
            raise HTTPException(404, 'Chế độ demo không khả dụng.')
        host=request.headers.get('host','').lower()
        if not (host.endswith('.vercel.app') and request.headers.get('origin')=='https://'+host):
            raise HTTPException(403, 'Yêu cầu DEMO phải đến từ đúng tên miền.')
        from backend.app import current_user, DonationInput, donate
        user=current_user(request)
        if user['id']!='aureva_demo_donor_v1' or user['role']!='donor':
            raise HTTPException(403, 'Chỉ tài khoản Donor DEMO được dùng chức năng này.')
        reference='DEMO-' + secrets.token_hex(12).upper()
        result=donate(payload.campaign_id,DonationInput(amount=payload.amount,reference=reference),user)
        return {**result,'simulated':True,'payment_processed':False}

    @app.post('/api/demo/switch')
    def switch(payload: DemoSelection, request: Request, response: Response):
        if not enabled():
            raise HTTPException(404, 'Chế độ demo không khả dụng.')
        # Same-origin is mandatory: unlike normal requests, a privileged demo
        # account switch must never accept a request with an absent Origin.
        host = request.headers.get('host', '').lower()
        origin = request.headers.get('origin', '')
        if not (host.endswith('.vercel.app') and origin == 'https://' + host):
            raise HTTPException(403, 'Chế độ DEMO chỉ cho phép trình duyệt cùng nguồn.')

        account_id, name, email = DEMO_ACCOUNTS[payload.role]
        old_token = request.cookies.get('aureva_session', '')
        token = secrets.token_urlsafe(32)
        with connect(write=True) as db:
            # Bound shared-demo session creation to avoid high-rate abuse.
            ip = request.client.host if request.client else 'unknown'
            abuse_key = 'demo-switch:' + digest(ip)
            now = int(time.time())
            record = db.execute('SELECT count,expires FROM attempts WHERE key=?',
                                (abuse_key,)).fetchone()
            active = bool(record and record['expires'] > now)
            prior_count = int(record['count']) if active else 0
            if prior_count >= 60:
                raise HTTPException(429, 'Đã đổi tài khoản quá nhiều lần. Thử lại sau 15 phút.')
            db.execute(
                'INSERT INTO attempts(key,count,expires) VALUES(?,?,?) '
                'ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires',
                (abuse_key, prior_count + 1, int(record['expires']) if active else now + 900),
            )
            # Never turn a real account into a demo identity, even if ids collide.
            user = db.execute('SELECT * FROM users WHERE id=?', (account_id,)).fetchone()
            if user:
                if user['role'] != payload.role or user['email'] != email:
                    raise HTTPException(409, 'Trùng định danh demo. Cần quản trị viên kiểm tra.')
            else:
                random_unrecoverable_password = password_hash(secrets.token_urlsafe(48))
                db.execute(
                    'INSERT INTO users(id,name,email,password,role) VALUES(?,?,?,?,?)',
                    (account_id, name, email, random_unrecoverable_password, payload.role),
                )
                user = db.execute('SELECT * FROM users WHERE id=?', (account_id,)).fetchone()
            if old_token:
                db.execute('DELETE FROM sessions WHERE token=?', (digest(old_token),))
            db.execute('INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)',
                       (digest(token), account_id, int(time.time()) + 28800))
        response.set_cookie(
            'aureva_session', token, httponly=True, samesite='strict',
            secure=True, max_age=28800,
        )
        return {**public_user(user), 'demo': True}
