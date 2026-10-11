import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.company import Company
from app.models.saved_lead import SavedLead
from app.schemas.company import CompanyResponse
from app.schemas.saved_lead import (
    SavedLeadCreate,
    SavedLeadResponse,
    SavedLeadUpdate,
)


def sanitize_csv_field(val: str | None) -> str:
    """Protects against spreadsheet formula injection (=, +, -, @, \t, \r)."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


router = APIRouter(prefix="/saved-leads", tags=["Saved Leads"])


@router.get("", response_model=list[SavedLeadResponse])
async def list_saved_leads(
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SavedLead)
        .options(
            selectinload(SavedLead.company).selectinload(Company.evidence),
            selectinload(SavedLead.company).selectinload(Company.signals),
        )
        .order_by(SavedLead.created_at.desc())
    )
    res = await db.execute(stmt)
    leads = res.scalars().all()

    response_items = []
    for lead in leads:
        company_dto = None
        if lead.company:
            v_count = sum(1 for e in lead.company.evidence if e.verification_status == "verified")
            company_dto = CompanyResponse(
                id=lead.company.id,
                domain=lead.company.domain,
                name=lead.company.name,
                industry=lead.company.industry,
                country=lead.company.country,
                region=lead.company.region,
                city=lead.company.city,
                employee_range=lead.company.employee_range,
                description=lead.company.description,
                website_url=lead.company.website_url,
                created_at=lead.company.created_at,
                updated_at=lead.company.updated_at,
                verified_evidence_count=v_count,
                total_evidence_count=len(lead.company.evidence),
                lead_score=None,
                score_tier=None,
                is_saved=True,
            )
        response_items.append(
            SavedLeadResponse(
                id=lead.id,
                company_id=lead.company_id,
                status=lead.status,
                notes=lead.notes,
                created_at=lead.created_at,
                updated_at=lead.updated_at,
                company=company_dto,
            )
        )
    return response_items


@router.post("", response_model=SavedLeadResponse)
async def save_lead(
    data: SavedLeadCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify company exists
    comp_stmt = (
        select(Company)
        .where(Company.id == data.company_id)
        .options(
            selectinload(Company.evidence),
            selectinload(Company.signals),
        )
    )
    comp_res = await db.execute(comp_stmt)
    company = comp_res.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID '{data.company_id}' not found.",
        )

    # Check if already saved
    existing_stmt = select(SavedLead).where(SavedLead.company_id == data.company_id)
    existing_res = await db.execute(existing_stmt)
    lead = existing_res.scalar_one_or_none()

    if lead:
        # Update existing
        lead.notes = data.notes or lead.notes
        lead.status = data.status or lead.status
    else:
        lead = SavedLead(
            company_id=data.company_id,
            status=data.status,
            notes=data.notes,
        )
        db.add(lead)

    await db.commit()
    await db.refresh(lead)

    v_count = sum(1 for e in company.evidence if e.verification_status == "verified")
    company_dto = CompanyResponse(
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
        verified_evidence_count=v_count,
        total_evidence_count=len(company.evidence),
        lead_score=None,
        score_tier=None,
        is_saved=True,
    )

    return SavedLeadResponse(
        id=lead.id,
        company_id=lead.company_id,
        status=lead.status,
        notes=lead.notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        company=company_dto,
    )


@router.patch("/{saved_lead_id}", response_model=SavedLeadResponse)
async def update_saved_lead(
    saved_lead_id: str,
    data: SavedLeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SavedLead)
        .where(SavedLead.id == saved_lead_id)
        .options(
            selectinload(SavedLead.company).selectinload(Company.evidence),
            selectinload(SavedLead.company).selectinload(Company.signals),
        )
    )
    res = await db.execute(stmt)
    lead = res.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved lead with ID '{saved_lead_id}' not found.",
        )

    if data.status is not None:
        lead.status = data.status
    if data.notes is not None:
        lead.notes = data.notes

    await db.commit()
    await db.refresh(lead)

    company_dto = None
    if lead.company:
        v_count = sum(1 for e in lead.company.evidence if e.verification_status == "verified")
        company_dto = CompanyResponse(
            id=lead.company.id,
            domain=lead.company.domain,
            name=lead.company.name,
            industry=lead.company.industry,
            country=lead.company.country,
            region=lead.company.region,
            city=lead.company.city,
            employee_range=lead.company.employee_range,
            description=lead.company.description,
            website_url=lead.company.website_url,
            created_at=lead.company.created_at,
            updated_at=lead.company.updated_at,
            verified_evidence_count=v_count,
            total_evidence_count=len(lead.company.evidence),
            lead_score=None,
            score_tier=None,
            is_saved=True,
        )

    return SavedLeadResponse(
        id=lead.id,
        company_id=lead.company_id,
        status=lead.status,
        notes=lead.notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        company=company_dto,
    )


@router.delete("/{saved_lead_id}")
async def remove_saved_lead(
    saved_lead_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SavedLead).where(SavedLead.id == saved_lead_id)
    res = await db.execute(stmt)
    lead = res.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved lead with ID '{saved_lead_id}' not found.",
        )

    await db.delete(lead)
    await db.commit()
    return {"success": True, "message": "Lead removed from saved list."}


@router.get("/export")
async def export_saved_leads_csv(
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SavedLead)
        .options(
            selectinload(SavedLead.company).selectinload(Company.evidence),
            selectinload(SavedLead.company).selectinload(Company.signals),
        )
        .order_by(SavedLead.created_at.desc())
    )
    res = await db.execute(stmt)
    leads = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Headers
    writer.writerow(
        [
            "Lead ID",
            "Company Name",
            "Domain",
            "Industry",
            "Location",
            "Employee Range",
            "Lead Status",
            "Verified Evidence Count",
            "Primary Source URL",
            "User Notes",
            "Saved At",
        ]
    )

    for lead in leads:
        comp = lead.company
        if not comp:
            continue

        verified_ev = [e for e in comp.evidence if e.verification_status == "verified"]
        primary_url = verified_ev[0].source_url if verified_ev else (comp.website_url or "")

        writer.writerow(
            [
                sanitize_csv_field(lead.id),
                sanitize_csv_field(comp.name),
                sanitize_csv_field(comp.domain),
                sanitize_csv_field(comp.industry),
                sanitize_csv_field(comp.city or comp.country),
                sanitize_csv_field(comp.employee_range),
                sanitize_csv_field(lead.status),
                str(len(verified_ev)),
                sanitize_csv_field(primary_url),
                sanitize_csv_field(lead.notes),
                lead.created_at.isoformat(),
            ]
        )

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leados_saved_leads.csv"},
    )
