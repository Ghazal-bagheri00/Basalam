# controllers/job_controller.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload # ✅ joinedload اضافه شد
from database.session import get_db
from schemas import schemas
from models import models

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/", response_model=list[schemas.JobOut])
def get_all_jobs(db: Session = Depends(get_db)):
    """
    دریافت لیست تمامی شغل‌های تأیید شده برای نمایش عمومی. # [cite: 65]
    """
    # فقط شغل‌های تأیید شده را نمایش می‌دهد
    jobs = db.query(models.JobDB).filter(models.JobDB.is_approved == True).all()
    return jobs

@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    """
    دریافت اطلاعات یک شغل خاص. # [cite: 66]
    ✅ اضافه شد: با joinedload اطلاعات شهر و کارفرما را هم بارگذاری می‌کنیم.
    """
    job = db.query(models.JobDB).options(
        joinedload(models.JobDB.city),
        joinedload(models.JobDB.employer)
    ).filter(models.JobDB.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد.")
    
    # می‌توان اینجا بررسی کرد که آیا شغل تأیید شده است یا خیر،
    # اگر تأیید نشده باشد، بسته به نیاز می‌توان 404 یا 403 برگرداند.
    # if not job.is_approved:
    #     raise HTTPException(status_code=404, detail="شغل یافت نشد یا هنوز تأیید نشده است.")
    return job

# روت‌های create, update, delete به admin_controller و employer_controller منتقل شده‌اند.