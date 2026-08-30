"""Interview Session and Question Orchestration Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models.session import InterviewSession, Question
from app.schemas.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    QuestionDetail,
    SubmitAnswerRequest,
    AnswerFeedbackResponse
)
from app.services.interview_engine import InterviewEngine
from app.core.logging import logger

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start", response_model=StartInterviewResponse, status_code=status.HTTP_201_CREATED)
def start_interview_session(
    request: StartInterviewRequest,
    db: Session = Depends(get_db)
):
    """Starts a new technical screening interview session and serves the first grounded question."""
    try:
        response = InterviewEngine.start_session(db=db, request=request)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to start interview session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Interview session error: {str(e)}")


@router.get("/{session_id}/current-question", response_model=QuestionDetail)
def get_current_question(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves the active question for a session."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")

    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This interview session is already completed.")

    question = db.query(Question).filter(
        Question.session_id == session_id,
        Question.order_index == session.current_question_index
    ).first()

    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active question not found.")

    return QuestionDetail(
        id=question.id,
        order_index=question.order_index,
        question_text=question.question_text,
        topic=question.topic,
        difficulty=question.difficulty,
        target_role=question.target_role,
        rag_source_book=question.rag_source_book,
        rag_context_snippet=question.rag_context_chunk[:250] + "..." if question.rag_context_chunk else None
    )


@router.post("/{session_id}/submit-answer", response_model=AnswerFeedbackResponse)
def submit_interview_answer(
    session_id: int,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """Submits candidate's answer, scores against RAG textbook ground-truth, and returns next question."""
    try:
        feedback = InterviewEngine.submit_answer(
            db=db,
            session_id=session_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text
        )
        return feedback
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error evaluating answer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{session_id}/status")
def get_session_status(session_id: int, db: Session = Depends(get_db)):
    """Fetches session metadata and progress."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")

    return {
        "session_id": session.id,
        "session_token": session.session_token,
        "target_role": session.target_role,
        "status": session.status,
        "current_question_index": session.current_question_index,
        "total_questions": session.total_questions,
        "created_at": session.created_at,
        "completed_at": session.completed_at
    }
