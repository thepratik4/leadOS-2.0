from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.models.company import Company
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceResponse, VerifyClaimRequest
from app.services.evidence_service import evidence_service

router = APIRouter(prefix="/companies/{company_id}/evidence", tags=["Evidence"])


@router.get("", response_model=list[EvidenceResponse])
async def list_company_evidence(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt_comp = select(Company).where(Company.id == company_id)
    comp_res = await db.execute(stmt_comp)
    if not comp_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found.",
        )

    stmt = (
        select(Evidence)
        .where(Evidence.company_id == company_id)
        .order_by(Evidence.retrieval_timestamp.desc())
    )
    res = await db.execute(stmt)
    evidence_items = res.scalars().all()
    return [EvidenceResponse.model_validate(e) for e in evidence_items]


@router.post("/verify", response_model=EvidenceResponse)
async def verify_new_claim(
    company_id: str,
    request: VerifyClaimRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt_comp = select(Company).where(Company.id == company_id)
    comp_res = await db.execute(stmt_comp)
    company = comp_res.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found.",
        )

    # Check for existing duplicate verification request for this company and source
    stmt_existing = (
        select(Evidence)
        .where(
            Evidence.company_id == company_id,
            Evidence.claim_type == request.claim_type,
            Evidence.claim_value == request.claim_value,
            Evidence.source_url == request.source_url,
        )
        .order_by(Evidence.retrieval_timestamp.desc())
        .limit(1)
    )
    existing_res = await db.execute(stmt_existing)
    existing_evidence = existing_res.scalar_one_or_none()
    if existing_evidence:
        return EvidenceResponse.model_validate(existing_evidence)

    try:
        ev = await evidence_service.verify_and_record_claim(
            db=db,
            company_id=company_id,
            claim_type=request.claim_type,
            claim_value=request.claim_value,
            source_url=request.source_url,
        )
        return EvidenceResponse.model_validate(ev)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.exception("Unexpected error verifying claim for company %s: %s", company_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify claim against source.",
        ) from e
