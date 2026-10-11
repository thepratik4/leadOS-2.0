from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.evidence import Evidence
from app.schemas.outreach import OutreachDraftRequest, OutreachDraftResponse


class OutreachService:
    async def generate_grounded_outreach(
        self, db: AsyncSession, company_id: str, request: OutreachDraftRequest
    ) -> OutreachDraftResponse:
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

        # Check for verified business triggers
        verified_evidence = [e for e in company.evidence if e.verification_status == "verified"]

        # Find verified trigger (hiring or tech stack or offering)
        hiring_trigger = next((e for e in verified_evidence if e.claim_type == "hiring"), None)
        tech_trigger = next((e for e in verified_evidence if e.claim_type == "tech_stack"), None)
        offering_trigger = next((e for e in verified_evidence if e.claim_type == "offering"), None)

        best_trigger: Evidence | None = hiring_trigger or tech_trigger or offering_trigger

        # If no verified trigger exists, return structured insufficient evidence response
        if not best_trigger:
            return OutreachDraftResponse(
                company_id=company.id,
                company_name=company.name,
                has_sufficient_evidence=False,
                status_reason=(
                    f"Insufficient verified evidence for {company.name}. "
                    "LeadOS strictly requires at least one primary source-verified trigger "
                    "before drafting outreach to prevent hallucinated or ungrounded claims."
                ),
                trigger_summary=None,
                supporting_evidence_id=None,
                supporting_source_url=None,
                subject_line=None,
                body_text=None,
                facts_referenced=[],
            )

        # Generate strictly evidence-grounded template
        facts_referenced = [
            f"Verified claim ({best_trigger.claim_type}): {best_trigger.claim_value}",
            f"Source URL: {best_trigger.source_url}",
        ]

        if best_trigger.claim_type == "hiring":
            subject = f"Question regarding growth at {company.name}"
            body = (
                f"Hi team,\n\n"
                f"I noticed on {company.name}'s official site ({best_trigger.source_name}) "
                f'that you are actively expanding: "{best_trigger.claim_value}".\n\n'
                f"As your team scales, managing workflow efficiency becomes essential. "
                f"Are you open to a brief conversation on how we assist organizations navigating this growth phase?\n\n"
                f"Best regards,\n[Your Name]"
            )
        elif best_trigger.claim_type == "tech_stack":
            subject = f"Infrastructure inquiry for {company.name}"
            body = (
                f"Hi team,\n\n"
                f"I was reviewing {company.name}'s platform documentation and noted your emphasis on: "
                f'"{best_trigger.claim_value}".\n\n'
                f"We specialize in integrations that enhance this technical architecture. "
                f"Would you be open to exploring whether our solution complements your stack?\n\n"
                f"Best regards,\n[Your Name]"
            )
        else:
            subject = f"Connecting regarding {company.name}"
            body = (
                f"Hi team,\n\n"
                f'I came across {company.name}\'s platform: "{best_trigger.claim_value}".\n\n'
                f"Given your focus in this space, I'd appreciate the opportunity to learn more about your priority initiatives "
                f"this quarter.\n\n"
                f"Best regards,\n[Your Name]"
            )

        return OutreachDraftResponse(
            company_id=company.id,
            company_name=company.name,
            has_sufficient_evidence=True,
            status_reason="Draft generated successfully from primary source-verified trigger.",
            trigger_summary=best_trigger.claim_value,
            supporting_evidence_id=best_trigger.id,
            supporting_source_url=best_trigger.source_url,
            subject_line=subject,
            body_text=body,
            facts_referenced=facts_referenced,
        )


outreach_service = OutreachService()
