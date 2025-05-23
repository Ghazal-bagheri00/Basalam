from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, Header
from sqlalchemy.orm import Session
from typing import Generator, List, Dict
from jose import jwt, JWTError

from models import models
from schemas import schemas
from database.session import SessionLocal
from config.config import settings

router = APIRouter(prefix="/messages", tags=["پیام‌ها"])

# اتصال به دیتابیس
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# اتصال‌های فعال WebSocket برای هر کاربر
active_connections: Dict[int, List[WebSocket]] = {}

# استخراج شناسه کاربر از توکن
def get_user_id_from_token(auth_header: str, db: Session) -> int:
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="توکن نامعتبر است.")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise HTTPException(status_code=403, detail="توکن نامعتبر است.")
        
        user = db.query(models.UserDB).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=403, detail="کاربر یافت نشد.")
        
        return user.id
    except (JWTError, ValueError):
        raise HTTPException(status_code=403, detail="توکن نامعتبر یا منقضی شده است.")

# دریافت یک پیام خاص
@router.get("/{message_id}", response_model=schemas.Message)
def get_message(message_id: int, db: Session = Depends(get_db), authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization, db)

    message = db.query(models.MessageDB).filter_by(id=message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد.")
    if user_id not in [message.sender_id, message.receiver_id]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز به پیام.")

    return message

# دریافت لیست پیام‌ها بین دو کاربر
@router.get("/", response_model=List[schemas.Message])
def get_conversation(receiver_id: int = Query(...), authorization: str = Header(...), db: Session = Depends(get_db)):
    sender_id = get_user_id_from_token(authorization, db)

    messages = db.query(models.MessageDB).filter(
        ((models.MessageDB.sender_id == sender_id) & (models.MessageDB.receiver_id == receiver_id)) |
        ((models.MessageDB.sender_id == receiver_id) & (models.MessageDB.receiver_id == sender_id))
    ).order_by(models.MessageDB.timestamp.asc()).all()

    return messages

# WebSocket برای چت بین دو کاربر
@router.websocket("/ws/chat/{receiver_id}")
async def websocket_chat(websocket: WebSocket, receiver_id: int, token: str = Query(...)):
    db = SessionLocal()
    try:
        sender_id = get_user_id_from_token(f"Bearer {token}", db)
        await websocket.accept()
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        db.close()
        return

    active_connections.setdefault(sender_id, []).append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()

            if not content:
                await websocket.send_json({"error": "متن پیام نمی‌تواند خالی باشد."})
                continue

            # ذخیره پیام در دیتابیس
            new_msg = models.MessageDB(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)

            payload = {
                "id": new_msg.id,
                "sender_id": new_msg.sender_id,
                "receiver_id": new_msg.receiver_id,
                "content": new_msg.content,
                "timestamp": str(new_msg.timestamp)
            }

            # ارسال به دریافت‌کننده
            for conn in active_connections.get(receiver_id, []):
                try:
                    await conn.send_json(payload)
                except:
                    continue

            # ارسال مجدد به فرستنده (سایر تب‌ها)
            for conn in active_connections.get(sender_id, []):
                if conn != websocket:
                    try:
                        await conn.send_json(payload)
                    except:
                        continue

    except WebSocketDisconnect:
        active_connections[sender_id].remove(websocket)
        if not active_connections[sender_id]:
            del active_connections[sender_id]
    finally:
        db.close()

# لیست مخاطبان برای کارفرما
@router.get("/employer/contacts", response_model=List[schemas.UserShort])
def employer_contacts(authorization: str = Header(...), db: Session = Depends(get_db)):
    employer_id = get_user_id_from_token(authorization, db)
    employer = db.query(models.UserDB).filter_by(id=employer_id).first()

    if not employer or not getattr(employer, "is_employer", False):
        raise HTTPException(status_code=403, detail="دسترسی فقط برای کارفرمایان مجاز است.")

    sender_ids = db.query(models.MessageDB.sender_id).filter(
        models.MessageDB.receiver_id == employer_id
    ).distinct().all()

    ids = [s[0] for s in sender_ids]
    if not ids:
        return []

    return db.query(models.UserDB).filter(models.UserDB.id.in_(ids)).all()
