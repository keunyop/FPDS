from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import os
import re
from typing import TYPE_CHECKING, Any
import urllib.error
import urllib.request

from api_service.errors import SourceRegistryError
from api_service.security import new_id, utc_now

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover
    Connection = Any


_GENERIC_EXPECTED_FIELDS = (
    "product_name",
    "description_short",
    "standard_rate",
    "promotional_rate",
    "monthly_fee",
    "minimum_deposit",
    "term_length_text",
    "eligibility_text",
    "notes",
)
_TAXONOMY_SEEDED_PRODUCT_TYPES = {"chequing", "savings", "gic"}
_STOPWORDS = {
    "able",
    "account",
    "accounts",
    "and",
    "are",
    "bank",
    "banking",
    "canada",
    "card",
    "deposit",
    "deposits",
    "designed",
    "easy",
    "for",
    "fund",
    "funds",
    "has",
    "have",
    "into",
    "little",
    "more",
    "most",
    "not",
    "offer",
    "offered",
    "offers",
    "often",
    "or",
    "product",
    "products",
    "rate",
    "rates",
    "such",
    "with",
    "from",
    "that",
    "this",
    "usually",
    "your",
}
_DISCOVERY_KEYWORD_LIMIT = 12
_DISCOVERY_KEYWORD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["summary", "keywords"],
}


@dataclass(frozen=True)
class ProductTypeFilters:
    search: str | None
    status: str | None


def normalize_product_type_filters(*, search: str | None, status: str | None) -> ProductTypeFilters:
    normalized_search = _normalize_search(search)
    normalized_status = _clean_text(status)
    return ProductTypeFilters(
        search=normalized_search,
        status=normalized_status.lower() if normalized_status else None,
    )


def load_product_type_list(connection: Connection, *, filters: ProductTypeFilters) -> dict[str, Any]:
    where_clauses = ["product_family = 'deposit'"]
    params: dict[str, Any] = {}
    if filters.status:
        where_clauses.append("status = %(status)s")
        params["status"] = filters.status
    if filters.search:
        params["search_pattern"] = f"%{filters.search}%"
        where_clauses.append(
            """
            (
                lower(product_type_code) LIKE %(search_pattern)s
                OR lower(display_name) LIKE %(search_pattern)s
                OR lower(description) LIKE %(search_pattern)s
            )
            """
        )

    rows = connection.execute(
        f"""
        SELECT
            product_type_code,
            product_family,
            display_name,
            description,
            status,
            built_in_flag,
            managed_flag,
            discovery_keywords,
            expected_fields,
            fallback_policy,
            created_at,
            updated_at
        FROM product_type_registry
        WHERE {" AND ".join(where_clauses)}
        ORDER BY built_in_flag DESC, display_name, product_type_code
        """,
        params,
    ).fetchall()
    items = [_serialize_product_type_row(row) for row in rows]
    status_counts = Counter(item["status"] for item in items)
    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "status_counts": dict(status_counts),
            "built_in_count": sum(1 for item in items if item["built_in_flag"]),
        },
        "facets": {
            "statuses": sorted(status_counts),
        },
        "applied_filters": {
            "search": filters.search,
            "status": filters.status,
        },
    }


