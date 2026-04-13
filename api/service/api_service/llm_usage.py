from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from math import ceil
from statistics import mean, pstdev
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection

_PROVIDER_NAME_SQL = "COALESCE(NULLIF(lur.usage_metadata ->> 'provider', ''), 'unknown')"
_MODEL_NAME_SQL = "COALESCE(NULLIF(lur.usage_metadata ->> 'model_id', ''), NULLIF(me.model_id, ''), 'unknown')"


@dataclass(frozen=True)
class LLMUsageFilters:
    recorded_from: datetime | None
    recorded_to: datetime | None
    run_id: str | None
    agent_name: str | None
    model_name: str | None
    provider_name: str | None
    stage: str | None
    search: str | None


def normalize_llm_usage_filters(
    *,
    recorded_from: datetime | None,
    recorded_to: datetime | None,
    run_id: str | None,
    agent_name: str | None,
    model_name: str | None,
    provider_name: str | None,
    stage: str | None,
    search: str | None,
) -> LLMUsageFilters:
    return LLMUsageFilters(
        recorded_from=recorded_from,
        recorded_to=recorded_to,
        run_id=_normalize_text(run_id),
        agent_name=_normalize_text(agent_name).lower() if _normalize_text(agent_name) else None,
        model_name=_normalize_text(model_name).lower() if _normalize_text(model_name) else None,
        provider_name=_normalize_text(provider_name).lower() if _normalize_text(provider_name) else None,
        stage=_normalize_text(stage).lower() if _normalize_text(stage) else None,
        search=_normalize_search(search),
    )


def load_llm_usage_dashboard(connection: Connection, *, filters: LLMUsageFilters) -> dict[str, Any]:
    where_sql, params = _build_where_clause(filters)
    rows = connection.execute(
        f"""
        SELECT
            lur.llm_usage_id,
            lur.recorded_at,
            lur.run_id,
            lur.model_execution_id,
            lur.candidate_id,
            lur.provider_request_id,
            lur.prompt_tokens,
            lur.completion_tokens,
            lur.estimated_cost,
            COALESCE(lur.usage_metadata, '{{}}'::jsonb) AS usage_metadata,
            me.stage_name,
            me.agent_name,
            {_PROVIDER_NAME_SQL} AS provider_name,
            {_MODEL_NAME_SQL} AS model_name,
            me.execution_status,
            me.started_at AS model_started_at,
            me.completed_at AS model_completed_at,
            ir.run_state,
            ir.trigger_type,
            COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), NULLIF(me.stage_name, '')) AS run_stage,
            COALESCE(ir.run_metadata ->> 'correlation_id', '') AS correlation_id,
            COALESCE(ir.run_metadata ->> 'request_id', '') AS request_id,
            nc.product_name,
            nc.bank_code,
            nc.product_type,
            nc.validation_status,
            rt.review_task_id,
            rt.review_state,
            rt.queue_reason_code
        FROM llm_usage_record AS lur
        LEFT JOIN model_execution AS me
          ON me.model_execution_id = lur.model_execution_id
        LEFT JOIN ingestion_run AS ir
          ON ir.run_id = lur.run_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = lur.candidate_id
        LEFT JOIN review_task AS rt
          ON rt.candidate_id = lur.candidate_id
        WHERE {where_sql}
        ORDER BY lur.recorded_at ASC, lur.llm_usage_id ASC
        """,
        params,
    ).fetchall()

    totals = _build_totals(rows)
    by_model = _build_by_model(rows)
    by_agent = _build_by_agent(rows)
    by_run = _build_by_run(rows)
    usage_trend = _build_usage_trend(rows)
    anomaly_candidates = _build_anomaly_candidates(rows)
    _apply_share_metrics(by_model, totals=totals)
    _apply_share_metrics(by_agent, totals=totals)
    _apply_share_metrics(by_run, totals=totals)

    return {
        "totals": {
            **totals,
            "anomaly_candidate_count": len(anomaly_candidates),
        },
        "by_model": by_model,
        "by_agent": by_agent,
        "by_run": by_run,
        "trend": usage_trend,
        "usage_trend": usage_trend,
        "anomaly_candidates": anomaly_candidates,
        "applied_filters": {
            "from": filters.recorded_from.isoformat() if filters.recorded_from else None,
            "to": filters.recorded_to.isoformat() if filters.recorded_to else None,
            "run_id": filters.run_id,
            "agent_name": filters.agent_name,
            "model_name": filters.model_name,
            "provider_name": filters.provider_name,
            "stage": filters.stage,
            "search": filters.search,
        },
    }


