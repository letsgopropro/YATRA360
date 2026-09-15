from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.destination import Destination


class Review(Base):
    """
    User review model containing rating, comments, and reported crowd feedback.
    """
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_crowd_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, moderate, high, overcrowded
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating"),
        Index("ix_reviews_dest_created", "destination_id", "created_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reviews"
    )
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="reviews"
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} user_id={self.user_id} dest_id={self.destination_id} rating={self.rating}>"
