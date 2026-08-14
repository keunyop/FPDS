from __future__ import annotations

from datetime import datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, TYPE_CHECKING
import unicodedata
from urllib.parse import urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import path guard for `uv run --directory api/service`
    sys.path.insert(0, str(REPO_ROOT))

from api_service.review_detail import (
    MUTATION_ROLES,
    ReviewTaskError,
    _normalize_override_payload,
)
from api_service.source_registry_utils import normalize_source_url
from api_service.security import new_id, utc_now
from worker.pipeline.fpds_approval_policy import dynamic_repair_fields, is_populated
from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)

if TYPE_CHECKING:
    from psycopg import Connection


AI_VERIFICATION_STAGE = "ai_verification"
AI_VERIFICATION_AGENT = "review_verification_agent"
AI_VERIFICATION_SCHEMA_NAME = "fpds_review_ai_verification"
AI_VERIFICATION_MAX_DOMAINS = 20
AI_VERIFICATION_MAX_FIELDS = 60
AI_VERIFICATION_READ_ONLY_FIELDS = {
    "bank_name",
    "bank_code",
    "country_code",
    "product_family",
    "product_type",
    "source_language",
    "last_verified_at",
    "effective_date",
    "product_id",
    "candidate_id",
    "run_id",
    "review_task_id",
    "currency",
    "source_subtype_label",
    "status",
    "subtype_code",
    "tags",
    "target_customer_tags",
}
AI_VERIFICATION_HARD_BLOCKERS = {
    "ambiguous_product_boundary",
    "invalid_taxonomy_code",
    "invalid_numeric_range",
    "invalid_field_type",
    "invalid_term_value",
    "conflicting_evidence",
    "ambiguous_mapping",
    "inconsistent_cross_field_logic",
}
AI_VERIFICATION_TERMINAL_BLOCKED_STATES = {"rejected"}


