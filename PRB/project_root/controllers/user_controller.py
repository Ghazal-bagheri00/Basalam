from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from schemas.schemas import User, UserOut
from models.models import UserDB  # این خط باید باشه
from database.session import get_db

router = APIRouter()

@router.get("/users", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users

@router.get("/users/{username}", response_model=UserOut)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{username}", response_model=UserOut)
def update_user(username: str, user_update: User, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # آپدیت فیلدها
    user.first_name = user_update.first_name
    user.last_name = user_update.last_name
    user.province = user_update.province

    if user_update.password:
        user.password = user_update.password  # هش کردن اینجا لازمه

    user.is_admin = user_update.is_admin or False
    user.is_employer = user_update.is_employer or False  # این خط اضافه شد

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}
