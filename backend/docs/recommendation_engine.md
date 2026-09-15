# YATRA360 — Personalized Recommendation Engine Documentation

This document describes the design, candidate filtering, scoring engine integration, diversity balancing, explainability generator, and API architecture for the **YATRA360 Personalized Recommendation Engine** (Step 3).

---

## 1. Objective & Architecture Overview

The recommendation engine is a content-based, multi-criteria decision service that translates user travel requests into prioritized, transparent destination recommendations.

```
+-------------------------------------------------------------+
|                 RecommendationRequest                       |
|  - Preferences: interests, budget, available_time_minutes,  |
|                 preferred_crowd, prefer_hidden_gems,        |
|                 accessibility, coordinates/radius           |
|  - Controls:    category, state, is_hidden_gem, limit,      |
|                 apply_diversity, diversity_threshold        |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               1. Candidate Destination Selection            |
|  - Query PostgreSQL destinations table                      |
|  - Apply explicit filters (category, state, gem, keyword)   |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               2. Scoring via Existing Engine                |
|  - Strictly reuses calculate_destination_score()            |
|  - Computes 6 proposal components (normalized 0-100)        |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               3. Recommendation-Level Adjustments           |
|  - Available-time penalty (destinations exceeding schedule) |
|  - Generate 3-5 factual explainability bullet points        |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               4. Conservative Category Diversity            |
|  - Caps single-category dominance (max 2 per category)      |
|  - Promotes diverse alternatives within 10-point threshold  |
|  - Preserves high relevance without forced artificiality    |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                 RecommendationResponse                      |
|  - Up to requested limit (never exceeds eligible candidates)|
|  - Ranked by overall score descending                       |
|  - Complete component scores and transparent reasons        |
+-------------------------------------------------------------+
```

---

## 2. Relationship with the Scoring Engine

