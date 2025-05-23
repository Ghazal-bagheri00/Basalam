from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from schemas.schemas import User, UserOut
from models.models import UserDB
from database.session import get_db
from dependencies import get_current_user  # بررسی توکن JWT و استخراج کاربر

router = APIRouter()


# 📋 دریافت لیست همه کاربران (برای ادمین‌ها)
@router.get("/users", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users


# 🔍 دریافت اطلاعات یک کاربر با نام کاربری
@router.get("/users/{username}", response_model=UserOut)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    return user


# ✏️ به‌روزرسانی اطلاعات کاربر
@router.put("/users/{username}", response_model=UserOut)
def update_user(username: str, user_update: User, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")

    user.first_name = user_update.first_name
    user.last_name = user_update.last_name
    user.province = user_update.province

    # ⚠️ نکته: رمز عبور باید قبل از ذخیره، هش شود.
    if user_update.password:
        user.password = user_update.password  # هش نشده، در نسخه واقعی حتماً هش کنید.

    user.is_admin = bool(user_update.is_admin)
    user.is_employer = bool(user_update.is_employer)

    db.commit()
    db.refresh(user)
    return user


# 🗑️ حذف کاربر با نام کاربری
@router.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    db.delete(user)
    db.commit()
    return {"detail": "کاربر حذف شد."}


# 🙋‍♂️ دریافت اطلاعات کاربر فعلی از روی توکن
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: UserDB = Depends(get_current_user)):
    return current_user
