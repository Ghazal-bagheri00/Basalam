from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models_employer import EmployerMessage
from schemas_employer import EmployerMessageCreate, EmployerMessage
from core_employer_auth import get_current_employer
from datetime import datetime

router = APIRouter()

@router.post("/employer/messages", response_model=EmployerMessage)
def send_message(
    message_in: EmployerMessageCreate,
    db: Session = Depends(get_db),
    current_employer=Depends(get_current_employer),
):
    message = EmployerMessage(
        sender_employer_id=current_employer.id,
        receiver_user_id=message_in.receiver_user_id,
        receiver_employer_id=message_in.receiver_employer_id,
        text=message_in.text,
        timestamp=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/employer/messages", response_model=List[EmployerMessage])
def get_messages(
    db: Session = Depends(get_db),
    current_employer=Depends(get_current_employer),
):
    messages = db.query(EmployerMessage).filter(
        (EmployerMessage.receiver_employer_id == current_employer.id) |
        (EmployerMessage.sender_employer_id == current_employer.id)
    ).order_by(EmployerMessage.timestamp.asc()).all()
    return messages