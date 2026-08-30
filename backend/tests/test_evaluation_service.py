"""Unit tests for EvaluationService and session scorecard reports."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.candidate import Candidate, ResumeData
from app.models.session import InterviewSession, Question, CandidateAnswer
from app.services.evaluation_service import evaluation_service


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_finalize_session_report(test_db):
    candidate = Candidate(full_name="Priya Sharma", email="priya@example.com")
    test_db.add(candidate)
    test_db.commit()

    resume = ResumeData(
        candidate_id=candidate.id,
        raw_text="Data Science, Scikit-Learn, XGBoost, SMOTE",
        skills=["Scikit-Learn", "XGBoost", "SMOTE"]
    )
    test_db.add(resume)
    test_db.commit()

    session = InterviewSession(
        session_token="test-eval-token",
        candidate_id=candidate.id,
        resume_id=resume.id,
        target_role="Data Science / Applied ML",
        status="completed",
        current_question_index=2,
        total_questions=2
    )
    test_db.add(session)
    test_db.commit()

    q1 = Question(
        session_id=session.id,
        order_index=1,
        question_text="Explain data leakage in Scikit-Learn pipelines.",
        topic="Data Preprocessing & Leakage Prevention",
        difficulty="intermediate",
        target_role=session.target_role,
        rag_source_book="Master Machine Learning Algorithms — Jason Brownlee",
        rag_context_chunk="Pipelines ensure fit occurs only on train folds."
    )
    test_db.add(q1)
    test_db.commit()

    ans1 = CandidateAnswer(
        question_id=q1.id,
        session_id=session.id,
        answer_text="Fitting scalers on test data causes data leakage. Pipelines guarantee strict split isolation.",
        score=8.5,
        technical_accuracy_score=9.0,
        depth_score=8.0,
        practical_application_score=8.5,
        clarity_score=9.0,
        feedback="Excellent explanation of pipeline containment.",
        strengths=["Accurate definition of data leakage"],
        areas_for_improvement=["Could mention time-series lookahead splits"]
    )
    test_db.add(ans1)
    test_db.commit()

    # Generate Report
    report = evaluation_service.get_full_session_report(test_db, session.id)

    assert report.overall_score >= 70.0
    assert report.recommendation in ["Principal Mastery", "Advanced Proficiency", "Demonstrated Competency"]
    assert len(report.questions_review) == 1
    assert report.questions_review[0].score == 8.5
    assert len(report.key_strengths) > 0
