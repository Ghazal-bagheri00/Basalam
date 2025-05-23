# ✅ chat_ws.py - اصلاح دریافت user_id با username

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Generator
from datetime import datetime
from jose import jwt, JWTError

from models import models
from database.session import SessionLocal
from config.config import settings

router = APIRouter()

active_connections: Dict[int, List[WebSocket]] = {}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id_from_token(token: str, db: Session) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")  # ✅ حالا sub همان username است
        if not username:
            raise HTTPException(status_code=status.WS_1008_POLICY_VIOLATION, detail="توکن فاقد sub است.")

        user = db.query(models.UserDB).filter(models.UserDB.username == username).first()
        if not user:
            raise HTTPException(status_code=status.WS_1008_POLICY_VIOLATION, detail="کاربر یافت نشد.")

        return user.id
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.WS_1008_POLICY_VIOLATION, detail="توکن نامعتبر است.")


@router.websocket("/ws/chat/{receiver_id}")
async def websocket_chat(websocket: WebSocket, receiver_id: int, token: str = Query(...)):
    db = SessionLocal()
    try:
        sender_id = get_user_id_from_token(token, db)
        await websocket.accept()
    except HTTPException as e:
        await websocket.close(code=int(e.status_code), reason=e.detail)
        return

    active_connections.setdefault(sender_id, []).append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue

            message = models.Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                timestamp=datetime.utcnow()
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            response_data = {
                "id": message.id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": content,
                "timestamp": message.timestamp.isoformat()
            }

            for conn in active_connections.get(receiver_id, []):
                try:
                    await conn.send_json(response_data)
                except:
                    pass

            for conn in active_connections.get(sender_id, []):
                if conn != websocket:
                    try:
                        await conn.send_json(response_data)
                    except:
                        pass

    except WebSocketDisconnect:
        if sender_id in active_connections:
            try:
                active_connections[sender_id].remove(websocket)
                if not active_connections[sender_id]:
                    del active_connections[sender_id]
            except:
                pass
    finally:
        db.close()
