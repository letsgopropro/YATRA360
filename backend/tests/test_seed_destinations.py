import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.core.database import SessionLocal
from app.main import app
from app.models.destination import Destination
from scripts.data.destinations_seed_data import DESTINATIONS_DATA
from scripts.seed_destinations import seed_destinations

client = TestClient(app)


# ============================================================================
# 1. Dataset Integrity Tests
# ============================================================================

def test_seed_dataset_size_and_diversity():
    """Verify that dataset contains 250 real destinations across all 36 Indian states and union territories."""
    assert len(DESTINATIONS_DATA) == 250, f"Expected 250 destinations, got {len(DESTINATIONS_DATA)}"
    
    states = {item["state"] for item in DESTINATIONS_DATA}
    assert len(states) == 36, f"Expected all 36 states and UTs, got {len(states)}"
    
    categories = {item["category"] for item in DESTINATIONS_DATA}
    assert len(categories) >= 8, f"Expected varied categories, got {len(categories)}"
    
    hidden_gems = [item for item in DESTINATIONS_DATA if item["is_hidden_gem"]]
    assert len(hidden_gems) >= 80, f"Expected meaningful hidden gems, got {len(hidden_gems)}"


def test_seed_dataset_fields_and_geographic_boundaries():
    """
    Verify each destination record has non-empty required fields and
    accurate coordinates within the Indian subcontinent bounding box
    (Lat: 6.0 to 38.0 N, Lon: 68.0 to 98.0 E).
    """
    slugs = set()
    for idx, item in enumerate(DESTINATIONS_DATA):
        assert item["name"].strip(), f"Empty name at index {idx}"
        assert item["slug"].strip(), f"Empty slug at index {idx}"
        assert item["slug"] == item["slug"].lower(), f"Slug should be lowercase: {item['slug']}"
        assert item["slug"] not in slugs, f"Duplicate slug in dataset: {item['slug']}"
        slugs.add(item["slug"])

        assert item["description"].strip(), f"Empty description for {item['name']}"
        assert item["category"].strip(), f"Empty category for {item['name']}"
        assert item["state"].strip(), f"Empty state for {item['name']}"
        assert item["city"].strip(), f"Empty city for {item['name']}"

        # Geographic bounds for India
        lat = item["latitude"]
        lon = item["longitude"]
        assert 6.0 <= lat <= 38.0, f"Latitude {lat} out of bounds for {item['name']}"
        assert 68.0 <= lon <= 98.0, f"Longitude {lon} out of bounds for {item['name']}"

        # Schema constraints
        assert item["entry_fee"] >= 0.0, f"Negative entry fee for {item['name']}"
        assert 1.0 <= item["safety_rating"] <= 5.0, f"Safety rating out of bounds for {item['name']}"
        assert item["base_crowd_level"] in {"low", "moderate", "high"}, f"Invalid crowd level for {item['name']}"
        
        # Image and attribution compliance
        assert item["image_url"] is not None and item["image_url"].startswith("http"), f"Image URL must be a valid HTTP URL for {item['name']}"
        assert item["image_attribution"] is not None and item["image_attribution"].strip(), f"Image attribution missing for {item['name']}"


# ============================================================================
# 2. Seed Execution & Idempotency Tests
# ============================================================================

def test_seed_destinations_idempotent():
    """Verify running seed_destinations multiple times produces 0 new inserts and skips duplicates."""
    db = SessionLocal()
    try:
        # First execution (destinations already seeded)
        stats1 = seed_destinations(db=db, update_existing=False, dry_run=False)
        assert stats1["errors"] == 0
        assert stats1["inserted"] == 0
        assert stats1["skipped"] == len(DESTINATIONS_DATA)

        # Second execution immediately after
        stats2 = seed_destinations(db=db, update_existing=False, dry_run=False)
        assert stats2["errors"] == 0
        assert stats2["inserted"] == 0
        assert stats2["skipped"] == len(DESTINATIONS_DATA)
    finally:
        db.close()


def test_seed_destinations_dry_run():
    """Verify dry_run does not commit any changes."""
    db = SessionLocal()
    try:
        stats = seed_destinations(db=db, update_existing=True, dry_run=True)
        assert stats["errors"] == 0
        assert stats["total"] == len(DESTINATIONS_DATA)
    finally:
        db.close()


# ============================================================================
# 3. API Endpoint Verification with Seeded Data
# ============================================================================

