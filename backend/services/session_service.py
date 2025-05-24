# backend/services/session_service.py
"""
Session Management Service for Mazungumzo AI
Handles user sessions, conversation history, and state management
"""

import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

from ..utils.config import settings
from ..utils.logging_config import get_logger, log_user_interaction, log_performance
from ..models.session_models import UserSession, SessionManager, ConversationMessage, MessageRole


class SessionService:
    """Service for managing user sessions and conversation state"""
    
    def __init__(self):
        self.logger = get_logger("session_service")
        self.session_manager = SessionManager()
        self.cleanup_task = None
        self.logger.info("✅ Session Service initialized")
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for session cleanup"""
        try:
            loop = asyncio.get_event_loop()
            self.cleanup_task = loop.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running, cleanup will be manual
            self.logger.info("No event loop available, session cleanup will be manual")
    
    async def _periodic_cleanup(self):
        """Periodically clean up old sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.cleanup_old_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup task: {str(e)}")
                await asyncio.sleep(3600)
    
    @log_performance("session_get_or_create")
    def get_or_create_session(self, user_id: str, platform: str = "web") -> UserSession:
        """Get existing session or create new one"""
        
        session = self.session_manager.get_session(user_id, platform)
        
        if not session.conversation_history:
            # New session - log user interaction
            log_user_interaction(self.logger, user_id, "session_created", platform)
            
            # Add welcome message for new sessions
            welcome_message = self._get_welcome_message(platform)
            session.add_message(
                MessageRole.ASSISTANT, 
                welcome_message,
                {"type": "welcome", "timestamp": datetime.now().isoformat()}
            )
        else:
            # Existing session - update last activity
            log_user_interaction(self.logger, user_id, "session_resumed", platform)
        
        self.session_manager.update_session(session)
        return session
    
    def _get_welcome_message(self, platform: str = "web") -> str:
        """Get appropriate welcome message based on platform"""
        
        current_hour = datetime.now().hour
        
        if platform == "whatsapp":
            if 5 <= current_hour < 12:
                return ("Habari za asubuhi! 🌅 Mimi ni Mazungumzo, rafiki yako wa msaada wa afya ya akili. "
                       "Niko hapa kukusikiliza. Unajisikiaje leo?")
            elif 12 <= current_hour < 17:
                return ("Habari za mchana! ☀️ Mimi ni Mazungumzo. Nimefurahi kuongea nawe. "
                       "Je, kuna kitu unachotaka kuongea nami?")
            elif 17 <= current_hour < 21:
                return ("Habari za jioni! 🌆 Mimi ni Mazungumzo, niko hapa kukusikiliza na kukusaidia. "
                       "Unajisikiaje?")
            else:
                return ("Habari za usiku! 🌙 Mimi ni Mazungumzo. Naona ni usiku wa manane - "
                       "unajisikiaje? Niko hapa kama unahitaji mtu wa kuongea naye.")
        else:
            return ("Hello! 👋 I'm Mazungumzo, your mental health companion. "
                   "I'm here to listen and support you. How are you feeling today?")
    
    @log_performance("session_add_message")
    def add_message_to_session(
        self, 
        user_id: str, 
        role: MessageRole, 
        content: str,
        platform: str = "web",
        metadata: Dict[str, Any] = None
    ) -> UserSession:
        """Add a message to user's session"""
        
        session = self.get_or_create_session(user_id, platform)
        session.add_message(role, content, metadata or {})
        
        # Log the interaction
        action = f"message_{role.value}"
        log_user_interaction(self.logger, user_id, action, platform)
        
        self.session_manager.update_session(session)
        return session
    
    def get_conversation_context(self, user_id: str, limit: int = None) -> List[ConversationMessage]:
        """Get conversation context for AI processing"""
        
        session = self.session_manager.get_session(user_id)
        context_limit = limit or settings.max_conversation_history
        
        return session.conversation_history[-context_limit:] if context_limit > 0 else session.conversation_history
    
    def get_session_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's session"""
        
        session = self.session_manager.get_session(user_id)
        
        # Count messages by role
        message_counts = {}
        for msg in session.conversation_history:
            role = msg.role.value
            message_counts[role] = message_counts.get(role, 0) + 1
        
        # Calculate session duration
        if session.conversation_history:
            session_duration = (session.last_activity - session.created_at).total_seconds() / 3600
        else:
            session_duration = 0
        
        return {
            "user_id": session.user_id,
            "platform": session.platform,
            "language_preference": session.language_preference,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "session_duration_hours": round(session_duration, 2),
            "message_counts": message_counts,
            "total_messages": len(session.conversation_history),
            "crisis_flags": len(session.crisis_flags),
            "has_recent_activity": (datetime.now() - session.last_activity).total_seconds() < 3600
        }
    
    def update_language_preference(self, user_id: str, language: str) -> UserSession:
        """Update user's language preference"""
        
        session = self.session_manager.get_session(user_id)
        session.language_preference = language
        session.last_activity = datetime.now()
        
        log_user_interaction(self.logger, user_id, f"language_changed_{language}", session.platform)
        
        self.session_manager.update_session(session)
        return session
    
    def get_user_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's risk profile based on session data"""
        
        session = self.session_manager.get_session(user_id)
        
        # Calculate risk indicators
        crisis_count = len(session.crisis_flags)
        recent_crisis = None
        
        if session.crisis_flags:
            recent_crisis = session.crisis_flags[-1]
            time_since_crisis = (datetime.now() - datetime.fromisoformat(recent_crisis["timestamp"])).total_seconds() / 3600
        else:
            time_since_crisis = float('inf')
        
        # Determine risk level
        if crisis_count >= 3 and time_since_crisis < 24:
            risk_level = "high"
        elif crisis_count >= 2 and time_since_crisis < 48:
            risk_level = "moderate"
        elif crisis_count >= 1 and time_since_crisis < 72:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_level": risk_level,
            "crisis_incidents": crisis_count,
            "last_crisis": recent_crisis,
            "hours_since_last_crisis": time_since_crisis if time_since_crisis != float('inf') else None,
            "needs_followup": risk_level in ["high", "moderate"],
            "recommended_action": self._get_risk_recommendation(risk_level, time_since_crisis)
        }
    
    def _get_risk_recommendation(self, risk_level: str, hours_since_crisis: float) -> str:
        """Get recommendation based on risk level"""
        
        if risk_level == "high":
            return "immediate_professional_support"
        elif risk_level == "moderate":
            return "professional_counseling_recommended"
        elif risk_level == "low" and hours_since_crisis < 72:
            return "continued_monitoring"
        else:
            return "regular_support"
    
    def cleanup_old_sessions(self, hours: int = None) -> int:
        """Clean up old sessions"""
        
        cleanup_hours = hours or settings.session_cleanup_hours
        initial_count = self.session_manager.get_active_users_count()
        
        self.session_manager.cleanup_old_sessions(cleanup_hours)
        
        final_count = self.session_manager.get_active_users_count()
        cleaned_count = initial_count - final_count
        
        if cleaned_count > 0:
            self.logger.info(f"🧹 Cleaned up {cleaned_count} old sessions (older than {cleanup_hours}h)")
        
        return cleaned_count
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics about platform usage"""
        
        platform_counts = {}
        language_counts = {}
        active_sessions = 0
        crisis_sessions = 0
        
        for session in self.session_manager._sessions.values():
            # Platform stats
            platform = session.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            # Language stats
            lang = session.language_preference
            language_counts[lang] = language_counts.get(lang, 0) + 1
            
            # Activity stats
            time_since_activity = (datetime.now() - session.last_activity).total_seconds() / 3600
            if time_since_activity < 1:  # Active in last hour
                active_sessions += 1
            
            # Crisis stats
            if session.crisis_flags:
                crisis_sessions += 1
        
        return {
            "platform_distribution": platform_counts,
            "language_distribution": language_counts,
            "active_sessions_last_hour": active_sessions,
            "sessions_with_crisis_flags": crisis_sessions,
            "total_sessions": len(self.session_manager._sessions)
        }
    
    def export_session_data(self, user_id: str, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export session data (for data portability/debugging)"""
        
        session = self.session_manager.get_session(user_id)
        
        export_data = {
            "user_id": session.user_id,
            "platform": session.platform,
            "language_preference": session.language_preference,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation_count": len(session.conversation_history),
            "crisis_flags_count": len(session.crisis_flags)
        }
        
        if include_sensitive:
            # Include actual conversation data (be careful with privacy)
            export_data["conversation_history"] = [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in session.conversation_history
            ]
            export_data["crisis_flags"] = session.crisis_flags
        
        return export_data
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global session statistics"""
        
        return {
            "active_users": self.session_manager.get_active_users_count(),
            "total_conversations": self.session_manager.get_total_conversations_count(),
            "platform_stats": self.get_platform_stats(),
            "session_service_status": "healthy"
        }


# Global session service instance
session_service = SessionService()
