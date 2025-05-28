from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


PHONE_PATTERN = r"^09\d{9}$"


# ---------- City ----------

class CityBase(BaseModel):
    """
    اطلاعات پایه شهر
    """
    name: str = Field(min_length=1, max_length=50, description="نام شهر")

class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="عنوان شغل")
    description: Optional[str] = Field(None, description="توضیحات")
    city_id: Optional[int] = Field(None, description="شناسه شهر")
    employer_info: Optional[str] = Field(None, description="اطلاعات کارفرما")
    is_approved: Optional[bool] = Field(None, description="وضعیت تایید شغل")

    model_config = ConfigDict(from_attributes=True)


class CityOut(CityBase):
    """
    مدل خروجی شهر همراه با شناسه
    """
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------

class UserBase(BaseModel):
    """
    اطلاعات پایه کاربر
    """
    username: str  # شماره موبایل
    first_name: str = Field(min_length=1, description="نام")
    last_name: str = Field(min_length=1, description="نام خانوادگی")
    province: str = Field(min_length=2, max_length=50, description="استان")
    is_admin: bool = Field(default=False, description="آیا کاربر ادمین است؟")
    is_employer: bool = Field(default=False, description="آیا کاربر کارفرما است؟")

    @field_validator("username")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        اعتبارسنجی شماره موبایل (باید با 09 شروع و 11 رقم باشد)
        """
        if not isinstance(v, str):
            raise TypeError("شماره موبایل باید رشته باشد.")
        phone = v.strip()
        if not re.fullmatch(PHONE_PATTERN, phone):
            raise ValueError("شماره موبایل باید با 09 شروع شود و 11 رقم داشته باشد.")
        return phone


class UserCreate(UserBase):
    """
    مدل دریافت اطلاعات ثبت‌نام کاربر به همراه رمز عبور
    """
    password: str = Field(min_length=8, max_length=128, description="رمز عبور")

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        """
        اعتبارسنجی رمز عبور قوی: حداقل یک حرف کوچک، یک حرف بزرگ و یک عدد
        """
        if not any(c.islower() for c in v):
            raise ValueError("رمز عبور باید حداقل یک حرف کوچک داشته باشد.")
        if not any(c.isupper() for c in v):
            raise ValueError("رمز عبور باید حداقل یک حرف بزرگ داشته باشد.")
        if not any(c.isdigit() for c in v):
            raise ValueError("رمز عبور باید حداقل یک عدد داشته باشد.")
        return v


class UserOut(UserBase):
    """
    مدل خروجی اطلاعات کاربر همراه با شناسه
    """
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Job ----------

class JobBase(BaseModel):
    """
    اطلاعات پایه شغل
    """
    title: str = Field(min_length=1, max_length=100, description="عنوان شغل")
    description: str = Field(min_length=1, description="توضیحات")
    city_id: int = Field(..., description="شناسه شهر")
    employer_info: Optional[str] = Field(default=None, description="اطلاعات کارفرما")


class JobCreate(JobBase):
    """
    مدل دریافت اطلاعات ایجاد شغل
    """
    employer_id: int = Field(..., description="شناسه کارفرما")


class JobOut(JobBase):
    id: int
    city: CityOut
    employer: Optional[UserOut] = None
    is_approved: bool   # ✅ این خط رو اضافه کن
    model_config = ConfigDict(from_attributes=True)

# ---------- UserJob ----------

class UserJobBase(BaseModel):
    """
    اطلاعات پایه برای کاربر و شغل مرتبط
    """
    job_id: int = Field(..., description="شناسه شغل")


class UserJobOut(UserJobBase):
    """
    مدل خروجی کاربر شغل مرتبط همراه با شناسه‌ها
    """
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- JobRequest ----------

class JobRequest(BaseModel):
    """
    درخواست شرکت در شغل با شماره موبایل و شناسه شغل
    """
    username: str = Field(..., description="شماره موبایل")
    job_id: int = Field(..., description="شناسه شغل")

    @field_validator("username")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        اعتبارسنجی شماره موبایل مشابه مدل UserBase
        """
        if not isinstance(v, str):
            raise TypeError("شماره موبایل باید رشته باشد.")
        phone = v.strip()
        if not re.fullmatch(PHONE_PATTERN, phone):
            raise ValueError("شماره موبایل باید با 09 شروع شود و 11 رقم داشته باشد.")
        return phone


# ---------- Token ----------

class Token(BaseModel):
    """
    مدل توکن JWT برای احراز هویت
    """
    access_token: str = Field(..., description="توکن دسترسی")
    token_type: str = Field(..., description="نوع توکن")


# ---------- Message ----------

class MessageBase(BaseModel):
    """
    اطلاعات پایه پیام
    """
    sender_id: int = Field(..., description="شناسه فرستنده پیام")
    receiver_id: int = Field(..., description="شناسه گیرنده پیام")
    content: str = Field(min_length=1, description="متن پیام")


class MessageCreate(MessageBase):
    """
    مدل دریافت پیام جدید (ارسال پیام)
    """
    pass


class MessageOut(MessageBase):
    """
    مدل خروجی پیام همراه با شناسه، زمان ارسال و اطلاعات کاربران
    """
    id: int
    timestamp: datetime
    sender: UserOut
    receiver: UserOut
    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    """
    مدل مختصر اطلاعات کاربر
    """
    id: int
    first_name: str
    last_name: str
    model_config = ConfigDict(from_attributes=True)

# --- Aliases ---
User = UserCreate
Job = JobCreate
City = CityBase
CityOut = CityOut
UserOut = UserOut
JobOut = JobOut
UserJob = UserJobBase
UserJobOut = UserJobOut
JobRequest = JobRequest
Token = Token
Message = MessageBase
MessageOut = MessageOut