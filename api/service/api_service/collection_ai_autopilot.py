from __future__ import annotations

from typing import Any, TYPE_CHECKING

from api_service.aggregate_refresh import queue_review_aggregate_refresh_request
from api_service.ai_verification import build_ai_verification_payload, run_review_ai_verification
from api_service.review_ai_correction import (
    apply_review_ai_corrections,
    assess_review_ai_auto_approval,
    persist_review_ai_auto_approval_assessment,
)
from api_service.review_detail import ReviewRequestContext, apply_review_decision, load_review_task_detail
from worker.pipeline.fpds_approval_policy import comparison_quality

if TYPE_CHECKING:
    from psycopg import Connection


DEFAULT_COLLECTION_AI_REVIEW_LIMIT = 200
DEFAULT_COLLECTION_AI_APPROVAL_THRESHOLD = 1.0
COLLECTION_AI_ACTOR = {
    "actor_type": "system",
    "role": "admin",
    "display_name": "FPDS collection AI autopilot",
}


def load_collection_ai_autopilot_policy(connection: Connection) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT DISTINCT ON (policy_key)
            policy_key,
            policy_value
        FROM processing_policy_config
        WHERE active_flag = true
          AND policy_key IN (
              'COLLECTION_AI_REVIEW_AUTOPILOT_ENABLED',
              'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
              'COLLECTION_AI_REVIEW_AUTOPILOT_MAX_CANDIDATES'
          )
        ORDER BY policy_key, version_no DESC
        """,
        {},
    ).fetchall()
    policy_map = {str(row["policy_key"]): row.get("policy_value") for row in rows}
    return {
        # The Product Owner instruction makes low-touch AI review the default;
        # the persisted policy still provides an auditable operational kill switch.
        "enabled": _coerce_policy_bool(
            policy_map.get("COLLECTION_AI_REVIEW_AUTOPILOT_ENABLED"),
            True,
        ),
        "approval_threshold": _coerce_policy_number(
            policy_map.get("COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE"),
            DEFAULT_COLLECTION_AI_APPROVAL_THRESHOLD,
            minimum=0.0,
            maximum=1.0,
        ),
        "max_candidates": int(
            _coerce_policy_number(
                policy_map.get("COLLECTION_AI_REVIEW_AUTOPILOT_MAX_CANDIDATES"),
                DEFAULT_COLLECTION_AI_REVIEW_LIMIT,
                minimum=1,
                maximum=1000,
            )
        ),
    }


def load_active_collection_review_task_ids(
    connection: Connection,
    *,
    run_id: str,
    limit: int,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT rt.review_task_id
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        JOIN source_document AS sd
          ON sd.source_document_id = nc.source_document_id
        WHERE rt.run_id = %(run_id)s
          AND rt.review_state IN ('queued', 'deferred')
          AND nc.candidate_state = 'in_review'
          AND COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') = 'detail'
          AND NOT (nc.validation_issue_codes ? 'ambiguous_product_boundary')
          AND NOT (
              COALESCE(
                  sd.source_metadata -> 'discovery_metadata' -> 'selection_reason_codes',
                  '[]'::jsonb
              ) ?| ARRAY[
                  'multi_product_family_overview',
                  'hub_page_not_detail',
                  'non_product_service_flow',
                  'non_product_editorial_page'
              ]
          )
          AND NOT (
              COALESCE(
                  sd.source_metadata -> 'discovery_metadata' -> 'page_evidence_reason_codes',
                  '[]'::jsonb
              ) ?| ARRAY[
                  'multi_product_family_overview',
                  'hub_page_not_detail',
                  'non_product_service_flow',
                  'non_product_editorial_page'
              ]
          )
        ORDER BY rt.created_at ASC, rt.review_task_id ASC
        LIMIT %(limit)s
        """,
        {"run_id": run_id, "limit": max(1, min(1000, int(limit)))},
    ).fetchall()
    return [str(row["review_task_id"]) for row in rows]


