from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
from typing import TYPE_CHECKING, Any

from api_service.aggregate_refresh import queue_auto_promotion_aggregate_refresh_request
from api_service.config import Settings
from api_service.db import open_connection
from api_service.review_detail import _apply_canonical_approval, _approved_product_name, _coerce_mapping
from api_service.security import new_id, utc_now

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover
    Connection = Any


DEFAULT_AUTO_PROMOTION_LIMIT = 1000
AUTO_PROMOTION_ACTOR = {
    "actor_type": "system",
    "role": "system",
    "display_name": "FPDS auto-promotion policy",
}
_NON_PRODUCT_NAME_PATTERNS = (
    re.compile(r"\bcalculator\b", re.IGNORECASE),
    re.compile(r"\bsearch tool\b", re.IGNORECASE),
    re.compile(r"^account fees?$", re.IGNORECASE),
    re.compile(r"^include in any bank plan$", re.IGNORECASE),
    re.compile(r"\bbenefits?\s+(of|on|for)\b", re.IGNORECASE),
    re.compile(r"^better banking\b", re.IGNORECASE),
    re.compile(r"^save smarter\b", re.IGNORECASE),
    re.compile(r"^banking for\b", re.IGNORECASE),
    re.compile(r"^a\s+(chequing|checking|bank)\s+account\b", re.IGNORECASE),
)


def promote_auto_validated_candidates(
    connection: Connection,
    *,
    run_id: str | None = None,
    actor: dict[str, Any] | None = None,
    request_context: dict[str, Any] | None = None,
    limit: int | None = DEFAULT_AUTO_PROMOTION_LIMIT,
    queue_aggregate_refresh: bool = True,
) -> dict[str, Any]:
    policy = _load_auto_promotion_policy(connection)
    rows = _load_candidate_rows(
        connection,
        run_id=run_id,
        min_confidence=policy["auto_approve_min_confidence"],
        limit=limit,
    )
    active_actor = {**AUTO_PROMOTION_ACTOR, **(actor or {})}
    active_context = dict(request_context or {})
    decided_at = utc_now()
    promoted_items: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []

    for row in rows:
        candidate_id = str(row["candidate_id"])
        issue_codes = _coerce_string_list(row.get("validation_issue_codes"))
        force_review_hits = sorted(set(issue_codes).intersection(policy["force_review_issue_codes"]))
        if force_review_hits:
            review_task_id = _queue_candidate_for_review(
                connection,
                row=row,
                queue_reason_code="force_review_issue_code",
                issue_codes=force_review_hits,
                decided_at=decided_at,
            )
            _record_candidate_auto_promotion_skip_audit_event(
                connection,
                actor=active_actor,
                request_context=active_context,
                row=row,
                decided_at=decided_at,
                previous_state="auto_validated",
                new_state="in_review",
                reason_code="force_review_issue_code",
                reason_text="Candidate passed validation but matched an active force-review issue policy.",
                review_task_id=review_task_id,
                event_payload={
                    "force_review_issue_codes": force_review_hits,
                    "source_confidence": float(row["source_confidence"]),
                },
            )
            skipped_items.append(
                {
                    "candidate_id": candidate_id,
                    "skip_reason": "force_review_issue_code",
                    "action": "queued_for_review",
                    "issue_codes": force_review_hits,
                }
            )
            continue
        product_name_skip_reason = _non_product_name_skip_reason(str(row.get("product_name") or ""))
        if product_name_skip_reason is not None:
            _mark_candidate_auto_rejected(
                connection,
                candidate_id=candidate_id,
                reason_code=product_name_skip_reason,
                decided_at=decided_at,
            )
            _record_candidate_auto_promotion_skip_audit_event(
                connection,
                actor=active_actor,
                request_context=active_context,
                row=row,
                decided_at=decided_at,
                previous_state="auto_validated",
                new_state="rejected",
                reason_code=product_name_skip_reason,
                reason_text="Candidate passed validation but matched the non-product page-name guard.",
                event_payload={
                    "product_name": str(row.get("product_name") or ""),
                    "source_confidence": float(row["source_confidence"]),
                },
            )
            skipped_items.append(
                {
                    "candidate_id": candidate_id,
                    "skip_reason": product_name_skip_reason,
                    "action": "rejected",
                    "product_name": str(row.get("product_name") or ""),
                }
            )
            continue

        review_row = _review_row_from_candidate(row)
        candidate_payload = _coerce_mapping(row.get("candidate_payload"))
        approved_product_name = _approved_product_name(review_row=review_row, approved_payload=candidate_payload)
        approved_payload = {**candidate_payload, "product_name": approved_product_name}
        product_result = _apply_canonical_approval(
            connection,
            review_row=review_row,
            approved_payload=approved_payload,
            override_changed_fields=[],
            action_type="auto_promote",
            actor=active_actor,
            decided_at=decided_at,
            request_id=str(active_context.get("request_id") or ""),
        )
        _mark_candidate_auto_promoted(
            connection,
            candidate_id=candidate_id,
            product_name=approved_product_name,
            candidate_payload=approved_payload,
            decided_at=decided_at,
        )
        _record_candidate_auto_promotion_audit_event(
            connection,
            actor=active_actor,
            request_context=active_context,
            row=row,
            product_result=product_result,
            decided_at=decided_at,
            policy=policy,
        )
        promoted_items.append(
            {
                "candidate_id": candidate_id,
                "run_id": str(row["run_id"]),
                "product_id": str(product_result["product_id"]),
                "product_version_id": product_result["product_version_id"],
                "change_event_types": [str(item) for item in product_result["change_event_types"]],
            }
        )

    aggregate_refresh_request = None
    if queue_aggregate_refresh and promoted_items:
        aggregate_refresh_request = queue_auto_promotion_aggregate_refresh_request(
            connection,
            actor=active_actor,
            request_context=active_context,
            promoted_count=len(promoted_items),
            product_ids=[str(item["product_id"]) for item in promoted_items],
            candidate_ids=[str(item["candidate_id"]) for item in promoted_items],
            run_ids=[str(item["run_id"]) for item in promoted_items],
            change_event_types=[
                str(change_type)
                for item in promoted_items
                for change_type in item["change_event_types"]
            ],
        )

    return {
        "run_id": run_id,
        "examined_count": len(rows),
        "promoted_count": len(promoted_items),
        "skipped_count": len(skipped_items),
        "promoted_items": promoted_items,
        "skipped_items": skipped_items,
        "policy": {
            "auto_approve_min_confidence": policy["auto_approve_min_confidence"],
            "force_review_issue_codes": sorted(policy["force_review_issue_codes"]),
        },
        "aggregate_refresh": aggregate_refresh_request,
    }


