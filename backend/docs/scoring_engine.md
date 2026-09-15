# YATRA360 — Dynamic Destination Scoring Engine Documentation

This document describes the design, mathematical formulation, normalization rules, and API integration for the **YATRA360 Dynamic Destination Scoring Engine** (Step 2).

---

## 1. Objective & Architectural Role

The scoring engine is a transparent, modular multi-criteria decision evaluation system. It takes a structured travel request and computes how well a candidate destination satisfies the user's explicit criteria and travel constraints.

```
+-------------------------------------------------------------+
|                      User Travel Request                    |
|  - Interests & categories         - Budget                  |
|  - Preferred crowd level          - Accessibility needs     |
|  - Starting coordinates / radius  - Weather preferences     |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               Dynamic Destination Scoring Engine            |
|                                                             |
|  0.25 × Preference Match (0-100)                            |
|  0.20 × Safety Baseline (0-100)                             |
|  0.20 × Crowd Suitability (0-100)                           |
|  0.15 × Accessibility & Proximity (0-100)                   |
|  0.10 × Cost Suitability (0-100)                            |
|  0.10 × Weather / Condition Suitability (0-100)             |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                     DestinationScoreResponse                |
|  - Overall Score (0.0 to 100.0)                             |
|  - Normalized Component Breakdown                           |
|  - Configured Weights (sum = 1.0)                           |
|  - Transparent Human-Readable Explanations                  |
+-------------------------------------------------------------+
```

---

## 2. Core Scoring Formula

As defined in the project proposal, the overall destination suitability score is a linear combination of six normalized sub-scores:

$$\text{Destination Score} = \sum_{i=1}^{6} w_i \cdot S_i$$

$$\begin{aligned}
\text{Destination Score} &= 0.25 \times S_{\text{preference}} \\
&+ 0.20 \times S_{\text{safety}} \\
&+ 0.20 \times S_{\text{crowd}} \\
&+ 0.15 \times S_{\text{accessibility\_distance}} \\
&+ 0.10 \times S_{\text{cost}} \\
&+ 0.10 \times S_{\text{weather}}
\end{aligned}$$

- **Weights**: $\sum w_i = 0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.10 = 1.00$.
- **Scale**: Every component $S_i \in [0.0, 100.0]$. Consequently, the overall score strictly falls within $[0.0, 100.0]$.

---

## 3. Component Details & Normalization

### 3.1 Preference Match ($S_{\text{preference}}$, Weight: 0.25)
Compares user interests against the destination category and characteristics:
- **No interests provided**: Evaluates to neutral baseline ($70.0$).
- **Direct category match**: Evaluates to $90.0$.
  - **Hidden-gem alignment**: $+10.0$ bonus if user preference aligns with `destination.is_hidden_gem` (up to $100.0$).
- **Keyword description match**: Evaluates to $45.0$ if interests are referenced in monument descriptions.
- **Non-matching category**: Evaluates to $20.0$.

### 3.2 Safety Score ($S_{\text{safety}}$, Weight: 0.20)
Normalizes the database `safety_rating` (scale 1.0 to 5.0) into a $0–100$ scale:
$$\text{Score} = \left(\frac{\text{safety\_rating}}{5.0}\right) \times 100.0$$

| Database Rating | Normalized Score | Rationale |
| :---: | :---: | :--- |
| **5.0** | **100.0** | Maximum safety baseline |
| **4.0** | **80.0** | Standard prototype default |
| **3.0** | **60.0** | Moderate safety baseline |
| **2.0** | **40.0** | Elevated caution advisory |
| **1.0** | **20.0** | High caution advisory |

> [!NOTE]
> **Safety Disclaimer**: The current values derive from prototype baseline ratings in the database. They do **NOT** constitute an official government safety guarantee. Live safety feeds (IMD/NDMA SACHET) will replace this baseline in Step 5.

### 3.3 Crowd Suitability ($S_{\text{crowd}}$, Weight: 0.20)
Evaluates crowd suitability using a configurable mapping:

#### A. When user specifies `preferred_crowd_level`:
- **User prefers `low`**:
  - `low` destination: **100.0**
  - `moderate` destination: **60.0**
  - `high` destination: **20.0**
- **User prefers `moderate`**:
  - `moderate` destination: **100.0**
  - `low` destination: **80.0**
  - `high` destination: **30.0**
- **User prefers `high`** (e.g. festivals, vibrant street bazaars):
  - `high` destination: **100.0**
  - `moderate` destination: **70.0**
  - `low` destination: **50.0**

#### B. When no crowd preference is specified:
General crowd pressure mapping is applied:
- `low`: **100.0**
- `moderate`: **60.0**
- `high`: **20.0**

