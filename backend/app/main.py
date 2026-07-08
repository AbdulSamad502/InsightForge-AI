import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ai.observability import setup_langsmith
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.core.middleware import RequestIDMiddleware, TimingMiddleware

# ── Logging setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App instance ───────────────────────────────────────────
app = FastAPI(
    title="AI Data Analyst Agent",
    description="AI-powered Business Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters — first added = outermost) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://*.streamlit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

# ── Exception handlers ─────────────────────────────────────
register_exception_handlers(app)

# ── Routers ────────────────────────────────────────────────
app.include_router(api_router)

# ── Health check ───────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": settings.environment}


logger.info(f"AI Data Analyst API started in {settings.environment} mode.")


@app.on_event("startup")
async def startup_event():
    setup_langsmith()
    logger.info("AI Data Analyst API is ready.")