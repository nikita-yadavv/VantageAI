"""Interview Session and Question/Answer ORM Models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class InterviewSession(Base):
    """Tracks the state and progression of an interactive technical interview."""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(100), unique=True, index=True, nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resume_data.id"), nullable=True)
    
    target_role = Column(String(100), nullable=False)  # e.g., "AI/ML Engineer", "Backend Engineer"
    difficulty_level = Column(String(50), default="intermediate")
    status = Column(String(50), default="in_progress")  # pending, in_progress, completed
    
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="sessions")
    resume = relationship("ResumeData", back_populates="sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan", order_by="Question.order_index")
    answers = relationship("CandidateAnswer", back_populates="session", cascade="all, delete-orphan")
    evaluation = relationship("SessionEvaluation", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Question(Base):
    """Individual interview question generated dynamically via RAG and candidate context."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    
    question_text = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(50), default="intermediate")
    target_role = Column(String(100), nullable=False)
    
    # RAG Grounding Traceability
    rag_context_chunk = Column(Text, nullable=True)
    rag_source_book = Column(String(255), nullable=True)
    rag_relevance_score = Column(Float, nullable=True)
    
    # Evaluation benchmark
    ideal_answer_rubric = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("CandidateAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class CandidateAnswer(Base):
    """Candidate's response to a specific question, including rubric-based evaluation."""
    __tablename__ = "candidate_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, unique=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    
    answer_text = Column(Text, nullable=False)
    
    # Scoring & Feedback metrics
    score = Column(Float, default=0.0)  # 0.0 - 10.0
    technical_accuracy_score = Column(Float, default=0.0)
    depth_score = Column(Float, default=0.0)
    practical_application_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, default=list)
    areas_for_improvement = Column(JSON, default=list)
    
    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="answer")
    session = relationship("InterviewSession", back_populates="answers")
