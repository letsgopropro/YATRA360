import pytest
from datetime import date
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal, engine
from app.models import (
    Base,
    User,
    Destination,
    CrowdMetric,
    Review,
    Itinerary,
    ItineraryItem,
    Business,
    Safety,
)


@pytest.fixture
def db_session():
    """Yield a database session and rollback changes after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_tables_exist_in_postgres():
    """Verify that all 8 expected YATRA360 MVP tables exist in PostgreSQL."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = {
        "users",
        "destinations",
        "crowd_metrics",
        "reviews",
        "itineraries",
        "itinerary_items",
        "businesses",
        "safety",
        "alembic_version",
    }
    assert expected_tables.issubset(existing_tables), f"Missing tables: {expected_tables - existing_tables}"


def test_table_columns_exist():
    """Verify essential columns exist on each table."""
    inspector = inspect(engine)

    user_cols = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "email", "hashed_password", "full_name", "role", "is_active", "created_at"}.issubset(user_cols)

    dest_cols = {c["name"] for c in inspector.get_columns("destinations")}
    assert {
        "id", "name", "slug", "description", "category", "state", "city",
        "latitude", "longitude", "entry_fee", "safety_rating", "is_hidden_gem",
        "base_crowd_level", "image_url", "accessibility_info", "estimated_visit_duration", "created_at"
    }.issubset(dest_cols)

    crowd_cols = {c["name"] for c in inspector.get_columns("crowd_metrics")}
    assert {"id", "destination_id", "crowd_level", "visitor_count", "recorded_at"}.issubset(crowd_cols)

    review_cols = {c["name"] for c in inspector.get_columns("reviews")}
    assert {"id", "user_id", "destination_id", "rating", "comment", "reported_crowd_level", "created_at"}.issubset(review_cols)

    itin_cols = {c["name"] for c in inspector.get_columns("itineraries")}
    assert {"id", "user_id", "title", "start_date", "end_date", "budget", "created_at"}.issubset(itin_cols)

    item_cols = {c["name"] for c in inspector.get_columns("itinerary_items")}
    assert {"id", "itinerary_id", "destination_id", "day_number", "visit_order", "notes"}.issubset(item_cols)

    biz_cols = {c["name"] for c in inspector.get_columns("businesses")}
    assert {
        "id", "name", "description", "category", "city", "state",
        "latitude", "longitude", "contact_info", "website", "image_url", "is_active", "created_at", "owner_id"
    }.issubset(biz_cols)

    safety_cols = {c["name"] for c in inspector.get_columns("safety")}
    assert {
        "id", "destination_id", "safety_level", "safety_rating",
        "risk_description", "emergency_information", "source", "updated_at", "created_at"
    }.issubset(safety_cols)


