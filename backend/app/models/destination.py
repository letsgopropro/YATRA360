from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.crowd_metric import CrowdMetric
    from app.models.review import Review
    from app.models.itinerary_item import ItineraryItem
    from app.models.safety import Safety


class Destination(Base):
    """
    Tourist destination model with geocoordinates, crowd levels,
    safety indicators, and hidden-gem status.
    """
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    entry_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    safety_rating: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    is_hidden_gem: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    base_crowd_level: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    accessibility_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_visit_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in minutes
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("safety_rating >= 1.0 AND safety_rating <= 5.0", name="chk_dest_safety_rating"),
        CheckConstraint("entry_fee >= 0.0", name="chk_dest_entry_fee"),
        Index("ix_destinations_category_state", "category", "state"),
    )

    # Relationships
    crowd_metrics: Mapped[List["CrowdMetric"]] = relationship(
        "CrowdMetric",
        back_populates="destination",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="destination",
        cascade="all, delete-orphan"
    )
    itinerary_items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="destination",
        cascade="all, delete-orphan"
    )
    safety_records: Mapped[List["Safety"]] = relationship(
        "Safety",
        back_populates="destination",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Destination id={self.id} name={self.name} category={self.category}>"
