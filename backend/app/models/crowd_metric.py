from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class CrowdMetric(Base):
    """
    Crowd metric tracking recorded crowd levels and visitor density for destinations.
    """
    __tablename__ = "crowd_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    crowd_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # low, moderate, high, overcrowded
    visitor_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("visitor_count IS NULL OR visitor_count >= 0", name="chk_crowd_visitor_count"),
        Index("ix_crowd_metrics_dest_recorded", "destination_id", "recorded_at"),
    )

    # Relationships
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="crowd_metrics"
    )

    def __repr__(self) -> str:
        return f"<CrowdMetric id={self.id} dest_id={self.destination_id} level={self.crowd_level}>"
