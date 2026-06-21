"""
Multi-Document QA & Risk Detection System — FastAPI Application Entry Point

Initializes CORS, database, vector store, risk detector, QA pipeline,
and mounts static file routes for PDF serving.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import router as api_router
from app.services.database import DatabaseManager
from app.services.vector_store import VectorStore
from app.services.risk_detector import RiskDetector
from app.services.qa_service import QAService

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan Context Manager (replaces deprecated on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle manager."""
    logger.info("Initializing backend services...")

    # 1. SQLite Database
    db = DatabaseManager()
    app.state.db = db

    # 2. FAISS Vector Store (loads SentenceTransformer all-MiniLM-L6-v2)
    vector_store = VectorStore()
    app.state.vector_store = vector_store

    # 3. Risk Detector (YAML rules + scikit-learn model)
    risk_detector = RiskDetector()
    app.state.risk_detector = risk_detector

    # 4. QA Service (DistilBERT extractive QA pipeline)
    qa_service = QAService(vector_store=vector_store)
    app.state.qa_service = qa_service

    logger.info("All services initialized successfully. FastAPI is ready!")


    yield  # Application runs here

    # Shutdown logic (if needed)
    logger.info("Shutting down backend services...")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="VERICO Compliance Scanner API",
    description=(
        "Production-grade compliance and contract scanner with hybrid semantic "
        "search, extractive QA, and automated risk classification."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and Docker container
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api prefix
app.include_router(api_router, prefix="/api")

# Mount uploads directory for static PDF serving
if os.environ.get("VERCEL"):
    upload_dir = "/tmp/uploads"
else:
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

try:
    os.makedirs(upload_dir, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create uploads directory: {e}")
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")



@app.get("/")
async def root():
    return {
        "message": (
            "Welcome to the Multi-Document QA & Risk Detection API. "
            "Navigate to /docs for interactive Swagger documentation."
        )
    }
