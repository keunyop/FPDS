from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import re
import unicodedata
from typing import TYPE_CHECKING, Any
import urllib.error
from urllib.parse import urlsplit, urlunsplit

from api_service.errors import SourceRegistryError
from api_service.product_type_localization import localize_product_type_definition
from api_service.security import new_id, utc_now
from api_service.source_catalog import (
    _normalize_bank_homepage_url,
    _normalize_optional_public_url,
    create_bank_profile,
)
from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover - keeps unit tests lightweight.
    Connection = Any


AI_BANK_ONBOARDING_STAGE = "bank_registry_onboarding"
AI_BANK_ONBOARDING_AGENT = "fpds_bank_onboarding"
AI_BANK_ONBOARDING_SCHEMA_NAME = "fpds_bank_registry_onboarding_v8"
AI_BANK_ONBOARDING_RANKING_SCHEMA_NAME = "fpds_bank_registry_ranking_v1"
AI_BANK_ONBOARDING_RANKING_SEARCH_TOOL_CALL_LIMIT = 4
AI_BANK_ONBOARDING_OFFICIAL_EVIDENCE_SEARCH_TOOL_CALL_LIMIT = 4


class _BankAiResultsInsufficientError(SourceRegistryError):
    def __init__(self, *, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=422,
            code="bank_ai_results_insufficient",
            message=(
                "AI research did not return enough fully sourced, non-duplicate banks "
                "with official homepage and Product Type coverage evidence. No banks were added."
            ),
        )
        self.diagnostics = diagnostics or {}


class _BankAiProviderStageError(RuntimeError):
    def __init__(
        self,
        *,
        stage: str,
        cause: Exception,
        provider_metadata: dict[str, Any],
    ) -> None:
        self.stage = stage
        self.cause = cause
        self.provider_metadata = provider_metadata
        super().__init__(str(cause))


