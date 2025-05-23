from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

# Import controllers
from controllers import (
    auth_controller,
    city_controller,
    job_controller,
    user_controller,
    user_job_controller,
    chat_controller,
)
from controllers.chat_ws import router as chat_ws_router

# Import DB engine and Base
from database.session import Base, engine

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# Create FastAPI instance
app = FastAPI(
    title="WorkNest Job Portal - سامانه کاریابی ورک‌نست",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files (e.g., index.html, JS, CSS)
app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")

# Register API routes
app.include_router(auth_controller.router, prefix="/v1", tags=["Auth"])
app.include_router(city_controller.router, prefix="/v1", tags=["Cities"])
app.include_router(job_controller.router, prefix="/v1", tags=["Jobs"])
app.include_router(user_controller.router, prefix="/v1/user", tags=["User"])
app.include_router(user_job_controller.router, prefix="/v1/user", tags=["UserJobs"])
app.include_router(chat_controller.router, prefix="/v1", tags=["Messages"])
app.include_router(chat_ws_router, prefix="/v1/messages/ws")

# Root endpoint to serve index.html
@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Index file not found"}, 404
