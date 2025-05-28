# controllers/user_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from schemas.schemas import User, UserOut
from models.models import UserDB
from database.session import get_db
from core.auth import get_current_user # بررسی توکن JWT و استخراج کاربر
from core.security import hash_password # ✅ برای هش کردن پسورد در صورت نیاز به آپدیت

router = APIRouter(prefix="/user", tags=["User"])


# 🙋‍♂️ دریافت اطلاعات کاربر فعلی از روی توکن
# این روت باید قبل از روت /{user_id} قرار گیرد تا تداخل ایجاد نشود.
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: UserDB = Depends(get_current_user)):
    """
    دریافت اطلاعات کاربر فعلی بر اساس توکن احراز هویت.
    """
    return current_user


# 🔍 دریافت اطلاعات یک کاربر با شناسه
# این روت باید بعد از روت /me قرار گیرد.
@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    دریافت اطلاعات یک کاربر خاص بر اساس شناسه عددی.
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    return user


# ✏️ به‌روزرسانی اطلاعات کاربر فعلی
@router.put("/me", response_model=UserOut)
def update_current_user(user_update: User, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """
    به‌روزرسانی اطلاعات کاربر فعلی.
    """
    user = current_user

    # فیلدهای قابل به‌روزرسانی را مشخص کنید.
    # به روزرسانی نام، نام خانوادگی، و استان
    user.first_name = user_update.first_name
    user.last_name = user_update.last_name
    user.province = user_update.province

    # اگر رمز عبور جدیدی ارسال شده باشد، آن را هش کرده و به روزرسانی کنید.
    # در User schema، password الزامی است، اما در اینجا اگر کاربر فقط بخواهد
    # نام یا استان را تغییر دهد، نیاز نیست رمز عبور را دوباره ارسال کند.
    # لذا، این قسمت نیاز به بازبینی schema UserCreate برای PUT دارد.
    # فعلاً فرض می‌کنیم UserUpdate schema مجزا نداریم و password در User (UserCreate) اجباری است.
    # اگر در User schema، password Optional باشد، این شرط لازم است:
    # if user_update.password:
    #     user.password = hash_password(user_update.password) # حتماً رمز عبور را هش کنید

    # نقش‌ها (is_admin, is_employer) نباید توسط کاربر عادی از طریق این روت تغییر کنند.
    # user.is_admin = user_update.is_admin # حذف شد
    # user.is_employer = user_update.is_employer # حذف شد

    db.commit()
    db.refresh(user)
    return user


# 🗑️ حذف کاربر با نام کاربری - این روت باید برای ادمین باشد و در admin_controller باشد
# @router.delete("/users/{username}")
# def delete_user(username: str, db: Session = Depends(get_db)):
#     # ... (حذف شد)