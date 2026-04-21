from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from api_service.security import new_id, utc_now
from api_service.source_registry_utils import repo_root

DEFAULT_REFRESH_SCOPE = "phase1_public"
DEFAULT_COUNTRY_CODE = "CA"
PRODUCT_PUBLIC_CACHE_TTL_SEC = 300
MUTATION_ROLES = {"admin", "reviewer"}


class AggregateRefreshError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def queue_review_aggregate_refresh_request(
    connection: Any,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    review_task_id: str,
    product_id: str | None,
    action_type: str,
    change_event_types: list[str],
    country_code: str = DEFAULT_COUNTRY_CODE,
    refresh_scope: str = DEFAULT_REFRESH_SCOPE,
) -> dict[str, Any]:
    requested_at = utc_now()
    request_row = {
        "aggregate_refresh_request_id": new_id("aggreq"),
        "refresh_scope": refresh_scope,
        "country_code": country_code,
        "request_status": "queued",
        "trigger_reason": "review_approval",
        "requested_by_user_id": actor.get("user_id"),
        "requested_by_label": _actor_label(actor),
        "review_task_id": review_task_id,
        "product_id": product_id,
        "request_metadata": {
            "action_type": action_type,
            "change_event_types": sorted({item for item in change_event_types if item}),
            "request_id": request_context.get("request_id"),
        },
        "requested_at": requested_at,
        "started_at": None,
        "completed_at": None,
        "snapshot_id": None,
        "error_summary": None,
    }
    _insert_request_row(connection, request_row=request_row)
    return _serialize_request_row(request_row, already_pending=False)


def request_manual_aggregate_refresh(
    connection: Any,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    country_code: str = DEFAULT_COUNTRY_CODE,
    refresh_scope: str = DEFAULT_REFRESH_SCOPE,
) -> dict[str, Any]:
    actor_role = str(actor.get("role", ""))
    if actor_role not in MUTATION_ROLES:
        raise AggregateRefreshError(
            status_code=403,
            code="forbidden",
            message="This account cannot queue aggregate refresh work.",
        )

    existing_pending = _load_latest_request_by_statuses(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
        statuses=("queued", "started"),
    )
    if existing_pending:
        return _serialize_request_row(existing_pending, already_pending=True)

    requested_at = utc_now()
    request_row = {
        "aggregate_refresh_request_id": new_id("aggreq"),
        "refresh_scope": refresh_scope,
        "country_code": country_code,
        "request_status": "queued",
        "trigger_reason": "manual_retry",
        "requested_by_user_id": actor.get("user_id"),
        "requested_by_label": _actor_label(actor),
        "review_task_id": None,
        "product_id": None,
        "request_metadata": {
            "request_id": request_context.get("request_id"),
            "reason": "manual_retry",
        },
        "requested_at": requested_at,
        "started_at": None,
        "completed_at": None,
        "snapshot_id": None,
        "error_summary": None,
    }
    _insert_request_row(connection, request_row=request_row)
    _record_aggregate_refresh_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        event_type="aggregate_refresh_retry_requested",
        target_id=str(request_row["aggregate_refresh_request_id"]),
        previous_state=None,
        new_state="queued",
        diff_summary=f"Queued manual aggregate refresh for {country_code} {refresh_scope}.",
        payload={
            "aggregate_refresh_request_id": request_row["aggregate_refresh_request_id"],
            "country_code": country_code,
            "refresh_scope": refresh_scope,
        },
    )
    return _serialize_request_row(request_row, already_pending=False)


def claim_aggregate_refresh_batch(
    connection: Any,
    *,
    country_code: str = DEFAULT_COUNTRY_CODE,
    refresh_scope: str = DEFAULT_REFRESH_SCOPE,
) -> dict[str, Any] | None:
    rows = connection.execute(
        """
        SELECT
            aggregate_refresh_request_id
        FROM aggregate_refresh_request
        WHERE refresh_scope = %(refresh_scope)s
          AND country_code = %(country_code)s
          AND request_status IN ('queued', 'started')
        ORDER BY requested_at ASC, aggregate_refresh_request_id ASC
        """,
        {
            "refresh_scope": refresh_scope,
            "country_code": country_code,
        },
    ).fetchall()
    request_ids = [str(row["aggregate_refresh_request_id"]) for row in rows]
    if not request_ids:
        return None

    started_at = utc_now()
    connection.execute(
        """
        UPDATE aggregate_refresh_request
        SET
            request_status = 'started',
            started_at = %(started_at)s,
            completed_at = NULL,
            snapshot_id = NULL,
            error_summary = NULL
        WHERE aggregate_refresh_request_id = ANY(%(request_ids)s)
        """,
        {
            "request_ids": request_ids,
            "started_at": started_at,
        },
    )
    return {
        "request_ids": request_ids,
        "country_code": country_code,
        "refresh_scope": refresh_scope,
        "started_at": _serialize_timestamp(started_at),
    }


