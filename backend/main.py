"""PhysioWave — FastAPI Application Entry Point.

HIPAA Compliance Note: All data stays on-device. No external API calls.
All AI inference runs via Ollama on localhost.
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import init_db
from backend.core.logger import logger
from backend.routers import health, advisor, patients, sessions, rag


import asyncio

is_shutting_down = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    global is_shutting_down
    from backend.rag.worker import worker_instance
    try:
        # Startup
        logger.info("PhysioWave starting up...")
        await init_db()
        logger.info("Database initialized")
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs("./backend/data/extracted_images", exist_ok=True)
        logger.info(f"Uploads directory verified at {settings.upload_dir}")
        
        # Start RAG Worker Queue
        worker_instance._task = asyncio.create_task(worker_instance.start())
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        is_shutting_down = True
        logger.info("PhysioWave received shutdown signal...")
    finally:
        # Shutdown
        is_shutting_down = True
        await worker_instance.stop()
        logger.info("PhysioWave shutting down completely.")


app = FastAPI(
    title="PhysioWave",
    description=(
        "Intelligent Clinical Assistant for Physiotherapists. "
        "100% offline, HIPAA-compliant, on-device AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ─────────────────────────────────────────────────

app.include_router(health.router, prefix="/api")
app.include_router(advisor.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(rag.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "app": "PhysioWave",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }
