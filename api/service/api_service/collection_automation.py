from __future__ import annotations

from collections.abc import Mapping
import logging
import threading
from typing import Any
from uuid import uuid4

from api_service.aggregate_refresh import launch_aggregate_refresh_runner
from api_service.candidate_auto_promotion import promote_auto_validated_candidates
from api_service.collection_ai_autopilot import (
    load_collection_ai_autopilot_policy,
    remediate_collection_review_task,
)
from api_service.config import Settings
from api_service.data_retention import apply_data_retention
from api_service.db import open_connection
from api_service.source_catalog import _record_catalog_audit_event, start_source_catalog_collection
from worker.pipeline.fpds_ai_runtime import llm_provider_configured


LOGGER = logging.getLogger(__name__)
COLLECTION_AUTOMATION_LOCK_KEY = 704251604235
AUTOMATED_PRODUCT_TYPES = (
    "chequing",
    "savings",
    "gic",
    "credit-card",
    "mortgage",
    "personal-loan",
    "line-of-credit",
)
AUTOMATION_ACTOR = {
    "actor_type": "scheduler",
    "user_id": None,
    "role": "admin",
    "display_name": "FPDS collection automation",
}


def run_collection_automation_scheduler(settings: Settings, stop_event: threading.Event) -> None:
    """Run one database-elected scheduler leader alongside the API runtime."""

    if not settings.automation_scheduler_enabled:
        return

    retry_seconds = min(settings.automation_poll_seconds, 60)
    while not stop_event.is_set():
        try:
            with open_connection(settings) as connection:
                if not _try_acquire_scheduler_lock(connection):
                    connection.commit()
                    stop_event.wait(settings.automation_poll_seconds)
                    continue
                connection.commit()
                try:
                    while not stop_event.is_set():
                        try:
                            retention = apply_data_retention(connection)
                            connection.commit()
                            summary = run_collection_automation_cycle(connection)
                            summary["retention"] = retention
                            LOGGER.info("FPDS collection automation cycle: %s", summary)
                        except Exception:
                            connection.rollback()
                            LOGGER.exception("FPDS collection automation cycle failed")
                        stop_event.wait(settings.automation_poll_seconds)
                finally:
                    _release_scheduler_lock(connection)
                    connection.commit()
        except Exception:
            LOGGER.exception("FPDS collection automation leader connection failed")
            stop_event.wait(retry_seconds)


