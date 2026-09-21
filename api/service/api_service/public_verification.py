"""Read-time product verification; never mutates canonical or collection state."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

# Initial operating defaults for warning/reporting only; no availability or collection changes.
# (recheck due after elapsed UTC days, verification expires after elapsed UTC days)
VERIFICATION_POLICY: dict[str, tuple[int, int]] = {
    "chequing": (30, 90),
    "credit-card": (30, 90),
    "savings": (7, 30),
    "gic": (7, 30),
    "mortgage": (7, 30),
    "personal-loan": (7, 30),
    "line-of-credit": (7, 30),
}


def as_utc(value: Any) -> datetime | None:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    try:
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    except (OverflowError, ValueError):
        return None


def product_verification(row: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = as_utc(now) or datetime.now(UTC)
    checked = as_utc(row.get("last_verified_at"))
    policy = VERIFICATION_POLICY.get(str(row.get("product_type") or ""))
    result = {
        "status": "unknown", "last_verified_at": None,
        "review_due_at": None, "expires_at": None,
        "review_interval_days": policy[0] if policy else None,
        "expiry_days": policy[1] if policy else None,
        "evaluated_at": now.isoformat(),
    }
    if checked is None or checked > now:
        return result
    result["last_verified_at"] = checked.isoformat()
    if policy is None:
        return result
    try:
        due = checked + timedelta(days=policy[0])
        expiry = checked + timedelta(days=policy[1])
    except OverflowError:
        return result
    result.update(
        status="expired" if now >= expiry else "review_due" if now >= due else "within_window",
        review_due_at=due.isoformat(), expires_at=expiry.isoformat(),
    )
    return result


def verification_summary(rows: list[dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
    now = as_utc(now) or datetime.now(UTC)
    counts = dict.fromkeys(("within_window", "review_due", "expired", "unknown"), 0)
    for row in rows:
        counts[product_verification(row, now=now)["status"]] += 1
    return {"total_products": len(rows), "counts": counts, "evaluated_at": now.isoformat()}


def overdue_products(rows: list[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    now = as_utc(now) or datetime.now(UTC)
    items = []
    for row in rows:
        verification = product_verification(row, now=now)
        if verification["status"] == "within_window":
            continue
        items.append({
            **{key: row.get(key) for key in (
                "product_id", "country_code", "bank_code", "bank_name", "product_type", "product_name", "product_url"
            )},
            **verification,
        })
    priority = {"expired": 0, "unknown": 1, "review_due": 2}
    return sorted(items, key=lambda item: (
        priority[item["status"]], item["review_due_at"] or "", str(item["product_id"])
    ))
