from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.core.database import get_db
from app.services.feedback_generator import FeedbackGenerator
from app.services.speaking_service import SpeakingService
from app.services.score_extractor import extract_overall_score, extract_rubric_scores
from app.services.progress_service import save_attempt

router = APIRouter(prefix="/feedback", tags=["feedback"])

feedback_generator = FeedbackGenerator()
speaking_service = SpeakingService()


class FeedbackRequest(BaseModel):
    student_text: str
    task_prompt: str
    exam: str = "TOEFL"
    student_id: Optional[str] = None
    skill_tag: Optional[str] = None


class ReadingResultRequest(BaseModel):
    student_id: Optional[str] = None
    exam: str = "TOEFL"
    correct_count: int
    total_count: int
    passage_details: Optional[str] = None


@router.post("/writing")
async def writing_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    try:
        result = await feedback_generator.generate_writing_feedback(
            student_text=request.student_text,
            task_prompt=request.task_prompt,
            exam=request.exam,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        if request.student_id:
            feedback_text = result.get("feedback", "")
            rubric = extract_rubric_scores(feedback_text, "writing", exam=request.exam)
            save_attempt(db, {
                "student_id": request.student_id,
                "exam": request.exam,
                "task_type": "writing",
                "task_prompt": request.task_prompt,
                "student_text": request.student_text,
                "skill_tag": request.skill_tag or None,
                "overall_score": extract_overall_score(feedback_text, exam=request.exam),
                "feedback_text": feedback_text,
                **rubric,
            })

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speaking")
async def speaking_feedback(
    audio: UploadFile = File(...),
    exam: str = Form("TOEFL"),
    task_prompt: str = Form(""),
    student_id: str = Form(""),
    skill_tag: str = Form(""),
    db: Session = Depends(get_db),
):
    temp_path = f"/tmp/{audio.filename}"
    try:
        content = await audio.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        result = speaking_service.analyze_audio(temp_path, exam, task_prompt)

        if student_id and result.get("status") == "success":
            feedback_text = result.get("feedback", "")
            rubric = extract_rubric_scores(feedback_text, "speaking")
            save_attempt(db, {
                "student_id": student_id,
                "exam": exam,
                "task_type": "speaking",
                "task_prompt": task_prompt,
                "skill_tag": skill_tag or None,
                "transcript": result.get("transcript"),
                "duration_seconds": result.get("duration_seconds"),
                "speech_rate_wpm": result.get("speech_rate_wpm"),
                "filler_count": result.get("filler_count"),
                "overall_score": extract_overall_score(feedback_text),
                "feedback_text": feedback_text,
                **rubric,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/reading")
async def reading_result(request: ReadingResultRequest, db: Session = Depends(get_db)):
    scaled_score = round((request.correct_count / request.total_count) * 30, 1)
    if request.student_id:
        save_attempt(db, {
            "student_id": request.student_id,
            "exam": request.exam,
            "task_type": "reading",
            "task_prompt": f"Reading comprehension — {request.total_count} questions",
            "overall_score": scaled_score,
            "feedback_text": request.passage_details or "",
        })
    return {
        "status": "success",
        "correct": request.correct_count,
        "total": request.total_count,
        "scaled_score": scaled_score,
    }
