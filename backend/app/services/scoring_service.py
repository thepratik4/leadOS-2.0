from typing import Any

from app.models.company import Company
from app.models.evidence import Evidence
from app.models.signal import BusinessSignal
from app.schemas.scoring import LeadScoreResult, ScoreBreakdownItem


class ScoringConfig:
    MAX_TRIGGER_POINTS: float = 30.0
    MAX_INDUSTRY_POINTS: float = 25.0
    MAX_GEO_POINTS: float = 20.0
    MAX_SIZE_POINTS: float = 15.0
    MAX_EVIDENCE_QUALITY_POINTS: float = 10.0


class ScoringService:
    def __init__(self, config: ScoringConfig | None = None):
        self.config = config or ScoringConfig()

    def calculate_lead_score(
        self,
        company: Company,
        evidence_list: list[Evidence],
        signals: list[BusinessSignal],
        criteria: dict[str, Any],
    ) -> LeadScoreResult:
        """
        Pure deterministic scoring function.
        Does NOT rely on LLM outputs or random numbers.
        """
        breakdown: list[ScoreBreakdownItem] = []
        matched_criteria: list[str] = []
        missing_evidence: list[str] = []

        # 1. Verified Business Trigger (Max 30)
        trigger_points = 0.0
        trigger_matched = False
        trigger_explanation = "No verified business trigger found."
        evidence_id_for_trigger = None

        verified_evidence_map = {
            e.id: e for e in evidence_list if e.verification_status == "verified"
        }
        partial_evidence_map = {
            e.id: e for e in evidence_list if e.verification_status == "partially_verified"
        }

        # Look for signal backed by verified evidence
        for sig in signals:
            if sig.evidence_id and sig.evidence_id in verified_evidence_map:
                ev = verified_evidence_map[sig.evidence_id]
                trigger_points = self.config.MAX_TRIGGER_POINTS
                trigger_matched = True
                trigger_explanation = (
                    f"Verified trigger: {sig.summary} substantiated by {ev.source_name}."
                )
                evidence_id_for_trigger = ev.id
                matched_criteria.append(f"Verified signal: {sig.signal_type}")
                break
            elif sig.evidence_id and sig.evidence_id in partial_evidence_map:
                ev = partial_evidence_map[sig.evidence_id]
                # Partial trigger gets half points
                trigger_points = max(trigger_points, self.config.MAX_TRIGGER_POINTS * 0.5)
                trigger_matched = True
                trigger_explanation = (
                    f"Partially verified trigger: {sig.summary} supported by excerpt."
                )
                evidence_id_for_trigger = ev.id
                matched_criteria.append(f"Partially verified signal: {sig.signal_type}")

        if not trigger_matched:
            missing_evidence.append("Active verified buying signal or growth trigger")

        breakdown.append(
            ScoreBreakdownItem(
                category="verified_trigger",
                awarded_points=round(trigger_points, 1),
                max_points=self.config.MAX_TRIGGER_POINTS,
                matched=trigger_matched,
                explanation=trigger_explanation,
                evidence_id=evidence_id_for_trigger,
            )
        )

        # 2. Industry Fit (Max 25)
        target_industry = criteria.get("industry")
        industry_points = 0.0
        industry_matched = False
        industry_explanation = "Industry does not match criteria."

        if target_industry:
            target_ind_lower = target_industry.lower()
            comp_ind = (company.industry or "").lower()
            comp_desc = (company.description or "").lower()

            if target_ind_lower in comp_ind:
                industry_points = self.config.MAX_INDUSTRY_POINTS
                industry_matched = True
                industry_explanation = f"Direct industry match for '{target_industry}'."
                matched_criteria.append(f"Industry: {company.industry}")
            elif target_ind_lower in comp_desc:
                industry_points = self.config.MAX_INDUSTRY_POINTS * 0.65
                industry_matched = True
                industry_explanation = (
                    f"Industry keywords '{target_industry}' found in company offering description."
                )
                matched_criteria.append(f"Industry keyword in description: {target_industry}")
            else:
                missing_evidence.append(
                    f"Confirmation of '{target_industry}' industry classification"
                )
        else:
            # If user didn't specify industry, give baseline for established offering
            has_offering = any(e.claim_type == "offering" for e in evidence_list)
            if has_offering:
                industry_points = 18.0
                industry_matched = True
                industry_explanation = (
                    "No industry filter set; company has verified core business offering."
                )
            else:
                industry_points = 10.0
                industry_explanation = "No industry filter specified; baseline assigned."

        breakdown.append(
            ScoreBreakdownItem(
                category="industry_fit",
                awarded_points=round(industry_points, 1),
                max_points=self.config.MAX_INDUSTRY_POINTS,
                matched=industry_matched,
                explanation=industry_explanation,
            )
        )

        # 3. Geographic Fit (Max 20)
        target_geo = criteria.get("geography")
        geo_points = 0.0
        geo_matched = False
        geo_explanation = "Geographic criteria not matched or unknown."

        if target_geo:
            t_geo = target_geo.lower()
            c_country = (company.country or "").lower()
            c_region = (company.region or "").lower()
            c_city = (company.city or "").lower()

            if t_geo in c_country or t_geo in c_region or t_geo in c_city:
                geo_points = self.config.MAX_GEO_POINTS
                geo_matched = True
                geo_explanation = f"Headquarters verified in target geography '{target_geo}'."
                matched_criteria.append(f"Geography: {target_geo}")
            else:
                missing_evidence.append(f"Headquarters location in '{target_geo}'")
        else:
            if company.country or company.city:
                geo_points = 15.0
                geo_matched = True
                geo_explanation = (
                    f"No geography filter set; known location: {company.city or company.country}."
                )
            else:
                geo_points = 8.0
                geo_explanation = "Location not explicitly verified; baseline points awarded."

        breakdown.append(
            ScoreBreakdownItem(
                category="geo_fit",
                awarded_points=round(geo_points, 1),
                max_points=self.config.MAX_GEO_POINTS,
                matched=geo_matched,
                explanation=geo_explanation,
            )
        )

        # 4. Company Size Fit (Max 15)
        target_size = criteria.get("employee_range")
        size_points = 0.0
        size_matched = False
        size_explanation = "Employee headcount unknown or unverified."

        if target_size:
            if company.employee_range and target_size.lower() in company.employee_range.lower():
                size_points = self.config.MAX_SIZE_POINTS
                size_matched = True
                size_explanation = f"Company size verified in range '{target_size}'."
                matched_criteria.append(f"Size: {company.employee_range}")
            else:
                missing_evidence.append(f"Verified headcount in range '{target_size}'")
        else:
            if company.employee_range:
                size_points = 12.0
                size_matched = True
                size_explanation = (
                    f"No size filter set; known employee headcount range: {company.employee_range}."
                )
            else:
                size_points = 6.0
                size_explanation = "Headcount unconfirmed; baseline awarded."

        breakdown.append(
            ScoreBreakdownItem(
                category="company_size",
                awarded_points=round(size_points, 1),
                max_points=self.config.MAX_SIZE_POINTS,
                matched=size_matched,
                explanation=size_explanation,
            )
        )

        # 5. Evidence Quality and Freshness (Max 10)
        total_evidence_count = len(evidence_list)
        verified_count = len(verified_evidence_map)
        partial_count = len(partial_evidence_map)

        if total_evidence_count == 0:
            evidence_quality_points = 0.0
            evidence_explanation = "Zero evidence records retrieved; data quality is unverified."
            data_quality_score = 10
            missing_evidence.append("Primary source website retrieval")
        else:
            verification_ratio = (verified_count + (0.5 * partial_count)) / total_evidence_count
            evidence_quality_points = self.config.MAX_EVIDENCE_QUALITY_POINTS * verification_ratio
            data_quality_score = int(min(100, max(20, verification_ratio * 100)))
            evidence_explanation = (
                f"{verified_count} verified and {partial_count} partially verified "
                f"out of {total_evidence_count} evidence records."
            )

        breakdown.append(
            ScoreBreakdownItem(
                category="evidence_quality",
                awarded_points=round(evidence_quality_points, 1),
                max_points=self.config.MAX_EVIDENCE_QUALITY_POINTS,
                matched=verified_count > 0,
                explanation=evidence_explanation,
            )
        )

        raw_total = sum(item.awarded_points for item in breakdown)
        total_score = int(round(min(100.0, max(0.0, raw_total))))

        if total_score >= 70:
            score_tier = "high"
        elif total_score >= 40:
            score_tier = "medium"
        else:
            score_tier = "low"

        scoring_notes = (
            f"Deterministic score: {total_score}/100. "
            f"Based on {len(matched_criteria)} matched criteria, {len(missing_evidence)} missing data points, "
            f"and {verified_count} verified sources."
        )

        return LeadScoreResult(
            total_score=total_score,
            score_tier=score_tier,
            breakdown=breakdown,
            matched_criteria=matched_criteria,
            missing_evidence=missing_evidence,
            data_quality_score=data_quality_score,
            scoring_notes=scoring_notes,
        )


scoring_service = ScoringService()