### 3.4 Accessibility & Distance ($S_{\text{accessibility\_distance}}$, Weight: 0.15)
Blends physical accessibility accommodations and geodesic distance proximity:
- **Accessibility ($S_{\text{acc}}$)**:
  - If accessibility is not required: $80.0$ baseline.
  - If accessibility is required:
    - Wheelchair / ramp / flat paved paths documented: **95.0**
    - Steep stairs / rocky trekking terrain / difficult access: **30.0**
    - Unverified / NULL: **50.0** (cautious prototype baseline)
- **Distance ($S_{\text{dist}}$)**:
  - When user coordinates are provided, computes the geodesic great-circle distance via the **Haversine formula**.
  - Scales linearly from $100.0$ (0 km) to $50.0$ at `max_distance_km`. Distance exceeding the threshold incurs a decay penalty.
  - When user coordinates are not provided: Documented neutral baseline of **70.0** (avoids inventing fictitious distances).
- **Composite**: $0.5 \times S_{\text{acc}} + 0.5 \times S_{\text{dist}}$.

### 3.5 Cost Suitability ($S_{\text{cost}}$, Weight: 0.10)
Evaluates `destination.entry_fee` relative to user `budget`:
- **No budget specified**: Neutral unconstrained baseline of **80.0**.
- **Free entry (`entry_fee == 0.0`)**: Maximum suitability of **100.0**.
- **Within budget**:
  - $\le 10\%$ of budget: **95.0**
  - $\le 30\%$ of budget: **85.0**
  - $\le 60\%$ of budget: **75.0**
  - $\le 100\%$ of budget: **65.0**
- **Over budget**: Linear penalty $\max\left(0, 50 - \left(\frac{\text{fee}}{\text{budget}} - 1\right) \times 50\right)$.

> [!WARNING]
> **Cost Limitation**: Destination entry fee represents admission ticket pricing only. It does not include transport, accommodation, or meal costs.

### 3.6 Weather / Condition Suitability ($S_{\text{weather}}$, Weight: 0.10)
Modular plug-in architecture for environmental conditions:
- **Prototype baseline**: Assigns a documented neutral score of **70.0** when live weather is unintegrated.
- **Climate heuristics**: Grants alignment scores ($90.0$) when user preferences correlate with destination topology (e.g. "cool" + Hill Station, "warm" + Beach).

---

## 4. API Endpoints

### 4.1 Score Single Destination
- **Route**: `POST /api/scoring/destination/{destination_id}`
- **Sample Request**:
```json
{
  "interests": ["Heritage"],
  "budget": 1000,
  "preferred_crowd_level": "moderate",
  "requires_accessibility": true
}
```
- **Sample Response**:
```json
{
  "destination_id": 24,
  "destination_name": "Taj Mahal",
  "destination_slug": "taj-mahal-agra",
  "overall_score": 73.4,
  "components": {
    "preference_match": 90.0,
    "safety": 80.0,
    "crowd_suitability": 30.0,
    "accessibility_distance": 82.5,
    "cost_suitability": 95.0,
    "weather_condition": 70.0
  },
  "weights": {
    "preference_match": 0.25,
    "safety": 0.20,
    "crowd_suitability": 0.20,
    "accessibility_distance": 0.15,
    "cost_suitability": 0.10,
    "weather_condition": 0.10
  },
  "explanations": {
    "preference_match": "Direct category match for interest 'Heritage' with 'Heritage'.",
    "safety": "Database safety baseline rating 4.0/5.0 normalized to 80.0 (prototype baseline, not an official safety guarantee).",
    "crowd_suitability": "User preferred 'moderate' crowd level matched against destination level 'high' -> score 30.0 (prototype baseline).",
    "accessibility_distance": "Documented wheelchair/ramp facilities match accessibility requirements. | User starting location not provided; neutral proximity baseline (70.0) used.",
    "cost_suitability": "Entry fee ₹50 is within budget ₹1000 (5.0% of budget; note: entry fee does not cover travel/lodging).",
    "weather_condition": "Neutral weather prototype baseline (70.0) applied; live weather API integration pending."
  }
}
```

### 4.2 Score Destinations Batch & Rank
- **Route**: `POST /api/scoring/destinations?limit=10&category=Nature`
- **Behavior**: Evaluates all filtered destinations, sorts them by `overall_score` descending, and returns ranked candidates for recommendations.

---

## 5. Integration with Future Recommendation Engine (Step 3)

The scoring engine is completely decoupled from database queries and UI layers:
1. **Candidate Retrieval**: Step 3 will query eligible destinations based on geographic filters or state/category facets.
2. **Scoring Pipeline**: Step 3 will pass retrieved destinations and user session criteria through `calculate_destination_score()`.
3. **Transparent Explainability**: The resulting `components` and `explanations` will allow the frontend to render "Why this was recommended" explainability cards.
