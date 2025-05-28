from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from models import models
from schemas import schemas
from core.auth import employer_required
from models.models import UserDB # برای type hinting

router = APIRouter(prefix="/employer", tags=["Employer"])

@router.post("/jobs", response_model=schemas.JobOut, status_code=status.HTTP_201_CREATED)
def create_job_by_employer(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    ثبت شغل جدید توسط کارفرما. شغل به صورت پیش‌فرض تأیید نشده است.
    """
    if job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما مجاز به ایجاد شغل برای کارفرمای دیگر نیستید."
        )

    city = db.query(models.CityDB).filter(models.CityDB.id == job.city_id).first()
    if not city:
        raise HTTPException(status_code=400, detail="شهر یافت نشد.")

    db_job = models.JobDB(
        title=job.title,
        description=job.description,
        city_id=job.city_id,
        employer_id=job.employer_id,
        employer_info=job.employer_info,
        is_approved=False # به صورت پیش‌فرض تأیید نشده
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/my-jobs", response_model=List[schemas.JobOut])
def get_my_posted_jobs(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    مشاهده لیست شغل‌های ثبت شده توسط کارفرمای فعلی.
    """
    jobs = db.query(models.JobDB).filter(models.JobDB.employer_id == current_user.id).all()
    return jobs

@router.get("/contacts", response_model=List[schemas.UserShort])
def employer_contacts(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    دریافت لیست مخاطبین چت (کارجویان) که با کارفرمای فعلی پیام رد و بدل کرده‌اند.
    """
    sent_to_ids = db.query(models.MessageDB.receiver_id).filter(
        models.MessageDB.sender_id == current_user.id
    ).distinct().all()

    received_from_ids = db.query(models.MessageDB.sender_id).filter(
        models.MessageDB.receiver_id == current_user.id
    ).distinct().all()

    user_ids = {u[0] for u in sent_to_ids} | {u[0] for u in received_from_ids}
    user_ids.discard(current_user.id) # خود کارفرما را از لیست حذف می‌کنیم

    if not user_ids:
        return []

    contacts = db.query(models.UserDB).filter(models.UserDB.id.in_(list(user_ids))).all()
    return contacts