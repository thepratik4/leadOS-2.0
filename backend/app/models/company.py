from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.saved_lead import SavedLead
    from app.models.signal import BusinessSignal


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    signals: Mapped[list["BusinessSignal"]] = relationship(
        "BusinessSignal",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    saved_lead: Mapped[Optional["SavedLead"]] = relationship(
        "SavedLead",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (Index("ix_companies_domain_industry", "domain", "industry"),)
