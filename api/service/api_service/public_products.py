from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from api_service.public_common import (
    PublicQueryFilters,
    SUPPORTED_LOCALES,
    applied_filters_payload,
    apply_public_filters,
    build_freshness_payload,
    coerce_string_list,
    load_latest_public_snapshot,
    load_public_projection_rows,
    localize_badge,
    localize_bucket,
    localize_product_type,
    localize_subtype,
    localize_target_customer_tag,
    normalize_public_query_filters,
    serialize_datetime,
    serialize_decimal,
)

PRODUCT_SORT_OPTIONS = (
    "default",
    "bank_name",
    "product_name",
    "display_rate",
    "monthly_fee",
    "minimum_balance",
    "minimum_deposit",
    "annual_fee",
    "last_changed_at",
)

_PERCENTAGE_PATTERN = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%")
_INTRO_RATE_PATTERN = re.compile(
    r"(?:(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%\s*(?:intro|introductory)\s+(?:APR|APY)|"
    r"\b(?:intro|introductory)\s+(?:APR|APY)[^.;]{0,16}?(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%)",
    re.IGNORECASE,
)
_RATE_RANGE_PATTERN = re.compile(
    r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%\s*(?:APR|APY)?\s*"
    r"(?:to|through|[-–—])\s*(\d{1,3}(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_RATE_LABEL_PATTERN = re.compile(
    r"\b(?:APR|APY|annual percentage rate|interest rate|fixed rates?|variable rates?|"
    r"loan rates?|mortgage[-\s]+rates?|purchase rates?)\b",
    re.IGNORECASE,
)
_NON_PRODUCT_RATE_CONTEXT_PATTERN = re.compile(
    r"\b(?:discount|down payment|LTV|CLTV|points?|finance charges?|origination fees?|"
    r"maximum|not exceed|rate cap|prime rate was|reference rate|SOFR|index rate)\b",
    re.IGNORECASE,
)
_REFERENCE_SPREAD_PATTERN = re.compile(
    r"(?:prime|SOFR|reference|index)[^.;]{0,24}[+\-]\s*\d{1,3}(?:\.\d+)?\s*%",
    re.IGNORECASE,
)
_REFERENCE_RANGE_PREFIX_PATTERN = re.compile(
    r"(?:prime|SOFR|reference|index)(?:\s+rate)?\s*(?:plus|[+\-])\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PublicProductsQuery:
    filters: PublicQueryFilters
    sort_by: str
    sort_order: str
    page: int
    page_size: int


def normalize_public_products_query(
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
    sort_by: str | None,
    sort_order: str | None,
    page: int,
    page_size: int,
) -> PublicProductsQuery:
    normalized_sort_by = (sort_by or "default").strip().lower()
    if normalized_sort_by not in PRODUCT_SORT_OPTIONS:
        normalized_sort_by = "default"

    normalized_sort_order = "asc" if (sort_order or "").strip().lower() == "asc" else "desc"
    if normalized_sort_by in {"default", "bank_name", "product_name"} and normalized_sort_by != "default":
        normalized_sort_order = "asc" if normalized_sort_order not in {"asc", "desc"} else normalized_sort_order

    return PublicProductsQuery(
        filters=normalize_public_query_filters(
            locale=locale,
            country_code=country_code,
            bank_codes=bank_codes,
            product_types=product_types,
            subtype_codes=subtype_codes,
            target_customer_tags=target_customer_tags,
            fee_bucket=fee_bucket,
            minimum_balance_bucket=minimum_balance_bucket,
            minimum_deposit_bucket=minimum_deposit_bucket,
            term_bucket=term_bucket,
        ),
        sort_by=normalized_sort_by,
        sort_order=normalized_sort_order,
        page=page,
        page_size=page_size,
    )


def load_public_products(connection, *, query: PublicProductsQuery) -> dict[str, Any]:
    snapshot = load_latest_public_snapshot(connection, country_code=query.filters.country_code)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=300)
    if not snapshot:
        return {
            "items": [],
            "applied_filters": applied_filters_payload(query.filters),
            "sort": {"sort_by": query.sort_by, "sort_order": query.sort_order},
            "freshness": freshness,
            "page": query.page,
            "page_size": query.page_size,
            "total_items": 0,
            "total_pages": 0,
            "has_next_page": False,
        }

    rows = load_public_projection_rows(
        connection,
        snapshot_id=str(snapshot["snapshot_id"]),
        country_code=query.filters.country_code,
    )
    filtered_rows = apply_public_filters(rows, filters=query.filters)
    sorted_rows = _sort_rows(filtered_rows, query=query)
    total_items = len(sorted_rows)
    total_pages = (total_items + query.page_size - 1) // query.page_size if total_items else 0
    page_rows = sorted_rows[(query.page - 1) * query.page_size : query.page * query.page_size]

    return {
        "items": [_serialize_product_row(row, locale=query.filters.locale) for row in page_rows],
        "applied_filters": applied_filters_payload(query.filters),
        "sort": {"sort_by": query.sort_by, "sort_order": query.sort_order},
        "freshness": freshness,
        "page": query.page,
        "page_size": query.page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next_page": query.page < total_pages,
    }


