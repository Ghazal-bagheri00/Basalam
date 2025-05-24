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

# ذخیره اتصال‌های فعال WebSocket به صورت دیکشنری: user_id -> لیست WebSocketها
active_connections: Dict[int, List[WebSocket]] = {}

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
        
        user = db.query(models.UserDB).filter_by(id=int(user_id)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="کاربر یافت نشد.")
        
        return user.id
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="توکن نامعتبر یا منقضی شده است.")

@router.get("/{message_id}", response_model=schemas.Message)
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

@router.get("/", response_model=List[schemas.Message])
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

@router.websocket("/ws/chat/{receiver_id}")
async def websocket_chat(websocket: WebSocket, receiver_id: int, token: str = Query(...)):
    """
    WebSocket چت بین sender و receiver
    """

    db = SessionLocal()
    sender_id = None
    try:
        # تایید توکن
        sender_id = get_user_id_from_token(f"Bearer {token}", db)
        await websocket.accept()

        # ثبت اتصال کاربر در active_connections
        if sender_id not in active_connections:
            active_connections[sender_id] = []
        active_connections[sender_id].append(websocket)

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

            # ساخت پیلود پیام
            payload = {
                "id": new_msg.id,
                "sender_id": new_msg.sender_id,
                "receiver_id": new_msg.receiver_id,
                "content": new_msg.content,
                "timestamp": new_msg.timestamp.isoformat()
            }

            # ارسال پیام به گیرنده اگر فعال است
            for conn in active_connections.get(receiver_id, []):
                try:
                    await conn.send_json(payload)
                except Exception:
                    pass

            # ارسال پیام به سایر تب‌های فرستنده به جز همین اتصال
            for conn in active_connections.get(sender_id, []):
                if conn != websocket:
                    try:
                        await conn.send_json(payload)
                    except Exception:
                        pass

    except WebSocketDisconnect:
        # حذف اتصال در زمان قطع شدن وب‌سوکت
        if sender_id and sender_id in active_connections:
            try:
                active_connections[sender_id].remove(websocket)
                if len(active_connections[sender_id]) == 0:
                    del active_connections[sender_id]
            except Exception:
                pass

    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)

    finally:
        db.close()

@router.get("/employer/contacts", response_model=List[schemas.UserShort])
def employer_contacts(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
):
    employer_id = get_user_id_from_token(authorization, db)
    employer = db.query(models.UserDB).filter_by(id=employer_id).first()

    if not employer or not getattr(employer, "is_employer", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="دسترسی فقط برای کارفرمایان مجاز است.")

    # دریافت شناسه کاربران ارسال‌کننده پیام به کارفرما
    sender_ids = db.query(models.MessageDB.sender_id).filter(
        models.MessageDB.receiver_id == employer_id
    ).distinct().all()

    user_ids = [sender[0] for sender in sender_ids]
    if not user_ids:
        return []

    contacts = db.query(models.UserDB).filter(models.UserDB.id.in_(user_ids)).all()
    return contacts