class AiVerificationError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def load_latest_ai_verification(
    connection: Connection,
    *,
    review_task_id: str,
    actor_role: str,
    review_state: str | None = None,
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            me.model_execution_id,
            me.model_id,
            me.execution_status,
            me.execution_metadata,
            me.started_at,
            me.completed_at,
            lur.llm_usage_id,
            lur.prompt_tokens,
            lur.completion_tokens,
            lur.estimated_cost,
            lur.recorded_at
        FROM model_execution AS me
        LEFT JOIN llm_usage_record AS lur
          ON lur.model_execution_id = me.model_execution_id
        WHERE me.stage_name = %(stage_name)s
          AND me.execution_metadata ->> 'review_task_id' = %(review_task_id)s
        ORDER BY me.started_at DESC, me.model_execution_id DESC
        LIMIT 1
        """,
        {
            "stage_name": AI_VERIFICATION_STAGE,
            "review_task_id": review_task_id,
        },
    ).fetchone()
    provider_ready = llm_provider_configured()
    can_run = (
        actor_role in MUTATION_ROLES
        and provider_ready
        and str(review_state or "") not in AI_VERIFICATION_TERMINAL_BLOCKED_STATES
    )
    if not row:
        return {
            "status": "ready" if provider_ready else "unavailable",
            "provider_configured": provider_ready,
            "can_run": can_run,
            "latest_attempt": None,
        }

    metadata = _mapping(row.get("execution_metadata"))
    result = _mapping(metadata.get("verification_result"))
    return {
        "status": "completed" if str(row["execution_status"]) == "completed" else "failed",
        "provider_configured": provider_ready,
        "can_run": can_run,
        "latest_attempt": {
            "model_execution_id": str(row["model_execution_id"]),
            "model_id": str(row["model_id"]),
            "execution_status": str(row["execution_status"]),
            "started_at": _iso(row.get("started_at")),
            "completed_at": _iso(row.get("completed_at")),
            "error_message": _string_or_none(metadata.get("error_message")),
            "allowed_domains": _string_list(metadata.get("allowed_domains")),
            "sources": _source_list(metadata.get("sources")),
            "result": result or None,
            "usage": {
                "llm_usage_id": _string_or_none(row.get("llm_usage_id")),
                "prompt_tokens": int(row["prompt_tokens"]) if row.get("prompt_tokens") is not None else None,
                "completion_tokens": int(row["completion_tokens"]) if row.get("completion_tokens") is not None else None,
                "estimated_cost": float(row["estimated_cost"]) if row.get("estimated_cost") is not None else None,
                "recorded_at": _iso(row.get("recorded_at")),
            },
        },
    }


def run_review_ai_verification(
    connection: Connection,
    *,
    detail: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
    invoke_model: Any = invoke_openai_json_schema,
) -> dict[str, Any]:
    actor_role = str(actor.get("role") or "")
    if actor_role not in MUTATION_ROLES:
        raise AiVerificationError(
            status_code=403,
            code="forbidden",
            message="This account cannot run AI verification.",
        )
    review_task = _mapping(detail.get("review_task"))
    candidate = _mapping(detail.get("candidate"))
    review_state = str(review_task.get("review_state") or "")
    if review_state in AI_VERIFICATION_TERMINAL_BLOCKED_STATES:
        raise AiVerificationError(
            status_code=409,
            code="review_task_not_verifiable",
            message="Rejected review tasks cannot run a new AI verification.",
        )
    if not llm_provider_configured():
        raise AiVerificationError(
            status_code=503,
            code="ai_provider_unavailable",
            message="AI verification is unavailable because the OpenAI provider is not configured.",
        )

    allowed_domains = load_registered_bank_domains(
        connection,
        bank_code=str(candidate.get("bank_code") or ""),
        country_code=_string_or_none(candidate.get("country_code")),
        preferred_urls=[
            _string_or_none(_mapping(detail.get("source_context")).get("source_url")),
        ],
    )
    if not allowed_domains:
        raise AiVerificationError(
            status_code=422,
            code="official_domain_unavailable",
            message="No registered official bank domain is available for this candidate.",
        )

    request_payload = build_ai_verification_payload(detail=detail, allowed_domains=allowed_domains)
    identity_evidence = authoritative_identity_evidence(detail)
    requested_field_names = [
        str(item.get("field_name") or "")
        for item in _dict_list(request_payload.get("fields_to_verify"))
        if str(item.get("field_name") or "").strip()
    ]
    field_evidence = authoritative_field_evidence(
        detail,
        field_names=requested_field_names,
        allowed_domains=allowed_domains,
    )
    model_execution_id = new_id("modelexec")
    model_id = configured_model_id()
    started_at = utc_now()
    execution_metadata = {
        "review_task_id": str(review_task.get("review_task_id") or ""),
        "candidate_id": str(review_task.get("candidate_id") or ""),
        "requested_by_user_id": _string_or_none(actor.get("user_id")),
        "allowed_domains": allowed_domains,
        "verification_contract_version": "review-ai-verification-v17",
        "requested_field_names": requested_field_names,
        "approval_field_names": requested_field_names,
        "requested_field_count": len(requested_field_names),
        "hard_blocking_issue_codes": sorted(
            AI_VERIFICATION_HARD_BLOCKERS.intersection(
                _string_list(candidate.get("validation_issue_codes"))
            )
        ),
        "authoritative_identity_evidence": identity_evidence,
        "authoritative_field_evidence": field_evidence,
    }
    _insert_model_execution(
        connection,
        model_execution_id=model_execution_id,
        run_id=str(review_task.get("run_id") or ""),
        source_document_id=_string_or_none(candidate.get("source_document_id")),
        model_id=model_id,
        execution_metadata=execution_metadata,
        started_at=started_at,
    )

    try:
        raw_result, provider_metadata = invoke_model(
            instructions=_verification_instructions(),
            payload=request_payload,
            schema_name=AI_VERIFICATION_SCHEMA_NAME,
            schema=AI_VERIFICATION_SCHEMA,
            model_id=model_id,
            web_search_allowed_domains=allowed_domains,
            require_web_search=True,
        )
        sources = _filter_sources_to_allowed_domains(
            _source_list(provider_metadata.get("web_search_sources")),
            allowed_domains=allowed_domains,
        )
        verification_result = sanitize_ai_verification_result(
            raw_result=raw_result,
            detail=detail,
            sources=sources,
            allowed_domains=allowed_domains,
        )
    except Exception as exc:
        error_message = _safe_provider_error(exc)
        completed_at = utc_now()
        failed_metadata = {
            **execution_metadata,
            "error_message": error_message,
            "failure_type": type(exc).__name__,
        }
        _complete_model_execution(
            connection,
            model_execution_id=model_execution_id,
            execution_status="failed",
            execution_metadata=failed_metadata,
            completed_at=completed_at,
        )
        _record_verification_audit(
            connection,
            event_type="review_ai_verification_failed",
            actor=actor,
            review_task=review_task,
            request_context=request_context,
            model_execution_id=model_execution_id,
            reason_text=error_message,
            result=None,
            sources=[],
            allowed_domains=allowed_domains,
        )
        return {
            "ok": False,
            "status_code": 502,
            "error": {
                "code": "ai_verification_failed",
                "message": error_message,
            },
            "ai_verification": load_latest_ai_verification(
                connection,
                review_task_id=str(review_task.get("review_task_id") or ""),
                actor_role=actor_role,
                review_state=review_state,
            ),
        }

    completed_at = utc_now()
    prompt_tokens = int(provider_metadata.get("prompt_tokens") or 0)
    completion_tokens = int(provider_metadata.get("completion_tokens") or 0)
    provider_request_id = _string_or_none(provider_metadata.get("provider_request_id"))
    completed_metadata = {
        **execution_metadata,
        "provider": str(provider_metadata.get("provider") or "openai"),
        "provider_request_id": provider_request_id,
        "sources": sources,
        "verification_result": verification_result,
    }
    _complete_model_execution(
        connection,
        model_execution_id=model_execution_id,
        execution_status="completed",
        execution_metadata=completed_metadata,
        completed_at=completed_at,
    )
    _insert_usage_record(
        connection,
        model_execution_id=model_execution_id,
        run_id=str(review_task.get("run_id") or ""),
        candidate_id=_string_or_none(review_task.get("candidate_id")),
        provider_request_id=provider_request_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model_id=str(provider_metadata.get("model_id") or model_id),
        recorded_at=completed_at,
    )
    _record_verification_audit(
        connection,
        event_type="review_ai_verification_completed",
        actor=actor,
        review_task=review_task,
        request_context=request_context,
        model_execution_id=model_execution_id,
        reason_text=str(verification_result.get("summary") or ""),
        result=verification_result,
        sources=sources,
        allowed_domains=allowed_domains,
    )
    return {
        "ok": True,
        "status_code": 200,
        "ai_verification": load_latest_ai_verification(
            connection,
            review_task_id=str(review_task.get("review_task_id") or ""),
            actor_role=actor_role,
            review_state=review_state,
        ),
    }


def load_registered_bank_domains(
    connection: Connection,
    *,
    bank_code: str,
    country_code: str | None = None,
    preferred_urls: list[str | None] | None = None,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT source_url
        FROM (
            SELECT 0 AS source_order, homepage_url AS source_url
            FROM bank
            WHERE bank_code = %(bank_code)s
              AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s::text)
            UNION ALL
            SELECT 1 AS source_order, normalized_url AS source_url
            FROM source_registry_item
            WHERE bank_code = %(bank_code)s
              AND (%(country_code)s::text IS NULL OR country_code = %(country_code)s::text)
              AND status = 'active'
        ) AS official_sources
        WHERE source_url IS NOT NULL
        ORDER BY source_order, source_url
        """,
        {"bank_code": bank_code, "country_code": country_code},
    ).fetchall()
    registered_domains = normalize_official_domains(
        [str(row["source_url"]) for row in rows if row.get("source_url")]
    )
    preferred_domains = normalize_official_domains(
        [value for value in (preferred_urls or []) if value]
    )
    ordered_domains = [
        *[domain for domain in preferred_domains if domain in registered_domains],
        *registered_domains,
    ]
    return list(dict.fromkeys(ordered_domains))[:AI_VERIFICATION_MAX_DOMAINS]