def load_public_product_detail(connection, *, product_id: str, filters: PublicQueryFilters) -> dict[str, Any] | None:
    snapshot = load_latest_public_snapshot(connection, country_code=filters.country_code)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=300)
    if not snapshot:
        return None

    rows = load_public_projection_rows(
        connection,
        snapshot_id=str(snapshot["snapshot_id"]),
        country_code=filters.country_code,
    )
    normalized_product_id = product_id.strip()
    product_row = next(
        (row for row in rows if str(row.get("product_id")) == normalized_product_id),
        None,
    )
    if product_row is None:
        return None

    return {
        "product": _serialize_product_row(product_row, locale=filters.locale),
        "applied_filters": applied_filters_payload(filters),
        "freshness": freshness,
    }


def load_public_filters(connection, *, filters: PublicQueryFilters) -> dict[str, Any]:
    countries = load_available_public_countries(connection)
    snapshot = load_latest_public_snapshot(connection, country_code=filters.country_code)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=300)
    if not snapshot:
        return {
            "countries": countries,
            "banks": [],
            "product_types": [],
            "subtypes": [],
            "target_customer_tags": [],
            "fee_buckets": [],
            "minimum_balance_buckets": [],
            "minimum_deposit_buckets": [],
            "term_buckets": [],
            "applied_filters": applied_filters_payload(filters),
            "freshness": freshness,
        }

    rows = load_public_projection_rows(
        connection,
        snapshot_id=str(snapshot["snapshot_id"]),
        country_code=filters.country_code,
    )
    filtered_rows = apply_public_filters(rows, filters=filters)
    locale = filters.locale
    return {
        "countries": countries,
        "banks": _count_labeled_options(
            ((str(row["bank_code"]), str(row["bank_name"])) for row in filtered_rows),
            code_key="code",
            label_key="label",
        ),
        "product_types": _count_labeled_options(
            (
                (
                    str(row["product_type"]),
                    localize_product_type(str(row["product_type"]), locale=locale) or str(row["product_type"]),
                )
                for row in filtered_rows
            ),
            code_key="code",
            label_key="label",
        ),
        "subtypes": _count_subtypes(filtered_rows, locale=locale),
        "target_customer_tags": _count_target_tags(filtered_rows, locale=locale),
        "fee_buckets": _count_bucket_options(filtered_rows, field_name="fee_bucket", locale=locale),
        "minimum_balance_buckets": _count_bucket_options(filtered_rows, field_name="minimum_balance_bucket", locale=locale),
        "minimum_deposit_buckets": _count_bucket_options(filtered_rows, field_name="minimum_deposit_bucket", locale=locale),
        "term_buckets": _count_bucket_options(filtered_rows, field_name="term_bucket", locale=locale),
        "applied_filters": applied_filters_payload(filters),
        "freshness": freshness,
    }


