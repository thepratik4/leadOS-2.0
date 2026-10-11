from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.outreach import OutreachDraftRequest, OutreachDraftResponse
from app.services.outreach_service import outreach_service

router = APIRouter(prefix="/companies/{company_id}/outreach", tags=["Outreach"])


@router.post("", response_model=OutreachDraftResponse)
async def draft_evidence_grounded_outreach(
    company_id: str,
    request: OutreachDraftRequest = OutreachDraftRequest(),
    db: AsyncSession = Depends(get_db),
):
    try:
        draft = await outreach_service.generate_grounded_outreach(
            db=db,
            company_id=company_id,
            request=request,
        )
        return draft
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outreach generation error: {e!s}",
        )
