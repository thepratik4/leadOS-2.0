from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.schemas.dossier import (
    CompanyDossierResponse,
    FactStatement,
    InferenceStatement,
)
from app.schemas.evidence import EvidenceResponse


class DossierService:
    async def generate_dossier(self, db: AsyncSession, company_id: str) -> CompanyDossierResponse:
        stmt = (
            select(Company)
            .where(Company.id == company_id)
            .options(
                selectinload(Company.evidence),
                selectinload(Company.signals),
            )
        )
        res = await db.execute(stmt)
        company = res.scalar_one_or_none()

        if not company:
            raise ValueError(f"Company with ID '{company_id}' not found.")

        verified_facts: list[FactStatement] = []
        unverified_claims: list[FactStatement] = []
        inferences: list[InferenceStatement] = []
        recommendations: list[str] = []

        verified_evidence = [e for e in company.evidence if e.verification_status == "verified"]
        partially_verified = [
            e for e in company.evidence if e.verification_status == "partially_verified"
        ]
        unverified_or_unknown = [
            e for e in company.evidence if e.verification_status in ("unverified", "unknown")
        ]

        # 1. Verified facts
        for ev in verified_evidence:
            verified_facts.append(
                FactStatement(
                    statement=f"{ev.claim_type.capitalize()}: {ev.claim_value}",
                    evidence_id=ev.id,
                    source_url=ev.source_url,
                    source_name=ev.source_name,
                    verification_status=ev.verification_status,
                )
            )

        # 2. Partially verified / Unverified
        for ev in partially_verified:
            unverified_claims.append(
                FactStatement(
                    statement=f"[Partially Verified] {ev.claim_type.capitalize()}: {ev.claim_value}",
                    evidence_id=ev.id,
                    source_url=ev.source_url,
                    source_name=ev.source_name,
                    verification_status=ev.verification_status,
                )
            )
        for ev in unverified_or_unknown:
            unverified_claims.append(
                FactStatement(
                    statement=f"[Unverified] {ev.claim_type.capitalize()}: {ev.claim_value}",
                    evidence_id=ev.id,
                    source_url=ev.source_url,
                    source_name=ev.source_name,
                    verification_status=ev.verification_status,
                )
            )

        # 3. Grounded Inferences (derived ONLY from verified facts)
        hiring_ev = [e for e in verified_evidence if e.claim_type == "hiring"]
        if hiring_ev:
            inferences.append(
                InferenceStatement(
                    inference=f"{company.name} is actively scaling operations and investing in human capital.",
                    based_on_evidence_ids=[e.id for e in hiring_ev],
                    confidence="high",
                    reasoning=f"Corroborated by active recruitment notices on official domain: '{hiring_ev[0].claim_value}'.",
                )
            )
            recommendations.append(
                "Engage decision-makers regarding headcount growth and team tooling needs."
            )

        tech_ev = [e for e in verified_evidence if e.claim_type == "tech_stack"]
        if tech_ev:
            inferences.append(
                InferenceStatement(
                    inference=f"{company.name} utilizes modern API and software infrastructure.",
                    based_on_evidence_ids=[e.id for e in tech_ev],
                    confidence="high",
                    reasoning=f"Verified technology stack: '{tech_ev[0].claim_value}'.",
                )
            )
            recommendations.append(
                f"Reference compatibility with their current tech ecosystem ({tech_ev[0].claim_value[:40]})."
            )

        if not recommendations:
            if verified_evidence:
                recommendations.append(
                    f"Perform initial introductory inquiry based on primary offering: '{verified_evidence[0].claim_value[:60]}'."
                )
            else:
                recommendations.append(
                    "Perform additional primary source investigation before initiating cold outreach."
                )

        total_ev = len(company.evidence)
        v_count = len(verified_evidence)
        data_quality_summary = (
            f"{v_count} of {total_ev} claims verified against primary sources "
            f"({len(unverified_claims)} unverified or unknown)."
        )

        return CompanyDossierResponse(
            company_id=company.id,
            company_name=company.name,
            domain=company.domain,
            verified_facts=verified_facts,
            unverified_claims=unverified_claims,
            inferences=inferences,
            recommendations=recommendations,
            data_quality_summary=data_quality_summary,
            evidence_items=[EvidenceResponse.model_validate(e) for e in company.evidence],
        )


dossier_service = DossierService()
