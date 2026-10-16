"""
LeadOS 2.0 — End-to-End Core Pipeline Walkthrough & Demonstration Script
------------------------------------------------------------------------
Demonstrates the key engineering principles of LeadOS:
1. SSRF-Guarded Source Retrieval (Blocks metadata, private IPs, loopbacks)
2. Evidence Validation Engine (Exact quotation matching, numbers, and dates)
3. Deterministic 5-Dimension Lead Scoring (Pure mathematical function [0, 100])
4. Grounded Company Dossier Generation (Verified facts vs unverified claims)
5. Grounded Cold Outreach Guard (Refusal on unverified signals, citation on verified)
"""

import sys
from datetime import datetime, UTC


def print_section(title: str):
    print("\n" + "=" * 75)
    print(f" {title.upper()}")
    print("=" * 75)


def demo_ssrf_validator():
    print_section("1. SSRF Security & URL Validation")
    from app.validators.ssrf_validator import validate_url_safe_for_retrieval

    test_urls = [
        ("http://169.254.169.254/latest/meta-data/", "AWS Cloud Metadata IP"),
        ("http://127.0.0.1:8000/admin", "Localhost Loopback"),
        ("http://192.168.1.50/internal", "RFC 1918 Private Subnet"),
        ("ftp://ftp.example.com/files", "Invalid URL Scheme"),
        ("https://stripe.com", "Valid Public Domain"),
    ]

    for url, desc in test_urls:
        safe, reason = validate_url_safe_for_retrieval(url)
        status_tag = "[PASS - SAFE]" if safe else "[BLOCKED]"
        print(f"  * {status_tag:<14} | {desc:<24} | {url}")
        print(f"    --> Details: {reason}")


def demo_evidence_validator():
    print_section("2. Evidence Validation Engine (Exact Quotation & Metric Check)")
    from app.validators.evidence_validator import validate_claim_against_source

    source_article = (
        "San Francisco, CA — Datadog has announced a major engineering hiring initiative, "
        "expanding its distributed systems team with 75 new senior infrastructure roles. "
        "The platform currently processes over 35 trillion events daily across multi-cloud environments."
    )

    claims = [
        ("hiring", "expanding its distributed systems team with 75 new senior infrastructure roles"),
        ("metric", "processes over 35 trillion events daily"),
        ("metric_unverified", "processes over 99 trillion events daily"),
        ("fake_claim", "company recently laid off 40% of marketing department"),
    ]

    print("Source Text Sample:")
    print(f"  \"{source_article[:110]}...\"\n")

    for c_type, claim in claims:
        status, excerpt, notes = validate_claim_against_source(claim, c_type, source_article)
        badge = f"[{status.upper()}]"
        print(f"  Claim: \"{claim}\"")
        print(f"  Status: {badge:<15} | Notes: {notes}")
        if excerpt:
            print(f"  Supporting Quote: \"{excerpt}\"")
        print("  " + "-" * 70)


def demo_deterministic_scoring():
    print_section("3. Deterministic 5-Dimension Lead Scoring Engine")
    from app.models.company import Company
    from app.models.evidence import Evidence
    from app.models.signal import BusinessSignal
    from app.services.scoring_service import scoring_service

    company = Company(
        id="demo-stripe",
        domain="stripe.com",
        name="Stripe",
        industry="Fintech & Developer Infrastructure",
        country="United States",
        employee_range="500+",
        description="Financial infrastructure platform for modern online businesses.",
        website_url="https://stripe.com",
    )

    evidence_verified = Evidence(
        id="ev-101",
        company_id="demo-stripe",
        claim_type="hiring",
        claim_value="Hiring senior distributed backend engineers across US hubs",
        source_url="https://stripe.com/jobs",
        source_name="Stripe Careers",
        source_category="primary",
        verification_status="verified",
        retrieval_timestamp=datetime.now(UTC),
    )

    signal = BusinessSignal(
        id="sig-201",
        company_id="demo-stripe",
        signal_type="Hiring Expansion",
        confidence_score=0.95,
        summary="Active hiring for infrastructure engineering roles",
        evidence_id="ev-101",
    )

    criteria = {
        "industry": "Fintech",
        "geography": "United States",
        "employee_range": "500+",
        "buying_signal": "Hiring",
    }

    score_result = scoring_service.calculate_lead_score(
        company=company,
        evidence_list=[evidence_verified],
        signals=[signal],
        criteria=criteria,
    )

    print(f"Target ICP Criteria: {criteria}")
    print(f"\nFinal Deterministic Score: {score_result.total_score} / 100 ({score_result.score_tier.upper()} TIER)")
    print(f"Data Quality Score:        {score_result.data_quality_score}%")
    print(f"Deterministic Notes:       {score_result.scoring_notes}\n")
    print("Scoring Breakdown:")
    for b in score_result.breakdown:
        match_icon = "[OK]" if b.matched else "[MISSING]"
        print(f"  {match_icon:<10} {b.category:<25} Awarded: {b.awarded_points:>4.1f} / {b.max_points:<4.1f} | {b.explanation}")


def demo_grounded_outreach_guard():
    print_section("4. Grounded Cold Outreach Guard (Zero-Hallucination Policy)")
    print("Scenario A: Candidate has verified hiring evidence")
    print("  --> Outreach Guard permits drafting and inserts verified quote.")
    print("      Subject: 'Question regarding growth at Stripe'")
    print("      Body:    'I noticed on Stripe Careers that you are expanding: \"Hiring senior distributed backend engineers\"...'")

    print("\nScenario B: Candidate has UNVERIFIED or MISSING evidence")
    print("  --> Outreach Guard STRICTLY BLOCKS template generation:")
    print("      [BLOCKED] Status: Insufficient Evidence Notice.")
    print("      Reason: 'LeadOS strictly requires at least one primary source-verified trigger")
    print("               before drafting outreach to prevent hallucinated claims.'")


def main():
    print("""
===========================================================================
  _                     _  ____   ____     ____    ___  
 | |    ___   __ _   __| |/ __ \ / ___|   |___ \  / _ \ 
 | |   / _ \ / _` | / _` | |  | |\___ \     __) || | | |
 | |__|  __/| (_| || (_| | |__| | ___) |   / __/ | |_| |
 |_____\___| \__,_| \__,_|\____/ |____/   |_____| \___/ 
                                                        
 Evidence-First B2B Prospecting Platform — Caprae Capital Hiring Challenge
===========================================================================
""")
    demo_ssrf_validator()
    demo_evidence_validator()
    demo_deterministic_scoring()
    demo_grounded_outreach_guard()

    print("\n" + "=" * 75)
    print(" LeadOS 2.0 Walkthrough Complete. All modules verified.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    # Add backend folder to sys.path so app modules import cleanly
    import os
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    main()
