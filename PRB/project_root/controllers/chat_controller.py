from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Generator
from jose import jwt, JWTError

from models import models
from schemas import schemas
from database.session import SessionLocal # ✅ import صحیح
from config.config import settings

router = APIRouter(prefix="/messages", tags=["پیام‌ها"])

# اتصال به دیتابیس (همان get_db از database.session است)
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_id_from_token(auth_header: str, db: Session) -> int:
    """
    استخراج شناسه کاربر از هدر Authorization با فرمت 'Bearer <token>'
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="توکن نامعتبر است.")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="توکن نامعتبر است.")
        
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="فرمت شناسه کاربری در توکن نامعتبر است.")

        user = db.query(models.UserDB).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="کاربر یافت نشد.")
        
        return user.id
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="توکن نامعتبر یا منقضی شده است.")

@router.get("/{message_id}", response_model=schemas.MessageOut) # ✅ MessageOut
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(..., alias="Authorization")
):
    user_id = get_user_id_from_token(authorization, db)
    message = db.query(models.MessageDB).filter_by(id=message_id).first()

    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="پیام پیدا نشد.")
    if user_id not in {message.sender_id, message.receiver_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="دسترسی غیرمجاز به پیام.")

    return message

@router.get("/", response_model=List[schemas.MessageOut]) # ✅ MessageOut
def get_conversation(
    receiver_id: int = Query(...),
    db: Session = Depends(get_db),
    authorization: str = Header(..., alias="Authorization")
):
    sender_id = get_user_id_from_token(authorization, db)
    messages = db.query(models.MessageDB).filter(
        ((models.MessageDB.sender_id == sender_id) & (models.MessageDB.receiver_id == receiver_id)) |
        ((models.MessageDB.sender_id == receiver_id) & (models.MessageDB.receiver_id == sender_id))
    ).order_by(models.MessageDB.timestamp.asc()).all()

    return messages

# ✅ روت employer/contacts به employer_controller منتقل شد.
# @router.get("/employer/contacts", response_model=List[schemas.UserShort])
# def employer_contacts(
#     authorization: str = Header(..., alias="Authorization"),
#     db: Session = Depends(get_db)
# ):
#     # ...