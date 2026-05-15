from pydantic import BaseModel
from typing import Optional

class FeedbackRequest(BaseModel):
    student_text: str
    task_prompt: str
    exam: str = "TOEFL"

class FeedbackResponse(BaseModel):
    status: str
    exam: str
    feedback: str
    used_examples: int
    error: Optional[str] = None