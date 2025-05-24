# backend/app/routes/__init__.py
"""
API route modules for Mazungumzo AI
"""

from .chat_routes import chat_router
from .webhook_routes import webhook_router  
from .health_routes import health_router

__all__ = [
    'chat_router',
    'webhook_router',
    'health_router'
]