def normalize_official_domains(urls: list[str]) -> list[str]:
    domains: list[str] = []
    seen: set[str] = set()
    for value in urls:
        raw = str(value).strip()
        if not raw:
            continue
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        host = (parsed.hostname or "").strip(".").lower()
        if host.startswith("www."):
            host = host[4:]
        if not host or host in seen or host == "localhost":
            continue
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            continue
        if "." not in host:
            continue
        seen.add(host)
        domains.append(host)
    return domains


def build_ai_verification_payload(*, detail: dict[str, Any], allowed_domains: list[str]) -> dict[str, Any]:
    review_task = _mapping(detail.get("review_task"))
    candidate = _mapping(detail.get("candidate"))
    source_context = _mapping(detail.get("source_context"))
    product_name_item = next(
        (
            item
            for item in _dict_list(detail.get("review_field_items"))
            if str(item.get("field_name") or "").strip() == "product_name"
        ),
        {},
    )
    review_fields = [
        {
            "field_name": "product_name",
            "label": str(product_name_item.get("label") or "Product Name"),
            "collected_value": candidate.get("product_name"),
            "missing": not bool(str(candidate.get("product_name") or "").strip()),
            "suspect": bool(product_name_item.get("suspect")),
            "issue_codes": _string_list(product_name_item.get("issue_codes")),
            "field_note": _string_or_none(product_name_item.get("field_note")),
        }
    ]
    seen_fields = {"product_name"}
    review_field_items = _dict_list(detail.get("review_field_items"))
    expected_fields = _string_list(source_context.get("expected_fields"))
    candidate_payload = _mapping(candidate.get("candidate_payload"))
    product_type = str(candidate.get("product_type") or "")
    essential_fields = dynamic_repair_fields(
        product_type=product_type,
        country_code=str(candidate.get("country_code") or ""),
        expected_fields=expected_fields,
        candidate_payload=candidate_payload,
    )
    essential_field_set = set(essential_fields)
    for item in review_field_items[:AI_VERIFICATION_MAX_FIELDS]:
        field_name = str(item.get("field_name") or "").strip()
        if (
            not field_name
            or field_name in seen_fields
            or field_name in AI_VERIFICATION_READ_ONLY_FIELDS
        ):
            continue
        effective_value = item.get("effective_value")
        approval_relevant = field_name in essential_field_set
        if not approval_relevant:
            continue
        seen_fields.add(field_name)
        review_fields.append(
            {
                "field_name": field_name,
                "label": str(item.get("label") or field_name),
                "collected_value": item.get("effective_value"),
                "missing": bool(item.get("missing"))
                or (field_name in essential_field_set and not is_populated(item.get("effective_value"))),
                "suspect": bool(item.get("suspect")),
                "issue_codes": _string_list(item.get("issue_codes")),
                "field_note": _string_or_none(item.get("field_note")),
            }
        )
    for field_name in essential_fields:
        if field_name in seen_fields or field_name in AI_VERIFICATION_READ_ONLY_FIELDS:
            continue
        seen_fields.add(field_name)
        review_fields.append(
            {
                "field_name": field_name,
                "label": _field_label(detail=detail, field_name=field_name),
                "collected_value": candidate_payload.get(field_name),
                "missing": not is_populated(candidate_payload.get(field_name)),
                "suspect": False,
                "issue_codes": ["required_field_missing"],
                "field_note": "Required for essential-field publication.",
            }
        )
    return {
        "verification_date": utc_now().date().isoformat(),
        "official_domain_allowlist": allowed_domains,
        "review_task": {
            "review_task_id": str(review_task.get("review_task_id") or ""),
            "queue_reason_code": str(review_task.get("queue_reason_code") or ""),
            "issue_summary": str(review_task.get("issue_summary") or ""),
        },
        "product": {
            "bank_code": str(candidate.get("bank_code") or ""),
            "bank_name": str(candidate.get("bank_name") or ""),
            "country_code": str(candidate.get("country_code") or ""),
            "product_family": str(candidate.get("product_family") or ""),
            "product_type": str(candidate.get("product_type") or ""),
            "product_name": str(candidate.get("product_name") or ""),
            "currency": str(candidate.get("currency") or ""),
            "origin_source_url": _string_or_none(source_context.get("source_url")),
            "authoritative_identity_evidence": authoritative_identity_evidence(detail),
        },
        "fields_to_verify": review_fields[:AI_VERIFICATION_MAX_FIELDS],
        "approval_policy": {
            "contract_version": "review-ai-verification-v17",
            "rule": "official product identity plus every product-type essential field",
            "empty_requested_fields_block_approval": True,
        },
        "collected_candidate_payload": candidate_payload,
    }


