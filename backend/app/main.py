"""
Mazungumzo AI - Main FastAPI Application
Mental Health Chat Companion for Kenya

This is the core server that handles:
- WhatsApp webhook integration
- AI chat processing with Cerebras/Qwen3
- Crisis detection and safety protocols
- Multilingual support (English/Swahili)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import our modular components
from backend.utils.config import get_settings
from backend.utils.logging_config import setup_logging, get_logger
from backend.services import AIService, CrisisDetectionService, SessionService
from backend.models import MentalHealthResources
from backend.app.routes import chat_router, webhook_router, health_router

# Initialize configuration and logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Mazungumzo AI application...")
    
    # Initialize services
    app.state.ai_service = AIService()
    app.state.crisis_service = CrisisDetectionService()
    app.state.session_service = SessionService()
    app.state.resources = MentalHealthResources.get_kenya_resources()
    
    # Health check for AI services
    ai_healthy = await app.state.ai_service.health_check()
    if ai_healthy:
        logger.info("✅ AI services are healthy")
    else:
        logger.warning("⚠️ AI services may have issues")
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Mazungumzo AI application...")
    # Cleanup if needed
    logger.info("✅ Application shutdown complete")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Mazungumzo AI",
    description="Mental Health Chat Companion for Kenya",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )