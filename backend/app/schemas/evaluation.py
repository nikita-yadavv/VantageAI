"""Pydantic schemas for the final Session Evaluation report."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class QuestionReviewItem(BaseModel):
    """Detailed review of an individual question within the final report."""
    order_index: int
    question_text: str
    topic: str
    difficulty: str
    rag_source_book: Optional[str]
    rag_context_chunk: Optional[str]
    candidate_answer: str
    ideal_rubric: Optional[str]
    score: float
    technical_accuracy_score: float
    depth_score: float
    practical_application_score: float
    clarity_score: float
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]


class SessionReportResponse(BaseModel):
    """Complete session scorecard and analytics report."""
    session_id: int
    session_token: str
    candidate_name: str
    target_role: str
    overall_score: float  # Scale of 0 - 100
    recommendation: str   # Strong Hire, Hire, Leaning Hire, Leaning Reject, Reject
    executive_summary: str
    category_scores: Dict[str, float]
    key_strengths: List[str]
    areas_for_growth: List[str]
    total_questions: int
    questions_answered: int
    rag_grounding_summary: Dict[str, Any]
    questions_review: List[QuestionReviewItem]
    created_at: datetime
    completed_at: Optional[datetime]