def _load_candidate_rows(
    connection: Connection,
    *,
    run_id: str | None,
    min_confidence: float,
    limit: int | None,
) -> list[dict[str, Any]]:
    limit_clause = "LIMIT %(limit)s" if limit is not None else ""
    run_filter_clause = "AND nc.run_id = %(run_id)s" if run_id is not None else ""
    params: dict[str, Any] = {
        "min_confidence": min_confidence,
    }
    if run_id is not None:
        params["run_id"] = run_id
    if limit is not None:
        params["limit"] = max(1, int(limit))
    rows = connection.execute(
        f"""
        SELECT
            nc.candidate_id,
            nc.run_id,
            NULL::text AS product_id,
            nc.country_code,
            nc.bank_code,
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
            nc.candidate_payload
        FROM normalized_candidate AS nc
        WHERE nc.candidate_state = 'auto_validated'
          AND nc.validation_status = 'pass'
          AND nc.source_confidence >= %(min_confidence)s
          {run_filter_clause}
          AND NOT EXISTS (
              SELECT 1
              FROM product_version AS pv
              WHERE pv.approved_candidate_id = nc.candidate_id
          )
          AND NOT EXISTS (
              SELECT 1
              FROM review_task AS rt
              WHERE rt.candidate_id = nc.candidate_id
                AND rt.review_state IN ('queued', 'deferred')
          )
        ORDER BY nc.created_at ASC, nc.candidate_id ASC
        {limit_clause}
        FOR UPDATE OF nc SKIP LOCKED
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _load_auto_promotion_policy(connection: Connection) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT DISTINCT ON (policy_key)
            policy_key,
            policy_value
        FROM processing_policy_config
        WHERE active_flag = true
          AND policy_key IN ('AUTO_APPROVE_MIN_CONFIDENCE', 'FORCE_REVIEW_ISSUE_CODES')
        ORDER BY policy_key, version_no DESC
        """,
        {},
    ).fetchall()
    policy_map = {str(row["policy_key"]): row.get("policy_value") for row in rows}
    return {
        "auto_approve_min_confidence": _coerce_policy_number(policy_map.get("AUTO_APPROVE_MIN_CONFIDENCE"), 1.0),
        "force_review_issue_codes": _coerce_policy_codes(policy_map.get("FORCE_REVIEW_ISSUE_CODES")),
    }


