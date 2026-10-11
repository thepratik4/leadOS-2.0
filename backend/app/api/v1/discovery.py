from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.models.search_run import SearchRun
from app.schemas.discovery import (
    DiscoverySearchRequest,
    DiscoverySearchResponse,
    SearchRunResponse,
)
from app.services.discovery_service import discovery_service

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.post("/search", response_model=DiscoverySearchResponse)
async def search_companies(
    request: DiscoverySearchRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        response = await discovery_service.run_discovery(db=db, request=request)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(re),
        )
    except Exception as e:
        logger.exception("Unexpected error during discovery search: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during company discovery.",
        ) from e


@router.get("/history", response_model=list[SearchRunResponse])
async def get_search_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SearchRun).order_by(desc(SearchRun.created_at)).limit(limit)
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [
        SearchRunResponse(
            id=r.id,
            query=r.query,
            filters_json=r.filters_json,
            candidate_count=r.candidate_count,
            provider=r.provider,
            status=r.status,
            duration_ms=r.duration_ms,
            created_at=r.created_at.isoformat(),
        )
        for r in runs
    ]
