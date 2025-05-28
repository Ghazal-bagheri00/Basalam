
from sqlalchemy import create_engine, inspect
from config.config import settings

def test_connection_and_users_table():
    print(f"Connecting to: {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        if "users" not in inspector.get_table_names():
            print("❌ جدول 'users' در دیتابیس وجود ندارد.")
            return

        print("✅ جدول 'users' پیدا شد.")
        columns = inspector.get_columns("users")
        print("ستون‌های جدول users:")
        for col in columns:
            print(f" - {col['name']} ({col['type']})")
    
    except Exception as e:
        print("❌ خطا در اتصال یا بررسی جدول:", str(e))

if __name__ == "__main__":
    test_connection_and_users_table()