def load_product_type_definition(connection: Connection, *, product_type_code: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            product_type_code,
            product_family,
            display_name,
            description,
            status,
            built_in_flag,
            managed_flag,
            discovery_keywords,
            expected_fields,
            fallback_policy,
            created_at,
            updated_at
        FROM product_type_registry
        WHERE product_type_code = %(product_type_code)s
        """,
        {"product_type_code": product_type_code.lower()},
    ).fetchone()
    return _serialize_product_type_row(row) if row else None


def load_product_type_definitions_map(
    connection: Connection,
    *,
    codes: list[str] | None = None,
    active_only: bool = False,
) -> dict[str, dict[str, Any]]:
    where_clauses = ["product_family = 'deposit'"]
    params: dict[str, Any] = {}
    if active_only:
        where_clauses.append("status = 'active'")
    if codes:
        normalized_codes = sorted({str(item).strip().lower() for item in codes if str(item).strip()})
        if not normalized_codes:
            return {}
        where_clauses.append("product_type_code = ANY(%(codes)s)")
        params["codes"] = normalized_codes

    rows = connection.execute(
        f"""
        SELECT
            product_type_code,
            product_family,
            display_name,
            description,
            status,
            built_in_flag,
            managed_flag,
            discovery_keywords,
            expected_fields,
            fallback_policy,
            created_at,
            updated_at
        FROM product_type_registry
        WHERE {" AND ".join(where_clauses)}
        """,
        params,
    ).fetchall()
    return {item["product_type_code"]: item for item in (_serialize_product_type_row(row) for row in rows)}


def require_product_type_definition(
    connection: Connection,
    *,
    product_type_code: str,
    active_only: bool = True,
) -> dict[str, Any]:
    normalized_code = _required_text(product_type_code, "product_type_code").lower()
    definition = load_product_type_definition(connection, product_type_code=normalized_code)
    if definition is None:
        raise SourceRegistryError(
            status_code=404,
            code="product_type_not_found",
            message="Product type was not found. Create it from /admin/product-types first.",
        )
    if active_only and definition["status"] != "active":
        raise SourceRegistryError(
            status_code=422,
            code="product_type_inactive",
            message="Only active product types can be added to bank coverage.",
        )
    return definition


def create_product_type_definition(
    connection: Connection,
    *,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    display_name = _required_text(payload.get("display_name"), "display_name")
    description = _required_text(payload.get("description"), "description")
    status = (_clean_text(payload.get("status")) or "active").lower()
    if status not in {"active", "inactive"}:
        raise SourceRegistryError(status_code=422, code="invalid_product_type_status", message="status must be active or inactive.")

    requested_code = _clean_text(payload.get("product_type_code"))
    product_type_code = _slugify_product_type_code(requested_code or display_name)
    existing = connection.execute(
        """
        SELECT product_type_code
        FROM product_type_registry
        WHERE product_type_code = %(product_type_code)s
        """,
        {"product_type_code": product_type_code},
    ).fetchone()
    if existing:
        raise SourceRegistryError(
            status_code=409,
            code="product_type_exists",
            message="A product type with this code already exists.",
        )

    now = utc_now()
    discovery_keywords = _merge_keywords(
        display_name=display_name,
        description=description,
        provided=list(payload.get("discovery_keywords") or []),
        regenerate=True,
    )
    expected_fields = _normalize_string_list(payload.get("expected_fields") or _GENERIC_EXPECTED_FIELDS)
    fallback_policy = "generic_ai_review"
    connection.execute(
        """
        INSERT INTO product_type_registry (
            product_type_code,
            product_family,
            display_name,
            description,
            status,
            built_in_flag,
            managed_flag,
            discovery_keywords,
            expected_fields,
            fallback_policy,
            created_at,
            updated_at
        )
        VALUES (
            %(product_type_code)s,
            'deposit',
            %(display_name)s,
            %(description)s,
            %(status)s,
            false,
            true,
            %(discovery_keywords)s::jsonb,
            %(expected_fields)s::jsonb,
            %(fallback_policy)s,
            %(created_at)s,
            %(updated_at)s
        )
        """,
        {
            "product_type_code": product_type_code,
            "display_name": display_name,
            "description": description,
            "status": status,
            "discovery_keywords": json.dumps(discovery_keywords, ensure_ascii=True),
            "expected_fields": json.dumps(expected_fields, ensure_ascii=True),
            "fallback_policy": fallback_policy,
            "created_at": now,
            "updated_at": now,
        },
    )
    _sync_dynamic_taxonomy_registry(connection, product_type_code=product_type_code, status=status)
    _record_product_type_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="product_type_created",
        target_id=product_type_code,
        diff_summary=f"Created product type `{product_type_code}`.",
        metadata={"product_type_code": product_type_code, "display_name": display_name},
    )
    created = load_product_type_definition(connection, product_type_code=product_type_code)
    if created is None:
        raise SourceRegistryError(status_code=500, code="product_type_missing_after_create", message="Created product type could not be reloaded.")
    return created


def update_product_type_definition(
    connection: Connection,
    *,
    product_type_code: str,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    existing = load_product_type_definition(connection, product_type_code=product_type_code.lower())
    if existing is None:
        raise SourceRegistryError(status_code=404, code="product_type_not_found", message="Product type was not found.")

    display_name = _required_text(payload.get("display_name", existing["display_name"]), "display_name")
    description = _required_text(payload.get("description", existing["description"]), "description")
    status = (_clean_text(payload.get("status", existing["status"])) or "active").lower()
    if status not in {"active", "inactive"}:
        raise SourceRegistryError(status_code=422, code="invalid_product_type_status", message="status must be active or inactive.")

    definition_supplied = "display_name" in payload or "description" in payload
    explicit_keywords = "discovery_keywords" in payload
    discovery_keywords = _merge_keywords(
        display_name=display_name,
        description=description,
        provided=list(payload.get("discovery_keywords") or ([] if definition_supplied else existing["discovery_keywords"])),
        regenerate=explicit_keywords or definition_supplied,
    )
    expected_fields = _normalize_string_list(payload.get("expected_fields") or existing["expected_fields"] or _GENERIC_EXPECTED_FIELDS)
    now = utc_now()
    connection.execute(
        """
        UPDATE product_type_registry
        SET
            display_name = %(display_name)s,
            description = %(description)s,
            status = %(status)s,
            discovery_keywords = %(discovery_keywords)s::jsonb,
            expected_fields = %(expected_fields)s::jsonb,
            updated_at = %(updated_at)s
        WHERE product_type_code = %(product_type_code)s
        """,
        {
            "product_type_code": product_type_code.lower(),
            "display_name": display_name,
            "description": description,
            "status": status,
            "discovery_keywords": json.dumps(discovery_keywords, ensure_ascii=True),
            "expected_fields": json.dumps(expected_fields, ensure_ascii=True),
            "updated_at": now,
        },
    )
    _sync_dynamic_taxonomy_registry(connection, product_type_code=product_type_code.lower(), status=status)
    updated = load_product_type_definition(connection, product_type_code=product_type_code.lower())
    if updated is None:
        raise SourceRegistryError(status_code=500, code="product_type_missing_after_update", message="Updated product type could not be reloaded.")
    _record_product_type_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="product_type_updated",
        target_id=product_type_code.lower(),
        diff_summary=_build_product_type_diff_summary(existing, updated),
        metadata={"product_type_code": product_type_code.lower(), "display_name": display_name},
    )
    return updated


def delete_product_type_definition(
    connection: Connection,
    *,
    product_type_code: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    normalized_code = _required_text(product_type_code, "product_type_code").lower()
    existing = load_product_type_definition(connection, product_type_code=normalized_code)
    if existing is None:
        raise SourceRegistryError(status_code=404, code="product_type_not_found", message="Product type was not found.")

    usage_counts = connection.execute(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM source_registry_catalog_item
                WHERE product_type = %(product_type_code)s
            ) AS catalog_count,
            (
                SELECT COUNT(*)
                FROM source_registry_item
                WHERE product_type = %(product_type_code)s
            ) AS source_count
        """,
        {"product_type_code": normalized_code},
    ).fetchone()
    catalog_count = int((usage_counts or {}).get("catalog_count") or 0)
    source_count = int((usage_counts or {}).get("source_count") or 0)
    if catalog_count > 0 or source_count > 0:
        raise SourceRegistryError(
            status_code=409,
            code="product_type_in_use",
            message="This product type is already attached to bank coverage or generated sources. Remove those references before deleting it.",
        )

    connection.execute(
        """
        DELETE FROM taxonomy_registry
        WHERE country_code = 'CA'
          AND product_family = 'deposit'
          AND product_type = %(product_type_code)s
        """,
        {"product_type_code": normalized_code},
    )
    connection.execute(
        """
        DELETE FROM product_type_registry
        WHERE product_type_code = %(product_type_code)s
        """,
        {"product_type_code": normalized_code},
    )
    _record_product_type_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="product_type_deleted",
        target_id=normalized_code,
        diff_summary=f"Deleted product type `{normalized_code}`.",
        metadata={"product_type_code": normalized_code, "display_name": existing["display_name"]},
    )
    return existing


