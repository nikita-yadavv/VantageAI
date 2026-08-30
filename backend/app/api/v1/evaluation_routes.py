"""Evaluation & Performance Reporting API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.schemas.evaluation import SessionReportResponse
from app.services.evaluation_service import evaluation_service
from app.core.logging import logger

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/{session_id}/report", response_model=SessionReportResponse)
def get_session_evaluation_report(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves full evaluation report card, rubric scoring, strengths, and RAG citations."""
    try:
        report = evaluation_service.get_full_session_report(db=db, session_id=session_id)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{session_id}/export-json")
def export_session_evaluation_json(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Exports session evaluation report as downloadable JSON payload."""
    try:
        report = evaluation_service.get_full_session_report(db=db, session_id=session_id)
        report_dict = report.model_dump(mode="json")
        
        return JSONResponse(
            content=report_dict,
            headers={
                "Content-Disposition": f"attachment; filename=candidate_screening_report_{session_id}.json"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
