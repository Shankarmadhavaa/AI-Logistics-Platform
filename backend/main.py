from fastapi import FastAPI

from backend.api.exception_handlers import app_exception_handler
from backend.core.exceptions import AppException
from backend.core.logging_config import setup_logging
from backend.api.routes.upload import router as upload_router
from backend.api.routes.documents import router as documents_router

setup_logging()

app = FastAPI(
    title="AI Logistics Platform",
    description="AI-powered Logistics Document Intelligence Platform",
    version="1.0.0",
)

app.add_exception_handler(AppException, app_exception_handler)
app.include_router(upload_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "AI Logistics Platform API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }