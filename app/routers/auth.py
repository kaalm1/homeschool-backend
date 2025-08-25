
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import User
from ..security import create_access_token, verify_password, get_db
from passlib.hash import bcrypt

router = APIRouter()

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email==data.email)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.email)
    return TokenOut(access_token=token)

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.execute(select(User).where(User.email==data.email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, password_hash=bcrypt.hash(data.password))
    db.add(user); db.commit()
    token = create_access_token(user.email)
    return TokenOut(access_token=token)