In strict adherence to architectural modularity:
- The recommendation engine **does NOT duplicate, recreate, or modify** any of the six scoring formulas or proposal weights.
- It calls `calculate_destination_score()` directly from [scoring_engine.py](file:///e:/YATRA360/backend/app/services/scoring_engine.py).
- The six components ($0.25 \times \text{Preference} + 0.20 \times \text{Safety} + 0.20 \times \text{Crowd} + 0.15 \times \text{Access/Distance} + 0.10 \times \text{Cost} + 0.10 \times \text{Weather}$) form the baseline evaluation for every candidate.
- Adjustments like available-time penalties and category diversity are applied strictly at the recommendation orchestration level *after* the baseline score is computed.

---

## 3. Candidate Selection & Filtering

Candidate selection pulls directly from the existing PostgreSQL `destinations` table using SQLAlchemy:
- **`category` filter**: Filters candidates by tourism category (e.g., `category="Beach"`).
- **`state` filter**: Limits candidates to a specific state or union territory (e.g., `state="Kerala"`).
- **`is_hidden_gem` filter**: Explicitly includes only hidden gems or only iconic landmarks.
- **`destination` keyword**: Searches city, state, or name (e.g., `destination="Jaipur"`).
- **No filters**: If no filters are provided, all available destinations in the database are evaluated.
- **Graceful limit handling**: The service returns *up to* the requested `limit` and never exceeds the number of matching candidates. If `limit=10` but only 4 candidates match a state filter, exactly 4 recommendations are returned without error.

---

## 4. Time Suitability Handling

The engine evaluates destination `estimated_visit_duration` against the user's `available_time_minutes`:
- **Within schedule (`duration <= available_time_minutes`)**: No penalty applied. A positive reason is recorded: *"Estimated visit time ({duration} mins) comfortably fits within your available schedule."*
- **Substantially exceeding schedule (`duration > 2.0 * available_time_minutes`)**: A penalty of -20.0 points is applied to prevent impractical recommendations (e.g., recommending an 8-hour trek for a 1-hour transit stop). A warning reason is noted.
- **Moderate overtime (`available_time_minutes < duration <= 2.0 * available_time_minutes`)**: A proportional penalty ($\le 10.0$ points) is applied.

---

## 5. Conservative Category Diversity Mechanism

To avoid returning 5 nearly identical destinations of the exact same category while preserving high recommendation relevance:
- **Threshold**: Configured to `10.0` points by default (`diversity_threshold=10.0`).
- **Algorithm**:
  1. Candidates are initially sorted by overall score descending.
  2. If the top selections already contain 2 destinations from category $A$, the engine looks ahead in the candidate list for a destination from a diverse category $B$.
  3. If candidate $B$ is within `10.0` points of the competing candidate $A$, candidate $B$ is promoted into the top recommendations.
  4. If candidate $B$ is more than `10.0` points below candidate $A$, candidate $A$ is retained.
  5. If the user explicitly filtered by a specific category (e.g., `category="Heritage"`), diversity balancing is automatically disabled.

---

## 6. Transparent Explainability (3–5 Reasons)

Every recommendation item includes 3 to 5 concise, factual bulleted reasons explaining the recommendation:
1. **Interest Match**: Identifies the specific user interest matching the destination category (e.g., *"Strong match for your interest 'Nature' in the Nature category"*).
2. **Hidden Gem**: Transparently indicates offbeat vs. iconic landmark status (e.g., *"Authentic offbeat hidden gem aligned with your preference for lesser-known spots"*).
3. **Crowd Atmosphere**: Explains crowd conditions relative to user preference (e.g., *"Matches your preferred low crowd level"*).
4. **Budget / Admission**: Mentions entry fee suitability (e.g., *"Free public entry with zero admission cost"* or *"Entry fee of ₹50 is well within your budget of ₹1000"*).
5. **Time Schedule**: Verifies compatibility between visit duration and available time.

---

## 7. Alternative Destination Scaffolding (Step 4 Preparation)

The service includes [find_alternative_destinations()](file:///e:/YATRA360/backend/app/services/recommendation_engine.py#L326-L395) as reusable foundation code:
- Given a destination ID (e.g., an overcrowded tourist site), queries candidates in the same category or state with lower crowd pressure or hidden-gem status.
- Evaluates them using the scoring engine and returns ranked alternatives.
- Exposes `GET /api/recommendations/alternatives/{destination_id}` for future overcrowding-mitigation pipelines.

---

## 8. API Endpoints

### 8.1 Generate Recommendations
- **Route**: `POST /api/recommendations`
- **Request Body**:
```json
{
  "interests": ["Nature", "Adventure"],
  "budget": 2000,
  "available_time_minutes": 480,
  "preferred_crowd_level": "low",
  "prefer_hidden_gems": true,
  "limit": 3
}
```
- **Response**:
```json
{
  "total_candidates_evaluated": 89,
  "recommendations_count": 3,
  "recommendations": [
    {
      "destination_id": 41,
      "destination_name": "Spiti Valley & Key Monastery",
      "slug": "spiti-valley-key-monastery",
      "city": "Lahaul and Spiti",
      "state": "Himachal Pradesh",
      "category": "Adventure",
      "is_hidden_gem": true,
      "entry_fee": 0.0,
      "safety_rating": 4.0,
      "base_crowd_level": "low",
      "estimated_visit_duration": 240,
      "overall_score": 89.2,
      "components": {
        "preference_match": 100.0,
        "safety": 80.0,
        "crowd_suitability": 100.0,
        "accessibility_distance": 75.0,
        "cost_suitability": 100.0,
        "weather_condition": 70.0
      },
      "reasons": [
        "Strong match for your interest 'Adventure' in the Adventure category.",
        "Authentic offbeat hidden gem aligned with your preference for lesser-known spots.",
        "Matches your preferred low crowd level.",
        "Free public entry with zero admission cost.",
        "Estimated visit time (240 mins) comfortably fits within your available schedule (480 mins)."
      ]
    }
  ],
  "request_summary": { ... },
  "applied_filters": {},
  "scoring_version": "1.0-weighted-content"
}
```

### 8.2 Alternative Destinations
- **Route**: `GET /api/recommendations/alternatives/{destination_id}?limit=5`
- **Response**: List of lower-crowd / offbeat alternatives.

---

## 9. Prototype Limitations & Future Roadmap

- **No ML / LLM in MVP**: The current engine uses deterministic, transparent, explainable content-based logic and multi-criteria scoring.
- **Future Enhancements**:
  - Collaborative filtering and user rating interaction history.
  - Live crowdsourced feedback calibration.
  - Multi-stop route itinerary clustering (Step 6).
