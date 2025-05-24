# backend/services/whatsapp_service.py
"""
WhatsApp Integration for Mazungumzo AI
Handles Twilio WhatsApp Business API integration

This service:
- Receives WhatsApp messages via webhooks
- Sends responses back to users
- Formats messages for WhatsApp constraints
- Handles media (future: voice messages)
"""

import os
import logging
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import asyncio
import httpx

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio WhatsApp client initialized")
        else:
            self.client = None
            logger.warning("⚠️ Twilio credentials not found - WhatsApp features disabled")
    
    def format_message_for_whatsapp(self, message: str, is_crisis: bool = False) -> str:
        """
        Format AI response for WhatsApp constraints
        - Max 1600 characters per message
        - Use WhatsApp-friendly formatting
        """
        
        # Add WhatsApp emoji formatting
        formatted = message.replace("**", "*")  # Bold formatting
        formatted = formatted.replace("__", "_")  # Italic formatting
        
        # Add crisis header if needed
        if is_crisis:
            crisis_header = "🆘 *MAZUNGUMZO CRISIS SUPPORT*\n\n"
            formatted = crisis_header + formatted
        
        # Split long messages
        if len(formatted) > 1500:
            # Find good break point
            break_point = formatted.rfind('\n', 0, 1500)
            if break_point == -1:
                break_point = formatted.rfind(' ', 0, 1500)
            if break_point == -1:
                break_point = 1500
            
            part1 = formatted[:break_point] + "\n\n_[Continued...]_"
            part2 = "_[...Continued]_\n\n" + formatted[break_point:]
            
            return [part1, part2]
        
        return [formatted]
    
    async def send_whatsapp_message(
        self, 
        to_number: str, 
        message: str, 
        is_crisis: bool = False
    ) -> bool:
        """
        Send message via Twilio WhatsApp API
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            # Format message for WhatsApp
            formatted_messages = self.format_message_for_whatsapp(message, is_crisis)
            
            # Send each part
            for msg_part in formatted_messages:
                message_obj = self.client.messages.create(
                    body=msg_part,
                    from_=self.whatsapp_number,
                    to=f"whatsapp:{to_number}"
                )
                
                logger.info(f"✅ WhatsApp message sent to {to_number}: {message_obj.sid}")
                
                # Small delay between parts
                if len(formatted_messages) > 1:
                    await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {str(e)}")
            return False
    
    def create_webhook_response(self, response_text: str) -> str:
        """
        Create TwiML response for webhook
        This is used when responding directly via webhook
        """
        try:
            resp = MessagingResponse()
            msg = resp.message()
            msg.body(response_text)
            return str(resp)
        except Exception as e:
            logger.error(f"Failed to create webhook response: {str(e)}")
            return ""
    
    def parse_webhook_data(self, form_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse incoming webhook data from Twilio
        """
        return {
            "from_number": form_data.get("From", "").replace("whatsapp:", ""),
            "to_number": form_data.get("To", "").replace("whatsapp:", ""),
            "message_body": form_data.get("Body", ""),
            "message_sid": form_data.get("MessageSid", ""),
            "account_sid": form_data.get("AccountSid", ""),
            "num_media": form_data.get("NumMedia", "0"),
            "profile_name": form_data.get("ProfileName", ""),
            "wa_id": form_data.get("WaId", "")
        }
    
    async def send_crisis_resources(self, to_number: str) -> bool:
        """
        Send Kenya mental health crisis resources via WhatsApp
        """
        crisis_message = """🆘 *MAZUNGUMZO - URGENT HELP*

Nakuona unaweza kuhitaji msaada wa haraka. Hii ni muhimu:

*24/7 Crisis Hotlines:*
📞 Kenya Red Cross: 1199
📞 Befrienders Kenya: +254 722 178 177
📞 Suicide Prevention: +254 722 178 177

*Hospitals:*
🏥 Mathari Hospital: +254 20 2723841
🏥 Nairobi Hospital: +254 719 055555
🏥 Aga Khan Hospital: +254 20 3662000

*Remember:*
✨ You are not alone
✨ Help is available
✨ Things can get better

_Tafadhali ongea na mtu wa karibu au ugonga hospitali. Maisha yako ni muhimu._

---
*I see you might need immediate help. Please talk to someone close or visit a hospital. Your life matters.*"""

        return await self.send_whatsapp_message(to_number, crisis_message, is_crisis=True)

