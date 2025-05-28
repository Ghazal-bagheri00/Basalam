# controllers/admin_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload # [cite: 1] ✅ joinedload اضافه شد
from typing import List

from database.session import get_db
from models import models
from schemas import schemas
from core.auth import admin_required
from models.models import UserDB

router = APIRouter(prefix="/admin", tags=["Admin"])

# ----------------- شهرها -----------------

@router.post("/cities", response_model=schemas.CityOut) # [cite: 2]
def create_city(city: schemas.City, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    if db.query(models.CityDB).filter(models.CityDB.name == city.name).first():
        raise HTTPException(status_code=400, detail="شهر قبلا وجود دارد")
    db_city = models.CityDB(name=city.name)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

# ----------------- شغل‌ها -----------------

@router.get("/jobs/all", response_model=List[schemas.JobOut]) # [cite: 2]
def get_all_jobs_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی شغل‌ها (تأیید شده و تأیید نشده) - فقط برای ادمین. # [cite: 3]
    """
    db.expire_all()
    # ✅ اضافه شد: با joinedload اطلاعات شهر و کارفرما را هم بارگذاری می‌کنیم
    return db.query(models.JobDB).options(
        joinedload(models.JobDB.city),
        joinedload(models.JobDB.employer)
    ).all()

@router.put("/jobs/{job_id}", response_model=schemas.JobOut) # [cite: 3]
def update_job_by_admin(
    job_id: int,
    job_update: schemas.JobUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(admin_required)
):
    """
    به‌روزرسانی یک شغل توسط ادمین (شامل تغییر وضعیت تأیید). # [cite: 4]
    """
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first() # [cite: 4]
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")

    update_data = job_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job, key, value)

    db.commit()
    db.refresh(db_job)
    
    print(f"Job {db_job.id} is_approved after update and refresh: {db_job.is_approved}")
    
    return db_job

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT) # [cite: 4]
def delete_job_by_admin(job_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    حذف یک شغل توسط ادمین. # [cite: 5]
    """
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first() # [cite: 5]
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")
    db.delete(db_job)
    db.commit()
    return

# ----------------- درخواست‌های شغل (UserJob) -----------------

@router.get("/user-jobs", response_model=List[schemas.UserJobOut]) # [cite: 5]
def get_all_user_jobs_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی درخواست‌های شغلی ثبت شده توسط کارجویان - فقط برای ادمین. # [cite: 6]
    ✅ با joinedload اطلاعات کاربر و شغل را هم بارگذاری می‌کنیم. # [cite: 6]
    """
    return db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.user),
        joinedload(models.UserJobDB.job).joinedload(models.JobDB.city) # [cite: 7] برای دسترسی به نام شهر
    ).all()


# ----------------- اطلاعات کاربران -----------------

@router.get("/users", response_model=List[schemas.UserOut]) # [cite: 7]
def get_all_users_for_admin(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    """
    دریافت لیست تمامی کاربران - فقط برای ادمین. # [cite: 8]
    """
    return db.query(models.UserDB).all()