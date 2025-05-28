# controllers/user_job_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime # [cite: 76] ✅ اضافه شد

from database.session import get_db
from models.models import UserJobDB, UserDB, JobDB
from schemas.schemas import UserJobBase, UserJobOut # [cite: 76] ✅ تغییر UserJob به UserJobBase
from core.auth import get_current_user

router = APIRouter(prefix="/user", tags=["UserJobs"])


@router.post("/jobs", response_model=UserJobOut, status_code=status.HTTP_201_CREATED)
def apply_job(user_job: UserJobBase, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """
    ثبت درخواست شغل توسط کارجو. # [cite: 77]
    """
    # بررسی اینکه آیا کاربر قبلا برای این شغل درخواست داده است
    existing_application = db.query(UserJobDB).filter_by(
        user_id=current_user.id,
        job_id=user_job.job_id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="شما قبلاً برای این شغل درخواست داده‌اید.")

    # بررسی وجود شغل و تأیید شده بودن آن
    job = db.query(JobDB).filter(JobDB.id == user_job.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد.") # [cite: 78]
    if not job.is_approved:
        raise HTTPException(status_code=400, detail="این شغل هنوز تأیید نشده است و امکان درخواست برای آن وجود ندارد.")

    db_user_job = UserJobDB(
        user_id=current_user.id,
        job_id=user_job.job_id,
        status="Pending", # [cite: 78] ✅ اضافه شد: وضعیت اولیه درخواست
        applied_at=datetime.utcnow(), # [cite: 78] ✅ اضافه شد: زمان ثبت درخواست
        applicant_notes=user_job.applicant_notes # ✅ جدید
    )
    db.add(db_user_job)
    db.commit()
    db.refresh(db_user_job)
    return db_user_job # [cite: 79]


@router.get("/my-jobs", response_model=List[UserJobOut])
def get_user_jobs(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """
    دریافت لیست شغل‌هایی که کارجوی فعلی برای آن‌ها درخواست داده است. # [cite: 80]
    """
    # بارگذاری ارتباطات user و job برای نمایش کامل‌تر
    return db.query(UserJobDB).filter(UserJobDB.user_id == current_user.id).all()