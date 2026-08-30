"""Integration tests for all FastAPI REST endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine, Base

# Ensure tables exist for test client
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ai_ml_engineer" in data["rag_roles_indexed"]
    assert data["total_rag_chunks"] > 0


def test_list_supported_roles_endpoint():
    response = client.get("/api/v1/rag/roles")
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) >= 4
    assert any(r["role_id"] == "ai_ml_engineer" for r in roles)
    assert any(r["role_id"] == "backend_system_design" for r in roles)


def test_rag_query_inspection_endpoint():
    response = client.post(
        "/api/v1/rag/query",
        json={"query": "Explain entropy and information gain in decision trees", "role": "AI / Machine Learning Engineer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_retrieved"] > 0
    assert len(data["chunks"]) > 0


def test_parse_text_resume_endpoint():
    payload = {
        "raw_text": "Alex Mercer | Machine Learning Engineer | Skills: PyTorch, Transformers, Backpropagation, RAG, Docker",
        "candidate_name": "Alex Mercer",
        "email": "alex@example.com"
    }
    response = client.post("/api/v1/resume/parse-text", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["resume_id"] is not None
    assert data["parsed_data"]["candidate_name"] == "Alex Mercer"
    assert "PyTorch" in data["parsed_data"]["skills"]


def test_full_screening_lifecycle_via_api():
    # 1. Parse Resume
    res = client.post(
        "/api/v1/resume/parse-text",
        json={
            "raw_text": "Jordan Hayes | Backend Engineer | Skills: FastAPI, Redis, Kafka, Concurrency, Sharding",
            "candidate_name": "Jordan Hayes",
            "email": "jordan@example.com"
        }
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    # 2. Start Interview Session
    start_res = client.post(
        "/api/v1/interview/start",
        json={
            "resume_id": resume_id,
            "target_role": "Backend Engineer / Distributed Systems",
            "difficulty_level": "intermediate",
            "total_questions": 1
        }
    )
    assert start_res.status_code == 201
    session_data = start_res.json()
    session_id = session_data["session_id"]
    question_id = session_data["current_question"]["id"]

    # 3. Submit Answer
    answer_res = client.post(
        f"/api/v1/interview/{session_id}/submit-answer",
        json={
            "question_id": question_id,
            "answer_text": "Cache-Aside reads from cache first. On a miss, it fetches from the database and populates Redis. Mutex locks prevent cache stampedes under high QPS."
        }
    )
    assert answer_res.status_code == 200
    answer_data = answer_res.json()
    assert answer_data["is_completed"] is True
    assert answer_data["score"] >= 5.0

    # 4. Fetch Final Evaluation Report
    report_res = client.get(f"/api/v1/evaluation/{session_id}/report")
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["overall_score"] > 0
    assert report["candidate_name"] == "Jordan Hayes"
    assert len(report["questions_review"]) == 1
