from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TYPE_CHECKING, Any
import urllib.error
import urllib.request
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import path guard for `uv run --directory api/service`
    sys.path.insert(0, str(REPO_ROOT))

from api_service.errors import SourceRegistryError
from api_service.product_types import (
    canonicalize_product_type_code,
    load_product_type_definitions_map,
    require_product_type_definition,
)
from api_service.security import new_id, utc_now
from api_service.source_registry import _insert_collection_run_row
from api_service.source_registry_utils import (
    infer_source_type,
    load_seed_source_registry_rows,
    normalize_source_url,
)
from worker.discovery.fpds_discovery.discovery import extract_links
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, fetch_text
from worker.pipeline.fpds_ai_runtime import estimated_cost_usd

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover
    Connection = Any

_AUTOGEN_SOURCE_PREFIX = "AUTO"
_EXCLUDED_LINK_KEYWORDS = (
    "login",
    "sign-in",
    "signin",
    "secure",
    "apply",
    "open-account",
    "openaccount",
    "promo",
    "offer",
    "compare",
    "modern-slavery",
    "human-trafficking",
    "privacy",
    "accessibility",
    "annual-report",
    "investor-relations",
    "modern slavery",
    "modern_slavery",
    "human_trafficking",
    "slavery",
)
_SUPPORTING_KEYWORDS = ("rate", "rates", "fee", "fees", "legal", "terms", "conditions", "service", "agreement", "disclosure")
_HUB_KEYWORDS = ("account", "accounts", "bank-account", "bank-accounts", "invest", "investments", "personal")
_PAGE_NEGATIVE_KEYWORDS = ("compare", "apply", "open account", "sign in", "login", "legal", "terms and conditions", "promotion", "offer")
_PRODUCT_TYPE_EXCLUSION_KEYWORDS = {
    "chequing": (
        "savings-account",
        "savings-accounts",
        "savings account",
        "savings accounts",
        "savings-amplifier",
        "premium-rate-savings",
        "us-prem-savings",
        "savings-builder",
        "gic",
        "guaranteed-investment",
        "mortgage",
        "credit-card",
        "credit cards",
        "loan",
        "loans",
    ),
    "savings": (
        "chequing-account",
        "chequing-accounts",
        "chequing account",
        "chequing accounts",
        "air-miles",
        "gic",
        "guaranteed-investment",
        "mortgage",
        "credit-card",
        "credit cards",
        "loan",
        "loans",
    ),
    "gic": (
        "chequing-account",
        "chequing-accounts",
        "chequing account",
        "chequing accounts",
        "savings-account",
        "savings-accounts",
        "savings account",
        "savings accounts",
        "mortgage",
        "credit-card",
        "credit cards",
        "loan",
        "loans",
    ),
}
_DISCOVERY_STOPWORDS = {
    "account",
    "accounts",
    "bank",
    "banking",
    "certificate",
    "daily",
    "deposit",
    "details",
    "focused",
    "guaranteed",
    "interest",
    "monthly",
    "official",
    "page",
    "pages",
    "product",
    "products",
    "public",
    "rules",
    "service",
    "with",
    "your",
}
_PRODUCT_TYPE_ATTRIBUTE_HINTS = {
    "chequing": ("transaction", "transactions", "debit", "everyday", "day-to-day", "monthly fee", "overdraft", "interac"),
    "savings": ("interest", "rate", "rates", "savings", "balance", "withdrawal", "tier", "tiering", "bonus"),
    "gic": ("term", "maturity", "redeemable", "non-redeemable", "minimum deposit", "compounding", "investment"),
}
_DISCOVERY_PROFILE_TERMS = {
    "chequing": ("chequing", "checking", "everyday banking", "transactions", "debit card", "monthly fee"),
    "savings": ("savings", "saving", "savings account", "high interest", "interest rate", "tiered interest", "withdrawal", "balance"),
    "gic": ("gic", "gics", "term deposit", "guaranteed investment", "maturity", "redeemable", "minimum deposit"),
}
_PAGE_EVIDENCE_MINIMUM_SCORE = 4
_AI_DISCOVERY_MAX_CANDIDATES = 12
_PAGE_EVIDENCE_MAX_CANDIDATES = 6


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


@dataclass(frozen=True)
class HomepageSourceGenerationResult:
    rows: list[dict[str, Any]]
    discovery_notes: list[str]
    detail_source_ids: list[str]
    model_execution_records: tuple[dict[str, Any], ...] = ()
    usage_records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class CatalogItemMaterializationResult:
    generated_rows: list[dict[str, Any]]
    discovery_notes: list[str]
    detail_source_ids: list[str]
    model_execution_records: tuple[dict[str, Any], ...] = ()
    usage_records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class AiParallelScoringResult:
    scores: dict[str, "AiParallelCandidateScore"]
    notes: list[str]
    model_execution_record: dict[str, Any] | None = None
    usage_record: dict[str, Any] | None = None


@dataclass(frozen=True)
class HomepageCandidate:
    normalized_url: str
    raw_url: str
    anchor_text: str
    source_type: str
    origin: str
    heuristic_score: int
    supporting_signal: bool
    seed_source_id: str | None
    source_name_hint: str | None
    priority_hint: str | None
    expected_fields_hint: list[str]


@dataclass(frozen=True)
class AiParallelCandidateScore:
    candidate_url: str
    predicted_role: str
    relevance_score: float
    confidence_band: str
    reason_codes: list[str]
    short_rationale: str


@dataclass(frozen=True)
class PageEvidenceAssessment:
    page_evidence_score: int
    page_evidence_reason_codes: list[str]
    page_title: str | None
    primary_heading: str | None
    heading_match: bool
    attribute_signal_count: int
    negative_signal_count: int
    fetch_error: str | None = None


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

    bank_codes = [str(row["bank_code"]) for row in rows]
    catalog_item_rows = connection.execute(
        """
        SELECT
            sci.catalog_item_id,
            sci.bank_code,
            sci.product_type,
            sci.status,
            COUNT(DISTINCT sri.source_id) AS generated_source_count
        FROM source_registry_catalog_item AS sci
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.product_type = sci.product_type
        WHERE sci.bank_code = ANY(%(bank_codes)s)
        GROUP BY sci.catalog_item_id, sci.bank_code, sci.product_type, sci.status
        ORDER BY sci.bank_code, sci.product_type
        """,
        {"bank_codes": bank_codes or [""]},
    ).fetchall() if bank_codes else []
    catalog_items_by_bank: dict[str, list[dict[str, Any]]] = {}
    for item in catalog_item_rows:
        catalog_items_by_bank.setdefault(str(item["bank_code"]), []).append(
            {
                "catalog_item_id": str(item["catalog_item_id"]),
                "product_type": str(item["product_type"]),
                "status": str(item["status"]),
                "generated_source_count": int(item["generated_source_count"] or 0),
            }
        )

    items = [
        _serialize_bank_row({**row, "catalog_items": catalog_items_by_bank.get(str(row["bank_code"]), [])})
        for row in rows
    ]
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
    bank_name = _required_text(payload.get("bank_name"), "bank_name")
    homepage_url, normalized_homepage_url = _normalize_bank_homepage_url(
        _required_text(payload.get("homepage_url"), "homepage_url")
    )
    initial_coverage_product_types = list(payload.get("initial_coverage_product_types") or [])
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
    for product_type in initial_coverage_product_types:
        create_source_catalog_item(
            connection,
            payload={
                "bank_code": bank_code,
                "product_type": product_type,
                "status": (_clean_text(payload.get("status")) or "active").lower(),
                "change_reason": _clean_text(payload.get("change_reason")),
            },
            actor=actor,
            request_context=request_context,
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
    homepage_url, normalized_homepage_url = _normalize_bank_homepage_url(
        _required_text(payload.get("homepage_url", existing_row["homepage_url"]), "homepage_url")
    )
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


def delete_bank_profile(
    connection: Connection,
    *,
    bank_code: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    normalized_bank_code = _required_text(bank_code, "bank_code").upper()
    detail = load_bank_detail(connection, bank_code=normalized_bank_code)
    if detail is None:
        raise SourceRegistryError(status_code=404, code="bank_profile_not_found", message="Bank profile was not found.")

    dependency_counts = connection.execute(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM source_registry_catalog_item
                WHERE bank_code = %(bank_code)s
            ) AS catalog_count,
            (
                SELECT COUNT(*)
                FROM source_registry_item
                WHERE bank_code = %(bank_code)s
            ) AS source_registry_count,
            (
                SELECT COUNT(*)
                FROM source_document
                WHERE bank_code = %(bank_code)s
            ) AS source_document_count,
            (
                SELECT COUNT(*)
                FROM normalized_candidate
                WHERE bank_code = %(bank_code)s
            ) AS candidate_count,
            (
                SELECT COUNT(*)
                FROM canonical_product
                WHERE bank_code = %(bank_code)s
            ) AS canonical_product_count,
            (
                SELECT COUNT(*)
                FROM public_product_projection
                WHERE bank_code = %(bank_code)s
            ) AS public_projection_count,
            (
                SELECT COUNT(*)
                FROM dashboard_ranking_snapshot
                WHERE bank_code = %(bank_code)s
            ) AS dashboard_ranking_count,
            (
                SELECT COUNT(*)
                FROM dashboard_scatter_snapshot
                WHERE bank_code = %(bank_code)s
            ) AS dashboard_scatter_count
        """,
        {"bank_code": normalized_bank_code},
    ).fetchone()
    blocking_dependency_total = sum(
        int((dependency_counts or {}).get(key) or 0)
        for key in (
            "source_document_count",
            "candidate_count",
            "canonical_product_count",
            "public_projection_count",
            "dashboard_ranking_count",
            "dashboard_scatter_count",
        )
    )
    if blocking_dependency_total > 0:
        raise SourceRegistryError(
            status_code=409,
            code="bank_profile_in_use",
            message="This bank already has collected source documents or downstream product history. Remove those dependent records before deleting the bank profile.",
        )

    connection.execute(
        """
        DELETE FROM source_registry_item
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": normalized_bank_code},
    )
    connection.execute(
        """
        DELETE FROM source_registry_catalog_item
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": normalized_bank_code},
    )
    connection.execute(
        """
        DELETE FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": normalized_bank_code},
    )
    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="bank_profile_deleted",
        target_id=normalized_bank_code,
        target_type="bank",
        diff_summary=f"Deleted bank profile `{normalized_bank_code}`.",
        metadata={
            "bank_code": normalized_bank_code,
            "bank_name": detail["bank"]["bank_name"],
            "deleted_catalog_count": int((dependency_counts or {}).get("catalog_count") or 0),
            "deleted_source_registry_count": int((dependency_counts or {}).get("source_registry_count") or 0),
        },
    )
    return detail["bank"]


