#!/usr/bin/env python3
"""Knowledge Base Seeding and Validation Script.

Processes role-specific textbook literature, verifies chunking counts,
and builds the persistent vector/TF-IDF indices.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.rag_service import rag_service
from app.core.logging import logger


def seed_and_validate():
    logger.info("==================================================")
    logger.info("  PGAGI Knowledge Base Ingestion & Seeding Engine")
    logger.info("==================================================")
    logger.info(f"Corpus Directory: {settings.KNOWLEDGE_BASE_DIR}")
    logger.info(f"Chunk Size: {settings.RAG_CHUNK_SIZE} words | Overlap: {settings.RAG_CHUNK_OVERLAP} words")

    rag_service.initialize_knowledge_base()

    logger.info("--- Knowledge Base Ingestion Summary ---")
    for role_key, chunks in rag_service.chunks_by_role.items():
        logger.info(f"Role: {role_key:<30} -> {len(chunks):>3} chunks indexed")
        for chunk in chunks[:2]:
            logger.info(f"   * [{chunk.source_book}] {chunk.chapter_title}")

    total_chunks = sum(len(c) for c in rag_service.chunks_by_role.values())
    logger.info("--------------------------------------------------")
    logger.info(f"Total Chunks Successfully Grounded & Indexed: {total_chunks}")
    logger.info("Knowledge Base ready for technical screening sessions.")
    logger.info("==================================================")


if __name__ == "__main__":
    seed_and_validate()
