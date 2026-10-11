from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.signal import BusinessSignal


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    claim_type: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="official_website"
    )
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieval_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    # Statuses: verified, partially_verified, unverified, unknown
    verification_status: Mapped[str] = mapped_column(
        String(50), index=True, default="unknown", nullable=False
    )
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="evidence")
    signals: Mapped[list["BusinessSignal"]] = relationship(
        "BusinessSignal", back_populates="evidence"
    )

    __table_args__ = (
        Index("ix_evidence_company_status", "company_id", "verification_status"),
        Index("ix_evidence_claim_type", "claim_type"),
    )
