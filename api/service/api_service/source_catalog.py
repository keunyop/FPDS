from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import path guard for `uv run --directory api/service`
    sys.path.insert(0, str(REPO_ROOT))

from api_service.security import new_id, utc_now
from api_service.source_registry import SourceRegistryError, start_source_collection
from api_service.source_registry_utils import (
    infer_source_type,
    load_seed_bank_homepage_repairs,
    load_seed_bank_profiles,
    load_seed_source_catalog_items,
    load_seed_source_registry_rows,
    normalize_source_url,
)
from worker.discovery.fpds_discovery.discovery import extract_links
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, fetch_text

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover
    Connection = Any


_PRODUCT_TYPE_OPTIONS = ("chequing", "savings", "gic")
_AUTOGEN_SOURCE_PREFIX = "AUTO"
_EXCLUDED_LINK_KEYWORDS = ("login", "sign-in", "signin", "secure", "apply", "open-account", "openaccount", "promo", "offer", "compare")
_SUPPORTING_KEYWORDS = ("rate", "rates", "fee", "fees", "legal", "terms", "conditions", "service", "agreement", "disclosure")
_HUB_KEYWORDS = ("account", "accounts", "bank-account", "bank-accounts", "invest", "investments", "personal")
_PRODUCT_KEYWORDS = {
    "chequing": ("chequing", "checking", "bank-account", "banking-plan", "daily-banking"),
    "savings": ("savings", "save", "high-interest", "interest"),
    "gic": ("gic", "term-deposit", "term-deposits", "certificate", "investment"),
}
_PRODUCT_FIELD_HINTS = {
    "chequing": ["product_name", "monthly_fee", "included_transactions"],
    "savings": ["product_name", "standard_rate", "monthly_fee"],
    "gic": ["product_name", "term_length_text", "minimum_deposit"],
}


@dataclass(frozen=True)
class BankFilters:
    search: str | None
    status: str | None


@dataclass(frozen=True)
class SourceCatalogFilters:
    search: str | None
    bank_code: str | None
    product_type: str | None
    status: str | None


def normalize_bank_filters(*, search: str | None, status: str | None) -> BankFilters:
    normalized_search = _normalize_search(search)
    normalized_status = _clean_text(status)
    return BankFilters(
        search=normalized_search,
        status=normalized_status.lower() if normalized_status else None,
    )


def normalize_source_catalog_filters(
    *,
    search: str | None,
    bank_code: str | None,
    product_type: str | None,
    status: str | None,
) -> SourceCatalogFilters:
    normalized_search = _normalize_search(search)
    normalized_bank_code = _clean_text(bank_code)
    normalized_product_type = _clean_text(product_type)
    normalized_status = _clean_text(status)
    return SourceCatalogFilters(
        search=normalized_search,
        bank_code=normalized_bank_code.upper() if normalized_bank_code else None,
        product_type=normalized_product_type.lower() if normalized_product_type else None,
        status=normalized_status.lower() if normalized_status else None,
    )


def load_bank_list(connection: Connection, *, filters: BankFilters) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    where_clauses = ["1 = 1"]
    params: dict[str, Any] = {}
    if filters.status:
        where_clauses.append("b.status = %(status)s")
        params["status"] = filters.status
    if filters.search:
        params["search_pattern"] = f"%{filters.search}%"
        where_clauses.append(
            """
            (
                lower(b.bank_code) LIKE %(search_pattern)s
                OR lower(b.bank_name) LIKE %(search_pattern)s
                OR lower(COALESCE(b.homepage_url, '')) LIKE %(search_pattern)s
            )
            """
        )

    rows = connection.execute(
        f"""
        SELECT
            b.bank_code,
            b.country_code,
            b.bank_name,
            b.status,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language,
            b.managed_flag,
            b.change_reason,
            b.created_at,
            b.updated_at,
            COUNT(DISTINCT sci.catalog_item_id) AS catalog_item_count,
            COUNT(DISTINCT sri.source_id) AS generated_source_count,
            COALESCE(
                ARRAY_AGG(DISTINCT sci.product_type) FILTER (WHERE sci.product_type IS NOT NULL),
                ARRAY[]::text[]
            ) AS catalog_product_types
        FROM bank AS b
        LEFT JOIN source_registry_catalog_item AS sci
            ON sci.bank_code = b.bank_code
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = b.bank_code
        WHERE {" AND ".join(where_clauses)}
        GROUP BY
            b.bank_code,
            b.country_code,
            b.bank_name,
            b.status,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language,
            b.managed_flag,
            b.change_reason,
            b.created_at,
            b.updated_at
        ORDER BY b.bank_name, b.bank_code
        """,
        params,
    ).fetchall()

    items = [_serialize_bank_row(row) for row in rows]
    status_counts = Counter(item["status"] for item in items)
    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "status_counts": dict(status_counts),
        },
        "facets": {
            "statuses": sorted(status_counts),
        },
        "applied_filters": {
            "search": filters.search,
            "status": filters.status,
        },
    }