def complete_aggregate_refresh_batch(
    connection: Any,
    *,
    request_ids: list[str],
    snapshot_id: str,
    completed_at: datetime | None = None,
) -> None:
    finished_at = completed_at or utc_now()
    connection.execute(
        """
        UPDATE aggregate_refresh_request
        SET
            request_status = 'completed',
            completed_at = %(completed_at)s,
            snapshot_id = %(snapshot_id)s,
            error_summary = NULL
        WHERE aggregate_refresh_request_id = ANY(%(request_ids)s)
        """,
        {
            "request_ids": request_ids,
            "completed_at": finished_at,
            "snapshot_id": snapshot_id,
        },
    )


def fail_aggregate_refresh_batch(
    connection: Any,
    *,
    request_ids: list[str],
    error_summary: str,
    completed_at: datetime | None = None,
) -> None:
    finished_at = completed_at or utc_now()
    connection.execute(
        """
        UPDATE aggregate_refresh_request
        SET
            request_status = 'failed',
            completed_at = %(completed_at)s,
            error_summary = %(error_summary)s
        WHERE aggregate_refresh_request_id = ANY(%(request_ids)s)
        """,
        {
            "request_ids": request_ids,
            "completed_at": finished_at,
            "error_summary": error_summary[:2000],
        },
    )