def _sync_dynamic_taxonomy_registry(connection: Connection, *, product_type_code: str, status: str) -> None:
    if product_type_code in _TAXONOMY_SEEDED_PRODUCT_TYPES:
        return
    now = utc_now()
    connection.execute(
        """
        INSERT INTO taxonomy_registry (
            taxonomy_id,
            country_code,
            product_family,
            product_type,
            subtype_code,
            display_order,
            active_flag,
            notes,
            created_at,
            updated_at
        )
        VALUES (
            %(taxonomy_id)s,
            'CA',
            'deposit',
            %(product_type)s,
            'other',
            999,
            %(active_flag)s,
            'dynamic_product_type_generic_fallback',
            %(created_at)s,
            %(updated_at)s
        )
        ON CONFLICT (country_code, product_family, product_type, subtype_code) DO UPDATE SET
            active_flag = EXCLUDED.active_flag,
            updated_at = EXCLUDED.updated_at,
            notes = EXCLUDED.notes
        """,
        {
            "taxonomy_id": f"tax-{product_type_code}-other",
            "product_type": product_type_code,
            "active_flag": status == "active",
            "created_at": now,
            "updated_at": now,
        },
    )


def _record_product_type_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    event_type: str,
    target_id: str,
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
            'config',
            %(event_type)s,
            %(actor_type)s,
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'product_type_registry',
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
            "event_type": event_type,
            "actor_type": "user",
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
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


