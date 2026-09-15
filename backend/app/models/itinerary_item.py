from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.itinerary import Itinerary
    from app.models.destination import Destination


class ItineraryItem(Base):
    """
    Individual stop within a user's multi-day itinerary.
    """
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    itinerary_id: Mapped[int] = mapped_column(
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    day_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    visit_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("day_number >= 1", name="chk_itinerary_item_day"),
        CheckConstraint("visit_order >= 1", name="chk_itinerary_item_order"),
        UniqueConstraint("itinerary_id", "day_number", "visit_order", name="uq_itinerary_day_order"),
    )

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship(
        "Itinerary",
        back_populates="items"
    )
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="itinerary_items"
    )

    def __repr__(self) -> str:
        return f"<ItineraryItem id={self.id} itin_id={self.itinerary_id} dest_id={self.destination_id} day={self.day_number} order={self.visit_order}>"
