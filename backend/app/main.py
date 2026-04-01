import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.database import init_db

app = FastAPI(
    title="College Basketball Predictor",
    version="0.1.0",
    description="MVP backend for predicting D1 college basketball game outcomes",
)

# ALLOWED_ORIGINS env var lets production Vercel URLs be added without code changes.
# Format: comma-separated list, e.g. "https://myapp.vercel.app,https://myapp-git-main.vercel.app"
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "app": "College Basketball Predictor",
        "version": "0.1.0",
    }