AI_BANK_ONBOARDING_RANKING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["country_code", "ranking_basis", "candidates"],
    "properties": {
        "country_code": {"type": "string"},
        "ranking_basis": {
            "type": "object",
            "additionalProperties": False,
            "required": ["metric", "as_of_date", "summary"],
            "properties": {
                "metric": {"type": "string"},
                "as_of_date": {"type": "string"},
                "summary": {"type": "string"},
            },
        },
        "candidates": {
            "type": "array",
            "minItems": 0,
            "maxItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "rank",
                    "ranking_name",
                    "known_names",
                    "size_metric_label",
                    "size_metric_value",
                    "size_metric_as_of",
                    "ranking_source_url",
                ],
                "properties": {
                    "rank": {"type": "integer", "minimum": 1},
                    "ranking_name": {"type": "string"},
                    "known_names": {
                        "type": "array",
                        "maxItems": 10,
                        "items": {"type": "string"},
                    },
                    "size_metric_label": {"type": "string"},
                    "size_metric_value": {"type": "string"},
                    "size_metric_as_of": {"type": "string"},
                    "ranking_source_url": {"type": "string"},
                },
            },
        },
    },
}
AI_BANK_ONBOARDING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["country_code", "ranking_basis", "candidates"],
    "properties": {
        "country_code": {"type": "string"},
        "ranking_basis": {
            "type": "object",
            "additionalProperties": False,
            "required": ["metric", "as_of_date", "summary"],
            "properties": {
                "metric": {"type": "string"},
                "as_of_date": {"type": "string"},
                "summary": {"type": "string"},
            },
        },
        "candidates": {
            "type": "array",
            "minItems": 1,
            "maxItems": 20,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "rank",
                    "bank_name",
                    "legal_name",
                    "legal_name_source_url",
                    "ranking_name",
                    "known_names",
                    "homepage_url",
                    "homepage_source_url",
                    "logo_url",
                    "logo_source_url",
                    "source_language",
                    "size_metric_label",
                    "size_metric_value",
                    "size_metric_as_of",
                    "ranking_source_url",
                    "coverage",
                ],
                "properties": {
                    "rank": {"type": "integer", "minimum": 1},
                    "bank_name": {"type": "string"},
                    "legal_name": {"type": "string"},
                    "legal_name_source_url": {"type": "string"},
                    "ranking_name": {"type": "string"},
                    "known_names": {
                        "type": "array",
                        "maxItems": 10,
                        "items": {"type": "string"},
                    },
                    "homepage_url": {"type": "string"},
                    "homepage_source_url": {"type": "string"},
                    "logo_url": {"type": ["string", "null"]},
                    "logo_source_url": {"type": ["string", "null"]},
                    "source_language": {"type": "string"},
                    "size_metric_label": {"type": "string"},
                    "size_metric_value": {"type": "string"},
                    "size_metric_as_of": {"type": "string"},
                    "ranking_source_url": {"type": "string"},
                    "coverage": {
                        "type": "array",
                        "maxItems": 50,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "product_type",
                                "source_url",
                                "current_offering_quote",
                                "relationship_source_url",
                                "relationship_quote",
                            ],
                            "properties": {
                                "product_type": {"type": "string"},
                                "source_url": {"type": "string"},
                                "current_offering_quote": {"type": "string"},
                                "relationship_source_url": {"type": "string"},
                                "relationship_quote": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    },
}


def run_bank_ai_onboarding(
    connection: Connection,
    *,
    country_code: str,
    requested_count: int,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    invoke_model: Any = invoke_openai_json_schema,
) -> dict[str, Any]:
    if str(actor.get("role") or "").lower() != "admin":
        raise SourceRegistryError(
            status_code=403,
            code="admin_role_required",
            message="Admin role is required.",
        )
    if requested_count < 1 or requested_count > 10:
        raise SourceRegistryError(
            status_code=422,
            code="bank_ai_count_invalid",
            message="count must be between 1 and 10.",
        )
    if not llm_provider_configured():
        raise SourceRegistryError(
            status_code=503,
            code="ai_provider_unavailable",
            message="AI bank onboarding is unavailable because the OpenAI provider is not configured.",
        )

    _require_standalone_ai_schema(connection)
    normalized_country_code = _normalize_country_code(country_code)
    country = _load_active_country(connection, country_code=normalized_country_code)
    product_types = _load_active_product_types(connection)
    if not product_types:
        raise SourceRegistryError(
            status_code=409,
            code="active_product_types_required",
            message="Add at least one active Product Type before using AI bank onboarding.",
        )
    existing_banks = _load_existing_banks(connection, country_code=normalized_country_code)

    operation_id = new_id("bankonboard")
    model_execution_id = new_id("modelexec")
    model_id = configured_model_id()
    candidate_limit = _bank_ai_candidate_limit(requested_count)
    official_evidence_candidate_limit = candidate_limit
    started_at = utc_now()
    execution_metadata = {
        "operation_id": operation_id,
        "country_code": normalized_country_code,
        "country_name": country["country_name"],
        "requested_count": requested_count,
        "requested_by_user_id": _string_or_none(actor.get("user_id")),
        "existing_bank_count": len(existing_banks),
        "active_product_type_count": len(product_types),
        "candidate_limit": candidate_limit,
        "ranking_search_tool_call_limit": AI_BANK_ONBOARDING_RANKING_SEARCH_TOOL_CALL_LIMIT,
        "official_evidence_search_tool_call_limit": (
            AI_BANK_ONBOARDING_OFFICIAL_EVIDENCE_SEARCH_TOOL_CALL_LIMIT
        ),
        "official_evidence_candidate_limit": official_evidence_candidate_limit,
        "web_search_tool_call_limit": (
            AI_BANK_ONBOARDING_RANKING_SEARCH_TOOL_CALL_LIMIT
            + (
                AI_BANK_ONBOARDING_OFFICIAL_EVIDENCE_SEARCH_TOOL_CALL_LIMIT
                * official_evidence_candidate_limit
            )
        ),
        "onboarding_contract_version": "bank-registry-onboarding-v8",
    }
    _insert_model_execution(
        connection,
        model_execution_id=model_execution_id,
        model_id=model_id,
        execution_metadata=execution_metadata,
        started_at=started_at,
    )
    # The live web-search request can use the full provider timeout. Commit the
    # started execution before that network wait so the database session is not
    # left idle inside a transaction and the diagnostic survives a disconnect.
    connection.commit()

    request_payload = build_bank_ai_onboarding_payload(
        country=country,
        requested_count=requested_count,
        existing_banks=existing_banks,
        product_types=product_types,
    )
    try:
        raw_result, provider_metadata = _invoke_bank_ai_onboarding_model(
            invoke_model=invoke_model,
            request_payload=request_payload,
            model_id=model_id,
            country_code=normalized_country_code,
            requested_count=requested_count,
            active_product_types={str(item["product_type_code"]) for item in product_types},
            existing_banks=existing_banks,
        )
    except Exception as exc:
        error_message = _safe_provider_error(exc)
        completed_at = utc_now()
        partial_provider_metadata = _mapping(
            getattr(exc, "provider_metadata", None)
        )
        partial_sources = _source_list(
            partial_provider_metadata.get("web_search_sources")
        )
        _persist_ai_onboarding_failure_best_effort(
            connection,
            model_execution_id=model_execution_id,
            execution_metadata={
                **execution_metadata,
                "provider": _string_or_none(partial_provider_metadata.get("provider")),
                "provider_request_id": _string_or_none(
                    partial_provider_metadata.get("provider_request_id")
                ),
                "provider_request_ids": _string_list(
                    partial_provider_metadata.get("provider_request_ids")
                ),
                "failure_type": type(getattr(exc, "cause", exc)).__name__,
                "failed_model_stage": _string_or_none(getattr(exc, "stage", None)),
                "error_message": error_message,
                "sources": partial_sources,
            },
            completed_at=completed_at,
            actor=actor,
            country_code=normalized_country_code,
            operation_id=operation_id,
            request_context=request_context,
            reason_code="provider_failure",
            reason_text=error_message,
            sources=partial_sources,
            provider_metadata=partial_provider_metadata or None,
            model_id=model_id if partial_provider_metadata else None,
        )
        return _error_result(
            status_code=502,
            code="bank_ai_onboarding_failed",
            message=error_message,
            operation_id=operation_id,
        )

    sources = _source_list(provider_metadata.get("web_search_sources"))
    try:
        sanitized = sanitize_bank_ai_onboarding_result(
            raw_result=raw_result,
            country_code=normalized_country_code,
            requested_count=requested_count,
            active_product_types={str(item["product_type_code"]) for item in product_types},
            existing_banks=existing_banks,
            sources=sources,
        )
    except SourceRegistryError as exc:
        completed_at = utc_now()
        failed_metadata = {
            **execution_metadata,
            "provider": str(provider_metadata.get("provider") or "openai"),
            "provider_request_id": _string_or_none(provider_metadata.get("provider_request_id")),
            "provider_request_ids": _string_list(provider_metadata.get("provider_request_ids")),
            "model_stages": _dict_list(provider_metadata.get("model_stages")),
            "failure_type": "result_validation",
            "error_code": exc.code,
            "validation_diagnostics": getattr(exc, "diagnostics", {}),
            "sources": sources,
        }
        _persist_ai_onboarding_failure_best_effort(
            connection,
            model_execution_id=model_execution_id,
            execution_metadata=failed_metadata,
            completed_at=completed_at,
            actor=actor,
            country_code=normalized_country_code,
            operation_id=operation_id,
            request_context=request_context,
            reason_code=exc.code,
            reason_text=exc.message,
            sources=sources,
            provider_metadata=provider_metadata,
            model_id=model_id,
        )
        return _error_result(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            operation_id=operation_id,
        )

    created_items: list[dict[str, Any]] = []
    try:
        # Start a new outer transaction after the pre-provider commit. The
        # nested block remains the batch savepoint, while its successful writes
        # and final model metadata are committed together by the request scope.
        connection.execute("SELECT 1", {})
        with connection.transaction():
            for candidate in sanitized["candidates"]:
                created_bank = create_bank_profile(
                    connection,
                    payload={
                        "country_code": normalized_country_code,
                        "bank_name": candidate["bank_name"],
                        "homepage_url": candidate["homepage_url"],
                        "logo_url": candidate["logo_url"],
                        "logo_alt_text": f"{candidate['bank_name']} logo",
                        "source_language": candidate["source_language"],
                        "status": "active",
                        "change_reason": (
                            f"AI bank onboarding {operation_id}; national size rank "
                            f"{candidate['rank']} by {candidate['size_metric_label']} "
                            f"({candidate['size_metric_as_of']})."
                        ),
                        "initial_coverage_product_types": candidate["coverage_product_types"],
                        "initial_coverage_source_urls": {
                            item["product_type"]: item["source_url"]
                            for item in candidate["coverage"]
                        },
                        "initial_coverage_source_metadata": {
                            item["product_type"]: item["source_metadata"]
                            for item in candidate["coverage"]
                        },
                    },
                    actor=actor,
                    request_context=request_context,
                )
                created_items.append(
                    {
                        "bank": created_bank,
                        "rank": candidate["rank"],
                        "size_metric_label": candidate["size_metric_label"],
                        "size_metric_value": candidate["size_metric_value"],
                        "size_metric_as_of": candidate["size_metric_as_of"],
                        "ranking_source_url": candidate["ranking_source_url"],
                        "ranking_name": candidate["ranking_name"],
                        "legal_name": candidate["legal_name"],
                        "legal_name_source_url": candidate["legal_name_source_url"],
                        "homepage_source_url": candidate["homepage_source_url"],
                        "logo_source_url": candidate["logo_source_url"],
                        "coverage": candidate["coverage"],
                    }
                )
    except Exception as exc:
        if isinstance(exc, SourceRegistryError):
            status_code = exc.status_code
            error_code = exc.code
            error_message = exc.message
        else:
            status_code = 500
            error_code = "bank_ai_registry_write_failed"
            error_message = "The verified banks could not be registered atomically."
        completed_at = utc_now()
        _persist_ai_onboarding_failure_best_effort(
            connection,
            model_execution_id=model_execution_id,
            execution_metadata={
                **execution_metadata,
                "provider": str(provider_metadata.get("provider") or "openai"),
                "provider_request_id": _string_or_none(provider_metadata.get("provider_request_id")),
                "provider_request_ids": _string_list(provider_metadata.get("provider_request_ids")),
                "model_stages": _dict_list(provider_metadata.get("model_stages")),
                "failure_type": "registry_write",
                "error_code": error_code,
                "sources": sources,
            },
            completed_at=completed_at,
            actor=actor,
            country_code=normalized_country_code,
            operation_id=operation_id,
            request_context=request_context,
            reason_code=error_code,
            reason_text=error_message,
            sources=sources,
            provider_metadata=provider_metadata,
            model_id=model_id,
        )
        return _error_result(
            status_code=status_code,
            code=error_code,
            message=error_message,
            operation_id=operation_id,
        )

    completed_at = utc_now()
    bank_codes = [str(item["bank"]["bank_code"]) for item in created_items]
    bank_evidence = [
        {
            "bank_code": str(item["bank"]["bank_code"]),
            "bank_name": str(item["bank"]["bank_name"]),
            "legal_name": item["legal_name"],
            "legal_name_source_url": item["legal_name_source_url"],
            "ranking_name": item["ranking_name"],
            "ranking_source_url": item["ranking_source_url"],
        }
        for item in created_items
    ]
    completed_metadata = {
        **execution_metadata,
        "provider": str(provider_metadata.get("provider") or "openai"),
        "provider_request_id": _string_or_none(provider_metadata.get("provider_request_id")),
        "provider_request_ids": _string_list(provider_metadata.get("provider_request_ids")),
        "model_stages": _dict_list(provider_metadata.get("model_stages")),
        "ranking_basis": sanitized["ranking_basis"],
        "created_bank_codes": bank_codes,
        "bank_name_evidence": bank_evidence,
        "sources": sources,
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
        operation_id=operation_id,
        country_code=normalized_country_code,
        request_id=_string_or_none(request_context.get("request_id")),
        provider_metadata=provider_metadata,
        model_id=model_id,
        recorded_at=completed_at,
    )
    _record_ai_onboarding_audit(
        connection,
        event_type="bank_ai_onboarding_completed",
        actor=actor,
        country_code=normalized_country_code,
        operation_id=operation_id,
        model_execution_id=model_execution_id,
        request_context=request_context,
        reason_code="ai_bank_onboarding",
        reason_text=f"Registered {len(created_items)} sourced bank profiles.",
        bank_codes=bank_codes,
        sources=sources,
        bank_name_evidence=bank_evidence,
    )
    return {
        "ok": True,
        "status_code": 201,
        "operation_id": operation_id,
        "country_code": normalized_country_code,
        "country_name": country["country_name"],
        "requested_count": requested_count,
        "added_count": len(created_items),
        "coverage_item_count": sum(
            len(item["coverage"])
            for item in created_items
        ),
        "ranking_basis": sanitized["ranking_basis"],
        "banks": created_items,
        "sources": sources,
    }


def build_bank_ai_onboarding_payload(
    *,
    country: dict[str, str],
    requested_count: int,
    existing_banks: list[dict[str, Any]],
    product_types: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "country": country,
        "requested_count": requested_count,
        "candidate_limit": _bank_ai_candidate_limit(requested_count),
        "existing_banks_to_exclude": [
            {
                "bank_name": str(item.get("bank_name") or ""),
                "homepage_url": _string_or_none(item.get("homepage_url")),
            }
            for item in existing_banks[:500]
        ],
        "allowed_product_types": [
            {
                "product_type_code": str(localized["product_type_code"]),
                "product_family": str(localized.get("product_family") or ""),
                "display_name": str(localized.get("display_name") or localized["product_type_code"]),
                "description": str(localized.get("description") or ""),
                "discovery_keywords": list(localized.get("discovery_keywords") or []),
            }
            for item in product_types
            for localized in [
                localize_product_type_definition(
                    country_code=str(country.get("country_code") or ""),
                    definition=item,
                )
            ]
        ],
    }


def sanitize_bank_ai_onboarding_result(
    *,
    raw_result: dict[str, Any],
    country_code: str,
    requested_count: int,
    active_product_types: set[str],
    existing_banks: list[dict[str, Any]],
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    if str(raw_result.get("country_code") or "").strip().upper() != country_code:
        raise _insufficient_result_error()
    if not sources:
        raise _insufficient_result_error()

    ranking_raw = _mapping(raw_result.get("ranking_basis"))
    ranking_basis = {
        "metric": _required_compact_text(ranking_raw.get("metric"), limit=160),
        "as_of_date": _required_compact_text(ranking_raw.get("as_of_date"), limit=80),
        "summary": _required_compact_text(ranking_raw.get("summary"), limit=500),
    }
    consulted_keys = {_citation_key(item["url"]) for item in sources if _citation_key(item["url"])}
    existing_hosts = {
        _hostname(str(item.get("homepage_url") or ""))
        for item in existing_banks
        if _hostname(str(item.get("homepage_url") or ""))
    }
    existing_identity_keys = {
        key
        for item in existing_banks
        for key in [_identity_key(item.get("bank_name"))]
        if key
    }

    candidates: list[dict[str, Any]] = []
    candidate_hosts: set[str] = set()
    candidate_identity_keys: set[str] = set()
    used_ranks: set[int] = set()
    for raw_candidate in sorted(
        _dict_list(raw_result.get("candidates")),
        key=lambda item: (_positive_integer(item.get("rank")) or 10_000, str(item.get("bank_name") or "")),
    ):
        rank = _positive_integer(raw_candidate.get("rank"))
        if rank is None or rank in used_ranks:
            continue
        bank_name = _required_compact_text(raw_candidate.get("bank_name"), limit=300, allow_error=False)
        legal_name = _required_compact_text(raw_candidate.get("legal_name"), limit=300, allow_error=False)
        ranking_name = _required_compact_text(raw_candidate.get("ranking_name"), limit=300, allow_error=False)
        if (
            not bank_name
            or not legal_name
            or not ranking_name
            or _looks_like_regulatory_report_name(bank_name, country_code=country_code)
        ):
            continue
        try:
            homepage_url, _normalized_homepage_url = _normalize_bank_homepage_url(
                str(raw_candidate.get("homepage_url") or "")
            )
        except SourceRegistryError:
            continue
        homepage_host = _hostname(homepage_url)
        if not homepage_host or homepage_host in existing_hosts or homepage_host in candidate_hosts:
            continue

        identity_keys = {
            key
            for name in [
                bank_name,
                legal_name,
                ranking_name,
                *_string_list(raw_candidate.get("known_names")),
            ]
            for key in [_identity_key(name)]
            if key
        }
        if _identities_overlap(identity_keys, existing_identity_keys | candidate_identity_keys):
            continue

        homepage_source_url = _consulted_same_host_source_url(
            reference_url=homepage_url,
            preferred_url=_string_or_none(raw_candidate.get("homepage_source_url")),
            sources=sources,
        )
        legal_name_source_url = _string_or_none(raw_candidate.get("legal_name_source_url"))
        ranking_source_url = _string_or_none(raw_candidate.get("ranking_source_url"))
        if (
            not homepage_source_url
            or not legal_name_source_url
            or not ranking_source_url
            or _citation_key(homepage_source_url) not in consulted_keys
            or _citation_key(legal_name_source_url) not in consulted_keys
            or _citation_key(ranking_source_url) not in consulted_keys
            or not _same_official_domain(homepage_url, homepage_source_url)
        ):
            continue

        coverage: list[dict[str, str]] = []
        covered_types: set[str] = set()
        for raw_coverage in _dict_list(raw_candidate.get("coverage")):
            product_type = str(raw_coverage.get("product_type") or "").strip().lower()
            source_url = _string_or_none(raw_coverage.get("source_url"))
            current_offering_quote = _string_or_none(raw_coverage.get("current_offering_quote"))
            relationship_source_url = _string_or_none(raw_coverage.get("relationship_source_url"))
            relationship_quote = _string_or_none(raw_coverage.get("relationship_quote"))
            if (
                not product_type
                or product_type not in active_product_types
                or product_type in covered_types
                or not source_url
                or _citation_key(source_url) not in consulted_keys
                or not current_offering_quote
                or not relationship_source_url
                or _citation_key(relationship_source_url) not in consulted_keys
                or not relationship_quote
                or not _relationship_quote_identifies_candidate(
                    relationship_quote,
                    bank_name=bank_name,
                    legal_name=legal_name,
                )
            ):
                continue
            coverage_host = _hostname(source_url)
            relationship_host = _hostname(relationship_source_url)
            if (
                not coverage_host
                or not relationship_host
                or relationship_host not in {homepage_host, coverage_host}
                or (
                    coverage_host != homepage_host
                    and relationship_host != coverage_host
                    and not _relationship_quote_identifies_coverage_domain(
                        relationship_quote,
                        coverage_host=coverage_host,
                    )
                )
            ):
                continue
            covered_types.add(product_type)
            coverage.append(
                {
                    "product_type": product_type,
                    "source_url": source_url,
                    "current_offering_quote": current_offering_quote,
                    "relationship_source_url": relationship_source_url,
                    "relationship_quote": relationship_quote,
                    "source_metadata": {
                        "verification_status": "verified",
                        "verification_method": "ai_bank_onboarding_web_search",
                        "homepage_domain": homepage_host,
                        "coverage_domain": coverage_host,
                        "relationship_source_url": relationship_source_url,
                        "relationship_quote": relationship_quote,
                        "current_offering_quote": current_offering_quote,
                    },
                }
            )
        if not coverage:
            continue

        source_language = str(raw_candidate.get("source_language") or "").strip()
        if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2,8})?", source_language):
            continue
        source_language = source_language.lower()

        logo_url = None
        logo_source_url = None
        proposed_logo_url = _string_or_none(raw_candidate.get("logo_url"))
        proposed_logo_source = _string_or_none(raw_candidate.get("logo_source_url"))
        if (
            proposed_logo_url
            and proposed_logo_source
            and _citation_key(proposed_logo_source) in consulted_keys
            and _same_official_domain(homepage_url, proposed_logo_source)
            and _same_official_domain(homepage_url, proposed_logo_url)
        ):
            try:
                logo_url = _normalize_optional_public_url(proposed_logo_url, "logo_url")
                logo_source_url = proposed_logo_source
            except SourceRegistryError:
                logo_url = None
                logo_source_url = None
        if logo_url is None:
            logo_url = _favicon_url(homepage_url)
            logo_source_url = homepage_source_url

        size_metric_label = _required_compact_text(
            raw_candidate.get("size_metric_label"),
            limit=160,
            allow_error=False,
        )
        size_metric_value = _required_compact_text(
            raw_candidate.get("size_metric_value"),
            limit=160,
            allow_error=False,
        )
        size_metric_as_of = _required_compact_text(
            raw_candidate.get("size_metric_as_of"),
            limit=80,
            allow_error=False,
        )
        if not size_metric_label or not size_metric_value or not size_metric_as_of:
            continue

        used_ranks.add(rank)
        candidate_hosts.add(homepage_host)
        candidate_identity_keys.update(identity_keys)
        candidates.append(
            {
                "rank": rank,
                "bank_name": bank_name,
                "legal_name": legal_name,
                "legal_name_source_url": legal_name_source_url,
                "ranking_name": ranking_name,
                "homepage_url": homepage_url,
                "homepage_source_url": homepage_source_url,
                "logo_url": logo_url,
                "logo_source_url": logo_source_url,
                "source_language": source_language,
                "size_metric_label": size_metric_label,
                "size_metric_value": size_metric_value,
                "size_metric_as_of": size_metric_as_of,
                "ranking_source_url": ranking_source_url,
                "coverage": coverage,
                "coverage_product_types": [item["product_type"] for item in coverage],
            }
        )
        if len(candidates) == requested_count:
            break

    if len(candidates) < requested_count:
        raise _insufficient_result_error(
            diagnostics={
                **_bank_ai_source_diagnostics(raw_result=raw_result, sources=sources),
                "accepted_candidate_count": len(candidates),
                "requested_count": requested_count,
            }
        )
    return {
        "ranking_basis": ranking_basis,
        "candidates": candidates,
    }