def test_create_and_query_models_with_relationships(db_session):
    """Verify model instantiation, persistence, and ORM relationship navigation."""
    # 1. Create a user
    user = User(
        email="test.tourist@yatra360.com",
        hashed_password="secure_hashed_password_sample",
        full_name="Rajesh Sharma",
        role="tourist",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    assert user.id is not None

    # 2. Create a destination
    destination = Destination(
        name="Hawa Mahal",
        slug="hawa-mahal-jaipur",
        description="Palace of Winds constructed of red and pink sandstone.",
        category="Heritage",
        state="Rajasthan",
        city="Jaipur",
        latitude=26.9239,
        longitude=75.8267,
        entry_fee=50.0,
        safety_rating=4.5,
        is_hidden_gem=False,
        base_crowd_level="high",
        accessibility_info="Ground floor wheelchair accessible.",
        estimated_visit_duration=90,
    )
    db_session.add(destination)
    db_session.flush()
    assert destination.id is not None

    # 3. Create CrowdMetric
    crowd = CrowdMetric(
        destination_id=destination.id,
        crowd_level="high",
        visitor_count=350,
    )
    db_session.add(crowd)
    db_session.flush()

    # 4. Create Review
    review = Review(
        user_id=user.id,
        destination_id=destination.id,
        rating=5,
        comment="Incredible architecture, best visited in early morning.",
        reported_crowd_level="moderate",
    )
    db_session.add(review)
    db_session.flush()

    # 5. Create Itinerary and ItineraryItem
    itinerary = Itinerary(
        user_id=user.id,
        title="Golden Triangle Heritage Tour",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
        budget=15000.0,
    )
    db_session.add(itinerary)
    db_session.flush()

    item = ItineraryItem(
        itinerary_id=itinerary.id,
        destination_id=destination.id,
        day_number=1,
        visit_order=1,
        notes="Visit during golden hour for photographs.",
    )
    db_session.add(item)
    db_session.flush()

    # 6. Create Business
    business = Business(
        name="Laxmi Mishthan Bhandar (LMB)",
        description="Historic sweet shop and authentic Rajasthani restaurant.",
        category="restaurant",
        city="Jaipur",
        state="Rajasthan",
        latitude=26.9215,
        longitude=75.8242,
        contact_info="+91 141 2565844",
        website="https://www.lmbjaipur.com",
        is_active=True,
        owner_id=user.id,
    )
    db_session.add(business)
    db_session.flush()

    # 7. Create Safety record
    safety = Safety(
        destination_id=destination.id,
        safety_level="safe",
        safety_rating=4.5,
        risk_description="Mild crowd congestion during peak tourist season (Oct-Feb).",
        emergency_information="Tourist Police Helpline: 1363 / +91 141 2603830. SMS Hospital: 108.",
        source="Rajasthan Tourism Police",
    )
    db_session.add(safety)
    db_session.flush()

    # Verify bidirectional relationships
    assert len(user.reviews) == 1
    assert user.reviews[0].destination.name == "Hawa Mahal"

    assert len(destination.crowd_metrics) == 1
    assert destination.crowd_metrics[0].crowd_level == "high"

    assert len(destination.reviews) == 1
    assert destination.reviews[0].user.full_name == "Rajesh Sharma"

    assert len(user.itineraries) == 1
    assert len(user.itineraries[0].items) == 1
    assert user.itineraries[0].items[0].destination.name == "Hawa Mahal"

    assert len(user.businesses) == 1
    assert user.businesses[0].name == "Laxmi Mishthan Bhandar (LMB)"

    assert len(destination.safety_records) == 1
    assert destination.safety_records[0].safety_level == "safe"


def test_user_role_check_constraint(db_session):
    """Verify that user role check constraint rejects invalid roles."""
    invalid_user = User(
        email="invalid@example.com",
        hashed_password="hash",
        full_name="Invalid Role User",
        role="superadmin",  # Not in ('tourist', 'business', 'admin')
        is_active=True,
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_destination_safety_rating_constraint(db_session):
    """Verify that destination safety rating constraint rejects out-of-range ratings."""
    invalid_dest = Destination(
        name="Invalid Rating Spot",
        slug="invalid-rating-spot",
        description="Testing constraints",
        category="Nature",
        state="Uttarakhand",
        city="Rishikesh",
        latitude=30.0869,
        longitude=78.2676,
        safety_rating=6.0,  # Max allowed is 5.0
    )
    db_session.add(invalid_dest)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_itinerary_item_unique_constraint(db_session):
    """Verify that duplicate (itinerary_id, day_number, visit_order) is rejected."""
    user = User(
        email="unique_test@example.com",
        hashed_password="hash",
        full_name="Order Test User",
        role="tourist",
    )
    db_session.add(user)
    db_session.flush()

    dest1 = Destination(
        name="Dest One",
        slug="dest-one-uq",
        description="First stop",
        category="Culture",
        state="Delhi",
        city="New Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )
    dest2 = Destination(
        name="Dest Two",
        slug="dest-two-uq",
        description="Second stop",
        category="Culture",
        state="Delhi",
        city="New Delhi",
        latitude=28.6239,
        longitude=77.2190,
    )
    db_session.add_all([dest1, dest2])
    db_session.flush()

    itinerary = Itinerary(
        user_id=user.id,
        title="Day Trip Delhi",
    )
    db_session.add(itinerary)
    db_session.flush()

    item1 = ItineraryItem(
        itinerary_id=itinerary.id,
        destination_id=dest1.id,
        day_number=1,
        visit_order=1,
    )
    item2 = ItineraryItem(
        itinerary_id=itinerary.id,
        destination_id=dest2.id,
        day_number=1,
        visit_order=1,  # Duplicate day 1, visit_order 1
    )
    db_session.add_all([item1, item2])
    with pytest.raises(IntegrityError):
        db_session.flush()
