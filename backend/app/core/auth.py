"""Small dependency-free password hashing and signed bearer-token helpers."""
import base64, hashlib, hmac, json, os, time
import secrets
from pathlib import Path
from fastapi import Header, Request, Depends
from backend.app.core.database import SessionLocal, User
from backend.app.core.errors import APIError

PRODUCTION = os.getenv('APP_ENV', '').lower() == 'production' or bool(os.getenv('VERCEL'))
COOKIE_NAME = 'decisionai_session'

def load_secret():
    configured = os.getenv('JWT_SECRET', '').strip()
    if configured and not configured.lower().startswith(('replace-', 'your_', 'local-development-')):
        if len(configured) < 32:
            raise RuntimeError('JWT_SECRET must contain at least 32 random characters.')
        return configured
    if PRODUCTION:
        raise RuntimeError('Configure a private, random JWT_SECRET before running in production.')
    # Persist the development secret so tokens survive restarts and multiple workers.
    path = Path(__file__).resolve().parents[2] / 'data' / '.auth-secret'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            handle.write(secrets.token_urlsafe(48))
        path.chmod(0o600)
    except FileExistsError:
        pass
    value = path.read_text(encoding='utf-8').strip()
    if len(value) < 32:
        raise RuntimeError('Local authentication secret is invalid. Configure JWT_SECRET privately.')
    return value

SECRET = load_secret()

def set_session(response, token):
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=PRODUCTION,
                        samesite='strict', max_age=86400, path='/')

def hash_password(password: str) -> str:
    salt=os.urandom(16); digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 240000)
    return base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_s,digest_s=encoded.split('$',1); salt=base64.urlsafe_b64decode(salt_s); expected=base64.urlsafe_b64decode(digest_s)
        actual=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,240000)
        return hmac.compare_digest(actual,expected)
    except Exception: return False

def create_token(user_id: int) -> str:
    payload=base64.urlsafe_b64encode(json.dumps({'sub':user_id,'exp':int(time.time())+86400}).encode()).decode().rstrip('=')
    sig=base64.urlsafe_b64encode(hmac.new(SECRET.encode(),payload.encode(),hashlib.sha256).digest()).decode().rstrip('=')
    return payload+'.'+sig

def token_user_id(token: str) -> int:
    try:
        payload,sig=token.split('.',1)
        expected=base64.urlsafe_b64encode(hmac.new(SECRET.encode(),payload.encode(),hashlib.sha256).digest()).decode().rstrip('=')
        if not hmac.compare_digest(sig,expected): raise ValueError()
        data=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
        if int(data['exp']) <= int(time.time()): raise ValueError()
        return int(data['sub'])
    except Exception: raise APIError(401,'invalid_token','Login token is invalid or expired.')

def get_optional_user(request: Request, authorization: str | None = Header(default=None)):
    token = request.cookies.get(COOKIE_NAME)
    if authorization:
        if not authorization.lower().startswith('bearer '): raise APIError(401,'invalid_token','Use a Bearer access token.')
        token = authorization.split(' ',1)[1].strip()
    if not token: return None
    uid=token_user_id(token)
    with SessionLocal() as db:
        user=db.get(User,uid)
        if not user: raise APIError(401,'invalid_token','User account no longer exists.')
        return {'id':user.id,'email':user.email}

def require_user(user=Depends(get_optional_user)):
    if not user: raise APIError(401,'authentication_required','Register or log in and send Authorization: Bearer <token>.')
    return user
