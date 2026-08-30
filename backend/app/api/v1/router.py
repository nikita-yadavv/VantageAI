"""API v1 consolidated router registration."""

from fastapi import APIRouter
from app.api.v1.resume_routes import router as resume_router
from app.api.v1.interview_routes import router as interview_router
from app.api.v1.evaluation_routes import router as evaluation_router
from app.api.v1.rag_routes import router as rag_router

api_router = APIRouter()

api_router.include_router(resume_router)
api_router.include_router(interview_router)
api_router.include_router(evaluation_router)
api_router.include_router(rag_router)
