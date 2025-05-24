# backend/app/routes/health_routes.py
"""
Health check and system status routes for Mazungumzo AI
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
import asyncio
import psutil
import os
from typing import Dict, Any

from backend.models.chat_models import APIHealthResponse
from backend.services.ai_service import AIService
from backend.services.session_service import SessionService
from backend.utils.config import get_settings
from backend.utils.logging_config import get_logger, log_error_with_context

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("health")
settings = get_settings()

# Service instances for health checks
ai_service = AIService()
session_service = SessionService()

# Cache for health check results
_health_cache = {}
_cache_ttl = 60  # Cache for 60 seconds


@router.get("/", response_model=APIHealthResponse)
async def health_check():
    """
    Basic health check endpoint
    """
    try:
        return APIHealthResponse(
            app="Mazungumzo AI",
            status="healthy",
            description="Mental Health Chat Companion for Kenya",
            version=settings.APP_VERSION,
            timestamp=datetime.utcnow(),
            environment=settings.ENVIRONMENT
        )
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with service status
    """
    try:
        # Check cache first
        cache_key = "detailed_health"
        if (cache_key in _health_cache and 
            datetime.utcnow() - _health_cache[cache_key]["timestamp"] < timedelta(seconds=_cache_ttl)):
            return _health_cache[cache_key]["data"]
        
        # Perform health checks
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {},
            "system": await get_system_metrics(),
            "uptime": get_uptime()
        }
        
        # Check AI service health
        ai_health = await check_ai_service_health()
        health_data["services"]["ai"] = ai_health
        
        # Check session service health
        session_health = await check_session_service_health()
        health_data["services"]["sessions"] = session_health
        
        # Check database health (if applicable)
        db_health = await check_database_health()
        health_data["services"]["database"] = db_health
        
        # Determine overall status
        service_statuses = [service["status"] for service in health_data["services"].values()]
        if "unhealthy" in service_statuses:
            health_data["status"] = "unhealthy"
        elif "degraded" in service_statuses:
            health_data["status"] = "degraded"
        
        # Cache the result
        _health_cache[cache_key] = {
            "data": health_data,
            "timestamp": datetime.utcnow()
        }
        
        return health_data
        
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detailed health check failed"
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    """
    try:
        # Check if all critical services are ready
        checks = await asyncio.gather(
            check_ai_service_health(),
            check_session_service_health(),
            return_exceptions=True
        )
        
        # If any check failed, return not ready
        for check in checks:
            if isinstance(check, Exception) or check.get("status") == "unhealthy":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not ready"
                )
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Readiness check failed"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    """
    try:
        # Basic liveness check - just ensure the service is running
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "pid": os.getpid()
        }
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Liveness check failed"
        )


@router.get("/metrics")
async def get_metrics():
    """
    Basic application metrics
    """
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": await get_system_metrics(),
            "application": await get_application_metrics(),
            "uptime": get_uptime()
        }
        
        return metrics
        
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


async def check_ai_service_health() -> Dict[str, Any]:
    """
    Check AI service health
    """
    try:
        # Test AI service with a simple health check
        health_result = await ai_service.health_check()
        
        return {
            "status": "healthy" if health_result else "unhealthy",
            "provider": ai_service.current_provider,
            "last_check": datetime.utcnow().isoformat(),
            "response_time_ms": getattr(health_result, "response_time", 0) if health_result else None
        }
        
    except Exception as e:
        logger.warning(f"AI service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }


async def check_session_service_health() -> Dict[str, Any]:
    """
    Check session service health
    """
    try:
        # Test session service
        session_count = await session_service.get_active_session_count()
        
        return {
            "status": "healthy",
            "active_sessions": session_count,
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.warning(f"Session service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }


async def check_database_health() -> Dict[str, Any]:
    """
    Check database health (placeholder for future database integration)
    """
    try:
        # For now, return healthy since we're using in-memory storage
        return {
            "status": "healthy",
            "type": "in_memory",
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }


async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics
    """
    try:
        # CPU and memory metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
        
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


async def get_application_metrics() -> Dict[str, Any]:
    """
    Get application-specific metrics
    """
    try:
        # Get session statistics
        session_stats = await session_service.get_session_statistics()
        
        return {
            "sessions": session_stats,
            "cache": {
                "health_cache_size": len(_health_cache),
                "cache_ttl_seconds": _cache_ttl
            },
            "process": {
                "pid": os.getpid(),
                "threads": len(psutil.Process().threads())
            }
        }
        
    except Exception as e:
        logger.warning(f"Failed to get application metrics: {e}")
        return {"error": str(e)}


def get_uptime() -> Dict[str, Any]:
    """
    Get application uptime
    """
    try:
        # Get process start time
        process = psutil.Process()
        start_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - start_time
        
        return {
            "start_time": start_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0]  # Remove microseconds
        }
        
    except Exception as e:
        logger.warning(f"Failed to get uptime: {e}")
        return {"error": str(e)}


@router.get("/version")
async def get_version():
    """
    Get application version information
    """
    try:
        return {
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        log_error_with_context(logger, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version information"
        )

# Export the router
health_router = router
