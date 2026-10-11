from pydantic import BaseModel

from app.schemas.evidence import EvidenceResponse


class FactStatement(BaseModel):
    statement: str
    evidence_id: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    verification_status: str


class InferenceStatement(BaseModel):
    inference: str
    based_on_evidence_ids: list[str] = []
    confidence: str  # "high", "medium", "low"
    reasoning: str


class CompanyDossierResponse(BaseModel):
    company_id: str
    company_name: str
    domain: str
    verified_facts: list[FactStatement] = []
    unverified_claims: list[FactStatement] = []
    inferences: list[InferenceStatement] = []
    recommendations: list[str] = []
    data_quality_summary: str
    evidence_items: list[EvidenceResponse] = []