def load_bank_detail(connection: Connection, *, bank_code: str) -> dict[str, Any] | None:
    _ensure_bank_and_catalog_seeded(connection)
    row = connection.execute(
        """
        SELECT
            bank_code,
            country_code,
            bank_name,
            status,
            homepage_url,
            normalized_homepage_url,
            source_language,
            managed_flag,
            change_reason,
            created_at,
            updated_at
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    if not row:
        return None

    catalog_rows = connection.execute(
        """
        SELECT
            catalog_item_id,
            bank_code,
            country_code,
            product_type,
            status,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_catalog_item
        WHERE bank_code = %(bank_code)s
        ORDER BY product_type
        """,
        {"bank_code": bank_code},
    ).fetchall()
    generated_counts_by_type_rows = connection.execute(
        """
        SELECT product_type, COUNT(DISTINCT source_id) AS generated_source_count
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
        GROUP BY product_type
        """,
        {"bank_code": bank_code},
    ).fetchall()
    generated_source_count_row = connection.execute(
        """
        SELECT COUNT(DISTINCT source_id) AS generated_source_count
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    generated_counts_by_type = {
        str(item["product_type"]): int(item["generated_source_count"] or 0)
        for item in generated_counts_by_type_rows
    }
    catalog_product_types = sorted(str(item["product_type"]) for item in catalog_rows)

    return {
        "bank": _serialize_bank_row(
            {
                **row,
                "catalog_item_count": len(catalog_rows),
                "generated_source_count": int((generated_source_count_row or {}).get("generated_source_count") or 0),
                "catalog_product_types": catalog_product_types,
            }
        ),
        "catalog_items": [
            _serialize_source_catalog_row(
                item,
                bank_row=row,
                generated_source_count=generated_counts_by_type.get(str(item["product_type"]), 0),
            )
            for item in catalog_rows
        ],
    }


def create_bank_profile(
    connection: Connection,
    *,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    bank_name = _required_text(payload.get("bank_name"), "bank_name")
    homepage_url = _required_text(payload.get("homepage_url"), "homepage_url")
    normalized_homepage_url = normalize_source_url(homepage_url)
    existing_by_homepage = connection.execute(
        """
        SELECT bank_code
        FROM bank
        WHERE normalized_homepage_url = %(normalized_homepage_url)s
        """,
        {"normalized_homepage_url": normalized_homepage_url},
    ).fetchone()
    if existing_by_homepage:
        raise SourceRegistryError(status_code=409, code="bank_homepage_exists", message="A bank with this homepage URL already exists.")

    bank_code = _generate_bank_code(connection, bank_name=bank_name)
    now = utc_now()
    connection.execute(
        """
        INSERT INTO bank (
            bank_code,
            country_code,
            bank_name,
            status,
            homepage_url,
            normalized_homepage_url,
            source_language,
            managed_flag,
            change_reason,
            created_at,
            updated_at
        )
        VALUES (
            %(bank_code)s,
            %(country_code)s,
            %(bank_name)s,
            %(status)s,
            %(homepage_url)s,
            %(normalized_homepage_url)s,
            %(source_language)s,
            %(managed_flag)s,
            %(change_reason)s,
            %(created_at)s,
            %(updated_at)s
        )
        """,
        {
            "bank_code": bank_code,
            "country_code": (_clean_text(payload.get("country_code")) or "CA").upper(),
            "bank_name": bank_name,
            "status": (_clean_text(payload.get("status")) or "active").lower(),
            "homepage_url": homepage_url,
            "normalized_homepage_url": normalized_homepage_url,
            "source_language": (_clean_text(payload.get("source_language")) or "en").lower(),
            "managed_flag": True,
            "change_reason": _clean_text(payload.get("change_reason")),
            "created_at": now,
            "updated_at": now,
        },
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="bank_profile_created",
        target_id=bank_code,
        target_type="bank",
        diff_summary=f"Created bank profile `{bank_code}`.",
        metadata={"bank_code": bank_code, "bank_name": bank_name},
    )
    detail = load_bank_detail(connection, bank_code=bank_code)
    if detail is None:
        raise SourceRegistryError(status_code=500, code="bank_profile_missing_after_create", message="Created bank profile could not be reloaded.")
    return detail["bank"]


def update_bank_profile(
    connection: Connection,
    *,
    bank_code: str,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    existing_row = connection.execute(
        """
        SELECT
            bank_code,
            country_code,
            bank_name,
            status,
            homepage_url,
            normalized_homepage_url,
            source_language,
            managed_flag,
            change_reason,
            created_at,
            updated_at
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    if not existing_row:
        raise SourceRegistryError(status_code=404, code="bank_profile_not_found", message="Bank profile was not found.")

    bank_name = _required_text(payload.get("bank_name", existing_row["bank_name"]), "bank_name")
    homepage_url = _required_text(payload.get("homepage_url", existing_row["homepage_url"]), "homepage_url")
    normalized_homepage_url = normalize_source_url(homepage_url)
    conflict_row = connection.execute(
        """
        SELECT bank_code
        FROM bank
        WHERE normalized_homepage_url = %(normalized_homepage_url)s
          AND bank_code <> %(bank_code)s
        """,
        {"normalized_homepage_url": normalized_homepage_url, "bank_code": bank_code},
    ).fetchone()
    if conflict_row:
        raise SourceRegistryError(status_code=409, code="bank_homepage_exists", message="A bank with this homepage URL already exists.")

    updated_status = (_clean_text(payload.get("status", existing_row["status"])) or "active").lower()
    updated_country_code = (_clean_text(payload.get("country_code", existing_row["country_code"])) or "CA").upper()
    updated_source_language = (_clean_text(payload.get("source_language", existing_row["source_language"])) or "en").lower()
    updated_change_reason = _clean_text(payload.get("change_reason", existing_row["change_reason"]))
    diff_summary = _build_bank_diff_summary(existing_row, {
        "bank_name": bank_name,
        "homepage_url": homepage_url,
        "status": updated_status,
        "country_code": updated_country_code,
        "source_language": updated_source_language,
    })

    connection.execute(
        """
        UPDATE bank
        SET
            country_code = %(country_code)s,
            bank_name = %(bank_name)s,
            status = %(status)s,
            homepage_url = %(homepage_url)s,
            normalized_homepage_url = %(normalized_homepage_url)s,
            source_language = %(source_language)s,
            change_reason = %(change_reason)s,
            updated_at = %(updated_at)s
        WHERE bank_code = %(bank_code)s
        """,
        {
            "bank_code": bank_code,
            "country_code": updated_country_code,
            "bank_name": bank_name,
            "status": updated_status,
            "homepage_url": homepage_url,
            "normalized_homepage_url": normalized_homepage_url,
            "source_language": updated_source_language,
            "change_reason": updated_change_reason,
            "updated_at": utc_now(),
        },
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="bank_profile_updated",
        target_id=bank_code,
        target_type="bank",
        diff_summary=diff_summary,
        metadata={"bank_code": bank_code},
    )
    detail = load_bank_detail(connection, bank_code=bank_code)
    if detail is None:
        raise SourceRegistryError(status_code=500, code="bank_profile_missing_after_update", message="Updated bank profile could not be reloaded.")
    return detail["bank"]


def load_source_catalog_list(connection: Connection, *, filters: SourceCatalogFilters) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    where_clauses = ["1 = 1"]
    params: dict[str, Any] = {}
    if filters.bank_code:
        where_clauses.append("sci.bank_code = %(bank_code)s")
        params["bank_code"] = filters.bank_code
    if filters.product_type:
        where_clauses.append("sci.product_type = %(product_type)s")
        params["product_type"] = filters.product_type
    if filters.status:
        where_clauses.append("sci.status = %(status)s")
        params["status"] = filters.status
    if filters.search:
        params["search_pattern"] = f"%{filters.search}%"
        where_clauses.append(
            """
            (
                lower(sci.catalog_item_id) LIKE %(search_pattern)s
                OR lower(b.bank_name) LIKE %(search_pattern)s
                OR lower(sci.bank_code) LIKE %(search_pattern)s
            )
            """
        )

    rows = connection.execute(
        f"""
        SELECT
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language,
            COUNT(DISTINCT sri.source_id) AS generated_source_count
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.product_type = sci.product_type
        WHERE {" AND ".join(where_clauses)}
        GROUP BY
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language
        ORDER BY b.bank_name, sci.product_type
        """,
        params,
    ).fetchall()

    bank_rows = connection.execute(
        """
        SELECT bank_code, bank_name
        FROM bank
        ORDER BY bank_name, bank_code
        """
    ).fetchall()

    items = [_serialize_source_catalog_row(row, bank_row=row, generated_source_count=int(row["generated_source_count"] or 0)) for row in rows]
    status_counts = Counter(item["status"] for item in items)
    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "status_counts": dict(status_counts),
            "generated_source_count": sum(int(item["generated_source_count"]) for item in items),
        },
        "facets": {
            "bank_options": [{"bank_code": str(row["bank_code"]), "bank_name": str(row["bank_name"])} for row in bank_rows],
            "product_types": list(_PRODUCT_TYPE_OPTIONS),
            "statuses": sorted(status_counts),
        },
        "applied_filters": {
            "search": filters.search,
            "bank_code": filters.bank_code,
            "product_type": filters.product_type,
            "status": filters.status,
        },
    }


def load_source_catalog_detail(connection: Connection, *, catalog_item_id: str) -> dict[str, Any] | None:
    _ensure_bank_and_catalog_seeded(connection)
    row = connection.execute(
        """
        SELECT
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language,
            COUNT(DISTINCT sri.source_id) AS generated_source_count
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.product_type = sci.product_type
        WHERE sci.catalog_item_id = %(catalog_item_id)s
        GROUP BY
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language
        """,
        {"catalog_item_id": catalog_item_id},
    ).fetchone()
    if not row:
        return None

    source_rows = connection.execute(
        """
        SELECT source_id
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND product_type = %(product_type)s
        ORDER BY source_id
        LIMIT 5
        """,
        {"bank_code": row["bank_code"], "product_type": row["product_type"]},
    ).fetchall()
    recent_runs = connection.execute(
        """
        SELECT
            run_id,
            run_state,
            trigger_type,
            triggered_by,
            source_scope_count,
            candidate_count,
            review_queued_count,
            partial_completion_flag,
            error_summary,
            run_metadata,
            started_at,
            completed_at
        FROM ingestion_run
        WHERE COALESCE(run_metadata ->> 'bank_code', '') = %(bank_code)s
          AND COALESCE(run_metadata ->> 'product_type', '') = %(product_type)s
        ORDER BY started_at DESC
        LIMIT 5
        """,
        {"bank_code": row["bank_code"], "product_type": row["product_type"]},
    ).fetchall()

    return {
        "catalog_item": _serialize_source_catalog_row(row, bank_row=row, generated_source_count=int(row["generated_source_count"] or 0)),
        "sample_source_ids": [str(item["source_id"]) for item in source_rows],
        "recent_runs": [_serialize_recent_run_row(item) for item in recent_runs],
    }


def create_source_catalog_item(
    connection: Connection,
    *,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    bank_code = _required_text(payload.get("bank_code"), "bank_code").upper()
    product_type = _required_text(payload.get("product_type"), "product_type").lower()
    if product_type not in _PRODUCT_TYPE_OPTIONS:
        raise SourceRegistryError(status_code=422, code="invalid_product_type", message="product_type must be chequing, savings, or gic.")

    bank_row = connection.execute(
        """
        SELECT bank_code, country_code, bank_name, homepage_url, normalized_homepage_url, source_language
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    if not bank_row:
        raise SourceRegistryError(status_code=404, code="bank_profile_not_found", message="Select a valid bank before creating source catalog coverage.")

    existing = connection.execute(
        """
        SELECT catalog_item_id
        FROM source_registry_catalog_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = %(product_type)s
        """,
        {"bank_code": bank_code, "country_code": bank_row["country_code"], "product_type": product_type},
    ).fetchone()
    if existing:
        raise SourceRegistryError(status_code=409, code="source_catalog_exists", message="This bank and product type already exists in the source catalog.")

    catalog_item_id = f"catalog-{str(bank_row['country_code']).lower()}-{bank_code.lower()}-{product_type}-{new_id('')[:8]}".rstrip("-")
    now = utc_now()
    connection.execute(
        """
        INSERT INTO source_registry_catalog_item (
            catalog_item_id,
            bank_code,
            country_code,
            product_type,
            status,
            change_reason,
            created_at,
            updated_at
        )
        VALUES (
            %(catalog_item_id)s,
            %(bank_code)s,
            %(country_code)s,
            %(product_type)s,
            %(status)s,
            %(change_reason)s,
            %(created_at)s,
            %(updated_at)s
        )
        """,
        {
            "catalog_item_id": catalog_item_id,
            "bank_code": bank_code,
            "country_code": bank_row["country_code"],
            "product_type": product_type,
            "status": (_clean_text(payload.get("status")) or "active").lower(),
            "change_reason": _clean_text(payload.get("change_reason")),
            "created_at": now,
            "updated_at": now,
        },
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="source_catalog_item_created",
        target_id=catalog_item_id,
        target_type="source_registry_catalog_item",
        diff_summary=f"Created source catalog item `{catalog_item_id}`.",
        metadata={"bank_code": bank_code, "product_type": product_type},
    )
    detail = load_source_catalog_detail(connection, catalog_item_id=catalog_item_id)
    if detail is None:
        raise SourceRegistryError(status_code=500, code="source_catalog_missing_after_create", message="Created source catalog item could not be reloaded.")
    return detail["catalog_item"]


def update_source_catalog_item(
    connection: Connection,
    *,
    catalog_item_id: str,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    existing = connection.execute(
        """
        SELECT catalog_item_id, bank_code, country_code, product_type, status, change_reason
        FROM source_registry_catalog_item
        WHERE catalog_item_id = %(catalog_item_id)s
        """,
        {"catalog_item_id": catalog_item_id},
    ).fetchone()
    if not existing:
        raise SourceRegistryError(status_code=404, code="source_catalog_not_found", message="Source catalog item was not found.")

    bank_code = _required_text(payload.get("bank_code", existing["bank_code"]), "bank_code").upper()
    product_type = _required_text(payload.get("product_type", existing["product_type"]), "product_type").lower()
    if product_type not in _PRODUCT_TYPE_OPTIONS:
        raise SourceRegistryError(status_code=422, code="invalid_product_type", message="product_type must be chequing, savings, or gic.")

    bank_row = connection.execute(
        """
        SELECT bank_code, country_code, bank_name, homepage_url, normalized_homepage_url, source_language
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    if not bank_row:
        raise SourceRegistryError(status_code=404, code="bank_profile_not_found", message="Select a valid bank before updating source catalog coverage.")

    conflict = connection.execute(
        """
        SELECT catalog_item_id
        FROM source_registry_catalog_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = %(product_type)s
          AND catalog_item_id <> %(catalog_item_id)s
        """,
        {
            "bank_code": bank_code,
            "country_code": bank_row["country_code"],
            "product_type": product_type,
            "catalog_item_id": catalog_item_id,
        },
    ).fetchone()
    if conflict:
        raise SourceRegistryError(status_code=409, code="source_catalog_exists", message="This bank and product type already exists in the source catalog.")

    updated_status = (_clean_text(payload.get("status", existing["status"])) or "active").lower()
    updated_change_reason = _clean_text(payload.get("change_reason", existing["change_reason"]))
    diff_summary = _build_catalog_diff_summary(existing, {"bank_code": bank_code, "product_type": product_type, "status": updated_status})
    connection.execute(
        """
        UPDATE source_registry_catalog_item
        SET
            bank_code = %(bank_code)s,
            country_code = %(country_code)s,
            product_type = %(product_type)s,
            status = %(status)s,
            change_reason = %(change_reason)s,
            updated_at = %(updated_at)s
        WHERE catalog_item_id = %(catalog_item_id)s
        """,
        {
            "catalog_item_id": catalog_item_id,
            "bank_code": bank_code,
            "country_code": bank_row["country_code"],
            "product_type": product_type,
            "status": updated_status,
            "change_reason": updated_change_reason,
            "updated_at": utc_now(),
        },
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="source_catalog_item_updated",
        target_id=catalog_item_id,
        target_type="source_registry_catalog_item",
        diff_summary=diff_summary,
        metadata={"bank_code": bank_code, "product_type": product_type},
    )
    detail = load_source_catalog_detail(connection, catalog_item_id=catalog_item_id)
    if detail is None:
        raise SourceRegistryError(status_code=500, code="source_catalog_missing_after_update", message="Updated source catalog item could not be reloaded.")
    return detail["catalog_item"]


def start_source_catalog_collection(
    connection: Connection,
    *,
    catalog_item_ids: list[str],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    _ensure_bank_and_catalog_seeded(connection)
    if not catalog_item_ids:
        raise SourceRegistryError(status_code=400, code="source_catalog_selection_required", message="Select at least one source catalog item.")

    rows = connection.execute(
        """
        SELECT
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
        WHERE sci.catalog_item_id = ANY(%(catalog_item_ids)s)
        ORDER BY b.bank_name, sci.product_type
        """,
        {"catalog_item_ids": catalog_item_ids},
    ).fetchall()
    if len(rows) != len(set(catalog_item_ids)):
        raise SourceRegistryError(status_code=404, code="source_catalog_not_found", message="One or more source catalog items could not be found.")

    selected_source_ids: list[str] = []
    materialization_summary: list[dict[str, Any]] = []
    for row in rows:
        generated_rows = _materialize_sources_for_catalog_item(connection, row=row)
        generated_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["status"]) != "removed"
        ]
        target_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["discovery_role"]) == "detail" and str(item["status"]) != "removed"
        ]
        if not target_source_ids:
            raise SourceRegistryError(
                status_code=422,
                code="source_catalog_generation_missing_detail",
                message=f"No detail sources could be generated for {row['bank_name']} {row['product_type']}.",
            )
        selected_source_ids.extend(generated_source_ids)
        materialization_summary.append(
            {
                "catalog_item_id": str(row["catalog_item_id"]),
                "bank_code": str(row["bank_code"]),
                "product_type": str(row["product_type"]),
                "generated_source_ids": generated_source_ids,
                "target_source_ids": target_source_ids,
            }
        )

    result = start_source_collection(
        connection,
        source_ids=selected_source_ids,
        actor=actor,
        request_context=request_context,
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="source_catalog_collection_launched",
        target_id=result["collection_id"],
        target_type="source_catalog_collection",
        diff_summary=f"Launched source catalog collection for {len(rows)} catalog item(s).",
        metadata={
            "catalog_item_ids": list(catalog_item_ids),
            "selected_source_ids": selected_source_ids,
        },
    )
    return {
        **result,
        "catalog_item_ids": list(catalog_item_ids),
        "materialized_items": materialization_summary,
    }


def _ensure_bank_and_catalog_seeded(connection: Connection) -> None:
    bank_row = connection.execute("SELECT COUNT(*) AS item_count FROM bank").fetchone()
    if bank_row and int(bank_row["item_count"]) == 0:
        seeded_at = utc_now()
        for item in load_seed_bank_profiles():
            connection.execute(
                """
                INSERT INTO bank (
                    bank_code,
                    country_code,
                    bank_name,
                    status,
                    homepage_url,
                    normalized_homepage_url,
                    source_language,
                    managed_flag,
                    change_reason,
                    created_at,
                    updated_at
                )
                VALUES (
                    %(bank_code)s,
                    %(country_code)s,
                    %(bank_name)s,
                    'active',
                    %(homepage_url)s,
                    %(normalized_homepage_url)s,
                    %(source_language)s,
                    %(managed_flag)s,
                    %(change_reason)s,
                    %(created_at)s,
                    %(updated_at)s
                )
                ON CONFLICT (bank_code) DO UPDATE
                SET
                    homepage_url = COALESCE(bank.homepage_url, EXCLUDED.homepage_url),
                    normalized_homepage_url = COALESCE(bank.normalized_homepage_url, EXCLUDED.normalized_homepage_url),
                    source_language = COALESCE(bank.source_language, EXCLUDED.source_language)
                """,
                {
                    **item,
                    "created_at": seeded_at,
                    "updated_at": seeded_at,
                },
            )

    _backfill_seeded_bank_profile_fields(connection)

    row = connection.execute("SELECT COUNT(*) AS item_count FROM source_registry_catalog_item").fetchone()
    if row and int(row["item_count"]) > 0:
        return

    seeded_at = utc_now()
    for item in load_seed_source_catalog_items():
        connection.execute(
            """
            INSERT INTO source_registry_catalog_item (
                catalog_item_id,
                bank_code,
                country_code,
                product_type,
                status,
                change_reason,
                created_at,
                updated_at
            )
            VALUES (
                %(catalog_item_id)s,
                %(bank_code)s,
                %(country_code)s,
                %(product_type)s,
                %(status)s,
                %(change_reason)s,
                %(created_at)s,
                %(updated_at)s
            )
            ON CONFLICT (bank_code, country_code, product_type) DO NOTHING
            """,
            {
                **item,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            },
        )


def _backfill_seeded_bank_profile_fields(connection: Connection) -> None:
    for item in load_seed_bank_homepage_repairs():
        connection.execute(
            """
            UPDATE bank
            SET
                homepage_url = CASE
                    WHEN NULLIF(BTRIM(homepage_url), '') IS NULL THEN %(homepage_url)s
                    WHEN normalized_homepage_url = ANY(%(legacy_homepage_urls)s) THEN %(homepage_url)s
                    ELSE homepage_url
                END,
                normalized_homepage_url = CASE
                    WHEN NULLIF(BTRIM(normalized_homepage_url), '') IS NULL THEN %(normalized_homepage_url)s
                    WHEN normalized_homepage_url = ANY(%(legacy_homepage_urls)s) THEN %(normalized_homepage_url)s
                    ELSE normalized_homepage_url
                END,
                source_language = COALESCE(NULLIF(BTRIM(source_language), ''), %(source_language)s)
            WHERE bank_code = %(bank_code)s
              AND managed_flag = true
              AND (
                NULLIF(BTRIM(homepage_url), '') IS NULL
                OR NULLIF(BTRIM(normalized_homepage_url), '') IS NULL
                OR normalized_homepage_url = ANY(%(legacy_homepage_urls)s)
                OR NULLIF(BTRIM(source_language), '') IS NULL
              )
            """,
            item,
        )


def _materialize_sources_for_catalog_item(connection: Connection, *, row: dict[str, Any]) -> list[dict[str, Any]]:
    bank_code = str(row["bank_code"])
    product_type = str(row["product_type"])
    generated_rows = _generate_sources_from_homepage(
        bank_code=bank_code,
        bank_name=str(row["bank_name"]),
        country_code=str(row["country_code"]),
        product_type=product_type,
        homepage_url=str(row["homepage_url"]),
        source_language=str(row.get("source_language") or "en"),
    )
    connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            updated_at = %(updated_at)s,
            change_reason = %(change_reason)s
        WHERE bank_code = %(bank_code)s
          AND product_type = %(product_type)s
        """,
        {
            "updated_at": utc_now(),
            "change_reason": "superseded_by_homepage_catalog_generation",
            "bank_code": bank_code,
            "product_type": product_type,
        },
    )
    _upsert_source_registry_rows(connection, generated_rows)
    return generated_rows


def _upsert_source_registry_rows(connection: Connection, rows: list[dict[str, Any]]) -> None:
    now = utc_now()
    for item in rows:
        connection.execute(
            """
            INSERT INTO source_registry_item (
                source_id,
                bank_code,
                country_code,
                product_type,
                product_key,
                source_name,
                source_url,
                normalized_url,
                source_type,
                discovery_role,
                status,
                priority,
                source_language,
                purpose,
                expected_fields,
                seed_source_flag,
                redirect_target_url,
                alias_urls,
                change_reason,
                created_at,
                updated_at
            )
            VALUES (
                %(source_id)s,
                %(bank_code)s,
                %(country_code)s,
                %(product_type)s,
                %(product_key)s,
                %(source_name)s,
                %(source_url)s,
                %(normalized_url)s,
                %(source_type)s,
                %(discovery_role)s,
                %(status)s,
                %(priority)s,
                %(source_language)s,
                %(purpose)s,
                %(expected_fields)s::jsonb,
                %(seed_source_flag)s,
                %(redirect_target_url)s,
                %(alias_urls)s::jsonb,
                %(change_reason)s,
                %(created_at)s,
                %(updated_at)s
            )
            ON CONFLICT (source_id) DO UPDATE
            SET
                bank_code = EXCLUDED.bank_code,
                country_code = EXCLUDED.country_code,
                product_type = EXCLUDED.product_type,
                product_key = EXCLUDED.product_key,
                source_name = EXCLUDED.source_name,
                source_url = EXCLUDED.source_url,
                normalized_url = EXCLUDED.normalized_url,
                source_type = EXCLUDED.source_type,
                discovery_role = EXCLUDED.discovery_role,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                source_language = EXCLUDED.source_language,
                purpose = EXCLUDED.purpose,
                expected_fields = EXCLUDED.expected_fields,
                seed_source_flag = EXCLUDED.seed_source_flag,
                redirect_target_url = EXCLUDED.redirect_target_url,
                alias_urls = EXCLUDED.alias_urls,
                change_reason = EXCLUDED.change_reason,
                updated_at = EXCLUDED.updated_at
            """,
            {
                **item,
                "expected_fields": json.dumps(item.get("expected_fields", []), ensure_ascii=True),
                "alias_urls": json.dumps(item.get("alias_urls", []), ensure_ascii=True),
                "created_at": now,
                "updated_at": now,
            },
        )


def _generate_sources_from_homepage(
    *,
    bank_code: str,
    bank_name: str,
    country_code: str,
    product_type: str,
    homepage_url: str,
    source_language: str,
) -> list[dict[str, Any]]:
    normalized_homepage_url = normalize_source_url(homepage_url)
    hostname = urlparse(normalized_homepage_url).hostname
    if not hostname:
        raise SourceRegistryError(status_code=422, code="bank_homepage_invalid", message="Bank homepage URL must include a hostname.")

    fetch_policy = DiscoveryFetchPolicy(allowed_domains=(hostname,))
    detail_links: list[tuple[int, Any]] = []
    supporting_links: list[tuple[int, Any]] = []
    pdf_links: list[tuple[int, Any]] = []
    hub_pages: list[tuple[int, str, str]] = []
    try:
        homepage_html = fetch_text(normalized_homepage_url, fetch_policy)
    except Exception:
        homepage_html = ""

    homepage_links = _extract_allowed_links(html_text=homepage_html, base_url=normalized_homepage_url, hostname=hostname)
    for link in homepage_links:
        fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
        if any(keyword in fingerprint for keyword in _EXCLUDED_LINK_KEYWORDS):
            continue
        score = _score_product_link(product_type=product_type, normalized_url=link.normalized_url, anchor_text=link.anchor_text)
        if link.source_type == "pdf":
            if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                pdf_links.append((score, link))
            continue
        if score > 0:
            detail_links.append((score, link))
        elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
            supporting_links.append((1, link))
        hub_score = _score_catalog_hub_link(product_type=product_type, normalized_url=link.normalized_url, anchor_text=link.anchor_text)
        if hub_score > 0:
            hub_pages.append((hub_score, link.normalized_url, link.resolved_url))

    seed_entry_url = _load_seed_entry_url(bank_code=bank_code, product_type=product_type)
    if seed_entry_url is not None:
        seed_score = _score_catalog_hub_link(product_type=product_type, normalized_url=seed_entry_url, anchor_text="")
        hub_pages.append((max(seed_score, 1), seed_entry_url, seed_entry_url))

    unique_hub_pages = _dedupe_page_candidates(hub_pages)
    for _score, normalized_page_url, resolved_page_url in unique_hub_pages[:3]:
        if normalized_page_url == normalized_homepage_url:
            continue
        try:
            page_html = fetch_text(resolved_page_url, fetch_policy)
        except Exception:
            continue
        for link in _extract_allowed_links(html_text=page_html, base_url=normalized_page_url, hostname=hostname):
            fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
            if any(keyword in fingerprint for keyword in _EXCLUDED_LINK_KEYWORDS):
                continue
            score = _score_product_link(product_type=product_type, normalized_url=link.normalized_url, anchor_text=link.anchor_text)
            if link.source_type == "pdf":
                if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                    pdf_links.append((score, link))
                continue
            if score > 0:
                detail_links.append((score, link))
            elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                supporting_links.append((1, link))

    unique_detail_links = _dedupe_scored_links(detail_links)[:6]
    unique_supporting_links = _dedupe_scored_links(supporting_links)[:4]
    unique_pdf_links = _dedupe_scored_links(pdf_links)[:4]
    source_rows: list[dict[str, Any]] = []
    entry_url = unique_hub_pages[0][1] if unique_hub_pages else normalized_homepage_url
    entry_raw_url = unique_hub_pages[0][2] if unique_hub_pages else homepage_url

    if unique_detail_links:
        source_rows.append(
            _build_generated_source_row(
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                source_language=source_language,
                normalized_url=entry_url,
                raw_url=entry_raw_url,
                source_name=f"{bank_name} {product_type.title()} catalog entry",
                discovery_role="entry",
                priority="P0",
                purpose=f"{bank_name} {product_type} catalog discovery entry",
                expected_fields=["product_name"],
            )
        )
        for _, link in unique_detail_links:
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=link.normalized_url,
                    raw_url=link.resolved_url,
                    source_name=_generated_link_name(bank_name, product_type, link.anchor_text, fallback="detail"),
                    discovery_role="detail",
                    priority="P1",
                    purpose=f"Auto-generated {product_type} detail source from bank homepage",
                    expected_fields=_PRODUCT_FIELD_HINTS[product_type],
                )
            )
    else:
        fallback_url = entry_url
        fallback_raw_url = entry_raw_url
        source_rows.append(
            _build_generated_source_row(
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                source_language=source_language,
                normalized_url=fallback_url,
                raw_url=fallback_raw_url,
                source_name=f"{bank_name} {product_type.title()} catalog fallback",
                discovery_role="detail",
                priority="P0",
                purpose=f"Homepage-derived fallback detail source for {product_type}",
                expected_fields=_PRODUCT_FIELD_HINTS[product_type],
            )
        )

    for _, link in unique_supporting_links:
        source_rows.append(
            _build_generated_source_row(
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                source_language=source_language,
                normalized_url=link.normalized_url,
                raw_url=link.resolved_url,
                source_name=_generated_link_name(bank_name, product_type, link.anchor_text, fallback="support"),
                discovery_role="supporting_html",
                priority="P2",
                purpose=f"Auto-generated supporting source for {product_type}",
                expected_fields=_PRODUCT_FIELD_HINTS[product_type],
            )
        )
    for _, link in unique_pdf_links:
        source_rows.append(
            _build_generated_source_row(
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                source_language=source_language,
                normalized_url=link.normalized_url,
                raw_url=link.resolved_url,
                source_name=_generated_link_name(bank_name, product_type, link.anchor_text, fallback="pdf"),
                discovery_role="linked_pdf",
                priority="P2",
                purpose=f"Auto-generated linked PDF source for {product_type}",
                expected_fields=_PRODUCT_FIELD_HINTS[product_type],
            )
        )
    return source_rows


def _load_seed_entry_url(*, bank_code: str, product_type: str) -> str | None:
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) == bank_code
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) == "entry"
        ):
            return str(item["normalized_url"])
    return None