def _build_where_clause(filters: LLMUsageFilters) -> tuple[str, dict[str, Any]]:
    clauses = ["1 = 1"]
    params: dict[str, Any] = {}

    if filters.recorded_from:
        clauses.append("lur.recorded_at >= %(recorded_from)s")
        params["recorded_from"] = filters.recorded_from
    if filters.recorded_to:
        clauses.append("lur.recorded_at <= %(recorded_to)s")
        params["recorded_to"] = filters.recorded_to
    if filters.run_id:
        clauses.append("lur.run_id = %(run_id)s")
        params["run_id"] = filters.run_id
    if filters.agent_name:
        clauses.append("LOWER(COALESCE(NULLIF(me.agent_name, ''), '')) = %(agent_name)s")
        params["agent_name"] = filters.agent_name
    if filters.model_name:
        clauses.append(f"LOWER({_MODEL_NAME_SQL}) = %(model_name)s")
        params["model_name"] = filters.model_name
    if filters.provider_name:
        clauses.append(f"LOWER({_PROVIDER_NAME_SQL}) = %(provider_name)s")
        params["provider_name"] = filters.provider_name
    if filters.stage:
        clauses.append(
            "LOWER(COALESCE(NULLIF(me.stage_name, ''), NULLIF(ir.run_metadata ->> 'pipeline_stage', ''))) = %(stage)s"
        )
        params["stage"] = filters.stage
    if filters.search:
        clauses.append(
            """
            (
                lur.llm_usage_id ILIKE %(search)s
                OR lur.run_id ILIKE %(search)s
                OR COALESCE(lur.model_execution_id, '') ILIKE %(search)s
                OR COALESCE(lur.candidate_id, '') ILIKE %(search)s
                OR COALESCE(lur.provider_request_id, '') ILIKE %(search)s
                OR COALESCE(me.stage_name, '') ILIKE %(search)s
                OR COALESCE(me.agent_name, '') ILIKE %(search)s
                OR {_PROVIDER_NAME_SQL} ILIKE %(search)s
                OR {_MODEL_NAME_SQL} ILIKE %(search)s
                OR COALESCE(ir.run_metadata ->> 'pipeline_stage', '') ILIKE %(search)s
                OR COALESCE(ir.run_metadata ->> 'correlation_id', '') ILIKE %(search)s
                OR COALESCE(ir.run_metadata ->> 'request_id', '') ILIKE %(search)s
                OR COALESCE(nc.product_name, '') ILIKE %(search)s
                OR COALESCE(nc.bank_code, '') ILIKE %(search)s
                OR COALESCE(rt.review_task_id, '') ILIKE %(search)s
                OR COALESCE(rt.queue_reason_code, '') ILIKE %(search)s
                OR COALESCE(lur.usage_metadata::text, '') ILIKE %(search)s
            )
            """
        )
        params["search"] = f"%{filters.search}%"

    return " AND ".join(clause.strip() for clause in clauses), params


