# YATRA360 — Destination Scoring & Recommendation Engine Documentation

This document describes the design, mathematical formulation, normalization rules, missing-data handling, explainability mechanisms, and API architecture for the **YATRA360 Destination Scoring and Recommendation Engine**.

---

## 1. How Destination Scoring Works

The YATRA360 Recommendation Engine is a transparent, explainable, multi-criteria decision support system designed specifically for smart tourism. Rather than operating as a black-box deep learning model or simply recommending the most famous monuments, the engine systematically evaluates destination candidates across six multidimensional dimensions:

1. **User Preference Alignment**: Content-based match between user travel interests/activities and destination categories/features.
2. **Safety Baseline**: Informational safety score derived from validated tourist safety ratings.
3. **Crowd Suitability**: Inverse crowd pressure mapping (higher crowd footfall produces lower suitability).
4. **Accessibility & Distance**: Physical accessibility accommodation and geodesic proximity from the user's starting point.
5. **Cost Suitability**: Proportional evaluation of admission fee against user budget.
6. **Weather & Condition**: Seasonal and environmental suitability relative to user climate preferences.

The system normalizes every component to a uniform $[0.0, 100.0]$ scale before combining them through a configurable linear weighted sum.

---

## 2. Mathematical Formulation

The suitability score $S(d,u)$ of a candidate destination $d$ for a user $u$ is given by:

$$S(d,u) = 0.25 \, P(d,u) + 0.20 \, Sa(d) + 0.20 \, C(d) + 0.15 \, A(d,u) + 0.10 \, Co(d,u) + 0.10 \, W(d)$$

where:

| Symbol | Component Name | Default Weight ($w_i$) | Scale |
| :---: | :--- | :---: | :---: |
| **$P(d,u)$** | Preference Match | $0.25$ ($25\%$) | $0.0 - 100.0$ |
| **$Sa(d)$** | Safety Baseline | $0.20$ ($20\%$) | $0.0 - 100.0$ |
| **$C(d)$** | Crowd Suitability | $0.20$ ($20\%$) | $0.0 - 100.0$ |
| **$A(d,u)$** | Accessibility & Distance | $0.15$ ($15\%$) | $0.0 - 100.0$ |
| **$Co(d,u)$** | Cost Suitability | $0.10$ ($10\%$) | $0.0 - 100.0$ |
| **$W(d)$** | Weather / Condition Suitability | $0.10$ ($10\%$) | $0.0 - 100.0$ |

- **Weight Sum**: $\sum_{i=1}^{6} w_i = 0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.10 = 1.00$.
- **Bounded Score**: Since every sub-score $S_i \in [0.0, 100.0]$ and $\sum w_i = 1.0$, the composite score $S(d,u) \in [0.0, 100.0]$.

---

## 3. Meaning of Each Component

### 3.1 Preference Match ($P(d,u)$)
Compares the user's explicit interests (e.g., `["nature", "wildlife"]`) and preferred activities against destination category, tags, and description:
- **Direct Category Match**: Evaluates to $85.0 - 100.0$ based on keyword overlap ratio.
- **Description Keyword Match**: Evaluates to $35.0 - 75.0$ if interests are referenced in monument descriptions.
- **Non-matching Category**: Evaluates to baseline $20.0$.
- **Hidden-Gem Preference**: Grants $+10.0$ bonus when user preference aligns with `destination.is_hidden_gem`.
- **No Preference Specified**: Excluded from evaluation and weight is dynamically renormalized (no arbitrary numbers).

### 3.2 Safety Baseline ($Sa(d)$)
Normalizes the database `safety_rating` ($1.0$ to $5.0$ scale) into a $0–100$ scale:
$$\text{Score} = \left(\frac{\text{safety\_rating}}{5.0}\right) \times 100.0$$
> [!NOTE]
> **Safety Disclaimer**: Safety scores provide informational decision support for trip planning and do **NOT** constitute an official government guarantee of personal safety.

### 3.3 Crowd Suitability ($C(d)$)
Measures crowd pressure. Conceptually: **higher crowd pressure $\to$ lower crowd suitability**:
- `low`: **100.0** (maximum suitability; serene atmosphere).
- `moderate`: **60.0** (comfortable footfall).
- `high`: **20.0** (high footfall pressure).
- `overcrowded`: **10.0** (extreme congestion).