def _build_product_type_diff_summary(existing: dict[str, Any], updated: dict[str, Any]) -> str:
    changes: list[str] = []
    for label, key in (("Name", "display_name"), ("Description", "description"), ("Status", "status")):
        if str(existing.get(key) or "") != str(updated.get(key) or ""):
            changes.append(label)
    if list(existing.get("discovery_keywords") or []) != list(updated.get("discovery_keywords") or []):
        changes.append("Discovery keywords")
    if list(existing.get("expected_fields") or []) != list(updated.get("expected_fields") or []):
        changes.append("Expected fields")
    if not changes:
        return f"Updated product type `{existing['product_type_code']}` with no material field changes."
    return f"Updated product type `{existing['product_type_code']}`: {', '.join(changes)}."


def _serialize_product_type_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_type_code": str(row["product_type_code"]),
        "product_family": str(row.get("product_family") or "deposit"),
        "display_name": str(row["display_name"]),
        "description": str(row["description"]),
        "status": str(row["status"]),
        "built_in_flag": bool(row.get("built_in_flag")),
        "managed_flag": bool(row.get("managed_flag", True)),
        "dynamic_onboarding_enabled": not bool(row.get("built_in_flag")),
        "discovery_keywords": _normalize_string_list(row.get("discovery_keywords") or []),
        "expected_fields": _normalize_string_list(row.get("expected_fields") or []),
        "fallback_policy": str(row.get("fallback_policy") or "generic_ai_review"),
        "created_at": _serialize_datetime(row.get("created_at")),
        "updated_at": _serialize_datetime(row.get("updated_at")),
    }


def _required_text(value: Any, field_name: str) -> str:
    normalized = _clean_text(value)
    if not normalized:
        raise SourceRegistryError(status_code=422, code="validation_error", message=f"{field_name} is required.")
    return normalized


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_search(value: str | None) -> str | None:
    normalized = _clean_text(value)
    return normalized.lower() if normalized else None


def _normalize_string_list(values: Any) -> list[str]:
    normalized: list[str] = []
    for item in values or []:
        candidate = _clean_text(item)
        if candidate and candidate not in normalized:
            normalized.append(candidate)
    return normalized


def _slugify_product_type_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise SourceRegistryError(status_code=422, code="invalid_product_type_code", message="A valid product type code could not be derived.")
    return normalized[:50]


def _merge_keywords(*, display_name: str, description: str, provided: list[str], regenerate: bool) -> list[str]:
    if not regenerate:
        return _normalize_existing_keywords(provided)

    candidates = [*_normalize_string_list(provided)]
    ai_keywords = _generate_ai_discovery_keywords(display_name=display_name, description=description, provided=candidates)
    if ai_keywords:
        candidates.extend(ai_keywords)
    else:
        candidates.extend(_generate_heuristic_discovery_keywords(display_name=display_name, description=description))
    return _sanitize_discovery_keywords(candidates, display_name=display_name)


