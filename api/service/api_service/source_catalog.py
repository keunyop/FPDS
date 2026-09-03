from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
import html as html_lib
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
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import path guard for `uv run --directory api/service`
    sys.path.insert(0, str(REPO_ROOT))

from api_service.errors import SourceRegistryError
from api_service.product_types import (
    canonicalize_product_type_code,
    expected_fields_for_product_type,
    load_product_type_definitions_map,
    require_product_type_definition,
)
from api_service.product_type_localization import localize_product_type_definition
from api_service.security import new_id, utc_now
from api_service.source_registry import _insert_collection_run_row
from api_service.source_registry_utils import (
    infer_source_type,
    load_seed_bank_profiles,
    load_seed_source_registry_rows,
    normalize_source_url,
)
from worker.discovery.fpds_discovery.discovery import (
    ExtractedLink,
    extract_links,
    extract_structured_text_sections,
)
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, fetch_text
from worker.pipeline.fpds_approval_policy import collection_fields_for_product_type
from worker.pipeline.fpds_market_profile import market_profile_metadata
from worker.discovery.fpds_discovery.url_utils import host_matches_allowed_domains
from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)

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
    "application",
    "prequalification",
    "open-account",
    "open-an-account",
    "openaccount",
    "open-an-investment",
    "open-investment",
    "investment-application",
    "promo",
    "offer",
    "compare",
    "calculator",
    "selector",
    "activate-your",
    "manage-your",
    "welcome-kit",
    "order-supplementary",
    "acknowledge",
    "digital-banking-guide",
    "advice-plus",
    "award-winning",
    "forms-downloads",
    "forms-and-downloads",
    "tips",
    "modern-slavery",
    "human-trafficking",
    "privacy",
    "accessibility",
    "annual-report",
    "climate-report",
    "climate-disclosure",
    "investor-relations",
    "modern slavery",
    "modern_slavery",
    "human_trafficking",
    "slavery",
    "investor",
    "investors",
    "investors-shareholders",
    "shareholder",
    "shareholders",
)
_SUPPORTING_KEYWORDS = ("rate", "rates", "fee", "fees", "legal", "terms", "conditions", "service", "agreement", "disclosure")
_DETAIL_COMPANION_ANCHOR_MARKERS = (
    "account guide",
    "cardmember agreement",
    "clarity statement",
    "consumer account addend",
    "credit card agreement",
    "current agreement",
    "deposit account agreement",
    "details of rate",
    "fee schedule",
    "important rates",
    "interest rates and interest charges",
    "pricing & terms",
    "pricing and terms",
    "rate and fee",
    "rate, fee",
    "rates and fees",
    "schedule of fees",
    "schumer",
    "view disclosure",
)
_DETAIL_COMPANION_URL_MARKERS = (
    "account-guide",
    "account_guide",
    "agreement",
    "cardmember-agreement",
    "disclosure",
    "fee-schedule",
    "get-disclosures",
    "getdisclosure",
    "pricing",
    "rate-and-fee",
    "rates-and-fees",
    "schedule-of-fees",
)
_DETAIL_COMPANION_EXCLUDED_MARKERS = (
    "accessibility",
    "cookie-policy",
    "legal-notice",
    "online-banking/service-agreement",
    "privacy",
    "security-center",
    "service-agreement.go",
    "site-terms",
    "terms-of-use",
    "user-agreement",
    "user_agreement",
)
_HUB_KEYWORDS = (
    "account",
    "accounts",
    "bank-account",
    "bank-accounts",
    "invest",
    "investments",
    "personal",
    "borrow",
    "borrowing",
    "lend",
    "lending",
    "loan",
    "loans",
    "mortgage",
    "mortgages",
    "credit-card",
    "credit-cards",
    "line-of-credit",
)
_PAGE_NEGATIVE_KEYWORDS = ("compare", "sign in", "login", "legal", "terms and conditions")
_AI_DETAIL_OVERRIDE_VETO_REASON_CODES = {
    "hub_page_not_detail",
    "insufficient_evidence",
    "not_product_detail",
    "promo_or_apply_flow",
    "supporting_terms_or_rates_page",
    "non_product_editorial_page",
    "non_product_service_flow",
}
_TERMINAL_SUPPORTING_ROLES = {"supporting_html", "supporting_pdf", "linked_pdf"}
_VERIFIED_COVERAGE_REVIEW_REASON = "verified_coverage_review_source"
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
    "credit-card": (
        "chequing-account",
        "chequing account",
        "savings-account",
        "savings account",
        "gic",
        "guaranteed-investment",
        "mortgage",
        "mortgages",
        "personal-loan",
        "personal loan",
        "line-of-credit",
        "line of credit",
        "home-equity-line",
        "home equity line",
        "auto-loan",
        "auto loan",
        "vehicle-loan",
        "vehicle loan",
    ),
    "mortgage": (
        "chequing-account",
        "chequing account",
        "savings-account",
        "savings account",
        "gic",
        "guaranteed-investment",
        "credit-card",
        "credit cards",
        "personal-loan",
        "personal loan",
        "line-of-credit",
        "line of credit",
        "student-line",
        "student line",
    ),
    "personal-loan": (
        "chequing-account",
        "chequing account",
        "savings-account",
        "savings account",
        "gic",
        "guaranteed-investment",
        "credit-card",
        "credit cards",
        "mortgage",
        "mortgages",
        "line-of-credit",
        "line of credit",
        "home-equity-line",
        "home equity line",
    ),
    "line-of-credit": (
        "chequing-account",
        "chequing account",
        "savings-account",
        "savings account",
        "gic",
        "guaranteed-investment",
        "credit-card",
        "credit cards",
        "mortgage",
        "mortgages",
        "personal-loan",
        "personal loan",
        "car-loan",
        "car loan",
        "vehicle-loan",
        "vehicle loan",
        "rrsp-loan",
        "rrsp loan",
    ),
}
_REGISTERED_PLAN_WRAPPER_KEYWORDS = (
    "tax-free-savings",
    "tax free savings",
    "tfsa",
    "rrsp",
    "resp",
    "fhsa",
    "first-home-savings",
    "first home savings",
    "registered-retirement",
    "registered retirement",
    "registered education",
)
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
    "credit-card": (
        "annual fee",
        "purchase interest",
        "cash advance",
        "balance transfer",
        "cash back",
        "rewards",
        "points",
        "credit limit",
    ),
    "mortgage": (
        "mortgage rate",
        "fixed rate",
        "variable rate",
        "term",
        "amortization",
        "prepayment",
        "payment frequency",
        "renewal",
    ),
    "personal-loan": (
        "interest rate",
        "loan amount",
        "monthly payment",
        "fixed rate",
        "term",
        "vehicle loan",
        "rrsp loan",
        "repayment",
    ),
    "line-of-credit": (
        "interest rate",
        "credit limit",
        "variable rate",
        "minimum payment",
        "secured",
        "unsecured",
        "home equity",
        "student line",
    ),
}
_PRODUCT_TYPE_IDENTITY_HINTS = {
    "chequing": ("chequing account", "checking account", "echequing", "e-chequing"),
    "savings": ("savings account", "saving account", "esavings", "e-savings"),
    "gic": (
        "gic",
        "term deposit",
        "guaranteed investment certificate",
        "certificate of deposit",
        "cd account",
        "bank cd",
    ),
    "credit-card": ("credit card", "visa card", "mastercard", "american express card"),
    "mortgage": ("mortgage",),
    "personal-loan": ("personal loan", "car loan", "vehicle loan", "rrsp loan"),
    "line-of-credit": ("line of credit", "home equity line", "student line", "professional line"),
}
_BANK_PRODUCT_TYPE_DISCOVERY_ALIASES = {
    ("EQBANK", "chequing"): ("personal account",),
}
_DISCOVERY_PROFILE_TERMS = {
    "chequing": ("chequing", "checking", "everyday banking", "transactions", "debit card", "monthly fee"),
    "savings": ("savings", "saving", "savings account", "high interest", "interest rate", "tiered interest", "withdrawal", "balance"),
    "gic": ("gic", "gics", "term deposit", "guaranteed investment", "maturity", "redeemable", "minimum deposit"),
    "credit-card": ("credit card", "credit cards", "cash back", "rewards", "annual fee", "purchase interest", "visa", "mastercard"),
    "mortgage": ("mortgage", "mortgages", "mortgage rates", "fixed rate", "variable rate", "amortization", "prepayment"),
    "personal-loan": ("personal loan", "personal loans", "loan rates", "vehicle loan", "car loan", "rrsp loan", "monthly payments"),
    "line-of-credit": (
        "line of credit",
        "lines of credit",
        "home equity line of credit",
        "student line of credit",
        "credit limit",
        "minimum payment",
    ),
}
_PAGE_EVIDENCE_MINIMUM_SCORE = 4
_DISCOVERY_DETAIL_LINK_MAX = 36
_DISCOVERY_SUPPORTING_LINK_MAX = 12
_DISCOVERY_PDF_LINK_MAX = 8
_DISCOVERY_DETAIL_COMPANION_MAX = 48
_DISCOVERY_DETAIL_COMPANION_PER_DETAIL_MAX = 2
_DISCOVERY_HUB_PAGE_MAX = 5
_DISCOVERY_SECONDARY_HUB_PAGE_MAX = 8
_DISCOVERY_REGISTRY_SEED_MAX = 48
_DISCOVERY_REGISTRY_DETAIL_PAGE_MAX = 12
_AI_DISCOVERY_MAX_CANDIDATES = 48
_PAGE_EVIDENCE_MAX_CANDIDATES = 32
_AUTHORITATIVE_CATALOG_DETAIL_BONUS = 6
_COVERAGE_ROUTE_RESOLUTION_SCHEMA_NAME = "source_catalog_coverage_route_resolution_v1"
_COVERAGE_ROUTE_RESOLUTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "status",
        "summary",
        "coverage_source_url",
        "current_offering_quote",
        "relationship_source_url",
        "relationship_quote",
        "not_offered_source_url",
        "not_offered_quote",
    ],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["current_offering", "not_currently_offered", "uncertain"],
        },
        "summary": {"type": "string"},
        "coverage_source_url": {"type": ["string", "null"]},
        "current_offering_quote": {"type": ["string", "null"]},
        "relationship_source_url": {"type": ["string", "null"]},
        "relationship_quote": {"type": ["string", "null"]},
        "not_offered_source_url": {"type": ["string", "null"]},
        "not_offered_quote": {"type": ["string", "null"]},
    },
}


@dataclass(frozen=True)
class BankFilters:
    country_code: str
    search: str | None
    status: str | None


@dataclass(frozen=True)
class SourceCatalogFilters:
    country_code: str
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
    rejected_detail_urls: tuple[str, ...] = ()
    discovery_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CatalogItemMaterializationResult:
    generated_rows: list[dict[str, Any]]
    discovery_notes: list[str]
    detail_source_ids: list[str]
    model_execution_records: tuple[dict[str, Any], ...] = ()
    usage_records: tuple[dict[str, Any], ...] = ()
    discovery_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CoverageRouteRepairResult:
    status: str
    coverage_source_url: str | None
    coverage_source_metadata: dict[str, Any]
    notes: list[str]


@dataclass(frozen=True)
class AiParallelScoringResult:
    scores: dict[str, "AiParallelCandidateScore"]
    notes: list[str]
    model_execution_record: dict[str, Any] | None = None
    usage_record: dict[str, Any] | None = None
    ai_unavailable: bool = False


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
class DetailCompanionLink:
    link: ExtractedLink
    parent_detail_url: str
    score: int


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
    product_identity_match: bool = False


def normalize_bank_filters(*, country_code: str, search: str | None, status: str | None) -> BankFilters:
    normalized_search = _normalize_search(search)
    normalized_status = _clean_text(status)
    return BankFilters(
        country_code=_normalize_country_code(country_code),
        search=normalized_search,
        status=normalized_status.lower() if normalized_status else None,
    )


def normalize_source_catalog_filters(
    *,
    country_code: str,
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
        country_code=_normalize_country_code(country_code),
        search=normalized_search,
        bank_code=normalized_bank_code.upper() if normalized_bank_code else None,
        product_type=normalized_product_type.lower() if normalized_product_type else None,
        status=normalized_status.lower() if normalized_status else None,
    )