def load_source_catalog_list(connection: Connection, *, filters: SourceCatalogFilters) -> dict[str, Any]:
    product_type_map = load_product_type_definitions_map(connection, active_only=False)
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
            "product_types": sorted(product_type_map),
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
    bank_code = _required_text(payload.get("bank_code"), "bank_code").upper()
    product_type = _canonical_product_type_code(_required_text(payload.get("product_type"), "product_type"))
    require_product_type_definition(connection, product_type_code=product_type, active_only=True)

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
          AND product_type = ANY(%(product_type_scope)s)
        """,
        {
            "bank_code": bank_code,
            "country_code": bank_row["country_code"],
            "product_type_scope": _product_type_scope_codes(product_type),
        },
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
    product_type = _canonical_product_type_code(_required_text(payload.get("product_type", existing["product_type"]), "product_type"))
    require_product_type_definition(connection, product_type_code=product_type, active_only=True)

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
          AND product_type = ANY(%(product_type_scope)s)
          AND catalog_item_id <> %(catalog_item_id)s
        """,
        {
            "bank_code": bank_code,
            "country_code": bank_row["country_code"],
            "product_type_scope": _product_type_scope_codes(product_type),
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
    retry_of_run_id: str | None = None,
) -> dict[str, Any]:
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

    collection_id = new_id("collection")
    correlation_id = new_id("corr")
    plan = _build_source_catalog_collection_plan(
        rows=rows,
        actor=actor,
        request_context=request_context,
        collection_id=collection_id,
        correlation_id=correlation_id,
    )

    for group in plan["groups"]:
        _insert_collection_run_row(
            connection,
            run_id=str(group["run_id"]),
            triggered_by=str(plan["triggered_by"]),
            request_id=request_context.get("request_id"),
            correlation_id=correlation_id,
            collection_id=collection_id,
            group=group,
            pipeline_stage="source_catalog_collection",
            retry_of_run_id=retry_of_run_id,
        )

    _record_catalog_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="source_catalog_collection_started",
        target_id=collection_id,
        target_type="source_catalog_collection",
        diff_summary=f"Queued source catalog collection for {len(rows)} catalog item(s).",
        metadata={
            "catalog_item_ids": list(catalog_item_ids),
            "run_ids": [str(group["run_id"]) for group in plan["groups"]],
            "retry_of_run_id": retry_of_run_id,
        },
    )
    _launch_source_catalog_collection_runner(plan)
    return _serialize_source_catalog_collection_launch(plan=plan, catalog_item_ids=catalog_item_ids)


def _build_source_catalog_collection_plan(
    *,
    rows: list[dict[str, Any]],
    actor: dict[str, Any],
    request_context: dict[str, Any],
    collection_id: str,
    correlation_id: str,
) -> dict[str, Any]:
    triggered_by = str(actor.get("email") or actor.get("display_name") or actor.get("user_id") or "admin")
    actor_payload = {
        "user_id": actor.get("user_id"),
        "email": actor.get("email"),
        "display_name": actor.get("display_name"),
        "role": actor.get("role"),
    }
    groups: list[dict[str, Any]] = []
    for row in rows:
        original_product_type = str(row["product_type"])
        product_type = _canonical_product_type_code(original_product_type)
        groups.append(
            {
                "run_id": _build_source_catalog_collection_run_id(
                    bank_code=str(row["bank_code"]),
                    product_type=product_type,
                ),
                "catalog_item_id": str(row["catalog_item_id"]),
                "bank_code": str(row["bank_code"]),
                "bank_name": str(row["bank_name"]),
                "country_code": str(row["country_code"]),
                "product_type": product_type,
                "source_catalog_product_type": original_product_type,
                "source_language": str(row.get("source_language") or "en"),
                "homepage_url": str(row["homepage_url"]),
                "normalized_homepage_url": str(row.get("normalized_homepage_url") or row["homepage_url"]),
                "selected_source_ids": [],
                "target_source_ids": [],
                "included_source_ids": [],
                "included_sources": [],
            }
        )

    return {
        "collection_id": collection_id,
        "correlation_id": correlation_id,
        "request_id": request_context.get("request_id"),
        "trigger_type": "admin_source_catalog_collection",
        "triggered_by": triggered_by,
        "actor": actor_payload,
        "groups": groups,
    }


