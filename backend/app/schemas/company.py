from datetime import datetime

from pydantic import BaseModel

from app.schemas.evidence import EvidenceResponse
from app.schemas.scoring import LeadScoreResult


class SignalResponse(BaseModel):
    id: str
    signal_type: str
    confidence_score: float
    summary: str
    detected_at: datetime
    evidence_id: str | None = None

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    domain: str
    name: str
    industry: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    employee_range: str | None = None
    description: str | None = None
    website_url: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime
    verified_evidence_count: int = 0
    total_evidence_count: int = 0
    lead_score: int | None = None
    score_tier: str | None = None
    is_saved: bool = False

    class Config:
        from_attributes = True


class CompanyDetailResponse(CompanyResponse):
    evidence: list[EvidenceResponse] = []
    signals: list[SignalResponse] = []
    score_result: LeadScoreResult | None = None