def _review_row_from_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_task_id": None,
        "candidate_id": str(row["candidate_id"]),
        "run_id": str(row["run_id"]),
        "product_id": row.get("product_id"),
        "review_state": "auto_validated",
        "country_code": str(row["country_code"]),
        "bank_code": str(row["bank_code"]),
        "product_family": str(row.get("product_family") or "deposit"),
        "product_type": str(row["product_type"]),
        "subtype_code": row.get("subtype_code"),
        "product_name": str(row["product_name"]),
        "source_language": str(row["source_language"]),
        "currency": str(row["currency"]),
        "candidate_payload": _coerce_mapping(row.get("candidate_payload")),
    }


def _mark_candidate_auto_promoted(
    connection: Connection,
    *,
    candidate_id: str,
    product_name: str,
    candidate_payload: dict[str, Any],
    decided_at: datetime,
) -> None:
    connection.execute(
        """
        UPDATE normalized_candidate
        SET
            candidate_state = 'approved',
            review_reason_code = 'auto_promoted',
            product_name = %(product_name)s,
            candidate_payload = %(candidate_payload)s::jsonb,
            updated_at = %(updated_at)s
        WHERE candidate_id = %(candidate_id)s
        """,
        {
            "candidate_id": candidate_id,
            "product_name": product_name,
            "candidate_payload": json.dumps(candidate_payload, ensure_ascii=True, sort_keys=True),
            "updated_at": decided_at,
        },
    )


def _queue_candidate_for_review(
    connection: Connection,
    *,
    row: dict[str, Any],
    queue_reason_code: str,
    issue_codes: list[str],
    decided_at: datetime,
) -> str:
    candidate_id = str(row["candidate_id"])
    issue_summary = [
        {
            "issue_code": issue_code,
            "severity": "warning",
            "message": "Auto-promotion policy requires manual review for this issue code.",
        }
        for issue_code in issue_codes
    ]
    connection.execute(
        """
        UPDATE normalized_candidate
        SET
            candidate_state = 'in_review',
            review_reason_code = %(queue_reason_code)s,
            updated_at = %(updated_at)s
        WHERE candidate_id = %(candidate_id)s
        """,
        {
            "candidate_id": candidate_id,
            "queue_reason_code": queue_reason_code,
            "updated_at": decided_at,
        },
    )
    review_row = connection.execute(
        """
        INSERT INTO review_task (
            review_task_id,
            candidate_id,
            run_id,
            product_id,
            review_state,
            queue_reason_code,
            issue_summary,
            created_at,
            updated_at
        )
        VALUES (
            %(review_task_id)s,
            %(candidate_id)s,
            %(run_id)s,
            NULL,
            'queued',
            %(queue_reason_code)s,
            %(issue_summary)s::jsonb,
            %(decided_at)s,
            %(decided_at)s
        )
        ON CONFLICT (candidate_id) DO UPDATE SET
            review_state = 'queued',
            queue_reason_code = EXCLUDED.queue_reason_code,
            issue_summary = EXCLUDED.issue_summary,
            updated_at = EXCLUDED.updated_at
        RETURNING review_task_id
        """,
        {
            "review_task_id": new_id("review"),
            "candidate_id": candidate_id,
            "run_id": str(row["run_id"]),
            "queue_reason_code": queue_reason_code,
            "issue_summary": json.dumps(issue_summary, ensure_ascii=True, sort_keys=True),
            "decided_at": decided_at,
        },
    ).fetchone()
    return str(review_row["review_task_id"])


def _mark_candidate_auto_rejected(
    connection: Connection,
    *,
    candidate_id: str,
    reason_code: str,
    decided_at: datetime,
) -> None:
    connection.execute(
        """
        UPDATE normalized_candidate
        SET
            candidate_state = 'rejected',
            review_reason_code = %(reason_code)s,
            updated_at = %(updated_at)s
        WHERE candidate_id = %(candidate_id)s
        """,
        {
            "candidate_id": candidate_id,
            "reason_code": reason_code,
            "updated_at": decided_at,
        },
    )