def _launch_source_catalog_collection_runner(plan: dict[str, Any]) -> None:
    temp_dir = REPO_ROOT / "tmp" / "source-catalog-collections"
    temp_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    current_python_path = env.get("PYTHONPATH", "")
    api_service_path = str(REPO_ROOT / "api" / "service")
    env["PYTHONPATH"] = os.pathsep.join([api_service_path, current_python_path]) if current_python_path else api_service_path

    for group in plan.get("groups", []):
        group_plan = {
            **plan,
            "groups": [group],
        }
        run_id = str(group["run_id"])
        plan_path = temp_dir / f"{run_id}.json"
        log_path = temp_dir / f"{run_id}.log"
        plan_path.write_text(json.dumps(group_plan, indent=2, ensure_ascii=True), encoding="utf-8")

        with log_path.open("a", encoding="utf-8") as log_file:
            try:
                subprocess.Popen(  # noqa: S603
                    [sys.executable, "-m", "api_service.source_catalog_collection_runner", "--plan-path", str(plan_path)],
                    cwd=str(REPO_ROOT),
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
            except OSError as exc:
                raise SourceRegistryError(
                    status_code=500,
                    code="source_catalog_collection_launch_failed",
                    message=f"Source catalog collection could not be launched: {exc}",
                ) from exc


def _serialize_source_catalog_collection_launch(*, plan: dict[str, Any], catalog_item_ids: list[str]) -> dict[str, Any]:
    return {
        "collection_id": str(plan["collection_id"]),
        "correlation_id": str(plan["correlation_id"]),
        "run_ids": [str(group["run_id"]) for group in plan["groups"]],
        "selected_source_ids": [],
        "target_source_ids": [],
        "auto_included_source_ids": [],
        "groups": [
            {
                "run_id": str(group["run_id"]),
                "bank_code": str(group["bank_code"]),
                "country_code": str(group["country_code"]),
                "product_type": str(group["product_type"]),
                "source_language": str(group["source_language"]),
                "target_source_ids": [],
                "included_source_ids": [],
            }
            for group in plan["groups"]
        ],
        "catalog_item_ids": list(catalog_item_ids),
        "materialized_items": [],
        "workflow_state": "queued",
        "queued_catalog_item_count": len(plan["groups"]),
    }


def _materialize_sources_for_catalog_item(
    connection: Connection,
    *,
    row: dict[str, Any],
    run_id: str | None = None,
    correlation_id: str | None = None,
    request_id: str | None = None,
) -> CatalogItemMaterializationResult:
    bank_code = str(row["bank_code"])
    original_product_type = str(row["product_type"])
    product_type = _canonical_product_type_code(original_product_type)
    product_type_definition = require_product_type_definition(connection, product_type_code=product_type, active_only=False)
    generation_result = _generate_sources_from_homepage(
        bank_code=bank_code,
        bank_name=str(row["bank_name"]),
        country_code=str(row["country_code"]),
        product_type=product_type,
        product_type_definition=product_type_definition,
        homepage_url=str(row["homepage_url"]),
        source_language=str(row.get("source_language") or "en"),
        run_id=run_id,
        correlation_id=correlation_id,
        request_id=request_id,
    )
    generated_rows = _dedupe_generated_source_rows(generation_result.rows)
    discovery_notes = list(generation_result.discovery_notes)
    if product_type != original_product_type:
        discovery_notes.append(f"Product type `{original_product_type}` was normalized to `{product_type}` for source collection.")
    if generation_result.detail_source_ids:
        connection.execute(
            """
            UPDATE source_registry_item
            SET
                status = 'inactive',
                updated_at = %(updated_at)s,
                change_reason = %(change_reason)s
            WHERE bank_code = %(bank_code)s
              AND product_type = ANY(%(product_type_scope)s)
              AND status <> 'removed'
            """,
            {
                "updated_at": utc_now(),
                "change_reason": "superseded_by_homepage_catalog_generation",
                "bank_code": bank_code,
                "product_type_scope": _product_type_scope_codes(product_type),
            },
        )
    else:
        discovery_notes.append(
            "Existing active detail sources were preserved because homepage discovery did not produce replacement detail sources."
        )
    persisted_rows = _upsert_source_registry_rows(connection, generated_rows) if generated_rows else []
    _persist_source_catalog_usage_records(
        connection,
        model_execution_records=list(generation_result.model_execution_records),
        usage_records=list(generation_result.usage_records),
    )
    return CatalogItemMaterializationResult(
        generated_rows=persisted_rows,
        discovery_notes=_dedupe_preserve_order([note for note in discovery_notes if note]),
        detail_source_ids=list(generation_result.detail_source_ids),
        model_execution_records=generation_result.model_execution_records,
        usage_records=generation_result.usage_records,
    )


def _upsert_source_registry_rows(connection: Connection, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = utc_now()
    persisted_rows: list[dict[str, Any]] = []
    for item in rows:
        row = connection.execute(
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
                discovery_metadata,
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
                %(discovery_metadata)s::jsonb,
                %(change_reason)s,
                %(created_at)s,
                %(updated_at)s
            )
            ON CONFLICT (bank_code, product_type, normalized_url, source_type) DO UPDATE
            SET
                country_code = EXCLUDED.country_code,
                product_key = EXCLUDED.product_key,
                source_name = EXCLUDED.source_name,
                source_url = EXCLUDED.source_url,
                discovery_role = EXCLUDED.discovery_role,
                status = CASE
                    WHEN source_registry_item.status = 'removed' THEN source_registry_item.status
                    ELSE EXCLUDED.status
                END,
                priority = EXCLUDED.priority,
                source_language = EXCLUDED.source_language,
                purpose = EXCLUDED.purpose,
                expected_fields = EXCLUDED.expected_fields,
                seed_source_flag = EXCLUDED.seed_source_flag,
                redirect_target_url = EXCLUDED.redirect_target_url,
                alias_urls = EXCLUDED.alias_urls,
                discovery_metadata = EXCLUDED.discovery_metadata,
                change_reason = CASE
                    WHEN source_registry_item.status = 'removed' THEN source_registry_item.change_reason
                    ELSE EXCLUDED.change_reason
                END,
                updated_at = EXCLUDED.updated_at
            RETURNING
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
                discovery_metadata,
                change_reason
            """,
            {
                **item,
                "expected_fields": json.dumps(item.get("expected_fields", []), ensure_ascii=True),
                "alias_urls": json.dumps(item.get("alias_urls", []), ensure_ascii=True),
                "discovery_metadata": json.dumps(item.get("discovery_metadata", {}), ensure_ascii=True),
                "created_at": now,
                "updated_at": now,
            },
        ).fetchone()
        if row is None:
            raise SourceRegistryError(status_code=500, code="source_registry_upsert_failed", message="Generated source row could not be reloaded after upsert.")
        persisted_rows.append(dict(row))
    return persisted_rows


def _persist_source_catalog_usage_records(
    connection: Connection,
    *,
    model_execution_records: list[dict[str, Any]],
    usage_records: list[dict[str, Any]],
) -> None:
    for item in model_execution_records:
        connection.execute(
            """
            INSERT INTO model_execution (
                model_execution_id,
                run_id,
                source_document_id,
                stage_name,
                agent_name,
                model_id,
                execution_status,
                execution_metadata,
                started_at,
                completed_at
            )
            VALUES (
                %(model_execution_id)s,
                %(run_id)s,
                %(source_document_id)s,
                %(stage_name)s,
                %(agent_name)s,
                %(model_id)s,
                %(execution_status)s,
                %(execution_metadata)s::jsonb,
                %(started_at)s,
                %(completed_at)s
            )
            ON CONFLICT (model_execution_id) DO UPDATE SET
                model_id = EXCLUDED.model_id,
                execution_status = EXCLUDED.execution_status,
                execution_metadata = EXCLUDED.execution_metadata,
                completed_at = EXCLUDED.completed_at
            """,
            {
                **item,
                "execution_metadata": json.dumps(item.get("execution_metadata") or {}, ensure_ascii=True),
            },
        )

    for item in usage_records:
        connection.execute(
            """
            INSERT INTO llm_usage_record (
                llm_usage_id,
                model_execution_id,
                run_id,
                candidate_id,
                provider_request_id,
                prompt_tokens,
                completion_tokens,
                estimated_cost,
                usage_metadata,
                recorded_at
            )
            VALUES (
                %(llm_usage_id)s,
                %(model_execution_id)s,
                %(run_id)s,
                %(candidate_id)s,
                %(provider_request_id)s,
                %(prompt_tokens)s,
                %(completion_tokens)s,
                %(estimated_cost)s,
                %(usage_metadata)s::jsonb,
                %(recorded_at)s
            )
            ON CONFLICT (llm_usage_id) DO UPDATE SET
                provider_request_id = EXCLUDED.provider_request_id,
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                estimated_cost = EXCLUDED.estimated_cost,
                usage_metadata = EXCLUDED.usage_metadata,
                recorded_at = EXCLUDED.recorded_at
            """,
            {
                **item,
                "usage_metadata": json.dumps(item.get("usage_metadata") or {}, ensure_ascii=True),
            },
        )


def _generate_sources_from_homepage(
    *,
    bank_code: str,
    bank_name: str,
    country_code: str,
    product_type: str,
    product_type_definition: dict[str, Any],
    homepage_url: str,
    source_language: str,
    run_id: str | None = None,
    correlation_id: str | None = None,
    request_id: str | None = None,
) -> HomepageSourceGenerationResult:
    product_type = _canonical_product_type_code(product_type)
    discovery_product_type = _product_type_discovery_profile(product_type, product_type_definition)
    normalized_homepage_url = normalize_source_url(homepage_url)
    hostname = urlparse(normalized_homepage_url).hostname
    if not hostname:
        raise SourceRegistryError(status_code=422, code="bank_homepage_invalid", message="Bank homepage URL must include a hostname.")

    fetch_policy = DiscoveryFetchPolicy(allowed_domains=(hostname,))
    detail_links: list[tuple[int, Any]] = []
    supporting_links: list[tuple[int, Any]] = []
    pdf_links: list[tuple[int, Any]] = []
    hub_pages: list[tuple[int, str, str]] = []
    discovery_notes: list[str] = []
    if discovery_product_type != product_type:
        discovery_notes.append(
            f"Homepage discovery used `{discovery_product_type}` discovery signals from the product type definition while preserving registered product type `{product_type}`."
        )
    homepage_fetch_error: str | None = None
    try:
        homepage_html = fetch_text(normalized_homepage_url, fetch_policy)
    except Exception as exc:
        homepage_html = ""
        homepage_fetch_error = str(exc)
        discovery_notes.append(f"Homepage fetch was unavailable: {homepage_fetch_error}")

    homepage_links = _extract_allowed_links(html_text=homepage_html, base_url=normalized_homepage_url, hostname=hostname)
    if homepage_html and not homepage_links:
        discovery_notes.append("Homepage fetch succeeded but no allowed detail or supporting links were extracted.")
    for link in homepage_links:
        fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
        if any(keyword in fingerprint for keyword in _EXCLUDED_LINK_KEYWORDS):
            continue
        score = _score_product_link(
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
        )
        if link.source_type == "pdf":
            if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                pdf_links.append((score, link))
            continue
        if score > 0:
            detail_links.append((score, link))
        elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
            supporting_links.append((1, link))
        hub_score = _score_catalog_hub_link(
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
        )
        if hub_score > 0:
            hub_pages.append((hub_score, link.normalized_url, link.resolved_url))

    seed_entry_url = _load_seed_entry_url(bank_code=bank_code, product_type=discovery_product_type)
    if seed_entry_url is not None:
        seed_score = _score_catalog_hub_link(
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=seed_entry_url,
            anchor_text="",
        )
        hub_pages.append((max(seed_score, 1), seed_entry_url, seed_entry_url))

    unique_hub_pages = _dedupe_page_candidates(hub_pages)
    for _score, normalized_page_url, resolved_page_url in unique_hub_pages[:3]:
        if normalized_page_url == normalized_homepage_url:
            continue
        try:
            page_html = fetch_text(resolved_page_url, fetch_policy)
        except Exception as exc:
            discovery_notes.append(f"Hub page fetch was unavailable for {normalized_page_url}: {exc}")
            continue
        for link in _extract_allowed_links(html_text=page_html, base_url=normalized_page_url, hostname=hostname):
            fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
            if any(keyword in fingerprint for keyword in _EXCLUDED_LINK_KEYWORDS):
                continue
            score = _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            )
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
    seed_detail_hints = _load_seed_detail_hints(bank_code=bank_code, product_type=discovery_product_type)
    seed_supporting_hints = _load_seed_supporting_hints(bank_code=bank_code, product_type=discovery_product_type)
    source_rows: list[dict[str, Any]] = []
    entry_url = unique_hub_pages[0][1] if unique_hub_pages else normalized_homepage_url
    entry_raw_url = unique_hub_pages[0][2] if unique_hub_pages else homepage_url
    product_type_label = _product_type_label(product_type_definition)
    expected_fields = _product_type_expected_fields(product_type_definition)
    html_candidates = _build_html_candidates(
        product_type=product_type,
        discovery_product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        detail_links=unique_detail_links,
        supporting_links=unique_supporting_links,
        seed_detail_hints=seed_detail_hints,
    )
    ai_result = _score_candidate_links_with_ai(
        bank_code=bank_code,
        bank_name=bank_name,
        country_code=country_code,
        product_type=product_type,
        discovery_product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        source_language=source_language,
        homepage_url=homepage_url,
        normalized_homepage_url=normalized_homepage_url,
        homepage_fetch_error=homepage_fetch_error,
        candidates=html_candidates,
        run_id=run_id,
        correlation_id=correlation_id,
        request_id=request_id,
    )
    discovery_notes.extend(ai_result.notes)
    detail_rows, detail_notes = _promote_detail_candidates(
        bank_code=bank_code,
        bank_name=bank_name,
        country_code=country_code,
        product_type=product_type,
        discovery_product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        source_language=source_language,
        fetch_policy=fetch_policy,
        candidates=html_candidates,
        ai_scores=ai_result.scores,
    )
    discovery_notes.extend(detail_notes)

    if detail_rows:
        source_rows.append(
            _build_generated_source_row(
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                source_language=source_language,
                normalized_url=entry_url,
                raw_url=entry_raw_url,
                source_name=f"{bank_name} {product_type_label} catalog entry",
                discovery_role="entry",
                priority="P0",
                purpose=f"{bank_name} {product_type_label} catalog discovery entry",
                expected_fields=["product_name"],
                discovery_metadata={
                    "selection_path": "entry_seed",
                    "selection_confidence": "n/a",
                    "selection_reason_codes": ["catalog_entry_context"],
                    "candidate_origin": "hub_page" if unique_hub_pages else "homepage",
                },
            )
        )
        source_rows.extend(detail_rows)
    else:
        if html_candidates:
            discovery_notes.append("Homepage discovery completed but candidate validation did not promote any detail sources.")
        else:
            discovery_notes.append("Homepage discovery completed but no candidate-producing detail sources were identified.")

    promoted_detail_urls = {str(item["normalized_url"]) for item in detail_rows}
    promoted_supporting_urls: set[str] = set()
    if detail_rows:
        for hint in seed_supporting_hints:
            normalized_url = normalize_source_url(str(hint["source_url"]))
            if normalized_url in promoted_detail_urls or normalized_url in promoted_supporting_urls:
                continue
            discovery_role = str(hint.get("discovery_role") or "supporting_html")
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=normalized_url,
                    raw_url=str(hint["source_url"]),
                    source_name=str(hint.get("source_name") or hint.get("purpose") or f"{bank_name} {product_type_label} support"),
                    discovery_role=discovery_role,
                    priority=str(hint.get("priority") or "P1"),
                    purpose=str(hint.get("purpose") or f"Seeded supporting source for {product_type_label}"),
                    expected_fields=[str(item) for item in (hint.get("expected_fields") or []) if str(item).strip()] or expected_fields,
                    discovery_metadata={
                        "selection_path": "seed_supporting_hint",
                        "selection_confidence": "high",
                        "selection_reason_codes": ["seed_hint_alignment", "supporting_source_seed"],
                        "candidate_origin": "seed_supporting_hint",
                    },
                )
            )
            source_rows[-1]["source_id"] = str(hint["source_id"])
            promoted_supporting_urls.add(normalized_url)
        for _, link in unique_supporting_links:
            if link.normalized_url in promoted_detail_urls:
                continue
            if link.normalized_url in promoted_supporting_urls:
                continue
            if not _link_is_relevant_supporting_source(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=link.normalized_url,
                    raw_url=link.resolved_url,
                    source_name=_generated_link_name(
                        bank_name,
                        product_type_label,
                        link.anchor_text,
                        fallback="support",
                        normalized_url=link.normalized_url,
                    ),
                    discovery_role="supporting_html",
                    priority="P2",
                    purpose=f"Auto-generated supporting source for {product_type_label}",
                    expected_fields=expected_fields,
                    discovery_metadata={
                        "selection_path": "supporting_only",
                        "selection_confidence": "medium" if _score_product_link(
                            product_type=discovery_product_type,
                            product_type_definition=product_type_definition,
                            normalized_url=link.normalized_url,
                            anchor_text=link.anchor_text,
                        ) > 0 else "low",
                        "selection_reason_codes": ["supporting_keyword_match"],
                        "candidate_origin": "homepage_or_hub_link",
                        "heuristic_score": _score_product_link(
                            product_type=discovery_product_type,
                            product_type_definition=product_type_definition,
                            normalized_url=link.normalized_url,
                            anchor_text=link.anchor_text,
                        ),
                    },
                )
            )
        for _, link in unique_pdf_links:
            if not _link_is_relevant_supporting_source(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=link.normalized_url,
                    raw_url=link.resolved_url,
                    source_name=_generated_link_name(
                        bank_name,
                        product_type_label,
                        link.anchor_text,
                        fallback="pdf",
                        normalized_url=link.normalized_url,
                    ),
                    discovery_role="linked_pdf",
                    priority="P2",
                    purpose=f"Auto-generated linked PDF source for {product_type_label}",
                    expected_fields=expected_fields,
                    discovery_metadata={
                        "selection_path": "linked_pdf",
                        "selection_confidence": "medium",
                        "selection_reason_codes": ["supporting_pdf_signal"],
                        "candidate_origin": "homepage_or_hub_link",
                        "heuristic_score": _score_product_link(
                            product_type=discovery_product_type,
                            product_type_definition=product_type_definition,
                            normalized_url=link.normalized_url,
                            anchor_text=link.anchor_text,
                        ),
                    },
                )
            )
    detail_source_ids = [
        str(item["source_id"])
        for item in source_rows
        if str(item["discovery_role"]) == "detail" and str(item["status"]) != "removed"
    ]
    return HomepageSourceGenerationResult(
        rows=source_rows,
        discovery_notes=_dedupe_preserve_order([note for note in discovery_notes if note]),
        detail_source_ids=detail_source_ids,
        model_execution_records=tuple(
            item for item in [ai_result.model_execution_record] if item is not None
        ),
        usage_records=tuple(item for item in [ai_result.usage_record] if item is not None),
    )


def _build_html_candidates(
    *,
    product_type: str,
    discovery_product_type: str | None = None,
    product_type_definition: dict[str, Any],
    detail_links: list[tuple[int, Any]],
    supporting_links: list[tuple[int, Any]],
    seed_detail_hints: list[dict[str, Any]],
) -> list[HomepageCandidate]:
    scoring_product_type = discovery_product_type or product_type
    by_url: dict[str, HomepageCandidate] = {}
    for score, link in [*detail_links, *supporting_links]:
        supporting_signal = any(keyword in f"{link.normalized_url} {link.anchor_text}".lower() for keyword in _SUPPORTING_KEYWORDS)
        candidate = HomepageCandidate(
            normalized_url=str(link.normalized_url),
            raw_url=str(link.resolved_url),
            anchor_text=str(link.anchor_text),
            source_type=str(link.source_type),
            origin="homepage_or_hub_link",
            heuristic_score=int(score),
            supporting_signal=supporting_signal,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        _merge_homepage_candidate(by_url, candidate)

    for hint in seed_detail_hints:
        normalized_url = normalize_source_url(str(hint["source_url"]))
        candidate = HomepageCandidate(
            normalized_url=normalized_url,
            raw_url=str(hint["source_url"]),
            anchor_text=str(hint.get("source_name") or ""),
            source_type=infer_source_type(normalized_url),
            origin="seed_detail_hint",
            heuristic_score=_score_product_link(
                product_type=scoring_product_type,
                product_type_definition=product_type_definition,
                normalized_url=normalized_url,
                anchor_text=str(hint.get("source_name") or ""),
            ),
            supporting_signal=False,
            seed_source_id=str(hint.get("source_id") or "") or None,
            source_name_hint=str(hint.get("source_name") or "") or None,
            priority_hint=str(hint.get("priority") or "P1"),
            expected_fields_hint=[str(item) for item in (hint.get("expected_fields") or []) if str(item).strip()],
        )
        _merge_homepage_candidate(by_url, candidate)

    candidates = list(by_url.values())
    candidates.sort(
        key=lambda item: (
            0 if item.origin == "seed_detail_hint" else 1,
            -item.heuristic_score,
            item.normalized_url,
        )
    )
    return candidates[:_AI_DISCOVERY_MAX_CANDIDATES]


def _merge_homepage_candidate(by_url: dict[str, HomepageCandidate], candidate: HomepageCandidate) -> None:
    current = by_url.get(candidate.normalized_url)
    if current is None:
        by_url[candidate.normalized_url] = candidate
        return
    if (
        candidate.origin == "seed_detail_hint"
        and current.origin != "seed_detail_hint"
        or candidate.heuristic_score > current.heuristic_score
    ):
        by_url[candidate.normalized_url] = HomepageCandidate(
            normalized_url=candidate.normalized_url,
            raw_url=candidate.raw_url,
            anchor_text=candidate.anchor_text or current.anchor_text,
            source_type=candidate.source_type,
            origin=candidate.origin,
            heuristic_score=max(candidate.heuristic_score, current.heuristic_score),
            supporting_signal=current.supporting_signal or candidate.supporting_signal,
            seed_source_id=candidate.seed_source_id or current.seed_source_id,
            source_name_hint=candidate.source_name_hint or current.source_name_hint,
            priority_hint=candidate.priority_hint or current.priority_hint,
            expected_fields_hint=candidate.expected_fields_hint or current.expected_fields_hint,
        )
        return
    by_url[candidate.normalized_url] = HomepageCandidate(
        normalized_url=current.normalized_url,
        raw_url=current.raw_url,
        anchor_text=current.anchor_text or candidate.anchor_text,
        source_type=current.source_type,
        origin=current.origin,
        heuristic_score=max(current.heuristic_score, candidate.heuristic_score),
        supporting_signal=current.supporting_signal or candidate.supporting_signal,
        seed_source_id=current.seed_source_id or candidate.seed_source_id,
        source_name_hint=current.source_name_hint or candidate.source_name_hint,
        priority_hint=current.priority_hint or candidate.priority_hint,
        expected_fields_hint=current.expected_fields_hint or candidate.expected_fields_hint,
    )


def _load_seed_entry_url(*, bank_code: str, product_type: str) -> str | None:
    product_type = _canonical_product_type_code(product_type)
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) == bank_code
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) == "entry"
        ):
            return str(item["normalized_url"])
    return None


def _load_seed_detail_hints(*, bank_code: str, product_type: str) -> list[dict[str, Any]]:
    product_type = _canonical_product_type_code(product_type)
    hints: list[dict[str, Any]] = []
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) == bank_code
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) == "detail"
        ):
            hints.append(
                {
                    "source_id": str(item["source_id"]),
                    "source_name": str(item.get("source_name") or item.get("purpose") or item["source_id"]),
                    "source_url": str(item["source_url"]),
                    "normalized_url": str(item["normalized_url"]),
                    "expected_fields": list(item.get("expected_fields") or []),
                    "purpose": str(item.get("purpose") or ""),
                    "priority": str(item.get("priority") or "P1"),
                }
            )
    return hints


def _load_seed_supporting_hints(*, bank_code: str, product_type: str) -> list[dict[str, Any]]:
    product_type = _canonical_product_type_code(product_type)
    hints: list[dict[str, Any]] = []
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) == bank_code
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) in {"supporting_html", "supporting_pdf", "linked_pdf"}
        ):
            hints.append(
                {
                    "source_id": str(item["source_id"]),
                    "source_name": str(item.get("source_name") or item.get("purpose") or item["source_id"]),
                    "source_url": str(item["source_url"]),
                    "normalized_url": str(item["normalized_url"]),
                    "source_type": str(item.get("source_type") or infer_source_type(str(item["source_url"]))),
                    "discovery_role": str(item["discovery_role"]),
                    "expected_fields": list(item.get("expected_fields") or []),
                    "purpose": str(item.get("purpose") or ""),
                    "priority": str(item.get("priority") or "P1"),
                }
            )
    return hints


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _score_candidate_links_with_ai(
    *,
    bank_code: str,
    bank_name: str,
    country_code: str,
    product_type: str,
    discovery_product_type: str | None = None,
    product_type_definition: dict[str, Any],
    source_language: str,
    homepage_url: str,
    normalized_homepage_url: str,
    homepage_fetch_error: str | None,
    candidates: list[HomepageCandidate],
    run_id: str | None = None,
    correlation_id: str | None = None,
    request_id: str | None = None,
) -> AiParallelScoringResult:
    if not candidates:
        return AiParallelScoringResult(scores={}, notes=[])
    provider = os.getenv("FPDS_LLM_PROVIDER", "openai").strip().lower()
    api_key = os.getenv("FPDS_LLM_API_KEY", "").strip()
    if provider != "openai" or not api_key:
        return AiParallelScoringResult(
            scores={},
            notes=["AI parallel scorer was unavailable because the OpenAI provider or API key was not configured."],
        )

    candidate_links = [
        {
            "candidate_url": item.normalized_url,
            "candidate_label": item.anchor_text or item.source_name_hint or item.normalized_url,
            "source_type": item.source_type,
            "heuristic_score": item.heuristic_score,
            "candidate_origin": item.origin,
        }
        for item in candidates
    ]
    model_id = os.getenv("FPDS_LLM_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini"
    started_at = datetime.now(UTC)
    try:
        resolution, usage = _invoke_openai_parallel_scorer(
            model_id=model_id,
            api_key=api_key,
            payload={
                "bank_code": bank_code,
                "bank_name": bank_name,
                "country_code": country_code,
                "product_type": product_type,
                "discovery_product_type": discovery_product_type or product_type,
                "product_type_definition": {
                    "display_name": _product_type_label(product_type_definition),
                    "description": str(product_type_definition.get("description") or ""),
                    "discovery_keywords": _product_type_keywords(product_type_definition),
                    "expected_fields": _product_type_expected_fields(product_type_definition),
                    "fallback_policy": str(product_type_definition.get("fallback_policy") or "generic_ai_review"),
                },
                "source_language": source_language,
                "homepage_url": homepage_url,
                "normalized_homepage_url": normalized_homepage_url,
                "homepage_fetch_error": homepage_fetch_error,
                "candidate_links": candidate_links,
            },
        )
    except Exception as exc:
        return AiParallelScoringResult(scores={}, notes=[f"AI parallel scorer was unavailable: {exc}"])
    completed_at = datetime.now(UTC)

    notes = [str(resolution.get("summary") or "").strip()] if str(resolution.get("summary") or "").strip() else []
    hostname = urlparse(normalized_homepage_url).hostname or ""
    scores: dict[str, AiParallelCandidateScore] = {}
    valid_candidate_urls = {item.normalized_url for item in candidates}
    for item in resolution.get("candidate_scores", []):
        candidate_url = str(item.get("candidate_url") or "").strip()
        if not candidate_url:
            continue
        normalized_url = normalize_source_url(candidate_url)
        parsed_hostname = urlparse(normalized_url).hostname or ""
        candidate_label = str(item.get("candidate_label") or normalized_url)
        if normalized_url not in valid_candidate_urls:
            notes.append(f"AI scored an unbounded candidate for {candidate_label}; the score was ignored.")
            continue
        if not parsed_hostname or not (parsed_hostname == hostname or parsed_hostname.endswith(f".{hostname}")):
            notes.append(f"AI scored an out-of-scope URL for {candidate_label}; the score was ignored.")
            continue
        if infer_source_type(normalized_url) != "html":
            notes.append(f"AI scored a non-HTML URL for {candidate_label}; the score was ignored.")
            continue
        scores[normalized_url] = AiParallelCandidateScore(
            candidate_url=normalized_url,
            predicted_role=str(item.get("predicted_role") or "irrelevant"),
            relevance_score=float(item.get("relevance_score") or 0.0),
            confidence_band=str(item.get("confidence_band") or "low"),
            reason_codes=[str(code) for code in (item.get("reason_codes") or []) if str(code).strip()],
            short_rationale=str(item.get("short_rationale") or "").strip(),
        )
    if scores:
        notes.append(f"AI parallel scorer evaluated {len(scores)} candidate link(s).")
    else:
        notes.append("AI parallel scorer returned no usable candidate scores.")
    model_execution_record = None
    usage_record = None
    if run_id:
        model_execution_id = _build_source_catalog_ai_model_execution_id(
            run_id=run_id,
            bank_code=bank_code,
            product_type=product_type,
            normalized_homepage_url=normalized_homepage_url,
        )
        model_execution_record = {
            "model_execution_id": model_execution_id,
            "run_id": run_id,
            "source_document_id": None,
            "stage_name": "source_catalog_collection",
            "agent_name": "fpds-homepage-ai-parallel-scorer",
            "model_id": str(usage.get("model_id") or model_id),
            "execution_status": "completed",
            "execution_metadata": {
                "bank_code": bank_code,
                "country_code": country_code,
                "product_type": product_type,
                "discovery_product_type": discovery_product_type or product_type,
                "source_language": source_language,
                "homepage_url": homepage_url,
                "normalized_homepage_url": normalized_homepage_url,
                "homepage_fetch_error": homepage_fetch_error,
                "candidate_link_count": len(candidate_links),
                "scored_candidate_count": len(scores),
                "correlation_id": correlation_id,
                "request_id": request_id,
            },
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
        }
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        usage_record = {
            "llm_usage_id": _build_source_catalog_ai_usage_id(model_execution_id),
            "model_execution_id": model_execution_id,
            "run_id": run_id,
            "candidate_id": None,
            "provider_request_id": usage.get("provider_request_id"),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost": estimated_cost_usd(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            "usage_metadata": {
                "usage_mode": "openai-homepage-parallel-scoring",
                "provider": "openai",
                "model_id": str(usage.get("model_id") or model_id),
            },
            "recorded_at": completed_at.isoformat(),
        }
    return AiParallelScoringResult(
        scores=scores,
        notes=_dedupe_preserve_order([note for note in notes if note]),
        model_execution_record=model_execution_record,
        usage_record=usage_record,
    )


def _invoke_openai_parallel_scorer(*, model_id: str, api_key: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    request_body = {
        "model": model_id,
        "instructions": (
            "You score bounded Canadian bank candidate URLs for homepage-first product discovery. "
            "Do not invent URLs. Score only the candidate links provided. "
            "Return whether each candidate is likely an official public detail page, a supporting page, or irrelevant for the given product type."
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=True),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "homepage_parallel_candidate_scores",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "summary": {"type": "string"},
                        "candidate_scores": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "candidate_url": {"type": "string"},
                                    "candidate_label": {"type": "string"},
                                    "predicted_role": {"type": "string", "enum": ["detail", "supporting_html", "irrelevant"]},
                                    "relevance_score": {"type": "number"},
                                    "confidence_band": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "reason_codes": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "short_rationale": {"type": "string"},
                                },
                                "required": [
                                    "candidate_url",
                                    "candidate_label",
                                    "predicted_role",
                                    "relevance_score",
                                    "confidence_band",
                                    "reason_codes",
                                    "short_rationale",
                                ],
                            },
                        },
                    },
                    "required": ["summary", "candidate_scores"],
                },
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body, ensure_ascii=True).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API request failed with status {exc.code}: {response_body}") from exc

    response_text = _extract_response_output_text(response_payload)
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI parallel scorer returned invalid JSON: {response_text}") from exc
    usage = response_payload.get("usage") or {}
    return parsed, {
        "provider": "openai",
        "model_id": str(response_payload.get("model") or model_id),
        "provider_request_id": response_payload.get("id"),
        "prompt_tokens": int(usage.get("input_tokens") or 0),
        "completion_tokens": int(usage.get("output_tokens") or 0),
    }


def _extract_response_output_text(response_payload: dict[str, Any]) -> str:
    for item in response_payload.get("output", []):
        if str(item.get("type")) != "message":
            continue
        for content in item.get("content", []):
            content_type = str(content.get("type") or "")
            if content_type == "refusal":
                raise RuntimeError(str(content.get("refusal") or "OpenAI refused the homepage discovery request."))
            if content_type == "output_text" and content.get("text"):
                return str(content["text"])
    raise RuntimeError("OpenAI discovery scorer returned no text output.")


def _promote_detail_candidates(
    *,
    bank_code: str,
    bank_name: str,
    country_code: str,
    product_type: str,
    discovery_product_type: str,
    product_type_definition: dict[str, Any],
    source_language: str,
    fetch_policy: DiscoveryFetchPolicy,
    candidates: list[HomepageCandidate],
    ai_scores: dict[str, AiParallelCandidateScore],
) -> tuple[list[dict[str, Any]], list[str]]:
    product_type_label = _product_type_label(product_type_definition)
    expected_fields = _product_type_expected_fields(product_type_definition)
    notes: list[str] = []
    detail_rows: list[dict[str, Any]] = []
    promoted_count = 0
    seed_fetch_fallback_count = 0
    seed_low_evidence_fallback_count = 0
    evaluated = 0
    for candidate in _ordered_detail_candidates(candidates=candidates, ai_scores=ai_scores):
        ai_score = ai_scores.get(candidate.normalized_url)
        if ai_score and ai_score.predicted_role == "irrelevant" and not candidate.seed_source_id:
            continue
        if not candidate.seed_source_id and candidate.heuristic_score <= 0 and (ai_score is None or ai_score.predicted_role != "detail"):
            continue
        evaluated += 1
        page_evidence = _score_page_evidence(
            raw_url=candidate.raw_url,
            fetch_policy=fetch_policy,
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
        )
        if page_evidence.fetch_error:
            notes.append(f"Page evidence was unavailable for {candidate.normalized_url}: {page_evidence.fetch_error}")
            if not candidate.seed_source_id:
                continue
            metadata = {
                "selection_path": "seed_hint_fetch_unavailable",
                "selection_confidence": "medium",
                "selection_reason_codes": ["seed_hint_alignment", "page_fetch_unavailable"],
                "candidate_origin": candidate.origin,
                "heuristic_score": candidate.heuristic_score,
                "ai_parallel_score": ai_score.relevance_score if ai_score is not None else None,
                "ai_predicted_role": ai_score.predicted_role if ai_score is not None else None,
                "ai_confidence_band": ai_score.confidence_band if ai_score is not None else None,
                "ai_reason_codes": _coerce_reason_codes(ai_score.reason_codes) if ai_score is not None else [],
                "ai_short_rationale": ai_score.short_rationale if ai_score is not None else None,
                "page_evidence_score": 0,
                "page_evidence_reason_codes": ["page_fetch_unavailable"],
                "page_title": None,
                "primary_heading": None,
                "heading_match": False,
                "attribute_signal_count": 0,
                "negative_signal_count": 0,
                "fetch_error": page_evidence.fetch_error,
            }
            seed_fetch_fallback_count += 1
        else:
            if not _candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=page_evidence):
                if not candidate.seed_source_id or page_evidence.negative_signal_count >= 2:
                    continue
                metadata = _build_detail_discovery_metadata(
                    candidate=candidate,
                    ai_score=ai_score,
                    page_evidence=page_evidence,
                )
                metadata["selection_path"] = "seed_hint_low_page_evidence"
                metadata["selection_confidence"] = "medium-low"
                metadata["selection_reason_codes"] = _dedupe_preserve_order(
                    [
                        *list(metadata.get("selection_reason_codes") or []),
                        "seed_hint_alignment",
                        "page_evidence_below_threshold",
                    ]
                )
                seed_low_evidence_fallback_count += 1
            else:
                metadata = _build_detail_discovery_metadata(
                    candidate=candidate,
                    ai_score=ai_score,
                    page_evidence=page_evidence,
                )
        row = _build_generated_source_row(
            bank_code=bank_code,
            country_code=country_code,
            product_type=product_type,
            source_language=source_language,
            normalized_url=candidate.normalized_url,
            raw_url=candidate.raw_url,
            source_name=candidate.source_name_hint or _generated_link_name(bank_name, product_type_label, candidate.anchor_text, fallback="detail"),
            discovery_role="detail",
            priority=candidate.priority_hint or "P1",
            purpose=(
                ai_score.short_rationale
                if ai_score and ai_score.short_rationale
                else f"Auto-generated {product_type_label} detail source from bank homepage"
            ),
            expected_fields=candidate.expected_fields_hint or expected_fields,
            discovery_metadata=metadata,
        )
        if candidate.seed_source_id:
            row["source_id"] = candidate.seed_source_id
        detail_rows.append(row)
        promoted_count += 1
    if promoted_count:
        fallback_parts = []
        if seed_fetch_fallback_count:
            fallback_parts.append(f"{seed_fetch_fallback_count} seed-backed source(s) whose page evidence fetch was unavailable")
        if seed_low_evidence_fallback_count:
            fallback_parts.append(f"{seed_low_evidence_fallback_count} seed-backed source(s) with low page evidence")
        if fallback_parts:
            notes.append(f"Homepage discovery promoted {promoted_count} detail source(s), including {', and '.join(fallback_parts)}.")
        else:
            notes.append(f"Homepage discovery promoted {promoted_count} detail source(s) after candidate scoring and page evidence validation.")
    elif evaluated:
        notes.append("Homepage discovery candidate validation rejected all tentative detail pages.")
    return detail_rows, _dedupe_preserve_order([note for note in notes if note])


def _ordered_detail_candidates(*, candidates: list[HomepageCandidate], ai_scores: dict[str, AiParallelCandidateScore]) -> list[HomepageCandidate]:
    ranked = sorted(candidates, key=lambda item: (-_candidate_combined_score(item, ai_scores), item.normalized_url))
    seed_candidates = [item for item in ranked if item.seed_source_id]
    if seed_candidates:
        return seed_candidates
    non_seed_candidates = [item for item in ranked if not item.seed_source_id]
    return non_seed_candidates[:_PAGE_EVIDENCE_MAX_CANDIDATES]


def _candidate_combined_score(candidate: HomepageCandidate, ai_scores: dict[str, AiParallelCandidateScore]) -> float:
    ai_score = ai_scores.get(candidate.normalized_url)
    total = float(candidate.heuristic_score * 2)
    if ai_score is None:
        return total
    role_bonus = {"detail": 2.0, "supporting_html": -1.0, "irrelevant": -3.0}.get(ai_score.predicted_role, 0.0)
    return total + ai_score.relevance_score + role_bonus


def _candidate_promotes_to_detail(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    if page_evidence.page_evidence_score < _PAGE_EVIDENCE_MINIMUM_SCORE:
        return False
    if candidate.seed_source_id:
        return True
    if page_evidence.negative_signal_count >= 2:
        return False
    if candidate.supporting_signal and (ai_score is None or ai_score.predicted_role != "detail"):
        return False
    if ai_score is not None:
        if ai_score.predicted_role != "detail":
            return False
        return ai_score.relevance_score >= 4.0
    return candidate.heuristic_score > 0


def _build_detail_discovery_metadata(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> dict[str, Any]:
    combined = _candidate_combined_score(candidate, {candidate.normalized_url: ai_score} if ai_score is not None else {})
    if page_evidence.page_evidence_score >= 7 and combined >= 8:
        confidence = "high"
    elif page_evidence.page_evidence_score >= _PAGE_EVIDENCE_MINIMUM_SCORE and combined >= 4:
        confidence = "medium"
    else:
        confidence = "low"
    selection_reason_codes = list(
        dict.fromkeys(
            [
                *(_coerce_reason_codes(ai_score.reason_codes) if ai_score is not None else []),
                *page_evidence.page_evidence_reason_codes,
                "seed_hint_alignment" if candidate.seed_source_id else "",
            ]
        )
    )
    return {
        "selection_path": _selection_path(candidate=candidate, ai_score=ai_score),
        "selection_confidence": confidence,
        "selection_reason_codes": [code for code in selection_reason_codes if code],
        "candidate_origin": candidate.origin,
        "heuristic_score": candidate.heuristic_score,
        "ai_parallel_score": ai_score.relevance_score if ai_score is not None else None,
        "ai_predicted_role": ai_score.predicted_role if ai_score is not None else None,
        "ai_confidence_band": ai_score.confidence_band if ai_score is not None else None,
        "ai_reason_codes": _coerce_reason_codes(ai_score.reason_codes) if ai_score is not None else [],
        "ai_short_rationale": ai_score.short_rationale if ai_score is not None else None,
        "page_evidence_score": page_evidence.page_evidence_score,
        "page_evidence_reason_codes": page_evidence.page_evidence_reason_codes,
        "page_title": page_evidence.page_title,
        "primary_heading": page_evidence.primary_heading,
        "heading_match": page_evidence.heading_match,
        "attribute_signal_count": page_evidence.attribute_signal_count,
        "negative_signal_count": page_evidence.negative_signal_count,
    }


def _selection_path(*, candidate: HomepageCandidate, ai_score: AiParallelCandidateScore | None) -> str:
    if ai_score is not None and candidate.seed_source_id:
        return "seed_hint_plus_ai_plus_page_evidence"
    if ai_score is not None:
        return "heuristic_plus_ai_plus_page_evidence"
    if candidate.seed_source_id:
        return "seed_hint_plus_page_evidence"
    return "heuristic_plus_page_evidence"


def _coerce_reason_codes(values: list[str]) -> list[str]:
    return [str(item) for item in values if str(item).strip()]


def _score_page_evidence(
    *,
    raw_url: str,
    fetch_policy: DiscoveryFetchPolicy,
    product_type: str,
    product_type_definition: dict[str, Any],
) -> PageEvidenceAssessment:
    try:
        html_text = fetch_text(raw_url, fetch_policy)
    except Exception as exc:
        return PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["page_fetch_unavailable"],
            page_title=None,
            primary_heading=None,
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=0,
            fetch_error=str(exc),
        )

    parser = _PageSignalParser()
    parser.feed(html_text)
    title_text = parser.title_text
    primary_heading = parser.primary_heading
    heading_text = " ".join([primary_heading, *parser.secondary_headings]).strip()
    body_text = " ".join(parser.body_chunks[:40]).strip()
    semantic_terms = _product_type_semantic_terms(product_type_definition)
    attribute_terms = _product_type_attribute_keywords(product_type, product_type_definition)
    title_match = _term_hits(title_text, semantic_terms)
    primary_heading_match = _term_hits(primary_heading, semantic_terms)
    body_match = _term_hits(body_text, semantic_terms)
    attribute_hits = _term_hits(body_text, attribute_terms) + _term_hits(heading_text, attribute_terms)
    negative_hits = _negative_term_hits(" ".join([title_text, heading_text, body_text]))

    score = 0
    reason_codes: list[str] = []
    if title_match:
        score += 3
        reason_codes.append("title_semantic_match")
    if primary_heading_match:
        score += 3
        reason_codes.append("detail_page_layout_signal")
    if body_match:
        score += 1
        reason_codes.append("product_type_semantic_match")
    if attribute_hits >= 2:
        score += 2
        reason_codes.append("pricing_or_feature_signal")
    elif attribute_hits == 1:
        score += 1
        reason_codes.append("pricing_or_feature_signal")
    if negative_hits:
        score -= min(4, negative_hits * 2)
        reason_codes.append("insufficient_evidence")
    if not title_match and not primary_heading_match and not body_match and attribute_hits == 0:
        reason_codes.append("insufficient_evidence")

    return PageEvidenceAssessment(
        page_evidence_score=max(score, 0),
        page_evidence_reason_codes=_dedupe_preserve_order([code for code in reason_codes if code]),
        page_title=title_text or None,
        primary_heading=primary_heading or None,
        heading_match=bool(primary_heading_match),
        attribute_signal_count=attribute_hits,
        negative_signal_count=negative_hits,
    )


class _PageSignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._tag_stack: list[str] = []
        self._ignore_depth = 0
        self._title_parts: list[str] = []
        self._h1_parts: list[str] = []
        self._h2_parts: list[str] = []
        self.body_chunks: list[str] = []

    @property
    def title_text(self) -> str:
        return _collapse_whitespace(" ".join(self._title_parts))

    @property
    def primary_heading(self) -> str:
        return _collapse_whitespace(" ".join(self._h1_parts))

    @property
    def secondary_headings(self) -> list[str]:
        return [_collapse_whitespace(" ".join(self._h2_parts))] if self._h2_parts else []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"}:
            self._ignore_depth += 1
            return
        self._tag_stack.append(normalized)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"} and self._ignore_depth > 0:
            self._ignore_depth -= 1
            return
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index] == normalized:
                del self._tag_stack[index]
                break

    def handle_data(self, data: str) -> None:
        if self._ignore_depth > 0:
            return
        text = _collapse_whitespace(data)
        if not text:
            return
        if "title" in self._tag_stack:
            self._title_parts.append(text)
        elif "h1" in self._tag_stack:
            self._h1_parts.append(text)
        elif "h2" in self._tag_stack or "h3" in self._tag_stack:
            self._h2_parts.append(text)
        else:
            self.body_chunks.append(text)


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _term_hits(text: str, terms: list[str]) -> int:
    fingerprint = text.lower()
    return sum(1 for term in terms if term and term in fingerprint)


def _negative_term_hits(text: str) -> int:
    fingerprint = text.lower()
    return sum(1 for term in _PAGE_NEGATIVE_KEYWORDS if term in fingerprint)


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


def _score_catalog_hub_link(
    *,
    product_type: str,
    product_type_definition: dict[str, Any],
    normalized_url: str,
    anchor_text: str,
) -> int:
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    score = _score_product_link(
        product_type=product_type,
        product_type_definition=product_type_definition,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    )
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
    discovery_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_type = infer_source_type(normalized_url)
    digest = hashlib.sha1(f"{bank_code}|{product_type}|{normalized_url}|{discovery_role}".encode("utf-8")).hexdigest()[:10]
    type_code = _product_type_short_code(product_type)
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
        "discovery_metadata": discovery_metadata or {},
        "change_reason": "generated_from_bank_homepage",
    }


def _dedupe_generated_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in rows:
        scope = (
            str(item["bank_code"]),
            str(item["product_type"]),
            str(item["normalized_url"]),
            str(item["source_type"]),
        )
        current = by_scope.get(scope)
        if current is None or _generated_source_row_sort_key(item) < _generated_source_row_sort_key(current):
            by_scope[scope] = item
    return list(by_scope.values())


def _generated_source_row_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    role_rank = {
        "detail": 0,
        "entry": 1,
        "linked_pdf": 2,
        "supporting_pdf": 3,
        "supporting_html": 4,
    }.get(str(item.get("discovery_role")), 9)
    priority_rank = {
        "P0": 0,
        "P1": 1,
        "P2": 2,
        "P3": 3,
    }.get(str(item.get("priority") or "P9").upper(), 9)
    return (role_rank, priority_rank, str(item.get("source_id", "")))


def _dedupe_scored_links(items: list[tuple[int, Any]]) -> list[tuple[int, Any]]:
    by_url: dict[str, tuple[int, Any]] = {}
    for score, link in sorted(items, key=lambda item: (-item[0], item[1].normalized_url)):
        if link.normalized_url not in by_url:
            by_url[link.normalized_url] = (score, link)
    return list(by_url.values())


def _score_product_link(
    *,
    product_type: str,
    product_type_definition: dict[str, Any],
    normalized_url: str,
    anchor_text: str,
) -> int:
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    score = 0
    for keyword in _product_type_keywords(product_type_definition):
        if keyword in fingerprint:
            score += 2
    for keyword in _product_type_description_terms(product_type_definition):
        if keyword in fingerprint:
            score += 1
    normalized_product_type = _canonical_product_type_code(product_type).replace("-", " ")
    if normalized_product_type and normalized_product_type in fingerprint:
        score += 1
    for keyword in _SUPPORTING_KEYWORDS:
        if keyword in fingerprint:
            score -= 1
    return score


def _generated_link_name(
    bank_name: str,
    product_type_label: str,
    anchor_text: str,
    *,
    fallback: str,
    normalized_url: str | None = None,
) -> str:
    cleaned = re.sub(r"\s+", " ", anchor_text.strip())
    if cleaned and not _looks_like_non_descriptive_anchor(cleaned):
        return cleaned[:280]
    if normalized_url:
        fingerprint = normalized_url.lower()
        if "terms" in fingerprint or "conditions" in fingerprint:
            return f"{bank_name} {product_type_label} terms and conditions"
        if "fee" in fingerprint or "fees" in fingerprint:
            return f"{bank_name} {product_type_label} fees"
        if "rate" in fingerprint or "rates" in fingerprint:
            return f"{bank_name} {product_type_label} rates"
        if "blue" in fingerprint or "air-miles" in fingerprint:
            return f"{bank_name} {product_type_label} rewards support"
    return f"{bank_name} {product_type_label} {fallback}"


def _looks_like_non_descriptive_anchor(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    if normalized.isdigit():
        return True
    if normalized in {"learn more", "more details", "details", "*"}:
        return True
    if normalized.startswith(".css-"):
        return True
    return False


def _link_is_relevant_supporting_source(
    *,
    product_type: str,
    discovery_product_type: str | None = None,
    product_type_definition: dict[str, Any],
    normalized_url: str,
    anchor_text: str,
) -> bool:
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    signal_product_type = discovery_product_type or product_type
    if any(keyword in fingerprint for keyword in _EXCLUDED_LINK_KEYWORDS):
        return False
    if _has_unrelated_product_type_signal(product_type=signal_product_type, fingerprint=fingerprint):
        return False
    has_supporting_signal = any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS)
    has_product_signal = _score_product_link(
        product_type=signal_product_type,
        product_type_definition=product_type_definition,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    ) > 0
    has_bank_account_terms_signal = "bank-account" in fingerprint or "bank accounts" in fingerprint
    return has_product_signal or (has_supporting_signal and has_bank_account_terms_signal)


def _has_unrelated_product_type_signal(*, product_type: str, fingerprint: str) -> bool:
    exclusions = _PRODUCT_TYPE_EXCLUSION_KEYWORDS.get(product_type, ())
    if not any(keyword in fingerprint for keyword in exclusions):
        return False
    product_terms = _product_type_keywords({"product_type_code": product_type, "display_name": product_type, "discovery_keywords": [product_type]})
    return not any(term and term in fingerprint for term in product_terms)


def _build_source_catalog_collection_run_id(*, bank_code: str, product_type: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    suffix = new_id("src").split("_", 1)[1][:8]
    return f"run_{timestamp}_{bank_code.lower()}_{product_type}_collect_{suffix}"


def _build_source_catalog_ai_model_execution_id(
    *,
    run_id: str,
    bank_code: str,
    product_type: str,
    normalized_homepage_url: str,
) -> str:
    digest = hashlib.sha256(
        f"{run_id}|{bank_code}|{product_type}|{normalized_homepage_url}|source_catalog_ai_parallel".encode("utf-8")
    ).hexdigest()[:16]
    return f"modelexec-{digest}"


def _build_source_catalog_ai_usage_id(model_execution_id: str) -> str:
    digest = hashlib.sha256(f"{model_execution_id}|llm_usage".encode("utf-8")).hexdigest()[:16]
    return f"usage-{digest}"


def _product_type_keywords(product_type_definition: dict[str, Any]) -> list[str]:
    keywords = []
    for item in product_type_definition.get("discovery_keywords", []):
        normalized = str(item).strip().lower()
        if normalized and normalized not in keywords:
            keywords.append(normalized)
    display_name = str(product_type_definition.get("display_name") or "").strip().lower()
    if display_name and display_name not in keywords:
        keywords.append(display_name)
    return keywords


def _product_type_description_terms(product_type_definition: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", str(product_type_definition.get("description") or "").lower()):
        if token in _DISCOVERY_STOPWORDS or token in tokens:
            continue
        tokens.append(token)
        if len(tokens) >= 16:
            break
    return tokens


def _product_type_semantic_terms(product_type_definition: dict[str, Any]) -> list[str]:
    return _dedupe_preserve_order([*_product_type_keywords(product_type_definition), *_product_type_description_terms(product_type_definition)])


def _product_type_attribute_keywords(product_type: str, product_type_definition: dict[str, Any]) -> list[str]:
    hints = list(_PRODUCT_TYPE_ATTRIBUTE_HINTS.get(product_type, ()))
    for token in _product_type_description_terms(product_type_definition):
        if token not in hints:
            hints.append(token)
    return hints[:16]


def _product_type_discovery_profile(product_type: str, product_type_definition: dict[str, Any]) -> str:
    product_type = _canonical_product_type_code(product_type)
    if product_type in _DISCOVERY_PROFILE_TERMS:
        return product_type
    code_tokens = set(filter(None, product_type.replace("-", " ").split()))
    if "gic" in code_tokens or {"term", "deposit"}.issubset(code_tokens):
        return "gic"
    if "savings" in code_tokens or "saving" in code_tokens:
        return "savings"
    if "chequing" in code_tokens or "checking" in code_tokens:
        return "chequing"
    fingerprint = " ".join(
        [
            product_type.replace("-", " "),
            str(product_type_definition.get("display_name") or ""),
            str(product_type_definition.get("description") or ""),
            " ".join(str(item) for item in product_type_definition.get("discovery_keywords", []) if str(item).strip()),
        ]
    ).lower()
    scored_profiles: list[tuple[int, str]] = []
    for profile, terms in _DISCOVERY_PROFILE_TERMS.items():
        score = sum(1 for term in terms if term in fingerprint)
        if score:
            scored_profiles.append((score, profile))
    if not scored_profiles:
        return product_type
    scored_profiles.sort(key=lambda item: (-item[0], item[1]))
    best_score, best_profile = scored_profiles[0]
    if best_score < 2:
        return product_type
    if len(scored_profiles) > 1 and scored_profiles[1][0] == best_score:
        return product_type
    return best_profile


def _product_type_expected_fields(product_type_definition: dict[str, Any]) -> list[str]:
    fields = [str(item).strip() for item in product_type_definition.get("expected_fields", []) if str(item).strip()]
    return fields or ["product_name", "description_short", "standard_rate", "monthly_fee", "notes"]


def _product_type_label(product_type_definition: dict[str, Any]) -> str:
    return str(product_type_definition.get("display_name") or product_type_definition.get("product_type_code") or "Product").strip()


def _product_type_short_code(product_type: str) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", product_type.upper())
    if not compact:
        return "SRC"
    return compact[:3].ljust(3, "X")


def _serialize_bank_row(row: dict[str, Any]) -> dict[str, Any]:
    catalog_product_types = sorted(str(value) for value in (row.get("catalog_product_types") or []) if value)
    catalog_items = [
        {
            "catalog_item_id": str(item["catalog_item_id"]),
            "product_type": str(item["product_type"]),
            "status": str(item["status"]),
            "generated_source_count": int(item.get("generated_source_count") or 0),
        }
        for item in (row.get("catalog_items") or [])
    ]
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
        "catalog_items": catalog_items,
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


def _canonical_product_type_code(value: Any) -> str:
    return canonicalize_product_type_code(value)


def _product_type_scope_codes(product_type: str) -> list[str]:
    return [_canonical_product_type_code(product_type)]


def _required_text(value: Any, field_name: str) -> str:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise SourceRegistryError(status_code=422, code="required_field_missing", message=f"{field_name} is required.")
    return cleaned


def _normalize_bank_homepage_url(homepage_url: str) -> tuple[str, str]:
    candidate = homepage_url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate.lstrip('/')}"
    try:
        normalized = normalize_source_url(candidate)
    except ValueError as exc:
        raise SourceRegistryError(
            status_code=422,
            code="homepage_url_invalid",
            message="homepage_url must be a valid public http or https URL.",
        ) from exc
    return normalized, normalized


def _normalize_search(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    return re.sub(r"\s+", " ", cleaned).lower()
