"""
YATRA360 — Step 1 (User Input) & Step 2 (Data Collection) Verification Tests
Verifies that:
1. FastAPI successfully receives and parses realistic user travel preferences.
2. The backend retrieves the corresponding destination data from PostgreSQL.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_step1_user_input():
    """
    TASK 2 — Test STEP 1 (User Input)
    Verifies that FastAPI receives, validates, and parses:
    - Destination: Jaipur
    - Budget: 2000 INR
    - Available time: 1 day
    - Interests: Culture, Nature
    - Travel group: Friends
    """
    payload = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }

    response = client.post("/api/destinations/collect", json=payload)
    
    assert response.status_code == 200, f"FAIL — Step 1 User Input: HTTP {response.status_code} - {response.text}"
    data = response.json()
    
    received = data.get("step_1_user_input", {})
    assert received.get("destination") == "Jaipur", "FAIL — Step 1 User Input: destination mismatch"
    assert received.get("budget") == 2000.0, "FAIL — Step 1 User Input: budget mismatch"
    assert received.get("available_time") == "1 day", "FAIL — Step 1 User Input: available_time mismatch"
    assert received.get("interests") == ["Culture", "Nature"], "FAIL — Step 1 User Input: interests mismatch"
    assert received.get("travel_group") == "Friends", "FAIL — Step 1 User Input: travel_group mismatch"

    print("\nPASS — Step 1 User Input")


def test_step2_data_collection():
    """
    TASK 3 — Test STEP 2 (Data Collection)
    Verifies that using the destination from Step 1 ('Jaipur'), the backend retrieves:
    - destination name
    - location/coordinates
    - crowd information
    - safety information
    - estimated cost
    - weather/condition information
    - accessibility/distance information
    """
    payload = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }

    response = client.post("/api/destinations/collect", json=payload)
    assert response.status_code == 200, f"FAIL — Step 2 Data Collection: HTTP {response.status_code}"
    data = response.json()

    destinations = data.get("step_2_data_collection", [])
    assert len(destinations) >= 1, "FAIL — Step 2 Data Collection: No destinations returned for Jaipur"

    # Inspect the Jaipur destination (Amber Palace & Fort)
    jaipur_dest = next((d for d in destinations if "jaipur" in d["city"].lower() or "amber" in d["name"].lower()), None)
    assert jaipur_dest is not None, "FAIL — Step 2 Data Collection: Amber Palace & Fort not found in Jaipur results"

    # Verify all required data fields
    assert jaipur_dest["name"] == "Amber Palace & Fort", "FAIL — Step 2 Data Collection: Name mismatch"
    assert jaipur_dest["city"] == "Jaipur", "FAIL — Step 2 Data Collection: City mismatch"
    assert jaipur_dest["state"] == "Rajasthan", "FAIL — Step 2 Data Collection: State mismatch"
    assert 26.0 <= jaipur_dest["latitude"] <= 28.0, "FAIL — Step 2 Data Collection: Invalid latitude"
    assert 74.0 <= jaipur_dest["longitude"] <= 76.5, "FAIL — Step 2 Data Collection: Invalid longitude"
    assert jaipur_dest["base_crowd_level"] in {"low", "moderate", "high"}, "FAIL — Step 2 Data Collection: Missing crowd information"
    assert 1.0 <= jaipur_dest["safety_rating"] <= 5.0, "FAIL — Step 2 Data Collection: Missing safety rating"
    assert jaipur_dest["entry_fee"] == 100.0, "FAIL — Step 2 Data Collection: Missing entry fee"
    assert jaipur_dest["accessibility_info"] is not None, "FAIL — Step 2 Data Collection: Missing accessibility information"
    assert "weather_condition" in jaipur_dest, "FAIL — Step 2 Data Collection: Missing weather condition information"

    print("\nPASS — Step 2 Data Collection")


def test_existing_endpoints_compatibility():
    """Verify that existing GET /api/destinations?city=Jaipur also retrieves destination data."""
    response = client.get("/api/destinations?city=Jaipur")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any("amber" in d["name"].lower() for d in items)


def test_step1_input_validation_rejections():
    """
    Step 1 Validation: Test rejection of invalid user inputs.
    - Negative budget -> HTTP 422
    - Non-numeric budget -> HTTP 422
    - Negative available_time_minutes -> HTTP 422
    - Invalid interests type -> HTTP 422
    - Missing body -> HTTP 422
    """
    valid_base = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }

    # Negative budget
    resp = client.post("/api/v1/destinations/collect", json=dict(valid_base, budget=-500.0))
    assert resp.status_code == 422, "Expected 422 for negative budget"

    # Non-numeric budget
    resp = client.post("/api/v1/destinations/collect", json=dict(valid_base, budget="invalid_cost"))
    assert resp.status_code == 422, "Expected 422 for string budget"

    # Negative visit duration minutes
    resp = client.post("/api/v1/destinations/collect", json=dict(valid_base, available_time_minutes=-45))
    assert resp.status_code == 422, "Expected 422 for negative minutes"

    # Invalid interests type (non-list)
    resp = client.post("/api/v1/destinations/collect", json=dict(valid_base, interests=12345))
    assert resp.status_code == 422, "Expected 422 for non-list interests"

    # Missing request body
    resp = client.post("/api/v1/destinations/collect", content=b"")
    assert resp.status_code == 422, "Expected 422 for empty request body"


def test_step1_prefix_compatibility():
    """Verify that both /api/v1/destinations/collect and /api/destinations/collect work identically."""
    payload = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }
    resp_v1 = client.post("/api/v1/destinations/collect", json=payload)
    resp_api = client.post("/api/destinations/collect", json=payload)

    assert resp_v1.status_code == 200
    assert resp_api.status_code == 200
    assert resp_v1.json()["total_found"] == resp_api.json()["total_found"]
    assert resp_v1.json()["step_2_data_collection"][0]["name"] == resp_api.json()["step_2_data_collection"][0]["name"]


def test_step2_db_record_exact_match():
    """
    Step 2 Data Collection: Direct comparison between API response and PostgreSQL database record.
    Queries the Destination model directly and asserts 100% field congruence.
    """
    from app.core.database import SessionLocal
    from app.models.destination import Destination

    db = SessionLocal()
    try:
        db_dest = db.query(Destination).filter(Destination.city.ilike("%Jaipur%")).first()
        assert db_dest is not None, "Jaipur destination must exist in PostgreSQL"

        payload = {
            "destination": "Jaipur",
            "budget": 2000.0,
            "available_time": "1 day",
            "interests": ["Culture", "Nature"],
            "travel_group": "Friends",
        }
        resp = client.post("/api/v1/destinations/collect", json=payload)
        assert resp.status_code == 200
        api_data = resp.json()["step_2_data_collection"][0]

        # Field-by-field verification against PostgreSQL
        assert api_data["id"] == db_dest.id
        assert api_data["name"] == db_dest.name
        assert api_data["slug"] == db_dest.slug
        assert api_data["city"] == db_dest.city
        assert api_data["state"] == db_dest.state
        assert api_data["category"] == db_dest.category
        assert api_data["latitude"] == db_dest.latitude
        assert api_data["longitude"] == db_dest.longitude
        assert api_data["entry_fee"] == db_dest.entry_fee
        assert api_data["safety_rating"] == db_dest.safety_rating
        assert api_data["base_crowd_level"] == db_dest.base_crowd_level
        assert api_data["accessibility_info"] == db_dest.accessibility_info
        assert api_data["estimated_visit_duration"] == db_dest.estimated_visit_duration
        assert api_data["is_hidden_gem"] == db_dest.is_hidden_gem
    finally:
        db.close()


def test_step2_unknown_destination_handling():
    """Step 2 Data Collection: Test handling of an unlisted destination."""
    payload = {"destination": "NonExistentAtlantisXYZ"}
    resp = client.post("/api/v1/destinations/collect", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["total_found"] > 0, "Graceful fallback destinations should be returned"


def test_step2_all_destination_endpoints():
    """
    Verify all 5 standard destination endpoints against Jaipur record:
    1. GET /api/v1/destinations
    2. GET /api/v1/destinations/{id}
    3. GET /api/v1/destinations/slug/{slug}
    4. GET /api/v1/destinations/{id}/crowd
    5. GET /api/v1/destinations/{id}/safety
    """
    from app.core.database import SessionLocal
    from app.models.destination import Destination

    db = SessionLocal()
    try:
        jaipur = db.query(Destination).filter(Destination.slug == "amber-fort-jaipur").first()
        assert jaipur is not None

        # 1. List
        resp1 = client.get("/api/v1/destinations?city=Jaipur")
        assert resp1.status_code == 200
        assert len(resp1.json()) == 1
        assert resp1.json()[0]["slug"] == "amber-fort-jaipur"

        # 2. Get by ID
        resp2 = client.get(f"/api/v1/destinations/{jaipur.id}")
        assert resp2.status_code == 200
        assert resp2.json()["name"] == jaipur.name

        # 2b. 404 for invalid ID
        resp2_404 = client.get("/api/v1/destinations/999999")
        assert resp2_404.status_code == 404

        # 3. Get by Slug
        resp3 = client.get(f"/api/v1/destinations/slug/{jaipur.slug}")
        assert resp3.status_code == 200
        assert resp3.json()["id"] == jaipur.id

        # 3b. 404 for invalid slug
        resp3_404 = client.get("/api/v1/destinations/slug/invalid-slug-999")
        assert resp3_404.status_code == 404

        # 4. Crowd
        resp4 = client.get(f"/api/v1/destinations/{jaipur.id}/crowd")
        assert resp4.status_code == 200
        assert resp4.json()["crowd_level"] in {"low", "moderate", "high"}

        # 5. Safety
        resp5 = client.get(f"/api/v1/destinations/{jaipur.id}/safety")
        assert resp5.status_code == 200
        assert resp5.json()["safety_rating"] is not None
    finally:
        db.close()


def test_step2_scoring_engine_pipeline_compatibility():
    """
    Verify that destination data collected in Step 2 is structurally compatible
    with the existing scoring engine (calculate_destination_score).
    """
    from app.core.database import SessionLocal
    from app.models.destination import Destination
    from app.schemas.scoring import TravelRequest
    from app.services.scoring_engine import calculate_destination_score

    payload = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }
    resp = client.post("/api/v1/destinations/collect", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    user_req = TravelRequest(**data["step_1_user_input"])
    dest_id = data["step_2_data_collection"][0]["id"]

    db = SessionLocal()
    try:
        dest = db.get(Destination, dest_id)
        score_res = calculate_destination_score(dest, user_req)

        assert score_res.destination_id == dest_id
        assert 0.0 <= score_res.overall_score <= 100.0
        assert 0.0 <= score_res.components.preference_match <= 100.0
        assert 0.0 <= score_res.components.safety <= 100.0
        assert 0.0 <= score_res.components.crowd_suitability <= 100.0
        assert 0.0 <= score_res.components.accessibility_distance <= 100.0
        assert 0.0 <= score_res.components.cost_suitability <= 100.0
        assert 0.0 <= score_res.components.weather_condition <= 100.0
        assert len(score_res.explanations) == 6
    finally:
        db.close()