def _bank_ai_onboarding_instructions() -> str:
    return (
        "You are the FPDS official-bank-evidence agent. You must use live web search before answering. "
        "Exactly one server-selected ranked candidate is supplied as ranking_research_result. Do not search for "
        "another ranking, bank-size "
        "list, statistical table, aggregator, Wikipedia page, or news summary. Preserve the supplied ranking basis, "
        "rank, ranking_name, size fields, and ranking_source_url exactly. Use every web search only to consult official "
        "bank-controlled homepages, official legal-identity pages, and current official product pages for that one "
        "candidate. Do not introduce a different bank. Return an empty candidates array when the supplied candidate "
        "cannot be fully sourced; never return a placeholder candidate. Do not return a candidate unless every URL "
        "used for its homepage, legal "
        "identity, and Product Type coverage was actually consulted. Exclude every supplied existing bank, including "
        "aliases, parent/brand duplicates, and matching official domains. Exclude closed institutions, investment-only "
        "firms, insurers, and institutions that do not offer any supplied Product Type to customers in the country. "
        "For each bank, verify the official bank-controlled "
        "homepage. `bank_name` is the customer-facing official display name used by the bank on that homepage. "
        "It must be readable title/brand casing and must not reuse fixed-width regulatory abbreviations such as "
        "`JPMORGAN CHASE BK NA`, legal charter suffixes such as `N.A.` or `National Association`, or an all-caps "
        "ranking label. Return the full official legal entity name separately as `legal_name`, cite it with "
        "`legal_name_source_url`, and preserve the ranking source's exact unedited label as `ranking_name`. "
        "The legal-name source must be an official bank or government regulator page actually consulted. "
        "Classify coverage only from the supplied Product Type codes and only when a current official "
        "product/detail/catalog page explicitly shows that product family. Give its exact source URL and a short "
        "exact current_offering_quote naming the Product Type. The product route may use a separate official consumer "
        "brand domain. For every coverage item, give a consulted relationship_source_url and exact relationship_quote "
        "proving that the product or brand is provided by, owned by, or a brand of the bank; this evidence must be on "
        "the bank homepage domain or product domain. Historical announcements, educational articles, help-only pages, "
        "legacy servicing pages, login/application flows, and sold, transferred, or discontinued products are not "
        "current coverage. "
        "Provide an official same-domain logo asset only when directly verified; otherwise return null so FPDS can "
        "use its controlled favicon fallback. Every ranking, homepage, logo, and coverage source URL must be a URL "
        "consulted in either the supplied ranking research or this official-evidence research. Never invent a bank, "
        "URL, rank, asset value, date, coverage type, "
        "or source. Keep display and legal names in their official source language and return the page language code."
    )


