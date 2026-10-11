from app.models.company import Company
from app.models.evidence import Evidence
from app.models.signal import BusinessSignal
from app.services.scoring_service import ScoringService


def test_scoring_determinism():
    scoring = ScoringService()

    company = Company(
        id="c-1",
        domain="databox.com",
        name="Databox",
        industry="SaaS",
        country="United States",
        employee_range="50-100",
        description="Analytics and dashboarding SaaS platform",
    )

    ev1 = Evidence(
        id="e-1",
        company_id="c-1",
        claim_type="hiring",
        claim_value="Hiring 10 backend engineers",
        source_url="https://databox.com/careers",
        source_name="Careers",
        source_category="official_website",
        verification_status="verified",
    )

    sig1 = BusinessSignal(
        id="s-1",
        company_id="c-1",
        evidence_id="e-1",
        signal_type="hiring_expansion",
        confidence_score=0.9,
        summary="Rapid engineering hiring",
    )

    criteria = {
        "industry": "SaaS",
        "geography": "United States",
        "employee_range": "50-100",
    }

    # Run multiple times to verify strict mathematical determinism
    res1 = scoring.calculate_lead_score(company, [ev1], [sig1], criteria)
    res2 = scoring.calculate_lead_score(company, [ev1], [sig1], criteria)
    res3 = scoring.calculate_lead_score(company, [ev1], [sig1], criteria)

    assert res1.total_score == res2.total_score == res3.total_score
    assert res1.score_tier == "high"
    assert res1.total_score == 100  # Max score because all criteria and verified signals matched!
    assert "Verified signal: hiring_expansion" in res1.matched_criteria


def test_scoring_unverified_signal_penalty():
    scoring = ScoringService()

    company = Company(
        id="c-2",
        domain="unknown.io",
        name="Unknown Corp",
        industry="Retail",
        country="Germany",
    )

    # Evidence is unverified
    ev = Evidence(
        id="e-2",
        company_id="c-2",
        claim_type="hiring",
        claim_value="Alleged hiring",
        source_url="https://unknown.io",
        source_name="Homepage",
        verification_status="unverified",
    )

    sig = BusinessSignal(
        id="s-2",
        company_id="c-2",
        evidence_id="e-2",
        signal_type="hiring_expansion",
        summary="Unverified hiring claim",
    )

    criteria = {"industry": "Fintech", "geography": "United States"}
    res = scoring.calculate_lead_score(company, [ev], [sig], criteria)

    # Must be low score because signal is unverified and filters did not match
    assert res.total_score < 40
    assert res.score_tier == "low"
    assert "Active verified buying signal or growth trigger" in res.missing_evidence


def test_scoring_boundary_clamps():
    scoring = ScoringService()
    empty_company = Company(id="c-3", domain="empty.com", name="Empty")

    res = scoring.calculate_lead_score(empty_company, [], [], {})
    assert 0 <= res.total_score <= 100
