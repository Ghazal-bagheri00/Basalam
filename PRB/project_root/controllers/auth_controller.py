from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import re

# وارد کردن مدل‌ها و شمای مورد نیاز
from schemas.schemas import User, UserOut, Token
from models.models import UserDB
from database.session import get_db

# وارد کردن توابع مربوط به امنیت و احراز هویت
# فرض بر این است که hash_password و verify_password در core.security هستند.
from core.security import hash_password, verify_password 
# فرض بر این است که create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, oauth در core.auth هستند.
from core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, oauth

router = APIRouter() # Router پیش‌فرض برای این کنترلر


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: User, db: Session = Depends(get_db)):
    # اعتبارسنجی ورودی‌ها (می‌تواند با Pydantic Field Validators بهتر انجام شود)
    # Pydantic schema شما (schemas.UserCreate) خودش شامل اعتبارسنجی برای username و password است.
    # بنابراین این اعتبارسنجی‌های دستی اضافی هستند و می‌توانید آنها را حذف کنید.
    # به عنوان مثال، Field(min_length=1) یا @field_validator("username") در schemas.py کافی است.
    
    # حذف اعتبارسنجی‌های تکراری دستی اگر در Pydantic schema انجام شده‌اند
    # if not all([user.username, user.password, user.first_name, user.last_name, user.province]):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="تمام فیلدها الزامی هستند.")

    # # بررسی فرمت شماره تلفن (ایران) - در Pydantic schema (UserBase) انجام می‌شود
    # if not re.match(r'^09\d{9}$', user.username):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
    #                         detail="فرمت شماره همراه معتبر نیست (مثلاً: 09123456789).")

    # # بررسی فرمت رمز عبور: حداقل ۸ کاراکتر، شامل حروف بزرگ، کوچک و عدد - در Pydantic schema (UserCreate) انجام می‌شود
    # if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', user.password):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
    #                         detail="رمز عبور باید حداقل ۸ کاراکتر و شامل حروف بزرگ، کوچک و عدد باشد.")

    # بررسی اینکه آیا کاربر وجود دارد
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="این شماره همراه قبلاً ثبت شده است.")

    # هش کردن رمز عبور
    hashed_pw = hash_password(user.password)

    # ساخت شیء UserDB
    db_user = UserDB(
        username=user.username,
        password=hashed_pw,
        is_admin=user.is_admin,  # Pydantic schema خودش مقدار پیش‌فرض False را می‌دهد
        is_employer=user.is_employer, # Pydantic schema خودش مقدار پیش‌فرض False را می‌دهد
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
    # پیدا کردن کاربر بر اساس نام کاربری (شماره تلفن)
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()

    # اعتبارسنجی رمز عبور
    # نکته: همیشه از verify_password برای بررسی رمز عبور هش شده استفاده کنید.
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="شماره همراه یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # ایجاد توکن دسترسی
    # ✅ اصلاح شده: ارسال مستقیم آبجکت user به create_access_token
    access_token = create_access_token(
        user=user, # ✅ به جای data={...}
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/google")
async def login_via_google(request: Request):
    # مسیر تغییر مسیر برای بازگشت از گوگل
    # نام "auth_google_callback" باید با نام تابع @router.get("/auth/google/callback") مطابقت داشته باشد.
    redirect_uri = request.url_for("auth_google_callback") 
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        username = user_info.get("email")

        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="اطلاعات کاربری گوگل ناقص است.")

        user = db.query(UserDB).filter(UserDB.username == username).first()

        if not user:
            # اگر کاربر وجود ندارد، ایجاد کاربر جدید با داده‌های اولیه
            user = UserDB(
                username=username,
                password="",  # برای کاربرانی که با گوگل وارد می‌شوند، رمز عبور خالی (یا یک هش دلخواه)
                is_admin=False,
                is_employer=False,
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                province="" # بهتر است این فیلد را اجباری کنید یا با یک مقدار پیش‌فرض منطقی پر کنید.
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # ایجاد توکن دسترسی
        # ✅ اصلاح شده: ارسال مستقیم آبجکت user به create_access_token
        access_token = create_access_token(
            user=user, # ✅ به جای data={...}
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        # در محیط توسعه، نمایش جزئیات خطا می‌تواند مفید باشد. در محیط تولید، خطاهای کلی‌تر نمایش دهید.
        print(f"خطا در ورود با گوگل: {e}") # برای دیباگ
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در ورود با گوگل. لطفاً مجدداً تلاش کنید." # پیام عمومی‌تر برای کاربر
        )