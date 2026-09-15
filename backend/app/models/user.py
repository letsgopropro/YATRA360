from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.review import Review
    from app.models.itinerary import Itinerary
    from app.models.business import Business


class User(Base):
    """
    User model supporting tourists, business owners, and platform administrators.
    Ready for JWT authentication and role-based access control.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="tourist", nullable=False)  # tourist, business, admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("role IN ('tourist', 'business', 'admin')", name="chk_user_role"),
    )

    # Relationships
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    businesses: Mapped[List["Business"]] = relationship(
        "Business",
        back_populates="owner"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
