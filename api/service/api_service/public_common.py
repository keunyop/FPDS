from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection

SUPPORTED_LOCALES = ("en", "ko", "ja")
SUPPORTED_PRODUCT_TYPES = ("chequing", "savings", "gic")
SUPPORTED_FEE_BUCKETS = ("free", "low_fee", "high_fee")
SUPPORTED_MINIMUM_BALANCE_BUCKETS = ("none", "under_1000", "from_1000_to_4999", "5000_plus")
SUPPORTED_MINIMUM_DEPOSIT_BUCKETS = ("none", "under_500", "from_500_to_4999", "5000_plus")
SUPPORTED_TERM_BUCKETS = ("under_1y", "from_1y_to_3y", "over_3y")

PRODUCT_TYPE_LABELS = {
    "en": {
        "chequing": "Chequing",
        "savings": "Savings",
        "gic": "GIC",
    },
    "ko": {
        "chequing": "입출금",
        "savings": "저축",
        "gic": "GIC",
    },
    "ja": {
        "chequing": "当座預金",
        "savings": "貯蓄預金",
        "gic": "GIC",
    },
}

SUBTYPE_LABELS = {
    "en": {
        "standard": "Standard",
        "package": "Package",
        "interest_bearing": "Interest Bearing",
        "premium": "Premium",
        "other": "Other",
        "high_interest": "High Interest",
        "redeemable": "Redeemable",
        "non_redeemable": "Non-Redeemable",
    },
    "ko": {
        "standard": "기본형",
        "package": "패키지형",
        "interest_bearing": "이자지급형",
        "premium": "프리미엄",
        "other": "기타",
        "high_interest": "고금리",
        "redeemable": "중도해지 가능",
        "non_redeemable": "중도해지 불가",
    },
    "ja": {
        "standard": "標準",
        "package": "パッケージ",
        "interest_bearing": "利付",
        "premium": "プレミアム",
        "other": "その他",
        "high_interest": "高金利",
        "redeemable": "中途解約可",
        "non_redeemable": "中途解約不可",
    },
}

TARGET_CUSTOMER_TAG_LABELS = {
    "en": {
        "student": "Student",
        "newcomer": "Newcomer",
        "youth": "Youth",
        "senior": "Senior",
        "business": "Business",
    },
    "ko": {
        "student": "학생",
        "newcomer": "신규 이주자",
        "youth": "청년",
        "senior": "시니어",
        "business": "비즈니스",
    },
    "ja": {
        "student": "学生",
        "newcomer": "新規移住者",
        "youth": "若年層",
        "senior": "シニア",
        "business": "ビジネス",
    },
}

BADGE_LABELS = {
    "en": {
        "high_rate": "High Rate",
        "no_monthly_fee": "No Monthly Fee",
        "low_minimum_deposit": "Low Minimum Deposit",
        "recently_changed": "Recently Changed",
    },
    "ko": {
        "high_rate": "고금리",
        "no_monthly_fee": "월 수수료 없음",
        "low_minimum_deposit": "낮은 최소 예치금",
        "recently_changed": "최근 변경",
    },
    "ja": {
        "high_rate": "高金利",
        "no_monthly_fee": "月額手数料なし",
        "low_minimum_deposit": "低い最低預入額",
        "recently_changed": "最近更新",
    },
}

BUCKET_LABELS = {
    "en": {
        "free": "Free",
        "low_fee": "Low Fee",
        "high_fee": "High Fee",
        "none": "None",
        "under_1000": "Under 1,000 CAD",
        "from_1000_to_4999": "1,000 to 4,999 CAD",
        "5000_plus": "5,000+ CAD",
        "under_500": "Under 500 CAD",
        "from_500_to_4999": "500 to 4,999 CAD",
        "under_1y": "Under 1 Year",
        "from_1y_to_3y": "1 to 3 Years",
        "over_3y": "Over 3 Years",
    },
    "ko": {
        "free": "무료",
        "low_fee": "저수수료",
        "high_fee": "고수수료",
        "none": "없음",
        "under_1000": "1,000 CAD 미만",
        "from_1000_to_4999": "1,000~4,999 CAD",
        "5000_plus": "5,000 CAD 이상",
        "under_500": "500 CAD 미만",
        "from_500_to_4999": "500~4,999 CAD",
        "under_1y": "1년 미만",
        "from_1y_to_3y": "1년~3년",
        "over_3y": "3년 초과",
    },
    "ja": {
        "free": "無料",
        "low_fee": "低手数料",
        "high_fee": "高手数料",
        "none": "なし",
        "under_1000": "1,000 CAD未満",
        "from_1000_to_4999": "1,000〜4,999 CAD",
        "5000_plus": "5,000 CAD以上",
        "under_500": "500 CAD未満",
        "from_500_to_4999": "500〜4,999 CAD",
        "under_1y": "1年未満",
        "from_1y_to_3y": "1年〜3年",
        "over_3y": "3年超",
    },
}


