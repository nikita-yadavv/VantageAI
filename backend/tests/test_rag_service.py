"""Unit tests for RAG Knowledge Base and Semantic Retrieval."""

import pytest
from app.services.rag_service import rag_service


def test_rag_service_initialization():
    assert len(rag_service.chunks_by_role) > 0
    assert "ai_ml_engineer" in rag_service.chunks_by_role
    assert "backend_system_design" in rag_service.chunks_by_role


def test_rag_retrieval_ai_ml():
    query = "Explain backpropagation algorithm and error gradient in multilayer neural networks"
    retrieved = rag_service.retrieve_context(
        query=query,
        role="AI / Machine Learning Engineer",
        top_k=2
    )
    
    assert len(retrieved) > 0
    assert retrieved[0]["relevance_score"] > 0
    assert any("neural" in r["content"].lower() or "backpropagation" in r["content"].lower() for r in retrieved)


def test_rag_retrieval_backend_systems():
    query = "Describe cache stampede thundering herd and cache-aside patterns with Redis"
    retrieved = rag_service.retrieve_context(
        query=query,
        role="Backend Engineer / Distributed Systems",
        top_k=2
    )
    
    assert len(retrieved) > 0
    assert any("cache" in r["content"].lower() for r in retrieved)


def test_rag_traceability_metadata():
    retrieved = rag_service.retrieve_context(
        query="Information gain entropy decision trees",
        role="AI / Machine Learning Engineer",
        top_k=1
    )
    
    assert len(retrieved) == 1
    chunk = retrieved[0]
    assert "chunk_id" in chunk
    assert "source_book" in chunk
    assert "chapter_title" in chunk
    assert len(chunk["content"]) > 50