### 3.4 Accessibility & Distance ($A(d,u)$)
Blends physical mobility accessibility with geodesic proximity:
- **Accessibility Sub-Score**:
  - Without requirement: baseline of $80.0$.
  - With requirement: $95.0$ if wheelchair ramps/paved pathways are documented; $30.0$ if steep stairs/rugged trek terrain are present.
- **Distance Sub-Score**:
  - Evaluated via the **Haversine formula** when user coordinates are provided.
  - Scales linearly from $100.0$ ($0$ km) down to $50.0$ at `max_distance_km`. Distance exceeding the threshold incurs a decay penalty.
- **Composite**: $0.5 \times \text{Accessibility} + 0.5 \times \text{Distance}$.

### 3.5 Cost Suitability ($Co(d,u)$)
Evaluates `destination.entry_fee` relative to user `budget`:
- **Free Entry (`entry_fee == 0.0`)**: Maximum suitability of **100.0**.
- **Within Budget**:
  - $\le 10\%$ of budget: **95.0**
  - $\le 30\%$ of budget: **85.0**
  - $\le 60\%$ of budget: **75.0**
  - $\le 100\%$ of budget: **65.0**
- **Over Budget**: Soft linear penalty $\max\left(0.0, 50.0 - \left(\frac{\text{fee}}{\text{budget}} - 1.0\right) \times 50.0\right)$.
- **Unconstrained Budget**: Default baseline of **80.0** (marked as `fallback`).

### 3.6 Weather / Condition Suitability ($W(d)$)
Modular plug-in interface:
- **Climate Heuristics**: Grants high affinity ($90.0$) when user preference aligns with topology (e.g., "cool" + Hill Station, "warm" + Beach).
- **Prototype Baseline**: Documented neutral score of **70.0** (marked as `fallback`) pending live sensor/API integration.
- **Missing Data**: Excluded and weight is dynamically renormalized.

---

## 4. Normalization Strategy

To guarantee mathematical consistency and prevent raw units (rupees, kilometres, crowd visitor counts) from distorting the evaluation:
1. Every component function strictly maps its raw domain into $[0.0, 100.0]$.
2. Explicit clamping via `max(0.0, min(100.0, score))` guarantees bounds are never violated.
3. Rounded to 1 decimal place for numerical stability.

---

## 5. Default Weights & Validation

Scoring weights are defined in a centralized dictionary:

```python
DEFAULT_WEIGHTS = {
    "preference": 0.25,
    "safety": 0.20,
    "crowd": 0.20,
    "accessibility": 0.15,
    "cost": 0.10,
    "weather": 0.10,
}
```

The validation function `validate_weights(weights)` guarantees:
- All keys are present and non-negative.
- Total weights sum to $1.0$ within floating-point tolerance ($| \sum w_i - 1.0 | \le 10^{-3}$).

---

## 6. Overcrowding Threshold & Redirection

The engine centrally defines:

```python
OVERCROWDING_THRESHOLD = "high"
```

The function `is_overcrowded(destination)` identifies destinations operating at `"high"` or `"overcrowded"` footfall.
When an overcrowded destination is requested:
1. `check_and_redirect_if_overcrowded()` detects the condition.
2. The user's preferred site is acknowledged.
3. The engine automatically calls `recommend_alternatives()` to surface lower-crowd substitutes in the same category or geographic region.

---

## 7. Alternative Recommendation Logic

Alternative destination discovery combines:
1. **Destination Similarity ($40\%$)**: Uses `calculate_destination_similarity()` to match category/theme ($40\%$), geographic proximity ($30\%$), crowd/gem affinity ($20\%$), and budget ($10\%$). All similarity weights are centrally configurable via `DEFAULT_SIMILARITY_WEIGHTS`.
2. **General Suitability ($60\%$)**: Uses `calculate_destination_score()` to evaluate candidate fit for user preferences.
3. **Crowd Relief Bonus ($+10.0$ pts)**: Boosts candidates with strictly lower crowd levels than the preferred site.
4. **Strict Self-Exclusion**: The preferred destination is **never** recommended as its own alternative.

---

## 8. Deterministic Missing-Data Strategy