def _bank_ai_ranking_instructions() -> str:
    return (
        "You are the FPDS bank-ranking discovery agent. Use live web search only to find one current, authoritative, "
        "comparable domestic ranking for the exact supplied country, preferably consolidated total assets from a "
        "regulator, central bank, or audited filing. Do not mix measures. Return the largest missing retail or "
        "commercial deposit-taking banks in exact ranking order. Return exactly candidate_limit bank entries while "
        "excluding supplied "
        "existing banks and their aliases. Exclude central banks, regulators, closed institutions, investment-only "
        "firms, and insurers. Each ranking_name must be the exact institution row label, never the title of a report, "
        "table, chart, or bank list. Preserve the source's exact ranking label, value, unit or metric label, as-of date, and "
        "consulted ranking URL. This stage must not investigate bank homepages, legal pages, logos, or products; a "
        "separate official-evidence stage handles those. Never invent a bank, rank, value, date, or URL."
    )


def _looks_like_regulatory_report_name(value: str, *, country_code: str) -> bool:
    if country_code != "US":
        return False
    compact = " ".join(str(value or "").split())
    upper = compact.upper()
    if re.search(r"(?:^|[\s,])N\.?\s*A\.?$", upper):
        return True
    if upper.endswith(" NATIONAL ASSOCIATION"):
        return True
    if compact == upper and re.search(r"(?:^|\s)(?:BK|AMER)(?:\s|$)", upper):
        return True
    return False


