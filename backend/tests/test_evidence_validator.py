from app.validators.evidence_validator import validate_claim_against_source


def test_verified_claim_exact_match():
    source_text = (
        "Acme Corp provides automated invoicing software for enterprise logistics teams worldwide."
    )
    claim = "automated invoicing software"
    status, excerpt, notes = validate_claim_against_source(claim, "offering", source_text)

    assert status == "verified"
    assert excerpt is not None
    assert "automated invoicing software" in excerpt.lower()


def test_verified_claim_numeric_match():
    source_text = (
        "Founded in 2021, Acme has grown to over 150 employees with $25M in Series B funding."
    )
    claim = "has 150 employees with $25M funding"
    status, excerpt, notes = validate_claim_against_source(claim, "hiring", source_text)

    assert status == "verified"
    assert excerpt is not None


def test_unverified_claim_missing_number():
    source_text = "Acme Corp has a small team based in Chicago."
    claim = "Acme Corp raised $100M and employs 5000 engineers"
    status, excerpt, notes = validate_claim_against_source(claim, "funding", source_text)

    assert status == "unverified"
    assert excerpt is None
    assert "were not found" in notes


def test_unknown_status_on_empty_source():
    status, excerpt, notes = validate_claim_against_source("any claim", "offering", "")
    assert status == "unknown"
    assert excerpt is None


def test_partially_verified_status():
    source_text = "We specialize in cloud data security solutions for healthcare organizations."
    # Partial keyword overlap:
    claim = "cloud data compliance audit automation platform"
    status, excerpt, notes = validate_claim_against_source(claim, "offering", source_text)

    assert status in ("partially_verified", "unverified")
