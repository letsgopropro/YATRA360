from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Safety(Base):
    """
    Safety model providing destination-level safety advisories,
    risk ratings, and emergency information.
    """
    __tablename__ = "safety"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    safety_level: Mapped[str] = mapped_column(String(50), default="safe", nullable=False)  # safe, moderate_risk, caution, high_risk
    safety_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # optional 1.0 - 5.0 scale
    risk_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_information: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)  # e.g., 'Local Authority', 'Tourist Police'
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("safety_rating IS NULL OR (safety_rating >= 1.0 AND safety_rating <= 5.0)", name="chk_safety_rating"),
        Index("ix_safety_dest_updated", "destination_id", "updated_at"),
    )

    # Relationships
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="safety_records"
    )

    def __repr__(self) -> str:
        return f"<Safety id={self.id} dest_id={self.destination_id} level={self.safety_level}>"
