from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime
from jose import jwt, JWTError

from models import models
from database.session import SessionLocal
from config.config import settings

router = APIRouter(prefix="/v1/messages", tags=["پیام‌ها"])

# نگهداری اتصال‌های WebSocket فعال برای هر کاربر
active_connections: Dict[int, List[WebSocket]] = {}

def get_user_id_from_token(token: str, db: Session) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # ✅ اصلاح شده: "sub" حاوی شناسه کاربری است، نه نام کاربری.
        user_id_str = payload.get("sub") 
        if user_id_str is None:
            raise HTTPException(
                status_code=status.WS_1008_POLICY_VIOLATION,
                detail="توکن نامعتبر است یا شناسه کاربری یافت نشد."
            )
        
        # ✅ اصلاح شده: تبدیل به عدد صحیح و جستجو بر اساس id
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.WS_1008_POLICY_VIOLATION,
                detail="فرمت شناسه کاربری در توکن نامعتبر است."
            )

        user = db.query(models.UserDB).filter(models.UserDB.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.WS_1008_POLICY_VIOLATION,
                detail="کاربر یافت نشد."
            )
        return user.id
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION,
            detail="توکن نامعتبر یا منقضی شده است."
        )

@router.websocket("/ws/chat/{receiver_id}")
async def websocket_chat(websocket: WebSocket, receiver_id: int, token: str = Query(...)):
    db = SessionLocal()
    sender_id = None
    try:
        # احراز هویت کاربر
        sender_id = get_user_id_from_token(token, db)
        await websocket.accept()
        active_connections.setdefault(sender_id, []).append(websocket)

        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()

            if not content:
                await websocket.send_json({"error": "متن پیام نمی‌تواند خالی باشد."})
                continue

            # ایجاد پیام جدید در دیتابیس
            message = models.MessageDB(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                timestamp=datetime.utcnow()
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            message_data = {
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            }

            # ارسال پیام به گیرنده (اگر آنلاین است)
            for conn in active_connections.get(receiver_id, []):
                try:
                    await conn.send_json(message_data)
                except Exception:
                    pass

            # ارسال پیام به تب‌های دیگر فرستنده (به جز اتصال فعلی)
            for conn in active_connections.get(sender_id, []):
                if conn != websocket:
                    try:
                        await conn.send_json(message_data)
                    except Exception:
                        pass

    except WebSocketDisconnect:
        # حذف اتصال هنگام قطع شدن
        if sender_id is not None and sender_id in active_connections:
            try:
                active_connections[sender_id].remove(websocket)
                if not active_connections[sender_id]:
                    del active_connections[sender_id]
            except Exception:
                pass

    except HTTPException as e:
        # بستن اتصال WebSocket در صورت خطا در احراز هویت
        await websocket.close(code=int(e.status_code), reason=e.detail)

    except Exception:
        # بستن اتصال WebSocket برای هر خطای غیرمنتظره دیگر
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="خطای داخلی سرور")

    finally:
        db.close()
