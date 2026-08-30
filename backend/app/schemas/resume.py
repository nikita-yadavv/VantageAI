"""Pydantic schemas for Resume parsing and candidate payloads."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedResumeData(BaseModel):
    """Structured fields parsed from resume text/PDF."""
    candidate_name: str = Field(default="Candidate", description="Detected candidate name")
    email: Optional[str] = Field(default=None, description="Contact email")
    phone: Optional[str] = Field(default=None, description="Contact phone")
    skills: List[str] = Field(default_factory=list, description="Extracted core skills")
    technologies: List[str] = Field(default_factory=list, description="Frameworks and tools")
    domain_exposure: List[str] = Field(default_factory=list, description="Domains such as RAG, Distributed Systems, ML")
    experience_years: float = Field(default=1.0, description="Estimated years of experience")
    summary: str = Field(default="", description="High-level candidate profile summary")
    projects: List[str] = Field(default_factory=list, description="Highlighted projects")


class ResumeUploadResponse(BaseModel):
    """Response payload returned after uploading/parsing a resume."""
    resume_id: int
    candidate_id: int
    file_name: str
    parsed_data: ExtractedResumeData
    message: str = "Resume parsed successfully"


class ResumeParseRequest(BaseModel):
    """Manual raw text resume parsing request."""
    raw_text: str
    file_name: Optional[str] = "manual_entry.txt"
    candidate_name: Optional[str] = None
    email: Optional[str] = None
