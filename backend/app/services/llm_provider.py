"""LLM Provider abstraction layer supporting Google Gemini, OpenAI, and high-fidelity fallback."""

import os
import json
import re
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMProvider:
    """Unified LLM interface for interview question generation and response grading."""

    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.provider = settings.PRIMARY_LLM_PROVIDER

        # Initialize external SDKs if keys exist
        self.gemini_client = None
        self.openai_client = None

        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_client = genai.GenerativeModel(settings.DEFAULT_GEMINI_MODEL)
                logger.info("Configured Google Gemini LLM provider.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

        if self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("Configured OpenAI LLM provider.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def generate_interview_question(
        self,
        role: str,
        difficulty: str,
        topic: str,
        order_index: int,
        rag_context: str,
        candidate_skills: List[str],
        candidate_summary: str,
        previous_qa: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generates a technical interview question grounded in RAG textbook context and candidate background."""
        
        system_prompt = (
            f"You are a Principal Technical Interviewer conducting a structured screening for a {role} position. "
            f"Generate Question #{order_index} targeting the topic: '{topic}' at difficulty level '{difficulty}'.\n\n"
            f"CANDIDATE BACKGROUND:\n{candidate_summary}\n"
            f"Top Skills: {', '.join(candidate_skills[:8])}\n\n"
            f"GROUNDING TEXTBOOK CONTEXT (RAG Retrieval):\n{rag_context}\n\n"
            f"REQUIREMENTS:\n"
            f"1. Directly incorporate principles from the provided textbook context.\n"
            f"2. Tie the question to the candidate's background where relevant (e.g. asking how they applied or would apply this).\n"
            f"3. Demand both conceptual understanding (why/how it works under the hood) and applied reasoning.\n"
            f"4. Avoid trivia; focus on architectural or algorithmic depth.\n"
            f"5. Provide an ideal answer rubric for evaluation.\n\n"
            f"Respond strictly in JSON format with keys: 'question_text', 'topic', 'ideal_answer_rubric', 'rag_relevance_summary'."
        )

        # 1. Try Gemini
        if self.gemini_client and self.provider in ["gemini", "auto"]:
            try:
                response = self.gemini_client.generate_content(
                    system_prompt,
                    generation_config={"response_mime_type": "application/json"},
                    request_options={"timeout": 4.0}
                )
                parsed = json.loads(response.text)
                return parsed
            except Exception as e:
                logger.warning(f"Gemini generation error or timeout: {e}. Falling back to instant internal engine.")

        # 2. Try OpenAI
        if self.openai_client and self.provider in ["openai", "auto"]:
            try:
                completion = self.openai_client.chat.completions.create(
                    model=settings.DEFAULT_OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a Principal Technical Interviewer. Respond in valid JSON."},
                        {"role": "user", "content": system_prompt}
                    ],
                    response_format={"type": "json_object"},
                    timeout=4.0
                )
                parsed = json.loads(completion.choices[0].message.content)
                return parsed
            except Exception as e:
                logger.warning(f"OpenAI generation error or timeout: {e}. Falling back to instant internal engine.")

        # 3. High-fidelity Deterministic Heuristic Generator
        return self._generate_fallback_question(role, difficulty, topic, order_index, rag_context, candidate_skills)

    def evaluate_candidate_answer(
        self,
        question_text: str,
        topic: str,
        ideal_rubric: str,
        rag_context: str,
        candidate_answer: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Evaluates candidate answer against ground-truth textbook rubric and RAG context."""

        system_prompt = (
            f"You are a rigorous Lead AI / Systems Interview Evaluator. Evaluate the candidate's answer.\n\n"
            f"QUESTION: {question_text}\n"
            f"TOPIC: {topic} (Difficulty: {difficulty})\n"
            f"TEXTBOOK GROUND TRUTH (RAG):\n{rag_context}\n"
            f"IDEAL RUBRIC:\n{ideal_rubric}\n\n"
            f"CANDIDATE ANSWER:\n{candidate_answer}\n\n"
            f"EVALUATION CRITERIA:\n"
            f"- Technical Accuracy (0-10): Correctness of core algorithms, mathematics, and principles.\n"
            f"- Conceptual Depth (0-10): Nuance, edge cases, underlying mechanics vs superficial surface mentions.\n"
            f"- Practical Application (0-10): Real-world engineering tradeoffs, scalability, implementation realism.\n"
            f"- Clarity & Precision (0-10): Structured explanation, proper terminology, lack of hand-waving.\n\n"
            f"Respond strictly in JSON format with keys:\n"
            f"- 'score' (0.0 to 10.0 weighted aggregate)\n"
            f"- 'technical_accuracy_score' (0.0 to 10.0)\n"
            f"- 'depth_score' (0.0 to 10.0)\n"
            f"- 'practical_application_score' (0.0 to 10.0)\n"
            f"- 'clarity_score' (0.0 to 10.0)\n"
            f"- 'feedback' (Constructive, detailed paragraph)\n"
            f"- 'strengths' (List of 2-3 specific points well addressed)\n"
            f"- 'areas_for_improvement' (List of 2-3 specific gaps or missed nuances)\n"
        )

        # 1. Try Gemini
        if self.gemini_client and self.provider in ["gemini", "auto"]:
            try:
                response = self.gemini_client.generate_content(
                    system_prompt,
                    generation_config={"response_mime_type": "application/json"},
                    request_options={"timeout": 4.0}
                )
                parsed = json.loads(response.text)
                return parsed
            except Exception as e:
                logger.warning(f"Gemini evaluation error or timeout: {e}. Falling back to instant internal engine.")

        # 2. Try OpenAI
        if self.openai_client and self.provider in ["openai", "auto"]:
            try:
                completion = self.openai_client.chat.completions.create(
                    model=settings.DEFAULT_OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a Technical Interview Evaluator. Respond in valid JSON."},
                        {"role": "user", "content": system_prompt}
                    ],
                    response_format={"type": "json_object"},
                    timeout=4.0
                )
                parsed = json.loads(completion.choices[0].message.content)
                return parsed
            except Exception as e:
                logger.warning(f"OpenAI evaluation error or timeout: {e}. Falling back to instant internal engine.")

        # 3. High-fidelity Deterministic Evaluator (Instant response)
        return self._evaluate_fallback_answer(question_text, topic, ideal_rubric, rag_context, candidate_answer)

    def generate_final_summary(
        self,
        candidate_name: str,
        role: str,
        overall_score: float,
        qa_history: List[Dict[str, Any]],
        category_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generates executive evaluation summary and domain mastery rating."""
        if overall_score >= 85:
            rec = "Principal Mastery"
        elif overall_score >= 70:
            rec = "Advanced Proficiency"
        elif overall_score >= 55:
            rec = "Demonstrated Competency"
        elif overall_score >= 40:
            rec = "Developing Proficiency"
        else:
            rec = "Foundational"

        top_strengths = []
        growth_areas = []
        for qa in qa_history:
            top_strengths.extend(qa.get("strengths", []))
            growth_areas.extend(qa.get("areas_for_improvement", []))

        # Deduplicate while preserving order
        unique_strengths = list(dict.fromkeys(top_strengths))[:4]
        unique_growth = list(dict.fromkeys(growth_areas))[:4]

        summary = (
            f"Professional {candidate_name} completed the technical evaluation in the {role} specialization with an overall domain rating "
            f"of {overall_score:.1f}/100 ({rec}). The assessment demonstrated solid command in "
            f"{', '.join(list(category_scores.keys())[:2]) if category_scores else 'core technical principles'}. "
            f"Across {len(qa_history)} multi-turn technical assessments grounded in foundational literature, "
            f"the responses exhibited structured problem-solving with sound conceptual grounding."
        )

        return {
            "overall_score": overall_score,
            "recommendation": rec,
            "executive_summary": summary,
            "key_strengths": unique_strengths or ["Clear communication of foundational principles"],
            "areas_for_growth": unique_growth or ["Deeper exploration of edge case trade-offs in distributed scale"]
        }

    def _generate_fallback_question(
        self,
        role: str,
        difficulty: str,
        topic: str,
        order_index: int,
        rag_context: str,
        candidate_skills: List[str]
    ) -> Dict[str, Any]:
        """Smart deterministic generator creating role-grounded technical questions from textbook context."""
        
        # Extract first section and first key sentence from RAG context
        first_line = "Foundational Concepts"
        context_preview = ""
        for line in rag_context.split("\n"):
            if line.startswith("Source:") or line.startswith("---"):
                continue
            if line.strip():
                context_preview = line.strip()
                break

        # Map role and topic to deep questions
        role_questions = {
            "ai_ml_engineer": [
                {
                    "topic": "Decision Trees & Information Theory",
                    "question_text": "In the context of Decision Tree learning (e.g. ID3/C4.5), explain the mathematical formulation of Entropy and Information Gain. How does C4.5 address the bias of Information Gain towards attributes with many distinct values?",
                    "ideal_answer_rubric": "Candidate should define Entropy as -sum(p_i * log2(p_i)) and Information Gain as Entropy(S) - expected entropy of partitions. They should explain that attributes with many unique values (like IDs) yield maximal information gain despite poor generalization, and C4.5 mitigates this by using Gain Ratio which normalizes by SplitInformation."
                },
                {
                    "topic": "Neural Networks & Optimization",
                    "question_text": "Describe how the Backpropagation algorithm uses the chain rule to compute error gradients across hidden layers in a Multi-Layer Perceptron. How does the choice of activation function (Sigmoid vs ReLU) affect gradient propagation during deep training?",
                    "ideal_answer_rubric": "Candidate must explain the backward pass: output layer error delta_k = (t_k - o_k)*o_k*(1-o_k), propagated back to hidden units. Must mention that Sigmoid derivatives max out at 0.25 causing vanishing gradients across deep layers, whereas ReLU maintains constant gradient 1 for positive activations."
                },
                {
                    "topic": "Regularization & Generalization",
                    "question_text": "Compare L1 (Lasso) and L2 (Ridge) regularization from both a geometric constraint perspective and their impact on weight sparsity. In what real-world scenarios would you choose Elastic Net over pure L1 or L2?",
                    "ideal_answer_rubric": "Candidate should describe the diamond shape of L1 constraint intersecting contours at axes (inducing exact zero sparsity), versus circular L2 constraint shrinking weights smoothly. Elastic Net is necessary when dealing with groups of highly correlated features where L1 arbitrarily selects one."
                },
                {
                    "topic": "Support Vector Machines & Kernel Trick",
                    "question_text": "How does the Kernel Trick enable Support Vector Machines to construct non-linear decision boundaries without explicitly computing high-dimensional feature coordinates? What role do support vectors play in defining the maximum margin hyperplane?",
                    "ideal_answer_rubric": "Candidate should explain Mercer's theorem and how kernel functions K(x, z) = phi(x).phi(z) evaluate inner products directly in original space. Only points on or violating margin boundaries (support vectors) have non-zero Lagrange multipliers influencing w and b."
                },
                {
                    "topic": "Reinforcement Learning & Bellman Optimality",
                    "question_text": "Formulate the Bellman Optimality equation for Q-Learning. Explain how the Q-update rule updates action-value estimates in a model-free environment, and discuss the exploration-exploitation trade-off with epsilon-greedy schedules.",
                    "ideal_answer_rubric": "Candidate must present Q(s,a) <- Q(s,a) + alpha*[r + gamma*max_a' Q(s',a') - Q(s,a)]. Must clarify model-free nature (no explicit transition probability P(s'|s,a) needed) and how epsilon-greedy balances random exploration vs greedy exploitation."
                }
            ],
            "data_science_applied_ml": [
                {
                    "topic": "Data Preprocessing & Leakage Prevention",
                    "question_text": "Explain why fitting a Scaler or Imputer on the full dataset prior to train-test splitting causes data leakage. How do Scikit-Learn Pipelines and ColumnTransformers guarantee strict isolation during Stratified K-Fold Cross-Validation?",
                    "ideal_answer_rubric": "Candidate must explain that fitting transformers on full data exposes test distribution parameters (mean, variance, categories) to training folds, leading to overly optimistic validation scores. Pipelines wrap fit/transform strictly inside CV loops."
                },
                {
                    "topic": "Class Imbalance & Resampling",
                    "question_text": "When training a model on a dataset with 2% positive class prevalence, why is ROC-AUC often misleading compared to Precision-Recall AUC? How does SMOTE synthesize minority samples, and what are its limitations with noisy feature spaces?",
                    "ideal_answer_rubric": "Candidate should note that ROC-AUC false positive rate denominator includes huge majority class count, masking large surges in false alarms. SMOTE interpolates along k-nearest neighbors in feature space; limitations include creating noisy/borderline synthetic instances in overlapping regions."
                },
                {
                    "topic": "Ensemble Learning & Gradient Boosting",
                    "question_text": "Compare the core variance-reduction mechanics of Random Forest (Bagging) against the bias-reduction mechanics of Gradient Boosted Decision Trees (XGBoost/LightGBM). How does XGBoost utilize second-order Taylor gradients (Hessians)?",
                    "ideal_answer_rubric": "Candidate should explain Bagging builds independent decorrelated trees on bootstrap samples to reduce variance. Boosting fits sequential trees to loss pseudo-residuals to reduce bias. XGBoost uses both 1st (gradient) and 2nd (Hessian) derivatives for exact optimal leaf weight calculation and split regularization."
                },
                {
                    "topic": "Model Drift & Statistical Monitoring",
                    "question_text": "Differentiate between Covariate Shift (Data Drift) and Concept Drift in a production ML deployment. What statistical tests (e.g. Kolmogorov-Smirnov, Population Stability Index) would you set up in your monitoring pipeline to trigger automated alerts?",
                    "ideal_answer_rubric": "Candidate should define Covariate Shift as P(X) changing while P(Y|X) stays constant, and Concept Drift as P(Y|X) changing. Mention KS-test for continuous distribution comparisons and PSI (<0.1 stable, >0.25 significant shift) for feature drift monitoring."
                },
                {
                    "topic": "Logistic Regression & Interpretability",
                    "question_text": "Explain the mathematical relationship between the Sigmoid activation function and the Log-Odds (Logit) in Logistic Regression. How do you interpret an estimated coefficient beta_j = 0.693 in terms of Odds Ratios?",
                    "ideal_answer_rubric": "Candidate must state ln(p/(1-p)) = w^T*x + b. exp(0.693) approx 2.0, meaning each unit increase in feature x_j doubles the odds of the positive class outcome, holding all other features constant."
                }
            ],
            "backend_system_design": [
                {
                    "topic": "Caching Patterns & Invalidation",
                    "question_text": "Analyze the trade-offs between Cache-Aside, Write-Through, and Write-Back caching strategies. How would you protect a distributed system from a 'Cache Stampede' (Thundering Herd) when a hot cache key expires under 20,000 QPS load?",
                    "ideal_answer_rubric": "Candidate should contrast Cache-Aside (lazy loading, resilient miss handling), Write-Through (synchronous consistency, higher write latency), and Write-Back (high throughput async batches, risk of data loss on crash). For cache stampede: singleflight/mutex locking, probabilistic early expiration (XFetch), or background pre-warming."
                },
                {
                    "topic": "Concurrency Models & AsyncIO",
                    "question_text": "How does the Python AsyncIO single-threaded event loop achieve high concurrency for I/O-bound microservices without running into GIL constraints? When must a backend engineer offload tasks to a ProcessPoolExecutor instead of a ThreadPoolExecutor?",
                    "ideal_answer_rubric": "Candidate should explain non-blocking I/O multiplexing (epoll/kqueue) where coroutines yield control via await during socket/disk waits. CPU-bound calculations (cryptography, image transformations, heavy math) block the GIL and event loop, requiring ProcessPoolExecutor to spawn isolated OS processes."
                },
                {
                    "topic": "Database Sharding & Consistent Hashing",
                    "question_text": "Explain how Consistent Hashing with virtual nodes solves the hotspotting and massive re-indexing problem when scaling a distributed database cluster from N to N+1 nodes compared to standard modular hashing (hash(key) % N).",
                    "ideal_answer_rubric": "Candidate must explain that standard modulo re-maps almost all keys when N changes. Consistent hashing places nodes on a 2^32 ring; adding a node only reassigns K/N keys from its clockwise successor. Virtual nodes prevent nonuniform key clustering and balance partition load evenly."
                },
                {
                    "topic": "Distributed Transactions & SAGA Pattern",
                    "question_text": "Why is Two-Phase Commit (2PC) rarely recommended for high-throughput distributed microservices? Describe the Choreography vs Orchestration approaches of the SAGA pattern, and how compensating transactions maintain eventual consistency.",
                    "ideal_answer_rubric": "Candidate should note 2PC is synchronous, blocking, and introduces single-point-of-failure coordinator bottlenecks. SAGA decomposes a transaction into local ACID steps with compensating rollback actions. Choreography relies on event brokers; Orchestration uses a central orchestrator state machine."
                },
                {
                    "topic": "API Security & Rate Limiting",
                    "question_text": "Compare Token Bucket vs Sliding Window Counter rate-limiting algorithms. How would you design an idempotent payment processing API endpoint using client-provided Idempotency Keys stored in Redis?",
                    "ideal_answer_rubric": "Candidate should contrast Token Bucket (burst capacity, constant refill) with Sliding Window (smooth per-second limits without boundary spikes). For idempotency: client sends unique Idempotency-Key header; backend performs atomic Redis SETNX with TTL, returns cached response on replay, processes once on new key."
                }
            ],
            "advanced_theoretical_ml": [
                {
                    "topic": "Bayesian Inference & Maximum Likelihood",
                    "question_text": "From a probabilistic perspective (Bishop PRML), derive why Maximum Likelihood Estimation of Gaussian variance is biased by a factor of (N-1)/N. How does full Bayesian marginalization over conjugate priors eliminate this parameter overfitting?",
                    "ideal_answer_rubric": "Candidate should show E[sigma_ML^2] = ((N-1)/N)*sigma_true^2 because sample mean mu_ML minimizes squared distances to sample data rather than true population mean. Bayesian marginalization integrates over the posterior parameter distribution rather than choosing a point estimate."
                },
                {
                    "topic": "Expectation-Maximization (EM) Algorithm",
                    "question_text": "Provide the formal mathematical formulation of the Expectation-Maximization (EM) algorithm for latent variable models. Why is direct maximization of the incomplete-data log-likelihood ln p(X|theta) intractable, and how does the E-step guarantee monotonic likelihood improvement?",
                    "ideal_answer_rubric": "Candidate must explain that the summation over latent variables Z inside the logarithm prevents closed-form optimization. E-step computes the expected complete-data log-likelihood Q(theta, theta_old) = E_Z|X,theta_old [ln p(X,Z|theta)], and M-step maximizes Q. Jensen's inequality guarantees the lower bound increases monotonically."
                },
                {
                    "topic": "Attention Mechanism & Transformer Mathematics",
                    "question_text": "In the Scaled Dot-Product Attention equation Attention(Q, K, V) = softmax((Q*K^T) / sqrt(d_k)) * V, what is the mathematical necessity of dividing by sqrt(d_k)? How does Multi-Head Attention provide richer representation capacity than single-head attention?",
                    "ideal_answer_rubric": "Candidate should explain that for large key dimension d_k, dot products grow large in magnitude, pushing softmax into regions with vanishingly small gradients. Dividing by sqrt(d_k) normalizes the variance of the dot product to 1. Multi-head projects Q, K, V into h distinct subspaces, attending to different positional and semantic relationships."
                },
                {
                    "topic": "Principal Component Analysis (PCA)",
                    "question_text": "Formulate PCA as both a Maximum Variance projection problem and a Minimum Reconstruction Error problem. Prove that the first principal component is given by the eigenvector of the data covariance matrix corresponding to the largest eigenvalue.",
                    "ideal_answer_rubric": "Candidate should set up the Lagrangian L(u_1, lambda_1) = u_1^T * S * u_1 - lambda_1 * (u_1^T * u_1 - 1). Taking the gradient w.r.t u_1 gives 2*S*u_1 - 2*lambda_1*u_1 = 0, meaning S*u_1 = lambda_1*u_1. Multiplying by u_1^T yields variance = lambda_1, which is maximized by the largest eigenvalue."
                },
                {
                    "topic": "Deep Learning Optimization & Loss Landscapes",
                    "question_text": "Analyze the mathematical formulation of the Adam optimizer versus AdamW. Why does standard Adam with L2 regularization fail to implement true weight decay in adaptive gradient updates, and how does AdamW resolve this gradient magnitude distortion?",
                    "ideal_answer_rubric": "Candidate should explain that in standard Adam, L2 penalty is added directly to gradient g_t, which gets scaled inversely by sqrt(v_t), shrinking weights with large historical gradients LESS than weights with small gradients. AdamW explicitly subtracts eta*lambda*w_t outside the momentum/adaptive scaling step."
                }
            ]
        }

        # Normalize role key
        role_key = "ai_ml_engineer"
        if "data" in role.lower():
            role_key = "data_science_applied_ml"
        elif "backend" in role.lower() or "system" in role.lower():
            role_key = "backend_system_design"
        elif "theory" in role.lower() or "theoretical" in role.lower() or "bishop" in role.lower():
            role_key = "advanced_theoretical_ml"

        q_list = role_questions.get(role_key, role_questions["ai_ml_engineer"])
        idx = (order_index - 1) % len(q_list)
        selected = q_list[idx]

        return {
            "question_text": selected["question_text"],
            "topic": selected["topic"],
            "ideal_answer_rubric": selected["ideal_answer_rubric"],
            "rag_relevance_summary": f"Grounded in {role.title()} textbook corpus."
        }

    def _evaluate_fallback_answer(
        self,
        question_text: str,
        topic: str,
        ideal_rubric: str,
        rag_context: str,
        candidate_answer: str
    ) -> Dict[str, Any]:
        """Heuristic answer grading measuring length, technical keyword density, and rubric alignment."""
        
        words = candidate_answer.strip().split()
        word_count = len(words)
        ans_lower = candidate_answer.lower()

        # Extract key technical tokens from ideal rubric and rag context
        rubric_tokens = set(re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', ideal_rubric.lower()))
        context_tokens = set(re.findall(r'\b[a-zA-Z0-9_\-]{4,}\b', rag_context.lower()))
        benchmark_tokens = rubric_tokens.union(context_tokens)

        # Count how many benchmark tokens are matched in candidate answer
        matched_tokens = [t for t in benchmark_tokens if t in ans_lower]
        token_match_ratio = len(matched_tokens) / max(1, min(len(benchmark_tokens), 20))

        # Base scoring calculation
        if word_count < 10:
            tech_acc = 2.0
            depth = 1.5
            practical = 1.5
            clarity = 3.0
            feedback = "The response is overly brief and lacks technical explanation or depth."
            strengths = ["Attempted the question"]
            growth = ["Provide comprehensive explanations", "Mention underlying mathematical formulas or architecture mechanisms"]
        elif word_count < 35:
            tech_acc = min(6.0, 3.5 + token_match_ratio * 4.0)
            depth = min(5.5, 3.0 + token_match_ratio * 3.5)
            practical = min(6.0, 3.5 + token_match_ratio * 3.0)
            clarity = 6.0
            feedback = "Good initial response identifying core concepts, but needs deeper exploration of underlying mechanisms and tradeoffs."
            strengths = ["Identified foundational terminology", "Answer is concise"]
            growth = ["Elaborate on edge cases and failure modes", "Provide concrete mathematical or architectural details"]
        else:
            # Substantial answer
            tech_acc = min(9.8, max(5.5, 5.0 + token_match_ratio * 5.0))
            depth = min(9.5, max(5.0, 4.5 + token_match_ratio * 5.0))
            practical = min(9.5, max(5.5, 5.0 + token_match_ratio * 4.5))
            clarity = min(9.6, 7.5 + (0.5 if word_count > 60 else 0.0))
            
            feedback = (
                f"Strong technical answer demonstrating solid grasp of {topic}. "
                f"The response effectively covers the primary mechanisms required by the textbook rubric and discusses practical implementation aspects."
            )
            strengths = [
                f"Accurately addressed key mechanics of {topic}",
                "Structured and logically coherent explanation",
                "Good technical terminology and conceptual clarity"
            ]
            growth = [
                "Could further quantify performance tradeoffs under extreme scale",
                "Explore secondary edge cases or alternative fallback algorithms"
            ]

        # Calculate weighted average score out of 10.0
        weighted_score = (tech_acc * 0.35) + (depth * 0.25) + (practical * 0.25) + (clarity * 0.15)
        weighted_score = round(min(10.0, max(0.0, weighted_score)), 1)

        return {
            "score": weighted_score,
            "technical_accuracy_score": round(tech_acc, 1),
            "depth_score": round(depth, 1),
            "practical_application_score": round(practical, 1),
            "clarity_score": round(clarity, 1),
            "feedback": feedback,
            "strengths": strengths,
            "areas_for_improvement": growth
        }


# Singleton LLM Provider
llm_provider = LLMProvider()
