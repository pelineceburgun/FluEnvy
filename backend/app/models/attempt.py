from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    exam = Column(String, nullable=False)       # TOEFL, TELC
    task_type = Column(String, nullable=False)  # writing, speaking
    task_prompt = Column(Text, nullable=True)

    # Writing
    student_text = Column(Text, nullable=True)

    # Speaking
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    speech_rate_wpm = Column(Float, nullable=True)
    filler_count = Column(Integer, nullable=True)

    # Scores (all nullable — extracted from LLM output)
    overall_score = Column(Float, nullable=True)     # /30

    # Writing category scores
    task_response_score = Column(Float, nullable=True)   # /5
    organization_score = Column(Float, nullable=True)    # /5
    language_use_score = Column(Float, nullable=True)    # /5

    # Speaking category scores
    fluency_score = Column(Float, nullable=True)         # /10
    pronunciation_score = Column(Float, nullable=True)   # /8
    content_score = Column(Float, nullable=True)         # /7
    speaking_language_score = Column(Float, nullable=True)  # /5

    skill_tag = Column(String, nullable=True)  # e.g. "main_idea", "register", "grammar"

    # TELC Writing category scores (total /15)
    aufgabenbewaltigung_score      = Column(Float, nullable=True)  # /5  Task Completion
    kommunikative_gestaltung_score = Column(Float, nullable=True)  # /5  Communicative Design
    formale_richtigkeit_score      = Column(Float, nullable=True)  # /5  Formal Correctness

    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
