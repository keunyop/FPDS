from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING
from urllib.parse import urlsplit

from api_service.review_detail import MUTATION_ROLES, ReviewTaskError, _normalize_override_payload
from api_service.security import new_id, utc_now

if TYPE_CHECKING:
    from psycopg import Connection


ACTIVE_REVIEW_STATES = {"queued", "deferred"}
AUTO_APPROVAL_THRESHOLD = 1.0
AI_CORRECTION_PROTECTED_SUPPRESSION_REASONS = {
    "mixed_account_scope_redeemability",
}


def assess_review_ai_auto_approval(
    *,
    execution_status: str,
    execution_metadata: dict[str, Any],
    threshold: float = AUTO_APPROVAL_THRESHOLD,
) -> dict[str, Any]:
    metadata = _mapping(execution_metadata)
    verification_result = _mapping(metadata.get("verification_result"))
    approval_field_source = (
        metadata.get("approval_field_names")
        if isinstance(metadata.get("approval_field_names"), list)
        else metadata.get("requested_field_names")
    )
    requested_fields = [
        str(item).strip()
        for item in approval_field_source or []
        if str(item).strip()
    ] if isinstance(approval_field_source, list) else []
    requested_fields = list(dict.fromkeys(requested_fields))
    fields_by_name = {
        str(item.get("field_name") or "").strip(): item
        for item in _mapping_list(verification_result.get("fields"))
        if str(item.get("field_name") or "").strip()
    }
    applied_corrections = _mapping(verification_result.get("applied_corrections"))
    authoritative_identity = _mapping(metadata.get("authoritative_identity_evidence"))
    authoritative_fields = _mapping(metadata.get("authoritative_field_evidence"))
    passed_fields = []
    origin_identity_passed = False
    origin_field_passes: list[str] = []
    for field_name in requested_fields:
        item = fields_by_name.get(field_name, {})
        status = str(item.get("status") or "")
        has_official_source = bool(_source_list(item.get("sources")))
        identity_verified_from_origin = bool(
            field_name == "product_name"
            and status == "unverified"
            and authoritative_identity.get("verified") is True
            and authoritative_identity.get("basis") == "exact_official_detail_h1"
            and authoritative_identity.get("source_url")
            and _url_matches_allowed_domains(
                str(authoritative_identity.get("source_url") or ""),
                metadata.get("allowed_domains"),
            )
        )
        origin_field = _mapping(authoritative_fields.get(field_name))
        field_verified_from_origin = bool(
            field_name != "product_name"
            and status == "unverified"
            and origin_field.get("verified") is True
            and origin_field.get("basis")
            in {
                "exact_official_detail_labeled_fee",
                "exact_official_detail_lending_comparison",
            }
            and origin_field.get("source_url")
            and _url_matches_allowed_domains(
                str(origin_field.get("source_url") or ""),
                metadata.get("allowed_domains"),
            )
        )
        if identity_verified_from_origin or field_verified_from_origin or (
            has_official_source
            and (
                status == "match"
                or (status == "mismatch" and field_name in applied_corrections and item.get("applied") is True)
            )
        ):
            passed_fields.append(field_name)
            origin_identity_passed = origin_identity_passed or identity_verified_from_origin
            if field_verified_from_origin:
                origin_field_passes.append(field_name)

    requested_count = len(requested_fields)
    passed_count = len(passed_fields)
    pass_rate = passed_count / requested_count if requested_count else 0.0
    remaining_corrections = _mapping(verification_result.get("proposed_corrections"))
    product_identity_verified = "product_name" in passed_fields
    reason_codes: list[str] = []
    if execution_status != "completed":
        reason_codes.append("verification_not_completed")
    if requested_count == 0:
        reason_codes.append("requested_field_contract_missing")
    if not product_identity_verified:
        reason_codes.append("product_identity_unverified")
    if remaining_corrections:
        reason_codes.append("corrections_not_applied")
    if (
        int(verification_result.get("source_count") or 0) <= 0
        and not origin_identity_passed
        and not origin_field_passes
    ):
        reason_codes.append("official_source_missing")
    hard_blocking_issue_codes = [
        str(item).strip()
        for item in metadata.get("hard_blocking_issue_codes", [])
        if str(item).strip()
    ] if isinstance(metadata.get("hard_blocking_issue_codes"), list) else []
    if hard_blocking_issue_codes:
        reason_codes.append("hard_validation_issue_unresolved")
    if pass_rate < threshold:
        reason_codes.append("verification_pass_rate_below_threshold")
    eligible = not reason_codes
    return {
        "eligible": eligible,
        "threshold": threshold,
        "requested_field_count": requested_count,
        "passed_field_count": passed_count,
        "pass_rate": round(pass_rate, 6),
        "passed_fields": passed_fields,
        "failed_or_unverified_fields": [
            field_name for field_name in requested_fields if field_name not in set(passed_fields)
        ],
        "product_identity_verified": product_identity_verified,
        "product_identity_verification_basis": (
            "exact_official_detail_h1"
            if origin_identity_passed
            else "review_ai_official_source"
            if product_identity_verified
            else None
        ),
        "authoritative_origin_fields": origin_field_passes,
        "hard_blocking_issue_codes": hard_blocking_issue_codes,
        "reason_codes": reason_codes,
    }


