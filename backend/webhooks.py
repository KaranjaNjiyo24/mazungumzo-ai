# backend/webhooks.py
"""
Webhook handlers for external services (WhatsApp, etc.)
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict
import logging
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from utils.config import settings
from services.json_database import db, add_message, log_crisis
from services.advanced_features import enhance_ai_response, voice_service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Request Models
class WhatsAppMessage(BaseModel):
    From: str
    Body: str
    MediaUrl0: Optional[str] = None
    NumMedia: Optional[int] = 0

# Twilio validator
validator = RequestValidator(settings.twilio_auth_token)

async def validate_twilio_request(request: Request):
    """Validate incoming Twilio requests"""
    if not settings.has_twilio_config:
        raise HTTPException(status_code=403, detail="Twilio not configured")
    
    # Get the URL and POST data
    url = str(request.url)
    form_data = await request.form()
    
    # Validate the request
    if not validator.validate(url, form_data, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        # Validate request
        await validate_twilio_request(request)
        
        # Parse message
        form_data = await request.form()
        message = WhatsAppMessage(**form_data)
        
        # Extract user ID from WhatsApp number
        user_id = message.From.replace("whatsapp:", "")
        
        # Handle voice message
        if message.NumMedia and message.MediaUrl0:
            # Process voice message
            transcription = await voice_service.process_voice_message(
                message.MediaUrl0,
                user_id
            )
            
            # Add transcription to chat
            await add_message(user_id, "user", transcription, "sw")
            
            # Get AI response
            enhanced = await enhance_ai_response(
                transcription,
                user_id,
                "I understand your voice message. Let's talk about it."
            )
            
            # Convert response to voice
            voice_url = await voice_service.convert_response_to_voice(
                enhanced["response"],
                "sw"
            )
            
            # Create TwiML response
            response = MessagingResponse()
            response.message(enhanced["response"])
            response.message().media(voice_url)
            
            return Response(content=str(response), media_type="application/xml")
        
        # Handle text message
        else:
            # Add message to chat
            await add_message(user_id, "user", message.Body, "sw")
            
            # Get AI response
            enhanced = await enhance_ai_response(
                message.Body,
                user_id,
                "I understand. Let's talk about it."
            )
            
            # Create TwiML response
            response = MessagingResponse()
            response.message(enhanced["response"])
            
            return Response(content=str(response), media_type="application/xml")
            
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook/whatsapp")
async def whatsapp_verification(request: Request):
    """Handle WhatsApp webhook verification"""
    try:
        # Get verification parameters
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        # Verify token
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Invalid verification token")
            
    except Exception as e:
        logger.error(f"WhatsApp verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 