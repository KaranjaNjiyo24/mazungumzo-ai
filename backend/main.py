# backend/main.py
"""
Main FastAPI application for Mazungumzo AI
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging
import time
import asyncio

from utils.config import settings, get_system_prompt, validate_environment
from services.json_database import db, get_user_session, add_message, log_crisis, get_stats
from services.advanced_features import (
    enhance_ai_response,
    advanced_service,
    voice_service,
    community_service
)
from webhooks import router as webhook_router
from services.ai_service import AIService
from models.session_models import MessageRole, ConversationMessage

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include webhook routes
app.include_router(webhook_router, prefix="/api/v1")

# Request Models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    language: Optional[str] = "en"

class VoiceRequest(BaseModel):
    audio_url: str
    user_id: str
    language: Optional[str] = "sw"

# Response Models
class ChatResponse(BaseModel):
    response: str
    mood_analysis: Optional[Dict] = None
    insights: Optional[Dict] = None
    community_suggestion: Optional[Dict] = None
    success_stories: Optional[List[Dict]] = None

class StatsResponse(BaseModel):
    stats: Dict
    resources: List[str]

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with advanced features"""
    try:
        # Get or create user session
        session = await get_user_session(request.user_id)
        if not session:
            session = await db.create_user_session(request.user_id)
        
        # Add user message to history
        await add_message(
            request.user_id,
            MessageRole.USER,
            request.message,
            request.language
        )
        
        # Get conversation history and format it for the AI service
        raw_history = session.get("conversation_history", [])
        conversation_history = []
        
        for msg in raw_history:
            conversation_history.append(ConversationMessage(
                role=MessageRole(msg["role"]),
                content=msg["content"],
                timestamp=msg.get("timestamp"),
                metadata={"language": msg.get("language", request.language)}
            ))
        
        # Generate AI response using the AI service
        ai_service = AIService()
        ai_response = await ai_service.generate_response(
            message=request.message,
            conversation_history=conversation_history,
            language=request.language,
            user_id=request.user_id
        )
        
        # Add AI response to history
        await add_message(
            request.user_id,
            MessageRole.ASSISTANT,
            ai_response,
            request.language
        )
        
        # Enhance response with advanced features
        enhanced = await enhance_ai_response(
            request.message,
            request.user_id,
            ai_response
        )
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/voice")
async def process_voice(request: VoiceRequest):
    """Process voice messages"""
    try:
        # Transcribe voice message
        transcription = await voice_service.process_voice_message(
            request.audio_url,
            request.user_id
        )
        
        # Process transcription through chat
        chat_response = await chat(ChatRequest(
            message=transcription,
            user_id=request.user_id,
            language=request.language
        ))
        
        # Convert response to voice
        voice_url = await voice_service.convert_response_to_voice(
            chat_response["response"],
            request.language
        )
        
        return {
            "transcription": transcription,
            "response": chat_response,
            "voice_url": voice_url
        }
        
    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_usage_stats():
    """Get usage statistics and resources"""
    try:
        stats = await get_stats()
        resources = await db.get_crisis_resources()
        
        return {
            "stats": stats,
            "resources": resources
        }
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/resources")
async def get_resources(category: Optional[str] = None):
    """Get mental health resources"""
    try:
        resources = await db.get_mental_health_resources(category)
        return resources
        
    except Exception as e:
        logger.error(f"Resources error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Validate environment
        issues = validate_environment()
        if issues:
            logger.warning("Environment validation issues:")
            for issue in issues:
                logger.warning(f"- {issue}")
        
        # Initialize database
        db._initialize_files()
        db._load_all_to_cache()
        
        logger.info("✅ Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Cleanup old sessions
        await db.cleanup_old_sessions(settings.session_cleanup_hours)
        logger.info("✅ Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Start server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    ) 