def _url_matches_allowed_domains(url: str, value: object) -> bool:
    host = (urlsplit(url).hostname or "").strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    allowed_domains = [
        str(item).strip(".").lower()
        for item in value
        if str(item).strip()
    ] if isinstance(value, list) else []
    return bool(
        host
        and any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)
    )


def persist_review_ai_auto_approval_assessment(
    connection: Connection,
    *,
    model_execution_id: str,
    assessment: dict[str, Any],
) -> None:
    row = connection.execute(
        """
        SELECT execution_metadata
        FROM model_execution
        WHERE model_execution_id = %(model_execution_id)s
          AND stage_name = 'ai_verification'
        FOR UPDATE
        """,
        {"model_execution_id": model_execution_id},
    ).fetchone()
    if not row:
        raise ReviewTaskError(
            status_code=404,
            code="review_ai_verification_not_found",
            message="The AI verification attempt was not found for approval assessment.",
        )
    execution_metadata = _mapping(row.get("execution_metadata"))
    execution_metadata["auto_approval_assessment"] = _mapping(assessment)
    connection.execute(
        """
        UPDATE model_execution
        SET execution_metadata = %(execution_metadata)s::jsonb
        WHERE model_execution_id = %(model_execution_id)s
        """,
        {
            "execution_metadata": json.dumps(execution_metadata, ensure_ascii=True, sort_keys=True),
            "model_execution_id": model_execution_id,
        },
    )


