from fastapi import APIRouter
from app.api.v1.feedback.router import router as feedback_router

api_router = APIRouter()

api_router.include_router(feedback_router)