"""Retrieval-Augmented Generation (RAG) Service.

Manages knowledge base ingestion, semantic chunking, vector indexing,
and grounded context retrieval for technical screening.
"""

import os
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger


class TextChunk:
    """Represents an ingested text chunk with rich metadata for citation traceability."""
    def __init__(
        self,
        chunk_id: str,
        content: str,
        role: str,
        source_book: str,
        chapter_title: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.role = role
        self.source_book = source_book
        self.chapter_title = chapter_title
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "role": self.role,
            "source_book": self.source_book,
            "chapter_title": self.chapter_title,
            "metadata": self.metadata
        }


class RAGService:
    """Manages role-specific corpus ingestion, indexing, and grounded semantic retrieval."""

    def __init__(self):
        self.kb_dir = Path(settings.KNOWLEDGE_BASE_DIR)
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP
        self.top_k = settings.RAG_TOP_K
        
        # In-memory inverted index & vector representations for fast, deterministic search
        self.chunks_by_role: Dict[str, List[TextChunk]] = {}
        self.role_vocab: Dict[str, Dict[str, float]] = {}
        self.doc_term_freqs: Dict[str, List[Dict[str, float]]] = {}
        
        # Load and index all corpora on initialization
        self.initialize_knowledge_base()

    def initialize_knowledge_base(self):
        """Discovers, loads, chunks, and indexes all role-based knowledge documents."""
        logger.info(f"Initializing RAG Knowledge Base from: {self.kb_dir}")
        if not self.kb_dir.exists():
            logger.warning(f"Knowledge base directory {self.kb_dir} not found. Creating it.")
            self.kb_dir.mkdir(parents=True, exist_ok=True)
            return

        role_folders = [d for d in self.kb_dir.iterdir() if d.is_dir()]
        total_chunks = 0

        for role_folder in role_folders:
            role_key = self._normalize_role_key(role_folder.name)
            self.chunks_by_role[role_key] = []
            
            for file_path in role_folder.glob("*.txt"):
                book_chunks = self._process_document(file_path, role_key)
                self.chunks_by_role[role_key].extend(book_chunks)
                total_chunks += len(book_chunks)

            # Build term frequency vector index for the role
            self._build_role_index(role_key)
            logger.info(f"Role '{role_key}' indexed with {len(self.chunks_by_role[role_key])} chunks.")

        logger.info(f"RAG Knowledge Base initialization complete: {total_chunks} total chunks indexed.")

    def _normalize_role_key(self, role_str: str) -> str:
        """Normalizes various role display names to canonical keys."""
        normalized = role_str.lower().strip()
        if "ai" in normalized or "machine learning" in normalized or "ml" in normalized:
            if "theoretical" in normalized or "advanced" in normalized or "bishop" in normalized:
                return "advanced_theoretical_ml"
            if "data science" in normalized or "applied" in normalized:
                return "data_science_applied_ml"
            return "ai_ml_engineer"
        elif "data" in normalized or "scientist" in normalized or "analytics" in normalized:
            return "data_science_applied_ml"
        elif "backend" in normalized or "system" in normalized or "distributed" in normalized:
            return "backend_system_design"
        elif "theory" in normalized or "theoretical" in normalized:
            return "advanced_theoretical_ml"
        return "ai_ml_engineer"

    def _process_document(self, file_path: Path, role_key: str) -> List[TextChunk]:
        """Splits document into semantic sections and overlapping chunks."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        source_book = file_path.stem.replace("_", " ").title()
        chunks: List[TextChunk] = []

        # Split into chapters/sections based on markdown headers
        sections = re.split(r'\n(?=##?\s+)', raw_text)
        chunk_counter = 1

        for section in sections:
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            header_line = lines[0].strip() if lines[0].startswith('#') else "General Principles"
            chapter_title = re.sub(r'^#+\s*', '', header_line)
            body_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else header_line

            # Sub-chunk the body if it exceeds chunk size
            sub_chunks = self._chunk_text(body_text, self.chunk_size, self.chunk_overlap)
            for idx, sc in enumerate(sub_chunks):
                chunk_id = f"{role_key}_{file_path.stem}_{chunk_counter}"
                chunk_counter += 1
                
                full_chunk_text = f"Source: {source_book} | Section: {chapter_title}\n{sc}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        content=full_chunk_text,
                        role=role_key,
                        source_book=source_book,
                        chapter_title=chapter_title,
                        metadata={
                            "file": file_path.name,
                            "section_index": idx,
                            "word_count": len(sc.split())
                        }
                    )
                )

        return chunks

    def _chunk_text(self, text: str, chunk_size_words: int, overlap_words: int) -> List[str]:
        """Splits a body of text into sliding word chunks with overlap."""
        words = text.split()
        if len(words) <= chunk_size_words:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size_words, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end >= len(words):
                break
            start += (chunk_size_words - overlap_words)
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes text into lowercase alphanumeric keywords."""
        return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text)]

    def _build_role_index(self, role_key: str):
        """Builds TF-IDF vector matrix and inverse document frequencies for role chunks."""
        chunks = self.chunks_by_role.get(role_key, [])
        num_docs = len(chunks)
        if num_docs == 0:
            return

        doc_freqs: Dict[str, int] = {}
        tf_list: List[Dict[str, float]] = []

        for chunk in chunks:
            tokens = self._tokenize(chunk.content)
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0
            
            # Normalize TF
            total_tokens = len(tokens) or 1
            for t in tf:
                tf[t] /= total_tokens
                doc_freqs[t] = doc_freqs.get(t, 0) + 1
            tf_list.append(tf)

        # Compute IDF
        idf: Dict[str, float] = {}
        for term, df in doc_freqs.items():
            idf[term] = math.log(1.0 + (num_docs / (1.0 + df)))

        self.role_vocab[role_key] = idf
        self.doc_term_freqs[role_key] = tf_list

    def retrieve_context(
        self,
        query: str,
        role: str,
        top_k: Optional[int] = None,
        candidate_skills: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves top grounded knowledge chunks based on query and candidate background."""
        role_key = self._normalize_role_key(role)
        chunks = self.chunks_by_role.get(role_key, [])
        
        # Fallback to general AI/ML if role collection is empty
        if not chunks:
            role_key = "ai_ml_engineer"
            chunks = self.chunks_by_role.get(role_key, [])
            if not chunks:
                return []

        k = top_k or self.top_k
        idf = self.role_vocab.get(role_key, {})
        tf_list = self.doc_term_freqs.get(role_key, [])

        # Enrich query with candidate skill highlights
        expanded_query = query
        if candidate_skills:
            expanded_query += " " + " ".join(candidate_skills[:5])

        query_tokens = self._tokenize(expanded_query)
        if not query_tokens:
            return [c.to_dict() for c in chunks[:k]]

        scores: List[Tuple[float, int]] = []
        for doc_idx, tf in enumerate(tf_list):
            score = 0.0
            for token in query_tokens:
                if token in tf:
                    # TF-IDF dot product
                    token_weight = tf[token] * idf.get(token, 1.0)
                    score += token_weight
            
            # Add slight boost if chapter title matches query token
            chunk_obj = chunks[doc_idx]
            for token in query_tokens:
                if token in chunk_obj.chapter_title.lower():
                    score += 0.5

            scores.append((score, doc_idx))

        # Sort by relevance score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc_idx in scores[:k]:
            chunk_data = chunks[doc_idx].to_dict()
            chunk_data["relevance_score"] = round(float(score), 4)
            results.append(chunk_data)

        return results

    def format_rag_context_for_prompt(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks into a clean prompt context block with citations."""
        if not retrieved_chunks:
            return "No specific textbook context found. Rely on standard technical principles."

        context_lines = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            source = chunk.get("source_book", "Textbook")
            section = chunk.get("chapter_title", "Foundations")
            content = chunk.get("content", "")
            context_lines.append(f"--- [Textbook Grounding {idx}: {source} -> {section}] ---\n{content}\n")

        return "\n".join(context_lines)


# Singleton RAG service instance
rag_service = RAGService()
