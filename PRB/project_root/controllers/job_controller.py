from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from schemas import schemas
from models import models
from core.auth import admin_required

router = APIRouter()

@router.get("/jobs", response_model=list[schemas.JobOut])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.JobDB).all()
    return jobs

@router.post("/jobs", response_model=schemas.JobOut)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    # بررسی وجود کارفرما
    employer = db.query(models.UserDB).filter(models.UserDB.id == job.employer_id).first()
    if not employer:
        raise HTTPException(status_code=400, detail="Employer not found")

    db_job = models.JobDB(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.put("/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, job: schemas.JobCreate, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # بررسی وجود کارفرما
    employer = db.query(models.UserDB).filter(models.UserDB.id == job.employer_id).first()
    if not employer:
        raise HTTPException(status_code=400, detail="Employer not found")

    for key, value in job.dict().items():
        setattr(db_job, key, value)

    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    db_job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(db_job)
    db.commit()
    return {"detail": "Job deleted successfully"}

@router.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.JobDB).filter(models.JobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

