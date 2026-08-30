from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Any


PUBLIC_ENGAGEMENT_EVENT_TYPES = {
    "finder_product_selected",
    "official_bank_click",
    "product_detail_click",
}


class PublicEngagementRateLimiter:
    def __init__(self, *, limit: int = 600, window_seconds: int = 60) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._events: deque[float] = deque()
        self._lock = Lock()

    def allow(self) -> bool:
        now = monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            while self._events and self._events[0] <= cutoff:
                self._events.popleft()
            if len(self._events) >= self._limit:
                return False
            self._events.append(now)
            return True


def record_public_product_engagement(
    connection: Any,
    *,
    country_code: str,
    product_id: str,
    event_type: str,
) -> bool:
    normalized_country = country_code.strip().upper()
    normalized_product_id = product_id.strip()
    normalized_event_type = event_type.strip().lower()
    if (
        len(normalized_country) != 2
        or not normalized_country.isalpha()
        or not normalized_product_id
        or normalized_event_type not in PUBLIC_ENGAGEMENT_EVENT_TYPES
    ):
        return False

    row = connection.execute(
        """
        WITH latest_completed AS (
            SELECT snapshot_id
            FROM aggregate_refresh_run
            WHERE country_code = %(country_code)s
              AND refresh_status = 'completed'
            ORDER BY COALESCE(refreshed_at, attempted_at) DESC, attempted_at DESC, snapshot_id DESC
            LIMIT 1
        ),
        eligible_product AS (
            SELECT projection.product_id
            FROM latest_completed
            JOIN public_product_projection AS projection
              ON projection.snapshot_id = latest_completed.snapshot_id
             AND projection.country_code = %(country_code)s
             AND projection.status = 'active'
            WHERE projection.product_id = %(product_id)s
        )
        INSERT INTO public_product_engagement_daily (
            event_date,
            country_code,
            product_id,
            event_type,
            event_count,
            first_recorded_at,
            last_recorded_at
        )
        SELECT
            %(event_date)s,
            %(country_code)s,
            eligible_product.product_id,
            %(event_type)s,
            1,
            %(recorded_at)s,
            %(recorded_at)s
        FROM eligible_product
        ON CONFLICT (event_date, country_code, product_id, event_type)
        DO UPDATE SET
            event_count = public_product_engagement_daily.event_count + 1,
            last_recorded_at = EXCLUDED.last_recorded_at
        RETURNING product_id
        """,
        {
            "country_code": normalized_country,
            "event_date": datetime.now(UTC).date(),
            "event_type": normalized_event_type,
            "product_id": normalized_product_id,
            "recorded_at": datetime.now(UTC),
        },
    ).fetchone()
    return row is not None