def _looks_like_ranking_report_title(value: str) -> bool:
    normalized = " ".join(str(value or "").casefold().split())
    return any(
        marker in normalized
        for marker in (
            "ranked by",
            "domestically chartered commercial banks",
            "banking industry profile",
            "list of largest banks",
            "commercial banks by consolidated assets",
        )
    )


def _load_active_country(connection: Connection, *, country_code: str) -> dict[str, str]:
    row = connection.execute(
        """
        SELECT country_code, country_name
        FROM country_registry
        WHERE country_code = %(country_code)s
          AND status = 'active'
        """,
        {"country_code": country_code},
    ).fetchone()
    if not row:
        raise SourceRegistryError(
            status_code=404,
            code="active_country_not_found",
            message="The signed-in country is not active.",
        )
    return {
        "country_code": str(row["country_code"]),
        "country_name": str(row["country_name"]),
    }


def _require_standalone_ai_schema(connection: Connection) -> None:
    row = connection.execute(
        """
        SELECT COUNT(*) AS nullable_run_columns
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name IN ('model_execution', 'llm_usage_record')
          AND column_name = 'run_id'
          AND is_nullable = 'YES'
        """
    ).fetchone()
    if not row or int(row.get("nullable_run_columns") or 0) != 2:
        raise SourceRegistryError(
            status_code=503,
            code="bank_ai_schema_not_ready",
            message="AI bank onboarding requires database migration 0027_standalone_ai_operations.sql.",
        )


def _load_active_product_types(connection: Connection) -> list[dict[str, Any]]:
    return list(
        connection.execute(
            """
            SELECT product_type_code, product_family, display_name, description
            FROM product_type_registry
            WHERE status = 'active'
            ORDER BY display_name, product_type_code
            """
        ).fetchall()
    )


def _load_existing_banks(connection: Connection, *, country_code: str) -> list[dict[str, Any]]:
    return list(
        connection.execute(
            """
            SELECT bank_name, homepage_url, normalized_homepage_url
            FROM bank
            WHERE country_code = %(country_code)s
            ORDER BY bank_name, bank_code
            """,
            {"country_code": country_code},
        ).fetchall()
    )


def _insert_model_execution(
    connection: Connection,
    *,
    model_execution_id: str,
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
            NULL,
            NULL,
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
            "stage_name": AI_BANK_ONBOARDING_STAGE,
            "agent_name": AI_BANK_ONBOARDING_AGENT,
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
    operation_id: str,
    country_code: str,
    request_id: str | None,
    provider_metadata: dict[str, Any],
    model_id: str,
    recorded_at: datetime,
) -> None:
    prompt_tokens = int(provider_metadata.get("prompt_tokens") or 0)
    completion_tokens = int(provider_metadata.get("completion_tokens") or 0)
    resolved_model_id = str(provider_metadata.get("model_id") or model_id)
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
            NULL,
            NULL,
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
            "provider_request_id": _string_or_none(provider_metadata.get("provider_request_id")),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost": estimated_cost_usd(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
            "usage_metadata": json.dumps(
                {
                    "provider": str(provider_metadata.get("provider") or "openai"),
                    "model_id": resolved_model_id,
                    "stage_name": AI_BANK_ONBOARDING_STAGE,
                    "usage_mode": "live_web_bank_onboarding",
                    "operation_id": operation_id,
                    "country_code": country_code,
                    "request_id": request_id,
                    "provider_request_ids": _string_list(
                        provider_metadata.get("provider_request_ids")
                    ),
                    "model_stages": _dict_list(provider_metadata.get("model_stages")),
                },
                ensure_ascii=True,
            ),
            "recorded_at": recorded_at,
        },
    )


def _record_ai_onboarding_audit(
    connection: Connection,
    *,
    event_type: str,
    actor: dict[str, Any],
    country_code: str,
    operation_id: str,
    model_execution_id: str,
    request_context: dict[str, Any],
    reason_code: str,
    reason_text: str,
    bank_codes: list[str],
    sources: list[dict[str, str]],
    bank_name_evidence: list[dict[str, Any]] | None = None,
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
            reason_code,
            reason_text,
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
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'bank_registry_onboarding',
            %(operation_id)s,
            %(reason_code)s,
            %(reason_text)s,
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
            "actor_id": _string_or_none(actor.get("user_id")),
            "actor_role_snapshot": _string_or_none(actor.get("role")),
            "operation_id": operation_id,
            "country_code": country_code,
            "reason_code": reason_code,
            "reason_text": _compact_text(reason_text, limit=2000),
            "request_id": _string_or_none(request_context.get("request_id")),
            "diff_summary": ", ".join(bank_codes) if bank_codes else None,
            "source_ref": sources[0]["url"] if sources else None,
            "ip_address": _string_or_none(request_context.get("ip_address")),
            "user_agent": _string_or_none(request_context.get("user_agent")),
            "event_payload": json.dumps(
                {
                    "operation_id": operation_id,
                    "model_execution_id": model_execution_id,
                    "country_code": country_code,
                    "bank_codes": bank_codes,
                    "bank_name_evidence": bank_name_evidence or [],
                    "source_count": len(sources),
                    "sources": sources,
                },
                ensure_ascii=True,
            ),
            "occurred_at": utc_now(),
        },
    )


