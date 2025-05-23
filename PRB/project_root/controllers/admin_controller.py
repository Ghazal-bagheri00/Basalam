from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from models import models
from schemas import schemas
from core.auth import admin_required, get_current_user
from models.models import UserDB

router = APIRouter()

# ----------------- شهرها -----------------

@router.post("/admin/cities", response_model=schemas.CityOut)
def create_city(city: schemas.City, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    if db.query(models.CityDB).filter(models.CityDB.name == city.name).first():
        raise HTTPException(status_code=400, detail="شهر قبلا وجود دارد")
    db_city = models.CityDB(name=city.name)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

@router.get("/cities", response_model=List[schemas.CityOut])
def get_cities(db: Session = Depends(get_db)):
    return db.query(models.CityDB).all()

# ----------------- شغل‌ها -----------------

@router.get("/jobs", response_model=List[schemas.JobOut])
def get_all_jobs(db: Session = Depends(get_db)):
    return db.query(models.JobDB).all()

@router.post("/admin/jobs", response_model=schemas.JobOut)
def create_job(job: schemas.Job, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    if job.employer_id is not None:
        employer = db.query(models.EmployerDB).filter(models.EmployerDB.id == job.employer_id).first()
        if not employer:
            raise HTTPException(status_code=400, detail="کارفرما یافت نشد")
    db_job = models.JobDB(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.put("/admin/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, job: schemas.Job, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")
    if job.employer_id is not None:
        employer = db.query(models.EmployerDB).filter(models.EmployerDB.id == job.employer_id).first()
        if not employer:
            raise HTTPException(status_code=400, detail="کارفرما یافت نشد")
    for key, value in job.dict().items():
        setattr(db_job, key, value)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/admin/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")
    db.delete(db_job)
    db.commit()
    return {"detail": "شغل با موفقیت حذف شد"}

@router.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="شغل یافت نشد")
    return job

# ----------------- درخواست‌های شغل (UserJob) -----------------

from schemas.schemas import UserJob, UserJobOut

@router.post("/user/jobs", response_model=UserJobOut)
def apply_job(user_job: UserJob, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    existing = db.query(models.UserJobDB).filter_by(user_id=current_user.id, job_id=user_job.job_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="درخواست قبلاً ثبت شده است")
    db_user_job = models.UserJobDB(user_id=current_user.id, job_id=user_job.job_id)
    db.add(db_user_job)
    db.commit()
    db.refresh(db_user_job)
    return db_user_job

@router.get("/user/my-jobs", response_model=List[UserJobOut])
def get_user_jobs(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    return db.query(models.UserJobDB).filter(models.UserJobDB.user_id == current_user.id).all()

# ----------------- اطلاعات کاربران -----------------

@router.get("/admin/users", response_model=List[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    return db.query(models.UserDB).all()

@router.get("/user/me", response_model=schemas.UserOut)
def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user