def load_public_product_engagement_summary(
    connection: Any,
    *,
    country_code: str | None,
) -> dict[str, Any]:
    normalized_country = _normalize_country(country_code)
    params = {"country_code": normalized_country}
    totals = connection.execute(
        """
        SELECT
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'product_detail_click'), 0) AS product_detail_clicks,
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'official_bank_click'), 0) AS official_bank_clicks,
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'finder_product_selected'), 0) AS finder_product_selections,
            MIN(event_date) AS first_event_date,
            MAX(last_recorded_at) AS last_recorded_at
        FROM public_product_engagement_daily
        WHERE event_date >= current_date - 399
          AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s)
        """,
        params,
    ).fetchone() or {}
    product_rows = connection.execute(
        """
        WITH latest_completed AS (
            SELECT DISTINCT ON (country_code)
                country_code,
                snapshot_id
            FROM aggregate_refresh_run
            WHERE refresh_status = 'completed'
              AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s)
            ORDER BY
                country_code,
                COALESCE(refreshed_at, attempted_at) DESC,
                attempted_at DESC,
                snapshot_id DESC
        ),
        engagement AS (
            SELECT
                country_code,
                product_id,
                SUM(event_count) FILTER (WHERE event_type = 'product_detail_click') AS product_detail_clicks,
                SUM(event_count) FILTER (WHERE event_type = 'official_bank_click') AS official_bank_clicks,
                SUM(event_count) FILTER (WHERE event_type = 'finder_product_selected') AS finder_product_selections,
                MAX(last_recorded_at) AS last_recorded_at
            FROM public_product_engagement_daily
            WHERE event_date >= current_date - 399
              AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s)
            GROUP BY country_code, product_id
        )
        SELECT
            projection.country_code,
            projection.product_id,
            projection.bank_code,
            projection.bank_name,
            projection.product_name,
            projection.product_type,
            COALESCE(engagement.product_detail_clicks, 0) AS product_detail_clicks,
            COALESCE(engagement.official_bank_clicks, 0) AS official_bank_clicks,
            COALESCE(engagement.finder_product_selections, 0) AS finder_product_selections,
            engagement.last_recorded_at
        FROM latest_completed
        JOIN public_product_projection AS projection
          ON projection.snapshot_id = latest_completed.snapshot_id
         AND projection.country_code = latest_completed.country_code
         AND projection.status = 'active'
        LEFT JOIN engagement
          ON engagement.country_code = projection.country_code
         AND engagement.product_id = projection.product_id
        ORDER BY
            COALESCE(engagement.finder_product_selections, 0) DESC,
            COALESCE(engagement.product_detail_clicks, 0) DESC,
            COALESCE(engagement.official_bank_clicks, 0) DESC,
            projection.product_name ASC,
            projection.product_id ASC
        """,
        params,
    ).fetchall()
    daily_rows = connection.execute(
        """
        SELECT
            event_date,
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'product_detail_click'), 0) AS product_detail_clicks,
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'official_bank_click'), 0) AS official_bank_clicks,
            COALESCE(SUM(event_count) FILTER (WHERE event_type = 'finder_product_selected'), 0) AS finder_product_selections
        FROM public_product_engagement_daily
        WHERE event_date >= current_date - 29
          AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s)
        GROUP BY event_date
        ORDER BY event_date ASC
        """,
        params,
    ).fetchall()

    products = [_serialize_product_row(row) for row in product_rows]
    return {
        "country_code": normalized_country,
        "retention_days": 400,
        "totals": {
            "product_detail_clicks": int(totals.get("product_detail_clicks") or 0),
            "official_bank_clicks": int(totals.get("official_bank_clicks") or 0),
            "finder_product_selections": int(totals.get("finder_product_selections") or 0),
            "published_products": len(products),
            "first_event_date": _serialize_date(totals.get("first_event_date")),
            "last_recorded_at": _serialize_datetime(totals.get("last_recorded_at")),
        },
        "products": products,
        "banks": _build_bank_rows(products),
        "daily": [
            {
                "event_date": _serialize_date(row.get("event_date")),
                "product_detail_clicks": int(row.get("product_detail_clicks") or 0),
                "official_bank_clicks": int(row.get("official_bank_clicks") or 0),
                "finder_product_selections": int(row.get("finder_product_selections") or 0),
            }
            for row in daily_rows
        ],
    }


def _normalize_country(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().upper()
    return normalized if len(normalized) == 2 and normalized.isalpha() else None


def _serialize_product_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "country_code": str(row.get("country_code") or "").upper(),
        "product_id": str(row.get("product_id") or ""),
        "bank_code": str(row.get("bank_code") or ""),
        "bank_name": str(row.get("bank_name") or ""),
        "product_name": str(row.get("product_name") or ""),
        "product_type": str(row.get("product_type") or ""),
        "product_detail_clicks": int(row.get("product_detail_clicks") or 0),
        "official_bank_clicks": int(row.get("official_bank_clicks") or 0),
        "finder_product_selections": int(row.get("finder_product_selections") or 0),
        "last_recorded_at": _serialize_datetime(row.get("last_recorded_at")),
    }


def _build_bank_rows(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_bank: dict[tuple[str, str], dict[str, Any]] = {}
    for product in products:
        key = (product["country_code"], product["bank_code"])
        row = by_bank.setdefault(
            key,
            {
                "country_code": product["country_code"],
                "bank_code": product["bank_code"],
                "bank_name": product["bank_name"],
                "product_detail_clicks": 0,
                "official_bank_clicks": 0,
                "finder_product_selections": 0,
            },
        )
        for field in (
            "product_detail_clicks",
            "official_bank_clicks",
            "finder_product_selections",
        ):
            row[field] += int(product[field])
    return sorted(
        by_bank.values(),
        key=lambda row: (
            -int(row["official_bank_clicks"]),
            -int(row["product_detail_clicks"]),
            str(row["bank_name"]),
        ),
    )


def _serialize_date(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else (str(value) if value else None)


def _serialize_datetime(value: Any) -> str | None:
    if isinstance(value, datetime):
        parsed = value if value.tzinfo else value.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    return str(value) if value else None
