from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from models.models import UserJobDB, UserDB
from schemas.schemas import UserJob, UserJobOut
from core.auth import get_current_user
from typing import List

router = APIRouter()


@router.post("/user/jobs", response_model=UserJobOut)
def apply_job(user_job: UserJob, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    db_user_job = UserJobDB(
        user_id=current_user.username,
        job_id=user_job.job_id
    )
    db.add(db_user_job)
    db.commit()
    db.refresh(db_user_job)
    return db_user_job


@router.get("/user/my-jobs", response_model=List[UserJobOut])
def get_user_jobs(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    return db.query(UserJobDB).filter(UserJobDB.user_id == current_user.username).all()
