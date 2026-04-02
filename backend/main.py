"""
MedBridge — FastAPI Application Entry Point

Run with: uvicorn backend.main:app --reload --port 8000
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables before anything else
load_dotenv()

# Ensure project root is on sys.path (needed for Render deployment)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.models.database import init_db
from backend.routers import auth, patient, doctor, chat, alerts, risk_engine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("medbridge")


# ---------------------------------------------------------------------------
# Lifespan — runs on startup/shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 MedBridge starting up — initializing database…")
    try:
        init_db()
        logger.info("✅ Database tables ready")
    except Exception:
        logger.exception("❌ Database initialization failed during startup")
        raise
    yield
    logger.info("🛑 MedBridge shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MedBridge API",
    description="AI-powered two-sided health record platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontends
origins = [
    "http://localhost:8501",  # Local Patient app
    "http://localhost:8502",  # Local Doctor app
]
# Add dynamic production frontend URLs via environment variable
frontend_urls = os.getenv("FRONTEND_URLS", "")
if frontend_urls:
    origins.extend([url.strip() for url in frontend_urls.split(",") if url.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENV") == "development" else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(chat.router)
app.include_router(alerts.router)
app.include_router(risk_engine.router)


# ---------------------------------------------------------------------------
# Root / health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"], response_class=HTMLResponse)
def root():
    html_path = Path(__file__).parent / "static" / "index.html"
    patient_portal_url = os.getenv("PATIENT_PORTAL_URL", "http://localhost:8501")
    doctor_portal_url = os.getenv("DOCTOR_PORTAL_URL", "http://localhost:8502")
    html = html_path.read_text(encoding="utf-8")
    html = html.replace("__PATIENT_PORTAL_URL__", patient_portal_url)
    html = html.replace("__DOCTOR_PORTAL_URL__", doctor_portal_url)
    return HTMLResponse(content=html, status_code=200)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}