def _generate_ai_discovery_keywords(*, display_name: str, description: str, provided: list[str]) -> list[str]:
    provider = os.getenv("FPDS_LLM_PROVIDER", "openai").strip().lower()
    api_key = os.getenv("FPDS_LLM_API_KEY", "").strip()
    if provider != "openai" or not api_key:
        return []

    payload = {
        "country_code": "CA",
        "product_family": "deposit",
        "display_name": display_name,
        "description": description,
        "operator_seed_keywords": provided,
        "keyword_purpose": (
            "Keywords are used to find and score official public bank pages from URLs, link text, "
            "page titles, headings, and short body excerpts during source discovery."
        ),
    }
    request_body = {
        "model": os.getenv("FPDS_LLM_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini",
        "instructions": (
            "You generate high-quality discovery keywords for FPDS Canadian deposit product types. "
            "Use the product type description plus your financial-domain knowledge. "
            "Return 6 to 12 short keywords or phrases that are likely to appear on official bank pages. "
            "Prefer product-category terms, URL or heading phrases, and useful attribute terms. "
            "Avoid filler words, generic words by themselves, sentence fragments, bank names, and invented product names."
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
                "name": "product_type_discovery_keywords",
                "strict": True,
                "schema": _DISCOVERY_KEYWORD_SCHEMA,
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
        with urllib.request.urlopen(request, timeout=45) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        response_text = _extract_response_output_text(response_payload)
        parsed = json.loads(response_text)
    except (OSError, RuntimeError, json.JSONDecodeError, urllib.error.HTTPError):
        return []
    return [str(item) for item in parsed.get("keywords", []) if str(item).strip()]


def _generate_heuristic_discovery_keywords(*, display_name: str, description: str) -> list[str]:
    text = f"{display_name} {description}".lower()
    candidates: list[str] = [display_name]
    rule_groups: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (
            ("chequing", "checking", "everyday transaction", "debit card", "bill payment", "withdrawal", "transfer"),
            (
                "chequing",
                "checking account",
                "everyday banking",
                "day-to-day banking",
                "transactions",
                "debit card",
                "bill payments",
                "transfers",
                "withdrawals",
                "monthly fee",
            ),
        ),
        (
            ("savings", "save", "interest", "tier", "withdrawal", "high interest"),
            ("savings account", "high interest savings", "interest rate", "tiered interest", "balance", "withdrawals"),
        ),
        (
            ("gic", "term deposit", "guaranteed investment", "maturity", "redeemable", "non-redeemable"),
            ("gic", "guaranteed investment certificate", "term deposit", "maturity", "redeemable", "minimum deposit"),
        ),
        (
            ("tfsa", "tax free", "tax-free"),
            ("tfsa", "tax free savings account", "registered savings"),
        ),
        (
            ("rrsp", "retirement"),
            ("rrsp", "retirement savings", "registered retirement savings"),
        ),
    )
    for triggers, terms in rule_groups:
        if any(trigger in text for trigger in triggers):
            candidates.extend(terms)

    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if token not in _STOPWORDS and len(token) >= 3
    ]
    for size in (3, 2):
        for index in range(0, max(0, len(tokens) - size + 1)):
            candidates.append(" ".join(tokens[index : index + size]))
    candidates.extend(tokens)
    return candidates


def _sanitize_discovery_keywords(values: list[str], *, display_name: str) -> list[str]:
    merged: list[str] = []
    for item in [*values, display_name]:
        normalized = _normalize_keyword(item)
        if not normalized or not _is_useful_discovery_keyword(normalized):
            continue
        if normalized not in merged:
            merged.append(normalized)
        if len(merged) >= _DISCOVERY_KEYWORD_LIMIT:
            break
    return merged


def _normalize_existing_keywords(values: list[str]) -> list[str]:
    merged: list[str] = []
    for item in values:
        normalized = _normalize_keyword(item)
        if not normalized or normalized in merged:
            continue
        merged.append(normalized)
        if len(merged) >= _DISCOVERY_KEYWORD_LIMIT:
            break
    return merged


def _is_useful_discovery_keyword(value: str) -> bool:
    if len(value) < 3 or len(value) > 64:
        return False
    if not re.search(r"[a-z0-9]", value):
        return False
    tokens = re.findall(r"[a-z0-9]+", value)
    if not tokens or len(tokens) > 5:
        return False
    if all(token in _STOPWORDS for token in tokens):
        return False
    if len(tokens) == 1 and tokens[0] in _STOPWORDS:
        return False
    return True


def _normalize_keyword(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"[^a-z0-9&' -]+", " ", value.strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip(" -")
    return normalized or None


def _extract_response_output_text(response_payload: dict[str, Any]) -> str:
    for item in response_payload.get("output", []):
        if str(item.get("type")) != "message":
            continue
        for content in item.get("content", []):
            content_type = str(content.get("type") or "")
            if content_type == "refusal":
                raise RuntimeError(str(content.get("refusal") or "OpenAI refused the product type keyword request."))
            if content_type == "output_text" and content.get("text"):
                return str(content["text"])
    raise RuntimeError("OpenAI product type keyword generator returned no text output.")


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
