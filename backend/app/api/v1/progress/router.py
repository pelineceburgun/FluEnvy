from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.progress_service import get_student_progress, detect_weak_points, predict_score

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{student_id}")
def student_progress(student_id: str, db: Session = Depends(get_db)):
    return get_student_progress(db, student_id)


@router.get("/{student_id}/weak-points")
def weak_points(
    student_id: str,
    task_type: Optional[str] = None,
    exam: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return detect_weak_points(db, student_id, task_type, exam)


@router.get("/{student_id}/prediction")
def score_prediction(
    student_id: str,
    task_type: Optional[str] = None,
    exam: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return predict_score(db, student_id, task_type, exam)
