from pydantic import BaseModel


class OutreachDraftRequest(BaseModel):
    angle: str | None = "pain_point_trigger"
    recipient_role: str | None = (
        None  # e.g., "VP Engineering", "Head of Sales" (generic role, never fake person)
    )


class OutreachDraftResponse(BaseModel):
    company_id: str
    company_name: str
    has_sufficient_evidence: bool
    status_reason: str
    trigger_summary: str | None = None
    supporting_evidence_id: str | None = None
    supporting_source_url: str | None = None
    subject_line: str | None = None
    body_text: str | None = None
    facts_referenced: list[str] = []
