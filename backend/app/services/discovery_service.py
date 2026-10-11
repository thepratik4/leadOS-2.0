import json
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.evidence import Evidence
from app.models.search_run import SearchRun
from app.models.signal import BusinessSignal
from app.providers.llm_extractor import claim_extractor
from app.providers.search_provider import get_search_provider
from app.providers.source_retrieval import source_retriever
from app.schemas.company import CompanyResponse, SignalResponse
from app.schemas.discovery import (
    DiscoveryCandidateItem,
    DiscoverySearchRequest,
    DiscoverySearchResponse,
)
from app.schemas.evidence import EvidenceResponse
from app.services.scoring_service import scoring_service
from app.validators.evidence_validator import validate_claim_against_source
from app.validators.url_normalizer import normalize_domain


class DiscoveryService:
    async def run_discovery(
        self, db: AsyncSession, request: DiscoverySearchRequest
    ) -> DiscoverySearchResponse:
        start_time = time.time()
        provider = get_search_provider()
        health = provider.get_health()

        # Record search run
        search_run = SearchRun(
            query=request.query,
            filters_json=json.dumps(
                {
                    "industry": request.industry,
                    "geography": request.geography,
                    "employee_range": request.employee_range,
                    "buying_signal": request.buying_signal,
                }
            ),
            candidate_count=0,
            provider=health.provider_name,
            status="pending",
        )
        db.add(search_run)
        await db.commit()
        await db.refresh(search_run)

        try:
            raw_candidates = await provider.search(
                query=request.query,
                industry=request.industry,
                geography=request.geography,
                employee_range=request.employee_range,
                buying_signal=request.buying_signal,
                limit=request.limit,
            )
        except Exception as search_err:
            duration_ms = int((time.time() - start_time) * 1000)
            search_run.status = "failed"
            search_run.error_message = str(search_err)
            search_run.duration_ms = duration_ms
            await db.commit()
            raise RuntimeError(f"Discovery search failed: {search_err!s}")

        candidate_items: list[DiscoveryCandidateItem] = []

        # Process candidates concurrently with bounds
        for raw in raw_candidates:
            domain = raw.domain or normalize_domain(raw.url)
            if not domain:
                continue

            # Check if company exists by domain
            stmt = select(Company).where(Company.domain == domain)
            result = await db.execute(stmt)
            company = result.scalar_one_or_none()

            # Clean name from title (e.g. "Stripe: Financial Infrastructure" -> "Stripe")
            raw_name = raw.title.split("|")[0].split("-")[0].split(":")[0].strip()
            clean_name = raw_name if len(raw_name) > 1 else domain.capitalize()

            if not company:
                company = Company(
                    domain=domain,
                    name=clean_name,
                    industry=request.industry,
                    country=request.geography,
                    employee_range=request.employee_range,
                    description=raw.snippet[:500] if raw.snippet else None,
                    website_url=raw.url,
                )
                db.add(company)
                await db.flush()
                await db.refresh(company)
            else:
                # Update attributes if they were missing
                if not company.industry and request.industry:
                    company.industry = request.industry
                if not company.country and request.geography:
                    company.country = request.geography
                if not company.description and raw.snippet:
                    company.description = raw.snippet[:500]

            # Evidence collection & verification
            if request.verify_sources:
                # 1. First record the search engine candidate source as initial evidence
                search_evidence = Evidence(
                    company_id=company.id,
                    claim_type="search_discovery",
                    claim_value=f"Company discovered via search query '{request.query}' with snippet: '{raw.snippet[:200]}'",
                    source_url=raw.url,
                    source_name=f"{health.provider_name} Result",
                    source_category="search_index",
                    source_excerpt=raw.snippet[:300] if raw.snippet else None,
                    retrieval_timestamp=datetime.now(UTC),
                    verification_status="partially_verified",
                    validation_notes="Candidate indexed by public web search provider.",
                )
                db.add(search_evidence)
                await db.flush()

                # 2. Fetch primary website source content safely
                retrieved = await source_retriever.fetch_source_content(raw.url)

                if retrieved.is_successful:
                    # Extract claims from retrieved content
                    extracted_claims = await claim_extractor.extract_candidate_claims(
                        company_name=company.name,
                        domain=company.domain,
                        source_url=raw.url,
                        source_text=retrieved.text_content,
                    )

                    for claim_cand in extracted_claims:
                        status, excerpt, notes = validate_claim_against_source(
                            claim_value=claim_cand.claim_value,
                            claim_type=claim_cand.claim_type,
                            source_text=retrieved.text_content,
                        )

                        ev = Evidence(
                            company_id=company.id,
                            claim_type=claim_cand.claim_type,
                            claim_value=claim_cand.claim_value,
                            source_url=retrieved.final_url,
                            source_name=retrieved.title or claim_cand.source_name,
                            source_category="official_website",
                            source_excerpt=excerpt or claim_cand.approximate_quote,
                            retrieval_timestamp=retrieved.retrieval_timestamp,
                            verification_status=status,
                            validation_notes=notes,
                        )
                        db.add(ev)
                        await db.flush()

                        # If this claim is hiring or tech stack, register a business signal
                        if claim_cand.claim_type == "hiring" and status in (
                            "verified",
                            "partially_verified",
                        ):
                            sig = BusinessSignal(
                                company_id=company.id,
                                evidence_id=ev.id,
                                signal_type="hiring_expansion",
                                confidence_score=0.9 if status == "verified" else 0.6,
                                summary=f"Active hiring verified on website: {claim_cand.claim_value}",
                            )
                            db.add(sig)
                        elif claim_cand.claim_type == "tech_stack" and status in (
                            "verified",
                            "partially_verified",
                        ):
                            sig = BusinessSignal(
                                company_id=company.id,
                                evidence_id=ev.id,
                                signal_type="tech_adoption",
                                confidence_score=0.85 if status == "verified" else 0.5,
                                summary=f"Tech infrastructure verified: {claim_cand.claim_value}",
                            )
                            db.add(sig)

                else:
                    # Record that primary website could not be retrieved
                    ev_failed = Evidence(
                        company_id=company.id,
                        claim_type="official_domain_access",
                        claim_value="Attempted to retrieve official domain",
                        source_url=raw.url,
                        source_name="Website Fetch",
                        source_category="official_website",
                        source_excerpt=None,
                        retrieval_timestamp=retrieved.retrieval_timestamp,
                        verification_status="unknown",
                        validation_notes=retrieved.error_reason or "Website unreachable.",
                    )
                    db.add(ev_failed)
                    await db.flush()

            # Refresh company with all evidence and signals
            stmt_full = (
                select(Company)
                .where(Company.id == company.id)
                .options(
                    selectinload(Company.evidence),
                    selectinload(Company.signals),
                    selectinload(Company.saved_lead),
                )
            )
            full_res = await db.execute(stmt_full)
            full_company = full_res.scalar_one()

            # Compute deterministic lead score
            criteria_dict = {
                "industry": request.industry,
                "geography": request.geography,
                "employee_range": request.employee_range,
                "buying_signal": request.buying_signal,
            }
            score_res = scoring_service.calculate_lead_score(
                company=full_company,
                evidence_list=full_company.evidence,
                signals=full_company.signals,
                criteria=criteria_dict,
            )

            # Build summary counts
            counts = {
                "verified": sum(
                    1 for e in full_company.evidence if e.verification_status == "verified"
                ),
                "partially_verified": sum(
                    1
                    for e in full_company.evidence
                    if e.verification_status == "partially_verified"
                ),
                "unverified": sum(
                    1 for e in full_company.evidence if e.verification_status == "unverified"
                ),
                "unknown": sum(
                    1 for e in full_company.evidence if e.verification_status == "unknown"
                ),
            }

            company_dto = CompanyResponse(
                id=full_company.id,
                domain=full_company.domain,
                name=full_company.name,
                industry=full_company.industry,
                country=full_company.country,
                region=full_company.region,
                city=full_company.city,
                employee_range=full_company.employee_range,
                description=full_company.description,
                website_url=full_company.website_url,
                created_at=full_company.created_at,
                updated_at=full_company.updated_at,
                verified_evidence_count=counts["verified"],
                total_evidence_count=len(full_company.evidence),
                lead_score=score_res.total_score,
                score_tier=score_res.score_tier,
                is_saved=full_company.saved_lead is not None,
            )

            signals_dto = [SignalResponse.model_validate(s) for s in full_company.signals]
            evidence_dto = [EvidenceResponse.model_validate(e) for e in full_company.evidence]

            candidate_items.append(
                DiscoveryCandidateItem(
                    company=company_dto,
                    signals=signals_dto,
                    evidence=evidence_dto,
                    score=score_res,
                    primary_signal=signals_dto[0].summary if signals_dto else None,
                    verification_summary=counts,
                )
            )

        # Sort candidates deterministically by lead score descending
        candidate_items.sort(key=lambda c: c.score.total_score, reverse=True)

        duration_ms = int((time.time() - start_time) * 1000)
        search_run.candidate_count = len(candidate_items)
        search_run.status = "completed"
        search_run.duration_ms = duration_ms
        await db.commit()

        verified_candidates = sum(
            1 for c in candidate_items if c.verification_summary["verified"] > 0
        )

        return DiscoverySearchResponse(
            search_run_id=search_run.id,
            query=request.query,
            total_candidates=len(candidate_items),
            verified_candidates=verified_candidates,
            provider=health.provider_name,
            duration_ms=duration_ms,
            candidates=candidate_items,
            provider_status="active",
            provider_notice=None if health.is_available else health.message,
        )


discovery_service = DiscoveryService()
