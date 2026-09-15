#!/usr/bin/env python3
"""
YATRA360 — Real Indian Destination Data Seeding Script
Step 1: Reliable, idempotent destination ingestion.

Usage:
    python scripts/seed_destinations.py [--dry-run] [--update]

Features:
- Connects via app.core.database.SessionLocal
- Fully idempotent: checks existing records by slug and (name, city, state)
- Uses transactions with automatic rollback on error
- Reports inserted, updated, skipped, and total counts
- Safe to rerun multiple times without duplicating data
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

# Ensure backend root is in sys.path so app imports work seamlessly
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, check_database_connection
from app.models.destination import Destination
from scripts.data.destinations_seed_data import DESTINATIONS_DATA


def seed_destinations(
    db: Session,
    update_existing: bool = False,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Seed destinations into the database idempotently.

    Args:
        db: SQLAlchemy database session
        update_existing: If True, updates attributes of existing records if changed
        dry_run: If True, performs operations but rolls back transaction at the end

    Returns:
        Dict with counts: {'total': int, 'inserted': int, 'updated': int, 'skipped': int, 'errors': int}
    """
    stats = {
        "total": len(DESTINATIONS_DATA),
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    print(f"Starting destination seeding: {stats['total']} destinations to process...")
    if dry_run:
        print("[DRY RUN MODE] No changes will be saved to the database.")

    try:
        for idx, item in enumerate(DESTINATIONS_DATA, start=1):
            slug = item["slug"]
            name = item["name"]
            city = item["city"]
            state = item["state"]

            # 1. Primary check: check by unique slug
            existing = db.scalar(select(Destination).where(Destination.slug == slug))

            # 2. Secondary check: check by name + city + state if slug differs
            if not existing:
                existing = db.scalar(
                    select(Destination).where(
                        Destination.name == name,
                        Destination.city == city,
                        Destination.state == state,
                    )
                )

            if existing:
                if update_existing:
                    # Update fields if requested
                    existing.name = item["name"]
                    existing.description = item["description"]
                    existing.category = item["category"]
                    existing.state = item["state"]
                    existing.city = item["city"]
                    existing.latitude = item["latitude"]
                    existing.longitude = item["longitude"]
                    existing.entry_fee = item["entry_fee"]
                    existing.safety_rating = item["safety_rating"]
                    existing.is_hidden_gem = item["is_hidden_gem"]
                    existing.base_crowd_level = item["base_crowd_level"]
                    existing.image_url = item["image_url"]
                    existing.accessibility_info = item["accessibility_info"]
                    existing.estimated_visit_duration = item["estimated_visit_duration"]
                    stats["updated"] += 1
                    print(f"  [{idx}/{stats['total']}] [UPDATED] {name} ({city}, {state})")
                else:
                    stats["skipped"] += 1
                    print(f"  [{idx}/{stats['total']}] [SKIPPED] {name} (already exists with id={existing.id})")
            else:
                new_dest = Destination(
                    name=item["name"],
                    slug=item["slug"],
                    description=item["description"],
                    category=item["category"],
                    state=item["state"],
                    city=item["city"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    entry_fee=item["entry_fee"],
                    safety_rating=item["safety_rating"],
                    is_hidden_gem=item["is_hidden_gem"],
                    base_crowd_level=item["base_crowd_level"],
                    image_url=item["image_url"],
                    accessibility_info=item["accessibility_info"],
                    estimated_visit_duration=item["estimated_visit_duration"],
                )
                db.add(new_dest)
                stats["inserted"] += 1
                print(f"  [{idx}/{stats['total']}] [INSERTED] {name} ({city}, {state})")

        if dry_run:
            db.rollback()
            print("\n[DRY RUN] Transaction rolled back. No database modifications made.")
        else:
            db.commit()
            print("\n[SUCCESS] Transaction committed successfully to database.")

    except Exception as exc:
        db.rollback()
        stats["errors"] += 1
        print(f"\n[ERROR] An error occurred during seeding: {exc}", file=sys.stderr)
        raise

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed real Indian destination dataset into YATRA360 PostgreSQL database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the seed process without committing any changes to the database.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing destinations if their data differs.",
    )
    args = parser.parse_args()

    # Verify database connectivity
    connected, msg = check_database_connection()
    if not connected:
        print(f"[FATAL] Cannot connect to database: {msg}", file=sys.stderr)
        return 1

    print("[INFO] Database connectivity verified.")

    db = SessionLocal()
    try:
        stats = seed_destinations(db=db, update_existing=args.update, dry_run=args.dry_run)
        print("=" * 60)
        print("SEEDING SUMMARY:")
        print(f"  Total processed : {stats['total']}")
        print(f"  Inserted        : {stats['inserted']}")
        print(f"  Updated         : {stats['updated']}")
        print(f"  Skipped         : {stats['skipped']}")
        print(f"  Errors          : {stats['errors']}")
        print("=" * 60)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
