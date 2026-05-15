from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine
from app.models.attempt import Attempt  # noqa: F401 — registers table with Base
from app.core.database import Base
from app.api.v1.feedback.router import router as feedback_router
from app.api.v1.progress.router import router as progress_router

Base.metadata.create_all(bind=engine)

# Auto-migrate: add columns introduced after the initial schema
_NEW_COLS = {
    "skill_tag":                      "VARCHAR",
    "aufgabenbewaltigung_score":      "REAL",
    "kommunikative_gestaltung_score": "REAL",
    "formale_richtigkeit_score":      "REAL",
}
with engine.connect() as conn:
    existing = {row[1] for row in conn.execute(text("PRAGMA table_info(attempts)"))}
    for col, col_type in _NEW_COLS.items():
        if col not in existing:
            conn.execute(text(f"ALTER TABLE attempts ADD COLUMN {col} {col_type}"))
    conn.commit()

app = FastAPI(
    title="TOEFL & TELC AI Preparation Platform",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedback_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "TOEFL & TELC Backend API is running",
        "status": "ok",
        "endpoints": {
            "writing_feedback":  "POST /api/v1/feedback/writing",
            "speaking_feedback": "POST /api/v1/feedback/speaking",
            "student_progress":  "GET  /api/v1/progress/{student_id}",
            "weak_points":       "GET  /api/v1/progress/{student_id}/weak-points",
            "prediction":        "GET  /api/v1/progress/{student_id}/prediction",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
