"""Small dependency-free password hashing and signed bearer-token helpers."""
import base64, hashlib, hmac, json, os, time
from fastapi import Header
from backend.app.core.database import SessionLocal, User
from backend.app.core.errors import APIError

SECRET = os.getenv("JWT_SECRET", "")
if len(SECRET) < 32:
    # Local-only fallback; production must configure JWT_SECRET.
    SECRET = SECRET or "local-development-secret-change-before-deploy-9f3a"

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
        if int(data['exp']) < int(time.time()): raise ValueError()
        return int(data['sub'])
    except Exception: raise APIError(401,'invalid_token','Login token is invalid or expired.')

def get_optional_user(authorization: str | None = Header(default=None)):
    if not authorization: return None
    if not authorization.lower().startswith('bearer '): raise APIError(401,'invalid_token','Use a Bearer access token.')
    uid=token_user_id(authorization.split(' ',1)[1].strip())
    with SessionLocal() as db:
        user=db.get(User,uid)
        if not user: raise APIError(401,'invalid_token','User account no longer exists.')
        return {'id':user.id,'email':user.email}

def require_user(authorization: str | None = Header(default=None)):
    user=get_optional_user(authorization)
    if not user: raise APIError(401,'authentication_required','Register or log in and send Authorization: Bearer <token>.')
    return user
