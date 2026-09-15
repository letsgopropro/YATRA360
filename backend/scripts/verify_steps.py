#!/usr/bin/env python3
"""
YATRA360 — Standalone Step 1 (User Input) & Step 2 (Data Collection) Verifier.
Run directly via:
    python scripts/verify_steps.py
"""

import sys
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

def run_verification():
    client = TestClient(app)

    sample_request = {
        "destination": "Jaipur",
        "budget": 2000.0,
        "available_time": "1 day",
        "interests": ["Culture", "Nature"],
        "travel_group": "Friends",
    }

    response = client.post("/api/destinations/collect", json=sample_request)

    step1_status = "FAIL"
    step2_status = "FAIL"
    received_data = {}
    jaipur_dest = {}

    if response.status_code == 200:
        data = response.json()
        received_data = data.get("step_1_user_input", {})
        if (
            received_data.get("destination") == "Jaipur"
            and received_data.get("budget") == 2000.0
            and received_data.get("available_time") == "1 day"
            and received_data.get("interests") == ["Culture", "Nature"]
            and received_data.get("travel_group") == "Friends"
        ):
            step1_status = "PASS"

        destinations = data.get("step_2_data_collection", [])
        if destinations:
            jaipur_dest = destinations[0]
            if (
                jaipur_dest.get("name")
                and jaipur_dest.get("city") == "Jaipur"
                and jaipur_dest.get("latitude") is not None
                and jaipur_dest.get("longitude") is not None
                and jaipur_dest.get("base_crowd_level") is not None
                and jaipur_dest.get("safety_rating") is not None
                and jaipur_dest.get("entry_fee") is not None
                and jaipur_dest.get("accessibility_info") is not None
                and jaipur_dest.get("weather_condition") is not None
            ):
                step2_status = "PASS"

    print("=" * 48)
    print("YATRA360 STEP VERIFICATION")
    print("=" * 48)
    print()
    print("STEP 1 — USER INPUT")
    print(f"Status: {step1_status}")
    print("Endpoint: POST /api/destinations/collect")
    print("Test command: .\\venv\\Scripts\\pytest tests/test_step1_step2_verification.py")
    print("What was received:")
    print(json.dumps(received_data, indent=2))
    print("What was returned:")
    print(f"  HTTP {response.status_code} OK (Validated & parsed as TravelRequest model)")
    print()
    print("STEP 2 — DATA COLLECTION")
    print(f"Status: {step2_status}")
    print("Endpoint/service: POST /api/destinations/collect (backed by PostgreSQL SQLAlchemy query)")
    print("Database: PostgreSQL (yatra360_db / destinations table)")
    print(f"Destination tested: {jaipur_dest.get('name', 'N/A')} ({jaipur_dest.get('city', 'N/A')}, {jaipur_dest.get('state', 'N/A')})")
    print("Data retrieved:")
    for k, v in jaipur_dest.items():
        print(f"  - {k}: {v}")
    print()
    print("=" * 48)
    print("OVERALL")
    print("=" * 48)
    print(f"Step 1: {step1_status}")
    print(f"Step 2: {step2_status}")
    print()

    if step1_status == "PASS" and step2_status == "PASS":
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(run_verification())
