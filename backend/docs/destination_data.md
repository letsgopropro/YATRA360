# YATRA360 — Destination Dataset Documentation

This document describes the foundational destination dataset ingested into the YATRA360 PostgreSQL database for the prototype stage.

---

## 1. Overview & Dataset Summary

- **Total Ingested Destinations**: 82 authentic Indian destinations
- **States & Union Territories Represented**: 26
- **Categories Covered**: 8 distinct categories
- **Hidden Gem vs. Iconic Split**: 38 hidden gems (46.3%) / 44 iconic tourist landmarks (53.7%)
- **Zero-Budget Compliance**: 100% created using verified open public domain knowledge without paid APIs, billing services, or scraping.

---

## 2. Authoritative Data Sources

The destinations and factual attributes were compiled strictly from public and authoritative tourism resources:

1. **Archaeological Survey of India (ASI)** ([asi.nic.in](https://asi.nic.in)):
   - Centrally protected monuments, World Heritage sites, and official domestic entry ticket categories.
2. **Ministry of Tourism, Government of India (Incredible India)** ([incredibleindia.gov.in](https://www.incredibleindia.gov.in)):
   - National tourism circuits, official monument descriptions, cultural heritage designations, and regional classifications.
3. **State Tourism Development Corporations & Boards**:
   - Rajasthan Tourism Development Corporation (RTDC)
   - Karnataka State Tourism Development Corporation (KSTDC)
   - Kerala Tourism
   - Madhya Pradesh Tourism (MP Tourism)
   - Maharashtra Tourism Development Corporation (MTDC)
   - Gujarat Tourism
   - Department of Tourism, Jammu & Kashmir and UT of Ladakh
   - Tourism departments of Tamil Nadu, Andhra Pradesh, Odisha, West Bengal, Assam, Meghalaya, Sikkim, Nagaland, and Andaman & Nicobar.
4. **Survey of India / Open Government Data**:
   - Geocoordinate positioning (latitude and longitude) and administrative boundaries.

---

## 3. Geographic Distribution (26 States & UTs)

The dataset provides nationwide coverage across all geographical zones of India:

| Region | States / Union Territories Included | Destination Count |
| :--- | :--- | :--- |
| **North** | Delhi, Uttar Pradesh, Punjab, Rajasthan, Himachal Pradesh, Uttarakhand, Jammu & Kashmir, Ladakh | 31 |
| **West** | Maharashtra, Gujarat, Goa | 12 |
| **South** | Karnataka, Kerala, Tamil Nadu, Andhra Pradesh, Telangana | 20 |
| **Central**| Madhya Pradesh, Chhattisgarh | 5 |
| **East** | Odisha, West Bengal, Bihar | 6 |
| **Northeast & Islands** | Assam, Meghalaya, Sikkim, Arunachal Pradesh, Nagaland, Andaman & Nicobar Islands | 8 |

---

## 4. Category Breakdown

Destinations are cataloged across 8 distinct operational categories:

1. **Heritage** (24 destinations): Architectural marvels, forts, stepwells, UNESCO World Heritage monuments (e.g. Taj Mahal, Hampi, Qutub Minar, Ajanta Caves, Chittorgarh Fort, Rani ki Vav).
2. **Nature** (20 destinations): Lakes, canyons, valleys, waterfalls, geological wonders (e.g. Pangong Tso, Gandikota Canyon, Lonar Crater Lake, Valley of Flowers, Living Root Bridges).
3. **Spiritual** (8 destinations): Historic temples, gurdwaras, pilgrimage centers (e.g. Golden Temple, Meenakshi Amman Temple, Kedarnath Temple, Mahabodhi Temple).
4. **Wildlife** (7 destinations): National parks, tiger reserves, bird sanctuaries (e.g. Kaziranga, Keoladeo, Gir, Jim Corbett, Sundarbans).
5. **Beach** (6 destinations): Coastal landscapes, drive-in beaches, marine shorelines (e.g. Palolem Beach, Muzhappilangad Drive-in Beach, Radhanagar Beach, Varkala Cliff Beach).
6. **Cultural** (6 destinations): Living traditions, tribal landscapes, rural heritage (e.g. Ziro Valley, Majuli River Island, Shekhawati Havelis, Chettinad Mansions).
7. **Adventure** (6 destinations): High-altitude passes, mountain treks, winter ski resorts (e.g. Spiti Valley, Gulmarg Gondola, Dzukou Valley, Chopta-Tungnath).
8. **Hill Station** (5 destinations): Mountain retreats and tea plantations (e.g. Munnar, Coorg, Darjeeling).

---

## 5. Authoritative vs. Prototype Fields

To maintain absolute data integrity and honesty, the origin of each field is clearly delineated below:

### Authoritative Fields
These fields are grounded in public records and geography:
- `name`: Official English name of the destination.
- `slug`: Deterministic, URL-safe kebab-case unique identifier.
- `description`: Factual historical and geographical overview.
- `category`: Categorical tourism domain.
- `state` & `city`: Verified administrative district and state/UT.
- `latitude` & `longitude`: Accurate geographic coordinates matching the physical monument or viewpoint.
- `is_hidden_gem`: Curated boolean indicating lesser-known/offbeat destination vs. prominent international magnet.
- `entry_fee` (ASI sites): Official domestic ticket price (e.g., ₹50 or ₹40 for ASI centrally protected monuments).

### Prototype / Static Assumptions (Non-Authoritative)
The following fields adapt to existing database check constraints or indicate unavailable data:
- `entry_fee` (non-ASI sites): Set to `0.0` (safest non-negative value) for open natural vistas, public temples, and unverified rates.
- `safety_rating`: The database schema requires `NOT NULL` and enforces `CheckConstraint("safety_rating >= 1.0 AND safety_rating <= 5.0")`. All seeded destinations are assigned a neutral baseline of `4.0`. **This is a static schema requirement and DOES NOT represent a live safety score or official security assessment.**
- `base_crowd_level`: Set to categorical prototype estimates (`"low"`, `"moderate"`, `"high"`). **This is a static baseline and is NOT real-time footfall data.**
- `accessibility_info`: Includes factual notes where official ramp/buggy facilities exist or obvious physical terrain constraints (e.g. steep mountain staircase) are documented. Left as `None` (NULL) where not reliably established.
- `estimated_visit_duration`: Realistic circuit duration in minutes (e.g., 60 to 300 minutes).
- `image_url`: Explicitly left as `None` (NULL) to respect copyright policies and avoid dead external links.

---

## 6. Disclaimers

> [!IMPORTANT]
> **Crowd Data Disclaimer**:
> The `base_crowd_level` values in this table are static baseline placeholders designed for user interface and database prototyping. They **DO NOT** reflect real-time visitor counts, live sensor metrics, or current queue times. Real-time crowd estimation will be integrated in subsequent phases.

> [!WARNING]
> **Safety Data Disclaimer**:
> The `safety_rating` field is currently populated with a neutral prototype default (`4.0`) to satisfy database schema constraints. It **DOES NOT** represent an official safety advisory, government rating, or real-time disaster alert. Official safety integrations (IMD weather warnings and NDMA SACHET disaster advisories) will be introduced in future phases.

---

## 7. How to Rerun the Seed Script Safely

The seed script is located at:
`backend/scripts/seed_destinations.py`

### Standard Run (Safe & Idempotent)
```powershell
cd e:\YATRA360\backend
.\venv\Scripts\python scripts/seed_destinations.py
```
- **Behavior**: Checks existing records by unique `slug` and `(name, city, state)`. If a destination is already present, it is **skipped** without creating duplicate rows or altering existing primary keys.

### Dry-Run Mode (Preview Only)
```powershell
.\venv\Scripts\python scripts/seed_destinations.py --dry-run
```
- **Behavior**: Simulates the entire process and executes database operations inside a transaction that is rolled back at the end. No database records are committed.

### Update Mode (Sync Attributes)
```powershell
.\venv\Scripts\python scripts/seed_destinations.py --update
```
- **Behavior**: If a destination exists, updates its attributes (description, coordinates, etc.) while preserving existing primary keys and foreign key relationships.
