"""Pydantic schemas for Interview orchestration, questions, and answers."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class StartInterviewRequest(BaseModel):
    """Payload to initiate a new role-based screening session."""
    resume_id: int
    candidate_id: Optional[int] = None
    target_role: str = Field(..., description="E.g., AI / Machine Learning Engineer, Backend Engineer")
    difficulty_level: Optional[str] = Field(default="intermediate", description="junior, intermediate, senior")
    total_questions: Optional[int] = Field(default=5, description="Number of questions in session")


class QuestionDetail(BaseModel):
    """Schema for individual question presented to candidate."""
    id: int
    order_index: int
    question_text: str
    topic: str
    difficulty: str
    target_role: str
    rag_source_book: Optional[str] = None
    rag_context_snippet: Optional[str] = None


class StartInterviewResponse(BaseModel):
    """Response returned upon successful interview session creation."""
    session_id: int
    session_token: str
    candidate_id: int
    target_role: str
    difficulty_level: str
    total_questions: int
    current_question: QuestionDetail


class SubmitAnswerRequest(BaseModel):
    """Candidate's submitted answer."""
    question_id: int
    answer_text: str


class AnswerFeedbackResponse(BaseModel):
    """Immediate evaluation and feedback for submitted answer."""
    question_id: int
    score: float
    technical_accuracy_score: float
    depth_score: float
    practical_application_score: float
    clarity_score: float
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    is_completed: bool
    current_question_index: int
    total_questions: int
    next_question: Optional[QuestionDetail] = None
