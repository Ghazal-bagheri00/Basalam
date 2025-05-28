from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from authlib.integrations.starlette_client import OAuth

from models.models import UserDB
from database.session import get_db
from config.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# نکته: tokenUrl باید به مسیری باشد که توکن JWT را برمی‌گرداند.
# در پروژه شما، این مسیر /v1/login است.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login")

def create_access_token(user: UserDB, expires_delta: timedelta) -> str:
    to_encode = {
        "sub": str(user.id),
        "username": user.username,
        "is_admin": user.is_admin,
        "is_employer": user.is_employer,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="❌ دسترسی غیرمجاز یا توکن نامعتبر است.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
        try:
            user_id = int(user_id)
        except ValueError:
            raise credentials_exception
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

def admin_required(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ فقط مدیران به این بخش دسترسی دارند.",
        )
    return current_user

def employer_required(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if not current_user.is_employer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ فقط کارفرمایان به این بخش دسترسی دارند.",
        )
    return current_user

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)