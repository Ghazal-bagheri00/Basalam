from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database.session import SessionLocal
from models import models
from config.config import settings  # فرض بر این که تنظیمات اینجا است

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="توکن نامعتبر است یا منقضی شده",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.UserDB).filter(models.UserDB.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