def test_api_list_destinations_returns_seeded_items():
    """Verify GET /api/destinations returns seeded Indian destinations."""
    response = client.get("/api/destinations?limit=100")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 50

    sample_names = {d["name"] for d in data}
    assert "Taj Mahal" in sample_names
    assert "Hampi Group of Monuments" in sample_names


def test_api_destination_category_filtering():
    """Verify filtering destinations by category."""
    response = client.get("/api/destinations?category=Heritage&limit=100")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 15
    for item in items:
        assert "heritage" in item["category"].lower()


def test_api_destination_hidden_gem_filtering():
    """Verify filtering destinations by hidden gem status."""
    response = client.get("/api/destinations?is_hidden_gem=true&limit=100")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 20
    for item in items:
        assert item["is_hidden_gem"] is True


def test_api_destination_state_filtering():
    """Verify filtering destinations by state."""
    response = client.get("/api/destinations?state=Kerala&limit=100")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 4
    for item in items:
        assert item["state"] == "Kerala"


def test_api_destination_get_by_slug():
    """Verify retrieving specific seeded destination by slug."""
    response = client.get("/api/destinations/slug/taj-mahal-agra")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Taj Mahal"
    assert data["city"] == "Agra"
    assert data["state"] == "Uttar Pradesh"
    assert data["entry_fee"] == 50.0
    assert data["latitude"] == pytest.approx(27.1751, rel=1e-3)
    assert data["longitude"] == pytest.approx(78.0421, rel=1e-3)
    assert data["image_url"] is not None and data["image_url"].startswith("http")
    assert data["image_attribution"] is not None


def test_api_destination_get_by_id():
    """Verify retrieving specific seeded destination by ID."""
    db = SessionLocal()
    dest = db.scalar(select(Destination).where(Destination.slug == "hampi-monuments-vijayanagara"))
    dest_id = dest.id
    db.close()

    response = client.get(f"/api/destinations/{dest_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dest_id
    assert data["name"] == "Hampi Group of Monuments"
    assert data["category"] == "Heritage"
    assert data["state"] == "Karnataka"


def test_api_destination_crowd_and_safety_endpoints():
    """Verify crowd and safety fallback endpoints work for seeded destinations."""
    response = client.get("/api/destinations/slug/taj-mahal-agra")
    dest_id = response.json()["id"]

    crowd_resp = client.get(f"/api/destinations/{dest_id}/crowd")
    assert crowd_resp.status_code == 200
    assert crowd_resp.json()["crowd_level"] in {"low", "moderate", "high"}

    safety_resp = client.get(f"/api/destinations/{dest_id}/safety")
    assert safety_resp.status_code == 200
    assert safety_resp.json()["safety_rating"] == 4.0


def test_api_destination_stats_endpoint():
    """Verify /api/destinations/stats returns accurate platform catalog counts."""
    response = client.get("/api/destinations/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_active"] == 250
    assert data["total_inactive"] == 21
    assert data["total_all"] == 271
    assert data["states_count"] == 36
    assert data["categories_count"] >= 8
    assert data["hidden_gems_count"] >= 100


def test_api_destination_count_and_headers():
    """Verify /api/destinations/count and X-Total-Count header."""
    # Unfiltered count
    resp_count = client.get("/api/destinations/count")
    assert resp_count.status_code == 200
    assert resp_count.json()["total"] == 250

    # Filtered count
    resp_kerala = client.get("/api/destinations/count?state=Kerala")
    assert resp_kerala.status_code == 200
    assert resp_kerala.json()["total"] == 12

    # List endpoint header
    resp_list = client.get("/api/destinations?limit=24&skip=0")
    assert resp_list.status_code == 200
    assert resp_list.headers.get("x-total-count") == "250"
    assert len(resp_list.json()) == 24


def test_api_pagination_covers_all_250_destinations_without_duplicates():
    """Verify pagination across all pages retrieves exactly 250 unique active destinations."""
    page_size = 24
    total_expected = 250
    collected_ids = []

    for skip in range(0, total_expected, page_size):
        resp = client.get(f"/api/destinations?limit={page_size}&skip={skip}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) <= page_size
        collected_ids.extend([item["id"] for item in items])

    assert len(collected_ids) == 250, f"Expected 250 total items, got {len(collected_ids)}"
    assert len(set(collected_ids)) == 250, "Duplicate destination IDs detected across pagination pages!"

