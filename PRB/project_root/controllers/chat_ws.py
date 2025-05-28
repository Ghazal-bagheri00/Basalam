from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime
from jose import jwt, JWTError

from models import models
from database.session import SessionLocal
from config.config import settings

router = APIRouter(prefix="/ws", tags=["WebSocket پیـام‌ها"]) # ✅ Prefix فقط برای WebSocket

# نگهداری اتصال‌های WebSocket فعال برای هر کاربر
active_connections: Dict[int, List[WebSocket]] = {}

def get_user_id_from_token_ws(token: str, db: Session) -> int: # ✅ تغییر نام برای جلوگیری از تداخل
    """
    استخراج شناسه کاربر از توکن JWT برای WebSocket
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub") 
        if user_id_str is None:
            raise HTTPException(
                status_code=status.WS_1008_POLICY_VIOLATION,
                detail="توکن نامعتبر است یا شناسه کاربری یافت نشد."
            )
        
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

@router.websocket("/chat/{receiver_id}") # ✅ مسیر فقط /chat/{receiver_id} شد
async def websocket_chat(websocket: WebSocket, receiver_id: int, token: str = Query(...)):
    db = SessionLocal()
    sender_id = None
    try:
        sender_id = get_user_id_from_token_ws(token, db) # ✅ استفاده از تابع جدید
        await websocket.accept()
        
        print(f"--- New WebSocket connection opened ---")
        print(f"  Sender ID (from token): {sender_id}")
        print(f"  Receiver ID (from URL): {receiver_id}")

        active_connections.setdefault(sender_id, []).append(websocket)
        print(f"  Active connections for sender {sender_id}: {len(active_connections[sender_id])}")


        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()

            if not content:
                await websocket.send_json({"error": "متن پیام نمی‌تواند خالی باشد."})
                continue

            new_msg = models.MessageDB(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                timestamp=datetime.utcnow()
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)

            message_data = {
                "id": new_msg.id,
                "sender_id": new_msg.sender_id,
                "receiver_id": new_msg.receiver_id,
                "content": new_msg.content,
                "timestamp": new_msg.timestamp.isoformat()
            }

            print(f"\n--- Processing message from {sender_id} to {receiver_id} ---")
            print(f"  Content: '{content}'")
            print(f"  Full Payload: {message_data}")
            print(f"  Total connections for SENDER ({sender_id}): {len(active_connections.get(sender_id, []))}")
            print(f"  Total connections for RECEIVER ({receiver_id}): {len(active_connections.get(receiver_id, []))}")


            # ارسال پیام به گیرنده (اگر آنلاین است)
            print(f"  Attempting to send to receiver ({receiver_id})...")
            if receiver_id in active_connections:
                for conn in active_connections[receiver_id]:
                    try:
                        await conn.send_json(message_data)
                        print(f"    ✅ Successfully sent to receiver connection: {conn.scope['client']}")
                    except Exception as e:
                        print(f"    ❌ Failed to send to receiver connection {conn.scope['client']}: {e}")
                        # اگر خطایی در ارسال بود، اتصال را پاک کنید
                        if conn in active_connections[receiver_id]: 
                            active_connections[receiver_id].remove(conn)
                            print(f"      Removed potentially broken connection for {receiver_id}.")
                        pass
            else:
                print(f"    Receiver {receiver_id} has no active connections.")

            # ارسال پیام به تب‌های دیگر فرستنده (به جز همین اتصال)
            print(f"  Attempting to send to other sender tabs ({sender_id})...")
            if sender_id in active_connections:
                for conn in active_connections[sender_id]:
                    if conn != websocket:
                        try:
                            await conn.send_json(message_data)
                            print(f"    ✅ Successfully sent to other sender tab connection: {conn.scope['client']}")
                        except Exception as e:
                            print(f"    ❌ Failed to send to other sender tab connection {conn.scope['client']}: {e}")
                            if conn in active_connections[sender_id]:
                                active_connections[sender_id].remove(conn)
                                print(f"      Removed potentially broken sender connection for {sender_id}.")
                            pass
            else:
                print(f"    Sender {sender_id} has no other active connections.")

    except WebSocketDisconnect:
        print(f"\n--- WebSocket disconnected for sender_id: {sender_id} ---")
        if sender_id is not None and sender_id in active_connections:
            try:
                active_connections[sender_id].remove(websocket)
                if not active_connections[sender_id]:
                    del active_connections[sender_id]
                    print(f"  All connections for {sender_id} removed.")
                else:
                    print(f"  {len(active_connections[sender_id])} connections remaining for {sender_id}.")
            except ValueError:
                print(f"  WebSocket connection for {sender_id} not found in list during disconnect (already removed?).")
            pass
        
    except HTTPException as e:
        print(f"\n--- HTTPException in WebSocket for {sender_id}: {e.detail} (Status: {e.status_code}) ---")
        await websocket.close(code=int(e.status_code), reason=e.detail)

    except Exception as e:
        print(f"\n--- UNEXPECTED General error in WebSocket for {sender_id}: {e} ---")
        import traceback
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    finally:
        db.close()
        print(f"DB session closed for {sender_id}.")