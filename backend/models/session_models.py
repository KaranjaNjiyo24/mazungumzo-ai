# backend/models/session_models.py
"""
User session and conversation models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message roles for conversation tracking"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserSession(BaseModel):
    """User session data model"""
    user_id: str
    platform: str = "web"  # web, whatsapp, sms
    language_preference: str = "en"
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    crisis_flags: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    session_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
        self.last_activity = datetime.now()
    
    def get_recent_messages(self, limit: int = 6) -> List[Dict[str, str]]:
        """Get recent messages formatted for AI API"""
        recent = self.conversation_history[-limit:] if limit > 0 else self.conversation_history
        return [{"role": msg.role.value, "content": msg.content} for msg in recent]
    
    def flag_crisis(self, confidence: float, keywords: List[str], message: str):
        """Flag a crisis incident"""
        crisis_flag = {
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "keywords_detected": keywords,
            "message_excerpt": message[:100],
            "handled": False
        }
        self.crisis_flags.append(crisis_flag)


class SessionManager:
    """In-memory session manager (replace with Redis/DB in production)"""
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
    
    def get_session(self, user_id: str, platform: str = "web") -> UserSession:
        """Get or create user session"""
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(
                user_id=user_id,
                platform=platform
            )
        return self._sessions[user_id]
    
    def update_session(self, session: UserSession):
        """Update session data"""
        session.last_activity = datetime.now()
        self._sessions[session.user_id] = session
    
    def get_active_users_count(self) -> int:
        """Get count of active users"""
        return len(self._sessions)
    
    def get_total_conversations_count(self) -> int:
        """Get total number of conversation messages"""
        return sum(len(session.conversation_history) for session in self._sessions.values())
    
    def cleanup_old_sessions(self, hours: int = 24):
        """Remove sessions older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        old_sessions = [
            user_id for user_id, session in self._sessions.items()
            if session.last_activity.timestamp() < cutoff_time
        ]
        for user_id in old_sessions:
            del self._sessions[user_id]