The system handles missing information deterministically using proportional weight renormalization:
- If a component's data is genuinely unavailable (e.g., `weather=None`, `safety_rating=None`, or no user preferences provided):
  - The component score is set to `None`.
  - The component is marked with `data_quality="missing"`.
  - The missing component's weight is excluded and the remaining available weights are renormalized proportionally:

$$w'_k = \frac{w_k}{\sum_{j \in K_{\text{avail}}} w_j} \quad \forall k \in K_{\text{avail}}$$

- If simulated or prototype baseline data is intentionally used:
  - The fallback value is used.
  - The component is clearly tagged with `data_quality="fallback"`.
- If verified telemetry, explicit reviews, or active user input was matched:
  - The component is tagged with `data_quality="real"`.

This guarantees that the frontend and examiners can distinguish between real, simulated, and missing data without crashing or inventing arbitrary numbers.

---

## 9. API Endpoints

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `POST` | `/api/recommendations` | Get personalized ranked destination recommendations. |
| `POST` | `/api/recommendations/alternatives` | Get alternatives for a preferred or overcrowded destination. |
| `GET` | `/api/recommendations/alternatives/{destination_id}` | Quick lookup of alternatives for a destination by ID. |
| `POST` | `/api/destinations/{destination_id}/score` | Calculate transparent suitability score for a single destination. |
| `POST` | `/api/scoring/destinations` | Score and rank candidate destinations against a travel request. |

---

## 10. Example Request

`POST /api/recommendations`

```json
{
  "interests": ["Nature", "Wildlife"],
  "budget": 2000.0,
  "available_time_minutes": 360,
  "preferred_crowd_level": "low",
  "prefer_hidden_gems": true,
  "user_latitude": 30.0869,
  "user_longitude": 78.2676,
  "max_distance_km": 300.0,
  "limit": 3
}
```

---

## 11. Example Response

```json
{
  "total_candidates_evaluated": 89,
  "recommendations_count": 1,
  "recommendations": [
    {
      "destination_id": 41,
      "destination_name": "Binsar Wildlife Sanctuary",
      "slug": "binsar-wildlife-sanctuary",
      "city": "Almora",
      "state": "Uttarakhand",
      "category": "Nature",
      "is_hidden_gem": true,
      "entry_fee": 150.0,
      "safety_rating": 4.5,
      "base_crowd_level": "low",
      "estimated_visit_duration": 240,
      "overall_score": 91.4,
      "components": {
        "preference_match": 100.0,
        "safety": 90.0,
        "crowd_suitability": 100.0,
        "accessibility_distance": 78.5,
        "cost_suitability": 95.0,
        "weather_condition": 70.0
      },
      "score_breakdown": {
        "preference": 100.0,
        "safety": 90.0,
        "crowd": 100.0,
        "accessibility": 78.5,
        "cost": 95.0,
        "weather": 70.0
      },
      "data_quality": {
        "preference": "real",
        "safety": "fallback",
        "crowd": "fallback",
        "accessibility": "real",
        "cost": "real",
        "weather": "fallback"
      },
      "is_alternative": false,
      "reasons": [
        "Strong match for your travel interests in the Nature category.",
        "Authentic offbeat hidden gem aligned with your preference for lesser-known spots.",
        "Matches your preferred low crowd atmosphere.",
        "Entry fee of ₹150 is well within your budget of ₹2000.",
        "Estimated visit time (240 mins) comfortably fits within your available schedule (360 mins)."
      ]
    }
  ],
  "request_summary": { ... },
  "applied_filters": {},
  "scoring_version": "1.0-weighted-content"
}
```

---

## 12. Future Expansion & Machine Learning Roadmap

The architecture was intentionally constructed as a modular foundation that leaves clear integration hooks for future AI enhancements:
1. **User Interaction & Feedback Learning**: Logging click-through rates, saved itineraries, and review ratings into the existing `reviews` table can train collaborative filtering or learning-to-rank models (e.g., LightGBM / RankNet).
2. **Embedding-Based Semantic Similarity**: The modular `destination_similarity.py` service can seamlessly replace token overlap with sentence-transformers or text embeddings without altering the recommendation engine.
3. **Live Telemetry Calibration**: Step 5 connects real-time crowd metrics and SACHET/IMD weather APIs to update `data_quality` from `"fallback"` to `"real"` dynamically.
