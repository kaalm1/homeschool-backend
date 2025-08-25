
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .settings import settings
from app.models.base import SessionLocal
from app.models.user import User
from sqlalchemy import select

bearer = HTTPBearer(auto_error=False)

def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db=Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.execute(select(User).where(User.email==email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
