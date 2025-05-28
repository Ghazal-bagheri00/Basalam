import redis

# اتصال به Redis
# اگر Redis در Docker اجرا می‌شود، 'localhost' باید به نام سرویس Redis در docker-compose.yml تغییر کند (مثلاً 'redis')
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)