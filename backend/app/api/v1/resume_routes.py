"""Resume Upload and Parsing API Endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.candidate import Candidate, ResumeData
from app.schemas.resume import ResumeUploadResponse, ResumeParseRequest, ExtractedResumeData
from app.services.resume_parser import ResumeParserService
from app.core.logging import logger

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Uploads a candidate resume (PDF or TXT), extracts skills and entities, and persists record."""
    try:
        content_bytes = await file.read()
        file_name = file.filename or "uploaded_resume.txt"

        if file_name.lower().endswith(".pdf"):
            raw_text = ResumeParserService.extract_text_from_pdf(content_bytes)
        else:
            raw_text = content_bytes.decode("utf-8", errors="ignore")

        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume content is empty or unreadable."
            )

        # Parse entities
        parsed = ResumeParserService.parse_resume_text(raw_text, file_name=file_name)
        
        # Override with explicit form fields if provided
        final_name = candidate_name or parsed.candidate_name
        final_email = email or parsed.email
        final_phone = phone or parsed.phone

        # Create or fetch candidate
        candidate = Candidate(
            full_name=final_name,
            email=final_email,
            phone=final_phone
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        # Create Resume record
        resume_record = ResumeData(
            candidate_id=candidate.id,
            file_name=file_name,
            raw_text=raw_text,
            skills=parsed.skills,
            technologies=parsed.technologies,
            domain_exposure=parsed.domain_exposure,
            experience_years=parsed.experience_years,
            summary=parsed.summary,
            projects=parsed.projects
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        parsed.candidate_name = final_name
        parsed.email = final_email
        parsed.phone = final_phone

        return ResumeUploadResponse(
            resume_id=resume_record.id,
            candidate_id=candidate.id,
            file_name=file_name,
            parsed_data=parsed,
            message="Resume successfully parsed and indexed."
        )

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process resume: {str(e)}")


@router.post("/parse-text", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def parse_raw_text(
    payload: ResumeParseRequest,
    db: Session = Depends(get_db)
):
    """Parses raw plain-text resume input (for manual testing or clipboard pasting)."""
    try:
        raw_text = payload.raw_text.strip()
        if not raw_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Raw text cannot be empty.")

        parsed = ResumeParserService.parse_resume_text(raw_text, file_name=payload.file_name)
        
        final_name = payload.candidate_name or parsed.candidate_name
        final_email = payload.email or parsed.email

        candidate = Candidate(
            full_name=final_name,
            email=final_email
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        resume_record = ResumeData(
            candidate_id=candidate.id,
            file_name=payload.file_name or "text_input.txt",
            raw_text=raw_text,
            skills=parsed.skills,
            technologies=parsed.technologies,
            domain_exposure=parsed.domain_exposure,
            experience_years=parsed.experience_years,
            summary=parsed.summary,
            projects=parsed.projects
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        parsed.candidate_name = final_name
        parsed.email = final_email

        return ResumeUploadResponse(
            resume_id=resume_record.id,
            candidate_id=candidate.id,
            file_name=payload.file_name or "text_input.txt",
            parsed_data=parsed,
            message="Resume text parsed successfully."
        )

    except Exception as e:
        logger.error(f"Text parsing failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{resume_id}", response_model=ResumeUploadResponse)
async def get_resume_details(resume_id: int, db: Session = Depends(get_db)):
    """Fetches previously parsed resume metadata by ID."""
    resume = db.query(ResumeData).filter(ResumeData.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume {resume_id} not found.")

    candidate = resume.candidate
    parsed = ExtractedResumeData(
        candidate_name=candidate.full_name if candidate else "Candidate",
        email=candidate.email if candidate else None,
        phone=candidate.phone if candidate else None,
        skills=resume.skills or [],
        technologies=resume.technologies or [],
        domain_exposure=resume.domain_exposure or [],
        experience_years=resume.experience_years or 0.0,
        summary=resume.summary or "",
        projects=resume.projects or []
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        candidate_id=candidate.id if candidate else 0,
        file_name=resume.file_name or "resume.txt",
        parsed_data=parsed
    )
