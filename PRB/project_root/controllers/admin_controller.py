# controllers/admin_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from models import models
from schemas import schemas
from core.auth import admin_required
from models.models import UserDB

router = APIRouter(prefix="/admin", tags=["Admin"])

# ----------------- شهرها -----------------

@router.post("/cities", response_model=schemas.CityOut)
def create_city(city: schemas.City, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    ایجاد یک شهر جدید توسط ادمین.
    """
    if db.query(models.CityDB).filter(models.CityDB.name == city.name).first():
        raise HTTPException(status_code=400, detail="شهر قبلا وجود دارد")
    db_city = models.CityDB(name=city.name)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

# ----------------- شغل‌ها -----------------

@router.get("/jobs/all", response_model=List[schemas.JobOut])
def get_all_jobs_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی شغل‌ها (تأیید شده و تأیید نشده) - فقط برای ادمین.
    ⭐️⭐️⭐️ این تابع اطمینان می‌دهد که داده‌ها از دیتابیس تازه واکشی می‌شوند، نه از کش سشن. ⭐️⭐️⭐️
    """
    db.expire_all() # پاک کردن هر شیء منقضی شده از سشن
    jobs = db.query(models.JobDB).all() # واکشی تمام مشاغل از دیتابیس
    
    # ⭐️⭐️⭐️⭐️⭐️ لاگ بسیار مهم برای دیباگ دقیق‌تر ⭐️⭐️⭐️⭐️⭐️
    print("\n--- DEBUG: State of jobs fetched by get_all_jobs_for_admin BEFORE returning ---")
    if not jobs:
        print("  No jobs found in the database.")
    else:
        for job in jobs:
            # استفاده از .__dict__ برای دیدن تمام اتریبیوت‌های آبجکت SQLAlchemy
            print(f"  Job ID: {job.id}, Title: '{job.title}', is_approved: {job.is_approved}, Raw DB Object State: {job.__dict__}")
    print("-----------------------------------------------------------------\n")
        
    return jobs

@router.put("/jobs/{job_id}", response_model=schemas.JobOut)
def update_job_by_admin(
    job_id: int,
    job_update: schemas.JobUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(admin_required)
):
    """
    به‌روزرسانی یک شغل توسط ادمین (شامل تغییر وضعیت تأیید).
    """
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")

    update_data = job_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job, key, value)

    try:
        db.commit() # تغییرات را در دیتابیس ذخیره کن
        db.refresh(db_job) # آبجکت را با اطلاعات جدید از دیتابیس رفرش کن
        
        # ⭐️⭐️⭐️ اضافه کردن لاگ‌های دقیق‌تر برای دیباگ بعد از Commit و Refresh ⭐️⭐️⭐️
        print(f"DEBUG: Job {db_job.id} (Title: '{db_job.title}') status committed successfully in update_job_by_admin.")
        print(f"DEBUG: is_approved for job {db_job.id} after commit and refresh: {db_job.is_approved}")
        print(f"DEBUG: Full object state after refresh: {db_job.__dict__}")
        
    except Exception as e:
        db.rollback() # اگر خطایی در حین commit رخ داد، تغییرات را برگردان
        print(f"ERROR: Failed to commit job update for ID {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در به‌روزرسانی شغل: {e}")

    return db_job

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_by_admin(job_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    حذف یک شغل توسط ادمین.
    """
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")
    
    try:
        db.delete(db_job)
        db.commit()
        print(f"DEBUG: Job {job_id} deleted successfully.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در حذف شغل: {e}")
    
    return

# ----------------- درخواست‌های شغل (UserJob) -----------------

@router.get("/user-jobs", response_model=List[schemas.UserJobOut])
def get_all_user_jobs_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی درخواست‌های شغلی ثبت شده توسط کارجویان - فقط برای ادمین.
    """
    return db.query(models.UserJobDB).all()


# ----------------- اطلاعات کاربران -----------------

@router.get("/users", response_model=List[schemas.UserOut])
def get_all_users_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی کاربران - فقط برای ادمین.
    """
    return db.query(models.UserDB).all()