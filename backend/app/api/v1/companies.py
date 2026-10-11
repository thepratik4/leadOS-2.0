from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyDetailResponse, SignalResponse
from app.schemas.evidence import EvidenceResponse
from app.services.scoring_service import scoring_service

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company_details(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Company)
        .where(Company.id == company_id)
        .options(
            selectinload(Company.evidence),
            selectinload(Company.signals),
            selectinload(Company.saved_lead),
        )
    )
    res = await db.execute(stmt)
    company = res.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{company_id}' not found.",
        )

    # Score calculation
    score_res = scoring_service.calculate_lead_score(
        company=company,
        evidence_list=company.evidence,
        signals=company.signals,
        criteria={"industry": company.industry, "geography": company.country},
    )

    verified_count = sum(1 for e in company.evidence if e.verification_status == "verified")

    return CompanyDetailResponse(
        id=company.id,
        domain=company.domain,
        name=company.name,
        industry=company.industry,
        country=company.country,
        region=company.region,
        city=company.city,
        employee_range=company.employee_range,
        description=company.description,
        website_url=company.website_url,
        created_at=company.created_at,
        updated_at=company.updated_at,
        verified_evidence_count=verified_count,
        total_evidence_count=len(company.evidence),
        lead_score=score_res.total_score,
        score_tier=score_res.score_tier,
        is_saved=company.saved_lead is not None,
        evidence=[EvidenceResponse.model_validate(e) for e in company.evidence],
        signals=[SignalResponse.model_validate(s) for s in company.signals],
        score_result=score_res,
    )