def apply_review_ai_corrections(
    connection: Connection,
    *,
    review_task_id: str,
    model_execution_id: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    """Apply sanitized AI mismatches before a separate approval assessment."""

    if str(actor.get("role") or "") not in MUTATION_ROLES:
        raise ReviewTaskError(
            status_code=403,
            code="forbidden",
            message="This account cannot apply AI candidate corrections.",
        )

    row = connection.execute(
        """
        SELECT
            rt.review_task_id,
            rt.candidate_id,
            rt.run_id,
            rt.product_id,
            rt.review_state,
            nc.candidate_state,
            nc.product_name,
            nc.candidate_payload,
            nc.field_mapping_metadata,
            me.stage_name,
            me.execution_status,
            me.execution_metadata
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        JOIN model_execution AS me
          ON me.model_execution_id = %(model_execution_id)s
        WHERE rt.review_task_id = %(review_task_id)s
        FOR UPDATE OF rt, nc, me
        """,
        {
            "review_task_id": review_task_id,
            "model_execution_id": model_execution_id,
        },
    ).fetchone()
    if not row:
        raise ReviewTaskError(
            status_code=404,
            code="review_ai_verification_not_found",
            message="The review task or AI verification attempt was not found.",
        )
    review_state = str(row["review_state"])
    if review_state not in ACTIVE_REVIEW_STATES:
        raise ReviewTaskError(
            status_code=409,
            code="review_task_not_correctable",
            message="Only queued or deferred review tasks can receive AI candidate corrections.",
        )
    execution_metadata = _mapping(row.get("execution_metadata"))
    if (
        str(row.get("stage_name") or "") != "ai_verification"
        or str(row.get("execution_status") or "") != "completed"
        or str(execution_metadata.get("review_task_id") or "") != review_task_id
        or str(execution_metadata.get("candidate_id") or "") != str(row["candidate_id"])
    ):
        raise ReviewTaskError(
            status_code=409,
            code="review_ai_verification_mismatch",
            message="The AI verification attempt does not belong to this active candidate.",
        )

    verification_result = _mapping(execution_metadata.get("verification_result"))
    proposed_corrections = _mapping(verification_result.get("proposed_corrections"))
    candidate_payload = {
        **_mapping(row.get("candidate_payload")),
        "product_name": str(row.get("product_name") or ""),
    }
    normalized_corrections = _normalize_override_payload(
        override_payload=proposed_corrections,
        base_payload=candidate_payload,
    )
    eligible_fields = {
        str(item.get("field_name") or ""): item
        for item in _mapping_list(verification_result.get("fields"))
        if item.get("can_apply") is True
        and str(item.get("status") or "") == "mismatch"
        and str(item.get("evidence_quote") or "").strip()
        and _source_list(item.get("sources"))
    }
    normalized_corrections = {
        field_name: value
        for field_name, value in normalized_corrections.items()
        if field_name in eligible_fields
        and eligible_fields[field_name].get("proposed_value") == value
        and str(
            _mapping(_mapping(row.get("field_mapping_metadata")).get(field_name)).get(
                "suppressed_reason"
            )
            or ""
        )
        not in AI_CORRECTION_PROTECTED_SUPPRESSION_REASONS
    }
    if not normalized_corrections:
        return {
            "review_task_id": review_task_id,
            "candidate_id": str(row["candidate_id"]),
            "review_state": review_state,
            "changed_fields": [],
            "applied": False,
        }

    corrected_at = utc_now()
    corrected_payload = {**candidate_payload, **normalized_corrections}
    corrected_product_name = str(corrected_payload.get("product_name") or row.get("product_name") or "").strip()
    corrected_payload["product_name"] = corrected_product_name
    field_mapping_metadata = _mapping(row.get("field_mapping_metadata"))
    for field_name, value in normalized_corrections.items():
        verification_field = eligible_fields[field_name]
        existing_mapping = _mapping(field_mapping_metadata.get(field_name))
        field_mapping_metadata[field_name] = {
            **existing_mapping,
            "normalized_value": value,
            "extraction_method": "review_ai_verification",
            "normalization_method": "review_ai_correction",
            "extraction_confidence": verification_field.get("confidence"),
            "model_execution_id": model_execution_id,
            "ai_verification_status": "applied_mismatch",
            "ai_verification_rationale": str(verification_field.get("rationale") or ""),
            "ai_verification_sources": _source_list(verification_field.get("sources")),
            "official_evidence_quote": str(verification_field.get("evidence_quote") or "")[:700],
            "ai_verification_corrected_at": corrected_at.isoformat(),
            "ai_verification_contract_version": str(
                execution_metadata.get("verification_contract_version") or "review-ai-verification-v19"
            ),
        }

    changed_fields = sorted(normalized_corrections)
    diff_summary = _diff_summary(
        changed_fields=changed_fields,
        before=candidate_payload,
        after=corrected_payload,
    )
    connection.execute(
        """
        UPDATE normalized_candidate
        SET
            product_name = %(product_name)s,
            candidate_payload = %(candidate_payload)s::jsonb,
            field_mapping_metadata = %(field_mapping_metadata)s::jsonb,
            updated_at = %(updated_at)s
        WHERE candidate_id = %(candidate_id)s
        """,
        {
            "product_name": corrected_product_name,
            "candidate_payload": json.dumps(corrected_payload, ensure_ascii=True, sort_keys=True),
            "field_mapping_metadata": json.dumps(field_mapping_metadata, ensure_ascii=True, sort_keys=True),
            "updated_at": corrected_at,
            "candidate_id": row["candidate_id"],
        },
    )
    connection.execute(
        """
        UPDATE review_task
        SET updated_at = %(updated_at)s
        WHERE review_task_id = %(review_task_id)s
        """,
        {"updated_at": corrected_at, "review_task_id": review_task_id},
    )

    applied_field_names = set(changed_fields)
    verification_result["applied_corrections"] = normalized_corrections
    verification_result["proposed_corrections"] = {
        field_name: value
        for field_name, value in proposed_corrections.items()
        if field_name not in applied_field_names
    }
    verification_result["correction_status"] = "applied"
    verification_result["correction_applied_at"] = corrected_at.isoformat()
    verification_result["fields"] = [
        {
            **item,
            "can_apply": False if str(item.get("field_name") or "") in applied_field_names else item.get("can_apply"),
            **(
                {"applied": True, "applied_at": corrected_at.isoformat()}
                if str(item.get("field_name") or "") in applied_field_names
                else {}
            ),
        }
        for item in _mapping_list(verification_result.get("fields"))
    ]
    execution_metadata["verification_result"] = verification_result
    execution_metadata["correction_applied_at"] = corrected_at.isoformat()
    execution_metadata["correction_changed_fields"] = changed_fields
    connection.execute(
        """
        UPDATE model_execution
        SET execution_metadata = %(execution_metadata)s::jsonb
        WHERE model_execution_id = %(model_execution_id)s
        """,
        {
            "execution_metadata": json.dumps(execution_metadata, ensure_ascii=True, sort_keys=True),
            "model_execution_id": model_execution_id,
        },
    )
    _record_correction_audit(
        connection,
        actor=actor,
        request_context=request_context,
        row=row,
        model_execution_id=model_execution_id,
        review_state=review_state,
        changed_fields=changed_fields,
        corrections=normalized_corrections,
        diff_summary=diff_summary,
        sources=_dedupe_sources(
            source
            for field_name in changed_fields
            for source in _source_list(eligible_fields[field_name].get("sources"))
        ),
        corrected_at=corrected_at,
    )
    return {
        "review_task_id": review_task_id,
        "candidate_id": str(row["candidate_id"]),
        "review_state": review_state,
        "changed_fields": changed_fields,
        "applied": True,
    }


def _record_correction_audit(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    row: dict[str, Any],
    model_execution_id: str,
    review_state: str,
    changed_fields: list[str],
    corrections: dict[str, Any],
    diff_summary: str,
    sources: list[dict[str, str]],
    corrected_at: Any,
) -> None:
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
            'review_ai_corrections_applied',
            %(actor_type)s,
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'review_task',
            %(target_id)s,
            %(review_state)s,
            %(review_state)s,
            'ai_verified_candidate_correction',
            'Official-domain AI corrections applied; review state is preserved until a separate approval assessment.',
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
            "actor_type": actor_type,
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": row["review_task_id"],
            "review_state": review_state,
            "run_id": row["run_id"],
            "candidate_id": row["candidate_id"],
            "review_task_id": row["review_task_id"],
            "product_id": row.get("product_id"),
            "request_id": request_context.get("request_id"),
            "diff_summary": diff_summary,
            "source_ref": sources[0]["url"] if sources else None,
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "event_payload": json.dumps(
                {
                    "model_execution_id": model_execution_id,
                    "changed_fields": changed_fields,
                    "corrections": corrections,
                    "sources": sources,
                    "review_state_preserved": True,
                    "canonical_product_mutated": False,
                    "public_projection_mutated": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
            "occurred_at": corrected_at,
        },
    )


def _diff_summary(*, changed_fields: list[str], before: dict[str, Any], after: dict[str, Any]) -> str:
    parts = [
        f"{field_name}: {_short(before.get(field_name))} -> {_short(after.get(field_name))}"
        for field_name in changed_fields[:5]
    ]
    if len(changed_fields) > 5:
        parts.append(f"+{len(changed_fields) - 5} more")
    return "; ".join(parts)


def _short(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return rendered if len(rendered) <= 80 else f"{rendered[:77]}..."


def _mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, dict) else {}


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    return [_mapping(item) for item in value] if isinstance(value, list) else []


def _source_list(value: Any) -> list[dict[str, str]]:
    return [
        {"url": str(item.get("url") or ""), "title": str(item.get("title") or "")}
        for item in _mapping_list(value)
        if str(item.get("url") or "").strip()
    ]


def _dedupe_sources(sources: Any) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        result.append({"url": url, "title": str(source.get("title") or "")})
    return result