def load_dashboard_health(
    connection: Any,
    *,
    country_code: str = DEFAULT_COUNTRY_CODE,
    refresh_scope: str = DEFAULT_REFRESH_SCOPE,
) -> dict[str, Any]:
    latest_success = _load_latest_refresh_run(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
        statuses=("completed",),
    )
    latest_attempt = _load_latest_refresh_run(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
        statuses=("started", "completed", "failed"),
    )
    latest_request = _load_latest_request_by_statuses(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
        statuses=("queued", "started", "completed", "failed"),
    )
    latest_failed_request = _load_latest_request_by_statuses(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
        statuses=("failed",),
    )
    pending_counts = _load_pending_request_counts(
        connection,
        country_code=country_code,
        refresh_scope=refresh_scope,
    )
    canonical_stats = _load_canonical_scope_stats(connection, country_code=country_code)
    projection_stats = _load_projection_scope_stats(
        connection,
        snapshot_id=str(latest_success["snapshot_id"]) if latest_success else None,
        country_code=country_code,
    )

    active_product_count = int(canonical_stats.get("active_product_count") or 0)
    projected_active_product_count = int(projection_stats.get("active_product_count") or 0)
    latest_canonical_change_at = canonical_stats.get("latest_canonical_change_at")
    success_cutoff_at = latest_success.get("source_change_cutoff_at") if latest_success else None
    missing_data_ratio = _missing_data_ratio(
        canonical_count=active_product_count,
        projected_count=projected_active_product_count,
    )
    stale_flag, stale_reason = _build_stale_state(
        latest_success=latest_success,
        latest_canonical_change_at=latest_canonical_change_at,
        success_cutoff_at=success_cutoff_at,
        active_product_count=active_product_count,
    )
    status = _domain_status(
        latest_success=latest_success,
        latest_request=latest_request,
        pending_counts=pending_counts,
        stale_flag=stale_flag,
    )

    domain = {
        "domain_key": f"public_aggregate_{country_code.lower()}",
        "latest_snapshot_id": str(latest_success["snapshot_id"]) if latest_success else None,
        "latest_success_at": _serialize_timestamp(latest_success.get("refreshed_at")) if latest_success else None,
        "latest_failure_at": _serialize_timestamp(latest_failed_request.get("completed_at")) if latest_failed_request else None,
        "status": status,
        "missing_data_ratio": missing_data_ratio,
        "cache_ttl_sec": PRODUCT_PUBLIC_CACHE_TTL_SEC,
        "serving_snapshot_id": str(latest_success["snapshot_id"]) if latest_success else None,
        "serving_snapshot_refreshed_at": _serialize_timestamp(latest_success.get("refreshed_at")) if latest_success else None,
        "serving_note": _build_serving_note(latest_success=latest_success, latest_attempt=latest_attempt),
        "latest_attempt_snapshot_id": str(latest_attempt["snapshot_id"]) if latest_attempt else None,
        "latest_attempt_status": str(latest_attempt["refresh_status"]) if latest_attempt else None,
        "latest_attempt_at": _serialize_timestamp(
            latest_attempt.get("attempted_at") or latest_attempt.get("refreshed_at")
        )
        if latest_attempt
        else None,
        "latest_attempt_error_summary": latest_attempt.get("error_summary") if latest_attempt else None,
        "latest_request_id": str(latest_request["aggregate_refresh_request_id"]) if latest_request else None,
        "latest_request_status": str(latest_request["request_status"]) if latest_request else None,
        "latest_request_reason": str(latest_request["trigger_reason"]) if latest_request else None,
        "latest_requested_at": _serialize_timestamp(latest_request.get("requested_at")) if latest_request else None,
        "latest_request_completed_at": _serialize_timestamp(latest_request.get("completed_at")) if latest_request else None,
        "latest_request_snapshot_id": str(latest_request["snapshot_id"]) if latest_request and latest_request.get("snapshot_id") else None,
        "queued_request_count": int(pending_counts.get("queued_count") or 0),
        "in_progress_request_count": int(pending_counts.get("started_count") or 0),
        "active_product_count": active_product_count,
        "projected_active_product_count": projected_active_product_count,
        "latest_canonical_change_at": _serialize_timestamp(latest_canonical_change_at),
        "stale_flag": stale_flag,
        "stale_reason": stale_reason,
        "retry_action": {
            "available": int(pending_counts.get("queued_count") or 0) + int(pending_counts.get("started_count") or 0) == 0,
            "reason": (
                "A refresh is already queued or running."
                if int(pending_counts.get("queued_count") or 0) + int(pending_counts.get("started_count") or 0) > 0
                else None
            ),
        },
    }

    summary = {
        "total_domains": 1,
        "healthy_domains": 1 if status == "healthy" else 0,
        "pending_domains": 1 if status == "pending" else 0,
        "failed_domains": 1 if status == "failed" else 0,
        "stale_domains": 1 if status == "stale" else 0,
        "empty_domains": 1 if status == "empty" else 0,
    }
    return {
        "domains": [domain],
        "summary": summary,
    }


