from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any
from typing import TYPE_CHECKING

from api_service.security import new_id, utc_now

if TYPE_CHECKING:
    from psycopg import Connection


MUTATION_ROLES = {"admin", "reviewer"}
TERMINAL_REVIEW_STATES = {"approved", "rejected", "edited"}
ACTION_TO_STATE = {
    "approve": "approved",
    "reject": "rejected",
    "edit_approve": "edited",
    "defer": "deferred",
}
MODEL_EXECUTION_STAGE_ORDER = {
    "extraction": 0,
    "normalization": 1,
    "validation_routing": 2,
}


@dataclass(frozen=True)
class ReviewRequestContext:
    request_id: str
    ip_address: str | None
    user_agent: str | None


class ReviewTaskError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def load_review_task_detail(
    connection: Connection,
    *,
    review_task_id: str,
    actor_role: str,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            rt.review_task_id,
            rt.candidate_id,
            rt.run_id,
            rt.product_id,
            rt.review_state,
            rt.queue_reason_code,
            rt.issue_summary,
            rt.created_at AS review_created_at,
            rt.updated_at AS review_updated_at,
            nc.source_document_id,
            nc.country_code,
            nc.bank_code,
            COALESCE(b.bank_name, nc.bank_code) AS bank_name,
            nc.product_family,
            nc.product_type,
            nc.subtype_code,
            nc.product_name,
            nc.source_language,
            nc.currency,
            nc.candidate_state,
            nc.validation_status,
            nc.validation_issue_codes,
            nc.source_confidence,
            nc.review_reason_code,
            nc.candidate_payload,
            nc.field_mapping_metadata,
            nc.model_execution_id AS candidate_model_execution_id,
            sd.normalized_source_url AS source_url,
            sd.source_type,
            sd.source_metadata,
            ss.snapshot_id,
            ss.fetched_at,
            pd.parsed_document_id,
            pd.parse_quality_note,
            rsi.stage_status,
            rsi.warning_count,
            rsi.error_count,
            rsi.error_summary,
            COALESCE(rsi.stage_metadata, '{}'::jsonb) AS stage_metadata,
            COALESCE(rsi.stage_metadata -> 'runtime_notes', '[]'::jsonb) AS runtime_notes
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        LEFT JOIN bank AS b
          ON b.bank_code = nc.bank_code
        JOIN source_document AS sd
          ON sd.source_document_id = nc.source_document_id
        LEFT JOIN run_source_item AS rsi
          ON rsi.run_id = rt.run_id
         AND rsi.source_document_id = nc.source_document_id
        LEFT JOIN source_snapshot AS ss
          ON ss.snapshot_id = rsi.selected_snapshot_id
        LEFT JOIN parsed_document AS pd
          ON pd.snapshot_id = ss.snapshot_id
        WHERE rt.review_task_id = %(review_task_id)s
        """,
        {"review_task_id": review_task_id},
    ).fetchone()
    if not row:
        return None

    evidence_rows = connection.execute(
        """
        SELECT
            fel.field_name,
            fel.candidate_value,
            fel.citation_confidence,
            fel.evidence_chunk_id,
            fel.source_document_id,
            ec.evidence_excerpt,
            ec.anchor_type,
            ec.anchor_value,
            ec.page_no,
            ec.chunk_index,
            ec.parsed_document_id,
            pd.snapshot_id AS source_snapshot_id,
            sd.normalized_source_url AS source_url,
            sd.source_type,
            sd.source_metadata
        FROM field_evidence_link AS fel
        JOIN evidence_chunk AS ec
          ON ec.evidence_chunk_id = fel.evidence_chunk_id
        JOIN parsed_document AS pd
          ON pd.parsed_document_id = ec.parsed_document_id
        JOIN source_document AS sd
          ON sd.source_document_id = fel.source_document_id
        WHERE fel.candidate_id = %(candidate_id)s
        ORDER BY fel.field_name, ec.chunk_index
        """,
        {"candidate_id": row["candidate_id"]},
    ).fetchall()

    history_rows = connection.execute(
        """
        SELECT
            rd.review_decision_id,
            rd.action_type,
            rd.reason_code,
            rd.reason_text,
            rd.diff_summary,
            rd.override_payload,
            rd.decided_at,
            ua.user_id AS actor_user_id,
            ua.display_name AS actor_display_name,
            ua.email AS actor_email,
            ua.role AS actor_role
        FROM review_decision AS rd
        LEFT JOIN user_account AS ua
          ON ua.user_id = rd.actor_user_id
        WHERE rd.review_task_id = %(review_task_id)s
        ORDER BY rd.decided_at DESC, rd.review_decision_id DESC
        """,
        {"review_task_id": review_task_id},
    ).fetchall()

    issue_items = _coerce_issue_items(row.get("issue_summary"))
    candidate_payload = _coerce_mapping(row.get("candidate_payload"))
    field_mapping_metadata = _coerce_mapping(row.get("field_mapping_metadata"))
    source_metadata = _coerce_mapping(row.get("source_metadata"))
    stage_metadata = _coerce_mapping(row.get("stage_metadata"))
    evidence_links = [
        _serialize_evidence_row(
            item,
            field_mapping_metadata=field_mapping_metadata,
            stage_metadata=stage_metadata,
        )
        for item in evidence_rows
    ]
    field_trace_groups = _build_field_trace_groups(
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        evidence_links=evidence_links,
    )
    validation_issue_codes = _coerce_string_list(row.get("validation_issue_codes"))
    model_executions = _load_model_execution_references(
        connection,
        candidate_model_execution_id=_string_or_none(row.get("candidate_model_execution_id")),
        stage_metadata=stage_metadata,
    )

    return {
        "review_task": {
            "review_task_id": str(row["review_task_id"]),
            "candidate_id": str(row["candidate_id"]),
            "run_id": str(row["run_id"]),
            "product_id": str(row["product_id"]) if row.get("product_id") else None,
            "review_state": str(row["review_state"]),
            "queue_reason_code": str(row["queue_reason_code"]),
            "issue_summary": _summarize_issue_items(issue_items, fallback_reason=str(row["queue_reason_code"])),
            "issue_summary_items": issue_items,
            "created_at": row["review_created_at"].isoformat(),
            "updated_at": row["review_updated_at"].isoformat(),
        },
        "candidate": {
            "source_document_id": str(row["source_document_id"]),
            "country_code": str(row["country_code"]),
            "bank_code": str(row["bank_code"]),
            "bank_name": str(row["bank_name"]),
            "product_family": str(row["product_family"]),
            "product_type": str(row["product_type"]),
            "subtype_code": _string_or_none(row.get("subtype_code")),
            "product_name": str(row["product_name"]),
            "source_language": str(row["source_language"]),
            "currency": str(row["currency"]),
            "candidate_state": str(row["candidate_state"]),
            "validation_status": str(row["validation_status"]),
            "validation_issue_codes": validation_issue_codes,
            "source_confidence": _serialize_confidence(row.get("source_confidence")),
            "review_reason_code": _string_or_none(row.get("review_reason_code")),
            "candidate_payload": candidate_payload,
            "field_mapping_metadata": field_mapping_metadata,
            "field_items": [
                {
                    "field_name": field_name,
                    "label": _titleize(field_name),
                    "value": value,
                }
                for field_name, value in sorted(candidate_payload.items())
                if not _is_empty_review_value(value)
            ],
        },
        "source_context": {
            "source_url": _string_or_none(row.get("source_url")),
            "source_type": _string_or_none(row.get("source_type")),
            "source_id": _string_or_none(source_metadata.get("source_id")),
            "snapshot_id": _string_or_none(row.get("snapshot_id")),
            "fetched_at": row["fetched_at"].isoformat() if row.get("fetched_at") else None,
            "parsed_document_id": _string_or_none(row.get("parsed_document_id")),
            "parse_quality_note": _string_or_none(row.get("parse_quality_note")),
            "stage_status": _string_or_none(row.get("stage_status")),
            "warning_count": int(row["warning_count"]) if row.get("warning_count") is not None else None,
            "error_count": int(row["error_count"]) if row.get("error_count") is not None else None,
            "error_summary": _string_or_none(row.get("error_summary")),
            "runtime_notes": _coerce_string_list(row.get("runtime_notes")),
        },
        "proposed_fields": [
            {
                "field_name": item["field_name"],
                "label": item["label"],
                "value": item["value"],
                "evidence_count": item["evidence_count"],
            }
            for item in field_trace_groups
        ],
        "field_trace_groups": field_trace_groups,
        "evidence_summary": {
            "item_count": len(evidence_links),
            "field_count": len({item["field_name"] for item in evidence_links}),
        },
        "evidence_links": evidence_links,
        "validation_issues": _build_validation_issues(
            issue_items=issue_items,
            validation_issue_codes=validation_issue_codes,
            validation_status=str(row["validation_status"]),
        ),
        "model_executions": model_executions,
        "current_product": _load_current_product_summary(connection, review_row=row),
        "decision_history": [_serialize_decision_row(item) for item in history_rows],
        "available_actions": _available_actions(review_state=str(row["review_state"]), actor_role=actor_role),
    }


def record_evidence_trace_viewed(
    connection: Connection,
    *,
    actor: dict[str, Any],
    review_task_id: str,
    run_id: str,
    candidate_id: str,
    product_id: str | None,
    request_id: str,
    ip_address: str | None,
    user_agent: str | None,
    field_count: int,
    evidence_item_count: int,
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
            run_id,
            candidate_id,
            review_task_id,
            product_id,
            request_id,
            reason_text,
            ip_address,
            user_agent,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            'evidence_trace_viewed',
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'review_task',
            %(target_id)s,
            %(run_id)s,
            %(candidate_id)s,
            %(review_task_id)s,
            %(product_id)s,
            %(request_id)s,
            %(reason_text)s,
            %(ip_address)s,
            %(user_agent)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": review_task_id,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "review_task_id": review_task_id,
            "product_id": product_id,
            "request_id": request_id,
            "reason_text": "Review detail trace context was opened.",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "event_payload": json.dumps(
                {
                    "field_count": field_count,
                    "evidence_item_count": evidence_item_count,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
            "occurred_at": utc_now(),
        },
    )


def record_evidence_trace_viewed_best_effort(
    connection: Connection,
    *,
    actor: dict[str, Any],
    review_task_id: str,
    run_id: str,
    candidate_id: str,
    product_id: str | None,
    request_id: str,
    ip_address: str | None,
    user_agent: str | None,
    field_count: int,
    evidence_item_count: int,
    statement_timeout_ms: int = 3000,
) -> None:
    try:
        connection.execute(f"SET LOCAL statement_timeout = '{int(statement_timeout_ms)}ms'", {})
        record_evidence_trace_viewed(
            connection,
            actor=actor,
            review_task_id=review_task_id,
            run_id=run_id,
            candidate_id=candidate_id,
            product_id=product_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            field_count=field_count,
            evidence_item_count=evidence_item_count,
        )
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()


def apply_review_decision(
    connection: Connection,
    *,
    review_task_id: str,
    action_type: str,
    actor: dict[str, Any],
    reason_code: str | None,
    reason_text: str | None,
    override_payload: dict[str, Any] | None,
    context: ReviewRequestContext,
) -> dict[str, Any]:
    actor_role = str(actor.get("role", ""))
    if actor_role not in MUTATION_ROLES:
        raise ReviewTaskError(status_code=403, code="forbidden", message="This account cannot change review decisions.")

    if action_type not in ACTION_TO_STATE:
        raise ReviewTaskError(status_code=400, code="invalid_action", message="Unsupported review action.")

    review_row = _load_locked_review_task(connection, review_task_id=review_task_id)
    current_state = str(review_row["review_state"])
    target_state = ACTION_TO_STATE[action_type]
    if current_state in TERMINAL_REVIEW_STATES:
        if _can_reedit_review(current_state=current_state, action_type=action_type):
            pass
        elif current_state == target_state:
            return {
                "review_task_id": review_task_id,
                "review_state": current_state,
                "already_applied": True,
            }
        else:
            raise ReviewTaskError(
                status_code=409,
                code="review_task_already_closed",
                message="Terminal review tasks cannot transition to a different decision.",
            )

    normalized_reason_code = _normalize_text(reason_code)
    normalized_reason_text = _normalize_text(reason_text)
    normalized_override_payload = _normalize_override_payload(
        override_payload=override_payload,
        base_payload=_coerce_mapping(review_row.get("candidate_payload")),
    )

    if action_type in {"reject", "defer"} and not (normalized_reason_code or normalized_reason_text):
        raise ReviewTaskError(
            status_code=400,
            code="decision_reason_required",
            message="Reject and defer actions need a reason code or a note.",
        )
    if action_type != "edit_approve" and normalized_override_payload:
        raise ReviewTaskError(
            status_code=400,
            code="override_not_allowed",
            message="Override payload is only allowed for edit-and-approve.",
        )
    if action_type == "edit_approve" and not normalized_override_payload:
        raise ReviewTaskError(
            status_code=400,
            code="override_required",
            message="Edit-and-approve needs at least one changed field.",
        )
    if action_type == "edit_approve" and not normalized_reason_code:
        normalized_reason_code = "manual_override"

    decided_at = utc_now()
    candidate_payload = _coerce_mapping(review_row.get("candidate_payload"))
    approved_payload = {
        **candidate_payload,
        **normalized_override_payload,
    }
    approved_product_name = _approved_product_name(review_row=review_row, approved_payload=approved_payload)
    persisted_candidate_payload = {
        **candidate_payload,
        "product_name": approved_product_name,
    }
    changed_fields = sorted(normalized_override_payload.keys())
    diff_summary = _build_diff_summary(
        changed_fields=changed_fields,
        before_payload=candidate_payload,
        after_payload=approved_payload,
    )
    candidate_state = _candidate_state_for_action(action_type)

    product_result: dict[str, Any] | None = None
    if action_type in {"approve", "edit_approve"}:
        product_result = _apply_canonical_approval(
            connection,
            review_row=review_row,
            approved_payload=approved_payload,
            override_changed_fields=changed_fields,
            action_type=action_type,
            actor=actor,
            decided_at=decided_at,
            request_id=context.request_id,
        )

    connection.execute(
        """
        UPDATE review_task
        SET
            review_state = %(review_state)s,
            product_id = COALESCE(%(product_id)s, product_id),
            updated_at = %(updated_at)s
        WHERE review_task_id = %(review_task_id)s
        """,
        {
            "review_state": target_state,
            "product_id": product_result["product_id"] if product_result else None,
            "updated_at": decided_at,
            "review_task_id": review_task_id,
        },
    )
    connection.execute(
        """
        UPDATE normalized_candidate
        SET
            candidate_state = %(candidate_state)s,
            review_reason_code = %(review_reason_code)s,
            product_name = %(product_name)s,
            candidate_payload = %(candidate_payload)s::jsonb,
            updated_at = %(updated_at)s
        WHERE candidate_id = %(candidate_id)s
        """,
        {
            "candidate_state": candidate_state,
            "review_reason_code": normalized_reason_code,
            "product_name": approved_product_name,
            "candidate_payload": json.dumps(persisted_candidate_payload, ensure_ascii=True, sort_keys=True),
            "updated_at": decided_at,
            "candidate_id": review_row["candidate_id"],
        },
    )
    connection.execute(
        """
        INSERT INTO review_decision (
            review_decision_id,
            review_task_id,
            actor_user_id,
            action_type,
            reason_code,
            reason_text,
            diff_summary,
            override_payload,
            decided_at
        )
        VALUES (
            %(review_decision_id)s,
            %(review_task_id)s,
            %(actor_user_id)s,
            %(action_type)s,
            %(reason_code)s,
            %(reason_text)s,
            %(diff_summary)s,
            %(override_payload)s::jsonb,
            %(decided_at)s
        )
        """,
        {
            "review_decision_id": new_id("rdec"),
            "review_task_id": review_task_id,
            "actor_user_id": actor.get("user_id"),
            "action_type": action_type,
            "reason_code": normalized_reason_code,
            "reason_text": normalized_reason_text,
            "diff_summary": diff_summary,
            "override_payload": json.dumps(normalized_override_payload, ensure_ascii=True, sort_keys=True),
            "decided_at": decided_at,
        },
    )

    _record_review_audit_event(
        connection,
        event_type={
            "approve": "review_task_approved",
            "reject": "review_task_rejected",
            "edit_approve": "review_task_edited",
            "defer": "review_task_deferred",
        }[action_type],
        actor=actor,
        target_id=review_task_id,
        previous_state=current_state,
        new_state=target_state,
        reason_code=normalized_reason_code,
        reason_text=normalized_reason_text,
        run_id=str(review_row["run_id"]),
        candidate_id=str(review_row["candidate_id"]),
        review_task_id=review_task_id,
        product_id=product_result["product_id"] if product_result else None,
        request_id=context.request_id,
        diff_summary=diff_summary,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        payload={
            "approved_product_id": product_result["product_id"] if product_result else None,
            "product_version_id": product_result["product_version_id"] if product_result else None,
            "change_event_types": product_result["change_event_types"] if product_result else [],
            "changed_fields": changed_fields,
        },
    )
    return {
        "review_task_id": review_task_id,
        "review_state": target_state,
        "product_id": product_result["product_id"] if product_result else None,
        "product_version_id": product_result["product_version_id"] if product_result else None,
        "change_event_types": product_result["change_event_types"] if product_result else [],
        "already_applied": False,
    }


def _apply_canonical_approval(
    connection: Connection,
    *,
    review_row: dict[str, Any],
    approved_payload: dict[str, Any],
    override_changed_fields: list[str],
    action_type: str,
    actor: dict[str, Any],
    decided_at: datetime,
    request_id: str,
) -> dict[str, Any]:
    current_product = _find_current_product(connection, review_row=review_row, approved_payload=approved_payload)
    product_id = current_product["product_id"] if current_product else new_id("prod")
    current_payload = _coerce_mapping(current_product.get("normalized_payload")) if current_product else {}
    current_version_no = int(current_product["current_version_no"]) if current_product else 0
    base_changed_fields = _changed_field_names(before=current_payload, after=approved_payload)
    requires_new_version = current_product is None or bool(base_changed_fields)
    product_version_id: str | None = None
    change_event_types: list[str] = []

    if current_product is None:
        connection.execute(
            """
            INSERT INTO canonical_product (
                product_id,
                bank_code,
                country_code,
                product_family,
                product_type,
                subtype_code,
                product_name,
                source_language,
                currency,
                status,
                current_version_no,
                last_verified_at,
                last_changed_at,
                current_snapshot_payload
            )
            VALUES (
                %(product_id)s,
                %(bank_code)s,
                %(country_code)s,
                %(product_family)s,
                %(product_type)s,
                %(subtype_code)s,
                %(product_name)s,
                %(source_language)s,
                %(currency)s,
                %(status)s,
                1,
                %(last_verified_at)s,
                %(last_changed_at)s,
                %(current_snapshot_payload)s::jsonb
            )
            """,
            _canonical_product_params(
                review_row=review_row,
                approved_payload=approved_payload,
                product_id=product_id,
                current_version_no=1,
                last_verified_at=decided_at,
                last_changed_at=decided_at,
            ),
        )
        product_version_id = new_id("pver")
        _insert_product_version(
            connection,
            product_version_id=product_version_id,
            product_id=product_id,
            approved_candidate_id=_product_version_approved_candidate_id(review_row=review_row, action_type=action_type),
            version_no=1,
            normalized_payload=approved_payload,
            approved_at=decided_at,
        )
        _clone_field_evidence_links(
            connection,
            candidate_id=str(review_row["candidate_id"]),
            product_version_id=product_version_id,
            skipped_fields=set(override_changed_fields),
        )
        _insert_change_event(
            connection,
            product_id=product_id,
            product_version_id=product_version_id,
            run_id=str(review_row["run_id"]),
            review_task_id=str(review_row["review_task_id"]),
            event_type="New",
            event_reason_code=None,
            detected_at=decided_at,
            metadata={
                "previous_version_no": None,
                "current_version_no": 1,
                "changed_field_names": sorted(base_changed_fields),
            },
        )
        change_event_types.append("New")
    elif requires_new_version:
        previous_version_no = current_version_no
        next_version_no = current_version_no + 1
        product_version_id = new_id("pver")
        connection.execute(
            """
            UPDATE product_version
            SET
                version_status = 'superseded',
                superseded_at = %(superseded_at)s
            WHERE product_id = %(product_id)s
              AND version_no = %(version_no)s
            """,
            {
                "superseded_at": decided_at,
                "product_id": product_id,
                "version_no": previous_version_no,
            },
        )
        _insert_product_version(
            connection,
            product_version_id=product_version_id,
            product_id=product_id,
            approved_candidate_id=_product_version_approved_candidate_id(review_row=review_row, action_type=action_type),
            version_no=next_version_no,
            normalized_payload=approved_payload,
            approved_at=decided_at,
        )
        _clone_field_evidence_links(
            connection,
            candidate_id=str(review_row["candidate_id"]),
            product_version_id=product_version_id,
            skipped_fields=set(override_changed_fields),
        )
        connection.execute(
            """
            UPDATE canonical_product
            SET
                product_type = %(product_type)s,
                subtype_code = %(subtype_code)s,
                product_name = %(product_name)s,
                source_language = %(source_language)s,
                currency = %(currency)s,
                status = %(status)s,
                current_version_no = %(current_version_no)s,
                last_verified_at = %(last_verified_at)s,
                last_changed_at = %(last_changed_at)s,
                current_snapshot_payload = %(current_snapshot_payload)s::jsonb,
                updated_at = %(updated_at)s
            WHERE product_id = %(product_id)s
            """,
            _canonical_product_params(
                review_row=review_row,
                approved_payload=approved_payload,
                product_id=product_id,
                current_version_no=next_version_no,
                last_verified_at=decided_at,
                last_changed_at=decided_at,
            ),
        )
        change_event_type = "Reclassified" if _is_reclassified(current_product=current_product, review_row=review_row) else "Updated"
        change_reason_code = "taxonomy_reclassified" if change_event_type == "Reclassified" else "source_content_changed"
        _insert_change_event(
            connection,
            product_id=product_id,
            product_version_id=product_version_id,
            run_id=str(review_row["run_id"]),
            review_task_id=str(review_row["review_task_id"]),
            event_type=change_event_type,
            event_reason_code=change_reason_code,
            detected_at=decided_at,
            metadata={
                "previous_version_no": previous_version_no,
                "current_version_no": next_version_no,
                "changed_field_names": sorted(base_changed_fields),
            },
        )
        change_event_types.append(change_event_type)
    else:
        connection.execute(
            """
            UPDATE canonical_product
            SET
                last_verified_at = %(last_verified_at)s,
                updated_at = %(updated_at)s
            WHERE product_id = %(product_id)s
            """,
            {
                "last_verified_at": decided_at,
                "updated_at": decided_at,
                "product_id": product_id,
            },
        )

    if action_type == "edit_approve" and override_changed_fields and product_version_id:
        _insert_change_event(
            connection,
            product_id=product_id,
            product_version_id=product_version_id,
            run_id=str(review_row["run_id"]),
            review_task_id=str(review_row["review_task_id"]),
            event_type="ManualOverride",
            event_reason_code="manual_override",
            detected_at=decided_at,
            metadata={
                "previous_version_no": current_version_no or None,
                "current_version_no": 1 if current_product is None else current_version_no + 1,
                "changed_field_names": override_changed_fields,
                "actor_user_id": actor.get("user_id"),
                "request_id": request_id,
            },
        )
        change_event_types.append("ManualOverride")
        _record_manual_override_audit_event(
            connection,
            actor=actor,
            product_id=product_id,
            review_row=review_row,
            request_id=request_id,
            decided_at=decided_at,
            changed_fields=override_changed_fields,
        )

    return {
        "product_id": product_id,
        "product_version_id": product_version_id,
        "change_event_types": change_event_types,
    }


def _canonical_product_params(
    *,
    review_row: dict[str, Any],
    approved_payload: dict[str, Any],
    product_id: str,
    current_version_no: int,
    last_verified_at: datetime,
    last_changed_at: datetime,
) -> dict[str, Any]:
    return {
        "product_id": product_id,
        "bank_code": str(review_row["bank_code"]),
        "country_code": str(review_row["country_code"]),
        "product_family": str(review_row["product_family"]),
        "product_type": str(review_row["product_type"]),
        "subtype_code": _string_or_none(review_row.get("subtype_code")),
        "product_name": _approved_product_name(review_row=review_row, approved_payload=approved_payload),
        "source_language": str(review_row["source_language"]),
        "currency": str(review_row["currency"]),
        "status": str(approved_payload.get("status") or "active"),
        "current_version_no": current_version_no,
        "last_verified_at": last_verified_at,
        "last_changed_at": last_changed_at,
        "current_snapshot_payload": json.dumps(approved_payload, ensure_ascii=True, sort_keys=True),
        "updated_at": last_verified_at,
    }


def _insert_product_version(
    connection: Connection,
    *,
    product_version_id: str,
    product_id: str,
    approved_candidate_id: str | None,
    version_no: int,
    normalized_payload: dict[str, Any],
    approved_at: datetime,
) -> None:
    connection.execute(
        """
        INSERT INTO product_version (
            product_version_id,
            product_id,
            approved_candidate_id,
            version_no,
            version_status,
            normalized_payload,
            approved_at
        )
        VALUES (
            %(product_version_id)s,
            %(product_id)s,
            %(approved_candidate_id)s,
            %(version_no)s,
            'approved',
            %(normalized_payload)s::jsonb,
            %(approved_at)s
        )
        """,
        {
            "product_version_id": product_version_id,
            "product_id": product_id,
            "approved_candidate_id": approved_candidate_id,
            "version_no": version_no,
            "normalized_payload": json.dumps(normalized_payload, ensure_ascii=True, sort_keys=True),
            "approved_at": approved_at,
        },
    )


def _product_version_approved_candidate_id(*, review_row: dict[str, Any], action_type: str) -> str | None:
    if action_type == "edit_approve" and str(review_row.get("review_state")) in {"approved", "edited"}:
        return None
    return str(review_row["candidate_id"])


def _clone_field_evidence_links(
    connection: Connection,
    *,
    candidate_id: str,
    product_version_id: str,
    skipped_fields: set[str],
) -> None:
    rows = connection.execute(
        """
        SELECT
            evidence_chunk_id,
            source_document_id,
            field_name,
            candidate_value,
            citation_confidence
        FROM field_evidence_link
        WHERE candidate_id = %(candidate_id)s
        """,
        {"candidate_id": candidate_id},
    ).fetchall()
    for row in rows:
        field_name = str(row["field_name"])
        if field_name in skipped_fields:
            continue
        connection.execute(
            """
            INSERT INTO field_evidence_link (
                field_evidence_link_id,
                candidate_id,
                product_version_id,
                evidence_chunk_id,
                source_document_id,
                field_name,
                candidate_value,
                citation_confidence
            )
            VALUES (
                %(field_evidence_link_id)s,
                NULL,
                %(product_version_id)s,
                %(evidence_chunk_id)s,
                %(source_document_id)s,
                %(field_name)s,
                %(candidate_value)s,
                %(citation_confidence)s
            )
            """,
            {
                "field_evidence_link_id": new_id("fel"),
                "product_version_id": product_version_id,
                "evidence_chunk_id": row["evidence_chunk_id"],
                "source_document_id": row["source_document_id"],
                "field_name": field_name,
                "candidate_value": str(row["candidate_value"]),
                "citation_confidence": row["citation_confidence"],
            },
        )


def _insert_change_event(
    connection: Connection,
    *,
    product_id: str,
    product_version_id: str | None,
    run_id: str,
    review_task_id: str,
    event_type: str,
    event_reason_code: str | None,
    detected_at: datetime,
    metadata: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO change_event (
            change_event_id,
            product_id,
            product_version_id,
            run_id,
            review_task_id,
            event_type,
            event_reason_code,
            event_metadata,
            detected_at
        )
        VALUES (
            %(change_event_id)s,
            %(product_id)s,
            %(product_version_id)s,
            %(run_id)s,
            %(review_task_id)s,
            %(event_type)s,
            %(event_reason_code)s,
            %(event_metadata)s::jsonb,
            %(detected_at)s
        )
        """,
        {
            "change_event_id": new_id("chg"),
            "product_id": product_id,
            "product_version_id": product_version_id,
            "run_id": run_id,
            "review_task_id": review_task_id,
            "event_type": event_type,
            "event_reason_code": event_reason_code,
            "event_metadata": json.dumps(metadata, ensure_ascii=True, sort_keys=True),
            "detected_at": detected_at,
        },
    )


