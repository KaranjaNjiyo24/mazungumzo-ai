# backend/utils/config.py
"""
Configuration management for Mazungumzo AI
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Configuration
    app_name: str = "Mazungumzo AI"
    app_version: str = "1.0.0"
    app_description: str = "Mental Health Chat Companion for Kenya"
    debug: bool = False
    environment: str = "development"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    # Database Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    redis_url: str = "redis://localhost:6379"
    
    # API Keys
    cerebras_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Twilio/WhatsApp Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    whatsapp_webhook_url: str = "https://your-ngrok-url.ngrok.io/webhook/whatsapp"
    whatsapp_verify_token: str = "mazungumzo_verify_token"
    
    # API Endpoints
    cerebras_base_url: str = "https://api.cerebras.ai/v1"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # CORS Configuration
    cors_origins: list = ["*"]  # In production, specify exact origins
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # AI Model Configuration
    cerebras_model: str = "qwen-3-32b"
    openrouter_model: str = "qwen/qwen3-8b:free"
    max_tokens: int = 200
    temperature: float = 0.7
    ai_timeout: float = 15.0
    
    # Crisis Detection Configuration
    crisis_confidence_threshold: float = 0.5
    max_conversation_history: int = 6
    
    # Session Management
    session_cleanup_hours: int = 24
    max_sessions: int = 10000
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def has_cerebras_config(self) -> bool:
        """Check if Cerebras API is configured"""
        return bool(self.cerebras_api_key)
    
    @property
    def has_openrouter_config(self) -> bool:
        """Check if OpenRouter API is configured"""
        return bool(self.openrouter_api_key)
    
    @property
    def has_twilio_config(self) -> bool:
        """Check if Twilio/WhatsApp is configured"""
        return bool(self.twilio_account_sid and self.twilio_auth_token)
    
    @property
    def has_ai_config(self) -> bool:
        """Check if any AI service is configured"""
        return self.has_cerebras_config or self.has_openrouter_config


# Global settings instance
settings = Settings()


def get_system_prompt(language: str = "en") -> str:
    """Get system prompt for AI based on language"""
    
    base_prompt = """You are Mazungumzo, a compassionate mental health companion for people in Kenya. 

Key guidelines:
- Be warm, empathetic, and culturally sensitive
- Provide emotional support and coping strategies
- If someone seems in crisis, gently suggest professional help
- Respect Kenyan cultural values and context
- Keep responses concise but meaningful (under 200 words)
- Never provide medical diagnosis or replace professional therapy
- Your goal is to be a supportive friend who listens and provides hope"""

    if language.lower() in ["sw", "swahili"]:
        return base_prompt + """
- Respond in Swahili when appropriate
- Use culturally relevant Kenyan expressions and understanding
- Remember that mental health stigma exists - be gentle and encouraging"""
    
    return base_prompt + """
- You can respond in both English and Swahili as needed
- Be sensitive to code-switching between languages
- Understand Kenyan English expressions and cultural context"""


def validate_environment():
    """Validate critical environment configuration"""
    issues = []
    
    if not settings.has_ai_config:
        issues.append("No AI service configured (CEREBRAS_API_KEY or OPENROUTER_API_KEY required)")
    
    if settings.environment == "production":
        if settings.cors_origins == ["*"]:
            issues.append("CORS origins should be restricted in production")
        if settings.debug:
            issues.append("Debug mode should be disabled in production")
    
    return issues


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
