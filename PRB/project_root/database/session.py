# database/session.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session # [cite: 68]
from config.config import settings # [cite: 68]

engine = create_engine(settings.DATABASE_URL) # [cite: 68]

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # [cite: 68]
Base = declarative_base() # [cite: 68]

def get_db():
    db: Session = SessionLocal() # [cite: 68]
    try:
        yield db
    finally:
        # ⭐️⭐️⭐️ تغییر موقت برای دیباگ: بستن صریح سشن پس از هر درخواست ⭐️⭐️⭐️
        # این کار اطمینان می‌دهد که سشن قبلی کاملاً بسته شده و سشن جدید، داده‌های تازه را ببیند.
        db.close() # [cite: 85]