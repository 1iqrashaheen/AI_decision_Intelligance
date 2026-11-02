from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from backend.app.core.database import SessionLocal, User
from backend.app.core.auth import hash_password, verify_password, create_token, require_user
from backend.app.core.errors import APIError
router=APIRouter(prefix='/auth',tags=['authentication'])
class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8,max_length=128)
@router.post('/register')
def register(body: Credentials):
    email=str(body.email).lower().strip()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)):
            raise APIError(409,'email_exists','An account with this email already exists.')
        user=User(email=email,password_hash=hash_password(body.password));db.add(user);db.commit();db.refresh(user)
        return {'access_token':create_token(user.id),'token_type':'bearer','user':{'id':user.id,'email':user.email}}
@router.post('/login')
def login(body: Credentials):
    email=str(body.email).lower().strip()
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if not user or not verify_password(body.password,user.password_hash):
            raise APIError(401,'invalid_credentials','Email or password is incorrect.')
        return {'access_token':create_token(user.id),'token_type':'bearer','user':{'id':user.id,'email':user.email}}
@router.get('/me')
def me(user=Depends(require_user)): return user
