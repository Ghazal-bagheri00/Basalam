# hash_test.py
import bcrypt

def hash_password(password: str):
    # gensalt() یک salt تصادفی تولید می‌کند
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

password_to_hash = "Gh1234123"
hashed_password = hash_password(password_to_hash)
print(f"Original password: {password_to_hash}")
print(f"Hashed password: {hashed_password}")