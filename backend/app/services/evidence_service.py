from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence
from app.providers.source_retrieval import source_retriever
from app.schemas.evidence import VerificationStatus
from app.validators.evidence_validator import validate_claim_against_source


class EvidenceService:
    async def verify_and_record_claim(
        self,
        db: AsyncSession,
        company_id: str,
        claim_type: str,
        claim_value: str,
        source_url: str,
        source_name: str = "Primary Website",
        source_category: str = "official_website",
    ) -> Evidence:
        """
        Retrieves live source text from the source URL safely and evaluates
        the claim against the retrieved text.
        """
        # Fetch live source text safely
        retrieved = await source_retriever.fetch_source_content(source_url)

        if not retrieved.is_successful:
            status: VerificationStatus = "unknown"
            excerpt = None
            notes = retrieved.error_reason or "Source retrieval failed."
        else:
            status, excerpt, notes = validate_claim_against_source(
                claim_value=claim_value,
                claim_type=claim_type,
                source_text=retrieved.text_content,
            )

        evidence = Evidence(
            company_id=company_id,
            claim_type=claim_type,
            claim_value=claim_value,
            source_url=retrieved.final_url or source_url,
            source_name=retrieved.title or source_name,
            source_category=source_category,
            source_excerpt=excerpt,
            retrieval_timestamp=datetime.now(UTC),
            verification_status=status,
            validation_notes=notes,
        )

        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        return evidence


evidence_service = EvidenceService()
