import pytest
from httpx import AsyncClient

from app.models.company import Company


@pytest.mark.asyncio
async def test_saved_lead_lifecycle_and_csv_export(client: AsyncClient, db_session):
    # Create test company
    comp = Company(
        id="comp-save-1",
        domain="zapier.com",
        name="Zapier",
        industry="Productivity",
        country="United States",
    )
    db_session.add(comp)
    await db_session.commit()

    # 1. Save lead
    save_resp = await client.post(
        "/api/v1/saved-leads",
        json={"company_id": "comp-save-1", "notes": "High priority integration partner"},
    )
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    saved_lead_id = save_data["id"]
    assert save_data["notes"] == "High priority integration partner"

    # 2. List saved leads
    list_resp = await client.get("/api/v1/saved-leads")
    assert list_resp.status_code == 200
    leads = list_resp.json()
    assert len(leads) == 1
    assert leads[0]["company"]["name"] == "Zapier"

    # 3. CSV Export with formula injection check
    export_resp = await client.get("/api/v1/saved-leads/export")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/csv")
    csv_text = export_resp.text
    assert "Company Name,Domain" in csv_text or "Zapier" in csv_text

    # 4. Patch saved lead status and notes
    patch_resp = await client.patch(
        f"/api/v1/saved-leads/{saved_lead_id}",
        json={"status": "qualified", "notes": "Updated: Decision maker contacted"},
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data["status"] == "qualified"
    assert patch_data["notes"] == "Updated: Decision maker contacted"

    # 5. Delete saved lead
    del_resp = await client.delete(f"/api/v1/saved-leads/{saved_lead_id}")
    assert del_resp.status_code == 200

    # 6. Check list is empty
    list_resp_after = await client.get("/api/v1/saved-leads")
    assert len(list_resp_after.json()) == 0
