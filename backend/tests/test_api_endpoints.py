import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.business import Business
from app.models.crowd_metric import CrowdMetric
from app.models.destination import Destination
from app.models.safety import Safety
from app.models.user import User

client = TestClient(app)


@pytest.fixture(scope="module")
def seeded_data():
    """Seed test destinations, businesses, crowd, and safety records once for API tests."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    dest = Destination(
        name=f"Varanasi Ghats {suffix}",
        slug=f"varanasi-ghats-{suffix}",
        description="Spiritual center on the banks of river Ganga.",
        category="Spiritual",
        state="Uttar Pradesh",
        city="Varanasi",
        latitude=25.3176,
        longitude=83.0125,
        entry_fee=0.0,
        safety_rating=4.2,
        is_hidden_gem=False,
        base_crowd_level="high",
        accessibility_info="Steep steps to river bank.",
        estimated_visit_duration=120,
    )
    db.add(dest)
    db.flush()

    crowd = CrowdMetric(
        destination_id=dest.id,
        crowd_level="high",
        visitor_count=1200,
    )
    db.add(crowd)

    safety = Safety(
        destination_id=dest.id,
        safety_level="safe",
        safety_rating=4.2,
        risk_description="Slippery stone steps during morning rituals.",
        emergency_information="Varanasi Tourist Police: 112.",
        source="UP Tourism Advisory",
    )
    db.add(safety)

    biz = Business(
        name=f"Kashi Ganga Boat Tours {suffix}",
        description="Traditional wooden boat rides during sunrise.",
        category="guide",
        city="Varanasi",
        state="Uttar Pradesh",
        latitude=25.3180,
        longitude=83.0130,
        contact_info="+91 9876543210",
        website="https://kashiboattours.in",
        is_active=True,
    )
    db.add(biz)

    db.commit()
    dest_id = dest.id
    dest_slug = dest.slug
    biz_id = biz.id
    db.close()

    yield {
        "dest_id": dest_id,
        "dest_slug": dest_slug,
        "biz_id": biz_id,
        "suffix": suffix,
    }


# ============================================================================
# 1. Authentication Tests
# ============================================================================

def test_auth_registration_succeeds():
    """Verify user registration returns 201, safe role, and no plaintext password."""
    email = f"tourist_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Aarav Patel",
        "role": "tourist",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email.lower()
    assert data["full_name"] == "Aarav Patel"
    assert data["role"] == "tourist"
    assert "hashed_password" not in data
    assert "id" in data


def test_auth_registration_duplicate_email_rejected():
    """Verify registering with an existing email returns 400 Bad Request."""
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "First Register",
        "role": "tourist",
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


def test_auth_password_is_hashed_in_database():
    """Verify plaintext passwords are never stored in the database."""
    email = f"hashcheck_{uuid.uuid4().hex[:8]}@example.com"
    plain_password = "MySuperSecretPassword#2026"
    payload = {
        "email": email,
        "password": plain_password,
        "full_name": "Hash Verifier",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201

    db = SessionLocal()
    user = db.scalar(select(User).where(User.email == email))
    db.close()

    assert user is not None
    assert user.hashed_password != plain_password
    assert user.hashed_password.startswith("$2b$")


def test_auth_admin_escalation_blocked():
    """Verify that registering with role 'admin' is rejected."""
    email = f"escalate_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "AdminPassword123",
        "full_name": "Malicious User",
        "role": "admin",
    }
    response = client.post("/api/auth/register", json=payload)
    # Pydantic pattern validation rejects 'admin' with 422, or route rejects with 403
    assert response.status_code in (403, 422)


def test_auth_login_succeeds():
    """Verify valid credentials return JWT access token."""
    email = f"login_ok_{uuid.uuid4().hex[:8]}@example.com"
    password = "LoginPass#123"
    client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Valid Login",
    })

    login_resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_auth_login_invalid_password_rejected():
    """Verify incorrect password returns 401 Unauthorized."""
    email = f"wrong_pwd_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "CorrectPassword",
        "full_name": "Wrong Pass User",
    })

    login_resp = client.post("/api/auth/login", json={
        "email": email,
        "password": "IncorrectPassword",
    })
    assert login_resp.status_code == 401
    assert "incorrect email or password" in login_resp.json()["detail"].lower()


def test_auth_me_requires_token():
    """Verify /auth/me returns 401 when accessed without Bearer token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_current_user():
    """Verify /auth/me returns authenticated user's profile with valid token."""
    email = f"me_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "MyPassword123"
    client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Me User",
    })

    login_data = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    }).json()
    token = login_data["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == email.lower()
    assert user_data["full_name"] == "Me User"


# ============================================================================
# 2. Destination Tests
# ============================================================================

def test_list_destinations(seeded_data):
    """Verify destinations list endpoint returns items."""
    response = client.get("/api/destinations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_destination_filtering(seeded_data):
    """Verify destination filtering by category, state, and city."""
    response = client.get("/api/destinations?category=Spiritual&city=Varanasi")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["id"] == seeded_data["dest_id"] for d in data)


def test_get_destination_by_id(seeded_data):
    """Verify retrieving destination by ID."""
    dest_id = seeded_data["dest_id"]
    response = client.get(f"/api/destinations/{dest_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dest_id
    assert "slug" in data


def test_get_destination_by_slug(seeded_data):
    """Verify retrieving destination by slug."""
    slug = seeded_data["dest_slug"]
    response = client.get(f"/api/destinations/slug/{slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug


def test_destination_not_found():
    """Verify requesting nonexistent destination ID returns 404."""
    response = client.get("/api/destinations/999999")
    assert response.status_code == 404


# ============================================================================
# 3. Business Tests
# ============================================================================

def test_list_businesses(seeded_data):
    """Verify business list endpoint returns active businesses."""
    response = client.get("/api/businesses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_business_filtering(seeded_data):
    """Verify business filtering by category and city."""
    response = client.get("/api/businesses?category=guide&city=Varanasi")
    assert response.status_code == 200
    data = response.json()
    assert any(b["id"] == seeded_data["biz_id"] for b in data)


def test_get_business_by_id(seeded_data):
    """Verify business lookup by ID and 404 on missing ID."""
    biz_id = seeded_data["biz_id"]
    response = client.get(f"/api/businesses/{biz_id}")
    assert response.status_code == 200
    assert response.json()["id"] == biz_id

    missing = client.get("/api/businesses/999999")
    assert missing.status_code == 404


# ============================================================================
# 4. Crowd & Safety Tests
# ============================================================================

def test_destination_crowd_endpoint(seeded_data):
    """Verify crowd endpoint returns latest crowd data."""
    dest_id = seeded_data["dest_id"]
    response = client.get(f"/api/destinations/{dest_id}/crowd")
    assert response.status_code == 200
    data = response.json()
    assert data["destination_id"] == dest_id
    assert data["crowd_level"] == "high"


def test_destination_safety_endpoint(seeded_data):
    """Verify safety endpoint returns advisory data."""
    dest_id = seeded_data["dest_id"]
    response = client.get(f"/api/destinations/{dest_id}/safety")
    assert response.status_code == 200
    data = response.json()
    assert data["destination_id"] == dest_id
    assert data["safety_level"] == "safe"
    assert "emergency_information" in data


def test_crowd_safety_missing_destination():
    """Verify crowd and safety endpoints return 404 for invalid destination."""
    r_crowd = client.get("/api/destinations/999999/crowd")
    assert r_crowd.status_code == 404

    r_safety = client.get("/api/destinations/999999/safety")
    assert r_safety.status_code == 404


# ============================================================================
# 5. Reviews Tests
# ============================================================================

def test_create_review_unauthenticated_rejected(seeded_data):
    """Verify review creation without auth returns 401."""
    dest_id = seeded_data["dest_id"]
    response = client.post(f"/api/destinations/{dest_id}/reviews", json={
        "rating": 5,
        "comment": "Unauthenticated test",
    })
    assert response.status_code == 401


def test_create_and_list_reviews(seeded_data):
    """Verify authenticated review creation and subsequent retrieval."""
    dest_id = seeded_data["dest_id"]
    email = f"reviewer_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123",
        "full_name": "Reviewer Person",
    })
    token = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123",
    }).json()["access_token"]

    review_resp = client.post(
        f"/api/destinations/{dest_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "rating": 5,
            "comment": "Breathtaking evening aarti ceremony.",
            "reported_crowd_level": "high",
        }
    )
    assert review_resp.status_code == 201
    data = review_resp.json()
    assert data["rating"] == 5
    assert data["destination_id"] == dest_id
    assert data["user_name"] == "Reviewer Person"

    # Verify review shows up in destination reviews list
    list_resp = client.get(f"/api/destinations/{dest_id}/reviews")
    assert list_resp.status_code == 200
    reviews = list_resp.json()
    assert any(r["id"] == data["id"] for r in reviews)