def authoritative_identity_evidence(detail: dict[str, Any]) -> dict[str, Any]:
    """Verify identity from an exact official detail-page H1 match."""

    candidate = _mapping(detail.get("candidate"))
    source_context = _mapping(detail.get("source_context"))
    discovery = _mapping(source_context.get("discovery_assessment"))
    product_name = str(candidate.get("product_name") or "").strip()
    primary_heading = str(discovery.get("primary_heading") or "").strip()
    product_type = str(candidate.get("product_type") or "").strip().lower()
    normalized_name = _normalize_identity_text(product_name)
    normalized_heading = _normalize_identity_text(primary_heading)
    exact_identity_match = normalized_name == normalized_heading
    descriptor_identity_match = _identity_differs_only_by_product_descriptor(
        normalized_name,
        normalized_heading,
        product_type=product_type,
    )
    cross_product_boundary = (
        product_type in {"chequing", "savings"}
        and any(token in normalized_name for token in ("checking", "chequing"))
        and "savings" in normalized_name
    )
    verified = bool(
        source_context.get("discovery_role") == "detail"
        and discovery.get("product_identity_match") is True
        and normalized_name
        and (exact_identity_match or descriptor_identity_match)
        and not cross_product_boundary
    )
    return {
        "verified": verified,
        "basis": (
            "exact_official_detail_h1"
            if verified and exact_identity_match
            else "official_detail_h1_product_descriptor_equivalent"
            if verified
            else None
        ),
        "candidate_value": product_name or None,
        "primary_heading": primary_heading or None,
        "source_url": _string_or_none(source_context.get("source_url")),
        "cross_product_boundary": cross_product_boundary,
    }


def _identity_differs_only_by_product_descriptor(
    normalized_name: str,
    normalized_heading: str,
    *,
    product_type: str,
) -> bool:
    if not normalized_name or not normalized_heading or normalized_name == normalized_heading:
        return False
    descriptor_by_type = {
        "chequing": ("chequing account", "checking account"),
        "savings": ("savings account",),
        "gic": ("guaranteed investment certificate", "certificate of deposit", "gic", "cd"),
        "credit-card": ("credit card", "card"),
        "mortgage": ("mortgage",),
        "line-of-credit": ("line of credit", "credit line", "heloc"),
        "personal-loan": ("personal loan",),
        "auto-loan": ("auto loan", "vehicle loan", "car loan"),
        "student-loan": ("student loan",),
        "business-loan": ("business loan",),
        "home-equity-loan": ("home equity loan",),
    }
    for descriptor in descriptor_by_type.get(product_type, (product_type.replace("-", " "),)):
        for shorter, longer in (
            (normalized_heading, normalized_name),
            (normalized_name, normalized_heading),
        ):
            if len(shorter.split()) >= 2 and longer == f"{shorter} {descriptor}":
                return True
    return False


def authoritative_field_evidence(
    detail: dict[str, Any],
    *,
    field_names: list[str],
    allowed_domains: list[str],
) -> dict[str, dict[str, Any]]:
    """Return persisted exact-origin comparison evidence safe after AI abstains."""

    candidate = _mapping(detail.get("candidate"))
    candidate_payload = _mapping(candidate.get("candidate_payload"))
    mappings = _mapping(candidate.get("field_mapping_metadata"))
    product_type = str(candidate.get("product_type") or "").strip().lower().replace("_", "-")
    lending_origin_fields = {
        "mortgage": {"interest_rate_summary", "term_length_text", "rate_type"},
        "personal-loan": {"interest_rate_summary", "loan_amount_text", "term_length_text"},
        "line-of-credit": {"interest_rate_summary", "credit_limit_text"},
    }
    evidence: dict[str, dict[str, Any]] = {}
    for field_name in dict.fromkeys(field_names):
        if field_name == "product_name" or field_name not in candidate_payload:
            continue
        metadata = _mapping(mappings.get(field_name))
        grounding_method = str(metadata.get("official_grounding_method") or "")
        exact_fee = grounding_method == "deterministic_labeled_origin"
        exact_lending_fact = (
            grounding_method == "deterministic_lending_comparison_origin"
            and field_name in lending_origin_fields.get(product_type, set())
            and (
                field_name != "interest_rate_summary"
                or "%" in str(candidate_payload.get(field_name) or "")
            )
        )
        sources = [
            source
            for source in _source_list(metadata.get("official_web_sources"))
            if _url_matches_allowed_domains(
                str(source.get("url") or ""),
                allowed_domains=allowed_domains,
            )
        ]
        if (
            metadata.get("official_grounding_contract_version") != "collection-official-grounding-v2"
            or not (exact_fee or exact_lending_fact)
            or metadata.get("official_verification_status") != "match"
            or not str(metadata.get("official_evidence_quote") or "").strip()
            or not sources
            or metadata.get("normalized_value") != candidate_payload.get(field_name)
        ):
            continue
        source = sources[0]
        evidence[field_name] = {
            "verified": True,
            "basis": (
                "exact_official_detail_lending_comparison"
                if exact_lending_fact
                else "exact_official_detail_labeled_fee"
            ),
            "candidate_value": candidate_payload.get(field_name),
            "source_url": str(source.get("url") or ""),
            "source_title": str(source.get("title") or source.get("url") or ""),
            "evidence_quote": str(metadata.get("official_evidence_quote") or "")[:500],
        }
    return evidence


