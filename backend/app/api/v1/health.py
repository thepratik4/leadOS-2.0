from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.providers.search_provider import get_search_provider

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    # Test database connectivity safely without letting session failures crash with 500
    db_status = "healthy"
    db_error = None
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)


    # Provider health
    provider = get_search_provider()
    provider_health = provider.get_health()

    ai_enabled = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": {
            "status": db_status,
            "error": db_error,
        },
        "search_provider": {
            "name": provider_health.provider_name,
            "available": provider_health.is_available,
            "requires_key": provider_health.requires_key,
            "message": provider_health.message,
        },
        "ai_assisted_extraction": {
            "configured": ai_enabled,
            "mode": "hybrid_gemini_assisted" if ai_enabled else "pure_deterministic_rules",
        },
    }
