from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.itinerary_item import ItineraryItem


class Itinerary(Base):
    """
    Itinerary model organizing multi-day travel plans for users.
    """
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("budget IS NULL OR budget >= 0.0", name="chk_itinerary_budget"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="itineraries"
    )
    items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="itinerary",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Itinerary id={self.id} user_id={self.user_id} title={self.title}>"
