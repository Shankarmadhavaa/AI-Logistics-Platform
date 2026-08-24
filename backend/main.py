from fastapi import FastAPI

app = FastAPI(
    title="AI Logistics Platform",
    description="AI-powered Logistics Document Verification Platform",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "AI Logistics Platform is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }