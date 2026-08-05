from __future__ import annotations

from datetime import datetime
import ipaddress
import json
import os
from pathlib import Path
import sys
from typing import Any, TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import path guard for `uv run --directory api/service`
    sys.path.insert(0, str(REPO_ROOT))

from api_service.review_detail import (
    MUTATION_ROLES,
    ReviewTaskError,
    _normalize_override_payload,
)
from api_service.security import new_id, utc_now
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
    requested_field_names = [
        str(item.get("field_name") or "")
        for item in _dict_list(request_payload.get("fields_to_verify"))
        if str(item.get("field_name") or "").strip()
    ]
    model_execution_id = new_id("modelexec")
    model_id = configured_model_id()
    started_at = utc_now()
    execution_metadata = {
        "review_task_id": str(review_task.get("review_task_id") or ""),
        "candidate_id": str(review_task.get("candidate_id") or ""),
        "requested_by_user_id": _string_or_none(actor.get("user_id")),
        "allowed_domains": allowed_domains,
        "verification_contract_version": "review-ai-verification-v1",
        "requested_field_names": requested_field_names,
        "requested_field_count": len(requested_field_names),
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
    for item in _dict_list(detail.get("review_field_items"))[:AI_VERIFICATION_MAX_FIELDS]:
        field_name = str(item.get("field_name") or "").strip()
        if (
            not field_name
            or field_name in seen_fields
            or field_name in AI_VERIFICATION_READ_ONLY_FIELDS
        ):
            continue
        seen_fields.add(field_name)
        review_fields.append(
            {
                "field_name": field_name,
                "label": str(item.get("label") or field_name),
                "collected_value": item.get("effective_value"),
                "missing": bool(item.get("missing")),
                "suspect": bool(item.get("suspect")),
                "issue_codes": _string_list(item.get("issue_codes")),
                "field_note": _string_or_none(item.get("field_note")),
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
        },
        "fields_to_verify": review_fields[:AI_VERIFICATION_MAX_FIELDS],
        "collected_candidate_payload": _mapping(candidate.get("candidate_payload")),
    }


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
        has_verified_value = bool(item.get("has_verified_value"))
        if has_verified_value:
            try:
                verified_value = json.loads(str(item.get("verified_value_json") or ""))
            except (json.JSONDecodeError, TypeError, ValueError):
                status = "unverified"
                has_verified_value = False
        if status in {"match", "mismatch"} and (
            not cited_sources or not has_verified_value
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
        "each requested canonical field with current official facts. Never infer a missing value. Mark a field "
        "unverified when the exact current fact is absent, ambiguous, personalized, dynamic, expired, or belongs "
        "to another product. Preserve canonical units: rates are numeric percentage points per annum, money is "
        "numeric in product currency, durations/counts are integers, booleans are true/false, and structured "
        "term rates are JSON arrays. Put a JSON-encoded canonical value in verified_value_json only when the "
        "official source states it directly. Every match or mismatch must cite at least one official source URL "
        "actually consulted. Keep rationale concise and operational. Do not approve, publish, or recommend a "
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