def load_available_public_countries(connection) -> list[dict[str, Any]]:
    """Return countries represented by their latest completed, active public snapshot."""
    rows = connection.execute(
        """
        WITH latest_completed AS (
            SELECT DISTINCT ON (country_code)
                snapshot_id,
                country_code
            FROM aggregate_refresh_run
            WHERE refresh_status = 'completed'
              AND refresh_scope = 'phase1_public'
            ORDER BY
                country_code ASC,
                COALESCE(refreshed_at, attempted_at) DESC,
                attempted_at DESC,
                snapshot_id DESC
        )
        SELECT
            latest_completed.country_code AS code,
            COUNT(projection.product_id)::integer AS count
        FROM latest_completed
        JOIN public_product_projection AS projection
          ON projection.snapshot_id = latest_completed.snapshot_id
         AND projection.country_code = latest_completed.country_code
         AND projection.status = 'active'
        GROUP BY latest_completed.country_code
        ORDER BY latest_completed.country_code ASC
        """,
        {},
    ).fetchall()
    return [
        {
            "code": str(row["code"]).upper(),
            "count": int(row["count"]),
        }
        for row in rows
    ]


def _sort_rows(rows: list[dict[str, Any]], *, query: PublicProductsQuery) -> list[dict[str, Any]]:
    if query.sort_by == "default":
        return sorted(
            rows,
            key=lambda row: (
                str(row.get("bank_name") or ""),
                str(row.get("product_type") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
        )
    if query.sort_by == "bank_name":
        return sorted(
            rows,
            key=lambda row: (
                str(row.get("bank_name") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
            reverse=query.sort_order == "desc",
        )
    if query.sort_by == "product_name":
        return sorted(
            rows,
            key=lambda row: (
                str(row.get("product_name") or ""),
                str(row.get("bank_name") or ""),
                str(row.get("product_id") or ""),
            ),
            reverse=query.sort_order == "desc",
        )
    if query.sort_by == "display_rate":
        return _sort_numeric_rows(
            rows,
            field_name="public_display_rate",
            descending=query.sort_order == "desc",
            value_builder=_card_display_rate,
        )
    if query.sort_by == "monthly_fee":
        return _sort_numeric_rows(rows, field_name="effective_fee", descending=query.sort_order == "desc")
    if query.sort_by == "minimum_balance":
        return _sort_numeric_rows(rows, field_name="minimum_balance", descending=query.sort_order == "desc")
    if query.sort_by == "minimum_deposit":
        return _sort_numeric_rows(rows, field_name="minimum_deposit", descending=query.sort_order == "desc")
    if query.sort_by == "annual_fee":
        def annual_fee(row: dict[str, Any]) -> float | None:
            return serialize_decimal(_coerce_metadata(row.get("refresh_metadata")).get("annual_fee"))

        if query.sort_order == "desc":
            return sorted(
                rows,
                key=lambda row: (
                    annual_fee(row) is None,
                    -(annual_fee(row) or 0.0),
                    str(row.get("bank_name") or ""),
                    str(row.get("product_name") or ""),
                    str(row.get("product_id") or ""),
                ),
            )
        return sorted(
            rows,
            key=lambda row: (
                annual_fee(row) is None,
                annual_fee(row) if annual_fee(row) is not None else float("inf"),
                str(row.get("bank_name") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
        )
    if query.sort_by == "last_changed_at":
        return sorted(
            rows,
            key=lambda row: (
                serialize_datetime(row.get("last_changed_at")) is None,
                serialize_datetime(row.get("last_changed_at")) or "",
                str(row.get("bank_name") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
            reverse=query.sort_order == "desc",
        )
    return rows


def _sort_numeric_rows(
    rows: list[dict[str, Any]],
    *,
    field_name: str,
    descending: bool,
    value_builder: Callable[[dict[str, Any]], float | None] | None = None,
) -> list[dict[str, Any]]:
    def numeric_value(row: dict[str, Any]) -> float | None:
        return value_builder(row) if value_builder is not None else serialize_decimal(row.get(field_name))

    if descending:
        return sorted(
            rows,
            key=lambda row: (
                numeric_value(row) is None,
                -(numeric_value(row) or 0.0),
                str(row.get("bank_name") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
        )
    return sorted(
        rows,
        key=lambda row: (
            numeric_value(row) is None,
            numeric_value(row) if numeric_value(row) is not None else float("inf"),
            str(row.get("bank_name") or ""),
            str(row.get("product_name") or ""),
            str(row.get("product_id") or ""),
        ),
    )


def _serialize_product_row(row: dict[str, Any], *, locale: str) -> dict[str, Any]:
    metadata = _coerce_metadata(row.get("refresh_metadata"))
    target_customer_tags = [str(tag).lower() for tag in coerce_string_list(row.get("target_customer_tags"))]
    badge_code = row.get("product_highlight_badge_code")
    standard_rate = metadata.get("standard_rate")
    base_12_month_rate = metadata.get("base_12_month_rate")
    return {
        "product_id": str(row["product_id"]),
        "bank_code": str(row["bank_code"]),
        "bank_name": str(row["bank_name"]),
        "country_code": str(row["country_code"]),
        "product_family": str(row["product_family"]),
        "product_type": str(row["product_type"]),
        "product_type_label": localize_product_type(str(row["product_type"]), locale=locale),
        "subtype_code": row.get("subtype_code"),
        "subtype_label": localize_subtype(str(row["subtype_code"]), locale=locale) if row.get("subtype_code") else None,
        "product_name": str(row["product_name"]),
        "product_url": row.get("product_url") or None,
        "source_language": str(row["source_language"]),
        "currency": str(row["currency"]),
        "status": str(row["status"]),
        "standard_rate": serialize_decimal(standard_rate),
        "base_12_month_rate": serialize_decimal(base_12_month_rate if base_12_month_rate is not None else standard_rate),
        "public_display_rate": serialize_decimal(row.get("public_display_rate")),
        "card_display_rate": _card_display_rate(row),
        "public_display_fee": serialize_decimal(row.get("effective_fee")),
        "annual_fee": serialize_decimal(metadata.get("annual_fee")),
        "purchase_interest_rate": serialize_decimal(metadata.get("purchase_interest_rate")),
        "purchase_interest_rate_summary": _string_or_none(metadata.get("purchase_interest_rate_summary")),
        "minimum_balance": serialize_decimal(row.get("minimum_balance")),
        "minimum_deposit": serialize_decimal(row.get("minimum_deposit")),
        "fee_waiver_condition": _string_or_none(metadata.get("fee_waiver_condition")),
        "included_transactions": _coerce_int(metadata.get("included_transactions")),
        "unlimited_transactions_flag": _bool_or_none(metadata.get("unlimited_transactions_flag")),
        "redeemable_flag": _bool_or_none(metadata.get("redeemable_flag")),
        "non_redeemable_flag": _bool_or_none(metadata.get("non_redeemable_flag")),
        "early_withdrawal_penalty": _string_or_none(metadata.get("early_withdrawal_penalty")),
        "secured_flag": _bool_or_none(metadata.get("secured_flag")),
        "eligibility_text": _string_or_none(metadata.get("eligibility_text")),
        "application_method": _string_or_none(metadata.get("application_method")),
        "post_maturity_interest_rate": _string_or_none(metadata.get("post_maturity_interest_rate")),
        "tax_benefits": _string_or_none(metadata.get("tax_benefits")),
        "deposit_insurance": _string_or_none(metadata.get("deposit_insurance")),
        "description_short": _string_or_none(metadata.get("description_short")),
        "mortgage_rate": _string_or_none(metadata.get("mortgage_rate")),
        "interest_rate": _string_or_none(metadata.get("interest_rate")),
        "interest_rate_summary": _string_or_none(metadata.get("interest_rate_summary")),
        "rate_type": _string_or_none(metadata.get("rate_type")),
        "term_length_text": _string_or_none(metadata.get("term_length_text")),
        "amortization_text": _string_or_none(metadata.get("amortization_text")),
        "payment_frequency": _string_or_none(metadata.get("payment_frequency")),
        "prepayment_privileges": _string_or_none(metadata.get("prepayment_privileges")),
        "loan_amount_text": _string_or_none(metadata.get("loan_amount_text")),
        "monthly_payment_text": _string_or_none(metadata.get("monthly_payment_text")),
        "credit_limit_text": _string_or_none(metadata.get("credit_limit_text")),
        "security_requirement": _string_or_none(metadata.get("security_requirement")),
        "collateral_text": _string_or_none(metadata.get("collateral_text")),
        "term_rate_table": _serialize_term_rate_table(metadata.get("term_rate_table")),
        "term_length_days": int(row["term_length_days"]) if row.get("term_length_days") is not None else None,
        "product_highlight_badge_code": badge_code,
        "product_highlight_badge_label": localize_badge(str(badge_code), locale=locale) if badge_code else None,
        "target_customer_tags": target_customer_tags,
        "target_customer_tag_labels": [
            localize_target_customer_tag(tag, locale=locale) or tag for tag in target_customer_tags
        ],
        "last_verified_at": serialize_datetime(row.get("last_verified_at")),
        "last_changed_at": serialize_datetime(row.get("last_changed_at")),
    }


def _card_display_rate(row: dict[str, Any]) -> float | None:
    """Return a card-only numeric rate without flattening the stored detail summary."""

    existing_rate = serialize_decimal(row.get("public_display_rate"))
    if str(row.get("product_family") or "").strip().lower() != "lending":
        return existing_rate

    metadata = _coerce_metadata(row.get("refresh_metadata"))
    product_type = str(row.get("product_type") or "").strip().lower()
    candidates: list[float] = []

    if product_type == "credit-card":
        candidates.extend(_explicit_rate_candidates(metadata.get("purchase_interest_rate")))
        candidates.extend(_explicit_rate_candidates(metadata.get("purchase_interest_rate_summary")))
        valid_candidates = [candidate for candidate in candidates if 0 <= candidate <= 100]
        if valid_candidates:
            return min(valid_candidates)
        return existing_rate if existing_rate is not None and 0 <= existing_rate <= 100 else None
    else:
        if existing_rate is not None:
            candidates.append(existing_rate)
        candidates.extend(_explicit_rate_candidates(metadata.get("mortgage_rate")))
        candidates.extend(_explicit_rate_candidates(metadata.get("interest_rate")))
        candidates.extend(_explicit_rate_candidates(metadata.get("interest_rate_summary")))

    valid_candidates = [candidate for candidate in candidates if 0 <= candidate <= 100]
    return min(valid_candidates) if valid_candidates else None


def _explicit_rate_candidates(value: Any) -> list[float]:
    numeric_value = serialize_decimal(value)
    if numeric_value is not None and not isinstance(value, str):
        return [numeric_value]
    if not isinstance(value, str):
        return []

    text = " ".join(value.replace("**", "").replace("__", "").split())
    if not text:
        return []
    plain_numeric = re.fullmatch(r"\s*(\d{1,3}(?:\.\d+)?)\s*%?\s*", text)
    if plain_numeric:
        return [float(plain_numeric.group(1))]

    intro_candidates = [
        float(next(group for group in match.groups() if group is not None))
        for match in _INTRO_RATE_PATTERN.finditer(text)
    ]
    for match in _RATE_RANGE_PATTERN.finditer(text):
        context = text[max(0, match.start() - 48) : min(len(text), match.end() + 48)]
        exclusion_context = text[max(0, match.start() - 28) : min(len(text), match.end() + 32)]
        range_prefix = text[max(0, match.start() - 32) : match.start()]
        if not _RATE_LABEL_PATTERN.search(context):
            continue
        if _NON_PRODUCT_RATE_CONTEXT_PATTERN.search(exclusion_context):
            continue
        if _REFERENCE_RANGE_PREFIX_PATTERN.search(range_prefix):
            continue
        return intro_candidates + [float(match.group(1)), float(match.group(2))]

    candidates = list(intro_candidates)
    for match in _PERCENTAGE_PATTERN.finditer(text):
        context = text[max(0, match.start() - 48) : min(len(text), match.end() + 48)]
        exclusion_context = text[max(0, match.start() - 24) : min(len(text), match.end() + 28)]
        if not _RATE_LABEL_PATTERN.search(context):
            continue
        if _NON_PRODUCT_RATE_CONTEXT_PATTERN.search(exclusion_context) or _REFERENCE_SPREAD_PATTERN.search(exclusion_context):
            continue
        candidates.append(float(match.group(1)))
    return candidates


def _coerce_metadata(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}


def _string_or_none(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    normalized = str(value).strip()
    return normalized or None


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _serialize_term_rate_table(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        term_label = _string_or_none(item.get("term_label"))
        term_length_days = _coerce_int(item.get("term_length_days"))
        rate = serialize_decimal(item.get("rate"))
        minimum_deposit = serialize_decimal(item.get("minimum_deposit"))
        notes = _string_or_none(item.get("notes"))
        if term_label is None and term_length_days is None and rate is None:
            continue
        rows.append(
            {
                "term_label": term_label,
                "term_length_days": term_length_days,
                "rate": rate,
                "minimum_deposit": minimum_deposit,
                "notes": notes,
            }
        )
    return rows


def _coerce_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _count_labeled_options(
    pairs: Iterable[tuple[str, str]],
    *,
    code_key: str,
    label_key: str,
) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for code, label in pairs:
        if not code.strip():
            continue
        counts[(code, label)] = counts.get((code, label), 0) + 1
    items = [
        {
            code_key: code,
            label_key: label,
            "count": count,
        }
        for (code, label), count in counts.items()
    ]
    items.sort(key=lambda item: (-int(item["count"]), str(item[label_key]), str(item[code_key])))
    return items


def _count_subtypes(rows: list[dict[str, Any]], *, locale: str) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        subtype_code = str(row.get("subtype_code") or "").strip().lower()
        if not subtype_code:
            continue
        key = (subtype_code, str(row["product_type"]))
        bucket = counts.setdefault(
            key,
            {
                "code": subtype_code,
                "label": localize_subtype(subtype_code, locale=locale) or subtype_code,
                "product_type": str(row["product_type"]),
                "count": 0,
            },
        )
        bucket["count"] += 1
    items = list(counts.values())
    items.sort(key=lambda item: (-int(item["count"]), str(item["label"]), str(item["code"])))
    return items


def _count_target_tags(rows: list[dict[str, Any]], *, locale: str) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for row in rows:
        for tag in coerce_string_list(row.get("target_customer_tags")):
            normalized = tag.lower()
            bucket = counts.setdefault(
                normalized,
                {
                    "code": normalized,
                    "label": localize_target_customer_tag(normalized, locale=locale) or normalized,
                    "count": 0,
                },
            )
            bucket["count"] += 1
    items = list(counts.values())
    items.sort(key=lambda item: (-int(item["count"]), str(item["label"]), str(item["code"])))
    return items


def _count_bucket_options(rows: list[dict[str, Any]], *, field_name: str, locale: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field_name) or "").strip().lower()
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    items = [
        {
            "code": code,
            "label": localize_bucket(code, locale=locale) or code,
            "count": count,
        }
        for code, count in counts.items()
    ]
    items.sort(key=lambda item: (-int(item["count"]), str(item["label"]), str(item["code"])))
    return items
