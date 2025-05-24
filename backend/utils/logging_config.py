# backend/utils/logging_config.py
"""
Logging configuration for Mazungumzo AI
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import os


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Add color to logger name
        record.name = f"\033[34m{record.name}\033[0m"  # Blue
        
        return super().format(record)


class MazungumzoFilter(logging.Filter):
    """Custom filter for Mazungumzo-specific logging"""
    
    def filter(self, record):
        # Add custom attributes
        record.app_name = "Mazungumzo"
        record.timestamp_iso = datetime.now().isoformat()
        
        # Filter out sensitive information
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Don't log API keys or tokens
            sensitive_patterns = ['api_key', 'token', 'password', 'secret']
            for pattern in sensitive_patterns:
                if pattern.lower() in record.msg.lower():
                    record.msg = record.msg.replace(pattern, '***REDACTED***')
        
        return True


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_colors: bool = True,
    include_timestamp: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        use_colors: Whether to use colored output for console
        include_timestamp: Whether to include timestamps in logs
        
    Returns:
        Configured logger instance
    """
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    
    # Create formatters
    if include_timestamp:
        console_format = "%(asctime)s | %(app_name)s | %(name)s | %(levelname)s | %(message)s"
        file_format = "%(timestamp_iso)s | %(app_name)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
    else:
        console_format = "%(app_name)s | %(name)s | %(levelname)s | %(message)s"
        file_format = "%(app_name)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if use_colors and sys.stdout.isatty():  # Only use colors if outputting to terminal
        console_formatter = ColoredFormatter(console_format)
    else:
        console_formatter = logging.Formatter(console_format)
    
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(MazungumzoFilter())
    
    # Add console handler to root logger
    logging.getLogger().addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(MazungumzoFilter())
        
        logging.getLogger().addHandler(file_handler)
    
    # Get the main logger
    logger = logging.getLogger("mazungumzo")
    
    # Log startup message
    logger.info("🚀 Mazungumzo AI logging system initialized")
    logger.info(f"📊 Log level: {level}")
    if log_file:
        logger.info(f"📁 Log file: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f"mazungumzo.{name}")


def log_api_call(logger: logging.Logger, service: str, endpoint: str, status: str, duration_ms: float):
    """Log API calls with standardized format"""
    logger.info(f"🔗 API Call | {service} | {endpoint} | {status} | {duration_ms:.2f}ms")


def log_user_interaction(logger: logging.Logger, user_id: str, action: str, platform: str = "web"):
    """Log user interactions with privacy protection"""
    # Hash user_id for privacy
    user_hash = hash(user_id) % 10000
    logger.info(f"👤 User Interaction | user_{user_hash} | {action} | {platform}")


def log_crisis_detection(logger: logging.Logger, user_id: str, confidence: float, keywords: list):
    """Log crisis detection events (with special attention)"""
    user_hash = hash(user_id) % 10000
    logger.warning(f"🚨 CRISIS DETECTED | user_{user_hash} | confidence: {confidence:.2f} | keywords: {len(keywords)}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    """Log errors with additional context"""
    context_str = ""
    if context:
        context_items = [f"{k}={v}" for k, v in context.items()]
        context_str = f" | Context: {', '.join(context_items)}"
    
    logger.error(f"❌ Error: {type(error).__name__}: {str(error)}{context_str}", exc_info=True)


# Performance logging decorator
def log_performance(func_name: str):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("performance")
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"⚡ Performance | {func_name} | {duration:.2f}ms | SUCCESS")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.warning(f"⚡ Performance | {func_name} | {duration:.2f}ms | ERROR: {str(e)}")
                raise
        return wrapper
    return decorator


# Async performance logging decorator
def log_async_performance(func_name: str):
    """Decorator to log async function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = get_logger("performance")
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"⚡ Async Performance | {func_name} | {duration:.2f}ms | SUCCESS")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.warning(f"⚡ Async Performance | {func_name} | {duration:.2f}ms | ERROR: {str(e)}")
                raise
        return wrapper
    return decorator
