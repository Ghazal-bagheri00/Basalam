from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

# ایمپورت کردن کنترلرها
from controllers import (
    auth_controller,
    city_controller,
    job_controller,
    user_controller,
    user_job_controller,
    chat_controller,
)
# ایمپورت کردن روتر WebSocket چت به صورت جداگانه
from controllers.chat_ws import router as chat_ws_router

# ایمپورت کردن Base و engine از دیتابیس برای ایجاد جداول
from database.session import Base, engine

# ایجاد جداول دیتابیس در زمان شروع اپلیکیشن
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WorkNest Job Portal - سامانه کاریابی ورک‌نست",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ** حتما قبل از روت‌ها، استاتیک رو mount می‌کنیم **
app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")

# ثبت روت‌های API با prefix های مشخص
app.include_router(auth_controller.router, prefix="/v1", tags=["Auth"])
app.include_router(city_controller.router, prefix="/v1", tags=["Cities"])
app.include_router(job_controller.router, prefix="/v1", tags=["Jobs"])
app.include_router(user_controller.router, prefix="/v1/user", tags=["User"])
app.include_router(user_job_controller.router, prefix="/v1/user", tags=["UserJobs"])
app.include_router(chat_controller.router, prefix="/v1", tags=["Messages"])


# ثبت وب‌سوکت روت با prefix مشخص (مثلا /v1/messages/ws)
app.include_router(chat_ws_router, prefix="/v1/messages/ws")

# endpoint ریشه برای سرویس دادن فایل index.html
@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Index file not found"}, 404
