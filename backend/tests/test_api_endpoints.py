import pytest
from httpx import AsyncClient

from app.models.company import Company
from app.models.evidence import Evidence


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "LeadOS"
    assert "search_provider" in data
    assert "ai_assisted_extraction" in data


@pytest.mark.asyncio
async def test_company_details_and_evidence(client: AsyncClient, db_session):
    # Insert test company directly
    comp = Company(
        id="test-comp-1",
        domain="stripe.com",
        name="Stripe",
        industry="Fintech",
        country="United States",
        website_url="https://stripe.com",
    )
    db_session.add(comp)
    await db_session.flush()

    ev = Evidence(
        id="test-ev-1",
        company_id="test-comp-1",
        claim_type="offering",
        claim_value="Financial infrastructure for the internet",
        source_url="https://stripe.com",
        source_name="Official Site",
        source_category="official_website",
        verification_status="verified",
    )
    db_session.add(ev)
    await db_session.commit()

    resp = await client.get("/api/v1/companies/test-comp-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Stripe"
    assert data["domain"] == "stripe.com"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["verification_status"] == "verified"
    assert data["lead_score"] is not None


@pytest.mark.asyncio
async def test_dossier_endpoint(client: AsyncClient, db_session):
    comp = Company(
        id="test-comp-2",
        domain="segment.com",
        name="Segment",
        industry="Analytics",
    )
    db_session.add(comp)
    await db_session.flush()

    ev = Evidence(
        id="test-ev-2",
        company_id="test-comp-2",
        claim_type="hiring",
        claim_value="Hiring solution engineers",
        source_url="https://segment.com/careers",
        source_name="Careers",
        verification_status="verified",
    )
    db_session.add(ev)
    await db_session.commit()

    resp = await client.get("/api/v1/companies/test-comp-2/dossier")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["verified_facts"]) >= 1
    assert len(data["inferences"]) >= 1
    assert data["inferences"][0]["confidence"] == "high"


@pytest.mark.asyncio
async def test_outreach_generation_grounded(client: AsyncClient, db_session):
    comp = Company(
        id="test-comp-3",
        domain="datadog.com",
        name="Datadog",
    )
    db_session.add(comp)
    await db_session.flush()

    ev = Evidence(
        id="test-ev-3",
        company_id="test-comp-3",
        claim_type="hiring",
        claim_value="Hiring Site Reliability Engineers",
        source_url="https://datadog.com/careers",
        source_name="Careers Portal",
        verification_status="verified",
    )
    db_session.add(ev)
    await db_session.commit()

    resp = await client.post("/api/v1/companies/test-comp-3/outreach", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_sufficient_evidence"] is True
    assert "Datadog" in data["subject_line"]
    assert "Hiring Site Reliability Engineers" in data["body_text"]


@pytest.mark.asyncio
async def test_outreach_generation_blocked_when_insufficient_evidence(
    client: AsyncClient, db_session
):
    comp = Company(
        id="test-comp-4",
        domain="unverified-corp.com",
        name="Unverified Corp",
    )
    db_session.add(comp)
    await db_session.commit()

    resp = await client.post("/api/v1/companies/test-comp-4/outreach", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_sufficient_evidence"] is False
    assert data["body_text"] is None
    assert "Insufficient verified evidence" in data["status_reason"]


@pytest.mark.asyncio
async def test_search_history_endpoint(client: AsyncClient, db_session):
    resp = await client.get("/api/v1/discovery/history?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_validation_error_format(client: AsyncClient):
    # Query length under minimum 2 chars should trigger structured 422
    resp = await client.post("/api/v1/discovery/search", json={"query": "a"})
    assert resp.status_code == 422
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