def launch_aggregate_refresh_runner() -> dict[str, Any]:
    root = repo_root()
    temp_dir = root / "tmp" / "aggregate-refresh"
    temp_dir.mkdir(parents=True, exist_ok=True)
    log_path = temp_dir / "aggregate-refresh-runner.log"

    env = os.environ.copy()
    current_python_path = env.get("PYTHONPATH", "")
    api_service_path = str(root / "api" / "service")
    env["PYTHONPATH"] = os.pathsep.join([api_service_path, current_python_path]) if current_python_path else api_service_path

    with log_path.open("a", encoding="utf-8") as log_file:
        try:
            subprocess.Popen(  # noqa: S603
                [sys.executable, "-m", "api_service.aggregate_refresh_runner"],
                cwd=str(root),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        except OSError as exc:
            return {
                "launched": False,
                "error": f"Aggregate refresh runner could not be launched: {exc}",
                "log_path": str(log_path),
            }
    return {
        "launched": True,
        "error": None,
        "log_path": str(log_path),
    }


def _insert_request_row(connection: Any, *, request_row: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO aggregate_refresh_request (
            aggregate_refresh_request_id,
            refresh_scope,
            country_code,
            request_status,
            trigger_reason,
            requested_by_user_id,
            requested_by_label,
            review_task_id,
            product_id,
            request_metadata,
            requested_at,
            started_at,
            completed_at,
            snapshot_id,
            error_summary
        )
        VALUES (
            %(aggregate_refresh_request_id)s,
            %(refresh_scope)s,
            %(country_code)s,
            %(request_status)s,
            %(trigger_reason)s,
            %(requested_by_user_id)s,
            %(requested_by_label)s,
            %(review_task_id)s,
            %(product_id)s,
            %(request_metadata)s::jsonb,
            %(requested_at)s,
            %(started_at)s,
            %(completed_at)s,
            %(snapshot_id)s,
            %(error_summary)s
        )
        """,
        {
            **request_row,
            "request_metadata": json.dumps(request_row["request_metadata"], ensure_ascii=True, sort_keys=True),
        },
    )


def _load_latest_refresh_run(
    connection: Any,
    *,
    country_code: str,
    refresh_scope: str,
    statuses: tuple[str, ...],
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            snapshot_id,
            refresh_scope,
            country_code,
            refresh_status,
            source_change_cutoff_at,
            attempted_at,
            refreshed_at,
            stale_flag,
            error_summary,
            refresh_metadata
        FROM aggregate_refresh_run
        WHERE country_code = %(country_code)s
          AND refresh_scope = %(refresh_scope)s
          AND refresh_status = ANY(%(statuses)s)
        ORDER BY COALESCE(refreshed_at, attempted_at) DESC, attempted_at DESC, snapshot_id DESC
        LIMIT 1
        """,
        {
            "country_code": country_code,
            "refresh_scope": refresh_scope,
            "statuses": list(statuses),
        },
    ).fetchone()
    return dict(row) if row else None


def _load_latest_request_by_statuses(
    connection: Any,
    *,
    country_code: str,
    refresh_scope: str,
    statuses: tuple[str, ...],
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            aggregate_refresh_request_id,
            refresh_scope,
            country_code,
            request_status,
            trigger_reason,
            requested_by_user_id,
            requested_by_label,
            review_task_id,
            product_id,
            request_metadata,
            requested_at,
            started_at,
            completed_at,
            snapshot_id,
            error_summary
        FROM aggregate_refresh_request
        WHERE country_code = %(country_code)s
          AND refresh_scope = %(refresh_scope)s
          AND request_status = ANY(%(statuses)s)
        ORDER BY COALESCE(completed_at, started_at, requested_at) DESC, aggregate_refresh_request_id DESC
        LIMIT 1
        """,
        {
            "country_code": country_code,
            "refresh_scope": refresh_scope,
            "statuses": list(statuses),
        },
    ).fetchone()
    return dict(row) if row else None


def _load_pending_request_counts(connection: Any, *, country_code: str, refresh_scope: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE request_status = 'queued') AS queued_count,
            COUNT(*) FILTER (WHERE request_status = 'started') AS started_count
        FROM aggregate_refresh_request
        WHERE country_code = %(country_code)s
          AND refresh_scope = %(refresh_scope)s
          AND request_status IN ('queued', 'started')
        """,
        {
            "country_code": country_code,
            "refresh_scope": refresh_scope,
        },
    ).fetchone()
    return dict(row) if row else {"queued_count": 0, "started_count": 0}


def _load_canonical_scope_stats(connection: Any, *, country_code: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'active') AS active_product_count,
            MAX(COALESCE(last_changed_at, last_verified_at)) AS latest_canonical_change_at
        FROM canonical_product
        WHERE country_code = %(country_code)s
          AND product_family = 'deposit'
        """,
        {"country_code": country_code},
    ).fetchone()
    return dict(row) if row else {"active_product_count": 0, "latest_canonical_change_at": None}


def _load_projection_scope_stats(connection: Any, *, snapshot_id: str | None, country_code: str) -> dict[str, Any]:
    if not snapshot_id:
        return {"active_product_count": 0}
    row = connection.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'active') AS active_product_count
        FROM public_product_projection
        WHERE snapshot_id = %(snapshot_id)s
          AND country_code = %(country_code)s
        """,
        {
            "snapshot_id": snapshot_id,
            "country_code": country_code,
        },
    ).fetchone()
    return dict(row) if row else {"active_product_count": 0}


