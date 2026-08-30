"""Resume parsing service for PDF and text input with structured entity extraction."""

import re
import io
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from app.schemas.resume import ExtractedResumeData
from app.core.logging import logger

# Comprehensive taxonomy of technical skills and frameworks
SKILL_TAXONOMY = {
    "ai_ml": [
        "machine learning", "deep learning", "neural networks", "pytorch", "tensorflow",
        "keras", "scikit-learn", "transformers", "hugging face", "rag", "retrieval-augmented generation",
        "embeddings", "vector database", "chromadb", "faiss", "q-learning", "reinforcement learning",
        "markov decision process", "backpropagation", "gradient descent", "decision trees",
        "random forest", "xgboost", "lightgbm", "svm", "support vector machines", "naive bayes",
        "computer vision", "nlp", "natural language processing", "llm", "large language models",
        "attention mechanism", "layer normalization", "regularization", "dropout", "cross-validation",
        "bias-variance", "roc-auc", "precision-recall", "feature engineering"
    ],
    "data_science": [
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "data analysis", "data preprocessing",
        "smote", "class imbalance", "logistic regression", "linear regression", "hypothesis testing",
        "a/b testing", "feature selection", "one-hot encoding", "target encoding", "time series",
        "mlflow", "weights & biases", "model drift", "psi", "ks-test", "jupyter"
    ],
    "backend": [
        "python", "fastapi", "flask", "django", "asyncio", "sqlalchemy", "node.js", "express",
        "go", "golang", "java", "spring boot", "rest", "restful api", "graphql", "grpc",
        "postgresql", "mysql", "sqlite", "redis", "mongodb", "cassandra", "dynamodb",
        "microservices", "docker", "kubernetes", "kafka", "rabbitmq", "celery", "distributed systems",
        "caching", "cache-aside", "rate limiting", "token bucket", "jwt", "oauth2", "concurrency",
        "connection pooling", "sharding", "load balancing", "consistent hashing", "cap theorem", "saga pattern"
    ]
}


class ResumeParserService:
    """Service to parse, sanitize, and extract structured metadata from candidate resumes."""

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extracts plain text content from PDF binary data."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_chunks = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
            full_text = "\n".join(text_chunks).strip()
            if not full_text:
                raise ValueError("Extracted PDF content is empty or scanned.")
            return full_text
        except Exception as e:
            logger.error(f"Error parsing PDF file: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    @classmethod
    def parse_resume_text(cls, text: str, file_name: Optional[str] = None) -> ExtractedResumeData:
        """Parses raw text and extracts structured skills, contact info, domains, and experience."""
        cleaned_text = re.sub(r'\s+', ' ', text)
        lower_text = text.lower()

        # 1. Candidate Name heuristic
        candidate_name = cls._extract_candidate_name(text)

        # 2. Contact details (email & phone)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None

        # 3. Match Skills and Technologies
        matched_skills = set()
        matched_tech = set()
        matched_domains = set()

        CANONICAL_NAMES = {
            "pytorch": "PyTorch",
            "scikit-learn": "Scikit-Learn",
            "fastapi": "FastAPI",
            "postgresql": "PostgreSQL",
            "xgboost": "XGBoost",
            "lightgbm": "LightGBM",
            "chromadb": "ChromaDB",
            "sqlalchemy": "SQLAlchemy",
            "asyncio": "AsyncIO",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "rag": "RAG",
            "llm": "LLM",
            "nlp": "NLP",
            "svm": "SVM",
            "sql": "SQL",
            "jwt": "JWT",
            "api": "API",
            "cap": "CAP",
            "q-learning": "Q-Learning",
            "markov decision process": "Markov Decision Process"
        }

        for category, keywords in SKILL_TAXONOMY.items():
            for kw in keywords:
                # Use word boundary search
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, lower_text):
                    formatted_kw = CANONICAL_NAMES.get(kw, kw.title() if len(kw) > 3 else kw.upper())
                    matched_skills.add(formatted_kw)
                    if category == "ai_ml":
                        matched_domains.add("Machine Learning & AI")
                    elif category == "data_science":
                        matched_domains.add("Data Science & Applied Analytics")
                    elif category == "backend":
                        matched_domains.add("Backend & Distributed Systems")

        # Extract frameworks / technologies
        tech_keywords = ["PyTorch", "TensorFlow", "FastAPI", "Docker", "PostgreSQL", "Redis", 
                         "Kafka", "Scikit-Learn", "ChromaDB", "Kubernetes", "AsyncIO", "SQLAlchemy"]
        for tech in tech_keywords:
            if tech.lower() in lower_text:
                matched_tech.add(tech)

        # 4. Estimate Experience Years
        exp_years = cls._estimate_experience_years(text)

        # 5. Extract Projects & Summary
        summary = cls._generate_candidate_summary(matched_skills, exp_years, matched_domains)
        projects = cls._extract_projects(text)

        return ExtractedResumeData(
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            skills=sorted(list(matched_skills)),
            technologies=sorted(list(matched_tech)),
            domain_exposure=sorted(list(matched_domains)),
            experience_years=exp_years,
            summary=summary,
            projects=projects
        )

    @staticmethod
    def _extract_candidate_name(text: str) -> str:
        """Extracts candidate name from the top lines of the resume."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:5]:
            # Avoid headers like 'RESUME', 'CURRICULUM VITAE', 'EMAIL'
            if re.match(r'^(resume|cv|curriculum vitae|summary|profile)', line, re.IGNORECASE):
                continue
            if '@' in line or 'http' in line or len(line.split()) > 5:
                continue
            cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            if 2 <= len(cleaned.split()) <= 4:
                return cleaned.title()
        return "Candidate"

    @staticmethod
    def _estimate_experience_years(text: str) -> float:
        """Estimates experience years by detecting numbers near 'years of experience' or year ranges."""
        exp_match = re.search(r'(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience', text, re.IGNORECASE)
        if exp_match:
            try:
                return float(exp_match.group(1))
            except ValueError:
                pass

        # Detect year ranges like 2021 - 2024 or 2021 - Present
        years = [int(y) for y in re.findall(r'\b(20[0-2][0-9])\b', text)]
        if len(years) >= 2:
            span = max(years) - min(years)
            if 1 <= span <= 20:
                return float(span)
        return 2.0  # Default reasonable estimate

    @staticmethod
    def _generate_candidate_summary(skills: set, exp_years: float, domains: set) -> str:
        """Synthesizes a short profile summary."""
        skill_sample = ", ".join(list(skills)[:6]) if skills else "software development"
        domain_sample = ", ".join(domains) if domains else "Engineering"
        return f"Candidate with ~{exp_years:.1f} years experience in {domain_sample}. Key competencies include: {skill_sample}."

    @staticmethod
    def _extract_projects(text: str) -> List[str]:
        """Extracts notable project titles from resume text."""
        projects = []
        project_section = re.search(r'(?:PROJECTS|NOTABLE PROJECTS|PERSONAL PROJECTS)(.*?)(?:EDUCATION|EXPERIENCE|SKILLS|\Z)', text, re.IGNORECASE | re.DOTALL)
        if project_section:
            proj_text = project_section.group(1)
            bullet_points = re.findall(r'(?:[-•*]|\b[0-9]\.)\s*(.*?)(?=\n(?:[-•*]|\b[0-9]\.)|\n\n|\Z)', proj_text, re.DOTALL)
            for bp in bullet_points[:4]:
                cleaned = re.sub(r'\s+', ' ', bp).strip()
                if 10 < len(cleaned) < 200:
                    projects.append(cleaned)
        return projects
