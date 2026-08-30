"""Final Session Evaluation & Performance Report ORM Model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SessionEvaluation(Base):
    """Aggregate evaluation report card for an entire candidate interview session."""
    __tablename__ = "session_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    
    overall_score = Column(Float, nullable=False, default=0.0)  # 0.0 - 100.0
    recommendation = Column(String(50), nullable=False)  # Strong Hire, Hire, Leaning Hire, Leaning Reject, Reject
    executive_summary = Column(Text, nullable=False)
    
    # Structured breakdown
    category_scores = Column(JSON, default=dict)  # {"Foundational ML": 8.5, "System Design": 9.0, ...}
    key_strengths = Column(JSON, default=list)
    areas_for_growth = Column(JSON, default=list)
    rag_grounding_summary = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="evaluation")