def _extract_allowed_links(*, html_text: str, base_url: str, hostname: str) -> list[Any]:
    allowed_links: list[Any] = []
    for link in extract_links(html_text, base_url=base_url):
        link_hostname = urlparse(link.normalized_url).hostname
        if not link_hostname or not (link_hostname == hostname or link_hostname.endswith(f".{hostname}")):
            continue
        allowed_links.append(link)
    return allowed_links


def _dedupe_page_candidates(items: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    by_url: dict[str, tuple[int, str, str]] = {}
    for score, normalized_url, resolved_url in sorted(items, key=lambda item: (-item[0], item[1])):
        if normalized_url not in by_url:
            by_url[normalized_url] = (score, normalized_url, resolved_url)
    return list(by_url.values())


def _score_catalog_hub_link(*, product_type: str, normalized_url: str, anchor_text: str) -> int:
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    score = _score_product_link(product_type=product_type, normalized_url=normalized_url, anchor_text=anchor_text)
    for keyword in _HUB_KEYWORDS:
        if keyword in fingerprint:
            score += 1
    for keyword in _SUPPORTING_KEYWORDS:
        if keyword in fingerprint:
            score -= 2
    return score


def _build_generated_source_row(
    *,
    bank_code: str,
    country_code: str,
    product_type: str,
    source_language: str,
    normalized_url: str,
    raw_url: str,
    source_name: str,
    discovery_role: str,
    priority: str,
    purpose: str,
    expected_fields: list[str],
) -> dict[str, Any]:
    source_type = infer_source_type(normalized_url)
    digest = hashlib.sha1(f"{bank_code}|{product_type}|{normalized_url}|{discovery_role}".encode("utf-8")).hexdigest()[:10]
    type_code = {"chequing": "CHQ", "savings": "SAV", "gic": "GIC"}[product_type]
    return {
        "source_id": f"{_AUTOGEN_SOURCE_PREFIX}-{bank_code}-{type_code}-{digest}",
        "bank_code": bank_code,
        "country_code": country_code,
        "product_type": product_type,
        "product_key": f"{bank_code}:{product_type}",
        "source_name": source_name,
        "source_url": raw_url,
        "normalized_url": normalized_url,
        "source_type": source_type,
        "discovery_role": discovery_role,
        "status": "active",
        "priority": priority,
        "source_language": source_language,
        "purpose": purpose,
        "expected_fields": expected_fields,
        "seed_source_flag": False,
        "redirect_target_url": None,
        "alias_urls": [],
        "change_reason": "generated_from_bank_homepage",
    }


def _dedupe_scored_links(items: list[tuple[int, Any]]) -> list[tuple[int, Any]]:
    by_url: dict[str, tuple[int, Any]] = {}
    for score, link in sorted(items, key=lambda item: (-item[0], item[1].normalized_url)):
        if link.normalized_url not in by_url:
            by_url[link.normalized_url] = (score, link)
    return list(by_url.values())


def _score_product_link(*, product_type: str, normalized_url: str, anchor_text: str) -> int:
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    score = 0
    for keyword in _PRODUCT_KEYWORDS[product_type]:
        if keyword in fingerprint:
            score += 2
    for keyword in _SUPPORTING_KEYWORDS:
        if keyword in fingerprint:
            score -= 1
    return score


def _generated_link_name(bank_name: str, product_type: str, anchor_text: str, *, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", anchor_text.strip())
    if cleaned:
        return cleaned[:280]
    return f"{bank_name} {product_type.title()} {fallback}"


def _serialize_bank_row(row: dict[str, Any]) -> dict[str, Any]:
    catalog_product_types = sorted(str(value) for value in (row.get("catalog_product_types") or []) if value)
    return {
        "bank_code": str(row["bank_code"]),
        "country_code": str(row["country_code"]),
        "bank_name": str(row["bank_name"]),
        "status": str(row["status"]),
        "homepage_url": row.get("homepage_url"),
        "normalized_homepage_url": row.get("normalized_homepage_url"),
        "source_language": str(row.get("source_language") or "en"),
        "managed_flag": bool(row.get("managed_flag", False)),
        "change_reason": row.get("change_reason"),
        "created_at": _serialize_datetime(row.get("created_at")),
        "updated_at": _serialize_datetime(row.get("updated_at")),
        "catalog_item_count": int(row.get("catalog_item_count") or 0),
        "catalog_product_types": catalog_product_types,
        "generated_source_count": int(row.get("generated_source_count") or 0),
    }


def _serialize_source_catalog_row(row: dict[str, Any], *, bank_row: dict[str, Any], generated_source_count: int) -> dict[str, Any]:
    return {
        "catalog_item_id": str(row["catalog_item_id"]),
        "bank_code": str(row["bank_code"]),
        "bank_name": str(bank_row["bank_name"]),
        "country_code": str(row["country_code"]),
        "product_type": str(row["product_type"]),
        "status": str(row["status"]),
        "homepage_url": bank_row.get("homepage_url"),
        "normalized_homepage_url": bank_row.get("normalized_homepage_url"),
        "source_language": str(bank_row.get("source_language") or "en"),
        "generated_source_count": generated_source_count,
        "change_reason": row.get("change_reason"),
        "created_at": _serialize_datetime(row.get("created_at")),
        "updated_at": _serialize_datetime(row.get("updated_at")),
    }


def _serialize_recent_run_row(row: dict[str, Any]) -> dict[str, Any]:
    run_metadata = row.get("run_metadata") or {}
    if isinstance(run_metadata, str):
        try:
            run_metadata = json.loads(run_metadata)
        except json.JSONDecodeError:
            run_metadata = {}
    return {
        "run_id": str(row["run_id"]),
        "run_status": str(row["run_state"]),
        "trigger_type": str(row["trigger_type"]),
        "triggered_by": row.get("triggered_by"),
        "source_scope_count": int(row.get("source_scope_count") or 0),
        "candidate_count": int(row.get("candidate_count") or 0),
        "review_queued_count": int(row.get("review_queued_count") or 0),
        "partial_completion_flag": bool(row.get("partial_completion_flag", False)),
        "error_summary": row.get("error_summary"),
        "started_at": _serialize_datetime(row.get("started_at")),
        "completed_at": _serialize_datetime(row.get("completed_at")),
        "pipeline_stage": str(run_metadata.get("pipeline_stage") or run_metadata.get("trigger_type") or "collection"),
    }


def _record_catalog_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    event_type: str,
    target_id: str,
    target_type: str,
    diff_summary: str,
    metadata: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO audit_event (
            audit_event_id,
            event_category,
            event_type,
            actor_type,
            actor_id,
            actor_role_snapshot,
            target_type,
            target_id,
            request_id,
            diff_summary,
            source_ref,
            ip_address,
            user_agent,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            %(event_category)s,
            %(event_type)s,
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            %(target_type)s,
            %(target_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(source_ref)s,
            %(ip_address)s,
            %(user_agent)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "event_category": "config",
            "event_type": event_type,
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_type": target_type,
            "target_id": target_id,
            "request_id": request_context.get("request_id"),
            "diff_summary": diff_summary,
            "source_ref": request_context.get("request_id"),
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "event_payload": json.dumps({"diff_summary": diff_summary, **metadata}, ensure_ascii=True),
            "occurred_at": utc_now(),
        },
    )


def _build_bank_diff_summary(existing_row: dict[str, Any], updated: dict[str, Any]) -> str:
    changes: list[str] = []
    if str(existing_row["bank_name"]) != str(updated["bank_name"]):
        changes.append("Bank name")
    if str(existing_row.get("homepage_url") or "") != str(updated["homepage_url"]):
        changes.append("Homepage URL")
    if str(existing_row["status"]) != str(updated["status"]):
        changes.append("Status")
    if str(existing_row["country_code"]) != str(updated["country_code"]):
        changes.append("Country")
    if str(existing_row.get("source_language") or "en") != str(updated["source_language"]):
        changes.append("Language")
    if not changes:
        return f"Updated bank profile `{existing_row['bank_code']}` with no material field changes."
    return f"Updated bank profile `{existing_row['bank_code']}`: {', '.join(changes)}."


def _build_catalog_diff_summary(existing_row: dict[str, Any], updated: dict[str, Any]) -> str:
    changes: list[str] = []
    if str(existing_row["bank_code"]) != str(updated["bank_code"]):
        changes.append("Bank")
    if str(existing_row["product_type"]) != str(updated["product_type"]):
        changes.append("Product type")
    if str(existing_row["status"]) != str(updated["status"]):
        changes.append("Status")
    if not changes:
        return f"Updated source catalog item `{existing_row['catalog_item_id']}` with no material field changes."
    return f"Updated source catalog item `{existing_row['catalog_item_id']}`: {', '.join(changes)}."


def _generate_bank_code(connection: Connection, *, bank_name: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", bank_name.upper())
    if not tokens:
        raise SourceRegistryError(status_code=422, code="bank_name_invalid", message="Bank name must contain letters or digits.")
    candidates: list[str] = []
    initials = "".join(token[0] for token in tokens)
    if 2 <= len(initials) <= 12:
        candidates.append(initials)
    joined = "".join(tokens)
    if joined:
        candidates.append(joined[:12])
    for token in tokens:
        if 2 <= len(token) <= 12:
            candidates.append(token[:12])
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if not _bank_code_exists(connection, candidate):
            return candidate
    base = joined[:8] or "BANK"
    suffix = 1
    while True:
        candidate = f"{base}{suffix}"
        if len(candidate) > 12:
            candidate = candidate[:12]
        if not _bank_code_exists(connection, candidate):
            return candidate
        suffix += 1


def _bank_code_exists(connection: Connection, bank_code: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    return row is not None


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()
    return str(value)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: Any, field_name: str) -> str:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise SourceRegistryError(status_code=422, code="required_field_missing", message=f"{field_name} is required.")
    return cleaned


def _normalize_search(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    return re.sub(r"\s+", " ", cleaned).lower()