def _build_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_ids = {str(row["run_id"]) for row in rows if row.get("run_id")}
    model_execution_ids = {str(row["model_execution_id"]) for row in rows if row.get("model_execution_id")}
    candidate_ids = {str(row["candidate_id"]) for row in rows if row.get("candidate_id")}
    agent_names = {str(row["agent_name"]) for row in rows if _string_or_none(row.get("agent_name"))}
    model_keys = {
        (str(row["provider_name"]), str(row["model_name"]))
        for row in rows
        if _string_or_none(row.get("provider_name")) and _string_or_none(row.get("model_name"))
    }

    prompt_tokens = 0
    completion_tokens = 0
    estimated_cost = Decimal("0")
    first_recorded_at: datetime | None = None
    last_recorded_at: datetime | None = None
    for row in rows:
        prompt_tokens += int(row.get("prompt_tokens") or 0)
        completion_tokens += int(row.get("completion_tokens") or 0)
        estimated_cost += _as_decimal(row.get("estimated_cost"))
        recorded_at = row.get("recorded_at")
        if isinstance(recorded_at, datetime):
            if first_recorded_at is None or recorded_at < first_recorded_at:
                first_recorded_at = recorded_at
            if last_recorded_at is None or recorded_at > last_recorded_at:
                last_recorded_at = recorded_at

    total_tokens = prompt_tokens + completion_tokens
    average_tokens_per_record = round(total_tokens / len(rows), 2) if rows else 0.0
    average_cost_per_record = round((_serialize_decimal(estimated_cost) or 0.0) / len(rows), 6) if rows else 0.0
    estimated_cost_per_1k_tokens = (
        round(((_serialize_decimal(estimated_cost) or 0.0) / total_tokens) * 1000, 6) if total_tokens else 0.0
    )
    return {
        "usage_record_count": len(rows),
        "run_count": len(run_ids),
        "model_execution_count": len(model_execution_ids),
        "candidate_count": len(candidate_ids),
        "agent_count": len(agent_names),
        "model_count": len(model_keys),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": _serialize_decimal(estimated_cost) or 0.0,
        "average_tokens_per_record": average_tokens_per_record,
        "average_cost_per_record": average_cost_per_record,
        "estimated_cost_per_1k_tokens": estimated_cost_per_1k_tokens,
        "first_recorded_at": first_recorded_at.isoformat() if first_recorded_at else None,
        "last_recorded_at": last_recorded_at.isoformat() if last_recorded_at else None,
        "zero_token_records": sum(1 for row in rows if _record_total_tokens(row) == 0),
    }