def _build_stale_state(
    *,
    latest_success: dict[str, Any] | None,
    latest_canonical_change_at: Any,
    success_cutoff_at: Any,
    active_product_count: int,
) -> tuple[bool, str | None]:
    if active_product_count > 0 and not latest_success:
        return True, "No successful aggregate snapshot is available yet."
    latest_change = _coerce_datetime(latest_canonical_change_at)
    success_cutoff = _coerce_datetime(success_cutoff_at)
    if latest_change and success_cutoff and latest_change > success_cutoff:
        return True, "Canonical product changes are newer than the latest successful public snapshot."
    return False, None


def _domain_status(
    *,
    latest_success: dict[str, Any] | None,
    latest_request: dict[str, Any] | None,
    pending_counts: dict[str, Any],
    stale_flag: bool,
) -> str:
    pending_total = int(pending_counts.get("queued_count") or 0) + int(pending_counts.get("started_count") or 0)
    if pending_total > 0:
        return "pending"
    if latest_request and str(latest_request.get("request_status") or "") == "failed":
        latest_request_completed_at = _coerce_datetime(latest_request.get("completed_at"))
        latest_success_at = _coerce_datetime(latest_success.get("refreshed_at")) if latest_success else None
        if latest_success_at is None or (latest_request_completed_at and latest_request_completed_at >= latest_success_at):
            return "failed"
    if stale_flag:
        return "stale"
    if latest_success:
        return "healthy"
    return "empty"


def _build_serving_note(*, latest_success: dict[str, Any] | None, latest_attempt: dict[str, Any] | None) -> str:
    if latest_success and latest_attempt and str(latest_attempt.get("refresh_status") or "") == "failed":
        latest_attempt_at = _coerce_datetime(latest_attempt.get("attempted_at") or latest_attempt.get("refreshed_at"))
        latest_success_at = _coerce_datetime(latest_success.get("refreshed_at") or latest_success.get("attempted_at"))
        if latest_attempt_at and latest_success_at and latest_attempt_at >= latest_success_at:
            return "Public is still serving the latest successful aggregate snapshot after a newer refresh failure."
    if latest_success:
        return "Public is serving the latest successful aggregate snapshot."
    return "No successful aggregate snapshot is available yet."


def _missing_data_ratio(*, canonical_count: int, projected_count: int) -> float:
    if canonical_count <= 0:
        return 0.0
    missing_count = max(canonical_count - projected_count, 0)
    return round(missing_count / canonical_count, 4)


def _serialize_request_row(row: dict[str, Any], *, already_pending: bool) -> dict[str, Any]:
    return {
        "aggregate_refresh_request_id": str(row["aggregate_refresh_request_id"]),
        "refresh_scope": str(row["refresh_scope"]),
        "country_code": str(row["country_code"]),
        "request_status": str(row["request_status"]),
        "trigger_reason": str(row["trigger_reason"]),
        "requested_by_label": row.get("requested_by_label"),
        "review_task_id": row.get("review_task_id"),
        "product_id": row.get("product_id"),
        "requested_at": _serialize_timestamp(row.get("requested_at")),
        "started_at": _serialize_timestamp(row.get("started_at")),
        "completed_at": _serialize_timestamp(row.get("completed_at")),
        "snapshot_id": row.get("snapshot_id"),
        "error_summary": row.get("error_summary"),
        "already_pending": already_pending,
    }


def _record_aggregate_refresh_audit_event(
    connection: Any,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    event_type: str,
    target_id: str,
    previous_state: str | None,
    new_state: str | None,
    diff_summary: str | None,
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
            'run',
            %(event_type)s,
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            'aggregate_refresh_request',
            %(target_id)s,
            %(previous_state)s,
            %(new_state)s,
            NULL,
            NULL,
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
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_id": target_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "request_id": request_context.get("request_id"),
            "diff_summary": diff_summary,
            "source_ref": request_context.get("request_id"),
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "event_payload": json.dumps(payload, ensure_ascii=True, sort_keys=True),
            "occurred_at": utc_now(),
        },
    )


def _actor_label(actor: dict[str, Any]) -> str | None:
    for key in ("email", "display_name", "user_id"):
        value = str(actor.get(key) or "").strip()
        if value:
            return value
    return None


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _serialize_timestamp(value: Any) -> str | None:
    normalized = _coerce_datetime(value)
    return normalized.isoformat() if normalized else None
