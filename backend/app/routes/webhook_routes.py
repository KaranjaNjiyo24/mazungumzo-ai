# backend/app/routes/webhook_routes.py
"""
WhatsApp webhook routes for Mazungumzo AI
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
import hmac
import hashlib
from typing import Dict, Any

from backend.models.chat_models import WhatsAppWebhookData
from backend.services.whatsapp_service import WhatsAppService
from backend.services.session_service import SessionService
from backend.services.crisis_service import CrisisDetectionService
from backend.utils.config import get_settings
from backend.utils.logging_config import get_logger, log_user_interaction, log_error_with_context

webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = get_logger("webhook")
settings = get_settings()

# Initialize services
whatsapp_service = WhatsAppService()
session_service = SessionService()
crisis_service = CrisisDetectionService()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from WhatsApp/Twilio"""
    try:
        expected_signature = hmac.new(
            settings.WHATSAPP_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@webhook_router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    """
    Verify WhatsApp webhook during setup
    """
    try:
        if (hub_mode == "subscribe" and 
            hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN):
            logger.info("✅ WhatsApp webhook verified successfully")
            return PlainTextResponse(hub_challenge)
        else:
            logger.warning("❌ WhatsApp webhook verification failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook verification failed"
            )
    except Exception as e:
        log_error_with_context(logger, e, {"hub_mode": hub_mode})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@webhook_router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature if enabled
        if settings.VERIFY_WEBHOOK_SIGNATURE:
            signature = request.headers.get("X-Hub-Signature-256", "")
            if not verify_webhook_signature(body, signature.replace("sha256=", "")):
                logger.warning("❌ Invalid webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid signature"
                )
        
        # Parse webhook data
        webhook_data = WhatsAppWebhookData.parse_raw(body)
        
        # Process each entry
        await process_whatsapp_message({
            "messages": [{
                "from": webhook_data.from_number,
                "text": {"body": webhook_data.message_body},
                "id": webhook_data.message_sid
            }]
        })
        
        return {"status": "success"}
        
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


async def process_whatsapp_message(message_data: Dict[str, Any]):
    """
    Process incoming WhatsApp message
    """
    try:
        messages = message_data.get("messages", [])
        
        for message in messages:
            user_phone = message.get("from")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            if not user_phone or not message_text:
                continue
            
            logger.info(f"📱 WhatsApp message received from {user_phone[:8]}...")
            log_user_interaction(logger, user_phone, "whatsapp_message", "whatsapp")
            
            # Get or create session
            session_id = await session_service.get_or_create_session(
                user_id=user_phone,
                platform="whatsapp"
            )
            
            # Check for crisis indicators
            crisis_result = await crisis_service.detect_crisis(message_text)
            
            if crisis_result.is_crisis:
                # Handle crisis situation
                await handle_crisis_message(user_phone, message_text, crisis_result)
            else:
                # Handle normal conversation
                await handle_normal_message(user_phone, message_text, session_id)
                
    except Exception as e:
        log_error_with_context(logger, e, {"message_data": message_data})


async def handle_crisis_message(user_phone: str, message: str, crisis_result):
    """
    Handle crisis messages with immediate resources
    """
    try:
        # Log crisis detection
        from backend.utils.logging_config import log_crisis_detection
        log_crisis_detection(logger, user_phone, crisis_result.confidence, crisis_result.keywords)
        
        # Send immediate crisis resources
        crisis_response = await crisis_service.get_crisis_resources(
            country="Kenya",  # Default for now
            urgent=True
        )
        
        # Send crisis response via WhatsApp
        await whatsapp_service.send_message(
            to=user_phone,
            message=crisis_response.message
        )
        
        # Update session with crisis flag
        await session_service.update_session_risk(
            user_id=user_phone,
            risk_level="high",
            crisis_indicators=crisis_result.keywords
        )
        
    except Exception as e:
        log_error_with_context(logger, e, {"user_phone": user_phone})


async def handle_normal_message(user_phone: str, message: str, session_id: str):
    """
    Handle normal conversation messages
    """
    try:
        # Get AI response
        from backend.services.ai_service import AIService
        ai_service = AIService()
        
        # Get conversation history
        history = await session_service.get_conversation_history(session_id)
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            message=message,
            conversation_history=history,
            user_context={
                "platform": "whatsapp",
                "country": "Kenya"
            }
        )
        
        # Send response via WhatsApp
        await whatsapp_service.send_message(
            to=user_phone,
            message=ai_response.message
        )
        
        # Update conversation history
        await session_service.add_message(
            session_id=session_id,
            message=message,
            response=ai_response.message,
            metadata={
                "platform": "whatsapp",
                "message_type": "text"
            }
        )
        
    except Exception as e:
        log_error_with_context(logger, e, {"user_phone": user_phone, "session_id": session_id})


@webhook_router.post("/twilio")
async def handle_twilio_webhook(request: Request):
    """
    Handle Twilio SMS webhooks (alternative to WhatsApp)
    """
    try:
        form_data = await request.form()
        
        user_phone = form_data.get("From")
        message_text = form_data.get("Body")
        
        if not user_phone or not message_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )
        
        logger.info(f"📨 Twilio SMS received from {user_phone[:8]}...")
        log_user_interaction(logger, user_phone, "sms_message", "sms")
        
        # Process similar to WhatsApp but via SMS
        session_id = await session_service.get_or_create_session(
            user_id=user_phone,
            platform="sms"
        )
        
        # Check for crisis
        crisis_result = await crisis_service.detect_crisis(message_text)
        
        if crisis_result.is_crisis:
            await handle_crisis_sms(user_phone, message_text, crisis_result)
        else:
            await handle_normal_sms(user_phone, message_text, session_id)
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing SMS webhook"
        )


async def handle_crisis_sms(user_phone: str, message: str, crisis_result):
    """Handle crisis SMS messages"""
    try:
        from backend.utils.logging_config import log_crisis_detection
        log_crisis_detection(logger, user_phone, crisis_result.confidence, crisis_result.keywords)
        
        crisis_response = await crisis_service.get_crisis_resources(
            country="Kenya",
            urgent=True
        )
        
        # Send SMS response (implement SMS sending)
        # This would use Twilio SMS API
        logger.info(f"📤 Crisis SMS response sent to {user_phone[:8]}...")
        
    except Exception as e:
        log_error_with_context(logger, e, {"user_phone": user_phone})


async def handle_normal_sms(user_phone: str, message: str, session_id: str):
    """Handle normal SMS conversation"""
    try:
        from backend.services.ai_service import AIService
        ai_service = AIService()
        
        history = await session_service.get_conversation_history(session_id)
        
        ai_response = await ai_service.generate_response(
            message=message,
            conversation_history=history,
            user_context={
                "platform": "sms",
                "country": "Kenya"
            }
        )
        
        # Send SMS response (implement SMS sending)
        logger.info(f"📤 SMS response sent to {user_phone[:8]}...")
        
        await session_service.add_message(
            session_id=session_id,
            message=message,
            response=ai_response.message,
            metadata={
                "platform": "sms",
                "message_type": "text"
            }
        )
        
    except Exception as e:
        log_error_with_context(logger, e, {"user_phone": user_phone, "session_id": session_id})
