from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

VerificationStatus = Literal["verified", "partially_verified", "unverified", "unknown"]


class EvidenceBase(BaseModel):
    claim_type: str = Field(..., min_length=2, max_length=100)
    claim_value: str = Field(..., min_length=2)
    source_url: str = Field(..., min_length=5)
    source_name: str = Field(..., min_length=1, max_length=255)
    source_category: str = Field(default="official_website")
    source_excerpt: str | None = None
    publication_date: str | None = None


class EvidenceCreate(EvidenceBase):
    company_id: str
    verification_status: VerificationStatus = "unknown"
    validation_notes: str | None = None


class EvidenceResponse(EvidenceBase):
    id: str
    company_id: str
    retrieval_timestamp: datetime
    verification_status: VerificationStatus
    validation_notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VerifyClaimRequest(BaseModel):
    claim_type: str
    claim_value: str
    source_url: str