@dataclass(frozen=True)
class PublicQueryFilters:
    locale: str
    country_code: str
    bank_codes: tuple[str, ...]
    product_types: tuple[str, ...]
    subtype_codes: tuple[str, ...]
    target_customer_tags: tuple[str, ...]
    fee_bucket: str | None
    minimum_balance_bucket: str | None
    minimum_deposit_bucket: str | None
    term_bucket: str | None


def normalize_public_query_filters(
    *,
    locale: str | None,
    country_code: str | None,
    bank_codes: Iterable[str] | None,
    product_types: Iterable[str] | None,
    subtype_codes: Iterable[str] | None,
    target_customer_tags: Iterable[str] | None,
    fee_bucket: str | None,
    minimum_balance_bucket: str | None,
    minimum_deposit_bucket: str | None,
    term_bucket: str | None,
) -> PublicQueryFilters:
    normalized_locale = (locale or "en").strip().lower()
    if normalized_locale not in SUPPORTED_LOCALES:
        normalized_locale = "en"

    normalized_country_code = (country_code or "CA").strip().upper() or "CA"

    normalized_product_types = tuple(
        value
        for value in _normalize_codes(product_types)
        if value in SUPPORTED_PRODUCT_TYPES
    )

    return PublicQueryFilters(
        locale=normalized_locale,
        country_code=normalized_country_code,
        bank_codes=tuple(code.upper() for code in _normalize_codes(bank_codes)),
        product_types=normalized_product_types,
        subtype_codes=_normalize_codes(subtype_codes),
        target_customer_tags=_normalize_codes(target_customer_tags),
        fee_bucket=_normalize_bucket(fee_bucket, SUPPORTED_FEE_BUCKETS),
        minimum_balance_bucket=_normalize_bucket(minimum_balance_bucket, SUPPORTED_MINIMUM_BALANCE_BUCKETS),
        minimum_deposit_bucket=_normalize_bucket(minimum_deposit_bucket, SUPPORTED_MINIMUM_DEPOSIT_BUCKETS),
        term_bucket=_normalize_bucket(term_bucket, SUPPORTED_TERM_BUCKETS),
    )


def load_latest_public_snapshot(connection: Connection, *, country_code: str) -> dict[str, Any] | None:
    latest_success = connection.execute(
        """
        SELECT
            snapshot_id,
            refresh_scope,
            country_code,
            refresh_status,
            source_change_cutoff_at,
            attempted_at,
            refreshed_at,
            stale_flag,
            error_summary,
            refresh_metadata
        FROM aggregate_refresh_run
        WHERE country_code = %(country_code)s
          AND refresh_status = 'completed'
        ORDER BY COALESCE(refreshed_at, attempted_at) DESC, attempted_at DESC, snapshot_id DESC
        LIMIT 1
        """,
        {"country_code": country_code},
    ).fetchone()
    if not latest_success:
        return None

    latest_attempt = connection.execute(
        """
        SELECT
            snapshot_id,
            refresh_status,
            attempted_at,
            refreshed_at,
            error_summary
        FROM aggregate_refresh_run
        WHERE country_code = %(country_code)s
        ORDER BY COALESCE(attempted_at, refreshed_at) DESC, snapshot_id DESC
        LIMIT 1
        """,
        {"country_code": country_code},
    ).fetchone()
    latest_success["latest_attempt"] = latest_attempt
    return latest_success


