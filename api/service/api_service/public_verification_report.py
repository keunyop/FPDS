"""Operator-invoked, read-only overdue list. Never schedules or starts collection."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json

from api_service.config import Settings
from api_service.db import open_connection
from api_service.public_common import load_latest_public_snapshot, load_public_projection_rows
from api_service.public_verification import overdue_products, verification_summary


def build_report(connection, *, country_code: str, now: datetime | None = None) -> dict:
    if len(country_code) != 2 or not country_code.isascii() or not country_code.isalpha() or not country_code.isupper():
        raise ValueError("An uppercase ISO alpha-2 country is required")
    now = now or datetime.now(UTC)
    snapshot = load_latest_public_snapshot(connection, country_code=country_code)
    rows = load_public_projection_rows(connection, snapshot_id=str(snapshot["snapshot_id"]), country_code=country_code) if snapshot else []
    return {
        "country_code": country_code,
        "snapshot_id": snapshot["snapshot_id"] if snapshot else None,
        "snapshot_generated_at": str(snapshot.get("refreshed_at") or "") if snapshot else None,
        "availability": "available" if snapshot else "unavailable",
        "verification": verification_summary(rows, now=now),
        "items": overdue_products(rows, now=now),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--country", required=True)
    args = parser.parse_args()
    settings = Settings.from_env(args.env_file)
    with open_connection(settings) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        report = build_report(connection, country_code=args.country)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
