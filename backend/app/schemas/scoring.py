from pydantic import BaseModel, Field


class ScoreBreakdownItem(BaseModel):
    category: str  # e.g., "verified_trigger", "industry_fit", "geo_fit", "company_size", "evidence_quality"
    awarded_points: float
    max_points: float
    matched: bool
    explanation: str
    evidence_id: str | None = None


class LeadScoreResult(BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    score_tier: str  # "high", "medium", "low"
    breakdown: list[ScoreBreakdownItem]
    matched_criteria: list[str]
    missing_evidence: list[str]
    data_quality_score: int = Field(..., ge=0, le=100)
    scoring_notes: str
