# backend/services/__init__.py
"""
Service modules for Mazungumzo AI
"""

from .json_database import db, get_user_session, add_message, log_crisis, get_stats
from .advanced_features import (
    enhance_ai_response,
    advanced_service,
    voice_service,
    community_service
)
from .ai_service import ai_service

__all__ = [
    'db',
    'get_user_session',
    'add_message',
    'log_crisis',
    'get_stats',
    'enhance_ai_response',
    'advanced_service',
    'voice_service',
    'community_service',
    'ai_service'
]
