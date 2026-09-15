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
