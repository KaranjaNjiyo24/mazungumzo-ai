# backend/models/chat_models.py
"""
Chat-related Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """Request model for chat messages"""
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="The user's message content")
    language: Optional[str] = Field(default="en", description="Language preference (en/sw)")
    platform: Optional[str] = Field(default="web", description="Platform origin (web/whatsapp)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatResponse(BaseModel):
    """Response model for chat responses"""
    response: str = Field(..., description="AI-generated response")
    is_crisis: bool = Field(..., description="Whether crisis was detected")
    confidence: float = Field(..., description="Crisis detection confidence score")
    language: str = Field(..., description="Response language")
    resources: List[str] = Field(default=[], description="Relevant mental health resources")
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = Field(None, description="Session identifier")


class WhatsAppWebhookData(BaseModel):
    """Model for WhatsApp webhook data from Twilio"""
    from_number: str = Field(..., description="Sender's WhatsApp number")
    to_number: str = Field(..., description="Recipient's WhatsApp number")
    message_body: str = Field(..., description="Message content")
    message_sid: str = Field(..., description="Twilio message SID")
    account_sid: str = Field(..., description="Twilio account SID")
    num_media: str = Field(default="0", description="Number of media attachments")
    profile_name: Optional[str] = Field(None, description="WhatsApp profile name")
    wa_id: Optional[str] = Field(None, description="WhatsApp ID")


class APIHealthResponse(BaseModel):
    """Response model for health check endpoints"""
    app: str
    status: str
    description: str
    version: str
    timestamp: datetime
    environment: Optional[str] = None


class StatsResponse(BaseModel):
    """Response model for usage statistics"""
    active_users: int
    total_conversations: int
    crisis_keywords_monitored: int
    resources_available: int
    uptime_hours: Optional[float] = None
