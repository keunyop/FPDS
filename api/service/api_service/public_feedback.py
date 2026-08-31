from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Any
from uuid import uuid4


PUBLIC_FEEDBACK_CATEGORIES = {
    "accessibility_issue",
    "broken_link",
    "content_issue",
    "feature_suggestion",
    "incorrect_product_details",
    "incorrect_rate_or_fee",
    "missing_information",
    "other",
    "outdated_information",
    "usability_issue",
}
PRODUCT_ERROR_CATEGORIES = {
    "broken_link",
    "incorrect_product_details",
    "incorrect_rate_or_fee",
    "missing_information",
    "other",
    "outdated_information",
}
SITE_FEEDBACK_CATEGORIES = {
    "accessibility_issue",
    "content_issue",
    "feature_suggestion",
    "other",
    "usability_issue",
}
PUBLIC_FEEDBACK_TYPES = {"product_error", "site_feedback"}
PUBLIC_FEEDBACK_LOCALES = {"en", "ko", "ja"}


class PublicFeedbackRateLimiter:
    def __init__(self, *, limit: int = 120, window_seconds: int = 60) -> None:
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


@dataclass(frozen=True)
class PublicFeedbackFilters:
    country_code: str
    submission_type: str | None
    category: str | None
    search: str | None
    page: int
    page_size: int


def is_feedback_category_allowed(*, submission_type: str, category: str) -> bool:
    normalized_type = submission_type.strip().lower()
    normalized_category = category.strip().lower()
    if normalized_type == "product_error":
        return normalized_category in PRODUCT_ERROR_CATEGORIES
    if normalized_type == "site_feedback":
        return normalized_category in SITE_FEEDBACK_CATEGORIES
    return False


def create_public_feedback_submission(
    connection: Any,
    *,
    country_code: str,
    submission_type: str,
    category: str,
    details: str | None,
    locale: str,
    product_id: str | None,
) -> dict[str, Any] | None:
    normalized_country = country_code.strip().upper()
    normalized_type = submission_type.strip().lower()
    normalized_category = category.strip().lower()
    normalized_details = details.strip() if details and details.strip() else None
    normalized_locale = locale.strip().lower()
    normalized_product_id = product_id.strip() if product_id and product_id.strip() else None

    if (
        len(normalized_country) != 2
        or not normalized_country.isalpha()
        or normalized_type not in PUBLIC_FEEDBACK_TYPES
        or normalized_category not in PUBLIC_FEEDBACK_CATEGORIES
        or not is_feedback_category_allowed(
            submission_type=normalized_type,
            category=normalized_category,
        )
        or normalized_locale not in PUBLIC_FEEDBACK_LOCALES
        or (normalized_details is not None and len(normalized_details) > 2000)
        or (normalized_type == "product_error" and not normalized_product_id)
        or (normalized_type == "site_feedback" and normalized_product_id is not None)
    ):
        return None

    params = {
        "category": normalized_category,
        "country_code": normalized_country,
        "details": normalized_details,
        "locale": normalized_locale,
        "product_id": normalized_product_id,
        "submission_id": f"feedback_{uuid4().hex}",
        "submission_type": normalized_type,
        "submitted_at": datetime.now(UTC),
    }
    row = (
        _insert_product_feedback(connection, params=params)
        if normalized_type == "product_error"
        else _insert_site_feedback(connection, params=params)
    )
    return _serialize_feedback_row(row) if row else None


def _insert_product_feedback(connection: Any, *, params: dict[str, Any]) -> dict[str, Any] | None:
    return connection.execute(
        """
        INSERT INTO public_feedback_submission (
            submission_id,
            submitted_at,
            country_code,
            submission_type,
            category,
            details,
            locale,
            snapshot_id,
            product_id,
            bank_code,
            bank_name,
            product_name,
            product_type
        )
        SELECT
            %(submission_id)s,
            %(submitted_at)s,
            %(country_code)s,
            %(submission_type)s,
            %(category)s,
            %(details)s,
            %(locale)s,
            projection.snapshot_id,
            projection.product_id,
            projection.bank_code,
            projection.bank_name,
            projection.product_name,
            projection.product_type
        FROM public_product_projection AS projection
        WHERE projection.snapshot_id = (
            SELECT snapshot_id
            FROM aggregate_refresh_run
            WHERE country_code = %(country_code)s
              AND refresh_status = 'completed'
            ORDER BY COALESCE(refreshed_at, attempted_at) DESC,
                     attempted_at DESC,
                     snapshot_id DESC
            LIMIT 1
        )
          AND projection.country_code = %(country_code)s
          AND projection.status = 'active'
          AND projection.product_id = %(product_id)s
        RETURNING *
        """,
        params,
    ).fetchone()