def _build_by_model(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        provider_name = _normalize_label(row.get("provider_name"))
        model_name = _normalize_label(row.get("model_name"))
        bucket = buckets.setdefault(
            (provider_name, model_name),
            {
                "provider_name": provider_name,
                "model_name": model_name,
                "usage_record_count": 0,
                "model_execution_ids": set(),
                "run_ids": set(),
                "candidate_ids": set(),
                "agent_names": set(),
                "stage_names": set(),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": Decimal("0"),
                "first_recorded_at": None,
                "last_recorded_at": None,
            },
        )
        _update_bucket(bucket, row)

    results = [_finalize_bucket(bucket, include_run_count=True, include_candidate_count=True) for bucket in buckets.values()]
    results.sort(
        key=lambda item: (
            -int(item["total_tokens"]),
            -int(item["usage_record_count"]),
            item["provider_name"],
            item["model_name"],
        )
    )
    return results


def _build_by_agent(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        agent_name = _normalize_label(row.get("agent_name"))
        bucket = buckets.setdefault(
            agent_name,
            {
                "agent_name": agent_name,
                "usage_record_count": 0,
                "model_execution_ids": set(),
                "run_ids": set(),
                "candidate_ids": set(),
                "provider_names": set(),
                "model_names": set(),
                "stage_names": set(),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": Decimal("0"),
                "first_recorded_at": None,
                "last_recorded_at": None,
            },
        )
        _update_bucket(bucket, row)

    results = [_finalize_bucket(bucket, include_run_count=True, include_candidate_count=True) for bucket in buckets.values()]
    results.sort(
        key=lambda item: (
            -int(item["total_tokens"]),
            -int(item["usage_record_count"]),
            item["agent_name"],
        )
    )
    return results


def _build_by_run(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        run_id = _normalize_label(row.get("run_id"))
        bucket = buckets.setdefault(
            run_id,
            {
                "run_id": run_id,
                "run_type": _normalize_label(row.get("run_stage")),
                "run_state": _normalize_label(row.get("run_state")),
                "trigger_type": _normalize_label(row.get("trigger_type")),
                "correlation_id": _string_or_none(row.get("correlation_id")),
                "request_id": _string_or_none(row.get("request_id")),
                "usage_record_count": 0,
                "model_execution_ids": set(),
                "candidate_ids": set(),
                "provider_names": set(),
                "model_names": set(),
                "agent_names": set(),
                "stage_names": set(),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": Decimal("0"),
                "first_recorded_at": None,
                "last_recorded_at": None,
            },
        )
        _update_bucket(bucket, row)

    runs = []
    for bucket in buckets.values():
        runs.append(
            {
                "run_id": bucket["run_id"],
                "run_type": bucket["run_type"],
                "run_state": bucket["run_state"],
                "trigger_type": bucket["trigger_type"],
                "correlation_id": bucket["correlation_id"],
                "request_id": bucket["request_id"],
                "usage_record_count": bucket["usage_record_count"],
                "model_execution_count": len(bucket["model_execution_ids"]),
                "candidate_count": len(bucket["candidate_ids"]),
                "provider_names": sorted(bucket["provider_names"]),
                "model_names": sorted(bucket["model_names"]),
                "agent_names": sorted(bucket["agent_names"]),
                "provider_name": _summarize_scope_names(bucket["provider_names"]),
                "model_name": _summarize_scope_names(bucket["model_names"]),
                "agent_name": _summarize_scope_names(bucket["agent_names"]),
                "stage_names": sorted(bucket["stage_names"]),
                "prompt_tokens": bucket["prompt_tokens"],
                "completion_tokens": bucket["completion_tokens"],
                "total_tokens": bucket["total_tokens"],
                "estimated_cost": _serialize_decimal(bucket["estimated_cost"]) or 0.0,
                "first_recorded_at": bucket["first_recorded_at"].isoformat() if bucket["first_recorded_at"] else None,
                "last_recorded_at": bucket["last_recorded_at"].isoformat() if bucket["last_recorded_at"] else None,
            }
        )

    runs.sort(key=lambda item: (item["last_recorded_at"] or "", item["run_id"]), reverse=True)
    return runs


def _build_usage_trend(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[date, dict[str, Any]] = {}
    for row in rows:
        recorded_at = row.get("recorded_at")
        if not isinstance(recorded_at, datetime):
            continue
        bucket_date = recorded_at.date()
        bucket = buckets.setdefault(
            bucket_date,
            {
                "bucket_date": bucket_date.isoformat(),
                "usage_record_count": 0,
                "run_ids": set(),
                "candidate_ids": set(),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": Decimal("0"),
            },
        )
        bucket["usage_record_count"] += 1
        if row.get("run_id"):
            bucket["run_ids"].add(str(row["run_id"]))
        if row.get("candidate_id"):
            bucket["candidate_ids"].add(str(row["candidate_id"]))
        bucket["prompt_tokens"] += int(row.get("prompt_tokens") or 0)
        bucket["completion_tokens"] += int(row.get("completion_tokens") or 0)
        bucket["total_tokens"] += _record_total_tokens(row)
        bucket["estimated_cost"] += _as_decimal(row.get("estimated_cost"))

    trend = []
    previous_total_tokens: int | None = None
    previous_estimated_cost: float | None = None
    for bucket in sorted(buckets.values(), key=lambda item: item["bucket_date"]):
        estimated_cost = _serialize_decimal(bucket["estimated_cost"]) or 0.0
        total_tokens = bucket["total_tokens"]
        token_delta = total_tokens - previous_total_tokens if previous_total_tokens is not None else None
        cost_delta = (
            round(estimated_cost - previous_estimated_cost, 6) if previous_estimated_cost is not None else None
        )
        token_delta_percent = _percent_change(previous_total_tokens, total_tokens)
        cost_delta_percent = _percent_change(previous_estimated_cost, estimated_cost)
        trend_state, trend_summary = _classify_trend_bucket(
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            previous_total_tokens=previous_total_tokens,
            previous_estimated_cost=previous_estimated_cost,
            token_delta_percent=token_delta_percent,
            cost_delta_percent=cost_delta_percent,
        )
        trend.append(
            {
                "bucket_date": bucket["bucket_date"],
                "period": bucket["bucket_date"],
                "interval_start": bucket["bucket_date"],
                "usage_record_count": bucket["usage_record_count"],
                "run_count": len(bucket["run_ids"]),
                "candidate_count": len(bucket["candidate_ids"]),
                "prompt_tokens": bucket["prompt_tokens"],
                "completion_tokens": bucket["completion_tokens"],
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost,
                "average_tokens_per_record": (
                    round(total_tokens / bucket["usage_record_count"], 2) if bucket["usage_record_count"] else 0.0
                ),
                "average_cost_per_record": (
                    round(estimated_cost / bucket["usage_record_count"], 6) if bucket["usage_record_count"] else 0.0
                ),
                "token_delta": token_delta,
                "cost_delta": cost_delta,
                "token_delta_percent": token_delta_percent,
                "cost_delta_percent": cost_delta_percent,
                "trend_state": trend_state,
                "summary": trend_summary,
            }
        )
        previous_total_tokens = total_tokens
        previous_estimated_cost = estimated_cost
    return trend


def _build_anomaly_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []

    token_values = [_record_total_tokens(row) for row in rows]
    cost_values = [_serialize_decimal(row.get("estimated_cost")) or 0.0 for row in rows]
    token_threshold = max(1000, int(ceil(mean(token_values) + pstdev(token_values))) if len(token_values) > 1 else max(token_values))
    cost_threshold = max(0.25, (mean(cost_values) + pstdev(cost_values)) if len(cost_values) > 1 else max(cost_values))

    anomalies: list[dict[str, Any]] = []
    for row in rows:
        total_tokens = _record_total_tokens(row)
        estimated_cost = _serialize_decimal(row.get("estimated_cost")) or 0.0
        reasons: list[str] = []
        score = 0

        if total_tokens > 0 and total_tokens >= token_threshold:
            reasons.append("high_token_usage")
            score += 5
        if estimated_cost > 0 and estimated_cost >= cost_threshold:
            reasons.append("high_cost_usage")
            score += 5
        if total_tokens == 0 and estimated_cost > 0:
            reasons.append("cost_without_tokens")
            score += 6
        if not _string_or_none(row.get("provider_name")) or not _string_or_none(row.get("model_name")) or not _string_or_none(row.get("agent_name")):
            reasons.append("missing_model_context")
            score += 3
        if str(row.get("run_state") or "").lower() in {"failed", "retried"} and total_tokens > 0:
            reasons.append("failed_run_context")
            score += 2
        if _string_or_none(row.get("candidate_id")) and str(row.get("validation_status") or "").lower() in {"warning", "error"}:
            reasons.append("candidate_review_context")
            score += 2

        if not reasons:
            continue

        anomalies.append(
            {
                "llm_usage_id": str(row["llm_usage_id"]),
                "recorded_at": row["recorded_at"].isoformat() if row.get("recorded_at") else None,
                "run_id": str(row["run_id"]),
                "model_execution_id": _string_or_none(row.get("model_execution_id")),
                "candidate_id": _string_or_none(row.get("candidate_id")),
                "provider_name": _normalize_label(row.get("provider_name")),
                "agent_name": _normalize_label(row.get("agent_name")),
                "model_name": _normalize_label(row.get("model_name")),
                "stage_name": _normalize_label(row.get("stage_name") or row.get("run_stage")),
                "run_type": _normalize_label(row.get("run_stage")),
                "run_state": _normalize_label(row.get("run_state")),
                "trigger_type": _normalize_label(row.get("trigger_type")),
                "prompt_tokens": int(row.get("prompt_tokens") or 0),
                "completion_tokens": int(row.get("completion_tokens") or 0),
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost,
                "anomaly_score": score,
                "signal": _anomaly_signal(score),
                "summary": _summarize_anomaly_reasons(reasons),
                "anomaly_reasons": reasons,
                "baseline_total_tokens": token_threshold,
                "baseline_cost": round(cost_threshold, 6),
                "correlation_id": _string_or_none(row.get("correlation_id")),
                "request_id": _string_or_none(row.get("request_id")),
                "provider_request_id": _string_or_none(row.get("provider_request_id")),
                "product_name": _string_or_none(row.get("product_name")),
                "bank_code": _string_or_none(row.get("bank_code")),
                "product_type": _string_or_none(row.get("product_type")),
                "validation_status": _string_or_none(row.get("validation_status")),
                "review_task_id": _string_or_none(row.get("review_task_id")),
                "review_state": _string_or_none(row.get("review_state")),
                "queue_reason_code": _string_or_none(row.get("queue_reason_code")),
            }
        )

    anomalies.sort(
        key=lambda item: (
            -int(item["anomaly_score"]),
            -int(item["total_tokens"]),
            -float(item["estimated_cost"]),
            item["recorded_at"] or "",
            item["llm_usage_id"],
        )
    )
    if anomalies:
        return anomalies[:20]

    fallback = sorted(rows, key=lambda row: (_record_total_tokens(row), _serialize_decimal(row.get("estimated_cost")) or 0.0), reverse=True)
    return [
        {
            "llm_usage_id": str(row["llm_usage_id"]),
            "recorded_at": row["recorded_at"].isoformat() if row.get("recorded_at") else None,
            "run_id": str(row["run_id"]),
            "model_execution_id": _string_or_none(row.get("model_execution_id")),
            "candidate_id": _string_or_none(row.get("candidate_id")),
            "provider_name": _normalize_label(row.get("provider_name")),
            "agent_name": _normalize_label(row.get("agent_name")),
            "model_name": _normalize_label(row.get("model_name")),
            "stage_name": _normalize_label(row.get("stage_name") or row.get("run_stage")),
            "run_type": _normalize_label(row.get("run_stage")),
            "run_state": _normalize_label(row.get("run_state")),
            "trigger_type": _normalize_label(row.get("trigger_type")),
            "prompt_tokens": int(row.get("prompt_tokens") or 0),
            "completion_tokens": int(row.get("completion_tokens") or 0),
            "total_tokens": _record_total_tokens(row),
            "estimated_cost": _serialize_decimal(row.get("estimated_cost")) or 0.0,
            "anomaly_score": 1,
            "signal": "info",
            "summary": "Highest usage row in the current scope.",
            "anomaly_reasons": ["highest_usage_in_scope"],
            "baseline_total_tokens": token_threshold,
            "baseline_cost": round(cost_threshold, 6),
            "correlation_id": _string_or_none(row.get("correlation_id")),
            "request_id": _string_or_none(row.get("request_id")),
            "provider_request_id": _string_or_none(row.get("provider_request_id")),
            "product_name": _string_or_none(row.get("product_name")),
            "bank_code": _string_or_none(row.get("bank_code")),
            "product_type": _string_or_none(row.get("product_type")),
            "validation_status": _string_or_none(row.get("validation_status")),
            "review_task_id": _string_or_none(row.get("review_task_id")),
            "review_state": _string_or_none(row.get("review_state")),
            "queue_reason_code": _string_or_none(row.get("queue_reason_code")),
        }
        for row in fallback[:5]
    ]


def _update_bucket(bucket: dict[str, Any], row: dict[str, Any]) -> None:
    bucket["usage_record_count"] += 1
    bucket["prompt_tokens"] += int(row.get("prompt_tokens") or 0)
    bucket["completion_tokens"] += int(row.get("completion_tokens") or 0)
    bucket["total_tokens"] += _record_total_tokens(row)
    bucket["estimated_cost"] += _as_decimal(row.get("estimated_cost"))
    recorded_at = row.get("recorded_at")
    if isinstance(recorded_at, datetime):
        if bucket["first_recorded_at"] is None or recorded_at < bucket["first_recorded_at"]:
            bucket["first_recorded_at"] = recorded_at
        if bucket["last_recorded_at"] is None or recorded_at > bucket["last_recorded_at"]:
            bucket["last_recorded_at"] = recorded_at
    if row.get("run_id") and "run_ids" in bucket:
        bucket["run_ids"].add(str(row["run_id"]))
    if row.get("model_execution_id") and "model_execution_ids" in bucket:
        bucket["model_execution_ids"].add(str(row["model_execution_id"]))
    if row.get("candidate_id") and "candidate_ids" in bucket:
        bucket["candidate_ids"].add(str(row["candidate_id"]))
    if _string_or_none(row.get("provider_name")) and "provider_names" in bucket:
        bucket["provider_names"].add(_normalize_label(row.get("provider_name")))
    if _string_or_none(row.get("model_name")) and "model_names" in bucket:
        bucket["model_names"].add(_normalize_label(row.get("model_name")))
    if _string_or_none(row.get("agent_name")) and "agent_names" in bucket:
        bucket["agent_names"].add(_normalize_label(row.get("agent_name")))
    stage_name = _normalize_label(row.get("stage_name") or row.get("run_stage"))
    if stage_name:
        bucket["stage_names"].add(stage_name)


def _finalize_bucket(
    bucket: dict[str, Any],
    *,
    include_run_count: bool,
    include_candidate_count: bool,
) -> dict[str, Any]:
    payload = {
        key: value
        for key, value in bucket.items()
        if key
        not in {
            "run_ids",
            "candidate_ids",
            "provider_names",
            "model_names",
            "agent_names",
            "stage_names",
            "model_execution_ids",
            "first_recorded_at",
            "last_recorded_at",
            "estimated_cost",
        }
    }
    payload["prompt_tokens"] = bucket["prompt_tokens"]
    payload["completion_tokens"] = bucket["completion_tokens"]
    payload["total_tokens"] = bucket["total_tokens"]
    payload["estimated_cost"] = _serialize_decimal(bucket["estimated_cost"]) or 0.0
    payload["average_tokens"] = (
        round(bucket["total_tokens"] / bucket["usage_record_count"], 2) if bucket["usage_record_count"] else 0.0
    )
    payload["average_cost"] = (
        round((_serialize_decimal(bucket["estimated_cost"]) or 0.0) / bucket["usage_record_count"], 6)
        if bucket["usage_record_count"]
        else 0.0
    )
    payload["first_recorded_at"] = bucket["first_recorded_at"].isoformat() if bucket["first_recorded_at"] else None
    payload["last_recorded_at"] = bucket["last_recorded_at"].isoformat() if bucket["last_recorded_at"] else None
    payload["last_seen_at"] = payload["last_recorded_at"]
    payload["stage_names"] = sorted(bucket["stage_names"])
    if "provider_names" in bucket:
        payload["provider_names"] = sorted(bucket["provider_names"])
    if "model_names" in bucket:
        payload["model_names"] = sorted(bucket["model_names"])
    if "agent_names" in bucket:
        payload["agent_names"] = sorted(bucket["agent_names"])
    if include_run_count:
        payload["run_count"] = len(bucket["run_ids"])
    if include_candidate_count:
        payload["candidate_count"] = len(bucket["candidate_ids"])
    if "model_execution_ids" in bucket:
        payload["model_execution_count"] = len(bucket["model_execution_ids"])
    return payload


def _apply_share_metrics(items: list[dict[str, Any]], *, totals: dict[str, Any]) -> None:
    total_tokens = int(totals.get("total_tokens") or 0)
    total_cost = float(totals.get("estimated_cost") or 0.0)
    for item in items:
        item_tokens = int(item.get("total_tokens") or 0)
        item_cost = float(item.get("estimated_cost") or 0.0)
        item["token_share_percent"] = round((item_tokens / total_tokens) * 100, 2) if total_tokens else 0.0
        item["cost_share_percent"] = round((item_cost / total_cost) * 100, 2) if total_cost else 0.0


def _record_total_tokens(row: dict[str, Any]) -> int:
    return int(row.get("prompt_tokens") or 0) + int(row.get("completion_tokens") or 0)


def _percent_change(previous: int | float | None, current: int | float) -> float | None:
    if previous is None:
        return None
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def _classify_trend_bucket(
    *,
    total_tokens: int,
    estimated_cost: float,
    previous_total_tokens: int | None,
    previous_estimated_cost: float | None,
    token_delta_percent: float | None,
    cost_delta_percent: float | None,
) -> tuple[str, str]:
    if previous_total_tokens is None or previous_estimated_cost is None:
        return "baseline", "First bucket in the selected window."
    if total_tokens == 0 and estimated_cost == 0:
        return "idle", "No token or cost activity was recorded in this bucket."
    largest_positive_delta = max(token_delta_percent or 0.0, cost_delta_percent or 0.0)
    largest_negative_delta = min(token_delta_percent or 0.0, cost_delta_percent or 0.0)
    if largest_positive_delta >= 50:
        return "spike", _build_trend_summary(
            token_delta_percent=token_delta_percent,
            cost_delta_percent=cost_delta_percent,
            prefix="Usage spiked versus the previous bucket",
        )
    if largest_positive_delta >= 20:
        return "elevated", _build_trend_summary(
            token_delta_percent=token_delta_percent,
            cost_delta_percent=cost_delta_percent,
            prefix="Usage is elevated versus the previous bucket",
        )
    if largest_negative_delta <= -20:
        return "down", _build_trend_summary(
            token_delta_percent=token_delta_percent,
            cost_delta_percent=cost_delta_percent,
            prefix="Usage cooled versus the previous bucket",
        )
    return "stable", _build_trend_summary(
        token_delta_percent=token_delta_percent,
        cost_delta_percent=cost_delta_percent,
        prefix="Usage stayed within the normal day-to-day range",
    )


def _build_trend_summary(
    *,
    token_delta_percent: float | None,
    cost_delta_percent: float | None,
    prefix: str,
) -> str:
    parts: list[str] = []
    if token_delta_percent is not None:
        parts.append(f"tokens {_format_signed_percent(token_delta_percent)}")
    if cost_delta_percent is not None:
        parts.append(f"cost {_format_signed_percent(cost_delta_percent)}")
    if not parts:
        return prefix + "."
    return f"{prefix}: {', '.join(parts)}."


def _format_signed_percent(value: float) -> str:
    return f"{value:+.2f}%"


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _serialize_decimal(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(Decimal(str(value)))


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split()).strip()
    return text or None


def _normalize_search(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    return normalized if normalized else None


def _normalize_label(value: Any) -> str:
    normalized = _string_or_none(value)
    return normalized if normalized else "unknown"


def _summarize_scope_names(values: set[str]) -> str:
    if not values:
        return "unknown"
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    return f"{ordered[0]} +{len(ordered) - 1}"


def _summarize_anomaly_reasons(reasons: list[str]) -> str:
    return ", ".join(reason.replace("_", " ") for reason in reasons)


def _anomaly_signal(score: int) -> str:
    if score >= 10:
        return "critical"
    if score >= 5:
        return "warning"
    return "info"


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)
