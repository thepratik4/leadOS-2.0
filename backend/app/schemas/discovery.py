from pydantic import BaseModel, Field

from app.schemas.company import CompanyResponse, SignalResponse
from app.schemas.evidence import EvidenceResponse
from app.schemas.scoring import LeadScoreResult


class DiscoverySearchRequest(BaseModel):
    query: str = Field(
        ..., min_length=2, max_length=200, description="Target search query or company category"
    )
    industry: str | None = Field(None, max_length=100, description="Target industry filter")
    geography: str | None = Field(
        None, max_length=100, description="Target geography or headquarters filter"
    )
    employee_range: str | None = Field(
        None, max_length=50, description="Desired company size range"
    )
    buying_signal: str | None = Field(
        None, max_length=100, description="Target buying signal (e.g. hiring, tech_adoption)"
    )
    limit: int = Field(
        default=10, ge=1, le=25, description="Maximum number of candidates to discover"
    )
    verify_sources: bool = Field(
        default=True, description="Whether to automatically retrieve and verify primary sources"
    )


class DiscoveryCandidateItem(BaseModel):
    company: CompanyResponse
    signals: list[SignalResponse] = []
    evidence: list[EvidenceResponse] = []
    score: LeadScoreResult
    primary_signal: str | None = None
    verification_summary: dict[str, int] = Field(
        default_factory=lambda: {
            "verified": 0,
            "partially_verified": 0,
            "unverified": 0,
            "unknown": 0,
        }
    )


class DiscoverySearchResponse(BaseModel):
    search_run_id: str
    query: str
    total_candidates: int
    verified_candidates: int
    provider: str
    duration_ms: int
    candidates: list[DiscoveryCandidateItem]
    provider_status: str
    provider_notice: str | None = None


class SearchRunResponse(BaseModel):
    id: str
    query: str
    filters_json: str
    candidate_count: int
    provider: str
    status: str
    duration_ms: int
    created_at: str

    class Config:
        from_attributes = True