def _insert_site_feedback(connection: Any, *, params: dict[str, Any]) -> dict[str, Any] | None:
    return connection.execute(
        """
        INSERT INTO public_feedback_submission (
            submission_id,
            submitted_at,
            country_code,
            submission_type,
            category,
            details,
            locale
        )
        SELECT
            %(submission_id)s,
            %(submitted_at)s,
            country_registry.country_code,
            %(submission_type)s,
            %(category)s,
            %(details)s,
            %(locale)s
        FROM country_registry
        WHERE country_registry.country_code = %(country_code)s
          AND country_registry.status = 'active'
        RETURNING *
        """,
        params,
    ).fetchone()


def normalize_public_feedback_filters(
    *,
    country_code: str,
    submission_type: str | None,
    category: str | None,
    search: str | None,
    page: int,
    page_size: int,
) -> PublicFeedbackFilters:
    normalized_country = country_code.strip().upper()
    normalized_type = submission_type.strip().lower() if submission_type else None
    normalized_category = category.strip().lower() if category else None
    normalized_search = search.strip() if search and search.strip() else None
    return PublicFeedbackFilters(
        country_code=normalized_country,
        submission_type=normalized_type if normalized_type in PUBLIC_FEEDBACK_TYPES else None,
        category=normalized_category if normalized_category in PUBLIC_FEEDBACK_CATEGORIES else None,
        search=normalized_search,
        page=max(1, page),
        page_size=min(100, max(1, page_size)),
    )


def load_public_feedback_submissions(
    connection: Any,
    *,
    filters: PublicFeedbackFilters,
) -> dict[str, Any]:
    params = {
        "category": filters.category,
        "country_code": filters.country_code,
        "limit": filters.page_size,
        "offset": (filters.page - 1) * filters.page_size,
        "search_pattern": f"%{filters.search}%" if filters.search else None,
        "submission_type": filters.submission_type,
    }
    where_sql = """
        country_code = %(country_code)s
        AND (%(submission_type)s::text IS NULL OR submission_type = %(submission_type)s)
        AND (%(category)s::text IS NULL OR category = %(category)s)
        AND (
            %(search_pattern)s::text IS NULL
            OR COALESCE(details, '') ILIKE %(search_pattern)s
            OR COALESCE(product_name, '') ILIKE %(search_pattern)s
            OR COALESCE(bank_name, '') ILIKE %(search_pattern)s
            OR category ILIKE %(search_pattern)s
            OR submission_id ILIKE %(search_pattern)s
        )
    """
    summary = connection.execute(
        f"""
        SELECT
            COUNT(*) AS total_items,
            COUNT(*) FILTER (WHERE submission_type = 'product_error') AS product_error_items,
            COUNT(*) FILTER (WHERE submission_type = 'site_feedback') AS site_feedback_items
        FROM public_feedback_submission
        WHERE {where_sql}
        """,
        params,
    ).fetchone() or {}
    rows = connection.execute(
        f"""
        SELECT *
        FROM public_feedback_submission
        WHERE {where_sql}
        ORDER BY submitted_at DESC, submission_id DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    ).fetchall()
    total_items = int(summary.get("total_items") or 0)
    total_pages = max(1, (total_items + filters.page_size - 1) // filters.page_size)
    return {
        "items": [_serialize_feedback_row(row) for row in rows],
        "summary": {
            "total_items": total_items,
            "product_error_items": int(summary.get("product_error_items") or 0),
            "site_feedback_items": int(summary.get("site_feedback_items") or 0),
        },
        "applied_filters": {
            "submission_type": filters.submission_type,
            "category": filters.category,
            "search": filters.search,
        },
        "page": filters.page,
        "page_size": filters.page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next_page": filters.page < total_pages,
    }


def _serialize_feedback_row(row: dict[str, Any]) -> dict[str, Any]:
    submitted_at = row.get("submitted_at")
    if isinstance(submitted_at, datetime):
        parsed = submitted_at if submitted_at.tzinfo else submitted_at.replace(tzinfo=UTC)
        serialized_submitted_at = parsed.astimezone(UTC).isoformat()
    else:
        serialized_submitted_at = str(submitted_at) if submitted_at else None
    return {
        "submission_id": str(row.get("submission_id") or ""),
        "submitted_at": serialized_submitted_at,
        "country_code": str(row.get("country_code") or "").upper(),
        "submission_type": str(row.get("submission_type") or ""),
        "category": str(row.get("category") or ""),
        "details": str(row["details"]) if row.get("details") is not None else None,
        "locale": str(row.get("locale") or "en"),
        "snapshot_id": str(row["snapshot_id"]) if row.get("snapshot_id") else None,
        "product": (
            {
                "product_id": str(row.get("product_id") or ""),
                "bank_code": str(row.get("bank_code") or ""),
                "bank_name": str(row.get("bank_name") or ""),
                "product_name": str(row.get("product_name") or ""),
                "product_type": str(row.get("product_type") or ""),
            }
            if row.get("product_id")
            else None
        ),
    }
