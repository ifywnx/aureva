"""Production presentation authorization and request-local demo database routing.

The presentation gate NEVER authorizes a request against the live `aureva`
schema. It only selects the isolated `aureva_presentation` schema.
No persistent process-wide environment variable is modified on requests.
"""
from contextvars import ContextVar
import hashlib
import hmac
import os
import secrets
import time

from fastapi import Request

SCHEMA = 'aureva_presentation'
COOKIE = 'aureva_presentation'
LIFETIME = 6 * 3600
_active_schema: ContextVar[str | None] = ContextVar('aureva_request_schema', default=None)


def selected_schema() -> str | None:
    return _active_schema.get()


def presentation_enabled() -> bool:
    """Fail closed unless production has both secrets and a database."""
    return all((
        os.getenv('VERCEL_ENV') == 'production',
        os.getenv('AUREVA_DB_SCHEMA', 'aureva') == 'aureva',
        bool(os.getenv('DATABASE_URL')),
        not os.getenv('AUREVA_DB'),
        (len(os.getenv('AUREVA_PRESENTATION_CODE', '')) >= 12
         or os.getenv('AUREVA_PUBLIC_DEMO') == '1'),
        len(os.getenv('AUREVA_PRESENTATION_SIGNING_KEY', '')) >= 32,
    ))


def public_demo_enabled() -> bool:
    """One kill switch for anonymous classroom admission on Production."""
    return presentation_enabled() and os.getenv('AUREVA_PUBLIC_DEMO') == '1'


def same_origin(request: Request) -> bool:
    """Do not accept Origin-less requests for unlocking/role switching."""
    host = request.headers.get('host', '').lower()
    return host.endswith('.vercel.app') and request.headers.get('origin') == 'https://' + host


def code_matches(entered: str) -> bool:
    expected = os.getenv('AUREVA_PRESENTATION_CODE', '')
    return presentation_enabled() and hmac.compare_digest(
        entered.encode('utf-8'), expected.encode('utf-8')
    )


def _signature(message: str) -> str:
    key = os.environ['AUREVA_PRESENTATION_SIGNING_KEY'].encode('utf-8')
    return hmac.new(key, message.encode('ascii'), hashlib.sha256).hexdigest()


def issue_ticket(public: bool = False) -> str:
    # Separate publicly issued tickets so disabling AUREVA_PUBLIC_DEMO
    # immediately invalidates them without waiting for cookie expiry.
    prefix = 'public.' if public else ''
    payload = prefix + f'{int(time.time()) + LIFETIME}.{secrets.token_hex(16)}'
    return payload + '.' + _signature(payload)


def valid_ticket(token: str) -> bool:
    if not presentation_enabled() or not token or len(token) > 200:
        return False
    parts = token.split('.')
    public_ticket = len(parts) == 4 and parts[0] == 'public'
    if public_ticket:
        if not public_demo_enabled():
            return False
        expiry, nonce, claimed = parts[1:]
    elif len(parts) == 3:
        expiry, nonce, claimed = parts
    else:
        return False
    if not expiry.isdigit() or len(nonce) != 32 or len(claimed) != 64:
        return False
    try:
        age = int(expiry) - int(time.time())
    except ValueError:
        return False
    if age <= 0 or age > LIFETIME:
        return False
    signed_payload = ('public.' if public_ticket else '') + expiry + '.' + nonce
    return hmac.compare_digest(_signature(signed_payload), claimed)


def gated_request(request: Request) -> bool:
    return valid_ticket(request.cookies.get(COOKIE, ''))


def push_schema(request: Request):
    """Return a token that middleware MUST reset in finally."""
    schema = SCHEMA if gated_request(request) else None
    return _active_schema.set(schema)


def pop_schema(token) -> None:
    _active_schema.reset(token)


def is_presentation_request() -> bool:
    return _active_schema.get() == SCHEMA



def reserve_public_ai_quota(db, kind: str, daily_limit: int) -> None:
    """Bound total paid-model calls even when visitors share/VPN-switch IPs.

    Call inside a DB write transaction before requesting a provider.
    Counts are per demo database, per UTC day. PIN-gated private Preview
    and normal Production visitors are unaffected by this budget.
    """
    if not is_presentation_request() or not public_demo_enabled():
        return
    from fastapi import HTTPException
    if kind not in ('invoice', 'assistant'):
        raise ValueError('Unsupported AI quota kind')
    now = int(time.time())
    expires = (now // 86400 + 1) * 86400
    key = f'public-demo-ai:{kind}:{now // 86400}'
    row = db.execute('SELECT count FROM attempts WHERE key=?', (key,)).fetchone()
    count = int(row['count']) if row else 0
    if count >= daily_limit:
        raise HTTPException(429, 'DEMO đã dùng hết lượt AI hôm nay. Hãy thử lại sau hoặc liên hệ nhóm.')
    db.execute(
        'INSERT INTO attempts(key,count,expires) VALUES(?,?,?) '
        'ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires',
        (key, count + 1, expires),
    )