def load_public_projection_rows(
    connection: Connection,
    *,
    snapshot_id: str,
    country_code: str,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            product_id,
            bank_code,
            bank_name,
            country_code,
            product_family,
            product_type,
            subtype_code,
            product_name,
            source_language,
            currency,
            status,
            public_display_rate,
            public_display_fee,
            monthly_fee,
            effective_fee,
            minimum_balance,
            minimum_deposit,
            term_length_days,
            product_highlight_badge_code,
            COALESCE(target_customer_tags, '[]'::jsonb) AS target_customer_tags,
            fee_bucket,
            minimum_balance_bucket,
            minimum_deposit_bucket,
            term_bucket,
            last_verified_at,
            last_changed_at,
            COALESCE(refresh_metadata, '{}'::jsonb) AS refresh_metadata
        FROM public_product_projection
        WHERE snapshot_id = %(snapshot_id)s
          AND country_code = %(country_code)s
          AND status = 'active'
        ORDER BY bank_name ASC, product_name ASC, product_id ASC
        """,
        {"snapshot_id": snapshot_id, "country_code": country_code},
    ).fetchall()
    return [dict(row) for row in rows]


def apply_public_filters(rows: list[dict[str, Any]], *, filters: PublicQueryFilters) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if filters.bank_codes and str(row.get("bank_code") or "").upper() not in filters.bank_codes:
            continue
        if filters.product_types and str(row.get("product_type") or "").lower() not in filters.product_types:
            continue
        if filters.subtype_codes and str(row.get("subtype_code") or "").lower() not in filters.subtype_codes:
            continue
        if filters.target_customer_tags:
            row_tags = {str(tag).lower() for tag in _coerce_string_list(row.get("target_customer_tags"))}
            if not row_tags.intersection(filters.target_customer_tags):
                continue
        if filters.fee_bucket and str(row.get("fee_bucket") or "").lower() != filters.fee_bucket:
            continue
        if filters.minimum_balance_bucket and str(row.get("minimum_balance_bucket") or "").lower() != filters.minimum_balance_bucket:
            continue
        if filters.minimum_deposit_bucket and str(row.get("minimum_deposit_bucket") or "").lower() != filters.minimum_deposit_bucket:
            continue
        if filters.term_bucket and str(row.get("term_bucket") or "").lower() != filters.term_bucket:
            continue
        filtered.append(row)
    return filtered


def build_freshness_payload(snapshot: dict[str, Any] | None, *, cache_ttl_sec: int) -> dict[str, Any]:
    if not snapshot:
        return {
            "snapshot_id": None,
            "refreshed_at": None,
            "source_change_cutoff_at": None,
            "cache_ttl_sec": cache_ttl_sec,
            "status": "unavailable",
        }

    latest_attempt = snapshot.get("latest_attempt") if isinstance(snapshot.get("latest_attempt"), dict) else {}
    refreshed_at = snapshot.get("refreshed_at")
    status = "fresh"
    if bool(snapshot.get("stale_flag")):
        status = "stale"
    elif latest_attempt:
        latest_attempt_status = str(latest_attempt.get("refresh_status") or "").lower()
        latest_attempt_time = _as_datetime(latest_attempt.get("attempted_at") or latest_attempt.get("refreshed_at"))
        refreshed_time = _as_datetime(refreshed_at or snapshot.get("attempted_at"))
        if latest_attempt_status == "failed" and latest_attempt_time and refreshed_time and latest_attempt_time > refreshed_time:
            status = "stale"

    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "refreshed_at": _serialize_datetime(refreshed_at),
        "source_change_cutoff_at": _serialize_datetime(snapshot.get("source_change_cutoff_at")),
        "cache_ttl_sec": cache_ttl_sec,
        "status": status,
        "latest_attempted_at": _serialize_datetime(latest_attempt.get("attempted_at")) if latest_attempt else None,
        "latest_error_summary": latest_attempt.get("error_summary") if latest_attempt and status == "stale" else None,
    }


def applied_filters_payload(filters: PublicQueryFilters) -> dict[str, Any]:
    return {
        "locale": filters.locale,
        "country_code": filters.country_code,
        "bank_code": list(filters.bank_codes),
        "product_type": list(filters.product_types),
        "subtype_code": list(filters.subtype_codes),
        "target_customer_tag": list(filters.target_customer_tags),
        "fee_bucket": filters.fee_bucket,
        "minimum_balance_bucket": filters.minimum_balance_bucket,
        "minimum_deposit_bucket": filters.minimum_deposit_bucket,
        "term_bucket": filters.term_bucket,
    }


def localize_product_type(product_type: str | None, *, locale: str) -> str | None:
    if not product_type:
        return None
    normalized = product_type.strip().lower()
    return PRODUCT_TYPE_LABELS.get(locale, PRODUCT_TYPE_LABELS["en"]).get(normalized, _humanize_code(normalized))


def localize_subtype(subtype_code: str | None, *, locale: str) -> str | None:
    if not subtype_code:
        return None
    normalized = subtype_code.strip().lower()
    return SUBTYPE_LABELS.get(locale, SUBTYPE_LABELS["en"]).get(normalized, _humanize_code(normalized))


def localize_target_customer_tag(tag_code: str | None, *, locale: str) -> str | None:
    if not tag_code:
        return None
    normalized = tag_code.strip().lower()
    return TARGET_CUSTOMER_TAG_LABELS.get(locale, TARGET_CUSTOMER_TAG_LABELS["en"]).get(
        normalized,
        _humanize_code(normalized),
    )


def localize_badge(badge_code: str | None, *, locale: str) -> str | None:
    if not badge_code:
        return None
    normalized = badge_code.strip().lower()
    return BADGE_LABELS.get(locale, BADGE_LABELS["en"]).get(normalized, _humanize_code(normalized))


def localize_bucket(bucket_code: str | None, *, locale: str) -> str | None:
    if not bucket_code:
        return None
    normalized = bucket_code.strip().lower()
    return BUCKET_LABELS.get(locale, BUCKET_LABELS["en"]).get(normalized, _humanize_code(normalized))


def serialize_decimal(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def serialize_datetime(value: Any) -> str | None:
    return _serialize_datetime(value)


def coerce_string_list(value: Any) -> list[str]:
    return _coerce_string_list(value)


def _normalize_codes(values: Iterable[str] | None) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for raw in values or []:
        normalized = " ".join(str(raw).strip().lower().split())
        if not normalized:
            continue
        seen.setdefault(normalized, None)
    return tuple(seen.keys())


def _normalize_bucket(value: str | None, allowed: tuple[str, ...]) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized if normalized in allowed else None


def _humanize_code(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _serialize_datetime(value: Any) -> str | None:
    parsed = _as_datetime(value)
    return parsed.isoformat() if parsed else None
