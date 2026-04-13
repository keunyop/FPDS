from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection

RUN_STATES = ("started", "completed", "failed", "retried")
DEFAULT_RUN_STATES = ("started", "completed", "failed")

_RUN_TYPE_SQL = "COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), ir.trigger_type)"
_SAFE_SOURCE_METADATA_KEYS = {
    "attempt_count",
    "candidate_id",
    "candidate_run_id",
    "chunk_count",
    "correlation_id",
    "field_evidence_link_count",
    "normalization_action",
    "parse_action",
    "parser_version",
    "preflight_status",
    "queue_reason_codes",
    "request_id",
    "review_task_id",
    "runtime_notes",
    "snapshot_action",
    "source_confidence",
    "validation_action",
    "validation_issue_codes",
    "validation_status",
}


@dataclass(frozen=True)
class RunStatusFilters:
    states: tuple[str, ...]
    run_type: str | None
    partial_only: bool
    started_from: datetime | None
    started_to: datetime | None
    search: str | None
    sort_by: str
    sort_order: str
    page: int
    page_size: int


def normalize_run_status_filters(
    *,
    states: Iterable[str] | None,
    run_type: str | None,
    partial_only: bool,
    started_from: datetime | None,
    started_to: datetime | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> RunStatusFilters:
    normalized_states = tuple(
        dict.fromkeys(
            state.strip().lower()
            for state in (states or DEFAULT_RUN_STATES)
            if state.strip() and state.strip().lower() in RUN_STATES
        )
    )
    if not normalized_states:
        normalized_states = DEFAULT_RUN_STATES

    normalized_sort_by = sort_by.strip().lower() if sort_by else "started_at"
    if normalized_sort_by not in {"started_at", "completed_at", "candidate_count", "review_queued_count", "run_type"}:
        normalized_sort_by = "started_at"

    normalized_sort_order = "asc" if sort_order == "asc" else "desc"

    return RunStatusFilters(
        states=normalized_states,
        run_type=run_type.strip().lower() if run_type and run_type.strip() else None,
        partial_only=partial_only,
        started_from=started_from,
        started_to=started_to,
        search=_normalize_search(search),
        sort_by=normalized_sort_by,
        sort_order=normalized_sort_order,
        page=page,
        page_size=page_size,
    )


def load_run_status_list(connection: Connection, *, filters: RunStatusFilters) -> dict[str, Any]:
    where_sql, params = _build_where_clause(filters)
    total_row = connection.execute(
        f"""
        SELECT COUNT(*) AS total_items
        FROM ingestion_run AS ir
        WHERE {where_sql}
        """,
        params,
    ).fetchone()
    total_items = int(total_row["total_items"]) if total_row else 0

    state_rows = connection.execute(
        f"""
        SELECT ir.run_state, COUNT(*) AS item_count
        FROM ingestion_run AS ir
        WHERE {where_sql}
        GROUP BY ir.run_state
        """,
        params,
    ).fetchall()

    type_rows = connection.execute(
        f"""
        SELECT {_RUN_TYPE_SQL} AS run_type, COUNT(*) AS item_count
        FROM ingestion_run AS ir
        WHERE {where_sql}
        GROUP BY {_RUN_TYPE_SQL}
        """,
        params,
    ).fetchall()
    partial_row = connection.execute(
        f"""
        SELECT COUNT(*) AS item_count
        FROM ingestion_run AS ir
        WHERE {where_sql}
          AND ir.partial_completion_flag = true
        """,
        params,
    ).fetchone()
    partial_items = int(partial_row["item_count"]) if partial_row else 0

    item_rows = connection.execute(
        f"""
        SELECT
            ir.run_id,
            {_RUN_TYPE_SQL} AS run_type,
            ir.run_state,
            ir.trigger_type,
            ir.triggered_by,
            ir.source_scope_count,
            ir.source_success_count,
            ir.source_failure_count,
            ir.candidate_count,
            ir.review_queued_count,
            ir.error_summary,
            ir.partial_completion_flag,
            ir.retry_of_run_id,
            ir.retried_by_run_id,
            ir.started_at,
            ir.completed_at,
            COALESCE(ir.run_metadata ->> 'pipeline_stage', '') AS pipeline_stage,
            COALESCE(ir.run_metadata ->> 'correlation_id', '') AS correlation_id,
            COALESCE(rsi_counts.source_item_count, ir.source_scope_count) AS source_item_count
        FROM ingestion_run AS ir
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS source_item_count
            FROM run_source_item AS rsi
            WHERE rsi.run_id = ir.run_id
        ) AS rsi_counts
          ON true
        WHERE {where_sql}
        ORDER BY {_build_order_by_clause(filters)}
        LIMIT %(limit)s
        OFFSET %(offset)s
        """,
        {
            **params,
            "limit": filters.page_size,
            "offset": (filters.page - 1) * filters.page_size,
        },
    ).fetchall()

    items = [_serialize_run_list_row(row) for row in item_rows]
    state_counts = {state: 0 for state in RUN_STATES}
    for row in state_rows:
        state_counts[str(row["run_state"])] = int(row["item_count"])

    run_type_counts: dict[str, int] = {}
    for row in type_rows:
        run_type = str(row["run_type"])
        run_type_counts[run_type] = int(row["item_count"])

    total_pages = (total_items + filters.page_size - 1) // filters.page_size if total_items else 0
    return {
        "items": items,
        "summary": {
            "total_items": total_items,
            "state_counts": state_counts,
            "run_type_counts": run_type_counts,
            "partial_items": partial_items,
        },
        "applied_filters": {
            "states": list(filters.states),
            "run_type": filters.run_type,
            "partial_only": filters.partial_only,
            "started_from": filters.started_from.isoformat() if filters.started_from else None,
            "started_to": filters.started_to.isoformat() if filters.started_to else None,
            "search": filters.search,
            "sort_by": filters.sort_by,
            "sort_order": filters.sort_order,
        },
        "page": filters.page,
        "page_size": filters.page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next_page": filters.page < total_pages,
    }


def load_run_status_detail(connection: Connection, *, run_id: str) -> dict[str, Any] | None:
    run_row = connection.execute(
        f"""
        SELECT
            ir.run_id,
            {_RUN_TYPE_SQL} AS run_type,
            ir.run_state,
            ir.trigger_type,
            ir.triggered_by,
            ir.source_scope_count,
            ir.source_success_count,
            ir.source_failure_count,
            ir.candidate_count,
            ir.review_queued_count,
            ir.error_summary,
            ir.partial_completion_flag,
            ir.retry_of_run_id,
            ir.retried_by_run_id,
            ir.run_metadata,
            ir.started_at,
            ir.completed_at,
            COALESCE(rsi_counts.source_item_count, ir.source_scope_count) AS source_item_count
        FROM ingestion_run AS ir
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS source_item_count
            FROM run_source_item AS rsi
            WHERE rsi.run_id = ir.run_id
        ) AS rsi_counts
          ON true
        WHERE ir.run_id = %(run_id)s
        """,
        {"run_id": run_id},
    ).fetchone()
    if not run_row:
        return None

    source_rows = connection.execute(
        """
        SELECT
            rsi.source_document_id,
            COALESCE(sd.source_metadata ->> 'source_id', rsi.source_document_id) AS source_id,
            sd.bank_code,
            COALESCE(b.bank_name, sd.bank_code) AS bank_name,
            sd.country_code,
            sd.normalized_source_url,
            sd.source_type,
            sd.source_language,
            rsi.selected_snapshot_id,
            ss.fetched_at,
            pd.parsed_document_id,
            pd.parse_quality_note,
            rsi.stage_status,
            rsi.warning_count,
            rsi.error_count,
            rsi.error_summary,
            COALESCE(rsi.stage_metadata, '{}'::jsonb) AS stage_metadata,
            COALESCE(rsi.stage_metadata -> 'runtime_notes', '[]'::jsonb) AS runtime_notes
        FROM run_source_item AS rsi
        JOIN source_document AS sd
          ON sd.source_document_id = rsi.source_document_id
        LEFT JOIN bank AS b
          ON b.bank_code = sd.bank_code
        LEFT JOIN source_snapshot AS ss
          ON ss.snapshot_id = rsi.selected_snapshot_id
        LEFT JOIN parsed_document AS pd
          ON pd.snapshot_id = ss.snapshot_id
        WHERE rsi.run_id = %(run_id)s
        ORDER BY COALESCE(sd.source_metadata ->> 'source_id', rsi.source_document_id), rsi.created_at ASC
        """,
        {"run_id": run_id},
    ).fetchall()

    model_execution_rows = connection.execute(
        """
        SELECT
            stage_name,
            execution_status,
            started_at,
            completed_at
        FROM model_execution
        WHERE run_id = %(run_id)s
        ORDER BY started_at ASC, stage_name ASC
        """,
        {"run_id": run_id},
    ).fetchall()

    usage_rows = connection.execute(
        """
        SELECT
            COALESCE(me.stage_name, '') AS stage_name,
            lur.prompt_tokens,
            lur.completion_tokens,
            lur.estimated_cost,
            COALESCE(lur.usage_metadata, '{}'::jsonb) AS usage_metadata
        FROM llm_usage_record AS lur
        LEFT JOIN model_execution AS me
          ON me.model_execution_id = lur.model_execution_id
        WHERE lur.run_id = %(run_id)s
        ORDER BY lur.recorded_at ASC
        """,
        {"run_id": run_id},
    ).fetchall()

    review_rows = connection.execute(
        """
        SELECT
            rt.review_task_id,
            rt.candidate_id,
            rt.review_state,
            rt.queue_reason_code,
            rt.created_at,
            nc.product_name,
            nc.validation_status,
            COALESCE(b.bank_name, nc.bank_code) AS bank_name
        FROM review_task AS rt
        JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        LEFT JOIN bank AS b
          ON b.bank_code = nc.bank_code
        WHERE rt.run_id = %(run_id)s
        ORDER BY rt.created_at DESC, rt.review_task_id ASC
        """,
        {"run_id": run_id},
    ).fetchall()

    run_metadata = _coerce_mapping(run_row.get("run_metadata"))
    serialized_source_rows = [_serialize_run_source_item_row(row) for row in source_rows]
    return {
        "run": {
            "run_id": str(run_row["run_id"]),
            "run_type": str(run_row["run_type"]),
            "run_status": str(run_row["run_state"]),
            "trigger_type": str(run_row["trigger_type"]),
            "triggered_by": _string_or_none(run_row.get("triggered_by")),
            "source_item_count": int(run_row["source_item_count"]) if run_row.get("source_item_count") is not None else 0,
            "source_scope_count": int(run_row["source_scope_count"]) if run_row.get("source_scope_count") is not None else 0,
            "success_count": int(run_row["source_success_count"]) if run_row.get("source_success_count") is not None else 0,
            "failure_count": int(run_row["source_failure_count"]) if run_row.get("source_failure_count") is not None else 0,
            "candidate_count": int(run_row["candidate_count"]) if run_row.get("candidate_count") is not None else 0,
            "review_queued_count": int(run_row["review_queued_count"]) if run_row.get("review_queued_count") is not None else 0,
            "partial_completion_flag": bool(run_row["partial_completion_flag"]),
            "error_summary": _string_or_none(run_row.get("error_summary")),
            "retry_of_run_id": _string_or_none(run_row.get("retry_of_run_id")),
            "retried_by_run_id": _string_or_none(run_row.get("retried_by_run_id")),
            "started_at": run_row["started_at"].isoformat() if run_row.get("started_at") else None,
            "completed_at": run_row["completed_at"].isoformat() if run_row.get("completed_at") else None,
            "pipeline_stage": _string_or_none(run_metadata.get("pipeline_stage")),
            "correlation_id": _string_or_none(run_metadata.get("correlation_id")),
            "request_id": _string_or_none(run_metadata.get("request_id")),
            "source_ids": _coerce_string_list(run_metadata.get("source_ids")),
        },
        "source_items": serialized_source_rows,
        "stage_summaries": _build_stage_summaries(run_row=run_row, source_rows=source_rows, model_execution_rows=model_execution_rows),
        "error_events": _build_error_events(run_row=run_row, source_rows=serialized_source_rows),
        "usage_summary": _build_usage_summary(usage_rows=usage_rows, model_execution_rows=model_execution_rows),
        "related_review_tasks": [_serialize_related_review_task_row(row) for row in review_rows],
    }


def _build_where_clause(filters: RunStatusFilters) -> tuple[str, dict[str, Any]]:
    clauses = ["ir.run_state = ANY(%(states)s)"]
    params: dict[str, Any] = {"states": list(filters.states)}

    if filters.run_type:
        clauses.append(f"{_RUN_TYPE_SQL} = %(run_type)s")
        params["run_type"] = filters.run_type
    if filters.partial_only:
        clauses.append("ir.partial_completion_flag = true")
    if filters.started_from:
        clauses.append("ir.started_at >= %(started_from)s")
        params["started_from"] = filters.started_from
    if filters.started_to:
        clauses.append("ir.started_at <= %(started_to)s")
        params["started_to"] = filters.started_to
    if filters.search:
        clauses.append(
            """
            (
                ir.run_id ILIKE %(search)s
                OR ir.trigger_type ILIKE %(search)s
                OR COALESCE(ir.triggered_by, '') ILIKE %(search)s
                OR COALESCE(ir.run_metadata ->> 'pipeline_stage', '') ILIKE %(search)s
                OR COALESCE(ir.run_metadata ->> 'correlation_id', '') ILIKE %(search)s
            )
            """
        )
        params["search"] = f"%{filters.search}%"

    return " AND ".join(clause.strip() for clause in clauses), params


def _build_order_by_clause(filters: RunStatusFilters) -> str:
    direction = "ASC" if filters.sort_order == "asc" else "DESC"
    if filters.sort_by == "completed_at":
        return f"ir.completed_at {direction} NULLS LAST, ir.started_at DESC, ir.run_id DESC"
    if filters.sort_by == "candidate_count":
        return f"ir.candidate_count {direction}, ir.started_at DESC, ir.run_id DESC"
    if filters.sort_by == "review_queued_count":
        return f"ir.review_queued_count {direction}, ir.started_at DESC, ir.run_id DESC"
    if filters.sort_by == "run_type":
        return f"{_RUN_TYPE_SQL} {direction}, ir.started_at DESC, ir.run_id DESC"
    return f"ir.started_at {direction}, ir.run_id DESC"


def _serialize_run_list_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": str(row["run_id"]),
        "run_type": str(row["run_type"]),
        "run_status": str(row["run_state"]),
        "trigger_type": str(row["trigger_type"]),
        "triggered_by": _string_or_none(row.get("triggered_by")),
        "started_at": row["started_at"].isoformat() if row.get("started_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "source_item_count": int(row["source_item_count"]) if row.get("source_item_count") is not None else 0,
        "candidate_count": int(row["candidate_count"]) if row.get("candidate_count") is not None else 0,
        "review_queued_count": int(row["review_queued_count"]) if row.get("review_queued_count") is not None else 0,
        "success_count": int(row["source_success_count"]) if row.get("source_success_count") is not None else 0,
        "failure_count": int(row["source_failure_count"]) if row.get("source_failure_count") is not None else 0,
        "partial_completion_flag": bool(row["partial_completion_flag"]),
        "error_summary": _string_or_none(row.get("error_summary")),
        "pipeline_stage": _string_or_none(row.get("pipeline_stage")),
        "correlation_id": _string_or_none(row.get("correlation_id")),
        "retry_of_run_id": _string_or_none(row.get("retry_of_run_id")),
        "retried_by_run_id": _string_or_none(row.get("retried_by_run_id")),
    }


def _serialize_run_source_item_row(row: dict[str, Any]) -> dict[str, Any]:
    stage_metadata = _coerce_mapping(row.get("stage_metadata"))
    return {
        "source_document_id": str(row["source_document_id"]),
        "source_id": str(row["source_id"]),
        "bank_code": str(row["bank_code"]),
        "bank_name": str(row["bank_name"]),
        "country_code": str(row["country_code"]),
        "source_type": str(row["source_type"]),
        "source_language": str(row["source_language"]),
        "source_url": _string_or_none(row.get("normalized_source_url")),
        "snapshot_id": _string_or_none(row.get("selected_snapshot_id")),
        "fetched_at": row["fetched_at"].isoformat() if row.get("fetched_at") else None,
        "parsed_document_id": _string_or_none(row.get("parsed_document_id")),
        "parse_quality_note": _string_or_none(row.get("parse_quality_note")),
        "stage_status": str(row["stage_status"]),
        "warning_count": int(row["warning_count"]) if row.get("warning_count") is not None else 0,
        "error_count": int(row["error_count"]) if row.get("error_count") is not None else 0,
        "error_summary": _string_or_none(row.get("error_summary")),
        "runtime_notes": _coerce_string_list(row.get("runtime_notes")),
        "safe_metadata": _filter_safe_source_metadata(stage_metadata),
    }


def _serialize_related_review_task_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_task_id": str(row["review_task_id"]),
        "candidate_id": str(row["candidate_id"]),
        "review_state": str(row["review_state"]),
        "queue_reason_code": str(row["queue_reason_code"]),
        "product_name": str(row["product_name"]),
        "bank_name": str(row["bank_name"]),
        "validation_status": str(row["validation_status"]),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _build_stage_summaries(
    *,
    run_row: dict[str, Any],
    source_rows: list[dict[str, Any]],
    model_execution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if model_execution_rows:
        grouped: dict[str, dict[str, Any]] = {}
        for row in model_execution_rows:
            stage_name = str(row["stage_name"])
            bucket = grouped.setdefault(
                stage_name,
                {
                    "stage_name": stage_name,
                    "stage_label": _stage_label(stage_name),
                    "execution_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "execution_status_counts": {},
                    "started_at": None,
                    "completed_at": None,
                },
            )
            bucket["execution_count"] += 1
            status = str(row["execution_status"])
            bucket["execution_status_counts"][status] = bucket["execution_status_counts"].get(status, 0) + 1
            if status == "completed":
                bucket["success_count"] += 1
            else:
                bucket["failure_count"] += 1

            started_at = row.get("started_at")
            completed_at = row.get("completed_at")
            if started_at and (bucket["started_at"] is None or started_at < bucket["started_at"]):
                bucket["started_at"] = started_at
            if completed_at and (bucket["completed_at"] is None or completed_at > bucket["completed_at"]):
                bucket["completed_at"] = completed_at

        summaries: list[dict[str, Any]] = []
        for stage_name, bucket in grouped.items():
            summaries.append(
                {
                    "stage_name": stage_name,
                    "stage_label": bucket["stage_label"],
                    "stage_status": _resolve_stage_status(
                        status_counts=bucket["execution_status_counts"],
                        partial_completion_flag=bool(run_row["partial_completion_flag"]),
                    ),
                    "execution_count": bucket["execution_count"],
                    "success_count": bucket["success_count"],
                    "failure_count": bucket["failure_count"],
                    "execution_status_counts": bucket["execution_status_counts"],
                    "started_at": bucket["started_at"].isoformat() if bucket["started_at"] else None,
                    "completed_at": bucket["completed_at"].isoformat() if bucket["completed_at"] else None,
                }
            )
        summaries.sort(key=lambda item: item["started_at"] or "")
        return summaries

    source_count = len(source_rows) or int(run_row.get("source_scope_count") or 0)
    success_count = int(run_row.get("source_success_count") or 0)
    failure_count = int(run_row.get("source_failure_count") or 0)
    return [
        {
            "stage_name": str(_coerce_mapping(run_row.get("run_metadata")).get("pipeline_stage") or run_row["run_type"]),
            "stage_label": _stage_label(str(run_row["run_type"])),
            "stage_status": _fallback_run_stage_status(run_row),
            "execution_count": source_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "execution_status_counts": {
                str(run_row["run_state"]): source_count,
            },
            "started_at": run_row["started_at"].isoformat() if run_row.get("started_at") else None,
            "completed_at": run_row["completed_at"].isoformat() if run_row.get("completed_at") else None,
        }
    ]


def _build_error_events(*, run_row: dict[str, Any], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if run_row.get("error_summary"):
        events.append(
            {
                "scope": "run",
                "severity": "error" if str(run_row["run_state"]) == "failed" else "warning",
                "summary": str(run_row["error_summary"]),
                "source_document_id": None,
                "source_id": None,
                "stage_status": str(run_row["run_state"]),
                "warning_count": 0,
                "error_count": int(run_row.get("source_failure_count") or 0),
                "runtime_notes": [],
                "source_url": None,
            }
        )

    for row in source_rows:
        has_issue = bool(row["error_summary"]) or row["error_count"] > 0 or row["warning_count"] > 0 or row["stage_status"] != "completed"
        if not has_issue:
            continue
        severity = "error" if row["error_count"] > 0 or row["stage_status"] == "failed" else "warning"
        summary = row["error_summary"] or ("Completed with warnings." if row["warning_count"] > 0 else f"Stage status: {row['stage_status']}.")
        events.append(
            {
                "scope": "source",
                "severity": severity,
                "summary": summary,
                "source_document_id": row["source_document_id"],
                "source_id": row["source_id"],
                "stage_status": row["stage_status"],
                "warning_count": row["warning_count"],
                "error_count": row["error_count"],
                "runtime_notes": row["runtime_notes"],
                "source_url": row["source_url"],
            }
        )

    events.sort(
        key=lambda item: (
            0 if item["severity"] == "error" else 1,
            -int(item["error_count"]),
            -int(item["warning_count"]),
            item["source_id"] or "",
        )
    )
    return events


def _build_usage_summary(*, usage_rows: list[dict[str, Any]], model_execution_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "usage_record_count": len(usage_rows),
        "model_execution_count": len(model_execution_rows),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "by_stage": [],
    }
    if not usage_rows:
        return summary

    by_stage: dict[str, dict[str, Any]] = {}
    for row in usage_rows:
        prompt_tokens = int(row.get("prompt_tokens") or 0)
        completion_tokens = int(row.get("completion_tokens") or 0)
        estimated_cost = _serialize_decimal(row.get("estimated_cost")) or 0.0
        stage_name = str(row.get("stage_name") or "unknown")
        bucket = by_stage.setdefault(
            stage_name,
            {
                "stage_name": stage_name,
                "stage_label": _stage_label(stage_name),
                "usage_record_count": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
            },
        )
        bucket["usage_record_count"] += 1
        bucket["prompt_tokens"] += prompt_tokens
        bucket["completion_tokens"] += completion_tokens
        bucket["total_tokens"] += prompt_tokens + completion_tokens
        bucket["estimated_cost"] += estimated_cost
        summary["prompt_tokens"] += prompt_tokens
        summary["completion_tokens"] += completion_tokens
        summary["total_tokens"] += prompt_tokens + completion_tokens
        summary["estimated_cost"] += estimated_cost

    summary["by_stage"] = list(by_stage.values())
    return summary


def _resolve_stage_status(*, status_counts: dict[str, int], partial_completion_flag: bool) -> str:
    if status_counts.get("failed"):
        return "failed"
    if status_counts.get("started"):
        return "started"
    if partial_completion_flag:
        return "degraded"
    if status_counts.get("completed"):
        return "completed"
    if status_counts.get("retried"):
        return "retried"
    return "unknown"


def _fallback_run_stage_status(run_row: dict[str, Any]) -> str:
    run_state = str(run_row["run_state"])
    if run_state == "completed" and bool(run_row["partial_completion_flag"]):
        return "degraded"
    return run_state


def _filter_safe_source_metadata(stage_metadata: dict[str, Any]) -> dict[str, Any]:
    safe_metadata: dict[str, Any] = {}
    for key, value in stage_metadata.items():
        if key not in _SAFE_SOURCE_METADATA_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe_metadata[key] = value
            continue
        if isinstance(value, Decimal):
            safe_metadata[key] = float(value)
            continue
        if isinstance(value, list):
            safe_metadata[key] = [item for item in value if isinstance(item, (str, int, float, bool))]
            continue
    return safe_metadata


def _stage_label(value: str) -> str:
    return value.replace("_", " ").title()


def _normalize_search(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _serialize_decimal(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
