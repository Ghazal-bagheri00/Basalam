from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from controllers import (
    auth_controller,
    city_controller,
    job_controller,
    user_controller,
    user_job_controller,
    chat_controller,
    employer_controller, # ✅ اضافه شد
    admin_controller, # ✅ اضافه شد
)
from controllers.chat_ws import router as chat_ws_router

from database.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WorkNest Job Portal - سامانه کاریابی ورک‌نست",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")

app.include_router(auth_controller.router, prefix="/v1", tags=["Auth"])
app.include_router(city_controller.router, prefix="/v1", tags=["Cities"])
app.include_router(job_controller.router, prefix="/v1", tags=["Jobs"])
app.include_router(user_controller.router, prefix="/v1", tags=["User"]) # ✅Prefix "/v1" شد
app.include_router(user_job_controller.router, prefix="/v1", tags=["UserJobs"]) # ✅Prefix "/v1" شد
app.include_router(chat_controller.router, prefix="/v1", tags=["Messages"])
app.include_router(chat_ws_router, prefix="/v1/messages") # ✅Prefix صحیح شد

app.include_router(employer_controller.router, prefix="/v1", tags=["Employer"]) # ✅ اضافه شد
app.include_router(admin_controller.router, prefix="/v1", tags=["Admin"]) # ✅ اضافه شد


@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Index file not found"}, 404