def remediate_collection_review_task(
    connection: Connection,
    *,
    review_task_id: str,
    approval_threshold: float,
    request_context: dict[str, Any],
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_actor = {**COLLECTION_AI_ACTOR, **(actor or {})}
    detail = load_review_task_detail(
        connection,
        review_task_id=review_task_id,
        actor_role=str(active_actor["role"]),
    )
    if not detail:
        return {
            "review_task_id": review_task_id,
            "status": "not_found",
            "approved": False,
        }
    review_state = str(detail["review_task"].get("review_state") or "")
    if review_state not in {"queued", "deferred"}:
        return {
            "review_task_id": review_task_id,
            "status": "already_closed",
            "approved": review_state in {"approved", "edited"},
        }

    execution = _load_latest_verification_execution(connection, review_task_id=review_task_id)
    if execution is not None and not _verification_matches_current_approval_fields(
        execution=execution,
        detail=detail,
    ):
        execution = None
    reused = execution is not None
    if execution is None:
        verification = run_review_ai_verification(
            connection,
            detail=detail,
            actor=active_actor,
            request_context=request_context,
        )
        if not verification.get("ok"):
            return {
                "review_task_id": review_task_id,
                "status": "verification_failed",
                "approved": False,
                "error_code": str((verification.get("error") or {}).get("code") or "ai_verification_failed"),
            }
        latest_attempt = (verification.get("ai_verification") or {}).get("latest_attempt") or {}
        model_execution_id = str(latest_attempt.get("model_execution_id") or "")
        execution = _load_verification_execution(
            connection,
            model_execution_id=model_execution_id,
        )

    if execution is None or str(execution.get("execution_status") or "") != "completed":
        return {
            "review_task_id": review_task_id,
            "status": "verification_failed",
            "approved": False,
            "reused_verification": reused,
        }

    model_execution_id = str(execution["model_execution_id"])
    execution_metadata = _mapping(execution.get("execution_metadata"))
    prior_assessment = _mapping(execution_metadata.get("auto_approval_assessment"))
    correction_result = {
        "applied": False,
        "changed_fields": [],
    }
    if not prior_assessment:
        correction_result = apply_review_ai_corrections(
            connection,
            review_task_id=review_task_id,
            model_execution_id=model_execution_id,
            actor=active_actor,
            request_context=request_context,
        )
        execution = _load_verification_execution(
            connection,
            model_execution_id=model_execution_id,
        )
        if execution is None:
            raise RuntimeError("AI verification execution disappeared before assessment.")
        execution_metadata = _mapping(execution.get("execution_metadata"))
        assessment = assess_review_ai_auto_approval(
            execution_status=str(execution.get("execution_status") or ""),
            execution_metadata=execution_metadata,
            threshold=approval_threshold,
        )
        persist_review_ai_auto_approval_assessment(
            connection,
            model_execution_id=model_execution_id,
            assessment=assessment,
        )
    else:
        assessment = prior_assessment

    if not bool(assessment.get("eligible")):
        return {
            "review_task_id": review_task_id,
            "model_execution_id": model_execution_id,
            "status": "review_retained",
            "approved": False,
            "reused_verification": reused,
            "changed_fields": list(correction_result.get("changed_fields") or []),
            "assessment": assessment,
        }

    current_detail = load_review_task_detail(
        connection,
        review_task_id=review_task_id,
        actor_role=str(active_actor["role"]),
    )
    guarded_assessment = _guard_assessment_against_current_comparison_contract(
        assessment=assessment,
        detail=current_detail,
    )
    if guarded_assessment != assessment:
        assessment = guarded_assessment
        persist_review_ai_auto_approval_assessment(
            connection,
            model_execution_id=model_execution_id,
            assessment=assessment,
        )
    if not bool(assessment.get("eligible")):
        return {
            "review_task_id": review_task_id,
            "model_execution_id": model_execution_id,
            "status": "review_retained",
            "approved": False,
            "reused_verification": reused,
            "changed_fields": list(correction_result.get("changed_fields") or []),
            "assessment": assessment,
        }

    approval_actor = {
        **active_actor,
        "ai_auto_approval_assessment": assessment,
        "ai_model_execution_id": model_execution_id,
    }
    decision = apply_review_decision(
        connection,
        review_task_id=review_task_id,
        action_type="approve",
        actor=approval_actor,
        reason_code="ai_verified_collection_auto_approval",
        reason_text=(
            "Collection AI verified official product identity and "
            f"{int(assessment.get('passed_field_count') or 0)}/"
            f"{int(assessment.get('requested_field_count') or 0)} requested fields."
        ),
        override_payload=None,
        context=ReviewRequestContext(
            request_id=str(request_context.get("request_id") or ""),
            ip_address=None,
            user_agent=str(request_context.get("user_agent") or "collection-ai-autopilot"),
        ),
    )
    aggregate_refresh = None
    if decision.get("product_id"):
        aggregate_refresh = queue_review_aggregate_refresh_request(
            connection,
            actor=approval_actor,
            request_context=request_context,
            review_task_id=review_task_id,
            product_id=str(decision["product_id"]),
            action_type="approve",
            change_event_types=[str(item) for item in decision.get("change_event_types", [])],
            country_code=str(decision["country_code"]),
        )
    return {
        "review_task_id": review_task_id,
        "model_execution_id": model_execution_id,
        "status": "approved",
        "approved": True,
        "reused_verification": reused,
        "changed_fields": list(correction_result.get("changed_fields") or []),
        "assessment": assessment,
        "decision": decision,
        "aggregate_refresh": aggregate_refresh,
    }


def _guard_assessment_against_current_comparison_contract(
    *,
    assessment: dict[str, Any],
    detail: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fail closed when corrections make new comparison fields essential."""

    if not detail:
        return _blocked_assessment(
            assessment,
            reason_code="review_detail_unavailable_before_approval",
        )
    candidate = _mapping(detail.get("candidate"))
    candidate_payload = {
        **_mapping(candidate.get("candidate_payload")),
        "product_name": candidate.get("product_name"),
    }
    quality = comparison_quality(
        product_type=str(candidate.get("product_type") or ""),
        country_code=str(candidate.get("country_code") or ""),
        expected_fields=[],
        candidate_payload=candidate_payload,
    )
    if quality.applicable and (not quality.contract_defined or not quality.complete):
        return _blocked_assessment(
            assessment,
            reason_code="essential_comparison_fields_missing_after_correction",
            comparison_contract_defined=quality.contract_defined,
            missing_comparison_fields=list(quality.missing_fields),
        )
    return assessment


def _blocked_assessment(
    assessment: dict[str, Any],
    *,
    reason_code: str,
    comparison_contract_defined: bool | None = None,
    missing_comparison_fields: list[str] | None = None,
) -> dict[str, Any]:
    reason_codes = [
        str(item)
        for item in assessment.get("reason_codes", [])
        if str(item)
    ] if isinstance(assessment.get("reason_codes"), list) else []
    if reason_code not in reason_codes:
        reason_codes.append(reason_code)
    guarded = {
        **assessment,
        "eligible": False,
        "reason_codes": reason_codes,
    }
    if comparison_contract_defined is not None:
        guarded["comparison_contract_defined"] = comparison_contract_defined
    if missing_comparison_fields is not None:
        guarded["missing_comparison_fields"] = missing_comparison_fields
    return guarded


def _load_latest_verification_execution(
    connection: Connection,
    *,
    review_task_id: str,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT model_execution_id, execution_status, execution_metadata
        FROM model_execution
        WHERE stage_name = 'ai_verification'
          AND execution_status = 'completed'
          AND execution_metadata ->> 'review_task_id' = %(review_task_id)s
          AND execution_metadata ->> 'verification_contract_version' = 'review-ai-verification-v19'
          AND completed_at >= now() - interval '24 hours'
        ORDER BY started_at DESC, model_execution_id DESC
        LIMIT 1
        """,
        {"review_task_id": review_task_id},
    ).fetchone()
    return dict(row) if row else None


def _verification_matches_current_approval_fields(
    *,
    execution: dict[str, Any],
    detail: dict[str, Any],
) -> bool:
    metadata = _mapping(execution.get("execution_metadata"))
    prior_fields = [
        str(item).strip()
        for item in metadata.get("approval_field_names", [])
        if str(item).strip()
    ] if isinstance(metadata.get("approval_field_names"), list) else []
    current_payload = build_ai_verification_payload(detail=detail, allowed_domains=[])
    current_fields = [
        str(item.get("field_name") or "").strip()
        for item in current_payload.get("fields_to_verify", [])
        if isinstance(item, dict) and str(item.get("field_name") or "").strip()
    ]
    return prior_fields == current_fields


def _load_verification_execution(
    connection: Connection,
    *,
    model_execution_id: str,
) -> dict[str, Any] | None:
    if not model_execution_id:
        return None
    row = connection.execute(
        """
        SELECT model_execution_id, execution_status, execution_metadata
        FROM model_execution
        WHERE model_execution_id = %(model_execution_id)s
          AND stage_name = 'ai_verification'
        """,
        {"model_execution_id": model_execution_id},
    ).fetchone()
    return dict(row) if row else None


def _coerce_policy_bool(value: object, default: bool) -> bool:
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return default


def _coerce_policy_number(
    value: object,
    default: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    if isinstance(value, dict):
        value = value.get("value")
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = float(default)
    return max(minimum, min(maximum, result))


def _mapping(value: object) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}
