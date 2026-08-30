"""FastAPI Application Main Entrypoint."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.services.rag_service import rag_service
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Verifying RAG Knowledge Base index...")
    rag_service.initialize_knowledge_base()
    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down screening engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Role-Based Candidate Screening System with Grounded RAG Pipelines",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static directory setup
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        """Serves the standalone interactive candidate screening dashboard."""
        return FileResponse(str(static_dir / "index.html"))


@app.get("/health", tags=["System"])
def health_check():
    """System health check and diagnostic status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "rag_roles_indexed": list(rag_service.chunks_by_role.keys()),
        "total_rag_chunks": sum(len(c) for c in rag_service.chunks_by_role.values())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
