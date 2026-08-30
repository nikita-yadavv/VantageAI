"""RAG Knowledge Base Inspection and Query API Endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])


class RAGQueryRequest(BaseModel):
    query: str
    role: str = "AI / Machine Learning Engineer"
    top_k: Optional[int] = 3


@router.get("/roles")
def list_supported_roles():
    """Lists supported technical screening roles and their mapped foundational textbooks."""
    return [
        {
            "role_id": "ai_ml_engineer",
            "display_name": "AI / Machine Learning Engineer",
            "description": "Evaluates foundational algorithms, backpropagation, decision trees, regularization, and RL.",
            "textbook_sources": [
                "Machine Learning — Tom Mitchell",
                "The Hundred-Page Machine Learning Book — Andriy Burkov"
            ]
        },
        {
            "role_id": "data_science_applied_ml",
            "display_name": "Data Science / Applied ML",
            "description": "Evaluates data pipelines, class imbalance, gradient boosting, drift monitoring, and Scikit-Learn.",
            "textbook_sources": [
                "Master Machine Learning Algorithms — Jason Brownlee",
                "Introduction to Machine Learning with Python — Applied Workflows"
            ]
        },
        {
            "role_id": "backend_system_design",
            "display_name": "Backend Engineer / Distributed Systems",
            "description": "Evaluates caching patterns, AsyncIO concurrency, database sharding, CAP theorem, and rate limiting.",
            "textbook_sources": [
                "High-Scale Distributed Systems Architecture",
                "API Architecture, Concurrency & Security Engineering"
            ]
        },
        {
            "role_id": "advanced_theoretical_ml",
            "display_name": "Advanced / Theoretical ML",
            "description": "Evaluates Bayesian inference, EM algorithm, Attention mechanism mathematics, and optimization theory.",
            "textbook_sources": [
                "Pattern Recognition and Machine Learning — Christopher Bishop",
                "Deep Learning Theory, Optimization & Transformer Architecture"
            ]
        }
    ]


@router.post("/query")
def query_knowledge_base(payload: RAGQueryRequest):
    """Inspects RAG retrieval output for any arbitrary query and role."""
    results = rag_service.retrieve_context(
        query=payload.query,
        role=payload.role,
        top_k=payload.top_k or 3
    )
    return {
        "query": payload.query,
        "role": payload.role,
        "total_retrieved": len(results),
        "chunks": results
    }
