import bcrypt

def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())