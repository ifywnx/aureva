"""Preview-only AUREVA role switch for classroom demonstrations.

This feature is intentionally unavailable in production, development and
unconfigured previews. The three identities are dedicated demo accounts,
never real user impersonation. Vercel Deployment Protection must remain on.
"""
import os
import secrets
import time
from typing import Literal

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from backend.app import connect, digest, password_hash, public_user

DEMO_ACCOUNTS = {
    'donor': ('aureva_demo_donor_v1', 'DEMO · Người đóng góp', 'preview-donor@aureva.invalid'),
    'manager': ('aureva_demo_manager_v1', 'DEMO · Người phụ trách', 'preview-manager@aureva.invalid'),
    'approver': ('aureva_demo_approver_v1', 'DEMO · Người phê duyệt', 'preview-approver@aureva.invalid'),
}


def enabled():
    """Fail closed if the site is not a DB-isolated protected Vercel Preview."""
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


def register(app):
    @app.get('/api/demo/status')
    def status():
        return {'enabled': enabled()}

    @app.post('/api/demo/donations', status_code=201)
    def demo_donation(payload: DemoDonationInput, request: Request):
        """Create a simulated pledge; NEVER contact a bank or charge a wallet."""
        if not enabled():
            raise HTTPException(404, 'Chế độ demo không khả dụng.')
        host=request.headers.get('host','').lower()
        if not (host.endswith('.vercel.app') and request.headers.get('origin')=='https://'+host):
            raise HTTPException(403, 'Chỉ cho phép thao tác trên Preview cùng nguồn.')
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
            raise HTTPException(403, 'Chế độ demo chỉ dành cho trình duyệt Vercel Preview.')

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
