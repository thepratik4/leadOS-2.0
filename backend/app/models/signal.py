from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.evidence import Evidence


class BusinessSignal(Base, TimestampMixin):
    __tablename__ = "business_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Signal types: hiring_expansion, tech_stack_adoption, leadership_change, product_launch, funding_growth
    signal_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="signals")
    evidence: Mapped[Optional["Evidence"]] = relationship("Evidence", back_populates="signals")

    __table_args__ = (Index("ix_signals_company_type", "company_id", "signal_type"),)
