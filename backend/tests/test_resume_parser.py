"""Unit tests for ResumeParserService."""

import pytest
from app.services.resume_parser import ResumeParserService


SAMPLE_RESUME_TEXT = """
Alex Mercer
Email: alex.mercer@example.com | Phone: (555) 019-2834

SUMMARY
Applied AI & Machine Learning Engineer with 3+ years of experience developing deep learning models, RAG pipelines, and NLP systems. Proficient in PyTorch, Transformers, Scikit-Learn, and Vector Databases.

CORE SKILLS
- Machine Learning & Deep Learning: Neural Networks, Backpropagation, Decision Trees, Random Forest, XGBoost, SVM, Attention Mechanisms, Transformers, Reinforcement Learning (Q-Learning).
- Frameworks & Tools: Python, PyTorch, Scikit-Learn, FastAPI, Docker, ChromaDB.

EXPERIENCE
Machine Learning Engineer | NeuralScale AI | 2023 - Present
- Deployed Retrieval-Augmented Generation (RAG) system utilizing ChromaDB.
- Fine-tuned PyTorch Transformer models with custom Loss functions.

PROJECTS
- Autonomous Q-Learning Game Agent: Implemented discrete MDP agent with Bellman Optimality.
"""


def test_resume_parser_extracts_candidate_name():
    parsed = ResumeParserService.parse_resume_text(SAMPLE_RESUME_TEXT)
    assert parsed.candidate_name == "Alex Mercer"


def test_resume_parser_extracts_contact_info():
    parsed = ResumeParserService.parse_resume_text(SAMPLE_RESUME_TEXT)
    assert parsed.email == "alex.mercer@example.com"
    assert parsed.phone is not None


def test_resume_parser_extracts_skills():
    parsed = ResumeParserService.parse_resume_text(SAMPLE_RESUME_TEXT)
    skills_lower = [s.lower() for s in parsed.skills]
    
    assert "pytorch" in skills_lower
    assert "backpropagation" in skills_lower
    assert "decision trees" in skills_lower
    assert "transformers" in skills_lower
    assert "rag" in skills_lower or "retrieval-augmented generation" in skills_lower


def test_resume_parser_domain_categorization():
    parsed = ResumeParserService.parse_resume_text(SAMPLE_RESUME_TEXT)
    assert "Machine Learning & AI" in parsed.domain_exposure


def test_resume_parser_experience_years():
    parsed = ResumeParserService.parse_resume_text(SAMPLE_RESUME_TEXT)
    assert parsed.experience_years >= 2.0