def run_collection_automation_cycle(connection: Any) -> dict[str, Any]:
    policy = load_collection_automation_policy(connection)
    if not policy["enabled"]:
        return {"status": "disabled", "policy": policy}

    request_context = {
        "request_id": f"scheduler_{uuid4().hex}",
        "ip_address": None,
        "user_agent": "fpds-collection-automation",
    }
    stale_run_ids = recover_stale_collection_runs(
        connection,
        stale_run_hours=int(policy["stale_run_hours"]),
        request_context=request_context,
    )
    connection.commit()

    promotion = promote_auto_validated_candidates(
        connection,
        actor=AUTOMATION_ACTOR,
        request_context=request_context,
        limit=1000,
        queue_aggregate_refresh=True,
    )
    connection.commit()

    ai_policy = load_collection_ai_autopilot_policy(connection)
    review_task_ids: list[str] = []
    review_outcomes: list[dict[str, Any]] = []
    if ai_policy["enabled"] and llm_provider_configured():
        review_task_ids = load_recoverable_collection_review_task_ids(
            connection,
            limit=int(policy["review_recovery_limit"]),
        )
        for review_task_id in review_task_ids:
            try:
                result = remediate_collection_review_task(
                    connection,
                    review_task_id=review_task_id,
                    approval_threshold=float(ai_policy["approval_threshold"]),
                    request_context=request_context,
                    actor=AUTOMATION_ACTOR,
                )
                connection.commit()
                review_outcomes.append(
                    {
                        "review_task_id": review_task_id,
                        "status": str(result.get("status") or "unknown"),
                        "approved": bool(result.get("approved")),
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive scheduler boundary
                connection.rollback()
                LOGGER.exception("Review recovery failed for %s", review_task_id)
                review_outcomes.append(
                    {
                        "review_task_id": review_task_id,
                        "status": "error",
                        "approved": False,
                        "error_type": type(exc).__name__,
                    }
                )

    aggregate_launch = None
    if has_pending_aggregate_refresh(connection):
        connection.commit()
        aggregate_launch = launch_aggregate_refresh_runner()

    collection_launch = None
    if not has_active_source_catalog_collection(connection):
        due_catalog_item_ids = load_due_catalog_item_ids(
            connection,
            interval_hours=int(policy["interval_hours"]),
            retry_hours=int(policy["retry_hours"]),
            limit=int(policy["batch_size"]),
        )
        if due_catalog_item_ids:
            collection_launch = start_source_catalog_collection(
                connection,
                catalog_item_ids=due_catalog_item_ids,
                actor=AUTOMATION_ACTOR,
                request_context=request_context,
            )
            connection.commit()

    return {
        "status": "completed",
        "policy": policy,
        "stale_run_count": len(stale_run_ids),
        "promotion": {
            "promoted_count": int(promotion.get("promoted_count") or 0),
            "skipped_count": int(promotion.get("skipped_count") or 0),
        },
        "review_recovery": {
            "selected_count": len(review_task_ids),
            "approved_count": sum(1 for item in review_outcomes if item["approved"]),
            "outcomes": review_outcomes,
        },
        "aggregate_launch": aggregate_launch,
        "collection_launch": collection_launch,
    }


def load_collection_automation_policy(connection: Any) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT DISTINCT ON (policy_key)
            policy_key,
            policy_value
        FROM processing_policy_config
        WHERE active_flag = true
          AND policy_key IN (
              'COLLECTION_AUTOMATION_ENABLED',
              'COLLECTION_AUTOMATION_INTERVAL_HOURS',
              'COLLECTION_AUTOMATION_RETRY_HOURS',
              'COLLECTION_AUTOMATION_BATCH_SIZE',
              'COLLECTION_AUTOMATION_REVIEW_RECOVERY_LIMIT',
              'COLLECTION_AUTOMATION_STALE_RUN_HOURS'
          )
        ORDER BY policy_key, version_no DESC
        """
    ).fetchall()
    values = {str(row["policy_key"]): row.get("policy_value") for row in rows}
    return {
        # An unmigrated database remains fail-closed even when the runtime loop is enabled.
        "enabled": _policy_bool(values.get("COLLECTION_AUTOMATION_ENABLED"), False),
        "interval_hours": _policy_int(
            values.get("COLLECTION_AUTOMATION_INTERVAL_HOURS"),
            168,
            minimum=1,
            maximum=24 * 365,
        ),
        "retry_hours": _policy_int(
            values.get("COLLECTION_AUTOMATION_RETRY_HOURS"),
            24,
            minimum=1,
            maximum=168,
        ),
        "batch_size": _policy_int(
            values.get("COLLECTION_AUTOMATION_BATCH_SIZE"),
            6,
            minimum=1,
            maximum=50,
        ),
        "review_recovery_limit": _policy_int(
            values.get("COLLECTION_AUTOMATION_REVIEW_RECOVERY_LIMIT"),
            10,
            minimum=1,
            maximum=200,
        ),
        "stale_run_hours": _policy_int(
            values.get("COLLECTION_AUTOMATION_STALE_RUN_HOURS"),
            12,
            minimum=2,
            maximum=168,
        ),
    }


def recover_stale_collection_runs(
    connection: Any,
    *,
    stale_run_hours: int,
    request_context: dict[str, Any],
) -> list[str]:
    rows = connection.execute(
        """
        UPDATE ingestion_run
        SET
            run_state = 'failed',
            partial_completion_flag = true,
            error_summary = COALESCE(
                NULLIF(error_summary, ''),
                'Collection automation recovered an abandoned source-catalog run.'
            ),
            run_metadata = COALESCE(run_metadata, '{}'::jsonb) || jsonb_build_object(
                'automation_recovered', true,
                'automation_recovery_reason', 'stale_started_run'
            ),
            completed_at = now()
        WHERE run_state = 'started'
          AND COALESCE(run_metadata ->> 'pipeline_stage', '') = 'source_catalog_collection'
          AND started_at < now() - make_interval(hours => %(stale_run_hours)s)
        RETURNING run_id
        """,
        {"stale_run_hours": stale_run_hours},
    ).fetchall()
    run_ids = [str(row["run_id"]) for row in rows]
    for run_id in run_ids:
        _record_catalog_audit_event(
            connection,
            actor=AUTOMATION_ACTOR,
            request_context=request_context,
            event_type="source_catalog_collection_stale_recovered",
            target_id=run_id,
            target_type="run",
            diff_summary="Closed an abandoned source-catalog run so scheduled collection can continue.",
            metadata={"run_id": run_id, "stale_run_hours": stale_run_hours},
        )
    return run_ids


def load_recoverable_collection_review_task_ids(connection: Any, *, limit: int) -> list[str]:
    rows = connection.execute(
        """
        SELECT rt.review_task_id
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        JOIN source_document AS sd
          ON sd.source_document_id = nc.source_document_id
        JOIN ingestion_run AS ir
          ON ir.run_id = rt.run_id
        WHERE rt.review_state IN ('queued', 'deferred')
          AND nc.candidate_state = 'in_review'
          AND ir.run_state IN ('completed', 'failed', 'retried')
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
          AND NOT EXISTS (
              SELECT 1
              FROM model_execution AS me
              WHERE me.stage_name = 'ai_verification'
                AND me.execution_status = 'completed'
                AND me.execution_metadata ->> 'review_task_id' = rt.review_task_id
                AND me.execution_metadata ->> 'verification_contract_version' = 'review-ai-verification-v17'
                AND me.execution_metadata ? 'auto_approval_assessment'
          )
        ORDER BY rt.created_at ASC, rt.review_task_id ASC
        LIMIT %(limit)s
        """,
        {"limit": max(1, min(200, int(limit)))},
    ).fetchall()
    return [str(row["review_task_id"]) for row in rows]


def has_active_source_catalog_collection(connection: Any) -> bool:
    row = connection.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM ingestion_run
            WHERE run_state = 'started'
              AND COALESCE(run_metadata ->> 'pipeline_stage', '') = 'source_catalog_collection'
        ) AS active
        """
    ).fetchone()
    return bool(row and row.get("active"))


def load_due_catalog_item_ids(
    connection: Any,
    *,
    interval_hours: int,
    retry_hours: int,
    limit: int,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT sci.catalog_item_id
        FROM source_registry_catalog_item AS sci
        JOIN bank AS b
          ON b.bank_code = sci.bank_code
         AND b.country_code = sci.country_code
         AND b.status = 'active'
        JOIN country_registry AS cr
          ON cr.country_code = sci.country_code
         AND cr.status = 'active'
        JOIN product_type_registry AS ptr
          ON ptr.product_type_code = sci.product_type
         AND ptr.status = 'active'
        LEFT JOIN LATERAL (
            SELECT
                ir.started_at AS latest_started_at,
                ir.run_state AS latest_run_state,
                ir.partial_completion_flag AS latest_partial_completion_flag
            FROM ingestion_run AS ir
            WHERE COALESCE(ir.run_metadata ->> 'pipeline_stage', '') = 'source_catalog_collection'
              AND COALESCE(ir.run_metadata ->> 'country_code', ir.country_code) = sci.country_code
              AND COALESCE(ir.run_metadata ->> 'bank_code', '') = sci.bank_code
              AND COALESCE(ir.run_metadata ->> 'product_type', '') = sci.product_type
            ORDER BY ir.started_at DESC, ir.run_id DESC
            LIMIT 1
        ) AS latest_run ON true
        WHERE sci.status = 'active'
          AND sci.product_type = ANY(%(product_types)s::text[])
          AND (
              latest_run.latest_started_at IS NULL
              OR latest_run.latest_started_at < now() - make_interval(hours => %(interval_hours)s)
              OR (
                  (
                      latest_run.latest_run_state IN ('failed', 'retried')
                      OR latest_run.latest_partial_completion_flag = true
                  )
                  AND latest_run.latest_started_at < now() - make_interval(hours => %(retry_hours)s)
              )
          )
        ORDER BY
            latest_run.latest_started_at ASC NULLS FIRST,
            sci.country_code ASC,
            b.bank_name ASC,
            sci.product_type ASC,
            sci.catalog_item_id ASC
        LIMIT %(limit)s
        """,
        {
            "product_types": list(AUTOMATED_PRODUCT_TYPES),
            "interval_hours": max(1, min(24 * 365, int(interval_hours))),
            "retry_hours": max(1, min(168, int(retry_hours))),
            "limit": max(1, min(50, int(limit))),
        },
    ).fetchall()
    return [str(row["catalog_item_id"]) for row in rows]


def has_pending_aggregate_refresh(connection: Any) -> bool:
    row = connection.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM aggregate_refresh_request
            WHERE request_status IN ('queued', 'started')
        ) AS pending
        """
    ).fetchone()
    return bool(row and row.get("pending"))


def _try_acquire_scheduler_lock(connection: Any) -> bool:
    row = connection.execute(
        "SELECT pg_try_advisory_lock(%(lock_key)s) AS acquired",
        {"lock_key": COLLECTION_AUTOMATION_LOCK_KEY},
    ).fetchone()
    return bool(row and row.get("acquired"))


def _release_scheduler_lock(connection: Any) -> None:
    connection.execute(
        "SELECT pg_advisory_unlock(%(lock_key)s)",
        {"lock_key": COLLECTION_AUTOMATION_LOCK_KEY},
    )


def _policy_value(value: object) -> object:
    if isinstance(value, Mapping):
        return value.get("value")
    return value


def _policy_bool(value: object, default: bool) -> bool:
    normalized = _policy_value(value)
    if isinstance(normalized, bool):
        return normalized
    if isinstance(normalized, str):
        if normalized.strip().lower() in {"true", "1", "yes", "on"}:
            return True
        if normalized.strip().lower() in {"false", "0", "no", "off"}:
            return False
    return default


def _policy_int(value: object, default: int, *, minimum: int, maximum: int) -> int:
    try:
        normalized = int(float(_policy_value(value)))
    except (TypeError, ValueError):
        normalized = default
    return max(minimum, min(maximum, normalized))
