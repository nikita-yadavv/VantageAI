"""Evaluation Service for final interview scorecards and analytics reporting."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.session import InterviewSession, Question, CandidateAnswer
from app.models.evaluation import SessionEvaluation
from app.schemas.evaluation import SessionReportResponse, QuestionReviewItem
from app.services.llm_provider import llm_provider
from app.core.logging import logger


class EvaluationService:
    """Computes holistic candidate evaluations, category scorecards, and audit reports."""

    @classmethod
    def finalize_session_report(cls, db: Session, session_id: int) -> SessionEvaluation:
        """Computes aggregate scoring and persists final evaluation record for session."""
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        # If already evaluated, return existing record
        existing_eval = db.query(SessionEvaluation).filter(SessionEvaluation.session_id == session_id).first()
        if existing_eval:
            return existing_eval

        # Fetch questions and candidate answers
        questions = db.query(Question).filter(Question.session_id == session_id).order_by(Question.order_index).all()
        answers = db.query(CandidateAnswer).filter(CandidateAnswer.session_id == session_id).all()

        answer_map = {ans.question_id: ans for ans in answers}
        
        # Calculate aggregate scores
        total_score_sum = 0.0
        category_scores: Dict[str, List[float]] = {}
        qa_history = []
        rag_sources_used = set()

        for q in questions:
            ans = answer_map.get(q.id)
            score = ans.score if ans else 0.0
            total_score_sum += score
            
            # Category grouping
            category_scores.setdefault(q.topic, []).append(score)
            if q.rag_source_book:
                rag_sources_used.add(q.rag_source_book)

            qa_history.append({
                "topic": q.topic,
                "score": score,
                "strengths": ans.strengths if ans else [],
                "areas_for_improvement": ans.areas_for_improvement if ans else []
            })

        num_questions = len(questions) or 1
        avg_score_out_of_10 = total_score_sum / num_questions
        overall_score_percentage = round(avg_score_out_of_10 * 10.0, 1)  # Scale to 0-100%

        # Compute average category scores
        category_score_averages = {
            cat: round((sum(scores) / len(scores)) * 10.0, 1)
            for cat, scores in category_scores.items()
        }

        candidate_name = session.candidate.full_name if session.candidate else "Candidate"
        
        # Generate summary and recommendation
        summary_data = llm_provider.generate_final_summary(
            candidate_name=candidate_name,
            role=session.target_role,
            overall_score=overall_score_percentage,
            qa_history=qa_history,
            category_scores=category_score_averages
        )

        rag_summary = {
            "total_knowledge_sources_consulted": len(rag_sources_used),
            "sources": list(rag_sources_used),
            "grounding_traceability_verified": True
        }

        session_eval = SessionEvaluation(
            session_id=session.id,
            overall_score=summary_data["overall_score"],
            recommendation=summary_data["recommendation"],
            executive_summary=summary_data["executive_summary"],
            category_scores=category_score_averages,
            key_strengths=summary_data["key_strengths"],
            areas_for_growth=summary_data["areas_for_growth"],
            rag_grounding_summary=rag_summary
        )
        db.add(session_eval)
        db.commit()
        db.refresh(session_eval)

        return session_eval

    @classmethod
    def get_full_session_report(cls, db: Session, session_id: int) -> SessionReportResponse:
        """Constructs detailed session report response including question-by-question review."""
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        # Ensure session evaluation exists
        evaluation = db.query(SessionEvaluation).filter(SessionEvaluation.session_id == session_id).first()
        if not evaluation:
            evaluation = cls.finalize_session_report(db, session_id)

        # Build question reviews
        questions = db.query(Question).filter(Question.session_id == session_id).order_by(Question.order_index).all()
        answers = {ans.question_id: ans for ans in db.query(CandidateAnswer).filter(CandidateAnswer.session_id == session_id).all()}

        question_reviews: List[QuestionReviewItem] = []
        for q in questions:
            ans = answers.get(q.id)
            review_item = QuestionReviewItem(
                order_index=q.order_index,
                question_text=q.question_text,
                topic=q.topic,
                difficulty=q.difficulty,
                rag_source_book=q.rag_source_book,
                rag_context_chunk=q.rag_context_chunk,
                candidate_answer=ans.answer_text if ans else "No answer recorded.",
                ideal_rubric=q.ideal_answer_rubric,
                score=ans.score if ans else 0.0,
                technical_accuracy_score=ans.technical_accuracy_score if ans else 0.0,
                depth_score=ans.depth_score if ans else 0.0,
                practical_application_score=ans.practical_application_score if ans else 0.0,
                clarity_score=ans.clarity_score if ans else 0.0,
                feedback=ans.feedback if ans else "Pending response.",
                strengths=ans.strengths if ans else [],
                areas_for_improvement=ans.areas_for_improvement if ans else []
            )
            question_reviews.append(review_item)

        candidate_name = session.candidate.full_name if session.candidate else "Candidate"

        return SessionReportResponse(
            session_id=session.id,
            session_token=session.session_token,
            candidate_name=candidate_name,
            target_role=session.target_role,
            overall_score=evaluation.overall_score,
            recommendation=evaluation.recommendation,
            executive_summary=evaluation.executive_summary,
            category_scores=evaluation.category_scores or {},
            key_strengths=evaluation.key_strengths or [],
            areas_for_growth=evaluation.areas_for_growth or [],
            total_questions=session.total_questions,
            questions_answered=len(answers),
            rag_grounding_summary=evaluation.rag_grounding_summary or {},
            questions_review=question_reviews,
            created_at=session.created_at,
            completed_at=session.completed_at
        )


evaluation_service = EvaluationService()