def load_bank_list(connection: Connection, *, filters: BankFilters) -> dict[str, Any]:
    where_clauses = ["b.country_code = %(country_code)s"]
    params: dict[str, Any] = {"country_code": filters.country_code}
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
                OR lower(COALESCE(b.logo_url, '')) LIKE %(search_pattern)s
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
            b.logo_url,
            b.logo_alt_text,
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
           AND sci.country_code = b.country_code
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = b.bank_code
           AND sri.country_code = b.country_code
        WHERE {" AND ".join(where_clauses)}
        GROUP BY
            b.bank_code,
            b.country_code,
            b.bank_name,
            b.status,
            b.homepage_url,
            b.normalized_homepage_url,
            b.logo_url,
            b.logo_alt_text,
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
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            COUNT(DISTINCT sri.source_id) AS generated_source_count,
            EXISTS (
                SELECT 1
                FROM ingestion_run AS completed_run
                WHERE completed_run.run_state = 'completed'
                  AND completed_run.source_scope_count > 0
                  AND completed_run.country_code = sci.country_code
                  AND COALESCE(completed_run.run_metadata ->> 'bank_code', '') = sci.bank_code
                  AND COALESCE(completed_run.run_metadata ->> 'product_type', '') = sci.product_type
            ) AS has_completed_collection
        FROM source_registry_catalog_item AS sci
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.country_code = sci.country_code
           AND sri.product_type = sci.product_type
        WHERE sci.bank_code = ANY(%(bank_codes)s)
          AND sci.country_code = %(country_code)s
        GROUP BY
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata
        ORDER BY sci.bank_code, sci.product_type
        """,
        {"bank_codes": bank_codes or [""], "country_code": filters.country_code},
    ).fetchall() if bank_codes else []
    catalog_items_by_bank: dict[str, list[dict[str, Any]]] = {}
    for item in catalog_item_rows:
        catalog_items_by_bank.setdefault(str(item["bank_code"]), []).append(
            {
                "catalog_item_id": str(item["catalog_item_id"]),
                "product_type": str(item["product_type"]),
                "status": str(item["status"]),
                "coverage_source_url": item.get("coverage_source_url"),
                "coverage_source_metadata": _mapping(item.get("coverage_source_metadata")),
                "generated_source_count": int(item["generated_source_count"] or 0),
                "has_completed_collection": bool(item.get("has_completed_collection", False)),
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
            "country_code": filters.country_code,
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
            logo_url,
            logo_alt_text,
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
            coverage_source_url,
            normalized_coverage_source_url,
            coverage_source_metadata,
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
    logo_url = _normalize_optional_public_url(payload.get("logo_url"), "logo_url")
    logo_alt_text = _normalize_logo_alt_text(payload.get("logo_alt_text"), bank_name=bank_name, logo_url=logo_url)
    initial_coverage_product_types = list(payload.get("initial_coverage_product_types") or [])
    initial_coverage_source_urls = dict(payload.get("initial_coverage_source_urls") or {})
    initial_coverage_source_metadata = dict(payload.get("initial_coverage_source_metadata") or {})
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

    bank_code = _generate_bank_code(connection, bank_name=bank_name, normalized_homepage_url=normalized_homepage_url)
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
            logo_url,
            logo_alt_text,
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
            %(logo_url)s,
            %(logo_alt_text)s,
            %(source_language)s,
            %(managed_flag)s,
            %(change_reason)s,
            %(created_at)s,
            %(updated_at)s
        )
        """,
        {
            "bank_code": bank_code,
            "country_code": _normalize_country_code(payload.get("country_code")),
            "bank_name": bank_name,
            "status": (_clean_text(payload.get("status")) or "active").lower(),
            "homepage_url": homepage_url,
            "normalized_homepage_url": normalized_homepage_url,
            "logo_url": logo_url,
            "logo_alt_text": logo_alt_text,
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
                "coverage_source_url": initial_coverage_source_urls.get(str(product_type)),
                "coverage_source_metadata": initial_coverage_source_metadata.get(str(product_type)) or {},
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
            logo_url,
            logo_alt_text,
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
    logo_url = _normalize_optional_public_url(payload.get("logo_url", existing_row.get("logo_url")), "logo_url")
    logo_alt_text = _normalize_logo_alt_text(
        payload.get("logo_alt_text", existing_row.get("logo_alt_text")),
        bank_name=bank_name,
        logo_url=logo_url,
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
    updated_country_code = _normalize_country_code(payload.get("country_code", existing_row["country_code"]))
    updated_source_language = (_clean_text(payload.get("source_language", existing_row["source_language"])) or "en").lower()
    updated_change_reason = _clean_text(payload.get("change_reason", existing_row["change_reason"]))
    diff_summary = _build_bank_diff_summary(existing_row, {
        "bank_name": bank_name,
        "homepage_url": homepage_url,
        "logo_url": logo_url,
        "logo_alt_text": logo_alt_text,
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
            logo_url = %(logo_url)s,
            logo_alt_text = %(logo_alt_text)s,
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
            "logo_url": logo_url,
            "logo_alt_text": logo_alt_text,
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
            ) AS public_projection_count
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
    where_clauses = ["sci.country_code = %(country_code)s"]
    params: dict[str, Any] = {"country_code": filters.country_code}
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
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            ptr.product_family,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.logo_url,
            b.logo_alt_text,
            b.source_language,
            COUNT(DISTINCT sri.source_id) AS generated_source_count,
            EXISTS (
                SELECT 1
                FROM ingestion_run AS completed_run
                WHERE completed_run.run_state = 'completed'
                  AND completed_run.source_scope_count > 0
                  AND completed_run.country_code = sci.country_code
                  AND COALESCE(completed_run.run_metadata ->> 'bank_code', '') = sci.bank_code
                  AND COALESCE(completed_run.run_metadata ->> 'product_type', '') = sci.product_type
            ) AS has_completed_collection
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
           AND b.country_code = sci.country_code
           AND b.country_code = sci.country_code
        JOIN product_type_registry AS ptr
            ON ptr.product_type_code = sci.product_type
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.country_code = sci.country_code
           AND sri.product_type = sci.product_type
        WHERE {" AND ".join(where_clauses)}
        GROUP BY
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.logo_url,
            b.logo_alt_text,
            b.source_language
        ORDER BY b.bank_name, sci.product_type
        """,
        params,
    ).fetchall()

    bank_rows = connection.execute(
        """
        SELECT bank_code, bank_name
        FROM bank
        WHERE country_code = %(country_code)s
        ORDER BY bank_name, bank_code
        """,
        {"country_code": filters.country_code},
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
            "country_code": filters.country_code,
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
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.logo_url,
            b.logo_alt_text,
            b.source_language,
            COUNT(DISTINCT sri.source_id) AS generated_source_count,
            EXISTS (
                SELECT 1
                FROM ingestion_run AS completed_run
                WHERE completed_run.run_state = 'completed'
                  AND completed_run.source_scope_count > 0
                  AND completed_run.country_code = sci.country_code
                  AND COALESCE(completed_run.run_metadata ->> 'bank_code', '') = sci.bank_code
                  AND COALESCE(completed_run.run_metadata ->> 'product_type', '') = sci.product_type
            ) AS has_completed_collection
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
           AND b.country_code = sci.country_code
        LEFT JOIN source_registry_item AS sri
            ON sri.bank_code = sci.bank_code
           AND sri.country_code = sci.country_code
           AND sri.product_type = sci.product_type
        WHERE sci.catalog_item_id = %(catalog_item_id)s
        GROUP BY
            sci.catalog_item_id,
            sci.bank_code,
            sci.country_code,
            sci.product_type,
            sci.status,
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            sci.change_reason,
            sci.created_at,
            sci.updated_at,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.logo_url,
            b.logo_alt_text,
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
        SELECT bank_code, country_code, bank_name, homepage_url, normalized_homepage_url, logo_url, logo_alt_text, source_language
        FROM bank
        WHERE bank_code = %(bank_code)s
        """,
        {"bank_code": bank_code},
    ).fetchone()
    if not bank_row:
        raise SourceRegistryError(status_code=404, code="bank_profile_not_found", message="Select a valid bank before creating source catalog coverage.")
    coverage_source_metadata = _mapping(payload.get("coverage_source_metadata"))
    coverage_source_url, normalized_coverage_source_url = _normalize_coverage_source_url(
        payload.get("coverage_source_url"),
        normalized_homepage_url=str(bank_row["normalized_homepage_url"] or bank_row["homepage_url"]),
        coverage_source_metadata=coverage_source_metadata,
    )

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
            coverage_source_url,
            normalized_coverage_source_url,
            coverage_source_metadata,
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
            %(coverage_source_url)s,
            %(normalized_coverage_source_url)s,
            %(coverage_source_metadata)s::jsonb,
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
            "coverage_source_url": coverage_source_url,
            "normalized_coverage_source_url": normalized_coverage_source_url,
            "coverage_source_metadata": json.dumps(coverage_source_metadata, ensure_ascii=True),
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
        metadata={
            "bank_code": bank_code,
            "product_type": product_type,
            "coverage_source_url": coverage_source_url,
            "coverage_source_verification_status": coverage_source_metadata.get("verification_status"),
        },
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
        SELECT
            catalog_item_id,
            bank_code,
            country_code,
            product_type,
            status,
            coverage_source_url,
            normalized_coverage_source_url,
            coverage_source_metadata,
            change_reason
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
    coverage_source_metadata = _mapping(
        payload.get("coverage_source_metadata", existing.get("coverage_source_metadata"))
    )
    coverage_source_url, normalized_coverage_source_url = _normalize_coverage_source_url(
        payload.get("coverage_source_url", existing.get("coverage_source_url")),
        normalized_homepage_url=str(bank_row["normalized_homepage_url"] or bank_row["homepage_url"]),
        coverage_source_metadata=coverage_source_metadata,
    )
    diff_summary = _build_catalog_diff_summary(existing, {"bank_code": bank_code, "product_type": product_type, "status": updated_status})
    connection.execute(
        """
        UPDATE source_registry_catalog_item
        SET
            bank_code = %(bank_code)s,
            country_code = %(country_code)s,
            product_type = %(product_type)s,
            status = %(status)s,
            coverage_source_url = %(coverage_source_url)s,
            normalized_coverage_source_url = %(normalized_coverage_source_url)s,
            coverage_source_metadata = %(coverage_source_metadata)s::jsonb,
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
            "coverage_source_url": coverage_source_url,
            "normalized_coverage_source_url": normalized_coverage_source_url,
            "coverage_source_metadata": json.dumps(coverage_source_metadata, ensure_ascii=True),
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
        metadata={
            "bank_code": bank_code,
            "product_type": product_type,
            "coverage_source_url": coverage_source_url,
            "coverage_source_verification_status": coverage_source_metadata.get("verification_status"),
        },
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
    precision_rediscovery: bool = False,
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
            sci.coverage_source_url,
            sci.normalized_coverage_source_url,
            sci.coverage_source_metadata,
            ptr.product_family,
            b.bank_name,
            b.homepage_url,
            b.normalized_homepage_url,
            b.source_language,
            EXISTS (
                SELECT 1
                FROM ingestion_run AS completed_run
                WHERE completed_run.run_state = 'completed'
                  AND completed_run.source_scope_count > 0
                  AND completed_run.country_code = sci.country_code
                  AND COALESCE(completed_run.run_metadata ->> 'bank_code', '') = sci.bank_code
                  AND COALESCE(completed_run.run_metadata ->> 'product_type', '') = sci.product_type
            ) AS has_completed_collection
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
            ON b.bank_code = sci.bank_code
           AND b.country_code = sci.country_code
        JOIN product_type_registry AS ptr
            ON ptr.product_type_code = sci.product_type
           AND ptr.status = 'active'
        WHERE sci.catalog_item_id = ANY(%(catalog_item_ids)s)
          AND sci.status = 'active'
          AND (
              sci.coverage_source_url IS NOT NULL
              OR EXISTS (
                  SELECT 1
                  FROM source_registry_item AS active_detail
                  WHERE active_detail.bank_code = sci.bank_code
                    AND active_detail.country_code = sci.country_code
                    AND active_detail.product_type = sci.product_type
                    AND active_detail.status = 'active'
                    AND active_detail.discovery_role = 'detail'
              )
              OR NOT EXISTS (
                  SELECT 1
                  FROM ingestion_run AS quarantined_run
                  WHERE COALESCE(quarantined_run.run_metadata ->> 'country_code', quarantined_run.country_code) = sci.country_code
                    AND COALESCE(quarantined_run.run_metadata ->> 'bank_code', '') = sci.bank_code
                    AND COALESCE(quarantined_run.run_metadata ->> 'product_type', '') = sci.product_type
                    AND quarantined_run.run_metadata #>> '{catalog_scope_quarantine,status}' = 'quarantined'
              )
          )
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
        precision_rediscovery=precision_rediscovery,
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
            trigger_type="admin_source_collection",
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
            "precision_rediscovery_requested": precision_rediscovery,
            "source_coverage_modes": {
                str(group["catalog_item_id"]): str(group["source_coverage_mode"])
                for group in plan["groups"]
            },
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
    precision_rediscovery: bool = False,
) -> dict[str, Any]:
    triggered_by = str(actor.get("email") or actor.get("display_name") or actor.get("user_id") or "admin")
    actor_payload = {
        "actor_type": actor.get("actor_type"),
        "user_id": actor.get("user_id"),
        "email": actor.get("email"),
        "display_name": actor.get("display_name"),
        "role": actor.get("role"),
    }
    groups: list[dict[str, Any]] = []
    for row in rows:
        original_product_type = str(row["product_type"])
        product_type = _canonical_product_type_code(original_product_type)
        has_completed_collection = bool(row.get("has_completed_collection", False))
        source_coverage_mode = (
            "precision"
            if precision_rediscovery or not has_completed_collection
            else "standard"
        )
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
                "product_family": str(row.get("product_family") or "deposit"),
                "source_language": str(row.get("source_language") or "en"),
                "homepage_url": str(row["homepage_url"]),
                "normalized_homepage_url": str(row.get("normalized_homepage_url") or row["homepage_url"]),
                "coverage_source_url": row.get("coverage_source_url"),
                "coverage_source_metadata": _mapping(row.get("coverage_source_metadata")),
                "has_completed_collection": has_completed_collection,
                "source_coverage_mode": source_coverage_mode,
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
        "precision_rediscovery_requested": precision_rediscovery,
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

    collection_id = str(plan["collection_id"])
    plan_path = temp_dir / f"{collection_id}.json"
    log_path = temp_dir / f"{collection_id}.log"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

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
                "has_completed_collection": bool(group.get("has_completed_collection", False)),
                "source_coverage_mode": str(group.get("source_coverage_mode") or "precision"),
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
    registry_seed_rows = _load_existing_precision_discovery_seeds(
        connection,
        bank_code=bank_code,
        country_code=str(row["country_code"]),
        product_type=product_type,
        source_language=str(row.get("source_language") or "en"),
    )
    generation_result = _generate_sources_from_homepage(
        bank_code=bank_code,
        bank_name=str(row["bank_name"]),
        country_code=str(row["country_code"]),
        product_type=product_type,
        product_type_definition=product_type_definition,
        homepage_url=str(row["homepage_url"]),
        coverage_source_url=_clean_text(row.get("coverage_source_url")),
        coverage_source_metadata=_mapping(row.get("coverage_source_metadata")),
        source_language=str(row.get("source_language") or "en"),
        run_id=run_id,
        correlation_id=correlation_id,
        request_id=request_id,
        registry_seed_rows=registry_seed_rows,
    )
    if not generation_result.detail_source_ids:
        existing_detail_rows = _load_existing_detail_rows_for_companion_discovery(
            connection,
            bank_code=bank_code,
            country_code=str(row["country_code"]),
            product_type=product_type,
            source_language=str(row.get("source_language") or "en"),
        )
        companion_rows, companion_notes = _generate_existing_detail_companion_rows(
            bank_code=bank_code,
            bank_name=str(row["bank_name"]),
            country_code=str(row["country_code"]),
            product_type=product_type,
            product_type_definition=product_type_definition,
            homepage_url=str(row["homepage_url"]),
            coverage_source_url=_clean_text(row.get("coverage_source_url")),
            coverage_source_metadata=_mapping(row.get("coverage_source_metadata")),
            source_language=str(row.get("source_language") or "en"),
            existing_detail_rows=existing_detail_rows,
        )
        if companion_rows:
            generation_result = HomepageSourceGenerationResult(
                rows=[*generation_result.rows, *companion_rows],
                discovery_notes=_dedupe_preserve_order(
                    [*generation_result.discovery_notes, *companion_notes]
                ),
                detail_source_ids=generation_result.detail_source_ids,
                model_execution_records=generation_result.model_execution_records,
                usage_records=generation_result.usage_records,
                rejected_detail_urls=generation_result.rejected_detail_urls,
                discovery_metrics=generation_result.discovery_metrics,
            )
    generated_rows = _dedupe_generated_source_rows(generation_result.rows)
    discovery_notes = list(generation_result.discovery_notes)
    generated_rows, terminal_404_source_ids = _exclude_terminal_404_supporting_rows(
        connection,
        generated_rows,
    )
    if terminal_404_source_ids:
        discovery_notes.append(
            f"Excluded {len(terminal_404_source_ids)} supporting source(s) after a persisted terminal HTTP 404."
        )
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
              AND discovery_role <> 'detail'
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
    rejected_detail_count = _deactivate_rejected_generated_detail_sources(
        connection,
        bank_code=bank_code,
        product_type=product_type,
        normalized_urls=list(generation_result.rejected_detail_urls),
    )
    if rejected_detail_count:
        discovery_notes.append(
            f"Deactivated {rejected_detail_count} previously generated detail source(s) that failed current detail-page validation."
        )
    hard_scope_excluded_count = _deactivate_hard_scope_excluded_generated_detail_sources(
        connection,
        bank_code=bank_code,
        country_code=str(row["country_code"]),
        product_type=product_type,
        source_language=str(row.get("source_language") or "en"),
    )
    if hard_scope_excluded_count:
        discovery_notes.append(
            f"Deactivated {hard_scope_excluded_count} previously generated detail source(s) with deterministic hard-scope exclusions."
        )
    case_alias_count = _deactivate_case_alias_generated_detail_sources(
        connection,
        bank_code=bank_code,
        product_type=product_type,
        selected_normalized_urls=[
            str(item.get("normalized_url") or "")
            for item in generated_rows
            if str(item.get("discovery_role") or "") == "detail"
        ],
    )
    if case_alias_count:
        discovery_notes.append(
            f"Deactivated {case_alias_count} previously generated case-only detail URL alias(es)."
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
        discovery_metrics=generation_result.discovery_metrics,
    )


def _exclude_terminal_404_supporting_rows(
    connection: Connection,
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    supporting_source_ids = sorted(
        {
            str(row.get("source_id") or "").strip()
            for row in rows
            if str(row.get("discovery_role") or "").strip().lower() in _TERMINAL_SUPPORTING_ROLES
            and str(row.get("source_id") or "").strip()
        }
    )
    if not supporting_source_ids:
        return rows, []

    terminal_rows = connection.execute(
        """
        WITH latest_source_attempt AS (
            SELECT DISTINCT ON (sd.source_metadata ->> 'source_id')
                sd.source_metadata ->> 'source_id' AS source_id,
                rsi.stage_status,
                rsi.error_summary
            FROM run_source_item AS rsi
            JOIN source_document AS sd
              ON sd.source_document_id = rsi.source_document_id
            WHERE sd.source_metadata ->> 'source_id' = ANY(%(source_ids)s)
            ORDER BY
                sd.source_metadata ->> 'source_id',
                rsi.updated_at DESC,
                rsi.created_at DESC
        )
        SELECT source_id
        FROM latest_source_attempt
        WHERE stage_status = 'failed'
          AND (
              LOWER(COALESCE(error_summary, '')) LIKE '%%http%%404%%'
              OR LOWER(COALESCE(error_summary, '')) LIKE '%%status 404%%'
          )
        """,
        {"source_ids": supporting_source_ids},
    ).fetchall()
    terminal_source_ids = sorted(
        {
            str(row.get("source_id") or "").strip()
            for row in terminal_rows
            if str(row.get("source_id") or "").strip()
        }
    )
    if not terminal_source_ids:
        return rows, []

    terminal_source_id_set = set(terminal_source_ids)
    connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            change_reason = 'terminal_404_supporting_source',
            updated_at = %(updated_at)s
        WHERE source_id = ANY(%(source_ids)s)
          AND status <> 'removed'
        """,
        {
            "source_ids": terminal_source_ids,
            "updated_at": utc_now(),
        },
    )
    return (
        [
            row
            for row in rows
            if str(row.get("source_id") or "").strip() not in terminal_source_id_set
        ],
        terminal_source_ids,
    )


def _load_existing_precision_discovery_seeds(
    connection: Connection,
    *,
    bank_code: str,
    country_code: str,
    product_type: str,
    source_language: str,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            source_id,
            source_name,
            source_url,
            normalized_url,
            discovery_role,
            priority,
            source_language,
            expected_fields
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND status = 'active'
          AND source_type = 'html'
          AND discovery_role IN ('entry', 'detail')
        ORDER BY
            CASE discovery_role WHEN 'entry' THEN 0 ELSE 1 END,
            priority,
            source_id
        """,
        {
            "bank_code": bank_code,
            "country_code": country_code,
            "product_type_scope": _product_type_scope_codes(product_type),
        },
    ).fetchall()
    return [
        dict(item)
        for item in rows
        if not _url_locale_conflicts_source_language(
            normalized_url=str(item.get("normalized_url") or item.get("source_url") or ""),
            source_language=source_language,
        )
    ][:_DISCOVERY_REGISTRY_SEED_MAX]


def _load_existing_detail_rows_for_companion_discovery(
    connection: Connection,
    *,
    bank_code: str,
    country_code: str,
    product_type: str,
    source_language: str,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT normalized_url, source_url
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND status = 'active'
          AND discovery_role = 'detail'
          AND source_type = 'html'
        ORDER BY priority, source_id
        """,
        {
            "bank_code": bank_code,
            "country_code": country_code,
            "product_type_scope": _product_type_scope_codes(product_type),
        },
    ).fetchall()
    details: list[dict[str, Any]] = []
    for row in rows:
        normalized_url = normalize_source_url(str(row["normalized_url"] or row["source_url"]))
        if _url_country_scope_conflicts(
            country_code=country_code,
            normalized_url=normalized_url,
        ):
            continue
        if _url_locale_conflicts_source_language(
            normalized_url=normalized_url,
            source_language=source_language,
        ):
            continue
        details.append(
            {
                "normalized_url": normalized_url,
                "raw_url": str(row["source_url"]),
            }
        )
        if len(details) >= _DISCOVERY_DETAIL_LINK_MAX:
            break
    return details


def _generate_existing_detail_companion_rows(
    *,
    bank_code: str,
    bank_name: str,
    country_code: str,
    product_type: str,
    product_type_definition: dict[str, Any],
    homepage_url: str,
    source_language: str,
    existing_detail_rows: list[dict[str, Any]],
    coverage_source_url: str | None = None,
    coverage_source_metadata: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not existing_detail_rows:
        return [], []
    localized_definition = localize_product_type_definition(
        country_code=country_code,
        definition=product_type_definition,
    )
    normalized_homepage_url = normalize_source_url(homepage_url)
    hostname = urlparse(normalized_homepage_url).hostname
    if not hostname:
        return [], []
    _, normalized_coverage_source_url = _normalize_coverage_source_url(
        coverage_source_url,
        normalized_homepage_url=normalized_homepage_url,
        coverage_source_metadata=coverage_source_metadata,
    )
    allowed_domains = _coverage_allowed_domains(
        normalized_homepage_url=normalized_homepage_url,
        normalized_coverage_source_url=normalized_coverage_source_url,
        coverage_source_metadata=coverage_source_metadata,
    )
    discovery_product_type = _product_type_discovery_profile(
        product_type,
        localized_definition,
    )
    companions, notes = _discover_detail_companion_links(
        detail_rows=existing_detail_rows,
        country_code=country_code,
        product_type=discovery_product_type,
        fetch_policy=DiscoveryFetchPolicy.from_env(allowed_domains=allowed_domains),
        hostname=hostname,
        allowed_domains=allowed_domains,
        page_html_by_url={},
    )
    expected_fields = _product_type_expected_fields(
        localized_definition,
        country_code=country_code,
    )
    product_type_label = _product_type_label(localized_definition)
    rows = [
        _build_generated_source_row(
            bank_code=bank_code,
            country_code=country_code,
            product_type=product_type,
            source_language=source_language,
            normalized_url=companion.link.normalized_url,
            raw_url=companion.link.resolved_url,
            source_name=_generated_link_name(
                bank_name,
                product_type_label,
                companion.link.anchor_text,
                fallback="pricing disclosure",
                normalized_url=companion.link.normalized_url,
            ),
            discovery_role=(
                "linked_pdf" if companion.link.source_type == "pdf" else "supporting_html"
            ),
            priority="P1",
            purpose=f"Exact-product pricing or terms companion for {product_type_label}",
            expected_fields=expected_fields,
            discovery_metadata={
                "selection_path": "selected_existing_detail_companion",
                "selection_confidence": "high",
                "selection_reason_codes": [
                    "existing_exact_product_detail_link",
                    "pricing_or_terms_companion",
                ],
                "candidate_origin": "existing_detail_outbound_link",
                "parent_detail_url": companion.parent_detail_url,
                "heuristic_score": companion.score,
            },
        )
        for companion in companions
    ]
    return rows, notes


def repair_catalog_coverage_route(
    connection: Connection,
    *,
    row: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
    run_id: str,
    correlation_id: str | None,
    invoke_model: Any | None = None,
) -> CoverageRouteRepairResult:
    """Resolve a missing/stale product route after bounded homepage discovery is exhausted."""
    if not llm_provider_configured():
        return CoverageRouteRepairResult(
            status="uncertain",
            coverage_source_url=None,
            coverage_source_metadata={},
            notes=["Coverage-route repair was unavailable because the OpenAI provider was not configured."],
        )

    product_type = _canonical_product_type_code(row["product_type"])
    definition = localize_product_type_definition(
        country_code=str(row["country_code"]),
        definition=require_product_type_definition(
            connection,
            product_type_code=product_type,
            active_only=False,
        ),
    )
    model_id = configured_model_id()
    started_at = datetime.now(UTC)
    provider_metadata: dict[str, Any] = {}
    raw_result: dict[str, Any] = {}
    execution_status = "completed"
    error_summary: str | None = None
    try:
        resolver = invoke_model or invoke_openai_json_schema
        raw_result, provider_metadata = resolver(
            instructions=_coverage_route_resolution_instructions(),
            payload={
                "bank_code": str(row["bank_code"]),
                "bank_name": str(row["bank_name"]),
                "country_code": str(row["country_code"]),
                "homepage_url": str(row["homepage_url"]),
                "product_type": product_type,
                "product_type_definition": {
                    "display_name": _product_type_label(definition),
                    "description": str(definition.get("description") or ""),
                    "discovery_keywords": _product_type_keywords(definition),
                },
                "existing_coverage_source_url": _clean_text(row.get("coverage_source_url")),
                "existing_coverage_route_rejected_by_retail_detail_discovery": bool(
                    _clean_text(row.get("coverage_source_url"))
                ),
            },
            schema_name=_COVERAGE_ROUTE_RESOLUTION_SCHEMA_NAME,
            schema=_COVERAGE_ROUTE_RESOLUTION_SCHEMA,
            model_id=model_id,
            require_web_search=True,
        )
        result = _sanitize_coverage_route_resolution(
            raw_result=raw_result,
            provider_metadata=provider_metadata,
            bank_name=str(row["bank_name"]),
            homepage_url=str(row["homepage_url"]),
            product_type=product_type,
            product_type_definition=definition,
        )
    except Exception as exc:
        execution_status = "failed"
        error_summary = str(exc)[:800]
        result = CoverageRouteRepairResult(
            status="uncertain",
            coverage_source_url=None,
            coverage_source_metadata={},
            notes=[f"Coverage-route repair was inconclusive: {error_summary}"],
        )
    completed_at = datetime.now(UTC)

    model_execution_id = _coverage_route_model_execution_id(
        run_id=run_id,
        catalog_item_id=str(row["catalog_item_id"]),
    )
    execution_metadata = {
        "bank_code": str(row["bank_code"]),
        "country_code": str(row["country_code"]),
        "product_type": product_type,
        "catalog_item_id": str(row["catalog_item_id"]),
        "correlation_id": correlation_id,
        "request_id": request_context.get("request_id"),
        "resolution_status": result.status,
        "coverage_source_url": result.coverage_source_url,
        "resolution_summary": _clean_text(raw_result.get("summary")),
        "provider_resolution": {
            key: (_clean_text(raw_result.get(key)) or None)
            for key in (
                "status",
                "coverage_source_url",
                "current_offering_quote",
                "relationship_source_url",
                "relationship_quote",
                "not_offered_source_url",
                "not_offered_quote",
            )
        },
        "web_search_sources": list(provider_metadata.get("web_search_sources") or [])[:40],
    }
    if error_summary:
        execution_metadata["error_summary"] = error_summary
    prompt_tokens = int(provider_metadata.get("prompt_tokens") or 0)
    completion_tokens = int(provider_metadata.get("completion_tokens") or 0)
    _persist_source_catalog_usage_records(
        connection,
        model_execution_records=[
            {
                "model_execution_id": model_execution_id,
                "run_id": run_id,
                "source_document_id": None,
                "stage_name": "source_catalog_coverage_resolution",
                "agent_name": "fpds-coverage-route-resolver",
                "model_id": str(provider_metadata.get("model_id") or model_id),
                "execution_status": execution_status,
                "execution_metadata": execution_metadata,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
            }
        ],
        usage_records=(
            [
                {
                    "llm_usage_id": _build_source_catalog_ai_usage_id(model_execution_id),
                    "model_execution_id": model_execution_id,
                    "run_id": run_id,
                    "candidate_id": None,
                    "provider_request_id": provider_metadata.get("provider_request_id"),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "estimated_cost": estimated_cost_usd(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    ),
                    "usage_metadata": {
                        "usage_mode": "openai-source-catalog-coverage-resolution",
                        "provider": str(provider_metadata.get("provider") or "openai"),
                        "model_id": str(provider_metadata.get("model_id") or model_id),
                    },
                    "recorded_at": completed_at.isoformat(),
                }
            ]
            if provider_metadata
            else []
        ),
    )

    now = utc_now()
    if result.status == "current_offering" and result.coverage_source_url:
        normalized_url = normalize_source_url(result.coverage_source_url)
        connection.execute(
            """
            UPDATE source_registry_catalog_item
            SET
                status = 'active',
                coverage_source_url = %(coverage_source_url)s,
                normalized_coverage_source_url = %(normalized_coverage_source_url)s,
                coverage_source_metadata = %(coverage_source_metadata)s::jsonb,
                change_reason = 'ai_verified_current_coverage_route',
                updated_at = %(updated_at)s
            WHERE catalog_item_id = %(catalog_item_id)s
            """,
            {
                "catalog_item_id": str(row["catalog_item_id"]),
                "coverage_source_url": result.coverage_source_url,
                "normalized_coverage_source_url": normalized_url,
                "coverage_source_metadata": json.dumps(result.coverage_source_metadata, ensure_ascii=True),
                "updated_at": now,
            },
        )
        _record_catalog_audit_event(
            connection,
            actor=actor,
            request_context=request_context,
            event_type="source_catalog_coverage_route_repaired",
            target_id=str(row["catalog_item_id"]),
            target_type="source_registry_catalog_item",
            diff_summary=f"Verified current coverage route for `{row['catalog_item_id']}`.",
            metadata={
                "bank_code": str(row["bank_code"]),
                "product_type": product_type,
                "coverage_source_url": result.coverage_source_url,
                "coverage_domain": result.coverage_source_metadata.get("coverage_domain"),
                "model_execution_id": model_execution_id,
            },
        )
    elif result.status == "not_currently_offered":
        connection.execute(
            """
            UPDATE source_registry_catalog_item
            SET
                status = 'inactive',
                coverage_source_metadata = %(coverage_source_metadata)s::jsonb,
                change_reason = 'ai_verified_product_not_currently_offered',
                updated_at = %(updated_at)s
            WHERE catalog_item_id = %(catalog_item_id)s
            """,
            {
                "catalog_item_id": str(row["catalog_item_id"]),
                "coverage_source_metadata": json.dumps(result.coverage_source_metadata, ensure_ascii=True),
                "updated_at": now,
            },
        )
        _record_catalog_audit_event(
            connection,
            actor=actor,
            request_context=request_context,
            event_type="source_catalog_coverage_deactivated",
            target_id=str(row["catalog_item_id"]),
            target_type="source_registry_catalog_item",
            diff_summary=f"Deactivated unavailable coverage `{row['catalog_item_id']}`.",
            metadata={
                "bank_code": str(row["bank_code"]),
                "product_type": product_type,
                "evidence_url": result.coverage_source_metadata.get("not_offered_source_url"),
                "model_execution_id": model_execution_id,
            },
        )
    return result


def _coverage_route_resolution_instructions() -> str:
    return (
        "You repair one FPDS retail-consumer bank Product Type coverage route using live web search. Find the current official "
        "public retail product or product-family page, including an official consumer brand domain when the legal bank "
        "uses a different customer-facing domain. A current offering requires a current product/detail/catalog "
        "page, not an article, investor page, historical announcement, help-only page, login, application flow, "
        "legacy servicing page, transaction-banking page, corporate cash-management page, institutional product, "
        "or business/commercial product. In the United States, the supplied GIC Product Type means a consumer "
        "Certificate of Deposit/CD, not a corporate term deposit. If the payload says an existing route was rejected "
        "by retail detail discovery, do not reuse it unless the page itself contains unambiguous retail-consumer "
        "product evidence. Return an exact short quote from the product page that names the Product Type. "
        "When the route is on another domain, also return a consulted official page and exact quote proving that "
        "the brand/product is provided by or is a brand of the supplied bank. If official current evidence instead "
        "explicitly says the product was sold, transferred, discontinued, is no longer offered, or no longer accepts "
        "customers, return not_currently_offered with that exact quote. Absence from navigation is not enough; use "
        "uncertain unless positive current or retirement evidence exists. Never invent a URL or quote. Prefer HTML "
        "evidence pages and return only URLs actually consulted during web search."
    )


def _sanitize_coverage_route_resolution(
    *,
    raw_result: dict[str, Any],
    provider_metadata: dict[str, Any],
    bank_name: str,
    homepage_url: str,
    product_type: str,
    product_type_definition: dict[str, Any],
) -> CoverageRouteRepairResult:
    status = str(raw_result.get("status") or "uncertain").strip()
    summary = _clean_text(raw_result.get("summary")) or "Coverage resolver returned no summary."
    consulted_keys = {
        key
        for source in provider_metadata.get("web_search_sources") or []
        for key in [_coverage_citation_key(source.get("url"))]
        if key
    }
    if not consulted_keys:
        raise ValueError("Coverage resolver returned no consulted web sources.")

    identity_terms = _product_type_identity_keywords(product_type, product_type_definition)
    homepage_host = _normalized_hostname(urlparse(homepage_url).hostname or "")
    if status == "current_offering":
        coverage_url = _validated_consulted_https_url(
            raw_result.get("coverage_source_url"),
            consulted_keys=consulted_keys,
            require_consulted=False,
        )
        if infer_source_type(coverage_url) != "html":
            raise ValueError("Current coverage route must be an HTML page.")
        current_quote = _required_coverage_quote(raw_result.get("current_offering_quote"))
        if not _coverage_quote_identifies_product_type(
            current_quote,
            identity_terms=identity_terms,
        ):
            raise ValueError("Current offering quote did not identify the requested Product Type.")
        _require_exact_quote_on_page(url=coverage_url, quote=current_quote)
        coverage_host = _normalized_hostname(urlparse(coverage_url).hostname or "")
        route_scope_reason = _source_scope_exclusion_reason(
            product_type=product_type,
            # Scope the proposed route from its own evidence. The resolver summary
            # may explain why a prior business route was rejected; including that
            # narrative here can incorrectly taint a valid consumer replacement.
            fingerprint=f"{coverage_url} {current_quote}",
        )
        if route_scope_reason:
            raise ValueError(
                f"Current coverage route failed retail Product Type scope: {route_scope_reason}."
            )

        relationship_url = _clean_text(raw_result.get("relationship_source_url"))
        relationship_quote = _clean_text(raw_result.get("relationship_quote"))
        if coverage_host != homepage_host:
            relationship_url = _validated_consulted_https_url(
                relationship_url,
                consulted_keys=consulted_keys,
                require_consulted=False,
            )
            relationship_host = _normalized_hostname(urlparse(relationship_url).hostname or "")
            if relationship_host not in {homepage_host, coverage_host}:
                raise ValueError("Brand relationship evidence must be on the bank or coverage domain.")
            relationship_quote = _required_coverage_quote(relationship_quote)
            if not _quote_identifies_bank(relationship_quote, bank_name=bank_name):
                raise ValueError("Brand relationship quote did not identify the bank.")
            if relationship_host != coverage_host and not _quote_identifies_coverage_domain(
                relationship_quote,
                coverage_host=coverage_host,
            ):
                raise ValueError("Brand relationship quote did not identify the coverage brand domain.")
            _require_quote_evidence(
                url=relationship_url,
                quote=relationship_quote,
                consulted_keys=consulted_keys,
            )
        else:
            relationship_url = relationship_url or coverage_url
            relationship_quote = relationship_quote or bank_name

        metadata = {
            "verification_status": "verified",
            "verification_method": "ai_web_search_exact_quote",
            "homepage_domain": homepage_host,
            "coverage_domain": coverage_host,
            "relationship_source_url": relationship_url,
            "relationship_quote": relationship_quote,
            "current_offering_quote": current_quote,
            "verified_at": utc_now().isoformat(),
            "resolution_summary": summary,
        }
        return CoverageRouteRepairResult(
            status=status,
            coverage_source_url=coverage_url,
            coverage_source_metadata=metadata,
            notes=[
                f"AI web resolution verified a current official coverage route on `{coverage_host}`.",
                summary,
            ],
        )

    if status == "not_currently_offered":
        evidence_url = _validated_consulted_https_url(
            raw_result.get("not_offered_source_url"),
            consulted_keys=consulted_keys,
            require_consulted=False,
        )
        evidence_quote = _required_coverage_quote(raw_result.get("not_offered_quote"))
        lowered_quote = evidence_quote.lower()
        retirement_terms = (
            "no longer",
            "stop accepting",
            "stopped accepting",
            "discontinued",
            "transferred",
            "transfer of",
            "sold",
            "sale of",
            "ceased",
            "winding down",
            "wind down",
        )
        retirement_identity_terms = list(identity_terms)
        if product_type == "personal-loan":
            retirement_identity_terms.extend(["loan", "loans", "unsecured loan"])
        if not _coverage_quote_identifies_product_type(
            evidence_quote,
            identity_terms=retirement_identity_terms,
        ) or not any(term in lowered_quote for term in retirement_terms):
            raise ValueError("Not-offered evidence lacked both product identity and an explicit retirement signal.")
        evidence_host = _normalized_hostname(urlparse(evidence_url).hostname or "")
        if evidence_host != homepage_host:
            relationship_url = _validated_consulted_https_url(
                raw_result.get("relationship_source_url"),
                consulted_keys=consulted_keys,
                require_consulted=False,
            )
            relationship_quote = _required_coverage_quote(raw_result.get("relationship_quote"))
            relationship_host = _normalized_hostname(urlparse(relationship_url).hostname or "")
            regulator_evidence = _is_authoritative_government_domain(evidence_host)
            if relationship_host not in {homepage_host, evidence_host} and not regulator_evidence:
                raise ValueError(
                    "Retirement relationship evidence must be on the bank/brand domain or paired with government evidence."
                )
            if not _quote_identifies_bank(relationship_quote, bank_name=bank_name):
                raise ValueError("Retirement relationship quote did not identify the bank.")
            if relationship_host not in {homepage_host, evidence_host} and not _quote_identifies_coverage_domain(
                relationship_quote,
                coverage_host=relationship_host,
            ):
                raise ValueError("Retirement relationship quote did not identify the evidence brand domain.")
            if regulator_evidence and relationship_host not in {homepage_host, evidence_host} and not _quote_identifies_coverage_domain(
                evidence_quote,
                coverage_host=relationship_host,
            ):
                raise ValueError("Government retirement evidence did not identify the official bank brand.")
            _require_quote_evidence(
                url=relationship_url,
                quote=relationship_quote,
                consulted_keys=consulted_keys,
            )
        _require_quote_evidence(
            url=evidence_url,
            quote=evidence_quote,
            consulted_keys=consulted_keys,
        )
        metadata = {
            "verification_status": "verified_not_currently_offered",
            "verification_method": "ai_web_search_exact_quote",
            "homepage_domain": homepage_host,
            "not_offered_source_url": evidence_url,
            "not_offered_quote": evidence_quote,
            "verified_at": utc_now().isoformat(),
            "resolution_summary": summary,
        }
        return CoverageRouteRepairResult(
            status=status,
            coverage_source_url=None,
            coverage_source_metadata=metadata,
            notes=["Official evidence verified that this Product Type is not currently offered.", summary],
        )

    return CoverageRouteRepairResult(
        status="uncertain",
        coverage_source_url=None,
        coverage_source_metadata={},
        notes=["AI web resolution could not verify a current product route or explicit retirement evidence.", summary],
    )


def _validated_consulted_https_url(
    value: Any,
    *,
    consulted_keys: set[str],
    require_consulted: bool = True,
) -> str:
    cleaned = _required_text(value, "coverage evidence URL")
    normalized = normalize_source_url(cleaned)
    parsed = urlparse(normalized)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("Coverage evidence URL must be public HTTPS.")
    if require_consulted and _coverage_citation_key(normalized) not in consulted_keys:
        raise ValueError("Coverage evidence URL was not present in consulted web-search sources.")
    return normalized


def _coverage_citation_key(value: Any) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return ""
    try:
        normalized = normalize_source_url(cleaned)
    except ValueError:
        return ""
    parsed = urlparse(normalized)
    host = _normalized_hostname(parsed.hostname or "")
    path = re.sub(r"/+", "/", unquote(parsed.path or "/")).rstrip("/") or "/"
    return f"{host}{path}".lower()


def _required_coverage_quote(value: Any) -> str:
    quote = _clean_text(value)
    if quote:
        # Web-search providers sometimes preserve Markdown presentation from a
        # rendered heading even though the official HTML contains only its text.
        quote = re.sub(r"^(?:#{1,6}\s+|>\s+|[-*]\s+)", "", quote).strip()
    if not quote or len(quote) < 8 or len(quote) > 600:
        raise ValueError("Coverage evidence quote must contain 8 to 600 characters.")
    return _collapse_whitespace(quote)


def _require_exact_quote_on_page(*, url: str, quote: str) -> None:
    host = _normalized_hostname(urlparse(url).hostname or "")
    html_text = fetch_text(url, DiscoveryFetchPolicy.from_env(allowed_domains=(host,)))
    page_text = _collapse_whitespace(
        html_lib.unescape(re.sub(r"<[^>]+>", " ", html_text))
    ).lower()
    normalized_quote = _collapse_whitespace(html_lib.unescape(quote)).lower()
    if normalized_quote not in page_text:
        raise ValueError("Coverage evidence quote was not found in the freshly fetched official page.")


def _require_quote_evidence(*, url: str, quote: str, consulted_keys: set[str]) -> None:
    if infer_source_type(url) == "pdf":
        if _coverage_citation_key(url) not in consulted_keys:
            raise ValueError("PDF coverage evidence was not present in consulted web-search sources.")
        return
    _require_exact_quote_on_page(url=url, quote=quote)


def _quote_identifies_bank(quote: str, *, bank_name: str) -> bool:
    quote_tokens = set(re.findall(r"[a-z0-9]+", quote.lower()))
    bank_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", bank_name.lower())
        if token not in {"bank", "banking", "national", "association", "na", "usa", "us"}
    ]
    if not bank_tokens:
        return False
    required_count = 1 if len(bank_tokens) == 1 else 2
    return len(set(bank_tokens).intersection(quote_tokens)) >= required_count


def _quote_identifies_coverage_domain(quote: str, *, coverage_host: str) -> bool:
    host_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", coverage_host.lower())
        if token not in {"www", "com", "org", "net", "bank", "banking", "co"}
    ]
    if not host_tokens:
        return False
    quote_tokens = set(re.findall(r"[a-z0-9]+", quote.lower()))
    return any(token in quote_tokens for token in host_tokens)


def _coverage_quote_identifies_product_type(
    quote: str,
    *,
    identity_terms: list[str],
) -> bool:
    replacements = {
        "accounts": "account",
        "cards": "card",
        "certificates": "certificate",
        "deposits": "deposit",
        "gics": "gic",
        "loans": "loan",
        "mortgages": "mortgage",
        "cds": "cd",
    }

    def normalize(value: str) -> str:
        tokens = re.findall(r"[a-z0-9]+", value.lower())
        return " ".join(replacements.get(token, token) for token in tokens)

    normalized_quote = normalize(quote)
    return any(normalize(term) in normalized_quote for term in identity_terms if normalize(term))


def _is_authoritative_government_domain(hostname: str) -> bool:
    normalized = _normalized_hostname(hostname)
    return normalized.endswith(".gov") or ".gov." in normalized


def _coverage_route_model_execution_id(*, run_id: str, catalog_item_id: str) -> str:
    digest = hashlib.sha256(
        f"{run_id}|{catalog_item_id}|coverage_route_resolution".encode("utf-8")
    ).hexdigest()[:20]
    return f"modelexec-{digest}"


def _deactivate_rejected_generated_detail_sources(
    connection: Connection,
    *,
    bank_code: str,
    product_type: str,
    normalized_urls: list[str],
) -> int:
    rejected_urls = sorted({normalize_source_url(item) for item in normalized_urls if str(item).strip()})
    if not rejected_urls:
        return 0
    result = connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            updated_at = %(updated_at)s,
            change_reason = 'rejected_by_homepage_detail_validation'
        WHERE bank_code = %(bank_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND normalized_url = ANY(%(normalized_urls)s)
          AND discovery_role = 'detail'
          AND status = 'active'
          AND seed_source_flag = false
          AND source_id LIKE 'AUTO-%%'
        """,
        {
            "updated_at": utc_now(),
            "bank_code": bank_code,
            "product_type_scope": _product_type_scope_codes(product_type),
            "normalized_urls": rejected_urls,
        },
    )
    return max(0, int(result.rowcount or 0))


def _deactivate_hard_scope_excluded_generated_detail_sources(
    connection: Connection,
    *,
    bank_code: str,
    country_code: str,
    product_type: str,
    source_language: str,
) -> int:
    rows = connection.execute(
        """
        SELECT source_id, normalized_url, source_name, discovery_metadata
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND discovery_role = 'detail'
          AND status = 'active'
          AND seed_source_flag = false
          AND source_id LIKE 'AUTO-%%'
        """,
        {
            "bank_code": bank_code,
            "country_code": country_code,
            "product_type_scope": _product_type_scope_codes(product_type),
        },
    ).fetchall()
    excluded_ids: list[str] = []
    exclusion_reasons: set[str] = set()
    for raw_row in rows:
        row = dict(raw_row)
        metadata = row.get("discovery_metadata") if isinstance(row.get("discovery_metadata"), dict) else {}
        fingerprint = " ".join(
            str(value or "")
            for value in (
                row.get("normalized_url"),
                row.get("source_name"),
                metadata.get("page_title"),
                metadata.get("primary_heading"),
            )
        )
        reason = (
            "other_country_market_route"
            if _url_country_scope_conflicts(
                country_code=country_code,
                normalized_url=str(row.get("normalized_url") or ""),
            )
            else (
                "other_source_language_route"
                if _url_locale_conflicts_source_language(
                    normalized_url=str(row.get("normalized_url") or ""),
                    source_language=source_language,
                )
                else _source_scope_exclusion_reason(product_type=product_type, fingerprint=fingerprint)
            )
        )
        if reason is None:
            continue
        excluded_ids.append(str(row["source_id"]))
        exclusion_reasons.add(reason)
    if not excluded_ids:
        return 0
    result = connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            updated_at = %(updated_at)s,
            change_reason = %(change_reason)s
        WHERE source_id = ANY(%(source_ids)s)
        """,
        {
            "updated_at": utc_now(),
            "change_reason": "hard_scope_exclusion:" + ",".join(sorted(exclusion_reasons)),
            "source_ids": sorted(set(excluded_ids)),
        },
    )
    return max(0, int(result.rowcount or 0))


def _deactivate_case_alias_generated_detail_sources(
    connection: Connection,
    *,
    bank_code: str,
    product_type: str,
    selected_normalized_urls: list[str],
) -> int:
    """Deactivate stale generated paths that differ only by URL casing.

    A currently selected and page-validated detail URL is authoritative for
    this collection slice. Keeping an older AUTO detail with the same
    case-folded URL creates duplicate candidates on case-insensitive bank
    sites even when their rendered HTML has small dynamic differences.
    """

    selected = {
        normalize_source_url(item)
        for item in selected_normalized_urls
        if str(item).strip()
    }
    selected_by_fold = {item.casefold(): item for item in selected}
    if not selected_by_fold:
        return 0
    rows = connection.execute(
        """
        SELECT source_id, normalized_url
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND discovery_role = 'detail'
          AND status = 'active'
          AND seed_source_flag = false
          AND source_id LIKE 'AUTO-%%'
        """,
        {
            "bank_code": bank_code,
            "product_type_scope": _product_type_scope_codes(product_type),
        },
    ).fetchall()
    alias_ids = sorted(
        str(row["source_id"])
        for row in rows
        if (
            str(row.get("normalized_url") or "").casefold() in selected_by_fold
            and str(row.get("normalized_url") or "")
            != selected_by_fold[str(row.get("normalized_url") or "").casefold()]
        )
    )
    if not alias_ids:
        return 0
    result = connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            updated_at = %(updated_at)s,
            change_reason = 'superseded_case_only_url_alias'
        WHERE source_id = ANY(%(source_ids)s)
        """,
        {
            "updated_at": utc_now(),
            "source_ids": alias_ids,
        },
    )
    return max(0, int(result.rowcount or 0))


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
            ON CONFLICT (country_code, bank_code, product_type, normalized_url, source_type) DO UPDATE
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
    coverage_source_url: str | None = None,
    coverage_source_metadata: dict[str, Any] | None = None,
    run_id: str | None = None,
    correlation_id: str | None = None,
    request_id: str | None = None,
    registry_seed_rows: list[dict[str, Any]] | None = None,
) -> HomepageSourceGenerationResult:
    product_type = _canonical_product_type_code(product_type)
    product_type_definition = localize_product_type_definition(
        country_code=country_code,
        definition=product_type_definition,
    )
    product_type_definition = _apply_bank_product_type_discovery_aliases(
        bank_code=bank_code,
        product_type=product_type,
        product_type_definition=product_type_definition,
    )
    discovery_product_type = _product_type_discovery_profile(product_type, product_type_definition)
    normalized_homepage_url = normalize_source_url(homepage_url)
    hostname = urlparse(normalized_homepage_url).hostname
    if not hostname:
        raise SourceRegistryError(status_code=422, code="bank_homepage_invalid", message="Bank homepage URL must include a hostname.")
    verified_coverage_source_url, normalized_coverage_source_url = _normalize_coverage_source_url(
        coverage_source_url,
        normalized_homepage_url=normalized_homepage_url,
        coverage_source_metadata=coverage_source_metadata,
    )

    allowed_domains = _coverage_allowed_domains(
        normalized_homepage_url=normalized_homepage_url,
        normalized_coverage_source_url=normalized_coverage_source_url,
        coverage_source_metadata=coverage_source_metadata,
    )
    fetch_policy = DiscoveryFetchPolicy.from_env(allowed_domains=allowed_domains)
    detail_links: list[tuple[int, Any]] = []
    supporting_links: list[tuple[int, Any]] = []
    pdf_links: list[tuple[int, Any]] = []
    hub_pages: list[tuple[int, str, str]] = []
    secondary_hub_pages: list[tuple[int, str, str]] = []
    registry_detail_pages: list[tuple[int, str, str]] = []
    registry_detail_hints: list[dict[str, Any]] = []
    registry_entry_seed_count = 0
    registry_detail_seed_count = 0
    rejected_registry_seed_count = 0
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
    prefetched_page_html_by_url: dict[str, str] = (
        {normalized_homepage_url: homepage_html}
        if homepage_html
        else {}
    )

    homepage_links = _extract_allowed_links(
        html_text=homepage_html,
        base_url=normalized_homepage_url,
        hostname=hostname,
        allowed_domains=allowed_domains,
    )
    if homepage_html and not homepage_links:
        discovery_notes.append("Homepage fetch succeeded but no allowed detail or supporting links were extracted.")
        if _looks_like_javascript_shell(homepage_html):
            discovery_notes.append(
                "Homepage appears to require JavaScript rendering; add bounded official detail-source URLs or use an approved rendered-HTML discovery path."
            )
    for link in homepage_links:
        fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
        if _has_excluded_product_discovery_link_signal(
            product_type=discovery_product_type,
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
        ):
            continue
        if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
            continue
        if _source_scope_exclusion_reason(product_type=discovery_product_type, fingerprint=fingerprint):
            continue
        score = _score_product_link(
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
        )
        if _is_product_type_rate_page(
            product_type=discovery_product_type,
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
        ):
            supporting_links.append((max(score, 1), link))
            continue
        if _is_product_fact_support_link(
            normalized_url=link.normalized_url,
            anchor_text=link.anchor_text,
            product_score=score,
        ):
            supporting_links.append((max(score, 1), link))
            continue
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

    if verified_coverage_source_url and normalized_coverage_source_url:
        if _url_country_scope_conflicts(
            country_code=country_code,
            normalized_url=normalized_coverage_source_url,
        ):
            discovery_notes.append(
                f"Ignored coverage URL from an explicit different-country route: {normalized_coverage_source_url}."
            )
            verified_coverage_source_url = None
            normalized_coverage_source_url = None
    if verified_coverage_source_url and normalized_coverage_source_url:
        coverage_link = ExtractedLink(
            href=verified_coverage_source_url,
            resolved_url=verified_coverage_source_url,
            normalized_url=normalized_coverage_source_url,
            source_type=infer_source_type(normalized_coverage_source_url),
            anchor_text=_product_type_label(product_type_definition),
        )
        coverage_score = max(
            1,
            _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=normalized_coverage_source_url,
                anchor_text=coverage_link.anchor_text,
            ),
        )
        detail_links.append((coverage_score + 100, coverage_link))
        hub_pages.append((coverage_score + 1_000, normalized_coverage_source_url, verified_coverage_source_url))
        discovery_notes.append(
            "Started bounded discovery from the catalog item's verified official Product Type coverage URL."
        )

    seed_entry_url = _load_seed_entry_url(
        bank_code=bank_code,
        bank_name=bank_name,
        normalized_homepage_url=normalized_homepage_url,
        product_type=discovery_product_type,
    )
    if seed_entry_url is not None and _has_excluded_link_signal(
        normalized_url=seed_entry_url,
        anchor_text="",
    ):
        discovery_notes.append(
            f"Ignored excluded seed entry URL {seed_entry_url}; product discovery continued from official catalog links."
        )
        seed_entry_url = None
    if seed_entry_url is not None and _url_country_scope_conflicts(
        country_code=country_code,
        normalized_url=seed_entry_url,
    ):
        discovery_notes.append(
            f"Ignored seed entry URL from an explicit different-country route: {seed_entry_url}."
        )
        seed_entry_url = None
    if seed_entry_url is not None:
        seed_score = _score_catalog_hub_link(
            product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=seed_entry_url,
            anchor_text="",
        )
        hub_pages.append((max(seed_score, 1) + 100, seed_entry_url, seed_entry_url))

    for registry_seed in registry_seed_rows or []:
        raw_seed_url = str(registry_seed.get("source_url") or registry_seed.get("normalized_url") or "").strip()
        if not raw_seed_url:
            rejected_registry_seed_count += 1
            continue
        try:
            normalized_seed_url = normalize_source_url(raw_seed_url)
        except (TypeError, ValueError):
            rejected_registry_seed_count += 1
            continue
        seed_hostname = urlparse(normalized_seed_url).hostname or ""
        seed_role = str(registry_seed.get("discovery_role") or "").strip().lower()
        seed_fingerprint = f"{normalized_seed_url} {registry_seed.get('source_name') or ''}".lower()
        if (
            seed_role not in {"entry", "detail"}
            or infer_source_type(normalized_seed_url) != "html"
            or not seed_hostname
            or not host_matches_allowed_domains(seed_hostname, allowed_domains)
            or _url_country_scope_conflicts(country_code=country_code, normalized_url=normalized_seed_url)
            or _url_locale_conflicts_source_language(
                normalized_url=normalized_seed_url,
                source_language=source_language,
            )
            or (
                seed_role == "entry"
                and _has_excluded_link_signal(
                    normalized_url=normalized_seed_url,
                    anchor_text=str(registry_seed.get("source_name") or ""),
                )
            )
            or _source_scope_exclusion_reason(
                product_type=discovery_product_type,
                fingerprint=seed_fingerprint,
            )
        ):
            rejected_registry_seed_count += 1
            continue
        seed_score = max(
            1,
            _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=normalized_seed_url,
                anchor_text=str(registry_seed.get("source_name") or ""),
            ),
        )
        if seed_role == "entry":
            registry_entry_seed_count += 1
            hub_pages.append((seed_score + 500, normalized_seed_url, raw_seed_url))
            continue
        registry_detail_seed_count += 1
        registry_detail_pages.append((seed_score, normalized_seed_url, raw_seed_url))
        registry_detail_hints.append(
            {
                "source_id": str(registry_seed.get("source_id") or ""),
                "source_name": str(registry_seed.get("source_name") or ""),
                "source_url": raw_seed_url,
                "normalized_url": normalized_seed_url,
                "priority": str(registry_seed.get("priority") or "P1"),
                "expected_fields": [
                    str(item)
                    for item in (registry_seed.get("expected_fields") or [])
                    if str(item).strip()
                ],
            }
        )
    if registry_entry_seed_count or registry_detail_seed_count:
        discovery_notes.append(
            "Precision coverage reused "
            f"{registry_entry_seed_count} active registry entry seed(s) and "
            f"{registry_detail_seed_count} active registry detail seed(s)."
        )
    if rejected_registry_seed_count:
        discovery_notes.append(
            f"Excluded {rejected_registry_seed_count} registry seed(s) that failed official-domain, country, language, or Product Type scope checks."
        )

    unique_hub_pages = _dedupe_page_candidates(hub_pages)
    selected_hub_pages = unique_hub_pages[:_DISCOVERY_HUB_PAGE_MAX]
    primary_hub_page_attempt_count = 0
    primary_hub_page_fetched_count = 0
    for _score, normalized_page_url, resolved_page_url in selected_hub_pages:
        if normalized_page_url == normalized_homepage_url:
            continue
        primary_hub_page_attempt_count += 1
        try:
            page_html = fetch_text(resolved_page_url, fetch_policy)
        except Exception as exc:
            discovery_notes.append(f"Hub page fetch was unavailable for {normalized_page_url}: {exc}")
            continue
        primary_hub_page_fetched_count += 1
        prefetched_page_html_by_url[normalized_page_url] = page_html
        for link in _extract_allowed_links(
            html_text=page_html,
            base_url=resolved_page_url,
            hostname=hostname,
            allowed_domains=allowed_domains,
        ):
            fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
            if _has_excluded_product_discovery_link_signal(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
                continue
            if _source_scope_exclusion_reason(product_type=discovery_product_type, fingerprint=fingerprint):
                continue
            score = _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            )
            score += _authoritative_catalog_detail_bonus(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                base_score=score,
                parent_url=normalized_page_url,
                seed_entry_url=seed_entry_url,
            )
            if _is_product_type_rate_page(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if _is_product_fact_support_link(
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
                product_score=score,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if link.source_type == "pdf":
                if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                    pdf_links.append((score, link))
                continue
            if score > 0:
                detail_links.append((score, link))
            elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                supporting_links.append((1, link))
            if _looks_like_secondary_catalog_hub(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                secondary_hub_pages.append((max(score, 1), link.normalized_url, link.resolved_url))

    visited_primary_hub_urls = {
        normalized_homepage_url,
        *(item[1] for item in selected_hub_pages),
    }
    registry_detail_page_attempt_count = 0
    registry_detail_page_fetched_count = 0
    unique_registry_detail_pages = _dedupe_page_candidates(registry_detail_pages)
    selected_registry_detail_pages = unique_registry_detail_pages[:_DISCOVERY_REGISTRY_DETAIL_PAGE_MAX]
    for _score, normalized_page_url, resolved_page_url in selected_registry_detail_pages:
        if normalized_page_url in visited_primary_hub_urls:
            continue
        registry_detail_page_attempt_count += 1
        try:
            page_html = fetch_text(resolved_page_url, fetch_policy)
        except Exception as exc:
            discovery_notes.append(
                f"Registry detail seed fetch was unavailable for {normalized_page_url}: {exc}"
            )
            continue
        registry_detail_page_fetched_count += 1
        prefetched_page_html_by_url[normalized_page_url] = page_html
        for link in _extract_allowed_links(
            html_text=page_html,
            base_url=resolved_page_url,
            hostname=hostname,
            allowed_domains=allowed_domains,
        ):
            if link.normalized_url == normalized_page_url:
                continue
            fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
            if _has_excluded_product_discovery_link_signal(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
                continue
            if _source_scope_exclusion_reason(product_type=discovery_product_type, fingerprint=fingerprint):
                continue
            score = _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            )
            if _is_product_type_rate_page(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if _is_product_fact_support_link(
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
                product_score=score,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if link.source_type == "pdf":
                if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                    pdf_links.append((score, link))
                continue
            if score > 0:
                detail_links.append((score, link))
            elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                supporting_links.append((1, link))
            if _looks_like_secondary_catalog_hub(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                secondary_hub_pages.append((max(score, 1), link.normalized_url, link.resolved_url))
    if registry_detail_page_fetched_count:
        discovery_notes.append(
            f"Inspected {registry_detail_page_fetched_count} existing detail page(s) for newly linked sibling products and evidence routes."
        )
    if len(unique_registry_detail_pages) > len(selected_registry_detail_pages):
        discovery_notes.append(
            "Registry detail-page expansion reached its bounded "
            f"{_DISCOVERY_REGISTRY_DETAIL_PAGE_MAX}-page precision limit."
        )

    visited_hub_urls = {normalized_homepage_url, *(item[1] for item in selected_hub_pages)}
    visited_hub_urls.update(item[1] for item in selected_registry_detail_pages)
    expanded_secondary_hub_count = 0
    secondary_hub_page_attempt_count = 0
    for _score, normalized_page_url, resolved_page_url in _dedupe_page_candidates(secondary_hub_pages)[
        :_DISCOVERY_SECONDARY_HUB_PAGE_MAX
    ]:
        if normalized_page_url in visited_hub_urls:
            continue
        visited_hub_urls.add(normalized_page_url)
        secondary_hub_page_attempt_count += 1
        try:
            page_html = fetch_text(resolved_page_url, fetch_policy)
        except Exception as exc:
            discovery_notes.append(f"Secondary hub page fetch was unavailable for {normalized_page_url}: {exc}")
            continue
        expanded_secondary_hub_count += 1
        prefetched_page_html_by_url[normalized_page_url] = page_html
        for link in _extract_allowed_links(
            html_text=page_html,
            base_url=resolved_page_url,
            hostname=hostname,
            allowed_domains=allowed_domains,
        ):
            fingerprint = f"{link.normalized_url} {link.anchor_text}".lower()
            if _has_excluded_product_discovery_link_signal(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
                continue
            if _source_scope_exclusion_reason(product_type=discovery_product_type, fingerprint=fingerprint):
                continue
            score = _score_product_link(
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            )
            if _is_product_type_rate_page(
                product_type=discovery_product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if _is_product_fact_support_link(
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
                product_score=score,
            ):
                supporting_links.append((max(score, 1), link))
                continue
            if link.source_type == "pdf":
                if score > 0 or any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                    pdf_links.append((score, link))
                continue
            if score > 0:
                detail_links.append((score, link))
            elif any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS):
                supporting_links.append((1, link))
    if expanded_secondary_hub_count:
        discovery_notes.append(
            f"Expanded {expanded_secondary_hub_count} bounded secondary product-category hub page(s) for detail coverage."
        )

    all_unique_detail_links = _dedupe_scored_links(detail_links)
    locale_mismatch_detail_candidate_count = sum(
        1
        for _, link in all_unique_detail_links
        if _url_locale_conflicts_source_language(
            normalized_url=link.normalized_url,
            source_language=source_language,
        )
    )
    all_unique_detail_links = [
        item
        for item in all_unique_detail_links
        if not _url_locale_conflicts_source_language(
            normalized_url=item[1].normalized_url,
            source_language=source_language,
        )
    ]
    if locale_mismatch_detail_candidate_count:
        discovery_notes.append(
            f"Excluded {locale_mismatch_detail_candidate_count} detail candidate(s) that conflicted "
            "with the run source language before bounded candidate selection."
        )
    unique_detail_links = all_unique_detail_links[:_DISCOVERY_DETAIL_LINK_MAX]
    all_relevant_supporting_links = [
        item
        for item in _dedupe_scored_links(supporting_links)
        if _link_is_relevant_supporting_source(
            product_type=product_type,
            discovery_product_type=discovery_product_type,
            product_type_definition=product_type_definition,
            normalized_url=item[1].normalized_url,
            anchor_text=item[1].anchor_text,
        )
    ]
    locale_mismatch_supporting_candidate_count = sum(
        1
        for _, link in all_relevant_supporting_links
        if _url_locale_conflicts_source_language(
            normalized_url=link.normalized_url,
            source_language=source_language,
        )
    )
    all_relevant_supporting_links = [
        item
        for item in all_relevant_supporting_links
        if not _url_locale_conflicts_source_language(
            normalized_url=item[1].normalized_url,
            source_language=source_language,
        )
    ]
    unique_supporting_links = all_relevant_supporting_links[:_DISCOVERY_SUPPORTING_LINK_MAX]
    all_unique_pdf_links = _dedupe_scored_links(pdf_links)
    unique_pdf_links = all_unique_pdf_links[:_DISCOVERY_PDF_LINK_MAX]
    seed_detail_hints = [
        *registry_detail_hints,
        *_load_seed_detail_hints(
            bank_code=bank_code,
            bank_name=bank_name,
            normalized_homepage_url=normalized_homepage_url,
            product_type=discovery_product_type,
        ),
    ]
    seed_supporting_hints = _load_seed_supporting_hints(
        bank_code=bank_code,
        bank_name=bank_name,
        normalized_homepage_url=normalized_homepage_url,
        product_type=discovery_product_type,
    )
    source_rows: list[dict[str, Any]] = []
    entry_url = (
        normalized_coverage_source_url
        or seed_entry_url
        or (unique_hub_pages[0][1] if unique_hub_pages else normalized_homepage_url)
    )
    entry_raw_url = (
        verified_coverage_source_url
        or seed_entry_url
        or (unique_hub_pages[0][2] if unique_hub_pages else homepage_url)
    )
    product_type_label = _product_type_label(product_type_definition)
    expected_fields = _product_type_expected_fields(
        product_type_definition,
        country_code=country_code,
    )
    html_candidates = _build_html_candidates(
        product_type=product_type,
        discovery_product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        detail_links=unique_detail_links,
        supporting_links=unique_supporting_links,
        seed_detail_hints=seed_detail_hints,
        verified_coverage_url=normalized_coverage_source_url,
    )
    cross_country_candidate_count = sum(
        1
        for candidate in html_candidates
        if _url_country_scope_conflicts(
            country_code=country_code,
            normalized_url=candidate.normalized_url,
        )
    )
    html_candidates = [
        candidate
        for candidate in html_candidates
        if not _url_country_scope_conflicts(
            country_code=country_code,
            normalized_url=candidate.normalized_url,
        )
    ]
    if cross_country_candidate_count:
        discovery_notes.append(
            f"Excluded {cross_country_candidate_count} source candidate(s) from explicit different-country routes."
        )
    homepage_self_candidate = _build_homepage_self_candidate(
        product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        homepage_url=homepage_url,
        normalized_homepage_url=normalized_homepage_url,
        homepage_html=homepage_html,
    )
    if homepage_self_candidate is not None:
        by_url = {candidate.normalized_url: candidate for candidate in html_candidates}
        _merge_homepage_candidate(by_url, homepage_self_candidate)
        html_candidates = list(by_url.values())
        discovery_notes.append(
            "Included the bank homepage as a bounded detail candidate because its title or primary heading identifies this product type."
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
        allowed_domains=allowed_domains,
        run_id=run_id,
        correlation_id=correlation_id,
        request_id=request_id,
    )
    discovery_notes.extend(ai_result.notes)
    page_evidence_by_url: dict[str, PageEvidenceAssessment] = {}
    page_html_by_url: dict[str, str] = dict(prefetched_page_html_by_url)
    detail_rows, rejected_detail_urls, detail_notes = _promote_detail_candidates(
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
        ai_unavailable=ai_result.ai_unavailable,
        page_evidence_by_url=page_evidence_by_url,
        page_html_by_url=page_html_by_url,
    )
    discovery_notes.extend(detail_notes)
    detail_companions, detail_companion_notes = _discover_detail_companion_links(
        detail_rows=detail_rows,
        country_code=country_code,
        product_type=discovery_product_type,
        fetch_policy=fetch_policy,
        hostname=hostname,
        allowed_domains=allowed_domains,
        page_html_by_url=page_html_by_url,
    )
    discovery_notes.extend(detail_companion_notes)

    should_emit_context_rows = bool(detail_rows) or bool(seed_entry_url)
    if should_emit_context_rows:
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
                    "candidate_origin": "seed_entry_hint" if seed_entry_url else ("hub_page" if unique_hub_pages else "homepage"),
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
    unavailable_supporting_count = 0
    locale_mismatch_supporting_count = locale_mismatch_supporting_candidate_count
    if should_emit_context_rows:
        for companion in detail_companions:
            link = companion.link
            if link.normalized_url in promoted_detail_urls or link.normalized_url in promoted_supporting_urls:
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
                        fallback="pricing disclosure",
                        normalized_url=link.normalized_url,
                    ),
                    discovery_role="linked_pdf" if link.source_type == "pdf" else "supporting_html",
                    priority="P1",
                    purpose=f"Exact-product pricing or terms companion for {product_type_label}",
                    expected_fields=expected_fields,
                    discovery_metadata={
                        "selection_path": "selected_detail_companion",
                        "selection_confidence": "high",
                        "selection_reason_codes": ["exact_product_detail_link", "pricing_or_terms_companion"],
                        "candidate_origin": "selected_detail_outbound_link",
                        "parent_detail_url": companion.parent_detail_url,
                        "heuristic_score": companion.score,
                    },
                )
            )
            promoted_supporting_urls.add(link.normalized_url)
        for hint in seed_supporting_hints:
            normalized_url = normalize_source_url(str(hint["source_url"]))
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=normalized_url):
                continue
            if normalized_url in promoted_detail_urls or normalized_url in promoted_supporting_urls:
                continue
            if not _seed_supporting_hint_is_relevant(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                hint=hint,
            ):
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
            if str(hint.get("source_id") or "").strip():
                source_rows[-1]["source_id"] = str(hint["source_id"])
            promoted_supporting_urls.add(normalized_url)
        ai_supporting_count = 0
        for candidate in html_candidates:
            ai_score = ai_result.scores.get(candidate.normalized_url)
            if ai_score is None or ai_score.predicted_role != "supporting_html":
                continue
            if not _ai_supporting_source_is_relevant(ai_score):
                continue
            if candidate.normalized_url in promoted_detail_urls or candidate.normalized_url in promoted_supporting_urls:
                continue
            if _url_locale_conflicts_source_language(
                normalized_url=candidate.normalized_url,
                source_language=source_language,
            ):
                locale_mismatch_supporting_count += 1
                continue
            if not _supporting_html_page_is_fetchable(
                normalized_url=candidate.normalized_url,
                raw_url=candidate.raw_url,
                fetch_policy=fetch_policy,
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                page_evidence_by_url=page_evidence_by_url,
            ):
                unavailable_supporting_count += 1
                continue
            if not _link_is_relevant_supporting_source(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=candidate.normalized_url,
                anchor_text=candidate.anchor_text,
            ):
                continue
            if not _supporting_source_is_bounded_to_selected_details(
                product_type=discovery_product_type or product_type,
                normalized_url=candidate.normalized_url,
                anchor_text=candidate.anchor_text,
                promoted_detail_urls=promoted_detail_urls,
            ):
                continue
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=candidate.normalized_url,
                    raw_url=candidate.raw_url,
                    source_name=candidate.source_name_hint or _generated_link_name(
                        bank_name,
                        product_type_label,
                        candidate.anchor_text,
                        fallback="support",
                        normalized_url=candidate.normalized_url,
                    ),
                    discovery_role="supporting_html",
                    priority="P1" if ai_score.confidence_band == "high" else "P2",
                    purpose=ai_score.short_rationale or f"AI-classified supporting source for {product_type_label}",
                    expected_fields=candidate.expected_fields_hint or expected_fields,
                    discovery_metadata={
                        "selection_path": "ai_supporting_role",
                        "selection_confidence": ai_score.confidence_band,
                        "selection_reason_codes": _coerce_reason_codes(ai_score.reason_codes),
                        "candidate_origin": candidate.origin,
                        "heuristic_score": candidate.heuristic_score,
                        "ai_parallel_score": ai_score.relevance_score,
                        "ai_predicted_role": ai_score.predicted_role,
                        "ai_confidence_band": ai_score.confidence_band,
                        "ai_reason_codes": _coerce_reason_codes(ai_score.reason_codes),
                        "ai_short_rationale": ai_score.short_rationale,
                    },
                )
            )
            promoted_supporting_urls.add(candidate.normalized_url)
            ai_supporting_count += 1
        if ai_supporting_count:
            discovery_notes.append(
                f"Preserved {ai_supporting_count} AI-classified supporting HTML source(s) for evidence merging."
            )
        deterministic_supporting_count = 0
        for candidate in html_candidates:
            if not candidate.supporting_signal:
                continue
            if candidate.normalized_url in promoted_detail_urls or candidate.normalized_url in promoted_supporting_urls:
                continue
            if _url_locale_conflicts_source_language(
                normalized_url=candidate.normalized_url,
                source_language=source_language,
            ):
                locale_mismatch_supporting_count += 1
                continue
            if not _supporting_html_page_is_fetchable(
                normalized_url=candidate.normalized_url,
                raw_url=candidate.raw_url,
                fetch_policy=fetch_policy,
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                page_evidence_by_url=page_evidence_by_url,
            ):
                unavailable_supporting_count += 1
                continue
            if not _link_is_relevant_supporting_source(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=candidate.normalized_url,
                anchor_text=candidate.anchor_text,
            ):
                continue
            if not _supporting_source_is_bounded_to_selected_details(
                product_type=discovery_product_type or product_type,
                normalized_url=candidate.normalized_url,
                anchor_text=candidate.anchor_text,
                promoted_detail_urls=promoted_detail_urls,
            ):
                continue
            source_rows.append(
                _build_generated_source_row(
                    bank_code=bank_code,
                    country_code=country_code,
                    product_type=product_type,
                    source_language=source_language,
                    normalized_url=candidate.normalized_url,
                    raw_url=candidate.raw_url,
                    source_name=candidate.source_name_hint or _generated_link_name(
                        bank_name,
                        product_type_label,
                        candidate.anchor_text,
                        fallback="support",
                        normalized_url=candidate.normalized_url,
                    ),
                    discovery_role="supporting_html",
                    priority="P2",
                    purpose=f"Deterministic supporting source for {product_type_label}",
                    expected_fields=candidate.expected_fields_hint or expected_fields,
                    discovery_metadata={
                        "selection_path": "deterministic_supporting_fallback",
                        "selection_confidence": "medium",
                        "selection_reason_codes": ["supporting_keyword_match"],
                        "candidate_origin": candidate.origin,
                        "heuristic_score": candidate.heuristic_score,
                    },
                )
            )
            promoted_supporting_urls.add(candidate.normalized_url)
            deterministic_supporting_count += 1
        if deterministic_supporting_count:
            discovery_notes.append(
                f"Preserved {deterministic_supporting_count} deterministically relevant supporting HTML source(s) for evidence merging."
            )
        for _, link in unique_supporting_links:
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
                continue
            if link.normalized_url in promoted_detail_urls:
                continue
            if link.normalized_url in promoted_supporting_urls:
                continue
            if _url_locale_conflicts_source_language(
                normalized_url=link.normalized_url,
                source_language=source_language,
            ):
                locale_mismatch_supporting_count += 1
                continue
            if not _supporting_html_page_is_fetchable(
                normalized_url=link.normalized_url,
                raw_url=link.resolved_url,
                fetch_policy=fetch_policy,
                product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                page_evidence_by_url=page_evidence_by_url,
            ):
                unavailable_supporting_count += 1
                continue
            if not _link_is_relevant_supporting_source(
                product_type=product_type,
                discovery_product_type=discovery_product_type,
                product_type_definition=product_type_definition,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            ):
                continue
            if not _supporting_source_is_bounded_to_selected_details(
                product_type=discovery_product_type or product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
                promoted_detail_urls=promoted_detail_urls,
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
        if unavailable_supporting_count:
            discovery_notes.append(
                f"Excluded {unavailable_supporting_count} unreachable supporting HTML source(s) before collection."
            )
        if locale_mismatch_supporting_count:
            discovery_notes.append(
                f"Excluded {locale_mismatch_supporting_count} supporting HTML source(s) that conflicted with the run source language."
            )
        for _, link in unique_pdf_links:
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
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
        rejected_detail_urls=tuple(rejected_detail_urls),
        discovery_metrics={
            "mode": "precision",
            "homepage_fetch_succeeded": bool(homepage_html),
            "registry_seed_count": registry_entry_seed_count + registry_detail_seed_count,
            "registry_entry_seed_count": registry_entry_seed_count,
            "registry_detail_seed_count": registry_detail_seed_count,
            "registry_seed_rejected_count": rejected_registry_seed_count,
            "primary_hub_page_candidate_count": len(unique_hub_pages),
            "primary_hub_page_attempt_count": primary_hub_page_attempt_count,
            "primary_hub_page_fetched_count": primary_hub_page_fetched_count,
            "registry_detail_page_candidate_count": len(unique_registry_detail_pages),
            "registry_detail_page_attempt_count": registry_detail_page_attempt_count,
            "registry_detail_page_fetched_count": registry_detail_page_fetched_count,
            "secondary_hub_page_candidate_count": len(_dedupe_page_candidates(secondary_hub_pages)),
            "secondary_hub_page_attempt_count": secondary_hub_page_attempt_count,
            "secondary_hub_page_fetched_count": expanded_secondary_hub_count,
            "detail_link_candidate_count": len(all_unique_detail_links),
            "source_language_mismatch_detail_candidate_count": locale_mismatch_detail_candidate_count,
            "supporting_link_candidate_count": len(all_relevant_supporting_links),
            "source_language_mismatch_supporting_candidate_count": locale_mismatch_supporting_candidate_count,
            "pdf_link_candidate_count": len(all_unique_pdf_links),
            "validated_html_candidate_count": len(html_candidates),
            "ai_scored_candidate_count": len(ai_result.scores),
            "promoted_detail_source_count": len(detail_source_ids),
            "promoted_supporting_source_count": sum(
                1
                for item in source_rows
                if str(item.get("discovery_role") or "") in {"supporting_html", "supporting_pdf", "linked_pdf"}
            ),
            "rejected_detail_candidate_count": len(rejected_detail_urls),
            "limits_reached": {
                "primary_hubs": len(unique_hub_pages) > len(selected_hub_pages),
                "registry_detail_pages": len(unique_registry_detail_pages) > len(selected_registry_detail_pages),
                "secondary_hubs": len(_dedupe_page_candidates(secondary_hub_pages)) > _DISCOVERY_SECONDARY_HUB_PAGE_MAX,
                "detail_links": len(all_unique_detail_links) > _DISCOVERY_DETAIL_LINK_MAX,
                "supporting_links": len(all_relevant_supporting_links) > _DISCOVERY_SUPPORTING_LINK_MAX,
                "pdf_links": len(all_unique_pdf_links) > _DISCOVERY_PDF_LINK_MAX,
            },
        },
    )


def _build_html_candidates(
    *,
    product_type: str,
    discovery_product_type: str | None = None,
    product_type_definition: dict[str, Any],
    detail_links: list[tuple[int, Any]],
    supporting_links: list[tuple[int, Any]],
    seed_detail_hints: list[dict[str, Any]],
    verified_coverage_url: str | None = None,
) -> list[HomepageCandidate]:
    scoring_product_type = discovery_product_type or product_type
    by_url: dict[str, HomepageCandidate] = {}
    for score, link in [*detail_links, *supporting_links]:
        supporting_signal = any(keyword in f"{link.normalized_url} {link.anchor_text}".lower() for keyword in _SUPPORTING_KEYWORDS)
        if _looks_like_credit_card_detail_path(
            product_type=scoring_product_type,
            normalized_url=str(link.normalized_url),
        ):
            # `no-fee` is a product attribute in a card slug, not evidence that
            # the page is a fee schedule. Keep likely singular card pages in
            # the detail pool when bounded candidate/page-evidence caps apply.
            supporting_signal = False
        candidate = HomepageCandidate(
            normalized_url=str(link.normalized_url),
            raw_url=str(link.resolved_url),
            anchor_text=str(link.anchor_text),
            source_type=str(link.source_type),
            origin=(
                "verified_coverage_source"
                if verified_coverage_url and str(link.normalized_url) == verified_coverage_url
                else "homepage_or_hub_link"
            ),
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
            {"seed_detail_hint": 0, "verified_coverage_source": 1}.get(item.origin, 2),
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


def _build_homepage_self_candidate(
    *,
    product_type: str,
    product_type_definition: dict[str, Any],
    homepage_url: str,
    normalized_homepage_url: str,
    homepage_html: str,
) -> HomepageCandidate | None:
    if not homepage_html:
        return None
    parser = _PageSignalParser()
    parser.feed(homepage_html)
    identity_text = " ".join([parser.title_text, parser.primary_heading]).strip()
    if not identity_text:
        return None
    identity_terms = _product_type_identity_keywords(product_type, product_type_definition)
    if _term_hits(identity_text, identity_terms) == 0:
        return None
    canonical_product_type = _canonical_product_type_code(product_type)
    if canonical_product_type == "gic" and re.search(
        r"\b(?:\d{1,3}\s*(?:day|days|month|months|year|years)|special|promotional|promo)\b",
        identity_text,
        flags=re.IGNORECASE,
    ):
        return None
    fingerprint = f"{normalized_homepage_url} {identity_text}".lower()
    if _source_scope_exclusion_reason(product_type=product_type, fingerprint=fingerprint):
        return None
    heuristic_score = _score_product_link(
        product_type=product_type,
        product_type_definition=product_type_definition,
        normalized_url=normalized_homepage_url,
        anchor_text=identity_text,
    )
    return HomepageCandidate(
        normalized_url=normalized_homepage_url,
        raw_url=homepage_url,
        anchor_text=identity_text,
        source_type="html",
        origin="homepage_self_detail_candidate",
        heuristic_score=max(1, heuristic_score),
        supporting_signal=False,
        seed_source_id=None,
        source_name_hint=identity_text[:280],
        priority_hint="P1",
        expected_fields_hint=[],
    )


def _looks_like_javascript_shell(html_text: str) -> bool:
    if not html_text:
        return False
    lowered = " ".join(html_text.lower().split())
    explicit_markers = (
        "enable javascript",
        "javascript is required",
        "javascript must be enabled",
        "requires javascript",
        "please turn on javascript",
    )
    return any(marker in lowered for marker in explicit_markers)


def _load_seed_entry_url(
    *,
    bank_code: str,
    product_type: str,
    bank_name: str | None = None,
    normalized_homepage_url: str | None = None,
) -> str | None:
    product_type = _canonical_product_type_code(product_type)
    seed_bank_codes = set(
        _seed_bank_codes_for_scope(
            bank_code=bank_code,
            bank_name=bank_name,
            normalized_homepage_url=normalized_homepage_url,
        )
    )
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) in seed_bank_codes
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) == "entry"
        ):
            return str(item["normalized_url"])
    return None


def _load_seed_detail_hints(
    *,
    bank_code: str,
    product_type: str,
    bank_name: str | None = None,
    normalized_homepage_url: str | None = None,
) -> list[dict[str, Any]]:
    product_type = _canonical_product_type_code(product_type)
    seed_bank_codes = set(
        _seed_bank_codes_for_scope(
            bank_code=bank_code,
            bank_name=bank_name,
            normalized_homepage_url=normalized_homepage_url,
        )
    )
    hints: list[dict[str, Any]] = []
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) in seed_bank_codes
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) == "detail"
        ):
            exact_bank_code_match = str(item["bank_code"]) == bank_code
            hints.append(
                {
                    "source_id": str(item["source_id"]) if exact_bank_code_match else "",
                    "seed_source_id": str(item["source_id"]),
                    "seed_bank_code": str(item["bank_code"]),
                    "source_name": str(item.get("source_name") or item.get("purpose") or item["source_id"]),
                    "source_url": str(item["source_url"]),
                    "normalized_url": str(item["normalized_url"]),
                    "expected_fields": list(item.get("expected_fields") or []),
                    "purpose": str(item.get("purpose") or ""),
                    "priority": str(item.get("priority") or "P1"),
                }
            )
    return hints


def _load_seed_supporting_hints(
    *,
    bank_code: str,
    product_type: str,
    bank_name: str | None = None,
    normalized_homepage_url: str | None = None,
) -> list[dict[str, Any]]:
    product_type = _canonical_product_type_code(product_type)
    seed_bank_codes = set(
        _seed_bank_codes_for_scope(
            bank_code=bank_code,
            bank_name=bank_name,
            normalized_homepage_url=normalized_homepage_url,
        )
    )
    hints: list[dict[str, Any]] = []
    for item in load_seed_source_registry_rows():
        if (
            str(item["bank_code"]) in seed_bank_codes
            and str(item["product_type"]) == product_type
            and str(item["discovery_role"]) in {"supporting_html", "supporting_pdf", "linked_pdf"}
        ):
            exact_bank_code_match = str(item["bank_code"]) == bank_code
            hints.append(
                {
                    "source_id": str(item["source_id"]) if exact_bank_code_match else "",
                    "seed_source_id": str(item["source_id"]),
                    "seed_bank_code": str(item["bank_code"]),
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


def _seed_bank_codes_for_scope(*, bank_code: str, bank_name: str | None = None, normalized_homepage_url: str | None = None) -> list[str]:
    codes = [bank_code]
    seed_code = _seed_bank_code_for_bank_profile(bank_name=bank_name or bank_code, normalized_homepage_url=normalized_homepage_url)
    if seed_code and seed_code not in codes:
        codes.append(seed_code)
    return codes


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
    allowed_domains: tuple[str, ...] | None = None,
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
            ai_unavailable=True,
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
    model_id = os.getenv("FPDS_LLM_MODEL", "gpt-5.6-luna").strip() or "gpt-5.6-luna"
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
                    "expected_fields": _product_type_expected_fields(
                        product_type_definition,
                        country_code=country_code,
                    ),
                    "fallback_policy": str(product_type_definition.get("fallback_policy") or "generic_ai_review"),
                },
                "source_language": source_language,
                "homepage_url": homepage_url,
                "normalized_homepage_url": normalized_homepage_url,
                "homepage_fetch_error": homepage_fetch_error,
                "allowed_domains": list(allowed_domains or ()),
                "candidate_links": candidate_links,
            },
        )
    except Exception as exc:
        completed_at = datetime.now(UTC)
        model_execution_record = None
        if run_id:
            model_execution_record = _build_source_catalog_ai_model_execution_record(
                run_id=run_id,
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
                discovery_product_type=discovery_product_type or product_type,
                source_language=source_language,
                homepage_url=homepage_url,
                normalized_homepage_url=normalized_homepage_url,
                homepage_fetch_error=homepage_fetch_error,
                candidate_link_count=len(candidate_links),
                scored_candidate_count=0,
                correlation_id=correlation_id,
                request_id=request_id,
                model_id=model_id,
                execution_status="failed",
                started_at=started_at,
                completed_at=completed_at,
                error_summary=str(exc),
                fallback_mode="deterministic",
            )
        return AiParallelScoringResult(
            scores={},
            notes=[f"AI parallel scorer was unavailable: {exc}", "Deterministic homepage discovery fallback will evaluate bounded candidates."],
            model_execution_record=model_execution_record,
            ai_unavailable=True,
        )
    completed_at = datetime.now(UTC)

    notes = [str(resolution.get("summary") or "").strip()] if str(resolution.get("summary") or "").strip() else []
    hostname = urlparse(normalized_homepage_url).hostname or ""
    bounded_allowed_domains = allowed_domains or _discovery_allowed_domains(hostname)
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
        if not host_matches_allowed_domains(parsed_hostname, bounded_allowed_domains):
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
        model_execution_record = _build_source_catalog_ai_model_execution_record(
            run_id=run_id,
            bank_code=bank_code,
            country_code=country_code,
            product_type=product_type,
            discovery_product_type=discovery_product_type or product_type,
            source_language=source_language,
            homepage_url=homepage_url,
            normalized_homepage_url=normalized_homepage_url,
            homepage_fetch_error=homepage_fetch_error,
            candidate_link_count=len(candidate_links),
            scored_candidate_count=len(scores),
            correlation_id=correlation_id,
            request_id=request_id,
            model_id=str(usage.get("model_id") or model_id),
            execution_status="completed",
            started_at=started_at,
            completed_at=completed_at,
            candidate_scores=[
                {
                    "candidate_url": score.candidate_url,
                    "predicted_role": score.predicted_role,
                    "relevance_score": score.relevance_score,
                    "confidence_band": score.confidence_band,
                    "reason_codes": score.reason_codes,
                }
                for score in scores.values()
            ],
        )
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
            "You score bounded bank candidate URLs for homepage-first product discovery in the supplied country. "
            "Do not invent URLs. Score only the candidate links provided. "
            "Return whether each candidate is likely an official public detail page, a supporting page, or irrelevant for the given product type. "
            "Use a relevance_score from 0 to 10. A detail page must describe one named financial product; category lists, rates or fee tables, calculators, "
            "educational articles, guides, resource centres, and banking-service pages such as transfers or debit-card instructions are supporting pages, "
            "not product detail pages."
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
                                    "relevance_score": {"type": "number", "minimum": 0, "maximum": 10},
                                    "confidence_band": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "reason_codes": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "product_type_semantic_match",
                                                "detail_page_layout_signal",
                                                "pricing_or_feature_signal",
                                                "hub_page_not_detail",
                                                "supporting_terms_or_rates_page",
                                                "promo_or_apply_flow",
                                                "insufficient_evidence",
                                                "seed_hint_alignment",
                                                "not_product_detail"
                                            ]
                                        },
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
    ai_unavailable: bool = False,
    page_evidence_by_url: dict[str, PageEvidenceAssessment] | None = None,
    page_html_by_url: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    product_type_label = _product_type_label(product_type_definition)
    expected_fields = _product_type_expected_fields(
        product_type_definition,
        country_code=country_code,
    )
    notes: list[str] = []
    detail_rows: list[dict[str, Any]] = []
    promoted_count = 0
    rejected_detail_urls: list[str] = []
    seed_fetch_fallback_count = 0
    seed_low_evidence_fallback_count = 0
    evaluated = 0
    rejection_counts: Counter[str] = Counter()
    rejection_diagnostics: list[str] = []
    for candidate in _ordered_detail_candidates(candidates=candidates, ai_scores=ai_scores):
        if _url_locale_conflicts_source_language(
            normalized_url=candidate.normalized_url,
            source_language=source_language,
        ):
            rejected_detail_urls.append(candidate.normalized_url)
            rejection_counts["source_language_mismatch"] += 1
            continue
        ai_score = ai_scores.get(candidate.normalized_url)
        if (
            ai_score
            and ai_score.predicted_role == "irrelevant"
            and not _candidate_is_seed_backed(candidate)
            and candidate.heuristic_score <= 0
        ):
            rejected_detail_urls.append(candidate.normalized_url)
            rejection_counts["ai_irrelevant"] += 1
            continue
        if not _candidate_is_seed_backed(candidate) and candidate.heuristic_score <= 0 and (ai_score is None or ai_score.predicted_role != "detail"):
            rejected_detail_urls.append(candidate.normalized_url)
            rejection_counts["insufficient_candidate_signal"] += 1
            continue
        evaluated += 1
        page_evidence_kwargs: dict[str, Any] = {
            "raw_url": candidate.raw_url,
            "fetch_policy": fetch_policy,
            "product_type": discovery_product_type,
            "product_type_definition": product_type_definition,
        }
        if page_html_by_url is not None:
            page_evidence_kwargs["page_html_by_url"] = page_html_by_url
        page_evidence = _score_page_evidence(
            **page_evidence_kwargs,
        )
        if page_evidence_by_url is not None:
            page_evidence_by_url[candidate.normalized_url] = page_evidence
        if page_evidence.fetch_error:
            notes.append(f"Page evidence was unavailable for {candidate.normalized_url}: {page_evidence.fetch_error}")
            if _page_fetch_error_is_structural_access_challenge(page_evidence.fetch_error):
                rejected_detail_urls.append(candidate.normalized_url)
                rejection_counts["access_challenge_persisted"] += 1
                if len(rejection_diagnostics) < 8:
                    rejection_diagnostics.append(
                        "Rejected detail "
                        f"{candidate.normalized_url}: reason=access_challenge_persisted; "
                        f"page_error={_collapse_whitespace(page_evidence.fetch_error)[:500]}."
                    )
                continue
            if not _candidate_is_seed_backed(candidate):
                rejection_counts["page_fetch_unavailable"] += 1
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
                "ai_unavailable": ai_unavailable,
            }
            seed_fetch_fallback_count += 1
        else:
            verified_coverage_review_source = _verified_coverage_page_requires_review(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=page_evidence,
            )
            if not _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=page_evidence,
                ai_unavailable=ai_unavailable,
                allow_family_overview=discovery_product_type in {"chequing", "savings", "gic"},
                allow_verified_coverage_review_source=True,
            ):
                if (
                    not _candidate_is_seed_backed(candidate)
                    or (ai_unavailable and _seed_detail_has_hard_negative(page_evidence))
                    or (_seed_detail_has_hard_negative(page_evidence) and not ai_unavailable)
                ):
                    if not _candidate_is_seed_backed(candidate):
                        rejected_detail_urls.append(candidate.normalized_url)
                    rejection_reason = _detail_rejection_reason(ai_score=ai_score, page_evidence=page_evidence)
                    rejection_counts[rejection_reason] += 1
                    if len(rejection_diagnostics) < 8:
                        rejection_diagnostics.append(
                            "Rejected detail "
                            f"{candidate.normalized_url}: reason={rejection_reason}; "
                            f"ai={ai_score.predicted_role if ai_score else 'missing'}/"
                            f"{ai_score.relevance_score if ai_score else 'n/a'}; "
                            f"page_score={page_evidence.page_evidence_score}; "
                            f"title={page_evidence.page_title or 'missing'}; "
                            f"h1={page_evidence.primary_heading or 'missing'}; "
                            f"page_reasons={','.join(page_evidence.page_evidence_reason_codes)}."
                        )
                    continue
                metadata = _build_detail_discovery_metadata(
                    candidate=candidate,
                    ai_score=ai_score,
                    page_evidence=page_evidence,
                    ai_unavailable=ai_unavailable,
                    verified_coverage_review_source=verified_coverage_review_source,
                )
                metadata["selection_path"] = "seed_hint_ai_unavailable_low_page_evidence" if ai_unavailable else "seed_hint_low_page_evidence"
                metadata["selection_confidence"] = "medium-low"
                metadata["selection_reason_codes"] = _dedupe_preserve_order(
                    [
                        *list(metadata.get("selection_reason_codes") or []),
                        "seed_hint_alignment",
                        "page_evidence_below_threshold",
                        "ai_unavailable_deterministic_fallback" if ai_unavailable else "",
                    ]
                )
                seed_low_evidence_fallback_count += 1
            else:
                metadata = _build_detail_discovery_metadata(
                    candidate=candidate,
                    ai_score=ai_score,
                    page_evidence=page_evidence,
                    ai_unavailable=ai_unavailable,
                    verified_coverage_review_source=verified_coverage_review_source,
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
            expected_fields=list(
                collection_fields_for_product_type(
                    product_type=product_type,
                    country_code=country_code,
                    expected_fields=[*candidate.expected_fields_hint, *expected_fields],
                )
            ),
            discovery_metadata=metadata,
        )
        if candidate.seed_source_id:
            row["source_id"] = candidate.seed_source_id
        detail_rows.append(row)
        promoted_count += 1
    detail_rows, duplicate_detail_urls = _dedupe_detail_rows_by_product_identity(detail_rows)
    if duplicate_detail_urls:
        rejected_detail_urls.extend(duplicate_detail_urls)
        notes.append(
            f"Collapsed {len(duplicate_detail_urls)} same-product locale or host alias page(s) into canonical detail sources."
        )
    detail_rows, suppressed_family_urls = _suppress_family_overviews_when_named_details_exist(detail_rows)
    if suppressed_family_urls:
        notes.append(
            f"Kept {len(suppressed_family_urls)} multi-product family overview page(s) as supporting evidence because named detail pages were available."
        )
    promoted_count = len(detail_rows)
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
    if rejection_counts:
        notes.append(
            "Detail rejection summary: "
            + ", ".join(f"{reason}={count}" for reason, count in sorted(rejection_counts.items()))
            + "."
        )
    notes.extend(rejection_diagnostics)
    return (
        detail_rows,
        _dedupe_preserve_order(rejected_detail_urls),
        _dedupe_preserve_order([note for note in notes if note]),
    )


def _discover_detail_companion_links(
    *,
    detail_rows: list[dict[str, Any]],
    country_code: str,
    product_type: str,
    fetch_policy: DiscoveryFetchPolicy,
    hostname: str,
    allowed_domains: tuple[str, ...],
    page_html_by_url: dict[str, str],
) -> tuple[list[DetailCompanionLink], list[str]]:
    """Follow exact-product pricing/terms links from promoted detail pages.

    US card and deposit sites commonly keep the customer-visible product name
    on one page while placing the comparison-critical APR, fee table, or
    account guide behind a directly linked disclosure. The parent detail link
    is the bounded product relationship; unrelated site-wide legal links do
    not satisfy the pricing marker policy below.
    """

    candidates: list[DetailCompanionLink] = []
    unavailable_detail_count = 0
    for detail_row in detail_rows:
        parent_normalized_url = str(detail_row.get("normalized_url") or "")
        parent_raw_url = str(detail_row.get("raw_url") or parent_normalized_url)
        html_text = page_html_by_url.get(parent_normalized_url)
        if html_text is None:
            try:
                html_text = fetch_text(parent_raw_url, fetch_policy)
            except Exception:
                unavailable_detail_count += 1
                continue
            page_html_by_url[parent_normalized_url] = html_text

        per_detail: list[DetailCompanionLink] = []
        for link in _extract_allowed_links(
            html_text=html_text,
            base_url=parent_raw_url,
            hostname=hostname,
            allowed_domains=allowed_domains,
        ):
            if link.normalized_url == parent_normalized_url:
                continue
            if _url_country_scope_conflicts(country_code=country_code, normalized_url=link.normalized_url):
                continue
            score = _detail_companion_link_score(
                product_type=product_type,
                normalized_url=link.normalized_url,
                anchor_text=link.anchor_text,
            )
            if score <= 0:
                continue
            per_detail.append(
                DetailCompanionLink(
                    link=link,
                    parent_detail_url=parent_normalized_url,
                    score=score,
                )
            )
        per_detail.sort(key=lambda item: (-item.score, item.link.normalized_url))
        candidates.extend(per_detail[:_DISCOVERY_DETAIL_COMPANION_PER_DETAIL_MAX])

    by_url: dict[str, DetailCompanionLink] = {}
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.link.normalized_url)):
        by_url.setdefault(candidate.link.normalized_url, candidate)
        if len(by_url) >= _DISCOVERY_DETAIL_COMPANION_MAX:
            break

    notes: list[str] = []
    if by_url:
        notes.append(
            f"Preserved {len(by_url)} exact-product pricing, fee, or terms companion source(s) linked from selected detail pages."
        )
    if unavailable_detail_count:
        notes.append(
            f"Could not inspect {unavailable_detail_count} selected detail page(s) for linked pricing or terms companions."
        )
    return list(by_url.values()), notes


def _is_non_product_supporting_document(
    *,
    product_type: str,
    normalized_url: str,
    anchor_text: str = "",
) -> bool:
    parsed = urlparse(normalized_url)
    path = parsed.path.lower()
    if any(
        marker in path
        for marker in (
            "/about/misc/user-agreement",
            "/user-agreement",
            "/user_agreement",
            "/website-terms",
        )
    ):
        return True

    canonical_type = _canonical_product_type_code(product_type)
    if canonical_type not in {"chequing", "savings", "gic"}:
        return False
    investment_path = any(
        marker in path
        for marker in ("/wealth/", "/invest/", "/investment/", "/investments/")
    )
    if not investment_path:
        return False
    fingerprint = f"{path} {_collapse_whitespace(anchor_text).lower()}"
    document_marker = any(
        marker in fingerprint
        for marker in ("disclosure", "prospectus", "fund-fact", "fund_fact")
    )
    deposit_context = any(
        marker in fingerprint
        for marker in (
            "account-guide",
            "chequing",
            "checking",
            "deposit-account",
            "fee-schedule",
            "gic",
            "interest-rate",
            "savings",
            "term-deposit",
        )
    )
    return document_marker and not deposit_context


def _detail_companion_link_score(*, product_type: str, normalized_url: str, anchor_text: str) -> int:
    parsed = urlparse(normalized_url)
    hostname = str(parsed.hostname or "").lower()
    if not hostname or hostname.startswith(("help.", "support.")):
        return 0
    anchor = _collapse_whitespace(anchor_text).lower()
    normalized_anchor = anchor.strip(" .:-|")
    if normalized_anchor in {"apply", "apply now", "login", "log in", "open account", "sign in"}:
        return 0
    path_and_query = " ".join(part for part in (parsed.path.lower(), parsed.query.lower()) if part)
    fingerprint = f"{path_and_query} {anchor}".strip()
    if any(marker in fingerprint for marker in _DETAIL_COMPANION_EXCLUDED_MARKERS):
        return 0
    if _is_non_product_supporting_document(
        product_type=product_type,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    ):
        return 0
    if _has_unrelated_product_type_signal(product_type=product_type, fingerprint=fingerprint):
        return 0

    anchor_hits = sum(marker in anchor for marker in _DETAIL_COMPANION_ANCHOR_MARKERS)
    url_hits = sum(marker in path_and_query for marker in _DETAIL_COMPANION_URL_MARKERS)
    if not anchor_hits and not url_hits:
        return 0
    score = anchor_hits * 5 + url_hits * 3
    if parsed.query:
        score += 2
    if infer_source_type(normalized_url) == "pdf" or "pdf" in anchor or "pdf" in parsed.path.lower():
        score += 2
    return score


def _supporting_html_page_is_fetchable(
    *,
    normalized_url: str,
    raw_url: str,
    fetch_policy: DiscoveryFetchPolicy,
    product_type: str,
    product_type_definition: dict[str, Any],
    page_evidence_by_url: dict[str, PageEvidenceAssessment],
) -> bool:
    page_evidence = page_evidence_by_url.get(normalized_url)
    if page_evidence is None:
        page_evidence = _score_page_evidence(
            raw_url=raw_url,
            fetch_policy=fetch_policy,
            product_type=product_type,
            product_type_definition=product_type_definition,
        )
        page_evidence_by_url[normalized_url] = page_evidence
    return not page_evidence.fetch_error


def _detail_rejection_reason(
    *,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> str:
    reason_codes = set(page_evidence.page_evidence_reason_codes)
    for reason in (
        "multi_product_family_overview",
        "non_consumer_business_page",
        "registered_plan_wrapper",
        "other_product_type",
        "non_product_or_investor_page",
        "non_product_editorial_page",
        "non_product_service_flow",
    ):
        if reason in reason_codes:
            return reason
    if page_evidence.page_evidence_score < _PAGE_EVIDENCE_MINIMUM_SCORE:
        return "page_evidence_below_threshold"
    if ai_score is None:
        return "ai_score_missing"
    if ai_score.predicted_role != "detail":
        return f"ai_role_{ai_score.predicted_role}"
    if ai_score.relevance_score < 4.0:
        return "ai_relevance_below_threshold"
    return "detail_policy_not_met"


def _dedupe_detail_rows_by_product_identity(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    unkeyed: list[dict[str, Any]] = []
    duplicate_urls: list[str] = []
    for row in rows:
        metadata = row.get("discovery_metadata") if isinstance(row.get("discovery_metadata"), dict) else {}
        page_title = " ".join(str(metadata.get("page_title") or "").lower().split())
        primary_heading = " ".join(str(metadata.get("primary_heading") or "").lower().split())
        identity_tokens = set(re.findall(r"[a-z0-9]+", f"{page_title} {primary_heading}"))
        generic_identity_tokens = {
            "account",
            "accounts",
            "bank",
            "banking",
            "card",
            "cards",
            "credit",
            "chequing",
            "checking",
            "savings",
            "saving",
            "gic",
            "gics",
            "mortgage",
            "mortgages",
            "loan",
            "loans",
            "line",
            "of",
            "personal",
            "product",
            "products",
            "service",
            "services",
            "offer",
            "offers",
            "the",
            *re.findall(r"[a-z0-9]+", str(row.get("bank_code") or "").lower()),
            *re.findall(r"[a-z0-9]+", str(row.get("product_type") or "").lower()),
        }
        distinctive_returned_identity = bool(identity_tokens - generic_identity_tokens)
        strong_returned_identity = bool(
            page_title
            and primary_heading
            and distinctive_returned_identity
            and int(metadata.get("attribute_signal_count") or 0) >= 2
            and int(metadata.get("negative_signal_count") or 0) == 0
            and not {
                "multi_product_family_overview",
                "non_product_or_investor_page",
                "non_product_editorial_page",
                "non_product_service_flow",
            }.intersection(_coerce_reason_codes(metadata.get("page_evidence_reason_codes") or []))
        )
        if (not metadata.get("product_identity_match") and not strong_returned_identity) or not page_title or not primary_heading:
            unkeyed.append(row)
            continue
        identity = (str(row["bank_code"]), str(row["product_type"]), page_title, primary_heading)
        current = by_identity.get(identity)
        if current is None:
            by_identity[identity] = row
            continue
        preferred, duplicate = sorted((current, row), key=_generated_source_row_sort_key)
        alias_urls = list(
            dict.fromkeys(
                [
                    *list(preferred.get("alias_urls") or []),
                    str(duplicate.get("source_url") or ""),
                    str(duplicate.get("normalized_url") or ""),
                ]
            )
        )
        preferred["alias_urls"] = [url for url in alias_urls if url and url != preferred.get("normalized_url")]
        by_identity[identity] = preferred
        duplicate_urls.append(str(duplicate["normalized_url"]))
    return [*by_identity.values(), *unkeyed], _dedupe_preserve_order(duplicate_urls)


def _suppress_family_overviews_when_named_details_exist(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    def is_verified_vancity_gic_seed_detail(row: dict[str, Any], metadata: dict[str, Any]) -> bool:
        return (
            str(row.get("bank_code") or "").upper() == "VANCITY"
            and str(row.get("product_type") or "").lower() == "gic"
            and metadata.get("candidate_origin") == "seed_detail_hint"
            and metadata.get("product_identity_match") is True
            and int(metadata.get("page_evidence_score") or 0) >= 7
            and int(metadata.get("negative_signal_count") or 0) == 0
        )

    def is_family_overview(row: dict[str, Any]) -> bool:
        metadata = row.get("discovery_metadata") if isinstance(row.get("discovery_metadata"), dict) else {}
        page_reasons = _coerce_reason_codes(metadata.get("page_evidence_reason_codes") or [])
        ai_reasons = _coerce_reason_codes(metadata.get("ai_reason_codes") or [])
        if "multi_product_family_overview" in page_reasons and is_verified_vancity_gic_seed_detail(row, metadata):
            # Named official product pages often end with an "Explore other
            # products" cross-sell section. The generic overview detector sees
            # those sibling headings, but a curated detail hint with strong
            # identity evidence remains a product page rather than a hub.
            return False
        return "multi_product_family_overview" in page_reasons or (
            metadata.get("ai_predicted_role") == "supporting_html"
            and "hub_page_not_detail" in ai_reasons
        )

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.get("discovery_metadata") if isinstance(row.get("discovery_metadata"), dict) else {}
        page_reasons = _coerce_reason_codes(metadata.get("page_evidence_reason_codes") or [])
        if (
            "multi_product_family_overview" not in page_reasons
            or not is_verified_vancity_gic_seed_detail(row, metadata)
        ):
            normalized_rows.append(row)
            continue
        normalized_metadata = dict(metadata)
        for reason_key in ("selection_reason_codes", "page_evidence_reason_codes"):
            normalized_metadata[reason_key] = [
                code
                for code in _coerce_reason_codes(metadata.get(reason_key) or [])
                if code != "multi_product_family_overview"
            ]
        normalized_row = dict(row)
        normalized_row["discovery_metadata"] = normalized_metadata
        normalized_rows.append(normalized_row)

    named_rows = [row for row in normalized_rows if not is_family_overview(row)]
    if not named_rows:
        return normalized_rows, []
    family_rows = [row for row in normalized_rows if is_family_overview(row)]
    return named_rows, [str(row.get("normalized_url") or "") for row in family_rows if row.get("normalized_url")]


def _ordered_detail_candidates(*, candidates: list[HomepageCandidate], ai_scores: dict[str, AiParallelCandidateScore]) -> list[HomepageCandidate]:
    ranked = sorted(candidates, key=lambda item: (-_candidate_combined_score(item, ai_scores), item.normalized_url))
    seed_candidates = [item for item in ranked if _candidate_is_seed_backed(item)]
    non_seed_candidates = [item for item in ranked if not _candidate_is_seed_backed(item)]
    if seed_candidates:
        return [*seed_candidates, *non_seed_candidates[:_PAGE_EVIDENCE_MAX_CANDIDATES]]
    return non_seed_candidates[:_PAGE_EVIDENCE_MAX_CANDIDATES]


def _candidate_combined_score(candidate: HomepageCandidate, ai_scores: dict[str, AiParallelCandidateScore]) -> float:
    ai_score = ai_scores.get(candidate.normalized_url)
    total = float(candidate.heuristic_score * 2)
    if ai_score is None:
        return total
    role_bonus = {"detail": 2.0, "supporting_html": -1.0, "irrelevant": -3.0}.get(ai_score.predicted_role, 0.0)
    return total + ai_score.relevance_score + role_bonus


def _candidate_is_seed_backed(candidate: HomepageCandidate) -> bool:
    return bool(candidate.seed_source_id) or candidate.origin == "seed_detail_hint"


def _page_fetch_error_is_structural_access_challenge(error_summary: str) -> bool:
    return "html access challenge remained after bounded browser fallback" in error_summary.strip().lower()


def _candidate_promotes_to_detail(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
    ai_unavailable: bool = False,
    allow_family_overview: bool = False,
    allow_verified_coverage_review_source: bool = False,
    allow_verified_lending_review_source: bool = False,
) -> bool:
    if _page_is_audience_offer_hub(page_evidence):
        return False
    if "non_product_service_flow" in page_evidence.page_evidence_reason_codes:
        return False
    verified_coverage_review_source = (
        (allow_verified_coverage_review_source or allow_verified_lending_review_source)
        and _verified_coverage_page_requires_review(
            candidate=candidate,
            ai_score=ai_score,
            page_evidence=page_evidence,
        )
    )
    if (
        "multi_product_family_overview" in page_evidence.page_evidence_reason_codes
        and not allow_family_overview
        and not verified_coverage_review_source
    ):
        specific_singular_identity = _page_has_specific_singular_product_identity(page_evidence)
        named_detail_override = specific_singular_identity and (
            (
                ai_score is not None
                and ai_score.predicted_role == "detail"
                and ai_score.relevance_score >= 8.0
                and ai_score.confidence_band == "high"
            )
            or _candidate_has_confirmed_product_identity(
                ai_score=ai_score,
                page_evidence=page_evidence,
            )
            or _strong_named_page_overrides_ai_irrelevant(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=page_evidence,
            )
        )
        if not named_detail_override:
            return False
    if _location_gated_structured_page_can_be_detail(
        candidate=candidate,
        ai_score=ai_score,
        page_evidence=page_evidence,
    ):
        return True
    if allow_family_overview and _deposit_family_overview_can_be_detail(
        candidate=candidate,
        ai_score=ai_score,
        page_evidence=page_evidence,
    ):
        return True
    if verified_coverage_review_source:
        return True
    if page_evidence.page_evidence_score < _PAGE_EVIDENCE_MINIMUM_SCORE:
        return _high_confidence_detail_overrides_low_page_score(
            candidate=candidate,
            ai_score=ai_score,
            page_evidence=page_evidence,
        )
    strong_page_detail_signal = _candidate_has_strong_page_detail_signal(candidate=candidate, page_evidence=page_evidence)
    if _candidate_is_seed_backed(candidate):
        return True
    confirmed_product_identity = _candidate_has_confirmed_product_identity(
        ai_score=ai_score,
        page_evidence=page_evidence,
    )
    if page_evidence.negative_signal_count >= 2 and not confirmed_product_identity:
        return False
    if candidate.supporting_signal and (ai_score is None or ai_score.predicted_role != "detail") and not strong_page_detail_signal:
        return False
    if ai_score is not None:
        if _strong_named_page_overrides_ai_irrelevant(
            candidate=candidate,
            ai_score=ai_score,
            page_evidence=page_evidence,
        ):
            return True
        if ai_score.predicted_role == "supporting_html" and strong_page_detail_signal:
            return _ai_supporting_override_allowed(ai_score)
        if ai_score.predicted_role != "detail":
            return False
        return ai_score.relevance_score >= 4.0 or strong_page_detail_signal
    if ai_unavailable:
        return (
            candidate.heuristic_score > 0
            and page_evidence.page_evidence_score >= 6
            and page_evidence.attribute_signal_count >= 2
            and page_evidence.negative_signal_count == 0
        )
    return candidate.heuristic_score > 0 or strong_page_detail_signal


def _verified_coverage_page_requires_review(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    page_reasons = set(page_evidence.page_evidence_reason_codes)
    strong_verified_family_overview = (
        "multi_product_family_overview" in page_reasons
        and page_evidence.page_evidence_score >= 7
        and page_evidence.product_identity_match
        and page_evidence.negative_signal_count == 0
        and ai_score is not None
        and ai_score.predicted_role in {"detail", "supporting_html"}
        and ai_score.relevance_score >= 8.0
        and ai_score.confidence_band != "low"
    )
    requires_bounded_exception = (
        page_evidence.page_evidence_score < _PAGE_EVIDENCE_MINIMUM_SCORE
        or "multi_product_family_overview" in page_reasons
    )
    if (
        candidate.origin != "verified_coverage_source"
        or not requires_bounded_exception
        or candidate.heuristic_score <= 0
        or ai_score is None
        or ai_score.predicted_role not in {"detail", "supporting_html"}
        or (
            ai_score.relevance_score < 8.5
            and not strong_verified_family_overview
        )
        or ai_score.confidence_band == "low"
        or page_evidence.page_evidence_score < 3
        or page_evidence.attribute_signal_count < 1
        or page_evidence.negative_signal_count > 1
        or "product_type_semantic_match" not in page_reasons
        or "pricing_or_feature_signal" not in page_reasons
    ):
        return False
    veto_page_reasons = {
        "non_consumer_business_page",
        "non_product_editorial_page",
        "non_product_service_flow",
        "other_product_type",
        "promo_or_apply_flow",
        "supporting_terms_or_rates_page",
    }
    if page_reasons.intersection(veto_page_reasons):
        return False
    ai_reasons = set(_coerce_reason_codes(ai_score.reason_codes))
    return not ai_reasons.intersection(
        {
            "insufficient_evidence",
            "non_product_editorial_page",
            "non_product_service_flow",
            "not_product_detail",
            "other_product_type",
            "promo_or_apply_flow",
            "supporting_terms_or_rates_page",
        }
    )


def _location_gated_structured_page_can_be_detail(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    page_reasons = set(page_evidence.page_evidence_reason_codes)
    verified_coverage_source = candidate.origin == "verified_coverage_source"
    verified_coverage_evidence_sufficient = (
        verified_coverage_source
        and ai_score is not None
        and (
            (
                ai_score.predicted_role == "detail"
                and ai_score.relevance_score >= 8.0
                and ai_score.confidence_band == "high"
                and page_evidence.page_evidence_score >= 1
                and page_evidence.attribute_signal_count >= 1
                and page_evidence.negative_signal_count <= 2
            )
            or (
                ai_score.predicted_role == "supporting_html"
                and ai_score.relevance_score >= 8.0
                and ai_score.confidence_band != "low"
                and page_evidence.page_evidence_score >= 4
                and page_evidence.attribute_signal_count >= 2
                and page_evidence.negative_signal_count <= 1
            )
        )
    )
    if (
        ai_score is None
        or ai_score.predicted_role not in {"detail", "supporting_html"}
        or ai_score.relevance_score < 6.0
        or ai_score.confidence_band == "low"
        or candidate.heuristic_score <= 0
        or (
            not verified_coverage_evidence_sufficient
            and (
                page_evidence.page_evidence_score < 5
                or page_evidence.attribute_signal_count < 2
            )
        )
        or not page_evidence.product_identity_match
        or "title_semantic_match" not in page_reasons
        or "location_access_gate" not in page_reasons
        or "structured_component_evidence" not in page_reasons
        or "multi_product_family_overview" in page_reasons
    ):
        return False
    ai_reasons = set(_coerce_reason_codes(ai_score.reason_codes))
    return not ai_reasons.intersection(
        {
            "non_product_editorial_page",
            "non_product_service_flow",
            "promo_or_apply_flow",
            "supporting_terms_or_rates_page",
        }
    )


def _page_has_specific_singular_product_identity(page_evidence: PageEvidenceAssessment) -> bool:
    heading = _collapse_whitespace(str(page_evidence.primary_heading or "")).lower()
    title = _collapse_whitespace(str(page_evidence.page_title or "").split("|", 1)[0]).lower()
    if not heading or not title:
        return False
    generic_plural_markers = (
        "chequing accounts", "checking accounts", "savings accounts", "gics", "term deposits",
        "credit cards", "mortgages", "personal loans", "lines of credit", "mortgage products",
    )
    if any(marker in heading for marker in generic_plural_markers):
        return False
    if heading in title or title in heading:
        return True
    ignored_tokens = {
        "american", "amex", "bank", "canada", "card", "cards", "credit", "express",
        "for", "mastercard", "scotia", "scotiabank", "student", "students", "the", "visa",
    }
    heading_tokens = set(re.findall(r"[a-z0-9]+", heading)) - ignored_tokens
    title_tokens = set(re.findall(r"[a-z0-9]+", title)) - ignored_tokens
    shared_tokens = heading_tokens.intersection(title_tokens)
    return bool(shared_tokens) and len(shared_tokens) >= max(1, min(len(heading_tokens), len(title_tokens)) - 1)


def _deposit_family_overview_can_be_detail(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    if (
        ai_score is None
        or ai_score.predicted_role != "supporting_html"
        or ai_score.relevance_score < 7.0
        or ai_score.confidence_band == "low"
        or candidate.heuristic_score <= 0
        or page_evidence.negative_signal_count > 0
        or not page_evidence.product_identity_match
        or not {
            "title_semantic_match",
            "url_product_identity_signal",
        }.intersection(page_evidence.page_evidence_reason_codes)
        or page_evidence.page_evidence_score < 4
        or "structured_component_evidence" not in page_evidence.page_evidence_reason_codes
        or "product_type_semantic_match" not in page_evidence.page_evidence_reason_codes
        or "pricing_or_feature_signal" not in page_evidence.page_evidence_reason_codes
    ):
        return False
    ai_reasons = set(_coerce_reason_codes(ai_score.reason_codes))
    if "hub_page_not_detail" not in ai_reasons:
        return False
    return not any(
        reason in ai_reasons
        for reason in (
            "not_product_detail",
            "supporting_terms_or_rates_page",
            "non_product_editorial_page",
            "non_product_service_flow",
            "promo_or_apply_flow",
            "insufficient_evidence",
        )
    )


def _high_confidence_detail_overrides_low_page_score(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    if (
        ai_score is None
        or ai_score.predicted_role != "detail"
        or ai_score.relevance_score < 8.0
        or ai_score.confidence_band != "high"
        or candidate.heuristic_score <= 0
    ):
        return False
    reason_codes = {
        *page_evidence.page_evidence_reason_codes,
        *_coerce_reason_codes(ai_score.reason_codes),
    }
    if any(
        code in reason_codes
        for code in (
            "registered_plan_wrapper",
            "other_product_type",
            "non_product_or_investor_page",
            "non_product_editorial_page",
            "non_product_service_flow",
            "non_consumer_business_page",
            "promo_or_apply_flow",
            "not_product_detail",
            "supporting_terms_or_rates_page",
        )
    ):
        return False
    named_title_and_heading = _page_has_specific_singular_product_identity(page_evidence)
    structured_product_route = (
        ai_score.relevance_score >= 9.0
        and page_evidence.product_identity_match
        and "title_semantic_match" in reason_codes
        and "structured_component_evidence" in reason_codes
        and page_evidence.page_evidence_score >= 3
        and page_evidence.negative_signal_count == 0
    )
    return (
        (
            page_evidence.product_identity_match
            and (page_evidence.heading_match or "title_semantic_match" in reason_codes)
            and page_evidence.page_evidence_score >= 2
            and page_evidence.attribute_signal_count >= 2
        )
        or (
            named_title_and_heading
            and "product_type_semantic_match" in reason_codes
            and (
                page_evidence.attribute_signal_count >= 1
                or (
                    ai_score.relevance_score >= 9.0
                    and page_evidence.negative_signal_count == 0
                    and _looks_like_credit_card_detail_path(
                        product_type="credit-card",
                        normalized_url=candidate.normalized_url,
                    )
                )
            )
        )
        or structured_product_route
    ) and page_evidence.negative_signal_count <= 2


def _candidate_has_confirmed_product_identity(
    *,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    if ai_score is None or ai_score.predicted_role != "detail" or ai_score.relevance_score < 4.0:
        return False
    reason_codes = set(page_evidence.page_evidence_reason_codes)
    if any(
        code in reason_codes
        for code in (
            "registered_plan_wrapper",
            "other_product_type",
            "non_product_or_investor_page",
            "non_product_editorial_page",
            "non_product_service_flow",
        )
    ):
        return False
    return (
        page_evidence.product_identity_match
        and (page_evidence.heading_match or "title_semantic_match" in reason_codes)
        and page_evidence.attribute_signal_count >= 1
    )


def _candidate_has_strong_page_detail_signal(*, candidate: HomepageCandidate, page_evidence: PageEvidenceAssessment) -> bool:
    candidate_fingerprint = f"{candidate.normalized_url} {candidate.anchor_text}".lower()
    if any(keyword in candidate_fingerprint for keyword in ("legal", "terms", "conditions", "agreement", "disclosure", "service-fee", "service fee")):
        return False
    if page_evidence.page_evidence_score < 7:
        return False
    if page_evidence.negative_signal_count > 0:
        return False
    if page_evidence.attribute_signal_count < 2:
        return False
    reason_codes = set(page_evidence.page_evidence_reason_codes)
    if "product_identity_signal" not in reason_codes:
        return False
    if not (page_evidence.heading_match or "title_semantic_match" in reason_codes):
        return False
    return candidate.heuristic_score > 0 or "product_type_semantic_match" in reason_codes


def _strong_named_page_overrides_ai_irrelevant(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
) -> bool:
    return (
        ai_score is not None
        and ai_score.predicted_role == "irrelevant"
        and _page_has_specific_singular_product_identity(page_evidence)
        and _candidate_has_strong_page_detail_signal(
            candidate=candidate,
            page_evidence=page_evidence,
        )
    )


def _ai_supporting_override_allowed(ai_score: AiParallelCandidateScore) -> bool:
    normalized_reason_codes = {str(item).strip().lower() for item in ai_score.reason_codes if str(item).strip()}
    has_veto = any(
        code in _AI_DETAIL_OVERRIDE_VETO_REASON_CODES
        or "not_product_detail" in code
        or code.startswith("supporting_")
        or code.endswith("_not_detail")
        for code in normalized_reason_codes
    )
    return ai_score.relevance_score >= 4.0 and ai_score.confidence_band != "low" and not has_veto


def _ai_supporting_source_is_relevant(ai_score: AiParallelCandidateScore) -> bool:
    reasons = set(_coerce_reason_codes(ai_score.reason_codes))
    if ai_score.predicted_role != "supporting_html" or ai_score.confidence_band == "low":
        return False
    if reasons.intersection({"not_product_detail", "non_product_editorial_page", "non_product_service_flow", "promo_or_apply_flow"}):
        return False
    if "insufficient_evidence" in reasons and ai_score.relevance_score < 4.0:
        return False
    return True


def _build_detail_discovery_metadata(
    *,
    candidate: HomepageCandidate,
    ai_score: AiParallelCandidateScore | None,
    page_evidence: PageEvidenceAssessment,
    ai_unavailable: bool = False,
    verified_coverage_review_source: bool = False,
    verified_coverage_lending_review_source: bool = False,
) -> dict[str, Any]:
    verified_coverage_review_source = (
        verified_coverage_review_source or verified_coverage_lending_review_source
    )
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
                (
                    "strong_page_evidence_detail_override"
                    if ai_score is not None
                    and ai_score.predicted_role == "supporting_html"
                    and _candidate_has_strong_page_detail_signal(candidate=candidate, page_evidence=page_evidence)
                    else ""
                ),
                (
                    "strong_named_page_ai_irrelevant_override"
                    if _strong_named_page_overrides_ai_irrelevant(
                        candidate=candidate,
                        ai_score=ai_score,
                        page_evidence=page_evidence,
                    )
                    else ""
                ),
                (
                    "high_confidence_structured_product_route"
                    if page_evidence.page_evidence_score < _PAGE_EVIDENCE_MINIMUM_SCORE
                    and _high_confidence_detail_overrides_low_page_score(
                        candidate=candidate,
                        ai_score=ai_score,
                        page_evidence=page_evidence,
                    )
                    else ""
                ),
                (
                    _VERIFIED_COVERAGE_REVIEW_REASON
                    if verified_coverage_review_source
                    else ""
                ),
            ]
        )
    )
    return {
        "selection_path": (
            _VERIFIED_COVERAGE_REVIEW_REASON
            if verified_coverage_review_source
            else _selection_path(candidate=candidate, ai_score=ai_score, ai_unavailable=ai_unavailable)
        ),
        "selection_confidence": "review" if verified_coverage_review_source else confidence,
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
        "product_identity_match": page_evidence.product_identity_match,
        "attribute_signal_count": page_evidence.attribute_signal_count,
        "negative_signal_count": page_evidence.negative_signal_count,
        "ai_unavailable": ai_unavailable,
    }


def _selection_path(*, candidate: HomepageCandidate, ai_score: AiParallelCandidateScore | None, ai_unavailable: bool = False) -> str:
    if ai_score is not None and _candidate_is_seed_backed(candidate):
        return "seed_hint_plus_ai_plus_page_evidence"
    if ai_score is not None:
        return "heuristic_plus_ai_plus_page_evidence"
    if ai_unavailable and _candidate_is_seed_backed(candidate):
        return "seed_hint_plus_page_evidence_ai_unavailable"
    if ai_unavailable:
        return "heuristic_plus_page_evidence_ai_unavailable"
    if _candidate_is_seed_backed(candidate):
        return "seed_hint_plus_page_evidence"
    return "heuristic_plus_page_evidence"


def _seed_detail_has_hard_negative(page_evidence: PageEvidenceAssessment) -> bool:
    if _page_is_audience_offer_hub(page_evidence):
        return True
    if page_evidence.negative_signal_count <= 0:
        return False
    fingerprint = " ".join(
        [
            str(page_evidence.page_title or ""),
            str(page_evidence.primary_heading or ""),
            " ".join(page_evidence.page_evidence_reason_codes),
        ]
    ).lower()
    return any(
        term in fingerprint
        for term in (
            "search tool",
            "compare",
            "comparison",
            "calculator",
            "selector",
            "login",
            "sign in",
            "registered_plan_wrapper",
            "other_product_type",
            "non_product_or_investor_page",
            "non_product_editorial_page",
            "non_product_service_flow",
        )
    )


def _url_locale_conflicts_source_language(*, normalized_url: str, source_language: str) -> bool:
    """Reject a clearly different locale host or path from an allowed domain."""

    requested = str(source_language or "").strip().lower().replace("_", "-").split("-", 1)[0]
    if not requested:
        return False
    known_languages = {"en", "fr", "es", "de", "it", "pt", "zh", "ja", "ko"}
    parsed = urlparse(normalized_url)
    hostname_labels = [item for item in str(parsed.hostname or "").lower().split(".") if item]
    if hostname_labels:
        host_locale = {"zt": "zh"}.get(hostname_labels[0], hostname_labels[0])
        if host_locale in known_languages and host_locale != requested:
            return True
    for segment in [item for item in parsed.path.lower().split("/") if item][:3]:
        locale = segment.replace("_", "-").split("-", 1)[0]
        if locale in known_languages:
            return locale != requested
    return False


def _url_country_scope_conflicts(*, country_code: str, normalized_url: str) -> bool:
    """Reject an explicit market route that conflicts with the collection country.

    Some banks serve Canada and the United States from one registered domain.
    Domain allowlisting therefore is not enough: `/ca/...` must never enter a
    US run and `/us/...` must never enter a Canada run. Unmarked shared legal or
    disclosure paths remain eligible as supporting evidence.
    """

    requested = str(country_code or "").strip().lower()
    if requested not in {"ca", "us"}:
        return False
    parsed = urlparse(str(normalized_url or ""))
    hostname = str(parsed.hostname or "").lower().strip(".")
    segments = [segment.lower().replace("_", "-") for segment in parsed.path.split("/") if segment]
    explicit_markets: set[str] = set()
    host_labels = [label for label in hostname.split(".") if label]
    if host_labels and host_labels[0] in {"ca", "us"}:
        explicit_markets.add(host_labels[0])
    if hostname.endswith(".ca"):
        explicit_markets.add("ca")
    if hostname.endswith(".us"):
        explicit_markets.add("us")
    for segment in segments[:3]:
        if segment in {"ca", "us"}:
            explicit_markets.add(segment)
        locale_match = re.fullmatch(r"[a-z]{2}-(ca|us)", segment)
        if locale_match:
            explicit_markets.add(locale_match.group(1))
    return bool(explicit_markets and requested not in explicit_markets)


def _page_is_audience_offer_hub(page_evidence: PageEvidenceAssessment) -> bool:
    """Identify audience benefits/offer hubs that mention accounts but are not one product."""

    heading = _collapse_whitespace(str(page_evidence.primary_heading or "")).lower().strip(" .:-|")
    title = _collapse_whitespace(str(page_evidence.page_title or "").split("|", 1)[0]).lower().strip(" .:-|")
    if any(
        marker in heading
        for marker in (
            "banking offers",
            "banking for foreign workers",
            "benefits on bank accounts",
            "bank account benefits",
        )
    ):
        return True
    return any(
        marker in title
        for marker in ("banking for foreign workers", "senior benefits on bank accounts")
    ) and not any(marker in heading for marker in (" chequing account", " checking account", " savings account"))


def _coerce_reason_codes(values: list[str]) -> list[str]:
    return [str(item) for item in values if str(item).strip()]


def _score_page_evidence(
    *,
    raw_url: str,
    fetch_policy: DiscoveryFetchPolicy,
    product_type: str,
    product_type_definition: dict[str, Any],
    page_html_by_url: dict[str, str] | None = None,
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

    if page_html_by_url is not None:
        page_html_by_url[normalize_source_url(raw_url)] = html_text

    parser = _PageSignalParser()
    parser.feed(html_text)
    title_text = parser.title_text
    primary_heading = parser.primary_heading
    heading_text = " ".join([primary_heading, *parser.secondary_headings]).strip()
    visible_body_text = " ".join(parser.body_chunks[:40]).strip()
    structured_sections = extract_structured_text_sections(html_text)
    structured_text = " ".join(structured_sections)
    body_text = " ".join([visible_body_text, structured_text]).strip()
    access_gate_detected = any(
        marker in f"{primary_heading} {visible_body_text}".lower()
        for marker in (
            "select your county",
            "select a location",
            "enter your zip code",
            "enter a zip code",
            "provide your zip code",
        )
    )
    identity_terms = _product_type_identity_keywords(product_type, product_type_definition)
    semantic_terms = _product_type_semantic_terms(product_type_definition)
    attribute_terms = _product_type_attribute_keywords(product_type, product_type_definition)
    title_match = _term_hits(title_text, identity_terms)
    if access_gate_detected and structured_sections and not title_match:
        title_match = _term_hits(
            title_text,
            list(_DISCOVERY_PROFILE_TERMS.get(_canonical_product_type_code(product_type), ())),
        )
    primary_heading_match = _term_hits(primary_heading, identity_terms)
    normalized_url_path = re.sub(r"[-_/]+", " ", unquote(urlparse(raw_url).path).lower())
    url_identity_match = _term_hits(normalized_url_path, identity_terms)
    body_match = _term_hits(body_text, semantic_terms)
    attribute_hits = _distinct_term_hits(" ".join([heading_text, body_text]), attribute_terms)
    # Global navigation and serialized application state routinely contain
    # Sign in, Compare, Legal, and Terms links on otherwise valid product
    # pages. Treat those words as negative only when they are prominent in the
    # requested route, title, or primary heading.
    negative_hits = _negative_term_hits(" ".join([raw_url, title_text, primary_heading]))
    scope_exclusion_reason = _source_scope_exclusion_reason(
        product_type=product_type,
        fingerprint=" ".join([raw_url, title_text, primary_heading]).lower(),
    )
    multi_product_family_overview = _looks_like_multi_product_family_overview(
        product_type=product_type,
        title_text=title_text,
        primary_heading=primary_heading,
        secondary_headings=parser.secondary_headings,
        body_text=" ".join([*parser.body_chunks, *structured_sections]),
    )

    score = 0
    reason_codes: list[str] = []
    product_identity_match = bool(title_match or primary_heading_match or url_identity_match)
    if product_identity_match:
        reason_codes.append("product_identity_signal")
    if structured_sections:
        reason_codes.append("structured_component_evidence")
    if access_gate_detected:
        reason_codes.append("location_access_gate")
    if title_match:
        score += 3
        reason_codes.append("title_semantic_match")
    if primary_heading_match:
        score += 3
        reason_codes.append("detail_page_layout_signal")
    if url_identity_match:
        score += 1
        reason_codes.append("url_product_identity_signal")
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
    if scope_exclusion_reason:
        score -= 6
        negative_hits += 2
        reason_codes.append(scope_exclusion_reason)
        reason_codes.append("insufficient_evidence")
    if multi_product_family_overview:
        reason_codes.append("multi_product_family_overview")
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
        product_identity_match=product_identity_match,
    )


class _PageSignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._tag_stack: list[str] = []
        self._ignore_depth = 0
        self._title_parts: list[str] = []
        self._h1_groups: list[list[str]] = []
        self._secondary_heading_groups: list[list[str]] = []
        self.body_chunks: list[str] = []

    @property
    def title_text(self) -> str:
        return _collapse_whitespace(" ".join(self._title_parts))

    @property
    def primary_heading(self) -> str:
        return _collapse_whitespace(" ".join(self._h1_groups[0])) if self._h1_groups else ""

    @property
    def secondary_headings(self) -> list[str]:
        return [
            heading
            for parts in self._secondary_heading_groups
            if (heading := _collapse_whitespace(" ".join(parts)))
        ]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"}:
            self._ignore_depth += 1
            return
        self._tag_stack.append(normalized)
        if normalized == "h1":
            self._h1_groups.append([])
        elif normalized in {"h2", "h3"}:
            self._secondary_heading_groups.append([])

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
            if not self._h1_groups:
                self._h1_groups.append([])
            self._h1_groups[-1].append(text)
        elif "h2" in self._tag_stack or "h3" in self._tag_stack:
            if not self._secondary_heading_groups:
                self._secondary_heading_groups.append([])
            self._secondary_heading_groups[-1].append(text)
        else:
            self.body_chunks.append(text)


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _term_hits(text: str, terms: list[str]) -> int:
    fingerprint = text.lower()
    return sum(1 for term in terms if term and term in fingerprint)


def _distinct_term_hits(text: str, terms: list[str]) -> int:
    fingerprint = text.lower()
    return len({term for term in terms if term and term in fingerprint})


def _looks_like_multi_product_family_overview(
    *,
    product_type: str,
    title_text: str,
    primary_heading: str,
    secondary_headings: list[str],
    body_text: str = "",
) -> bool:
    normalized_type = _canonical_product_type_code(product_type)
    generic_identity_terms = {
        "chequing": ("chequing", "chequing accounts", "checking", "checking accounts", "bank accounts"),
        "savings": ("savings", "savings accounts", "saving accounts"),
        "gic": ("gic", "gics", "term deposit", "term deposits", "guaranteed investment certificates"),
        "credit-card": ("credit card", "credit cards"),
        "mortgage": ("mortgage", "mortgages", "mortgage solutions", "mortgage products"),
        "personal-loan": ("personal loan", "personal loans"),
        "line-of-credit": ("line of credit", "lines of credit"),
    }.get(normalized_type)
    if generic_identity_terms is None:
        return False

    heading_identity = _collapse_whitespace(primary_heading).lower().strip(" .:-|")
    title_identity = _collapse_whitespace(title_text.split("|", 1)[0]).lower().strip(" .:-|")
    if normalized_type == "savings":
        full_body = _collapse_whitespace(" ".join([*secondary_headings, body_text])).lower()
        educational_hisa = (
            "high interest savings account" in heading_identity
            and "what is a high interest savings account" in full_body
            and "type of savings account" in full_body
        )
        named_savings_heading = any(
            "account" in _collapse_whitespace(heading).lower()
            and "high interest savings account" not in _collapse_whitespace(heading).lower()
            for heading in secondary_headings
        )
        if educational_hisa and named_savings_heading:
            return True
    exact_generic_identity = heading_identity in generic_identity_terms or title_identity in generic_identity_terms
    plural_identity_terms = {
        "chequing": ("chequing accounts", "checking accounts", "bank accounts"),
        "savings": ("savings accounts", "saving accounts"),
        "gic": ("gics", "term deposits", "guaranteed investment certificates"),
        "credit-card": ("credit cards",),
        "mortgage": ("mortgages", "mortgage solutions", "mortgage products"),
        "personal-loan": ("personal loans",),
        "line-of-credit": ("lines of credit",),
    }[normalized_type]
    plural_family_identity = any(
        term in heading_identity or term in title_identity
        for term in plural_identity_terms
    )
    action_family_identity = any(
        re.search(pattern, identity)
        for identity in (heading_identity, title_identity)
        for pattern in (
            rf"\b(?:open|compare|choose|find|explore|discover)\b.{{0,45}}\b{re.escape(plural_term)}\b"
            for plural_term in plural_identity_terms
        )
    )
    if normalized_type == "savings" and any(
        phrase in heading_identity or phrase in title_identity
        for phrase in ("save for tomorrow", "starting today", "savings goals")
    ):
        action_family_identity = True
    if not exact_generic_identity and not plural_family_identity and not action_family_identity:
        return False

    variant_terms = {
        "chequing": ("account", "chequing", "checking", "student", "newcomer", "unlimited", "premium", "everyday"),
        "savings": ("savings", "saving", "notice", "youth", "student", "high interest", "premium", "us dollar", "usd"),
        "gic": (
            "gic",
            "term deposit",
            "redeemable",
            "non-redeemable",
            "non redeemable",
            "cashable",
            "non-cashable",
            "non cashable",
            "long-term",
            "long term",
            "short-term",
            "short term",
            "market-linked",
            "market linked",
            "wait and see",
        ),
        "credit-card": ("credit card", "visa", "mastercard", "cash back", "rewards"),
        "mortgage": ("mortgage", "fixed-rate", "fixed rate", "convertible", "rental", "improvements", "second mortgage"),
        "personal-loan": (),
        "line-of-credit": ("line of credit", "home equity", "student", "professional"),
    }[normalized_type]
    normalized_secondary_headings = {
        _collapse_whitespace(heading).lower()
        for heading in secondary_headings
        if _collapse_whitespace(heading)
    }
    if normalized_type == "personal-loan":
        # Repeated headings such as "Personal loan rates" and "Personal loan
        # calculator" describe one offering. Only distinct lending subtypes
        # establish a multi-product boundary.
        personal_loan_subtypes = {
            "personal": ("personal loan",),
            "auto": ("auto loan", "auto financing", "car loan", "vehicle loan"),
            "student": ("student loan",),
            "registered": ("rrsp loan",),
            "consolidation": ("debt consolidation loan", "consolidation loan"),
            "home-improvement": ("home improvement loan", "home renovation loan", "home reno loan"),
            "recreational": ("recreational vehicle", "rv loan"),
        }
        represented_subtypes = {
            subtype
            for subtype, markers in personal_loan_subtypes.items()
            if any(
                marker in heading
                for marker in markers
                for heading in normalized_secondary_headings
            )
        }
        if len(represented_subtypes) >= 2:
            return True
    else:
        variant_headings = {
            heading
            for heading in normalized_secondary_headings
            if any(term in heading for term in variant_terms)
        }
        if len(variant_headings) >= 2:
            return True

    normalized_body = _collapse_whitespace(body_text).lower()
    category_match = re.search(r"\bselect\s+categor(?:y|ies)\b", normalized_body)
    if category_match is None:
        return False
    category_window = normalized_body[category_match.end():category_match.end() + 1400]
    category_variant_terms = {
        "chequing": ("student", "newcomer", "unlimited", "premium", "everyday"),
        "savings": ("notice", "youth", "student", "high interest", "premium", "u.s. dollar", "us dollar"),
        "gic": (
            "non-redeemable", "non redeemable", "redeemable", "cashable", "rateadvantage",
            "u.s. dollar term", "us dollar term", "income builder", "market-linked", "market linked",
            "marketsmart", "interest-linked", "interest linked",
        ),
        "credit-card": ("visa", "mastercard", "cash back", "rewards", "low interest"),
        "mortgage": ("fixed rate", "variable rate", "open mortgage", "closed mortgage"),
        "personal-loan": ("auto loan", "personal loan", "student loan", "recreational vehicle"),
        "line-of-credit": ("home equity", "student", "professional", "personal line"),
    }[normalized_type]
    category_variants = {term for term in category_variant_terms if term in category_window}
    return len(category_variants) >= 2


def _negative_term_hits(text: str) -> int:
    fingerprint = text.lower()
    return sum(1 for term in _PAGE_NEGATIVE_KEYWORDS if term in fingerprint)


def _extract_allowed_links(
    *,
    html_text: str,
    base_url: str,
    hostname: str,
    allowed_domains: tuple[str, ...] | None = None,
) -> list[Any]:
    bounded_domains = allowed_domains or _discovery_allowed_domains(hostname)
    allowed_links: list[Any] = []
    for link in extract_links(html_text, base_url=base_url):
        link_hostname = urlparse(link.normalized_url).hostname
        if not link_hostname or not host_matches_allowed_domains(link_hostname, bounded_domains):
            continue
        allowed_links.append(link)
    return allowed_links


def _discovery_allowed_domains(hostname: str) -> tuple[str, ...]:
    normalized = hostname.strip().lower().rstrip(".")
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return (normalized,)


def _coverage_allowed_domains(
    *,
    normalized_homepage_url: str,
    normalized_coverage_source_url: str | None,
    coverage_source_metadata: dict[str, Any] | None,
) -> tuple[str, ...]:
    homepage_host = urlparse(normalized_homepage_url).hostname or ""
    domains = list(_discovery_allowed_domains(homepage_host))
    if not normalized_coverage_source_url:
        return tuple(domains)
    coverage_host = urlparse(normalized_coverage_source_url).hostname or ""
    normalized_coverage_host = _normalized_hostname(coverage_host)
    if normalized_coverage_host and normalized_coverage_host not in domains:
        metadata = _mapping(coverage_source_metadata)
        if (
            metadata.get("verification_status") == "verified"
            and _normalized_hostname(str(metadata.get("coverage_domain") or "")) == normalized_coverage_host
        ):
            domains.append(normalized_coverage_host)
    return tuple(domains)


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
    if _source_scope_exclusion_reason(product_type=product_type, fingerprint=fingerprint):
        return -8
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


def _looks_like_secondary_catalog_hub(
    *,
    product_type: str,
    normalized_url: str,
    anchor_text: str,
) -> bool:
    """Recognize bounded product-category pages that can lead to detail pages.

    Many institutions place individual products two links below the configured
    entry page (catalog -> category -> product).  Keep this deliberately
    structural: plural product-family language is required and operational,
    application, legal, and rate-only destinations are excluded.
    """

    fingerprint = f"{normalized_url} {anchor_text}".lower()
    if _has_excluded_link_signal(normalized_url=normalized_url, anchor_text=anchor_text):
        return False
    if _source_scope_exclusion_reason(product_type=product_type, fingerprint=fingerprint):
        return False
    if infer_source_type(normalized_url) == "pdf":
        return False
    if any(
        marker in fingerprint
        for marker in (
            "agreement", "apply", "calculator", "disclosure", "fees-at-a-glance",
            "interest-rates", "legal", "manage", "service-fee", "terms", "welcome-kit",
        )
    ):
        return False

    path_segments = [segment.lower() for segment in urlparse(normalized_url).path.split("/") if segment]
    if not path_segments:
        return False
    terminal = re.sub(r"\.(?:html?|aspx?)$", "", path_segments[-1])
    terminal_words = terminal.replace("_", "-").replace("%20", "-")
    anchor = _collapse_whitespace(anchor_text).lower()
    normalized_type = _canonical_product_type_code(product_type)
    plural_markers = {
        "chequing": ("accounts", "bank-accounts", "chequing-accounts", "checking-accounts"),
        "savings": ("accounts", "saving-accounts", "savings-accounts"),
        "gic": ("gics", "term-deposits", "guaranteed-investment-certificates"),
        "credit-card": ("cards", "credit-cards"),
        "mortgage": ("mortgages", "mortgage-products", "mortgage-solutions"),
        "personal-loan": ("loans", "personal-loans"),
        "line-of-credit": ("lines-of-credit", "credit-lines"),
    }.get(normalized_type, ())
    anchor_markers = {
        "chequing": ("bank accounts", "chequing accounts", "checking accounts"),
        "savings": ("saving accounts", "savings accounts"),
        "gic": ("gics", "term deposits", "guaranteed investment certificates"),
        "credit-card": ("credit cards", "cards"),
        "mortgage": ("mortgages", "mortgage products", "mortgage solutions"),
        "personal-loan": ("loans", "personal loans"),
        "line-of-credit": ("lines of credit", "credit lines"),
    }.get(normalized_type, ())
    return any(
        terminal_words == marker or terminal_words.endswith(f"-{marker}")
        for marker in plural_markers
    ) or any(marker in anchor for marker in anchor_markers)


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
        "product_key": f"{country_code.upper()}:{bank_code.upper()}:{product_type}",
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
        "discovery_metadata": {
            **(discovery_metadata or {}),
            **market_profile_metadata(
                country_code=country_code,
                product_type=product_type,
            ),
        },
        "change_reason": "generated_from_bank_homepage",
    }


def _dedupe_generated_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detail_rows = [item for item in rows if str(item.get("discovery_role")) == "detail"]
    non_detail_rows = [item for item in rows if str(item.get("discovery_role")) != "detail"]
    detail_rows, _ = _dedupe_detail_rows_by_product_identity(detail_rows)
    by_scope: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in [*detail_rows, *non_detail_rows]:
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
    if _source_scope_exclusion_reason(product_type=product_type, fingerprint=fingerprint):
        return -8
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
    card_detail_path = _looks_like_credit_card_detail_path(
        product_type=product_type,
        normalized_url=normalized_url,
    )
    if card_detail_path:
        score += 6
    for keyword in _SUPPORTING_KEYWORDS:
        if keyword in fingerprint and not (card_detail_path and keyword in {"fee", "fees"}):
            score -= 1
    return score


def _authoritative_catalog_detail_bonus(
    *,
    product_type: str,
    normalized_url: str,
    base_score: int,
    parent_url: str,
    seed_entry_url: str | None,
) -> int:
    """Keep named products from the registered catalog entry ahead of secondary-hub noise."""

    if (
        base_score <= 0
        or not seed_entry_url
        or normalize_source_url(parent_url) != normalize_source_url(seed_entry_url)
    ):
        return 0
    if _looks_like_credit_card_detail_path(
        product_type=product_type,
        normalized_url=normalized_url,
    ):
        return _AUTHORITATIVE_CATALOG_DETAIL_BONUS
    return 0


def _looks_like_credit_card_detail_path(*, product_type: str, normalized_url: str) -> bool:
    """Recognize a bounded singular-card URL shape without bank-specific slugs."""

    if _canonical_product_type_code(product_type) != "credit-card":
        return False
    segments = [segment.lower() for segment in urlparse(normalized_url).path.split("/") if segment]
    try:
        root_index = next(index for index, segment in enumerate(segments) if segment in {"credit-card", "credit-cards"})
    except StopIteration:
        return False
    tail = segments[root_index + 1 :]
    if not tail:
        return False
    terminal = re.sub(r"\.(?:html?|aspx?)$", "", tail[-1])
    generic_terminal = {
        "all", "cards", "cash-back", "compare", "credit-cards", "low-interest", "no-annual-fee",
        "rewards", "sceneplus", "student", "students", "travel", "types",
    }
    non_product_terminal_markers = (
        "activate", "agreement", "apply", "calculator", "disclosure", "fees-at-a-glance",
        "interest-rates", "manage", "rates", "service-fee", "terms", "welcome-kit",
    )
    if (
        terminal in generic_terminal
        or terminal.endswith("-cards")
        or any(marker in terminal for marker in non_product_terminal_markers)
    ):
        return False
    networks = {"american-express", "amex", "mastercard", "visa"}
    return (
        len(tail) >= 2 and tail[-2] in networks
        or len(tail) >= 1
        and bool(re.search(r"(?:card|visa|mastercard|amex|american-express)", terminal))
    )


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
    normalized_path = urlparse(normalized_url).path.lower().rstrip("/")
    if _is_product_type_rate_page(
        product_type=signal_product_type,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    ):
        return True
    generic_deposit_rate_page = (
        _canonical_product_type_code(signal_product_type) in {"savings", "gic"}
        and normalized_path.rsplit("/", 1)[-1] in {"rate", "rates", "interest-rate", "interest-rates"}
        and not any(
            segment in normalized_path.split("/")
            for segment in ("business", "commercial", "mortgage", "mortgages", "loan", "loans", "credit-card", "credit-cards")
        )
    )
    if generic_deposit_rate_page:
        return True
    if _has_excluded_link_signal(normalized_url=normalized_url, anchor_text=anchor_text):
        return False
    if _source_scope_exclusion_reason(product_type=signal_product_type, fingerprint=fingerprint):
        return False
    has_supporting_signal = any(keyword in fingerprint for keyword in _SUPPORTING_KEYWORDS)
    if _has_unrelated_product_type_signal(product_type=signal_product_type, fingerprint=fingerprint):
        return False
    if _has_unrelated_product_path_signal(product_type=signal_product_type, normalized_url=normalized_url):
        return False
    if _canonical_product_type_code(signal_product_type) == "gic" and not any(
        marker in fingerprint
        for marker in (
            "gic",
            "guaranteed investment",
            "guaranteed-investment",
            "term deposit",
            "term-deposit",
            "deposit investment",
            "deposit-investment",
        )
    ):
        # General bank-account fee/service pages are useful to transactional
        # deposits, but are not evidence for fixed-term deposit products. A
        # generic deposit rate page was handled explicitly above.
        return False
    has_product_signal = _score_product_link(
        product_type=signal_product_type,
        product_type_definition=product_type_definition,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    ) > 0
    return has_product_signal or (
        has_supporting_signal and _has_supporting_product_context_signal(fingerprint)
    )


def _supporting_source_is_bounded_to_selected_details(
    *,
    product_type: str,
    normalized_url: str,
    anchor_text: str = "",
    promoted_detail_urls: set[str],
) -> bool:
    """Keep comparison support near a selected product or essential-fact page.

    Bank navigation surfaces frequently make unrelated education, help,
    servicing, transfer, investment, and sibling-product pages look relevant.
    Those pages cannot establish an exact-product comparison fact and add
    substantial latency, so keep selected-product companions plus bounded
    rate/APR and product-fact FAQ pages.
    """

    canonical_type = _canonical_product_type_code(product_type)
    governed_types = {
        "chequing",
        "savings",
        "gic",
        "mortgage",
        "personal-loan",
        "credit-card",
        "line-of-credit",
    }
    if canonical_type not in governed_types:
        return True
    parsed = urlparse(normalized_url)
    path = parsed.path.lower().rstrip("/")
    path_tail = path.rsplit("/", 1)[-1]
    if _is_product_type_rate_page(
        product_type=canonical_type,
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    ):
        return True
    rate_page = (
        path_tail in {"rate", "rates", "interest-rate", "interest-rates", "apr"}
        or path_tail.endswith(("-rate", "-rates", "-apr"))
    )
    if rate_page and not any(
        segment in path.split("/")
        for segment in ("business", "commercial", "mortgage", "mortgages", "loan", "loans", "credit-card", "credit-cards")
    ):
        if canonical_type in {"chequing", "savings", "gic"}:
            return True
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    lending_markers = {
        "mortgage": ("mortgage", "home loan", "home-loan"),
        "personal-loan": ("personal loan", "personal-loan", "personal-loans"),
        "credit-card": ("credit card", "credit-card", "credit-cards"),
        "line-of-credit": ("line of credit", "line-of-credit", "line-of-credits"),
    }
    if rate_page and canonical_type in lending_markers and any(
        marker in fingerprint for marker in lending_markers[canonical_type]
    ):
        return True
    if (
        canonical_type == "gic"
        and any(marker in path for marker in ("/faq/", "/faqs/", "/help/", "/help-centre/", "/help-center/"))
        and any(marker in fingerprint for marker in ("gic", "guaranteed investment", "term deposit"))
        and any(
            marker in fingerprint
            for marker in ("minimum balance", "minimum deposit", "minimum investment", "interest rate", "withdraw", "redeem", "maturity")
        )
    ):
        return True
    if (
        canonical_type in lending_markers
        and any(marker in path for marker in ("/faq/", "/faqs/", "/help/", "/help-centre/", "/help-center/"))
        and any(marker in fingerprint for marker in lending_markers[canonical_type])
        and any(
            marker in fingerprint
            for marker in ("rate", "apr", "amount", "term", "fee", "limit", "payment")
        )
    ):
        return True
    for detail_url in promoted_detail_urls:
        detail = urlparse(detail_url)
        if parsed.scheme != detail.scheme or parsed.netloc != detail.netloc:
            continue
        detail_path = detail.path.lower().rstrip("/")
        if detail_path and (
            path.startswith(f"{detail_path}/")
            or path.startswith(f"{detail_path}-")
        ):
            return True
    return False


def _is_product_type_rate_page(
    *,
    product_type: str,
    normalized_url: str,
    anchor_text: str,
) -> bool:
    """Recognize an official rate route whose path names the product family.

    Some banks use `/rates/accounts` or `/rates/loans-lines-of-credit` rather
    than a terminal `rates` slug. These pages are comparison evidence, not
    standalone product details, and must be retained for every applicable
    product type without admitting a generic or cross-product rate page.
    """

    parsed = urlparse(normalized_url)
    path = parsed.path.lower().rstrip("/")
    segments = {segment for segment in path.split("/") if segment}
    fingerprint = f"{path} {anchor_text}".lower()
    has_rate_route = (
        "rates" in segments
        or "rate" in segments
        or path.endswith(("-rate", "-rates", "/interest-rate", "/interest-rates", "/apr"))
    )
    if not has_rate_route:
        return False
    canonical_type = _canonical_product_type_code(product_type)
    markers = {
        "chequing": ("account", "accounts", "chequing", "checking"),
        "savings": ("account", "accounts", "saving", "savings"),
        "gic": ("gic", "term-deposit", "term deposit", "guaranteed-investment"),
        "credit-card": ("credit-card", "credit card", "cards"),
        "mortgage": ("mortgage", "mortgages"),
        "personal-loan": ("personal-loan", "personal loan", "loans-lines-of-credit", "loans lines of credit"),
        "line-of-credit": ("line-of-credit", "line of credit", "lines-of-credit", "loans-lines-of-credit"),
    }.get(canonical_type, ())
    return bool(markers) and any(marker in fingerprint for marker in markers)


def _is_product_fact_support_link(*, normalized_url: str, anchor_text: str, product_score: int) -> bool:
    """Keep narrow official FAQ/help facts as evidence, never as product candidates."""

    if product_score <= 0:
        return False
    path = urlparse(normalized_url).path.lower()
    if not any(marker in path for marker in ("/faq/", "/faqs/", "/help/", "/help-centre/", "/help-center/")):
        return False
    fingerprint = f"{normalized_url} {anchor_text}".lower()
    return any(
        marker in fingerprint
        for marker in (
            "minimum balance",
            "minimum deposit",
            "minimum investment",
            "minimum amount",
            "fees",
            "interest paid",
            "interest rate",
            "eligible",
            "eligibility",
            "withdraw",
            "redeem",
            "maturity",
        )
    )


def _seed_supporting_hint_is_relevant(
    *,
    product_type: str,
    discovery_product_type: str | None,
    product_type_definition: dict[str, Any],
    hint: dict[str, Any],
) -> bool:
    """Apply current scope policy to curated hints as well as discovered links.

    Seed files are durable discovery hints, not an exemption from later source
    safety improvements. This prevents retired action flows, calculators and
    editorial pages from remaining active indefinitely solely because they
    were once listed in a registry seed.
    """

    source_url = normalize_source_url(str(hint.get("source_url") or ""))
    if not source_url:
        return False
    anchor_text = " ".join(
        str(value or "").strip()
        for value in (
            hint.get("source_name"),
            hint.get("purpose"),
            " ".join(str(item) for item in (hint.get("expected_fields") or [])),
        )
        if str(value or "").strip()
    )
    path_tail = urlparse(source_url).path.lower().rstrip("/").rsplit("/", 1)[-1]
    expected_fields = {
        str(item or "").strip().lower()
        for item in (hint.get("expected_fields") or [])
        if str(item or "").strip()
    }
    if (
        _canonical_product_type_code(discovery_product_type or product_type) == "chequing"
        and path_tail in {"rate", "rates", "interest-rate", "interest-rates"}
        and "chequing" in anchor_text.lower()
        and expected_fields.intersection({"account_interest_rates", "chequing_account_list"})
        and not _has_excluded_link_signal(normalized_url=source_url, anchor_text=anchor_text)
    ):
        # A curated cross-listing rate table may serve both Chequing and
        # Savings. Require an explicit Chequing purpose/field declaration;
        # ordinary discovered Savings pages do not receive this exception.
        return True
    return _link_is_relevant_supporting_source(
        product_type=product_type,
        discovery_product_type=discovery_product_type,
        product_type_definition=product_type_definition,
        normalized_url=source_url,
        anchor_text=anchor_text,
    )


def _has_supporting_product_context_signal(fingerprint: str) -> bool:
    return any(
        keyword in fingerprint
        for keyword in (
            "bank-account",
            "bank accounts",
            "deposit-investment",
            "deposit investment",
            "credit-card",
            "credit cards",
            "mortgage",
            "mortgages",
            "loan",
            "loans",
            "line-of-credit",
            "line of credit",
            "borrow",
            "borrowing",
            "lending",
        )
    )


def _has_excluded_link_signal(*, normalized_url: str, anchor_text: str) -> bool:
    hostname = str(urlparse(normalized_url).hostname or "").lower()
    if hostname.startswith(("help.", "support.")):
        return True
    path_segments = {
        segment
        for segment in urlparse(normalized_url).path.lower().split("/")
        if segment
    }
    if any(segment == "join" or segment.startswith("join-") for segment in path_segments):
        return True
    path_and_query = " ".join(
        part
        for part in (urlparse(normalized_url).path.lower(), urlparse(normalized_url).query.lower())
        if part
    )
    application_guide = any(
        marker in path_and_query
        for marker in ("application-guide", "application_checklist", "application-checklist")
    )
    if any(
        keyword in path_and_query
        for keyword in _EXCLUDED_LINK_KEYWORDS
        if keyword != "application" or not application_guide
    ):
        return True
    normalized_anchor = _collapse_whitespace(anchor_text).lower().strip(" .:-|")
    if not normalized_anchor:
        return False
    exact_action_labels = {
        "login",
        "log in",
        "sign in",
        "apply",
        "apply now",
        "open account",
        "open an account",
        "compare",
        "compare now",
        "view offer",
        "special offer",
    }
    if normalized_anchor in exact_action_labels:
        return True
    return len(normalized_anchor) <= 120 and bool(
        re.match(
            r"^(?:login|log in|sign in|apply now|start (?:your|an?) application|"
            r"open (?:an )?account|compare(?: now)?)\b",
            normalized_anchor,
        )
    )


def _has_excluded_product_discovery_link_signal(
    *,
    product_type: str,
    normalized_url: str,
    anchor_text: str,
) -> bool:
    normalized_anchor = _collapse_whitespace(anchor_text).lower().strip(" .:-|")
    if (
        normalized_anchor == "view offer"
        and _looks_like_credit_card_detail_path(
            product_type=product_type,
            normalized_url=normalized_url,
        )
    ):
        # Some official catalog cards use a generic acquisition CTA as the
        # only anchor for an exact, named product detail route. The singular
        # URL contract remains fail-closed for category and campaign pages.
        return False
    return _has_excluded_link_signal(
        normalized_url=normalized_url,
        anchor_text=anchor_text,
    )


def _has_unrelated_product_type_signal(*, product_type: str, fingerprint: str) -> bool:
    exclusions = _PRODUCT_TYPE_EXCLUSION_KEYWORDS.get(product_type, ())
    if not any(keyword in fingerprint for keyword in exclusions):
        return False
    canonical_type = _canonical_product_type_code(product_type)
    product_terms = tuple(
        dict.fromkeys(
            (
                canonical_type,
                canonical_type.replace("-", " "),
                *_PRODUCT_TYPE_IDENTITY_HINTS.get(canonical_type, ()),
            )
        )
    )
    return not any(term and term in fingerprint for term in product_terms)


def _has_unrelated_product_path_signal(*, product_type: str, normalized_url: str) -> bool:
    normalized_type = _canonical_product_type_code(product_type)
    if normalized_type not in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        return False
    path_segments = {segment for segment in urlparse(normalized_url).path.lower().split("/") if segment}
    if not path_segments.intersection({"account", "accounts", "bank-account", "bank-accounts"}):
        return False
    expected_path_terms = {
        "credit-card": {"credit-card", "credit-cards", "cards"},
        "mortgage": {"mortgage", "mortgages"},
        "personal-loan": {"loan", "loans", "personal-loan", "personal-loans"},
        "line-of-credit": {"line-of-credit", "lines-of-credit"},
    }[normalized_type]
    return path_segments.isdisjoint(expected_path_terms)


def _source_scope_exclusion_reason(*, product_type: str, fingerprint: str) -> str | None:
    normalized_fingerprint = fingerprint.lower()
    source_url = normalized_fingerprint.split(" ", 1)[0]
    source_path = urlparse(source_url).path.lower()
    source_slug = source_path.rstrip("/").rsplit("/", 1)[-1]
    canonical_type = _canonical_product_type_code(product_type)
    explicit_slug_types = {
        "chequing": any(marker in source_slug for marker in ("chequing", "checking")),
        "savings": any(marker in source_slug for marker in ("savings", "saving")),
        "gic": any(
            marker in source_slug
            for marker in ("gic", "term-deposit", "term_deposit", "bank-cd", "certificate-of-deposit")
        ) or bool(re.search(r"(?:^|-)cds?(?:-|$)", source_slug)),
    }
    explicit_other_types = {key for key, matched in explicit_slug_types.items() if matched and key != canonical_type}
    if canonical_type in explicit_slug_types and explicit_other_types and not explicit_slug_types[canonical_type]:
        # A page's own slug is stronger identity evidence than global nav copy.
        # This prevents a chequing detail page from becoming a savings detail
        # merely because the common header also links to savings products.
        return "other_product_type"
    path_segments = {segment for segment in source_path.split("/") if segment}
    explicit_path_types = {
        "chequing": bool(path_segments.intersection({"chequing", "checking", "chequing-accounts", "checking-accounts"}))
        or any(
            re.search(r"(?:^|-)(?:chequing|checking)(?:-|$)", segment)
            for segment in path_segments
        ),
        "savings": bool(path_segments.intersection({"savings", "saving", "savings-accounts", "saving-accounts"}))
        or any(
            re.search(r"(?:^|-)savings?(?:-|$)", segment)
            for segment in path_segments
        ),
        "gic": bool(
            path_segments.intersection(
                {"gic", "gics", "term-deposit", "term-deposits", "cd", "cds", "bank-cd", "certificate-of-deposit"}
            )
        ) or any(re.search(r"(?:^|-)cds?(?:-|$)", segment) for segment in path_segments),
    }
    explicit_other_path_types = {
        key for key, matched in explicit_path_types.items() if matched and key != canonical_type
    }
    if (
        canonical_type in explicit_path_types
        and explicit_other_path_types
        and not explicit_path_types[canonical_type]
    ):
        return "other_product_type"
    if "/content/" in normalized_fingerprint and "/content/dam/" not in normalized_fingerprint:
        # Public product pages can expose their Adobe/enterprise CMS backing
        # URL as a link. The CMS path is an alias of the canonical public page,
        # not a second source identity or product.
        return "non_product_service_flow"
    if re.search(r"\boffers?\b", normalized_fingerprint) and any(
        marker in normalized_fingerprint
        for marker in (
            "/young-adults/",
            "/campaign/",
            "/campaigns/",
            "/promotion/",
            "/promotions/",
        )
    ):
        # Audience/campaign landing pages can describe an existing product and
        # its temporary acquisition rate, but they are not a second product.
        return "non_product_service_flow"
    if any(
        marker in normalized_fingerprint
        for marker in (
            "consider adding a ",
            "selecting one of the products below",
            "continue with my current application",
        )
    ) and any(
        marker in normalized_fingerprint
        for marker in ("/bundles/", "/apply/", "/application/")
    ):
        # Some acquisition journeys retain the selected product name in the
        # browser title while the H1/body has already advanced to a cross-sell
        # step.  They are application state, not a second product detail page.
        return "non_product_service_flow"
    if _canonical_product_type_code(product_type) in {"chequing", "savings", "gic"} and any(
        keyword in normalized_fingerprint
        for keyword in (
            "/mutual_funds/",
            "/mutual-funds/",
            "/mutual-funds-",
            "reporting_and_governance",
            "reporting-and-governance",
            "simplified-prospectus",
            "fund-facts",
        )
    ):
        return "other_product_type"
    if canonical_type in {"savings", "gic"} and any(
        marker in source_path
        for marker in ("/e-transfer", "/global-money-transfer", "/money-transfer")
    ):
        return "non_product_service_flow"
    if any(
        keyword in normalized_fingerprint
        for keyword in (
            "/resource-centre/",
            "/resource-center/",
            "/article/",
            "/articles/",
            "/blog/",
            "/thejuice/",
        )
    ):
        return "non_product_editorial_page"
    editorial_path_segments = {
        segment
        for segment in urlparse(normalized_fingerprint.split(" ", 1)[0]).path.lower().split("/")
        if segment
    }
    if any(
        segment in {"article", "articles", "blog"}
        or segment.endswith("-blog")
        or segment.startswith("blog-")
        or segment.startswith(("what-is-", "what-are-", "how-does-", "how-to-choose-", "rules-of-"))
        or "-vs-" in segment
        or segment in {"getting-started", "emergency-fund", "multiple-bank-accounts"}
        for segment in editorial_path_segments
    ):
        return "non_product_editorial_page"
    if _canonical_product_type_code(product_type) in {"savings", "gic"} and any(
        segment.startswith(("value-program", "rewards-program", "relationship-program"))
        for segment in editorial_path_segments
    ):
        return "other_product_type"
    if _canonical_product_type_code(product_type) == "gic" and any(
        keyword in normalized_fingerprint
        for keyword in (
            "/personal/invest/non-registered-funds",
            "/personal/invest mutual funds",
        )
    ):
        return "other_product_type"
    if any(
        keyword in normalized_fingerprint
        for keyword in (
            "/shadow-site/",
            "/switch-mortgage",
            "/switch-your-mortgage",
            "/manage-mortgage",
            "/manage-my-mortgage",
        )
    ):
        return "non_product_service_flow"
    if _looks_like_mortgage_advice_or_servicing_flow(
        product_type=product_type,
        fingerprint=normalized_fingerprint,
    ):
        return "non_product_service_flow"
    if any(
        keyword in normalized_fingerprint
        for keyword in (
            "/small-business",
            "small business",
            "/business-banking",
            "/business",
            "business banking",
            "/commercial-banking",
            "/commercial/",
            "commercial banking",
            "/corporate-banking",
            "corporate banking",
            "/transaction-banking",
            "transaction banking",
            "corporate cash management",
            "global liquidity management solutions",
            "business credit",
            "business card",
            "business loan",
            "business mortgage",
            "business account",
            "business gic",
            "commercial gic",
            "commercial deposit",
            "commercial mortgage",
            "commercial loan",
            "commercial account",
        )
    ):
        return "non_consumer_business_page"
    if _canonical_product_type_code(product_type) == "credit-card" and any(
        keyword in normalized_fingerprint
        for keyword in (
            "/corporate-",
            " corporate ",
            "/bizline",
            " bizline ",
        )
    ):
        return "non_consumer_business_page"
    if canonical_type == "credit-card" and (
        "/products/insurance/" in source_path
        or "credit card payment protection" in normalized_fingerprint
    ):
        return "other_product_type"
    if canonical_type == "mortgage" and any(
        marker in normalized_fingerprint
        for marker in (
            "home-equity-line",
            "home equity line of credit",
            "heloc",
        )
    ):
        # A HELOC can be linked from a mortgage hub or even live below a
        # `/mortgage/` route, but its product identity is line-of-credit.
        return "other_product_type"
    if any(keyword in fingerprint for keyword in ("investor", "investors", "shareholder", "shareholders")):
        return "non_product_or_investor_page"
    registered_plan_signal = any(
        keyword in fingerprint for keyword in _REGISTERED_PLAN_WRAPPER_KEYWORDS
    )
    explicit_registered_underlying_product = (
        canonical_type == "personal-loan"
        and any(marker in source_path for marker in ("/rrsp-loan", "/registered-retirement-loan"))
        or canonical_type == "gic"
        and any(marker in source_path for marker in ("/term-deposit-gic/", "/gic/", "/gics/"))
    )
    if registered_plan_signal and not explicit_registered_underlying_product:
        return "registered_plan_wrapper"
    if _has_unrelated_product_type_signal(product_type=product_type, fingerprint=fingerprint):
        return "other_product_type"
    return None


def _looks_like_mortgage_advice_or_servicing_flow(*, product_type: str, fingerprint: str) -> bool:
    if _canonical_product_type_code(product_type) != "mortgage":
        return False
    mortgage_flow_path = any(
        token in fingerprint
        for token in (
            "/mortgage/refinance",
            "/mortgages/refinance",
            "/mortgage/renewal",
            "/mortgages/renewal",
        )
    )
    if not mortgage_flow_path:
        return False
    advice_or_servicing_signal = any(
        phrase in fingerprint
        for phrase in (
            "thinking about",
            "should i ",
            "when should",
            "why refinance",
            "reasons to refinance",
            "understanding refinancing",
            "how refinancing works",
            "what does refinancing",
            "what is refinancing",
            "mortgage servicing",
            "contact an account manager",
            "talk to an account manager",
        )
    )
    return advice_or_servicing_signal


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


def _build_source_catalog_ai_model_execution_record(
    *,
    run_id: str,
    bank_code: str,
    country_code: str,
    product_type: str,
    discovery_product_type: str,
    source_language: str,
    homepage_url: str,
    normalized_homepage_url: str,
    homepage_fetch_error: str | None,
    candidate_link_count: int,
    scored_candidate_count: int,
    correlation_id: str | None,
    request_id: str | None,
    model_id: str,
    execution_status: str,
    started_at: datetime,
    completed_at: datetime,
    error_summary: str | None = None,
    fallback_mode: str | None = None,
    candidate_scores: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "bank_code": bank_code,
        "country_code": country_code,
        "product_type": product_type,
        "discovery_product_type": discovery_product_type,
        "source_language": source_language,
        "homepage_url": homepage_url,
        "normalized_homepage_url": normalized_homepage_url,
        "homepage_fetch_error": homepage_fetch_error,
        "candidate_link_count": candidate_link_count,
        "scored_candidate_count": scored_candidate_count,
        "correlation_id": correlation_id,
        "request_id": request_id,
    }
    if error_summary:
        metadata["error_summary"] = error_summary[:800]
    if fallback_mode:
        metadata["fallback_mode"] = fallback_mode
    if candidate_scores:
        metadata["candidate_scores"] = candidate_scores[:40]
    return {
        "model_execution_id": _build_source_catalog_ai_model_execution_id(
            run_id=run_id,
            bank_code=bank_code,
            product_type=product_type,
            normalized_homepage_url=normalized_homepage_url,
        ),
        "run_id": run_id,
        "source_document_id": None,
        "stage_name": "source_catalog_collection",
        "agent_name": "fpds-homepage-ai-parallel-scorer",
        "model_id": model_id,
        "execution_status": execution_status,
        "execution_metadata": metadata,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }


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


def _apply_bank_product_type_discovery_aliases(
    *,
    bank_code: str,
    product_type: str,
    product_type_definition: dict[str, Any],
) -> dict[str, Any]:
    aliases = _BANK_PRODUCT_TYPE_DISCOVERY_ALIASES.get(
        (str(bank_code).strip().upper(), _canonical_product_type_code(product_type)),
        (),
    )
    if not aliases:
        return product_type_definition
    return {
        **product_type_definition,
        "discovery_keywords": _dedupe_preserve_order(
            [
                *[
                    str(item).strip().lower()
                    for item in product_type_definition.get("discovery_keywords", [])
                    if str(item).strip()
                ],
                *aliases,
            ]
        ),
    }


def _product_type_identity_keywords(product_type: str, product_type_definition: dict[str, Any]) -> list[str]:
    canonical_product_type = _canonical_product_type_code(product_type)
    curated_hints = list(_PRODUCT_TYPE_IDENTITY_HINTS.get(canonical_product_type, ()))

    identity_nouns = (
        "account",
        "card",
        "mortgage",
        "loan",
        "line of credit",
        "gic",
        "term deposit",
        "certificate",
    )
    candidates = [
        str(product_type_definition.get("display_name") or "").strip().lower(),
        canonical_product_type.replace("-", " "),
        *_product_type_keywords(product_type_definition),
    ]
    canonical_identity_markers = {
        "chequing": ("account",),
        "savings": ("account",),
        "gic": ("gic", "deposit", "certificate", "cd"),
        "credit-card": ("card",),
        "mortgage": ("mortgage", "home loan"),
        "personal-loan": ("loan",),
        "line-of-credit": (
            "line of credit",
            "personal line",
            "home equity line",
            "student line",
            "professional line",
            "heloc",
        ),
    }.get(canonical_product_type)
    if canonical_identity_markers is None:
        definition_hints = [
            item
            for item in candidates
            if item and (any(noun in item for noun in identity_nouns) or len(item.split()) >= 2)
        ]
    else:
        definition_hints = [
            item
            for item in candidates
            if item
            and any(
                bool(re.search(r"\bcd\b", item)) if marker == "cd" else marker in item
                for marker in canonical_identity_markers
            )
        ]
    return _dedupe_preserve_order(
        [
            *curated_hints,
            *definition_hints,
        ]
    )


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
    if {"credit", "card"}.issubset(code_tokens) or "card" in code_tokens:
        return "credit-card"
    if "mortgage" in code_tokens or "mortgages" in code_tokens:
        return "mortgage"
    if "loc" in code_tokens or "heloc" in code_tokens or {"line", "credit"}.issubset(code_tokens):
        return "line-of-credit"
    if "loan" in code_tokens or "loans" in code_tokens:
        return "personal-loan"
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


def _product_type_expected_fields(
    product_type_definition: dict[str, Any],
    *,
    country_code: str | None = None,
) -> list[str]:
    fields = [str(item).strip() for item in product_type_definition.get("expected_fields", []) if str(item).strip()]
    product_type_code = str(product_type_definition.get("product_type_code") or "").strip()
    product_family = str(product_type_definition.get("product_family") or "deposit").strip().lower()
    baseline = list(expected_fields_for_product_type(product_type_code=product_type_code, product_family=product_family)) if product_type_code else []
    registered = list(dict.fromkeys([*fields, *baseline]))
    return list(
        collection_fields_for_product_type(
            product_type=product_type_code,
            country_code=country_code,
            expected_fields=registered,
        )
    )


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
            "has_completed_collection": bool(item.get("has_completed_collection", False)),
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
        "logo_url": row.get("logo_url"),
        "logo_alt_text": row.get("logo_alt_text"),
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
        "coverage_source_url": row.get("coverage_source_url"),
        "coverage_source_metadata": _mapping(row.get("coverage_source_metadata")),
        "homepage_url": bank_row.get("homepage_url"),
        "normalized_homepage_url": bank_row.get("normalized_homepage_url"),
        "logo_url": bank_row.get("logo_url"),
        "logo_alt_text": bank_row.get("logo_alt_text"),
        "source_language": str(bank_row.get("source_language") or "en"),
        "generated_source_count": generated_source_count,
        "has_completed_collection": bool(row.get("has_completed_collection", False)),
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
    actor_type = str(actor.get("actor_type") or "user").lower()
    if actor_type not in {"system", "user", "service"}:
        actor_type = "user"
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
            %(actor_type)s,
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
            "actor_type": actor_type,
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
    if str(existing_row.get("logo_url") or "") != str(updated.get("logo_url") or ""):
        changes.append("Logo URL")
    if str(existing_row.get("logo_alt_text") or "") != str(updated.get("logo_alt_text") or ""):
        changes.append("Logo alt text")
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


def _generate_bank_code(connection: Connection, *, bank_name: str, normalized_homepage_url: str | None = None) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", bank_name.upper())
    if not tokens:
        raise SourceRegistryError(status_code=422, code="bank_name_invalid", message="Bank name must contain letters or digits.")
    candidates: list[str] = []
    seed_code = _seed_bank_code_for_bank_profile(bank_name=bank_name, normalized_homepage_url=normalized_homepage_url)
    if seed_code:
        candidates.append(seed_code)
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


def _seed_bank_code_for_bank_profile(*, bank_name: str, normalized_homepage_url: str | None = None) -> str | None:
    normalized_name = _normalize_bank_match_text(bank_name)
    homepage_host = _hostname_or_none(normalized_homepage_url)
    for profile in load_seed_bank_profiles():
        seed_code = str(profile["bank_code"]).strip().upper()
        seed_name = _normalize_bank_match_text(str(profile.get("bank_name") or ""))
        seed_host = _hostname_or_none(str(profile.get("normalized_homepage_url") or profile.get("homepage_url") or ""))
        if normalized_name and normalized_name == seed_name:
            return seed_code
        if homepage_host and seed_host and homepage_host == seed_host:
            return seed_code
    return None


def _normalize_bank_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _hostname_or_none(value: str | None) -> str | None:
    if not value:
        return None
    hostname = urlparse(value).hostname
    if not hostname:
        return None
    hostname = hostname.lower()
    return hostname[4:] if hostname.startswith("www.") else hostname


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


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalized_hostname(value: str) -> str:
    candidate = value.strip().lower().rstrip(".")
    if "://" in candidate:
        candidate = urlparse(candidate).hostname or ""
    if candidate.startswith("www."):
        candidate = candidate[4:]
    return candidate


def _normalize_country_code(value: Any) -> str:
    normalized = (_clean_text(value) or "CA").upper()
    if len(normalized) != 2 or not normalized.isascii() or not normalized.isalpha():
        raise SourceRegistryError(
            status_code=422,
            code="invalid_country_code",
            message="country_code must be a two-letter ISO 3166-1 alpha-2 code.",
        )
    return normalized


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


def _normalize_optional_public_url(value: Any, field_name: str) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    candidate = cleaned
    if "://" not in candidate:
        candidate = f"https://{candidate.lstrip('/')}"
    try:
        return normalize_source_url(candidate)
    except ValueError as exc:
        raise SourceRegistryError(
            status_code=422,
            code=f"{field_name}_invalid",
            message=f"{field_name} must be a valid public http or https URL.",
        ) from exc


def _normalize_coverage_source_url(
    value: Any,
    *,
    normalized_homepage_url: str,
    coverage_source_metadata: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None, None
    candidate = cleaned if "://" in cleaned else f"https://{cleaned.lstrip('/')}"
    try:
        normalized = normalize_source_url(candidate)
    except ValueError as exc:
        raise SourceRegistryError(
            status_code=422,
            code="coverage_source_url_invalid",
            message="coverage_source_url must be a valid public HTTPS URL.",
        ) from exc
    parsed = urlparse(normalized)
    homepage_host = urlparse(normalized_homepage_url).hostname
    if parsed.scheme.lower() != "https" or not parsed.hostname or not homepage_host:
        raise SourceRegistryError(
            status_code=422,
            code="coverage_source_url_invalid",
            message="coverage_source_url must be a valid public HTTPS URL.",
        )
    same_homepage_domain = host_matches_allowed_domains(
        parsed.hostname,
        _discovery_allowed_domains(homepage_host),
    )
    metadata = _mapping(coverage_source_metadata)
    verified_cross_domain = (
        metadata.get("verification_status") == "verified"
        and metadata.get("verification_method") in {
            "ai_web_search_exact_quote",
            "ai_bank_onboarding_web_search",
        }
        and _normalized_hostname(str(metadata.get("coverage_domain") or ""))
        == _normalized_hostname(parsed.hostname)
        and bool(_clean_text(metadata.get("relationship_source_url")))
        and bool(_clean_text(metadata.get("relationship_quote")))
    )
    if not same_homepage_domain and not verified_cross_domain:
        raise SourceRegistryError(
            status_code=422,
            code="coverage_source_domain_mismatch",
            message=(
                "coverage_source_url must be on the bank's official homepage domain or carry "
                "verified official brand-domain relationship evidence."
            ),
        )
    return candidate, normalized


def _normalize_logo_alt_text(value: Any, *, bank_name: str, logo_url: str | None) -> str | None:
    if logo_url is None:
        return None
    return _clean_text(value) or f"{bank_name} logo"


def _normalize_search(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    return re.sub(r"\s+", " ", cleaned).lower()