def test_review_rating_validation(seeded_data):
    """Verify rating out of 1-5 range is rejected with 422."""
    dest_id = seeded_data["dest_id"]
    email = f"rater_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123",
        "full_name": "Rater Person",
    })
    token = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123",
    }).json()["access_token"]

    # Rating 6 is invalid
    resp_high = client.post(
        f"/api/destinations/{dest_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"rating": 6, "comment": "Invalid rating"}
    )
    assert resp_high.status_code == 422

    # Rating 0 is invalid
    resp_low = client.post(
        f"/api/destinations/{dest_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"rating": 0, "comment": "Invalid rating"}
    )
    assert resp_low.status_code == 422


# ============================================================================
# 6. Itinerary Tests
# ============================================================================

def test_itinerary_requires_authentication():
    """Verify itinerary endpoints require authentication."""
    r_list = client.get("/api/itineraries")
    assert r_list.status_code == 401

    r_create = client.post("/api/itineraries", json={"title": "Unauthorized Trip"})
    assert r_create.status_code == 401


def test_itinerary_creation_and_ownership(seeded_data):
    """Verify authenticated user can create itineraries and only owner can view."""
    dest_id = seeded_data["dest_id"]

    # User 1
    email1 = f"user1_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email1,
        "password": "Password123",
        "full_name": "User One",
    })
    token1 = client.post("/api/auth/login", json={
        "email": email1,
        "password": "Password123",
    }).json()["access_token"]

    # User 2
    email2 = f"user2_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email2,
        "password": "Password123",
        "full_name": "User Two",
    })
    token2 = client.post("/api/auth/login", json={
        "email": email2,
        "password": "Password123",
    }).json()["access_token"]

    # User 1 creates itinerary
    create_resp = client.post(
        "/api/itineraries",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "title": "Spiritual Journey to Varanasi",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 12000.0,
            "items": [
                {
                    "destination_id": dest_id,
                    "day_number": 1,
                    "visit_order": 1,
                    "notes": "Morning boat ride",
                }
            ],
        }
    )
    assert create_resp.status_code == 201
    itin = create_resp.json()
    itin_id = itin["id"]
    assert len(itin["items"]) == 1
    assert itin["items"][0]["destination_id"] == dest_id

    # User 1 can view their itinerary
    get_owner = client.get(
        f"/api/itineraries/{itin_id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert get_owner.status_code == 200
    assert get_owner.json()["title"] == "Spiritual Journey to Varanasi"

    # User 2 CANNOT view User 1's itinerary (403 Forbidden)
    get_other = client.get(
        f"/api/itineraries/{itin_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert get_other.status_code == 403

    # Nonexistent itinerary returns 404
    get_missing = client.get(
        "/api/itineraries/999999",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert get_missing.status_code == 404
