# models/models.py

from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from database.session import Base
from datetime import datetime


class CityDB(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    jobs = relationship("JobDB", back_populates="city")


class JobDB(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    employer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False) # [cite: 88]
    is_approved = Column(Boolean, default=False, nullable=False)
    employer_info = Column(String, nullable=True)

    city = relationship("CityDB", back_populates="jobs")
    employer = relationship("UserDB", back_populates="posted_jobs", foreign_keys=[employer_id])
    user_jobs = relationship("UserJobDB", back_populates="job")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_employer = Column(Boolean, default=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    province = Column(String, nullable=False) # [cite: 89]

    jobs = relationship("UserJobDB", back_populates="user")
    posted_jobs = relationship("JobDB", back_populates="employer", foreign_keys=[JobDB.employer_id])
    sent_messages = relationship("MessageDB", foreign_keys='MessageDB.sender_id', back_populates="sender")
    received_messages = relationship("MessageDB", foreign_keys='MessageDB.receiver_id', back_populates="receiver")


class UserJobDB(Base):
    __tablename__ = "user_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String, default="Pending", nullable=False) # [cite: 90] ✅ اضافه شد: وضعیت درخواست (Pending, Accepted, Rejected)
    applied_at = Column(DateTime, default=datetime.utcnow) # [cite: 90] ✅ اضافه شد: زمان ثبت درخواست
    employer_approved_at = Column(DateTime, nullable=True) # [cite: 90] ✅ اضافه شد: زمان تایید توسط کارفرما
    applicant_notes = Column(Text, nullable=True) # ✅ جدید: توضیحات ارسالی کارجو

    user = relationship("UserDB", back_populates="jobs")
    job = relationship("JobDB", back_populates="user_jobs")


class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    sender = relationship("UserDB", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("UserDB", foreign_keys=[receiver_id], back_populates="received_messages")