# schemas/schemas.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re # [cite: 91]


PHONE_PATTERN = r"^09\d{9}$"


# ---------- City ----------

class CityBase(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="نام شهر")

class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="عنوان شغل")
    description: Optional[str] = Field(None, description="توضیحات")
    city_id: Optional[int] = Field(None, description="شناسه شهر")
    employer_info: Optional[str] = Field(None, description="اطلاعات کارفرما")
    is_approved: Optional[bool] = Field(None, description="وضعیت تایید شغل")

    model_config = ConfigDict(from_attributes=True)


class CityOut(CityBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------

class UserBase(BaseModel):
    username: str
    first_name: str = Field(min_length=1, description="نام")
    last_name: str = Field(min_length=1, description="نام خانوادگی") # [cite: 92]
    province: str = Field(min_length=2, max_length=50, description="استان")
    is_admin: bool = Field(default=False, description="آیا کاربر ادمین است؟")
    is_employer: bool = Field(default=False, description="آیا کاربر کارفرما است؟")

    @field_validator("username")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("شماره موبایل باید رشته باشد.")
        phone = v.strip()
        if not re.fullmatch(PHONE_PATTERN, phone): # [cite: 93]
            raise ValueError("شماره موبایل باید با 09 شروع شود و 11 رقم داشته باشد.")
        return phone


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128, description="رمز عبور")

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError("رمز عبور باید حداقل یک حرف کوچک داشته باشد.") # [cite: 94]
        if not any(c.isupper() for c in v):
            raise ValueError("رمز عبور باید حداقل یک حرف بزرگ داشته باشد.")
        if not any(c.isdigit() for c in v):
            raise ValueError("رمز عبور باید حداقل یک عدد داشته باشد.")
        return v


class UserOut(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ✅ اضافه شد: UserShort برای نمایش اطلاعات مختصر کاربر
class UserShort(BaseModel): # [cite: 95]
    id: int
    username: str
    first_name: str
    last_name: str
    
    model_config = ConfigDict(from_attributes=True)


# ---------- Job ----------

class JobBase(BaseModel):
    title: str = Field(min_length=1, max_length=100, description="عنوان شغل")
    description: str = Field(min_length=1, description="توضیحات")
    city_id: int = Field(..., description="شناسه شهر")
    employer_info: Optional[str] = Field(default=None, description="اطلاعات کارفرما")


class JobCreate(JobBase):
    employer_id: int = Field(..., description="شناسه کارفرما")


class JobOut(JobBase):
    id: int
    city: CityOut
    employer: Optional[UserOut] = None
    is_approved: bool # [cite: 96]
    model_config = ConfigDict(from_attributes=True)

# ---------- UserJob ----------

class UserJobBase(BaseModel):
    job_id: int = Field(..., description="شناسه شغل")
    applicant_notes: Optional[str] = Field(None, description="توضیحات تکمیلی کارجو") # ✅ جدید

class UserJobOut(UserJobBase):
    """
    مدل خروجی کاربر شغل مرتبط همراه با شناسه‌ها و وضعیت جدید
    """
    id: int
    user_id: int
    status: str # [cite: 96] ✅ اضافه شد
    applied_at: datetime # [cite: 96] ✅ اضافه شد
    employer_approved_at: Optional[datetime] = None # [cite: 97] ✅ اضافه شد
    user: UserOut # [cite: 97] ✅ اضافه شد: اطلاعات کامل کاربر متقاضی
    job: JobOut # [cite: 97] ✅ اضافه شد: اطلاعات کامل شغل مربوطه
    
    model_config = ConfigDict(from_attributes=True)

# ✅ اضافه شد: شمای برای به‌روزرسانی وضعیت درخواست شغل توسط کارفرما
class UserJobUpdate(BaseModel): # [cite: 97]
    status: str = Field(..., pattern="^(Pending|Accepted|Rejected)$", description="وضعیت درخواست: Pending, Accepted, Rejected")
    model_config = ConfigDict(from_attributes=True)

# ✅ جدید: شمای برای نمایش کارکنان پذیرفته شده (بر اساس UserJobOut)
class AcceptedEmployeeOut(BaseModel):
    id: int # user_job id
    user: UserOut # اطلاعات کامل کارجو
    job: JobOut # اطلاعات کامل شغلی که برای آن پذیرفته شده
    applied_at: datetime
    employer_approved_at: datetime
    applicant_notes: Optional[str]
    model_config = ConfigDict(from_attributes=True)


# ---------- Token ----------

class Token(BaseModel): # [cite: 99]
    access_token: str = Field(..., description="توکن دسترسی")
    token_type: str = Field(..., description="نوع توکن")


# ---------- Message ----------

class MessageBase(BaseModel):
    sender_id: int = Field(..., description="شناسه فرستنده پیام")
    receiver_id: int = Field(..., description="شناسه گیرنده پیام")
    content: str = Field(min_length=1, description="متن پیام")


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    id: int
    timestamp: datetime
    sender: UserOut
    receiver: UserOut
    model_config = ConfigDict(from_attributes=True)


# --- Aliases ---
User = UserCreate
Job = JobCreate
City = CityBase
CityOut = CityOut # تکراری، حذف شد
UserOut = UserOut # تکراری، حذف شد
JobOut = JobOut # تکراری، حذف شد
UserJob = UserJobBase # ✅ نام‌گذاری بهتر برای ورودی ایجاد درخواست
UserJobOut = UserJobOut # تکراری، حذف شد
#JobRequest = JobRequest # حذف شد
Token = Token # تکراری، حذف شد
Message = MessageBase
MessageOut = MessageOut # تکراری، حذف شد