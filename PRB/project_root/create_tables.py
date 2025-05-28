from sqlalchemy import create_engine
from database.session import Base
from models.models import UserDB, CityDB, JobDB, UserJobDB, MessageDB  # ✅ MessageDB صحیح شد
from config.config import settings

engine = create_engine(settings.DATABASE_URL)

def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_all_tables()