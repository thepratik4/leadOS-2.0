from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.company import CompanyResponse


class SavedLeadCreate(BaseModel):
    company_id: str
    notes: str | None = None
    status: str = Field(default="new")


class SavedLeadUpdate(BaseModel):
    notes: str | None = None
    status: str | None = None


class SavedLeadResponse(BaseModel):
    id: str
    company_id: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    company: CompanyResponse | None = None

    class Config:
        from_attributes = True
