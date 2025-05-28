# controllers/employer_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload # [cite: 54] ✅ joinedload اضافه شد
from typing import List
from datetime import datetime # [cite: 54] ✅ datetime اضافه شد

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
    ثبت شغل جدید توسط کارفرما. # [cite: 54] شغل به صورت پیش‌فرض تأیید نشده است.
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
        title=job.title, # [cite: 55]
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
    مشاهده لیست شغل‌های ثبت شده توسط کارفرمای فعلی. # [cite: 56]
    ✅ اضافه شد: نمایش اطلاعات کامل شغل (شهر و کارفرما)
    """
    jobs = db.query(models.JobDB).options(
        joinedload(models.JobDB.city),
        joinedload(models.JobDB.employer)
    ).filter(models.JobDB.employer_id == current_user.id).all()
    return jobs

@router.get("/contacts", response_model=List[schemas.UserShort])
def employer_contacts(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    دریافت لیست مخاطبین چت (کارجویان) که با کارفرمای فعلی پیام رد و بدل کرده‌اند. # [cite: 57]
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

# ✅ اضافه شد: مشاهده تمامی درخواست‌های شغلی مربوط به شغل‌های کارفرمای فعلی
@router.get("/job-applications", response_model=List[schemas.UserJobOut])
def get_employer_job_applications(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    دریافت لیست تمامی درخواست‌های شغلی برای شغل‌های کارفرمای فعلی. # [cite: 59] شامل اطلاعات کامل کارجو و شغل مربوطه.
    """
    # ابتدا شناسه شغل‌های متعلق به کارفرمای فعلی را پیدا می‌کنیم
    employer_job_ids = db.query(models.JobDB.id).filter(
        models.JobDB.employer_id == current_user.id
    ).all()
    
    # تبدیل لیست تاپل‌ها به یک لیست ساده از شناسه‌ها
    job_ids = [job_id[0] for job_id in employer_job_ids]

    if not job_ids:
        return []

    # سپس درخواست‌های شغلی مربوط به این شغل‌ها را واکشی می‌کنیم # [cite: 60]
    # با استفاده از joinedload، اطلاعات کاربر و شغل نیز به طور همزمان بارگذاری می‌شوند
    applications = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.user), # [cite: 60] ✅ بارگذاری اطلاعات کاربر متقاضی
        joinedload(models.UserJobDB.job).joinedload(models.JobDB.city) # [cite: 60] ✅ بارگذاری اطلاعات شهر شغل
    ).filter(
        models.UserJobDB.job_id.in_(job_ids)
    ).all()
    
    return applications

# ✅ اضافه شد: تأیید یا رد درخواست شغل توسط کارفرما
@router.put("/job-applications/{application_id}", response_model=schemas.UserJobOut)
def update_job_application_status(
    application_id: int,
    user_job_update: schemas.UserJobUpdate, # [cite: 61] ✅ استفاده از شمای جدید
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    به‌روزرسانی وضعیت یک درخواست شغلی توسط کارفرما (تأیید یا رد). # [cite: 62]
    """
    db_application = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.job)
    ).filter(models.UserJobDB.id == application_id).first()

    if not db_application:
        raise HTTPException(status_code=404, detail="درخواست شغلی یافت نشد.")

    # بررسی اینکه آیا شغل مربوط به این درخواست، متعلق به کارفرمای فعلی است
    if db_application.job.employer_id != current_user.id:
        raise HTTPException(status_code=403, detail="شما مجاز به تغییر وضعیت این درخواست نیستید.")

    # به‌روزرسانی وضعیت
    db_application.status = user_job_update.status
    if user_job_update.status == "Accepted":
        db_application.employer_approved_at = datetime.utcnow() # [cite: 63]
    else:
        db_application.employer_approved_at = None # در صورت رد یا pending، زمان تایید را پاک می‌کنیم

    db.commit()
    db.refresh(db_application)
    
    # برای اینکه response_model درست کار کند، نیاز داریم اطلاعات user و job را دوباره بارگذاری کنیم
    # این یک workaround است، راه بهتر این است که refresh را با options استفاده کنیم یا UserJobOut را ساده‌تر کنیم
    db_application_full = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.user), # [cite: 64]
        joinedload(models.UserJobDB.job).joinedload(models.JobDB.city)
    ).filter(models.UserJobDB.id == application_id).first()
    
    return db_application_full


# ✅ جدید: لیست کارکنان پذیرفته شده
@router.get("/accepted-employees", response_model=List[schemas.AcceptedEmployeeOut])
def get_accepted_employees(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    دریافت لیست کارجویانی که برای شغل‌های کارفرمای فعلی پذیرفته شده‌اند.
    """
    # ابتدا شناسه شغل‌های متعلق به کارفرمای فعلی را پیدا می‌کنیم
    employer_job_ids = db.query(models.JobDB.id).filter(
        models.JobDB.employer_id == current_user.id
    ).all()
    
    job_ids = [job_id[0] for job_id in employer_job_ids]

    if not job_ids:
        return []

    accepted_applications = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.user),
        joinedload(models.UserJobDB.job).joinedload(models.JobDB.city)
    ).filter(
        models.UserJobDB.job_id.in_(job_ids),
        models.UserJobDB.status == "Accepted"
    ).all()

    return accepted_applications

# ✅ جدید: حذف کارمند از لیست (در واقع تغییر وضعیت درخواست به Rejected)
@router.put("/accepted-employees/{user_job_id}/remove", response_model=schemas.UserJobOut)
def remove_accepted_employee(
    user_job_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(employer_required)
):
    """
    تغییر وضعیت یک درخواست شغلی پذیرفته شده به 'رد شده' (حذف از لیست کارکنان پذیرفته شده).
    """
    db_application = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.job)
    ).filter(models.UserJobDB.id == user_job_id).first()

    if not db_application:
        raise HTTPException(status_code=404, detail="درخواست شغلی یافت نشد.")

    # بررسی اینکه آیا شغل مربوط به این درخواست، متعلق به کارفرمای فعلی است
    if db_application.job.employer_id != current_user.id:
        raise HTTPException(status_code=403, detail="شما مجاز به تغییر وضعیت این درخواست نیستید.")
    
    if db_application.status != "Accepted":
        raise HTTPException(status_code=400, detail="این کارجو در وضعیت 'پذیرفته شده' نیست که حذف شود.")

    db_application.status = "Rejected"
    db_application.employer_approved_at = None

    db.commit()
    db.refresh(db_application)

    db_application_full = db.query(models.UserJobDB).options(
        joinedload(models.UserJobDB.user),
        joinedload(models.UserJobDB.job).joinedload(models.JobDB.city)
    ).filter(models.UserJobDB.id == user_job_id).first()
    
    return db_application_full