def _record_candidate_auto_promotion_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    row: dict[str, Any],
    product_result: dict[str, Any],
    decided_at: datetime,
    policy: dict[str, Any],
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
            product_id,
            request_id,
            diff_summary,
            source_ref,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            'candidate_auto_promoted',
            'system',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'candidate',
            %(target_id)s,
            'auto_validated',
            'approved',
            'auto_validated_pass',
            %(reason_text)s,
            %(run_id)s,
            %(candidate_id)s,
            %(product_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(source_ref)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": str(row["candidate_id"]),
            "reason_text": "Candidate passed validation and confidence policy without force-review issues.",
            "run_id": str(row["run_id"]),
            "candidate_id": str(row["candidate_id"]),
            "product_id": product_result["product_id"],
            "request_id": request_context.get("request_id"),
            "diff_summary": "Auto-promoted validation pass candidate to canonical product.",
            "source_ref": request_context.get("request_id"),
            "event_payload": json.dumps(
                {
                    "product_version_id": product_result["product_version_id"],
                    "change_event_types": product_result["change_event_types"],
                    "source_confidence": float(row["source_confidence"]),
                    "validation_status": str(row["validation_status"]),
                    "validation_issue_codes": _coerce_string_list(row.get("validation_issue_codes")),
                    "auto_approve_min_confidence": policy["auto_approve_min_confidence"],
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
            "occurred_at": decided_at,
        },
    )


def _record_candidate_auto_promotion_skip_audit_event(
    connection: Connection,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    row: dict[str, Any],
    decided_at: datetime,
    previous_state: str,
    new_state: str,
    reason_code: str,
    reason_text: str,
    event_payload: dict[str, Any],
    review_task_id: str | None = None,
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
            request_id,
            diff_summary,
            source_ref,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'review',
            'candidate_auto_promotion_skipped',
            'system',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'candidate',
            %(target_id)s,
            %(previous_state)s,
            %(new_state)s,
            %(reason_code)s,
            %(reason_text)s,
            %(run_id)s,
            %(candidate_id)s,
            %(review_task_id)s,
            %(request_id)s,
            %(diff_summary)s,
            %(source_ref)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": str(row["candidate_id"]),
            "previous_state": previous_state,
            "new_state": new_state,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "run_id": str(row["run_id"]),
            "candidate_id": str(row["candidate_id"]),
            "review_task_id": review_task_id,
            "request_id": request_context.get("request_id"),
            "diff_summary": f"Auto-promotion skipped candidate with reason `{reason_code}`.",
            "source_ref": request_context.get("request_id"),
            "event_payload": json.dumps(event_payload, ensure_ascii=True, sort_keys=True),
            "occurred_at": decided_at,
        },
    )


def _coerce_policy_number(policy_value: object, default: float) -> float:
    if isinstance(policy_value, dict):
        policy_value = policy_value.get("value")
    try:
        return float(policy_value)
    except (TypeError, ValueError):
        return default


def _coerce_policy_codes(policy_value: object) -> set[str]:
    if isinstance(policy_value, list):
        return {str(item) for item in policy_value}
    if isinstance(policy_value, str):
        try:
            parsed = json.loads(policy_value)
        except json.JSONDecodeError:
            return set()
        if isinstance(parsed, list):
            return {str(item) for item in parsed}
    return set()


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value.strip() else []
        return _coerce_string_list(parsed)
    return []


def _non_product_name_skip_reason(product_name: str) -> str | None:
    normalized = " ".join(product_name.split())
    if not normalized:
        return "empty_product_name"
    for pattern in _NON_PRODUCT_NAME_PATTERNS:
        if pattern.search(normalized):
            return "non_product_page_title"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote auto-validated pass candidates to canonical products.")
    parser.add_argument("--run-id", help="Limit promotion to a single ingestion run.")
    parser.add_argument("--limit", type=int, default=DEFAULT_AUTO_PROMOTION_LIMIT)
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--no-aggregate-refresh", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env()
    with open_connection(settings) as connection:
        result = promote_auto_validated_candidates(
            connection,
            run_id=args.run_id,
            request_context={"request_id": args.request_id},
            limit=args.limit,
            queue_aggregate_refresh=not args.no_aggregate_refresh,
        )
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