def _record_review_audit_event(
    connection: Connection,
    *,
    event_type: str,
    actor: dict[str, Any],
    target_id: str,
    previous_state: str | None,
    new_state: str | None,
    reason_code: str | None,
    reason_text: str | None,
    run_id: str,
    candidate_id: str,
    review_task_id: str,
    product_id: str | None,
    request_id: str,
    diff_summary: str | None,
    ip_address: str | None,
    user_agent: str | None,
    payload: dict[str, Any],
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
            ip_address,
            user_agent,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            %(event_type)s,
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'review_task',
            %(target_id)s,
            %(previous_state)s,
            %(new_state)s,
            %(reason_code)s,
            %(reason_text)s,
            %(run_id)s,
            %(candidate_id)s,
            %(review_task_id)s,
            %(product_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(ip_address)s,
            %(user_agent)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "event_type": event_type,
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": target_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "review_task_id": review_task_id,
            "product_id": product_id,
            "request_id": request_id,
            "diff_summary": diff_summary,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "event_payload": json.dumps(payload, ensure_ascii=True, sort_keys=True),
            "occurred_at": utc_now(),
        },
    )


def _record_manual_override_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    product_id: str,
    review_row: dict[str, Any],
    request_id: str,
    decided_at: datetime,
    changed_fields: list[str],
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
            run_id,
            candidate_id,
            review_task_id,
            product_id,
            request_id,
            diff_summary,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            'manual_override_recorded',
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'product',
            %(target_id)s,
            'manual_override',
            %(run_id)s,
            %(candidate_id)s,
            %(review_task_id)s,
            %(product_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": product_id,
            "run_id": review_row["run_id"],
            "candidate_id": review_row["candidate_id"],
            "review_task_id": review_row["review_task_id"],
            "product_id": product_id,
            "request_id": request_id,
            "diff_summary": f"Manual override fields: {', '.join(changed_fields)}",
            "event_payload": json.dumps({"changed_fields": changed_fields}, ensure_ascii=True, sort_keys=True),
            "occurred_at": decided_at,
        },
    )