def _normalize_identity_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(
        "".join(character if character.isalnum() else " " for character in normalized).split()
    )


def sanitize_ai_verification_result(
    *,
    raw_result: dict[str, Any],
    detail: dict[str, Any],
    sources: list[dict[str, str]],
    allowed_domains: list[str],
) -> dict[str, Any]:
    candidate = _mapping(detail.get("candidate"))
    base_payload = {
        **_mapping(candidate.get("candidate_payload")),
        "product_name": candidate.get("product_name"),
        "currency": candidate.get("currency"),
        "subtype_code": candidate.get("subtype_code"),
    }
    editable_fields = {
        str(item.get("field_name") or "").strip()
        for item in _dict_list(detail.get("review_field_items"))
        if str(item.get("field_name") or "").strip()
    }
    editable_fields.add("product_name")
    editable_fields -= AI_VERIFICATION_READ_ONLY_FIELDS
    source_by_url = {item["url"]: item for item in sources}
    sanitized_fields: list[dict[str, Any]] = []
    proposed_corrections: dict[str, Any] = {}
    seen_fields: set[str] = set()

    for item in _dict_list(raw_result.get("fields"))[:AI_VERIFICATION_MAX_FIELDS]:
        field_name = str(item.get("field_name") or "").strip()
        if not field_name or field_name in seen_fields or field_name not in editable_fields:
            continue
        seen_fields.add(field_name)
        status = str(item.get("status") or "unverified")
        if status not in {"match", "mismatch", "unverified"}:
            status = "unverified"
        cited_sources = []
        for source in _source_list(item.get("sources"))[:5]:
            url = _canonical_source_url(source.get("url"))
            matched = source_by_url.get(url)
            if matched and _url_matches_allowed_domains(url, allowed_domains=allowed_domains):
                cited_sources.append(matched)
        cited_sources = _dedupe_sources(cited_sources)
        collected_value = base_payload.get(field_name)
        verified_value: Any = None
        evidence_quote = _compact_text(item.get("evidence_quote"), limit=700)
        has_verified_value = bool(item.get("has_verified_value"))
        if has_verified_value:
            try:
                verified_value = json.loads(str(item.get("verified_value_json") or ""))
            except (json.JSONDecodeError, TypeError, ValueError):
                status = "unverified"
                has_verified_value = False
            if not is_populated(verified_value):
                status = "unverified"
                has_verified_value = False
        if cited_sources and (
            collected_value in (None, "") or field_name == "purchase_interest_rate_summary"
        ):
            derived_value = _derive_missing_exact_product_value(
                detail=detail,
                field_name=field_name,
                evidence_quote=evidence_quote,
                cited_sources=cited_sources,
            )
            if derived_value is not None:
                verified_value = derived_value
                has_verified_value = True
                status = "mismatch"
        if status in {"match", "mismatch"} and (
            not cited_sources
            or not has_verified_value
            or not _verification_evidence_is_exact_product(
                detail=detail,
                field_name=field_name,
                verified_value=verified_value,
                evidence_quote=evidence_quote,
                cited_sources=cited_sources,
            )
        ):
            status = "unverified"
            has_verified_value = False

        proposed_value: Any = None
        can_apply = False
        validation_note: str | None = None
        if status in {"match", "mismatch"} and has_verified_value:
            try:
                normalized = _normalize_override_payload(
                    override_payload={field_name: verified_value},
                    base_payload=base_payload,
                )
                if field_name in normalized:
                    status = "mismatch"
                    proposed_value = normalized[field_name]
                    proposed_corrections[field_name] = proposed_value
                    can_apply = True
                else:
                    status = "match"
            except ReviewTaskError as exc:
                validation_note = exc.message
                if status == "match":
                    status = "unverified"

        sanitized_fields.append(
            {
                "field_name": field_name,
                "label": _field_label(detail=detail, field_name=field_name),
                "status": status,
                "collected_value": collected_value,
                "verified_value": verified_value if has_verified_value else None,
                "confidence": _confidence(item.get("confidence")),
                "rationale": _compact_text(item.get("rationale"), limit=600),
                "evidence_quote": evidence_quote,
                "sources": cited_sources,
                "can_apply": can_apply,
                "proposed_value": proposed_value,
                "validation_note": validation_note,
            }
        )

    status_counts = {
        "match": sum(1 for item in sanitized_fields if item["status"] == "match"),
        "mismatch": sum(1 for item in sanitized_fields if item["status"] == "mismatch"),
        "unverified": sum(1 for item in sanitized_fields if item["status"] == "unverified"),
    }
    if not sources or not sanitized_fields:
        overall_status = "unable"
    elif status_counts["mismatch"] > 0:
        overall_status = "differences_found"
    elif status_counts["unverified"] > 0:
        overall_status = "partial"
    else:
        overall_status = "verified"
    return {
        "overall_status": overall_status,
        "summary": _compact_text(raw_result.get("summary"), limit=800),
        "verified_at": utc_now().isoformat(),
        "status_counts": status_counts,
        "fields": sanitized_fields,
        "proposed_corrections": proposed_corrections,
        "source_count": len(sources),
    }


