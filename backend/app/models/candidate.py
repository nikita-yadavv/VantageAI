"""Candidate and Resume ORM Models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Candidate(Base):
    """Represents a job candidate applying for technical screening."""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, default="Anonymous Candidate")
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resumes = relationship("ResumeData", back_populates="candidate", cascade="all, delete-orphan")
    sessions = relationship("InterviewSession", back_populates="candidate", cascade="all, delete-orphan")


class ResumeData(Base):
    """Structured parsed data extracted from uploaded candidate resume."""
    __tablename__ = "resume_data"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    file_name = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    
    # Structured extracted entities
    skills = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    domain_exposure = Column(JSON, default=list)
    experience_years = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    projects = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    sessions = relationship("InterviewSession", back_populates="resume")
