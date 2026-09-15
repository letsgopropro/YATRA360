"""
Database Models Package for YATRA360.
All models are imported here so that Base.metadata contains complete
schema definitions for Alembic autogeneration and application runtime.
"""
from app.core.database import Base
from app.models.user import User
from app.models.destination import Destination
from app.models.crowd_metric import CrowdMetric
from app.models.review import Review
from app.models.itinerary import Itinerary
from app.models.itinerary_item import ItineraryItem
from app.models.business import Business
from app.models.safety import Safety

__all__ = [
    "Base",
    "User",
    "Destination",
    "CrowdMetric",
    "Review",
    "Itinerary",
    "ItineraryItem",
    "Business",
    "Safety",
]
