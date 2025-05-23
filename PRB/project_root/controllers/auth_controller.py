from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import re

from schemas.schemas import User, UserOut, Token
from models.models import UserDB
from database.session import get_db
from core.security import hash_password, verify_password
from core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, oauth

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: User, db: Session = Depends(get_db)):
    # اعتبارسنجی ورودی‌ها
    required_fields = [user.username, user.password, user.first_name, user.last_name, user.province]
    if not all(required_fields):
        raise HTTPException(status_code=400, detail="تمام فیلدها الزامی هستند.")

    if not re.fullmatch(r'^09\d{9}$', user.username):
        raise HTTPException(status_code=400, detail="شماره همراه معتبر نیست (مثلاً 09123456789).")

    if not re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', user.password):
        raise HTTPException(
            status_code=400,
            detail="رمز عبور باید حداقل ۸ کاراکتر و شامل حروف بزرگ، کوچک و عدد باشد."
        )

    # بررسی یکتا بودن
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="این شماره همراه قبلاً ثبت شده است.")

    # ذخیره در دیتابیس
    db_user = UserDB(
        username=user.username,
        password=hash_password(user.password),
        is_admin=getattr(user, "is_admin", False),
        is_employer=getattr(user, "is_employer", False),
        first_name=user.first_name,
        last_name=user.last_name,
        province=user.province
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="شماره همراه یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        user=user,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/google")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        email = user_info.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="ایمیل از گوگل دریافت نشد.")

        user = db.query(UserDB).filter(UserDB.username == email).first()

        if not user:
            user = UserDB(
                username=email,
                password="",  # چون با گوگل وارد شده
                is_admin=False,
                is_employer=False,
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                province=""
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        access_token = create_access_token(
            user=user,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"خطا در ورود با گوگل: {str(e)}"
        )
