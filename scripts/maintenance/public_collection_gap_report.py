"""Read-only CA/US comparison-gap audit; no bank fetch, model call or mutation."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api/service"))
from api_service.config import Settings
from api_service.db import open_connection
from api_service.public_common import load_latest_public_snapshot, load_public_projection_rows
from api_service.public_products import _serialize_product_row
from worker.pipeline.fpds_approval_policy import comparison_quality


def inspect_rows(rows, canonical):
    """Missing optional conditions are follow-up hints, never automatic errors."""
    items = []
    for row in rows:
        p = _serialize_product_row(row, locale="en")
        terms = p.get("deposit_terms") or {}
        reasons = []
        if terms.get("reason"):
            reasons.append("deposit:" + terms["reason"])
        if p["product_type"] in ("mortgage", "personal-loan", "line-of-credit") and p.get("secured_flag") is None:
            reasons.append("security:undisclosed")
        if p["product_type"] in ("savings", "chequing"):
            for key in ("minimum_deposit", "minimum_balance"):
                if p.get(key) is None:
                    reasons.append(key + ":undisclosed")
        if not p.get("product_url"):
            reasons.append("official_url:missing")
        if reasons:
            items.append({"country_code": p["country_code"], "product_id": p["product_id"],
                          "bank_code": p["bank_code"], "product_type": p["product_type"],
                          "product_name": p["product_name"], "product_url": p.get("product_url"),
                          "reasons": reasons, "last_verified_at": p.get("last_verified_at")})
    incomplete = []
    for row in canonical:
        quality = comparison_quality(country_code=row["country_code"], product_type=row["product_type"],
                                     expected_fields=[], candidate_payload=row["current_snapshot_payload"])
        if not quality.complete:
            incomplete.append({"product_id": row["product_id"], "product_type": row["product_type"],
                               "missing_fields": list(quality.missing_fields)})
    # Deduplicate an official URL before proposing any future paid work.
    shortlist, seen = [], set()
    for item in sorted(items, key=lambda x: ("deposit:basis_unknown" not in x["reasons"], x["bank_code"], x["product_id"])):
        key = item["product_url"] or item["product_id"]
        if key not in seen:
            seen.add(key)
            shortlist.append(item["product_id"])
    return {"published_count": len(rows), "active_canonical_count": len(canonical),
            "gap_counts": dict(Counter(reason for item in items for reason in item["reasons"])),
            "items": items, "incomplete_canonical": incomplete,
            "suggested_product_ids": shortlist[:10]}


def build_report(connection):
    report = {"checked_at": datetime.now(UTC).isoformat(), "model_calls": 0,
              "bank_fetches": 0, "countries": {}}
    for country in ("CA", "US"):
        snapshot = load_latest_public_snapshot(connection, country_code=country)
        rows = load_public_projection_rows(connection, snapshot_id=snapshot["snapshot_id"], country_code=country) if snapshot else []
        canonical = connection.execute("SELECT product_id,country_code,product_type,current_snapshot_payload FROM canonical_product WHERE country_code=%s AND status='active'", (country,)).fetchall()
        report["countries"][country] = {"snapshot_id": snapshot["snapshot_id"] if snapshot else None,
                                        **inspect_rows(rows, canonical)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=str(ROOT / ".env.dev"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open_connection(Settings.from_env(args.env_file)) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        report = build_report(connection)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf8")
    print(json.dumps({country: {k: v for k, v in data.items() if k not in ("items", "incomplete_canonical", "suggested_product_ids")}
                      for country, data in report["countries"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