def _invoke_bank_ai_onboarding_model(
    *,
    invoke_model: Any,
    request_payload: dict[str, Any],
    model_id: str,
    country_code: str,
    requested_count: int,
    active_product_types: set[str],
    existing_banks: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_limit = _positive_integer(request_payload.get("candidate_limit")) or requested_count
    ranking_result, ranking_metadata = _invoke_bank_ai_model_stage(
        invoke_model=invoke_model,
        instructions=_bank_ai_ranking_instructions(),
        payload=request_payload,
        schema_name=AI_BANK_ONBOARDING_RANKING_SCHEMA_NAME,
        schema=_bank_ai_ranking_schema(candidate_limit),
        model_id=model_id,
        max_web_search_tool_calls=AI_BANK_ONBOARDING_RANKING_SEARCH_TOOL_CALL_LIMIT,
    )
    ranking_metadata = _retain_bank_ai_relevant_sources(
        result=ranking_result,
        provider_metadata=ranking_metadata,
    )
    ranking_basis = _mapping(ranking_result.get("ranking_basis"))
    aggregate_result: dict[str, Any] = {
        "country_code": str(ranking_result.get("country_code") or country_code),
        "ranking_basis": ranking_basis,
        "candidates": [],
    }
    stages: list[tuple[str, dict[str, Any]]] = [
        ("ranking_discovery", ranking_metadata)
    ]
    ranked_candidates = _ranked_candidates_for_evidence(
        ranking_result=ranking_result,
        existing_banks=existing_banks,
        candidate_limit=candidate_limit,
    )
    for ranked_candidate in ranked_candidates:
        rank = int(ranked_candidate["rank"])
        stage_name = f"official_evidence_rank_{rank}"
        try:
            evidence_result, evidence_metadata = _invoke_bank_ai_model_stage(
                invoke_model=invoke_model,
                instructions=_bank_ai_onboarding_instructions(),
                payload={
                    **request_payload,
                    "requested_count": 1,
                    "candidate_limit": 1,
                    "ranking_research_result": {
                        "country_code": aggregate_result["country_code"],
                        "ranking_basis": ranking_basis,
                        "candidates": [ranked_candidate],
                    },
                },
                schema_name=AI_BANK_ONBOARDING_SCHEMA_NAME,
                schema=AI_BANK_ONBOARDING_SCHEMA,
                model_id=model_id,
                max_web_search_tool_calls=(
                    AI_BANK_ONBOARDING_OFFICIAL_EVIDENCE_SEARCH_TOOL_CALL_LIMIT
                ),
            )
            evidence_metadata = _retain_bank_ai_relevant_sources(
                result=evidence_result,
                provider_metadata=evidence_metadata,
            )
        except Exception as exc:
            raise _BankAiProviderStageError(
                stage=stage_name,
                cause=exc,
                provider_metadata=_merge_bank_ai_provider_metadata(*stages),
            ) from exc
        stages.append((stage_name, evidence_metadata))
        merged_candidate = _merge_ranked_candidate_evidence(
            ranked_candidate=ranked_candidate,
            evidence_result=evidence_result,
        )
        if merged_candidate is None:
            continue
        aggregate_result["candidates"].append(merged_candidate)
        combined_metadata = _merge_bank_ai_provider_metadata(*stages)
        try:
            sanitize_bank_ai_onboarding_result(
                raw_result=aggregate_result,
                country_code=country_code,
                requested_count=requested_count,
                active_product_types=active_product_types,
                existing_banks=existing_banks,
                sources=_source_list(combined_metadata.get("web_search_sources")),
            )
        except SourceRegistryError:
            continue
        break
    return aggregate_result, _merge_bank_ai_provider_metadata(*stages)


def _ranked_candidates_for_evidence(
    *,
    ranking_result: dict[str, Any],
    existing_banks: list[dict[str, Any]],
    candidate_limit: int,
) -> list[dict[str, Any]]:
    existing_identity_keys = {
        key
        for item in existing_banks
        for key in [_identity_key(item.get("bank_name"))]
        if key
    }
    selected: list[dict[str, Any]] = []
    selected_identity_keys: set[str] = set()
    used_ranks: set[int] = set()
    for candidate in sorted(
        _dict_list(ranking_result.get("candidates")),
        key=lambda item: (_positive_integer(item.get("rank")) or 10_000),
    ):
        rank = _positive_integer(candidate.get("rank"))
        ranking_name = _compact_text(candidate.get("ranking_name"), limit=300)
        known_names = _string_list(candidate.get("known_names"))[:10]
        identity_keys = {
            key
            for value in [ranking_name, *known_names]
            for key in [_identity_key(value)]
            if key
        }
        size_metric_label = _compact_text(candidate.get("size_metric_label"), limit=160)
        size_metric_value = _compact_text(candidate.get("size_metric_value"), limit=160)
        size_metric_as_of = _compact_text(candidate.get("size_metric_as_of"), limit=80)
        ranking_source_url = _string_or_none(candidate.get("ranking_source_url"))
        if (
            rank is None
            or rank in used_ranks
            or not ranking_name
            or _looks_like_ranking_report_title(ranking_name)
            or not identity_keys
            or _identities_overlap(
                identity_keys,
                existing_identity_keys | selected_identity_keys,
            )
            or not size_metric_label
            or not size_metric_value
            or not size_metric_as_of
            or not ranking_source_url
            or not _citation_key(ranking_source_url)
        ):
            continue
        used_ranks.add(rank)
        selected_identity_keys.update(identity_keys)
        selected.append(
            {
                "rank": rank,
                "ranking_name": ranking_name,
                "known_names": known_names,
                "size_metric_label": size_metric_label,
                "size_metric_value": size_metric_value,
                "size_metric_as_of": size_metric_as_of,
                "ranking_source_url": ranking_source_url,
            }
        )
        if len(selected) == candidate_limit:
            break
    return selected


def _bank_ai_ranking_schema(candidate_limit: int) -> dict[str, Any]:
    schema = deepcopy(AI_BANK_ONBOARDING_RANKING_SCHEMA)
    candidates_schema = schema["properties"]["candidates"]
    candidates_schema["minItems"] = candidate_limit
    candidates_schema["maxItems"] = candidate_limit
    return schema


def _merge_ranked_candidate_evidence(
    *,
    ranked_candidate: dict[str, Any],
    evidence_result: dict[str, Any],
) -> dict[str, Any] | None:
    ranking_identity_keys = {
        key
        for value in [
            ranked_candidate.get("ranking_name"),
            *_string_list(ranked_candidate.get("known_names")),
        ]
        for key in [_identity_key(value)]
        if key
    }
    for candidate in _dict_list(evidence_result.get("candidates")):
        evidence_identity_keys = {
            key
            for value in [
                candidate.get("bank_name"),
                candidate.get("legal_name"),
                candidate.get("ranking_name"),
                *_string_list(candidate.get("known_names")),
            ]
            for key in [_identity_key(value)]
            if key
        }
        if not _identities_overlap(ranking_identity_keys, evidence_identity_keys):
            continue
        return {
            **candidate,
            **ranked_candidate,
        }
    return None


def _invoke_bank_ai_model_stage(
    *,
    invoke_model: Any,
    instructions: str,
    payload: dict[str, Any],
    schema_name: str,
    schema: dict[str, Any],
    model_id: str,
    max_web_search_tool_calls: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    for attempt in range(2):
        try:
            return invoke_model(
                instructions=instructions,
                payload=payload,
                schema_name=schema_name,
                schema=schema,
                model_id=model_id,
                require_web_search=True,
                max_web_search_tool_calls=max_web_search_tool_calls,
            )
        except Exception as exc:
            if attempt == 0 and _is_transient_provider_transport_error(exc):
                continue
            raise
    raise AssertionError("Bank onboarding provider retry loop exited unexpectedly.")


def _retain_bank_ai_relevant_sources(
    *,
    result: dict[str, Any],
    provider_metadata: dict[str, Any],
) -> dict[str, Any]:
    consulted_sources = _source_list(
        provider_metadata.get("web_search_sources"),
        limit=500,
    )
    referenced_keys: set[str] = set()
    homepage_hosts: set[str] = set()
    for candidate in _dict_list(result.get("candidates")):
        for field_name in (
            "homepage_source_url",
            "legal_name_source_url",
            "ranking_source_url",
            "logo_source_url",
        ):
            key = _citation_key(candidate.get(field_name))
            if key:
                referenced_keys.add(key)
        homepage_host = _hostname(str(candidate.get("homepage_url") or ""))
        if homepage_host:
            homepage_hosts.add(homepage_host)
        for coverage in _dict_list(candidate.get("coverage")):
            for field_name in ("source_url", "relationship_source_url"):
                key = _citation_key(coverage.get(field_name))
                if key:
                    referenced_keys.add(key)

    retained: list[dict[str, str]] = []
    retained_keys: set[str] = set()
    retained_hosts: set[str] = set()
    for source in consulted_sources:
        key = _citation_key(source.get("url"))
        if not key or key not in referenced_keys or key in retained_keys:
            continue
        retained.append(source)
        retained_keys.add(key)
        retained_hosts.add(_hostname(source["url"]))
    for homepage_host in sorted(homepage_hosts - retained_hosts):
        source = next(
            (
                item
                for item in consulted_sources
                if _hostname(item.get("url", "")) == homepage_host
            ),
            None,
        )
        if source is None:
            continue
        key = _citation_key(source.get("url"))
        if not key or key in retained_keys:
            continue
        retained.append(source)
        retained_keys.add(key)

    return {
        **provider_metadata,
        "web_search_sources": retained,
        "web_search_source_total_count": len(consulted_sources),
    }


def _merge_bank_ai_provider_metadata(
    *stages: tuple[str, dict[str, Any]],
) -> dict[str, Any]:
    provider_request_ids = [
        request_id
        for _stage_name, metadata in stages
        for request_id in [_string_or_none(metadata.get("provider_request_id"))]
        if request_id
    ]
    stage_metadata = [
        {
            "stage": stage_name,
            "provider_request_id": _string_or_none(metadata.get("provider_request_id")),
            "prompt_tokens": int(metadata.get("prompt_tokens") or 0),
            "completion_tokens": int(metadata.get("completion_tokens") or 0),
            "web_search_source_count": len(_dict_list(metadata.get("web_search_sources"))),
            "web_search_total_source_count": int(
                metadata.get("web_search_source_total_count")
                or len(_dict_list(metadata.get("web_search_sources")))
            ),
        }
        for stage_name, metadata in stages
    ]
    final_metadata = stages[-1][1]
    return {
        "provider": str(final_metadata.get("provider") or "openai"),
        "model_id": str(final_metadata.get("model_id") or ""),
        "provider_request_id": provider_request_ids[-1] if provider_request_ids else None,
        "provider_request_ids": provider_request_ids,
        "prompt_tokens": sum(int(metadata.get("prompt_tokens") or 0) for _name, metadata in stages),
        "completion_tokens": sum(
            int(metadata.get("completion_tokens") or 0)
            for _name, metadata in stages
        ),
        "web_search_sources": _source_list(
            [
                source
                for _stage_name, metadata in stages
                for source in _dict_list(metadata.get("web_search_sources"))
            ]
        ),
        "model_stages": stage_metadata,
    }


def _bank_ai_candidate_limit(requested_count: int) -> int:
    return min(20, requested_count + min(5, requested_count))


def _bank_ai_web_search_tool_call_limit(requested_count: int) -> int:
    return min(20, max(8, (requested_count * 2) + 2))


def _is_transient_provider_transport_error(exc: Exception) -> bool:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, urllib.error.HTTPError):
            return current.code in {502, 503, 504}
        if isinstance(current, (ConnectionResetError, TimeoutError)):
            return True
        if isinstance(current, urllib.error.URLError):
            reason = current.reason
            if isinstance(reason, BaseException) and reason is not current:
                current = reason
                continue
            return True
        if getattr(current, "winerror", None) in {10053, 10054, 10060}:
            return True
        current = current.__cause__ or current.__context__
    return False


def _persist_ai_onboarding_failure_best_effort(
    connection: Connection,
    *,
    model_execution_id: str,
    execution_metadata: dict[str, Any],
    completed_at: datetime,
    actor: dict[str, Any],
    country_code: str,
    operation_id: str,
    request_context: dict[str, Any],
    reason_code: str,
    reason_text: str,
    sources: list[dict[str, str]],
    provider_metadata: dict[str, Any] | None = None,
    model_id: str | None = None,
) -> None:
    try:
        _complete_model_execution(
            connection,
            model_execution_id=model_execution_id,
            execution_status="failed",
            execution_metadata=execution_metadata,
            completed_at=completed_at,
        )
        if provider_metadata is not None and model_id is not None:
            _insert_usage_record(
                connection,
                model_execution_id=model_execution_id,
                operation_id=operation_id,
                country_code=country_code,
                request_id=_string_or_none(request_context.get("request_id")),
                provider_metadata=provider_metadata,
                model_id=model_id,
                recorded_at=completed_at,
            )
        _record_ai_onboarding_audit(
            connection,
            event_type="bank_ai_onboarding_failed",
            actor=actor,
            country_code=country_code,
            operation_id=operation_id,
            model_execution_id=model_execution_id,
            request_context=request_context,
            reason_code=reason_code,
            reason_text=reason_text,
            bank_codes=[],
            sources=sources,
        )
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass


def _error_result(*, status_code: int, code: str, message: str, operation_id: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status_code": status_code,
        "operation_id": operation_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _insufficient_result_error(
    *,
    diagnostics: dict[str, Any] | None = None,
) -> SourceRegistryError:
    return _BankAiResultsInsufficientError(diagnostics=diagnostics)


def _bank_ai_source_diagnostics(
    *,
    raw_result: dict[str, Any],
    sources: list[dict[str, str]],
) -> dict[str, int]:
    consulted_keys = {
        key
        for item in sources
        for key in [_citation_key(item.get("url"))]
        if key
    }
    raw_candidates = _dict_list(raw_result.get("candidates"))

    def candidate_has_consulted(field_name: str, candidate: dict[str, Any]) -> bool:
        return _citation_key(candidate.get(field_name)) in consulted_keys

    def candidate_has_consulted_coverage(field_name: str, candidate: dict[str, Any]) -> bool:
        return any(
            _citation_key(item.get(field_name)) in consulted_keys
            for item in _dict_list(candidate.get("coverage"))
        )

    return {
        "raw_candidate_count": len(raw_candidates),
        "consulted_source_count": len(sources),
        "candidates_with_consulted_homepage_source": sum(
            candidate_has_consulted("homepage_source_url", candidate)
            for candidate in raw_candidates
        ),
        "candidates_with_consulted_homepage_domain": sum(
            any(
                _hostname(source.get("url", ""))
                == _hostname(str(candidate.get("homepage_url") or ""))
                for source in sources
            )
            for candidate in raw_candidates
        ),
        "candidates_with_consulted_legal_name_source": sum(
            candidate_has_consulted("legal_name_source_url", candidate)
            for candidate in raw_candidates
        ),
        "candidates_with_consulted_ranking_source": sum(
            candidate_has_consulted("ranking_source_url", candidate)
            for candidate in raw_candidates
        ),
        "candidates_with_consulted_coverage_source": sum(
            candidate_has_consulted_coverage("source_url", candidate)
            for candidate in raw_candidates
        ),
        "candidates_with_consulted_relationship_source": sum(
            candidate_has_consulted_coverage("relationship_source_url", candidate)
            for candidate in raw_candidates
        ),
    }


def _safe_provider_error(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    if "API key" in message or "Authorization" in message:
        return "AI bank onboarding provider authentication failed. Check the configured API credential."
    if "status 429" in message:
        return "AI bank onboarding is temporarily rate limited. Try again later."
    if "timed out" in message.lower() or "timeout" in message.lower():
        return "AI bank onboarding timed out before the bank research completed."
    return "AI bank onboarding failed before a verified result was returned."


def _source_list(value: Any, *, limit: int = 250) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    if not isinstance(value, list):
        return output
    for item in value:
        if not isinstance(item, dict):
            continue
        url = _string_or_none(item.get("url"))
        if not url or url in seen:
            continue
        if not _citation_key(url):
            continue
        seen.add(url)
        output.append(
            {
                "url": url,
                "title": _compact_text(item.get("title") or url, limit=300),
            }
        )
        if len(output) == limit:
            break
    return output


def _consulted_same_host_source_url(
    *,
    reference_url: str,
    preferred_url: str | None,
    sources: list[dict[str, str]],
) -> str | None:
    consulted_by_key = {
        key: item["url"]
        for item in sources
        for key in [_citation_key(item.get("url"))]
        if key
    }
    preferred_key = _citation_key(preferred_url)
    if preferred_key and preferred_key in consulted_by_key:
        return preferred_url
    reference_host = _hostname(reference_url)
    if not reference_host:
        return None
    return next(
        (
            item["url"]
            for item in sources
            if _hostname(item.get("url", "")) == reference_host
        ),
        None,
    )


def _citation_key(value: Any) -> str:
    candidate = str(value or "").strip()
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+", "/", parts.path or "/").rstrip("/") or "/"
    return f"{host}{path}".lower()


def _hostname(value: str) -> str:
    try:
        hostname = urlsplit(value).hostname or ""
    except ValueError:
        return ""
    hostname = hostname.lower().strip(".")
    return hostname[4:] if hostname.startswith("www.") else hostname


def _same_official_domain(left: str, right: str) -> bool:
    left_host = _hostname(left)
    right_host = _hostname(right)
    if not left_host or not right_host:
        return False
    return (
        left_host == right_host
        or left_host.endswith(f".{right_host}")
        or right_host.endswith(f".{left_host}")
    )


def _relationship_quote_identifies_candidate(
    quote: str,
    *,
    bank_name: str,
    legal_name: str,
) -> bool:
    quote_tokens = set(re.findall(r"[a-z0-9]+", quote.casefold()))
    ignored = {
        "bank", "banking", "national", "association", "na", "usa", "us",
        "legal", "entity", "inc", "incorporated", "corp", "corporation", "llc",
    }
    candidate_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", bank_name.casefold())
        if token not in ignored
    ]
    if not candidate_tokens:
        candidate_tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", legal_name.casefold())
            if token not in ignored
        ]
    distinctive_tokens = set(candidate_tokens)
    if not distinctive_tokens:
        return False
    required_count = 1 if len(distinctive_tokens) == 1 else 2
    return len(distinctive_tokens.intersection(quote_tokens)) >= required_count


def _relationship_quote_identifies_coverage_domain(
    quote: str,
    *,
    coverage_host: str,
) -> bool:
    host_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", coverage_host.casefold())
        if token not in {"www", "com", "org", "net", "bank", "banking", "co"}
    ]
    if not host_tokens:
        return False
    quote_tokens = set(re.findall(r"[a-z0-9]+", quote.casefold()))
    return any(token in quote_tokens for token in host_tokens)


def _favicon_url(homepage_url: str) -> str:
    parts = urlsplit(homepage_url)
    return urlunsplit((parts.scheme, parts.netloc, "/favicon.ico", "", ""))


def _identity_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _identities_overlap(candidate_keys: set[str], known_keys: set[str]) -> bool:
    if candidate_keys & known_keys:
        return True
    for candidate in candidate_keys:
        for known in known_keys:
            if min(len(candidate), len(known)) >= 8 and (candidate in known or known in candidate):
                return True
    return False


def _positive_integer(value: Any) -> int | None:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return None
    return integer if integer > 0 else None


def _required_compact_text(value: Any, *, limit: int, allow_error: bool = True) -> str:
    text = _compact_text(value, limit=limit)
    if not text and allow_error:
        raise _insufficient_result_error()
    return text


def _compact_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _string_or_none(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}


def _normalize_country_code(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if len(normalized) != 2 or not normalized.isascii() or not normalized.isalpha():
        raise SourceRegistryError(
            status_code=422,
            code="invalid_country_code",
            message="country_code must be a two-letter ISO 3166-1 alpha-2 code.",
        )
    return normalized