# Global instance
whatsapp_service = WhatsAppService()


# backend/services/twilio_webhook.py
"""
Enhanced webhook handler for Twilio WhatsApp integration
"""

from fastapi import Request, HTTPException
from fastapi.responses import Response
import logging
from .whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

async def handle_whatsapp_webhook(request: Request) -> Response:
    """
    Enhanced WhatsApp webhook handler
    Processes incoming messages and sends responses
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        webhook_data = whatsapp_service.parse_webhook_data(dict(form_data))
        
        from_number = webhook_data["from_number"]
        message_body = webhook_data["message_body"]
        profile_name = webhook_data.get("profile_name", "Friend")
        
        if not message_body:
            logger.warning("Received empty message from WhatsApp")
            return Response(content="", status_code=200)
        
        logger.info(f"📱 WhatsApp message from {profile_name} ({from_number}): {message_body}")
        
        # Import here to avoid circular imports
        from ..app.main import call_ai_api, detect_crisis
        
        # Process through AI system
        user_id = f"whatsapp_{from_number}"
        
        # Crisis detection
        is_crisis, confidence = await detect_crisis(message_body)
        
        if is_crisis and confidence > 0.5:
            # High-priority crisis response
            logger.warning(f"🚨 Crisis detected for user {user_id} (confidence: {confidence})")
            
            # Send crisis resources immediately
            await whatsapp_service.send_crisis_resources(from_number)
            
            # Also send AI response
            ai_response = await call_ai_api(message_body, user_id, "sw")  # Default to Swahili
            await whatsapp_service.send_whatsapp_message(from_number, ai_response, is_crisis=True)
        
        else:
            # Normal AI response
            ai_response = await call_ai_api(message_body, user_id, "sw")
            await whatsapp_service.send_whatsapp_message(from_number, ai_response)
        
        # Return empty response (we're handling sending separately)
        return Response(content="", status_code=200, media_type="text/xml")
        
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {str(e)}")
        
        # Try to send error message to user
        try:
            error_msg = "Pole sana, nina tatizo kidogo. Tafadhali jaribu tena. 🤖 (Sorry, I have a small problem. Please try again.)"
            if 'from_number' in locals():
                await whatsapp_service.send_whatsapp_message(from_number, error_msg)
        except:
            pass
        
        return Response(content="", status_code=200)


# backend/services/message_formatter.py
"""
Message formatting utilities for different platforms
"""

class MessageFormatter:
    
    @staticmethod
    def format_for_whatsapp(message: str, is_crisis: bool = False) -> str:
        """Format message for WhatsApp with proper emoji and formatting"""
        
        # Replace markdown with WhatsApp formatting
        formatted = message.replace("**", "*")  # Bold
        formatted = formatted.replace("__", "_") # Italic
        
        # Add appropriate emojis
        if "hujambo" in message.lower() or "hello" in message.lower():
            formatted = "👋 " + formatted
        
        if "pole" in message.lower() or "sorry" in message.lower():
            formatted = "💙 " + formatted
        
        if is_crisis:
            formatted = "🆘 " + formatted
        
        return formatted
    
    @staticmethod
    def format_for_sms(message: str, max_length: int = 160) -> list:
        """Format message for SMS with length constraints"""
        
        # Remove emojis for SMS compatibility
        import re
        formatted = re.sub(r'[^\w\s.,!?-]', '', message)
        
        # Split into SMS-sized chunks
        if len(formatted) <= max_length:
            return [formatted]
        
        chunks = []
        while len(formatted) > max_length:
            # Find good break point
            break_point = formatted.rfind(' ', 0, max_length - 10)
            if break_point == -1:
                break_point = max_length - 10
            
            chunk = formatted[:break_point] + "...(1/2)"
            chunks.append(chunk)
            formatted = "...(2/2)" + formatted[break_point:]
        
        chunks.append(formatted)
        return chunks
    
    @staticmethod
    def add_crisis_header(message: str, platform: str = "whatsapp") -> str:
        """Add crisis-specific formatting based on platform"""
        
        headers = {
            "whatsapp": "🆘 *MAZUNGUMZO CRISIS SUPPORT*\n\n",
            "sms": "CRISIS SUPPORT - MAZUNGUMZO\n",
            "web": "⚠️ CRISIS SUPPORT ACTIVATED\n\n"
        }
        
        header = headers.get(platform, headers["web"])
        return header + message