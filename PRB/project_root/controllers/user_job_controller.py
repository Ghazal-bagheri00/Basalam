# controllers/user_job_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from models.models import UserJobDB, UserDB, JobDB # JobDB اضافه شد
from schemas.schemas import UserJobBase, UserJobOut # ✅ تغییر UserJob به UserJobBase
from core.auth import get_current_user

router = APIRouter(prefix="/user", tags=["UserJobs"])


@router.post("/jobs", response_model=UserJobOut, status_code=status.HTTP_201_CREATED)
def apply_job(user_job: UserJobBase, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)): # ✅ تغییر UserJob به UserJobBase
    """
    ثبت درخواست شغل توسط کارجو.
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
        raise HTTPException(status_code=404, detail="شغل یافت نشد.")
    if not job.is_approved: # فقط برای شغل‌های تأیید شده می‌توان درخواست داد
        raise HTTPException(status_code=400, detail="این شغل هنوز تأیید نشده است و امکان درخواست برای آن وجود ندارد.")

    db_user_job = UserJobDB(
        user_id=current_user.id, # شناسه کاربری عددی از current_user گرفته می‌شود
        job_id=user_job.job_id
    )
    db.add(db_user_job)
    db.commit()
    db.refresh(db_user_job)
    return db_user_job


@router.get("/my-jobs", response_model=List[UserJobOut])
def get_user_jobs(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """
    دریافت لیست شغل‌هایی که کارجوی فعلی برای آن‌ها درخواست داده است.
    """
    # فیلتر بر اساس user_id عددی
    return db.query(UserJobDB).filter(UserJobDB.user_id == current_user.id).all()