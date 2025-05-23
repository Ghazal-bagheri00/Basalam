from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Generator, List, Dict
from models import models
from schemas import schemas
from database.session import SessionLocal
from jose import JWTError, jwt
from config.config import settings

router = APIRouter(prefix="/messages", tags=["پیام‌ها"])

# اتصال دیتابیس
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# مدیریت اتصالات WebSocket به شکل دیکشنری از لیست WebSocketها بر اساس شناسه کاربر
active_connections: Dict[int, List[WebSocket]] = {}

# استخراج ID کاربر از توکن JWT
def get_user_id_from_token(token: str, db: Session) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=403, detail="توکن فاقد فیلد 'sub' است.")
        user = db.query(models.UserDB).filter(models.UserDB.username == username).first()
        if not user:
            raise HTTPException(status_code=403, detail="کاربر یافت نشد.")
        return user.id
    except JWTError:
        raise HTTPException(status_code=403, detail="توکن نامعتبر یا منقضی شده است.")

# دریافت پیام خاص با آیدی
@router.get("/{message_id}", response_model=schemas.Message)
def get_message_by_id(
    message_id: int,
    db: Session = Depends(get_db),
    token: str = Query(...)
):
    user_id = get_user_id_from_token(token, db)
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد.")
    if user_id not in [message.sender_id, message.receiver_id]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز.")
    return message

# لیست پیام‌ها بین دو کاربر
@router.get("/", response_model=List[schemas.Message])
def get_messages_between_users(
    receiver_id: int = Query(...),
    db: Session = Depends(get_db),
    token: str = Query(...)
):
    user_id = get_user_id_from_token(token, db)
    messages = db.query(models.Message).filter(
        ((models.Message.sender_id == user_id) & (models.Message.receiver_id == receiver_id)) |
        ((models.Message.sender_id == receiver_id) & (models.Message.receiver_id == user_id))
    ).order_by(models.Message.timestamp.asc()).all()
    return messages

# WebSocket چت
@router.websocket("/ws/chat/{receiver_id}")
async def chat_websocket(
    websocket: WebSocket,
    receiver_id: int,
    token: str = Query(...)
):
    db = SessionLocal()
    try:
        sender_id = get_user_id_from_token(token, db)
        await websocket.accept()
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        db.close()
        return

    # ثبت اتصال WebSocket برای فرستنده
    active_connections.setdefault(sender_id, []).append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                await websocket.send_json({"error": "متن پیام نمی‌تواند خالی باشد."})
                continue

            # ذخیره پیام در دیتابیس
            try:
                message = models.Message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=content
                )
                db.add(message)
                db.commit()
                db.refresh(message)
            except Exception as e:
                await websocket.send_json({"error": "خطا در ذخیره پیام."})
                print(f"خطا در ذخیره پیام: {e}")
                continue

            message_data = {
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "timestamp": str(message.timestamp),
            }

            # ارسال پیام به همه اتصال‌های گیرنده
            receiver_conns = active_connections.get(receiver_id, [])
            disconnected_conns = []
            for conn in receiver_conns:
                try:
                    await conn.send_json(message_data)
                except Exception:
                    disconnected_conns.append(conn)
            # حذف کانکشن‌های قطع شده
            for dc in disconnected_conns:
                receiver_conns.remove(dc)
            if not receiver_conns:
                active_connections.pop(receiver_id, None)

            # ارسال پیام به بقیه اتصال‌های فرستنده (مثلاً تب‌های دیگر)
            sender_conns = active_connections.get(sender_id, [])
            disconnected_conns = []
            for conn in sender_conns:
                if conn != websocket:
                    try:
                        await conn.send_json(message_data)
                    except Exception:
                        disconnected_conns.append(conn)
            for dc in disconnected_conns:
                sender_conns.remove(dc)
            if not sender_conns:
                active_connections.pop(sender_id, None)

    except WebSocketDisconnect:
        # حذف اتصال در صورت قطع WebSocket
        if sender_id in active_connections and websocket in active_connections[sender_id]:
            active_connections[sender_id].remove(websocket)
            if not active_connections[sender_id]:
                del active_connections[sender_id]
    finally:
        db.close()

# لیست کاربران پیام‌دهنده به کارفرما (مخاطبین)
@router.get("/employer/contacts", response_model=List[schemas.UserShort])
def get_employer_contacts(token: str = Query(...), db: Session = Depends(get_db)):
    employer_id = get_user_id_from_token(token, db)

    employer = db.query(models.UserDB).filter(models.UserDB.id == employer_id).first()
    if not employer or not getattr(employer, "is_employer", False):
        raise HTTPException(status_code=403, detail="دسترسی فقط برای کارفرمایان مجاز است.")

    sender_ids = db.query(models.Message.sender_id).filter(
        models.Message.receiver_id == employer.id
    ).distinct().all()

    sender_ids = [s[0] for s in sender_ids]
    if not sender_ids:
        return []

    users = db.query(models.UserDB).filter(models.UserDB.id.in_(sender_ids)).all()
    return users


