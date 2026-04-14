from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

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
    "last_changed_at",
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


def load_public_filters(connection, *, filters: PublicQueryFilters) -> dict[str, Any]:
    snapshot = load_latest_public_snapshot(connection, country_code=filters.country_code)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=300)
    if not snapshot:
        return {
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
        return _sort_numeric_rows(rows, field_name="public_display_rate", descending=query.sort_order == "desc")
    if query.sort_by == "monthly_fee":
        return _sort_numeric_rows(rows, field_name="effective_fee", descending=query.sort_order == "desc")
    if query.sort_by == "minimum_balance":
        return _sort_numeric_rows(rows, field_name="minimum_balance", descending=query.sort_order == "desc")
    if query.sort_by == "minimum_deposit":
        return _sort_numeric_rows(rows, field_name="minimum_deposit", descending=query.sort_order == "desc")
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


def _sort_numeric_rows(rows: list[dict[str, Any]], *, field_name: str, descending: bool) -> list[dict[str, Any]]:
    if descending:
        return sorted(
            rows,
            key=lambda row: (
                row.get(field_name) is None,
                -(serialize_decimal(row.get(field_name)) or 0.0),
                str(row.get("bank_name") or ""),
                str(row.get("product_name") or ""),
                str(row.get("product_id") or ""),
            ),
        )
    return sorted(
        rows,
        key=lambda row: (
            row.get(field_name) is None,
            serialize_decimal(row.get(field_name)) if row.get(field_name) is not None else float("inf"),
            str(row.get("bank_name") or ""),
            str(row.get("product_name") or ""),
            str(row.get("product_id") or ""),
        ),
    )


def _serialize_product_row(row: dict[str, Any], *, locale: str) -> dict[str, Any]:
    target_customer_tags = [str(tag).lower() for tag in coerce_string_list(row.get("target_customer_tags"))]
    badge_code = row.get("product_highlight_badge_code")
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
        "source_language": str(row["source_language"]),
        "currency": str(row["currency"]),
        "status": str(row["status"]),
        "public_display_rate": serialize_decimal(row.get("public_display_rate")),
        "public_display_fee": serialize_decimal(row.get("effective_fee")),
        "minimum_balance": serialize_decimal(row.get("minimum_balance")),
        "minimum_deposit": serialize_decimal(row.get("minimum_deposit")),
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
