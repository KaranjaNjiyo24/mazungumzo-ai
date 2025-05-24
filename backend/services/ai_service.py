# backend/services/ai_service.py
"""
AI Service for Mazungumzo AI
Handles communication with Cerebras and OpenRouter APIs
"""

import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from utils.config import settings, get_system_prompt
from utils.logging_config import get_logger, log_async_performance, log_api_call, log_error_with_context
from utils.constants import SYSTEM_PROMPTS
from models.session_models import ConversationMessage, MessageRole


class AIService:
    """Service for AI chat completions using Cerebras and OpenRouter"""
    
    def __init__(self):
        self.logger = get_logger("ai_service")
        self.cerebras_available = settings.has_cerebras_config
        self.openrouter_available = settings.has_openrouter_config
        
        if not (self.cerebras_available or self.openrouter_available):
            self.logger.warning("⚠️ No AI services configured")
        else:
            self.logger.info(f"✅ AI Service initialized - Cerebras: {self.cerebras_available}, OpenRouter: {self.openrouter_available}")
    
    @log_async_performance("ai_generate_response")
    async def generate_response(
        self, 
        message: str, 
        conversation_history: List[ConversationMessage] = None,
        language: str = "en",
        is_crisis: bool = False,
        user_id: str = None
    ) -> str:
        """
        Generate AI response using available services
        
        Args:
            message: User's message
            conversation_history: Previous conversation messages
            language: Preferred language (en/sw)
            is_crisis: Whether this is a crisis situation
            user_id: User identifier for logging
            
        Returns:
            AI-generated response
        """
        
        # Prepare conversation context
        messages = self._prepare_messages(message, conversation_history, language, is_crisis)
        
        # Try Cerebras first (faster)
        if self.cerebras_available:
            try:
                response = await self._call_cerebras(messages, user_id)
                if response:
                    return response
            except Exception as e:
                self.logger.warning(f"Cerebras API failed, falling back to OpenRouter: {str(e)}")
        
        # Fallback to OpenRouter
        if self.openrouter_available:
            try:
                response = await self._call_openrouter(messages, user_id)
                if response:
                    return response
            except Exception as e:
                self.logger.error(f"OpenRouter API also failed: {str(e)}")
        
        # Final fallback response
        return self._get_fallback_response(language, is_crisis)
    
    def _prepare_messages(
        self, 
        message: str, 
        conversation_history: List[ConversationMessage] = None,
        language: str = "en",
        is_crisis: bool = False
    ) -> List[Dict[str, str]]:
        """Prepare messages array for AI API"""
        
        # Choose appropriate system prompt
        if is_crisis:
            system_prompt = SYSTEM_PROMPTS["crisis"]
        elif language != "en":
            system_prompt = SYSTEM_PROMPTS["multilingual"] 
        else:
            system_prompt = get_system_prompt(language)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limited to recent messages)
        if conversation_history:
            recent_history = conversation_history[-settings.max_conversation_history:]
            for msg in recent_history:
                if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    async def _call_cerebras(self, messages: List[Dict[str, str]], user_id: str = None) -> Optional[str]:
        """Call Cerebras API for fast response"""
        
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.cerebras_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.cerebras_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.cerebras_model,
                        "messages": messages,
                        "max_tokens": settings.max_tokens,
                        "temperature": settings.temperature
                    },
                    timeout=settings.ai_timeout
                )
                
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    
                    log_api_call(self.logger, "Cerebras", "chat/completions", "SUCCESS", duration_ms)
                    self.logger.info(f"✅ Cerebras response generated ({len(ai_response)} chars)")
                    
                    return ai_response
                else:
                    log_api_call(self.logger, "Cerebras", "chat/completions", f"HTTP_{response.status_code}", duration_ms)
                    self.logger.warning(f"Cerebras API returned {response.status_code}: {response.text}")
                    return None
                    
        except asyncio.TimeoutError:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_api_call(self.logger, "Cerebras", "chat/completions", "TIMEOUT", duration_ms)
            self.logger.warning("Cerebras API timeout")
            return None
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_api_call(self.logger, "Cerebras", "chat/completions", "ERROR", duration_ms)
            log_error_with_context(self.logger, e, {"service": "cerebras", "user_id": user_id})
            return None
    
    async def _call_openrouter(self, messages: List[Dict[str, str]], user_id: str = None) -> Optional[str]:
        """Call OpenRouter API for multilingual support"""
        
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://mazungumzo-ai.hackathon",
                        "X-Title": "Mazungumzo AI Hackathon"
                    },
                    json={
                        "model": settings.openrouter_model,
                        "messages": messages,
                        "max_tokens": settings.max_tokens,
                        "temperature": settings.temperature
                    },
                    timeout=settings.ai_timeout
                )
                
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    
                    log_api_call(self.logger, "OpenRouter", "chat/completions", "SUCCESS", duration_ms)
                    self.logger.info(f"✅ OpenRouter response generated ({len(ai_response)} chars)")
                    
                    return ai_response
                else:
                    log_api_call(self.logger, "OpenRouter", "chat/completions", f"HTTP_{response.status_code}", duration_ms)
                    self.logger.warning(f"OpenRouter API returned {response.status_code}: {response.text}")
                    return None
                    
        except asyncio.TimeoutError:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_api_call(self.logger, "OpenRouter", "chat/completions", "TIMEOUT", duration_ms)
            self.logger.warning("OpenRouter API timeout")
            return None
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_api_call(self.logger, "OpenRouter", "chat/completions", "ERROR", duration_ms)
            log_error_with_context(self.logger, e, {"service": "openrouter", "user_id": user_id})
            return None
    
    def _get_fallback_response(self, language: str = "en", is_crisis: bool = False) -> str:
        """Get fallback response when AI services are unavailable"""
        
        if is_crisis:
            if language.lower() in ["sw", "swahili"]:
                return ("Pole sana, nina tatizo la kiufundi lakini hii ni muhimu. "
                       "Tafadhali wasiliana na msaada wa haraka: Kenya Red Cross 1199 au "
                       "Befrienders Kenya +254 722 178 177. Huwezi kukabiliana na hili peke yako.")
            else:
                return ("I'm sorry, I'm having technical difficulties but this is important. "
                       "Please contact immediate help: Kenya Red Cross 1199 or "
                       "Befrienders Kenya +254 722 178 177. You don't have to face this alone.")
        
        if language.lower() in ["sw", "swahili"]:
            return ("Pole sana, nina tatizo kidogo la kiufundi sasa. "
                   "Tafadhali jaribu tena baadae. Je, kuna mtu wa karibu unayeweza kuongea naye?")
        else:
            return ("I'm sorry, I'm having some technical difficulties right now. "
                   "Please try again later. Is there someone close to you that you can talk to?")
    
    async def health_check(self) -> Dict[str, any]:
        """Check health of AI services"""
        
        health_status = {
            "cerebras": {"available": self.cerebras_available, "status": "unknown"},
            "openrouter": {"available": self.openrouter_available, "status": "unknown"}
        }
        
        # Quick health check for Cerebras
        if self.cerebras_available:
            try:
                start_time = datetime.now()
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.cerebras_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.cerebras_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": settings.cerebras_model,
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 10
                        },
                        timeout=5.0
                    )
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                health_status["cerebras"]["status"] = "healthy" if response.status_code == 200 else "error"
                health_status["cerebras"]["response_time_ms"] = duration_ms
            except Exception as e:
                health_status["cerebras"]["status"] = "error"
                health_status["cerebras"]["error"] = str(e)
        
        # Quick health check for OpenRouter
        if self.openrouter_available:
            try:
                start_time = datetime.now()
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.openrouter_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.openrouter_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": settings.openrouter_model,
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 10
                        },
                        timeout=5.0
                    )
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                health_status["openrouter"]["status"] = "healthy" if response.status_code == 200 else "error"
                health_status["openrouter"]["response_time_ms"] = duration_ms
            except Exception as e:
                health_status["openrouter"]["status"] = "error"
                health_status["openrouter"]["error"] = str(e)
        
        return health_status


# Global AI service instance
ai_service = AIService()
