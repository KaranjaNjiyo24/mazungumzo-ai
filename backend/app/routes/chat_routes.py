# backend/app/routes/chat_routes.py
"""
Chat API routes for Mazungumzo AI
Handles web-based chat interactions
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import asyncio
from datetime import datetime

from ...models.chat_models import ChatMessage, ChatResponse
from ...models.session_models import MessageRole
from ...services.ai_service import ai_service
from ...services.crisis_service import crisis_service
from ...services.session_service import session_service
from ...utils.logging_config import get_logger, log_user_interaction, log_async_performance
from ...utils.config import settings

# Create router
chat_router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger("chat_routes")


@chat_router.post("/", response_model=ChatResponse)
@log_async_performance("chat_endpoint")
async def chat_endpoint(chat_request: ChatMessage):
    """
    Main chat endpoint for web interface
    Processes messages and returns AI responses with crisis detection
    """
    try:
        user_id = chat_request.user_id
        message = chat_request.message
        language = chat_request.language or "en"
        platform = chat_request.platform or "web"
        
        logger.info(f"💬 Chat request from {user_id[:8]}... on {platform}: {message[:50]}...")
        
        # Get or create user session
        session = session_service.get_or_create_session(user_id, platform)
        
        # Update language preference if provided
        if language != session.language_preference:
            session_service.update_language_preference(user_id, language)
        
        # Add user message to session
        session_service.add_message_to_session(
            user_id, MessageRole.USER, message, platform,
            {"timestamp": datetime.now().isoformat(), "language": language}
        )
        
        # Crisis detection
        is_crisis, confidence, detected_keywords = crisis_service.detect_crisis(message, session)
        
        # Get conversation context
        conversation_context = session_service.get_conversation_context(user_id)
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            message=message,
            conversation_history=conversation_context,
            language=language,
            is_crisis=is_crisis,
            user_id=user_id
        )
        
        # Add AI response to session
        session_service.add_message_to_session(
            user_id, MessageRole.ASSISTANT, ai_response, platform,
            {
                "timestamp": datetime.now().isoformat(),
                "is_crisis": is_crisis,
                "confidence": confidence,
                "detected_keywords": detected_keywords
            }
        )
        
        # Get appropriate resources if crisis detected
        resources = []
        if is_crisis:
            resources = crisis_service.get_appropriate_resources(confidence, detected_keywords)
            
            # Add crisis response template if confidence is high
            if confidence >= 0.6:
                crisis_template = crisis_service.get_crisis_response_template(confidence, language)
                ai_response = crisis_template + "\n\n" + ai_response
        
        # Log successful interaction
        log_user_interaction(logger, user_id, "chat_completed", platform)
        
        return ChatResponse(
            response=ai_response,
            is_crisis=is_crisis,
            confidence=confidence,
            language=language,
            resources=resources,
            session_id=user_id
        )
        
    except Exception as e:
        logger.error(f"❌ Chat processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat processing failed")


@chat_router.get("/session/{user_id}")
async def get_session_info(user_id: str):
    """Get session information for a user"""
    try:
        session_summary = session_service.get_session_summary(user_id)
        risk_profile = session_service.get_user_risk_profile(user_id)
        
        return {
            "session": session_summary,
            "risk_profile": risk_profile,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session information")


@chat_router.post("/session/{user_id}/language")
async def update_language(user_id: str, language: str):
    """Update user's language preference"""
    try:
        if language not in ["en", "sw"]:
            raise HTTPException(status_code=400, detail="Unsupported language. Use 'en' or 'sw'")
        
        session = session_service.update_language_preference(user_id, language)
        return {
            "message": f"Language updated to {language}",
            "user_id": user_id,
            "language": session.language_preference
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating language: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update language preference")


@chat_router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Get chat history for a user (limited for privacy)"""
    try:
        conversation_context = session_service.get_conversation_context(user_id, limit)
        
        # Format for API response (exclude sensitive metadata)
        history = []
        for msg in conversation_context:
            history.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        return {
            "user_id": user_id,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@chat_router.delete("/session/{user_id}")
async def clear_session(user_id: str):
    """Clear/reset a user's session (for privacy/testing)"""
    try:
        # Note: In a real implementation, you might want authentication for this
        session_service.session_manager._sessions.pop(user_id, None)
        
        log_user_interaction(logger, user_id, "session_cleared", "api")
        
        return {
            "message": f"Session cleared for user {user_id}",
            "user_id": user_id,
            "status": "cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")


@chat_router.get("/crisis-resources")
async def get_crisis_resources():
    """Get mental health crisis resources for Kenya"""
    try:
        from ...models.resource_models import DEFAULT_KENYA_RESOURCES
        
        # Format resources for API response
        resources = {
            "crisis_hotlines": [
                {
                    "name": r.name,
                    "contact": r.contact,
                    "description": r.description,
                    "availability": r.availability,
                    "is_emergency": r.is_emergency
                }
                for r in DEFAULT_KENYA_RESOURCES.crisis_hotlines
            ],
            "hospitals": [
                {
                    "name": r.name,
                    "contact": r.contact,
                    "description": r.description,
                    "location": r.location,
                    "availability": r.availability
                }
                for r in DEFAULT_KENYA_RESOURCES.hospitals
            ],
            "professional_help": [
                {
                    "name": r.name,
                    "contact": r.contact,
                    "description": r.description
                }
                for r in DEFAULT_KENYA_RESOURCES.professional_help
            ],
            "online_resources": [
                {
                    "name": r.name,
                    "contact": r.contact,
                    "description": r.description
                }
                for r in DEFAULT_KENYA_RESOURCES.online_resources
            ]
        }
        
        return resources
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resources")


@chat_router.post("/feedback")
async def submit_feedback(user_id: str, rating: int, feedback: str = None):
    """Submit user feedback (for improving the service)"""
    try:
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Log feedback (in production, store in database)
        log_user_interaction(logger, user_id, f"feedback_rating_{rating}", "web")
        
        if feedback:
            logger.info(f"💭 User feedback from {user_id[:8]}... (rating: {rating}): {feedback[:100]}...")
        
        return {
            "message": "Thank you for your feedback!",
            "rating": rating,
            "status": "received"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")