def _load_locked_review_task(connection: Connection, *, review_task_id: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            rt.review_task_id,
            rt.candidate_id,
            rt.run_id,
            rt.product_id,
            rt.review_state,
            rt.queue_reason_code,
            nc.country_code,
            nc.bank_code,
            nc.product_family,
            nc.product_type,
            nc.subtype_code,
            nc.product_name,
            nc.source_language,
            nc.currency,
            nc.candidate_payload
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        WHERE rt.review_task_id = %(review_task_id)s
        FOR UPDATE
        """,
        {"review_task_id": review_task_id},
    ).fetchone()
    if not row:
        raise ReviewTaskError(status_code=404, code="review_task_not_found", message="Review task was not found.")
    return row


def _load_current_product_summary(connection: Connection, *, review_row: dict[str, Any]) -> dict[str, Any] | None:
    product_row = _find_current_product(connection, review_row=review_row)
    if not product_row:
        return None
    return {
        "product_id": str(product_row["product_id"]),
        "status": str(product_row["status"]),
        "current_version_no": int(product_row["current_version_no"]),
        "product_name": str(product_row["product_name"]),
        "product_type": str(product_row["product_type"]),
        "subtype_code": _string_or_none(product_row.get("subtype_code")),
        "last_verified_at": product_row["last_verified_at"].isoformat() if product_row.get("last_verified_at") else None,
        "last_changed_at": product_row["last_changed_at"].isoformat() if product_row.get("last_changed_at") else None,
        "normalized_payload": _coerce_mapping(product_row.get("normalized_payload")),
    }


def _find_current_product(
    connection: Connection,
    *,
    review_row: dict[str, Any],
    approved_payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if review_row.get("product_id"):
        product_row = connection.execute(
            """
            SELECT
                cp.product_id,
                cp.status,
                cp.current_version_no,
                cp.product_name,
                cp.product_type,
                cp.subtype_code,
                cp.last_verified_at,
                cp.last_changed_at,
                pv.normalized_payload
            FROM canonical_product AS cp
            LEFT JOIN product_version AS pv
              ON pv.product_id = cp.product_id
             AND pv.version_no = cp.current_version_no
            WHERE cp.product_id = %(product_id)s
            """,
            {"product_id": review_row["product_id"]},
        ).fetchone()
        if product_row:
            return product_row

    return connection.execute(
        """
        SELECT
            cp.product_id,
            cp.status,
            cp.current_version_no,
            cp.product_name,
            cp.product_type,
            cp.subtype_code,
            cp.last_verified_at,
            cp.last_changed_at,
            pv.normalized_payload
        FROM canonical_product AS cp
        LEFT JOIN product_version AS pv
          ON pv.product_id = cp.product_id
         AND pv.version_no = cp.current_version_no
        WHERE cp.country_code = %(country_code)s
          AND cp.bank_code = %(bank_code)s
          AND cp.product_family = %(product_family)s
          AND cp.product_type = %(product_type)s
          AND lower(cp.product_name) = lower(%(product_name)s)
          AND (
              cp.subtype_code IS NOT DISTINCT FROM %(subtype_code)s
              OR %(subtype_code)s IS NULL
          )
        ORDER BY cp.updated_at DESC
        LIMIT 1
        """,
        {
            "country_code": review_row["country_code"],
            "bank_code": review_row["bank_code"],
            "product_family": review_row["product_family"],
            "product_type": review_row["product_type"],
            "product_name": _approved_product_name(review_row=review_row, approved_payload=approved_payload),
            "subtype_code": review_row.get("subtype_code"),
        },
    ).fetchone()


def _available_actions(*, review_state: str, actor_role: str) -> list[str]:
    if actor_role not in MUTATION_ROLES:
        return []
    if review_state in {"approved", "edited"}:
        return ["edit_approve"]
    if review_state in TERMINAL_REVIEW_STATES:
        return []
    return ["approve", "reject", "edit_approve", "defer"]


def _can_reedit_review(*, current_state: str, action_type: str) -> bool:
    return current_state in {"approved", "edited"} and action_type == "edit_approve"


def _candidate_state_for_action(action_type: str) -> str:
    if action_type == "reject":
        return "rejected"
    if action_type in {"approve", "edit_approve"}:
        return "approved"
    return "in_review"


def _serialize_decision_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_decision_id": str(row["review_decision_id"]),
        "action_type": str(row["action_type"]),
        "reason_code": _string_or_none(row.get("reason_code")),
        "reason_text": _string_or_none(row.get("reason_text")),
        "diff_summary": _string_or_none(row.get("diff_summary")),
        "override_payload": _coerce_mapping(row.get("override_payload")),
        "decided_at": row["decided_at"].isoformat(),
        "actor": {
            "user_id": _string_or_none(row.get("actor_user_id")),
            "display_name": _string_or_none(row.get("actor_display_name")),
            "email": _string_or_none(row.get("actor_email")),
            "role": _string_or_none(row.get("actor_role")),
        },
    }


def _serialize_evidence_row(
    row: dict[str, Any],
    *,
    field_mapping_metadata: dict[str, Any],
    stage_metadata: dict[str, Any],
) -> dict[str, Any]:
    field_name = str(row["field_name"])
    page_no = int(row["page_no"]) if row.get("page_no") is not None else None
    chunk_index = int(row["chunk_index"]) if row.get("chunk_index") is not None else None
    field_mapping = _serialize_field_mapping(field_mapping_metadata.get(field_name))
    source_metadata = _coerce_mapping(row.get("source_metadata"))
    return {
        "field_name": field_name,
        "label": _titleize(field_name),
        "candidate_value": str(row["candidate_value"]),
        "citation_confidence": _serialize_confidence(row.get("citation_confidence")),
        "evidence_chunk_id": str(row["evidence_chunk_id"]),
        "evidence_excerpt": _string_or_none(row.get("evidence_excerpt")),
        "source_document_id": _string_or_none(row.get("source_document_id")),
        "source_snapshot_id": _string_or_none(row.get("source_snapshot_id")),
        "parsed_document_id": _string_or_none(row.get("parsed_document_id")),
        "source_url": _string_or_none(row.get("source_url")),
        "source_type": _string_or_none(row.get("source_type")),
        "source_id": _string_or_none(source_metadata.get("source_id")),
        "anchor_type": _string_or_none(row.get("anchor_type")),
        "anchor_value": _string_or_none(row.get("anchor_value")),
        "page_no": page_no,
        "chunk_index": chunk_index,
        "field_mapping": field_mapping,
        "model_execution_id": _resolve_trace_model_execution_id(
            field_mapping=field_mapping,
            stage_metadata=stage_metadata,
        ),
        "anchor_label": _build_anchor_label(
            page_no=page_no,
            anchor_type=row.get("anchor_type"),
            anchor_value=row.get("anchor_value"),
            chunk_index=chunk_index,
        ),
    }


def _build_field_trace_groups(
    *,
    candidate_payload: dict[str, Any],
    field_mapping_metadata: dict[str, Any],
    evidence_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence_by_field: dict[str, list[dict[str, Any]]] = {}
    for item in evidence_links:
        evidence_by_field.setdefault(str(item["field_name"]), []).append(item)

    groups: list[dict[str, Any]] = []
    for field_name, value in sorted(candidate_payload.items()):
        if _is_empty_review_value(value):
            continue
        field_evidence = evidence_by_field.get(field_name, [])
        groups.append(
            {
                "field_name": field_name,
                "label": _titleize(field_name),
                "value": value,
                "mapping": _serialize_field_mapping(field_mapping_metadata.get(field_name)),
                "evidence_count": len(field_evidence),
                "has_evidence": bool(field_evidence),
                "evidence_links": field_evidence,
            }
        )
    return groups


def _build_validation_issues(
    *,
    issue_items: list[dict[str, str]],
    validation_issue_codes: list[str],
    validation_status: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    for item in issue_items:
        code = item.get("code", "")
        issues.append(
            {
                "code": code,
                "severity": item.get("severity") or validation_status,
                "summary": item.get("summary") or _titleize(code or validation_status),
            }
        )
        if code:
            seen_codes.add(code)

    fallback_severity = "error" if validation_status == "error" else "warning"
    for code in validation_issue_codes:
        if code in seen_codes:
            continue
        issues.append({"code": code, "severity": fallback_severity, "summary": _titleize(code)})
    return issues


def _load_model_execution_references(
    connection: Connection,
    *,
    candidate_model_execution_id: str | None,
    stage_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    model_execution_ids = _collect_model_execution_ids(
        candidate_model_execution_id=candidate_model_execution_id,
        stage_metadata=stage_metadata,
    )
    if not model_execution_ids:
        return []

    rows = connection.execute(
        """
        SELECT
            me.model_execution_id,
            me.stage_name,
            me.agent_name,
            me.model_id,
            me.execution_status,
            me.execution_metadata,
            me.started_at,
            me.completed_at,
            lur.llm_usage_id,
            lur.prompt_tokens,
            lur.completion_tokens,
            lur.estimated_cost,
            lur.usage_metadata,
            lur.recorded_at
        FROM model_execution AS me
        LEFT JOIN llm_usage_record AS lur
          ON lur.model_execution_id = me.model_execution_id
        WHERE me.model_execution_id IN (
            SELECT jsonb_array_elements_text(%(model_execution_ids_json)s::jsonb)
        )
        """,
        {"model_execution_ids_json": json.dumps(model_execution_ids, ensure_ascii=True)},
    ).fetchall()

    serialized = [_serialize_model_execution_row(item) for item in rows]
    return sorted(
        serialized,
        key=lambda item: (
            MODEL_EXECUTION_STAGE_ORDER.get(item["stage_name"], 99),
            item["started_at"] or "",
            item["model_execution_id"],
        ),
    )


def _collect_model_execution_ids(
    *,
    candidate_model_execution_id: str | None,
    stage_metadata: dict[str, Any],
) -> list[str]:
    ordered_ids = [
        _string_or_none(stage_metadata.get("extraction_model_execution_id")),
        candidate_model_execution_id,
        _string_or_none(stage_metadata.get("normalization_model_execution_id")),
        _string_or_none(stage_metadata.get("validation_model_execution_id")),
        _string_or_none(stage_metadata.get("model_execution_id")),
    ]
    result: list[str] = []
    seen: set[str] = set()
    for item in ordered_ids:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _serialize_model_execution_row(row: dict[str, Any]) -> dict[str, Any]:
    usage_metadata = _coerce_mapping(row.get("usage_metadata"))
    return {
        "model_execution_id": str(row["model_execution_id"]),
        "stage_name": str(row["stage_name"]),
        "stage_label": _titleize(str(row["stage_name"])),
        "agent_name": str(row["agent_name"]),
        "model_id": str(row["model_id"]),
        "execution_status": str(row["execution_status"]),
        "execution_metadata": _coerce_mapping(row.get("execution_metadata")),
        "started_at": row["started_at"].isoformat() if row.get("started_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "usage": {
            "llm_usage_id": _string_or_none(row.get("llm_usage_id")),
            "prompt_tokens": int(row["prompt_tokens"]) if row.get("prompt_tokens") is not None else None,
            "completion_tokens": int(row["completion_tokens"]) if row.get("completion_tokens") is not None else None,
            "estimated_cost": float(row["estimated_cost"]) if row.get("estimated_cost") is not None else None,
            "usage_mode": _string_or_none(usage_metadata.get("usage_mode")),
            "provider": _string_or_none(usage_metadata.get("provider")),
            "recorded_at": row["recorded_at"].isoformat() if row.get("recorded_at") else None,
            "usage_metadata": usage_metadata,
        },
    }


def _serialize_field_mapping(value: Any) -> dict[str, Any]:
    mapping = _coerce_mapping(value)
    return {
        "source_field_name": _string_or_none(mapping.get("source_field_name")),
        "normalized_value": mapping.get("normalized_value"),
        "value_type": _string_or_none(mapping.get("value_type")),
        "extraction_method": _string_or_none(mapping.get("extraction_method")),
        "extraction_confidence": _serialize_confidence(mapping.get("extraction_confidence")),
        "evidence_chunk_id": _string_or_none(mapping.get("evidence_chunk_id")),
        "normalization_method": _string_or_none(mapping.get("normalization_method")),
        "source_subtype_label": _string_or_none(mapping.get("source_subtype_label")),
    }


def _resolve_trace_model_execution_id(*, field_mapping: dict[str, Any], stage_metadata: dict[str, Any]) -> str | None:
    return (
        _string_or_none(field_mapping.get("model_execution_id"))
        or _string_or_none(stage_metadata.get("extraction_model_execution_id"))
        or _string_or_none(stage_metadata.get("model_execution_id"))
        or _string_or_none(stage_metadata.get("normalization_model_execution_id"))
        or _string_or_none(stage_metadata.get("validation_model_execution_id"))
    )


def _normalize_override_payload(*, override_payload: dict[str, Any] | None, base_payload: dict[str, Any]) -> dict[str, Any]:
    if not override_payload:
        return {}
    normalized: dict[str, Any] = {}
    for key, value in override_payload.items():
        field_name = str(key).strip()
        if not field_name:
            continue
        if field_name in {"product_id", "candidate_id", "run_id", "review_task_id"}:
            continue
        if field_name == "product_name":
            normalized_product_name = _normalize_text(str(value)) if value is not None else None
            if not normalized_product_name:
                continue
            if base_payload.get(field_name) == normalized_product_name:
                continue
            normalized[field_name] = normalized_product_name
            continue
        normalized_value = _normalize_json_value(value)
        if base_payload.get(field_name) == normalized_value:
            continue
        normalized[field_name] = normalized_value
    return normalized


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    return str(value)


def _build_diff_summary(*, changed_fields: list[str], before_payload: dict[str, Any], after_payload: dict[str, Any]) -> str | None:
    if not changed_fields:
        return None
    parts = [
        f"{_titleize(field_name)}: {_short_value(before_payload.get(field_name))} -> {_short_value(after_payload.get(field_name))}"
        for field_name in changed_fields[:5]
    ]
    suffix = f" (+{len(changed_fields) - 5} more)" if len(changed_fields) > 5 else ""
    return "; ".join(parts) + suffix


def _changed_field_names(*, before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    field_names = set(before) | set(after)
    return sorted(field_name for field_name in field_names if before.get(field_name) != after.get(field_name))


def _is_reclassified(*, current_product: dict[str, Any], review_row: dict[str, Any]) -> bool:
    return (
        _string_or_none(current_product.get("product_type")) != _string_or_none(review_row.get("product_type"))
        or _string_or_none(current_product.get("subtype_code")) != _string_or_none(review_row.get("subtype_code"))
    )


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _coerce_issue_items(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    items: list[dict[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "")).strip()
        severity = str(entry.get("severity", "")).strip()
        summary = str(entry.get("summary", "")).strip()
        if not code and not summary:
            continue
        items.append({"code": code, "severity": severity, "summary": summary})
    return items


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _serialize_confidence(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _summarize_issue_items(issue_items: list[dict[str, str]], *, fallback_reason: str) -> str:
    summaries = [item["summary"] for item in issue_items if item.get("summary")]
    if summaries:
        primary = summaries[:2]
        summary = " ".join(primary)
        if len(summaries) > 2:
            summary = f"{summary} (+{len(summaries) - 2} more)"
        return summary
    return fallback_reason.replace("_", " ")


def _build_anchor_label(*, page_no: int | None, anchor_type: Any, anchor_value: Any, chunk_index: int | None) -> str:
    if page_no is not None:
        return f"Page {page_no}"
    if not _is_empty_review_value(anchor_value):
        return f"{_titleize(str(anchor_type or 'anchor'))} {anchor_value}"
    if chunk_index is not None:
        return f"Chunk {chunk_index}"
    return "Evidence chunk"


def _titleize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _approved_product_name(*, review_row: dict[str, Any], approved_payload: dict[str, Any] | None) -> str:
    if approved_payload:
        approved_value = approved_payload.get("product_name")
        normalized = _normalize_text(str(approved_value)) if approved_value is not None else None
        if normalized:
            return normalized
    return str(review_row["product_name"])


def _is_empty_review_value(value: Any) -> bool:
    return value is None or value == ""


def _short_value(value: Any) -> str:
    if _is_empty_review_value(value):
        return "empty"
    if isinstance(value, str):
        compact = " ".join(value.split())
        return compact if len(compact) <= 40 else f"{compact[:37]}..."
    if isinstance(value, (int, float, bool)):
        return str(value)
    serialized = json.dumps(value, ensure_ascii=True, sort_keys=True)
    return serialized if len(serialized) <= 40 else f"{serialized[:37]}..."


def _normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _string_or_none(value: Any) -> str | None:
    if _is_empty_review_value(value):
        return None
    normalized = str(value).strip()
    return normalized or None
