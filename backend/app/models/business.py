from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Business(Base):
    """
    Local business model for discovering verified local guides, artisans,
    restaurants, homestays, and cultural experiences.
    """
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # restaurant, guide, artisan, homestay, cultural_experience
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    contact_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Optional linkage to business owner user account
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )

    __table_args__ = (
        Index("ix_businesses_category_city", "category", "city"),
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="businesses"
    )

    def __repr__(self) -> str:
        return f"<Business id={self.id} name={self.name} category={self.category} city={self.city}>"