def _derive_missing_exact_product_value(
    *,
    detail: dict[str, Any],
    field_name: str,
    evidence_quote: str,
    cited_sources: list[dict[str, str]],
) -> Any:
    """Recover two bounded US card facts when the model omitted its JSON flag.

    This is intentionally narrower than normal AI correction: the citation
    must be the candidate's exact official detail URL and the exact quote must
    contain the complete labeled value. No neighboring catalog or generic fee
    page can supply a value through this fallback.
    """

    candidate = _mapping(detail.get("candidate"))
    if (
        str(candidate.get("country_code") or "").upper() != "US"
        or str(candidate.get("product_type") or "").lower() != "credit-card"
    ):
        return None
    exact_origin_url = _source_identity_url(_mapping(detail.get("source_context")).get("source_url"))
    cites_exact_origin = bool(
        exact_origin_url
        and any(
            _source_identity_url(source.get("url")) == exact_origin_url
            for source in cited_sources
        )
    )
    normalized_product = _normalize_identity_text(str(candidate.get("product_name") or ""))
    normalized_quote = _normalize_identity_text(evidence_quote)
    cites_named_product_companion = bool(
        normalized_product
        and normalized_product in normalized_quote
        and any(
            re.search(
                r"(?:agreement|disclosure|pricing|terms|/content/documents/creditcard/)",
                str(source.get("url") or ""),
                re.IGNORECASE,
            )
            for source in cited_sources
        )
    )
    if not (cites_exact_origin or cites_named_product_companion):
        return None
    compact_quote = _compact_text(evidence_quote, limit=1400)
    lowered_quote = compact_quote.casefold()
    if not compact_quote or "..." in compact_quote:
        return None
    if field_name == "annual_fee":
        if candidate.get("candidate_payload") and _mapping(candidate.get("candidate_payload")).get(field_name) not in (None, ""):
            return None
        if re.search(r"\bannual\s+fee\b\s*(?:is\s*)?\$\s*0(?:\.0+)?\b", lowered_quote):
            return 0.0
        if re.search(r"\bno\s+annual\s+fee\b", lowered_quote):
            return 0.0
        return None
    if field_name != "purchase_interest_rate_summary":
        return None
    if not re.search(r"\b(?:intro(?:ductory)?\s+)?apr\b", lowered_quote):
        return None
    percentage_values = re.findall(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%", compact_quote)
    intro_range = bool(
        len(percentage_values) >= 3
        and "purchase" in lowered_quote
        and re.search(r"\b(?:billing\s+cycles?|months?|days?)\b", lowered_quote)
        and re.search(r"\b(?:variable\s+apr|apr\s+range|apr\b[^.]{0,100}\bto\b)\b", lowered_quote)
    )
    prime_formula = bool(
        len(percentage_values) >= 4
        and re.search(r"\bapr\b[^\n]{0,30}\bfor\s+purchases\b", lowered_quote)
        and "prime rate" in lowered_quote
        and re.search(r"\bas\s+of\s+\d{1,2}/\d{1,2}/\d{4}\b", lowered_quote)
        and re.search(r"\bprime\s*\+\s*\d", lowered_quote)
    )
    if not (intro_range or prime_formula):
        return None
    return compact_quote


def _verification_evidence_is_exact_product(
    *,
    detail: dict[str, Any],
    field_name: str,
    verified_value: Any,
    evidence_quote: str,
    cited_sources: list[dict[str, str]],
) -> bool:
    """Reject same-bank citations that do not establish the exact product fact."""

    if not evidence_quote or "..." in evidence_quote or "…" in evidence_quote:
        return False
    candidate = _mapping(detail.get("candidate"))
    expected_product = (
        str(verified_value or "")
        if field_name == "product_name"
        else str(candidate.get("product_name") or "")
    )
    normalized_product = _normalize_identity_text(expected_product)
    normalized_quote = _normalize_identity_text(evidence_quote)
    quote_names_product = bool(normalized_product and normalized_product in normalized_quote)
    exact_origin_url = _source_identity_url(
        _mapping(detail.get("source_context")).get("source_url")
    )
    from api_service.source_catalog import _source_scope_exclusion_reason

    product_type = str(candidate.get("product_type") or "")
    compatible_sources = [
        source
        for source in cited_sources
        if _source_identity_url(source.get("url")) == exact_origin_url
        or (
            quote_names_product
            and re.search(
                r"(?:agreement|disclosure|pricing|terms|/content/documents/creditcard/)",
                str(source.get("url") or ""),
                re.IGNORECASE,
            )
        )
        or not _source_scope_exclusion_reason(
            product_type=product_type,
            fingerprint=f"{source.get('url') or ''} {source.get('title') or ''}".lower(),
        )
    ]
    if not compatible_sources:
        return False
    cites_exact_origin = bool(
        exact_origin_url
        and any(
            _source_identity_url(source.get("url")) == exact_origin_url
            for source in compatible_sources
        )
    )
    if field_name == "product_name":
        return quote_names_product
    if not (quote_names_product or cites_exact_origin):
        return False

    if field_name in {
        "early_withdrawal_penalty",
        "fee_waiver_condition",
        "interest_rate_summary",
        "security_requirement",
    }:
        normalized_value = _compact_text(verified_value, limit=2000)
        normalized_quote_text = _compact_text(evidence_quote, limit=2000)
        if not normalized_value or normalized_value.casefold() not in normalized_quote_text.casefold():
            return False

    if field_name == "annual_fee" and str(verified_value).strip() in {"0", "0.0"}:
        if re.search(r"\bno\s+annual\s+fee\b", evidence_quote, re.IGNORECASE):
            return True

    numeric_tokens = re.findall(r"\d+(?:\.\d+)?", str(verified_value).replace(",", ""))
    if not numeric_tokens:
        return True
    normalized_financial_quote = evidence_quote.replace(",", "")
    return all(
        re.search(
            rf"(?<!\d){re.escape(token.rstrip('0').rstrip('.') if '.' in token else token)}(?:\.0+)?(?!\d)",
            normalized_financial_quote,
        )
        for token in numeric_tokens
    )


def _insert_model_execution(
    connection: Connection,
    *,
    model_execution_id: str,
    run_id: str,
    source_document_id: str | None,
    model_id: str,
    execution_metadata: dict[str, Any],
    started_at: datetime,
) -> None:
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
            'started',
            %(execution_metadata)s::jsonb,
            %(started_at)s,
            NULL
        )
        """,
        {
            "model_execution_id": model_execution_id,
            "run_id": run_id,
            "source_document_id": source_document_id,
            "stage_name": AI_VERIFICATION_STAGE,
            "agent_name": AI_VERIFICATION_AGENT,
            "model_id": model_id,
            "execution_metadata": json.dumps(execution_metadata, ensure_ascii=True),
            "started_at": started_at,
        },
    )


def _complete_model_execution(
    connection: Connection,
    *,
    model_execution_id: str,
    execution_status: str,
    execution_metadata: dict[str, Any],
    completed_at: datetime,
) -> None:
    connection.execute(
        """
        UPDATE model_execution
        SET
            execution_status = %(execution_status)s,
            execution_metadata = %(execution_metadata)s::jsonb,
            completed_at = %(completed_at)s
        WHERE model_execution_id = %(model_execution_id)s
        """,
        {
            "model_execution_id": model_execution_id,
            "execution_status": execution_status,
            "execution_metadata": json.dumps(execution_metadata, ensure_ascii=True),
            "completed_at": completed_at,
        },
    )


def _insert_usage_record(
    connection: Connection,
    *,
    model_execution_id: str,
    run_id: str,
    candidate_id: str | None,
    provider_request_id: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    model_id: str,
    recorded_at: datetime,
) -> None:
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
            "llm_usage_id": new_id("llmusage"),
            "model_execution_id": model_execution_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "provider_request_id": provider_request_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost": estimated_cost_usd(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
            "usage_metadata": json.dumps(
                {
                    "provider": "openai",
                    "model_id": model_id,
                    "stage_name": AI_VERIFICATION_STAGE,
                    "usage_mode": "live_web_verification",
                },
                ensure_ascii=True,
            ),
            "recorded_at": recorded_at,
        },
    )


def _record_verification_audit(
    connection: Connection,
    *,
    event_type: str,
    actor: dict[str, Any],
    review_task: dict[str, Any],
    request_context: dict[str, Any],
    model_execution_id: str,
    reason_text: str,
    result: dict[str, Any] | None,
    sources: list[dict[str, str]],
    allowed_domains: list[str],
) -> None:
    proposed_fields = sorted(_mapping((result or {}).get("proposed_corrections")).keys())
    actor_type = str(actor.get("actor_type") or "user")
    if actor_type not in {"system", "user", "service", "scheduler"}:
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
            previous_state,
            new_state,
            reason_code,
            reason_text,
            run_id,
            candidate_id,
            review_task_id,
            product_id,
            request_id,
            diff_summary,
            source_ref,
            ip_address,
            user_agent,
            retention_class,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            %(event_type)s,
            %(actor_type)s,
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'review_task',
            %(target_id)s,
            %(review_state)s,
            %(review_state)s,
            'ai_verification',
            %(reason_text)s,
            %(run_id)s,
            %(candidate_id)s,
            %(review_task_id)s,
            %(product_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(source_ref)s,
            %(ip_address)s,
            %(user_agent)s,
            'hot',
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "event_type": event_type,
            "actor_type": actor_type,
            "actor_id": _string_or_none(actor.get("user_id")),
            "actor_role_snapshot": _string_or_none(actor.get("role")),
            "target_id": str(review_task.get("review_task_id") or ""),
            "review_state": _string_or_none(review_task.get("review_state")),
            "reason_text": _compact_text(reason_text, limit=2000),
            "run_id": _string_or_none(review_task.get("run_id")),
            "candidate_id": _string_or_none(review_task.get("candidate_id")),
            "review_task_id": _string_or_none(review_task.get("review_task_id")),
            "product_id": _string_or_none(review_task.get("product_id")),
            "request_id": _string_or_none(request_context.get("request_id")),
            "diff_summary": ", ".join(proposed_fields) if proposed_fields else None,
            "source_ref": sources[0]["url"] if sources else None,
            "ip_address": _string_or_none(request_context.get("ip_address")),
            "user_agent": _string_or_none(request_context.get("user_agent")),
            "event_payload": json.dumps(
                {
                    "model_execution_id": model_execution_id,
                    "overall_status": (result or {}).get("overall_status"),
                    "proposed_fields": proposed_fields,
                    "allowed_domains": allowed_domains,
                    "source_count": len(sources),
                    "sources": sources,
                },
                ensure_ascii=True,
            ),
            "occurred_at": utc_now(),
        },
    )


def _verification_instructions() -> str:
    return (
        "You are the FPDS financial-product verification agent. You must use web search before answering. "
        "Search only the supplied official bank domain allowlist and verify the exact named product, not a "
        "neighboring product, family overview, promotion landing page, calculator, or service flow. Compare "
        "each requested approval field with current official facts. A requested empty field is a mandatory repair target, not "
        "an optional omission. Never infer a missing value. Mark a field "
        "unverified when the exact current fact is absent, ambiguous, personalized, dynamic, expired, or belongs "
        "to another product. Preserve canonical units: rates are numeric percentage points per annum, money is "
        "numeric in product currency, durations/counts are integers, booleans are true/false, and structured "
        "term rates are JSON arrays. For interest_rate_summary, preserve a current official APR/rate range, reference-rate "
        "formula, or representative example together with its disclosed term, credit, discount, date, and other assumptions; "
        "when a discount affects the displayed rate, include its qualifying account, automatic-payment, relationship, and "
        "existing-customer conditions; "
        "for a conditional deposit APY, include new-customer eligibility, qualifying balance and timing, fallback-rate "
        "outcome, as-of date, and variability when disclosed; "
        "do not force a range or conditional example into one scalar rate. Put a JSON-encoded canonical value in "
        "verified_value_json only when the "
        "official source states it directly. Every match or mismatch must cite at least one official source URL "
        "actually consulted and copy a short exact evidence_quote from that source. The quote must name the exact "
        "product when the source is a separate rate/fee/disclosure page. Evidence quotes must be contiguous verbatim text: "
        "never insert ellipses or combine non-adjacent fragments. Keep rationale concise and operational. "
        "For an empty requested field, return mismatch with has_verified_value=true when the official source states "
        "the value; empty does not mean unverified. For annual_fee, an exact '$0' or 'no annual fee' statement is the "
        "canonical numeric value 0. For purchase_interest_rate_summary, return one concise source-language string that "
        "preserves the introductory purchase APR and period, followed by the standard variable APR range and any stated "
        "creditworthiness or Prime Rate qualification. Do not require an as-of date when the issuer does not disclose one. "
        "Put each field's consulted official URL in that field's sources array, even if another field cites the same URL. "
        "When a collected purchase_interest_rate_summary is incomplete or overstates the source, return mismatch with a "
        "corrected verified value whenever the exact product agreement states the complete current purchase APR. In that "
        "case the contiguous quote must include 'APR for Purchases', the Prime Rate formula, its as-of date, and the APR range. "
        "Do not approve, publish, or recommend a "
        "financial product."
    )


AI_VERIFICATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_status": {
            "type": "string",
            "enum": ["verified", "differences_found", "partial", "unable"],
        },
        "summary": {"type": "string"},
        "fields": {
            "type": "array",
            "maxItems": AI_VERIFICATION_MAX_FIELDS,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "field_name": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["match", "mismatch", "unverified"],
                    },
                    "has_verified_value": {"type": "boolean"},
                    "verified_value_json": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "rationale": {"type": "string"},
                    "evidence_quote": {"type": "string"},
                    "sources": {
                        "type": "array",
                        "maxItems": 5,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                            },
                            "required": ["url", "title"],
                        },
                    },
                },
                "required": [
                    "field_name",
                    "status",
                    "has_verified_value",
                    "verified_value_json",
                    "confidence",
                    "rationale",
                    "evidence_quote",
                    "sources",
                ],
            },
        },
    },
    "required": ["overall_status", "summary", "fields"],
}


def _filter_sources_to_allowed_domains(
    sources: list[dict[str, str]],
    *,
    allowed_domains: list[str],
) -> list[dict[str, str]]:
    filtered = []
    for source in sources:
        url = _canonical_source_url(source.get("url"))
        if not url or not _url_matches_allowed_domains(url, allowed_domains=allowed_domains):
            continue
        filtered.append(
            {
                "url": url,
                "title": _compact_text(source.get("title") or url, limit=300),
            }
        )
    return _dedupe_sources(filtered)[:100]


def _url_matches_allowed_domains(url: str, *, allowed_domains: list[str]) -> bool:
    host = (urlsplit(url).hostname or "").lower().strip(".")
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def _canonical_source_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def _source_identity_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return normalize_source_url(raw)
    except ValueError:
        return _canonical_source_url(raw)


def _field_label(*, detail: dict[str, Any], field_name: str) -> str:
    for item in _dict_list(detail.get("review_field_items")):
        if str(item.get("field_name") or "") == field_name:
            return str(item.get("label") or field_name.replace("_", " ").title())
    return field_name.replace("_", " ").title()


def _safe_provider_error(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    if not message:
        return "AI verification failed before a result was returned."
    if "API key" in message or "Authorization" in message:
        return "AI verification provider authentication failed. Check the configured API credential."
    if "status 429" in message:
        return "AI verification is temporarily rate limited. Try again later."
    if "timed out" in message.lower() or "timeout" in message.lower():
        return "AI verification timed out before official-source comparison completed."
    return _compact_text(message, limit=700)


def _dedupe_sources(sources: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    seen: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        output.append({"url": url, "title": str(source.get("title") or url)})
    return output


def _source_list(value: Any) -> list[dict[str, str]]:
    return [
        {
            "url": str(item.get("url") or ""),
            "title": str(item.get("title") or item.get("url") or ""),
        }
        for item in value
        if isinstance(item, dict) and item.get("url")
    ] if isinstance(value, list) else []


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(number, 1.0))


def _compact_text(value: Any, *, limit: int) -> str:
    normalized = " ".join(str(value or "").split())
    return normalized[:limit]


def _iso(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else _string_or_none(value)
