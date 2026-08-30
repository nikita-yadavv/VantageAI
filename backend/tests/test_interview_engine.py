"""Unit and Integration tests for InterviewEngine and Session Lifecycle."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.candidate import Candidate, ResumeData
from app.schemas.interview import StartInterviewRequest
from app.services.interview_engine import InterviewEngine


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


def test_start_interview_session(test_db):
    # Setup candidate & resume
    candidate = Candidate(full_name="Alex Mercer", email="alex@example.com")
    test_db.add(candidate)
    test_db.commit()

    resume = ResumeData(
        candidate_id=candidate.id,
        raw_text="PyTorch, Transformers, Decision Trees, Backpropagation",
        skills=["PyTorch", "Transformers", "Decision Trees", "Backpropagation"]
    )
    test_db.add(resume)
    test_db.commit()

    # Start session
    req = StartInterviewRequest(
        resume_id=resume.id,
        candidate_id=candidate.id,
        target_role="AI / Machine Learning Engineer",
        total_questions=3
    )

    response = InterviewEngine.start_session(test_db, req)
    assert response.session_id is not None
    assert response.session_token is not None
    assert response.current_question.order_index == 1
    assert "Decision Tree" in response.current_question.topic or "Neural" in response.current_question.topic or len(response.current_question.question_text) > 20


def test_submit_answer_and_progression(test_db):
    candidate = Candidate(full_name="Jordan Hayes", email="jordan@example.com")
    test_db.add(candidate)
    test_db.commit()

    resume = ResumeData(
        candidate_id=candidate.id,
        raw_text="FastAPI, Redis, Kafka, Concurrency, Sharding",
        skills=["FastAPI", "Redis", "Kafka"]
    )
    test_db.add(resume)
    test_db.commit()

    # Start session with 2 questions
    req = StartInterviewRequest(
        resume_id=resume.id,
        candidate_id=candidate.id,
        target_role="Backend Engineer / Distributed Systems",
        total_questions=2
    )
    start_res = InterviewEngine.start_session(test_db, req)
    
    # Submit Answer 1
    ans1_text = (
        "In Cache-Aside, the application queries the cache first. On a cache miss, it reads from the database "
        "and updates the cache. To prevent a cache stampede, we use mutex locks or singleflight patterns with Redis SETNX."
    )
    feedback1 = InterviewEngine.submit_answer(
        db=test_db,
        session_id=start_res.session_id,
        question_id=start_res.current_question.id,
        answer_text=ans1_text
    )

    assert feedback1.score >= 5.0
    assert feedback1.is_completed is False
    assert feedback1.next_question is not None
    assert feedback1.next_question.order_index == 2

    # Submit Answer 2 (Final Question)
    ans2_text = (
        "AsyncIO single-threaded event loops use non-blocking multiplexed I/O like epoll/kqueue. "
        "For CPU-intensive workloads that block the GIL, we must offload tasks to a ProcessPoolExecutor."
    )
    feedback2 = InterviewEngine.submit_answer(
        db=test_db,
        session_id=start_res.session_id,
        question_id=feedback1.next_question.id,
        answer_text=ans2_text
    )

    assert feedback2.is_completed is True
    assert feedback2.score >= 5.0
