"""Interview Orchestration Engine.

Coordinates the interactive screening lifecycle: session creation,
grounded question generation, multi-turn state transitions, and answer handling.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.candidate import Candidate, ResumeData
from app.models.session import InterviewSession, Question, CandidateAnswer
from app.schemas.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    QuestionDetail,
    AnswerFeedbackResponse
)
from app.services.rag_service import rag_service
from app.services.llm_provider import llm_provider
from app.core.logging import logger


# Topic sequences for each technical role
ROLE_TOPIC_SEQUENCES = {
    "ai_ml_engineer": [
        "Decision Trees & Information Theory",
        "Neural Networks & Optimization",
        "Regularization & Generalization",
        "Support Vector Machines & Kernel Trick",
        "Reinforcement Learning & Bellman Optimality"
    ],
    "data_science_applied_ml": [
        "Data Preprocessing & Leakage Prevention",
        "Class Imbalance & Resampling",
        "Ensemble Learning & Gradient Boosting",
        "Model Drift & Statistical Monitoring",
        "Logistic Regression & Interpretability"
    ],
    "backend_system_design": [
        "Caching Patterns & Invalidation",
        "Concurrency Models & AsyncIO",
        "Database Sharding & Consistent Hashing",
        "Distributed Transactions & SAGA Pattern",
        "API Security & Rate Limiting"
    ],
    "advanced_theoretical_ml": [
        "Bayesian Inference & Maximum Likelihood",
        "Expectation-Maximization (EM) Algorithm",
        "Attention Mechanism & Transformer Mathematics",
        "Principal Component Analysis (PCA)",
        "Deep Learning Optimization & Loss Landscapes"
    ]
}


class InterviewEngine:
    """Manages state transitions, question generation, and answers for interview sessions."""

    @classmethod
    def start_session(
        cls,
        db: Session,
        request: StartInterviewRequest
    ) -> StartInterviewResponse:
        """Initializes a new interview session and generates the first grounded question."""
        
        # 1. Fetch resume and candidate
        resume = db.query(ResumeData).filter(ResumeData.id == request.resume_id).first()
        if not resume:
            raise ValueError(f"Resume with ID {request.resume_id} not found.")

        candidate = resume.candidate
        if not candidate:
            candidate = Candidate(full_name="Candidate", email="candidate@example.com")
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

        # 2. Create InterviewSession
        session_token = str(uuid.uuid4())
        session = InterviewSession(
            session_token=session_token,
            candidate_id=candidate.id,
            resume_id=resume.id,
            target_role=request.target_role,
            difficulty_level=request.difficulty_level or "intermediate",
            status="in_progress",
            current_question_index=1,
            total_questions=request.total_questions or 5
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # 3. Generate Question #1
        q1 = cls._generate_and_save_question(
            db=db,
            session=session,
            order_index=1,
            resume=resume
        )

        return StartInterviewResponse(
            session_id=session.id,
            session_token=session.session_token,
            candidate_id=candidate.id,
            target_role=session.target_role,
            difficulty_level=session.difficulty_level,
            total_questions=session.total_questions,
            current_question=QuestionDetail(
                id=q1.id,
                order_index=q1.order_index,
                question_text=q1.question_text,
                topic=q1.topic,
                difficulty=q1.difficulty,
                target_role=q1.target_role,
                rag_source_book=q1.rag_source_book,
                rag_context_snippet=q1.rag_context_chunk[:200] + "..." if q1.rag_context_chunk else None
            )
        )

    @classmethod
    def submit_answer(
        cls,
        db: Session,
        session_id: int,
        question_id: int,
        answer_text: str
    ) -> AnswerFeedbackResponse:
        """Processes candidate answer, computes grounded evaluation, and serves next question."""
        
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        question = db.query(Question).filter(Question.id == question_id, Question.session_id == session_id).first()
        if not question:
            raise ValueError(f"Question {question_id} not found in session {session_id}.")

        # Check if question already answered
        existing_answer = db.query(CandidateAnswer).filter(CandidateAnswer.question_id == question_id).first()
        if existing_answer:
            raise ValueError(f"Question {question_id} has already been answered.")

        # 1. Evaluate answer against textbook rubric & RAG context
        eval_result = llm_provider.evaluate_candidate_answer(
            question_text=question.question_text,
            topic=question.topic,
            ideal_rubric=question.ideal_answer_rubric or "",
            rag_context=question.rag_context_chunk or "",
            candidate_answer=answer_text,
            difficulty=question.difficulty
        )

        # 2. Save candidate answer
        answer_record = CandidateAnswer(
            question_id=question.id,
            session_id=session.id,
            answer_text=answer_text,
            score=eval_result["score"],
            technical_accuracy_score=eval_result["technical_accuracy_score"],
            depth_score=eval_result["depth_score"],
            practical_application_score=eval_result["practical_application_score"],
            clarity_score=eval_result["clarity_score"],
            feedback=eval_result["feedback"],
            strengths=eval_result["strengths"],
            areas_for_improvement=eval_result["areas_for_improvement"]
        )
        db.add(answer_record)
        db.commit()

        # 3. Check if all questions are completed
        is_completed = session.current_question_index >= session.total_questions
        next_question_detail = None

        if is_completed:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.commit()
            
            # Lazy import to avoid circular dependency
            from app.services.evaluation_service import evaluation_service
            evaluation_service.finalize_session_report(db, session.id)
        else:
            # Advance to next question
            session.current_question_index += 1
            db.commit()
            
            resume = db.query(ResumeData).filter(ResumeData.id == session.resume_id).first()
            next_q = cls._generate_and_save_question(
                db=db,
                session=session,
                order_index=session.current_question_index,
                resume=resume
            )
            next_question_detail = QuestionDetail(
                id=next_q.id,
                order_index=next_q.order_index,
                question_text=next_q.question_text,
                topic=next_q.topic,
                difficulty=next_q.difficulty,
                target_role=next_q.target_role,
                rag_source_book=next_q.rag_source_book,
                rag_context_snippet=next_q.rag_context_chunk[:200] + "..." if next_q.rag_context_chunk else None
            )

        return AnswerFeedbackResponse(
            question_id=question.id,
            score=eval_result["score"],
            technical_accuracy_score=eval_result["technical_accuracy_score"],
            depth_score=eval_result["depth_score"],
            practical_application_score=eval_result["practical_application_score"],
            clarity_score=eval_result["clarity_score"],
            feedback=eval_result["feedback"],
            strengths=eval_result["strengths"],
            areas_for_improvement=eval_result["areas_for_improvement"],
            is_completed=is_completed,
            current_question_index=session.current_question_index,
            total_questions=session.total_questions,
            next_question=next_question_detail
        )

    @classmethod
    def _generate_and_save_question(
        cls,
        db: Session,
        session: InterviewSession,
        order_index: int,
        resume: Optional[ResumeData]
    ) -> Question:
        """Retrieves role-specific RAG context and crafts a grounded interview question."""
        
        role_key = rag_service._normalize_role_key(session.target_role)
        topics = ROLE_TOPIC_SEQUENCES.get(role_key, ROLE_TOPIC_SEQUENCES["ai_ml_engineer"])
        topic_idx = (order_index - 1) % len(topics)
        target_topic = topics[topic_idx]

        # Extract resume attributes
        skills = resume.skills if resume else []
        candidate_summary = resume.summary if resume else "Experienced candidate."

        # RAG Retrieval
        retrieved_chunks = rag_service.retrieve_context(
            query=f"{target_topic} {session.target_role}",
            role=session.target_role,
            top_k=2,
            candidate_skills=skills
        )
        rag_context = rag_service.format_rag_context_for_prompt(retrieved_chunks)
        primary_source = retrieved_chunks[0].get("source_book", "Foundational Textbook") if retrieved_chunks else "Textbook"

        # Generate Question
        q_data = llm_provider.generate_interview_question(
            role=session.target_role,
            difficulty=session.difficulty_level,
            topic=target_topic,
            order_index=order_index,
            rag_context=rag_context,
            candidate_skills=skills,
            candidate_summary=candidate_summary
        )

        question = Question(
            session_id=session.id,
            order_index=order_index,
            question_text=q_data.get("question_text", "Explain core algorithmic principles."),
            topic=target_topic,
            difficulty=session.difficulty_level,
            target_role=session.target_role,
            rag_context_chunk=rag_context,
            rag_source_book=primary_source,
            rag_relevance_score=retrieved_chunks[0].get("relevance_score", 1.0) if retrieved_chunks else 1.0,
            ideal_answer_rubric=q_data.get("ideal_answer_rubric", "Candidate should cover conceptual depth and tradeoffs.")
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question
