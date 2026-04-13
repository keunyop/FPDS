from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection

REVIEW_STATES = ("queued", "approved", "rejected", "edited", "deferred")
DEFAULT_REVIEW_STATES = ("queued", "deferred")
VALIDATION_STATES = ("pass", "warning", "error")


@dataclass(frozen=True)
class ReviewQueueFilters:
    states: tuple[str, ...]
    bank_code: str | None
    product_type: str | None
    validation_status: str | None
    created_from: datetime | None
    created_to: datetime | None
    search: str | None
    sort_by: str
    sort_order: str
    page: int
    page_size: int


def normalize_review_queue_filters(
    *,
    states: Iterable[str] | None,
    bank_code: str | None,
    product_type: str | None,
    validation_status: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> ReviewQueueFilters:
    normalized_states = tuple(dict.fromkeys(state.strip().lower() for state in (states or DEFAULT_REVIEW_STATES) if state.strip()))
    if not normalized_states:
        normalized_states = DEFAULT_REVIEW_STATES

    normalized_validation_status = validation_status.strip().lower() if validation_status else None
    if normalized_validation_status not in {*VALIDATION_STATES, None}:
        normalized_validation_status = None

    return ReviewQueueFilters(
        states=normalized_states,
        bank_code=bank_code.strip().upper() if bank_code and bank_code.strip() else None,
        product_type=product_type.strip().lower() if product_type and product_type.strip() else None,
        validation_status=normalized_validation_status,
        created_from=created_from,
        created_to=created_to,
        search=_normalize_search(search),
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


def load_review_queue(
    connection: Connection,
    *,
    filters: ReviewQueueFilters,
) -> dict[str, Any]:
    from_clause = """
    FROM review_task AS rt
    JOIN normalized_candidate AS nc
      ON nc.candidate_id = rt.candidate_id
    LEFT JOIN bank AS b
      ON b.bank_code = nc.bank_code
    """
    where_sql, params = _build_where_clause(filters)

    total_row = connection.execute(
        f"""
        SELECT COUNT(*) AS total_items
        {from_clause}
        WHERE {where_sql}
        """,
        params,
    ).fetchone()
    total_items = int(total_row["total_items"]) if total_row else 0

    state_rows = connection.execute(
        f"""
        SELECT rt.review_state, COUNT(*) AS item_count
        {from_clause}
        WHERE {where_sql}
        GROUP BY rt.review_state
        """,
        params,
    ).fetchall()
    validation_rows = connection.execute(
        f"""
        SELECT nc.validation_status, COUNT(*) AS item_count
        {from_clause}
        WHERE {where_sql}
        GROUP BY nc.validation_status
        """,
        params,
    ).fetchall()

    item_rows = connection.execute(
        f"""
        SELECT
            rt.review_task_id,
            rt.candidate_id,
            rt.run_id,
            nc.country_code,
            nc.bank_code,
            COALESCE(b.bank_name, nc.bank_code) AS bank_name,
            nc.product_type,
            nc.product_name,
            rt.review_state,
            nc.candidate_state,
            nc.validation_status,
            nc.validation_issue_codes,
            nc.source_confidence,
            rt.queue_reason_code,
            rt.issue_summary,
            rt.created_at,
            rt.updated_at
        {from_clause}
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

    items = [_serialize_review_task_row(row) for row in item_rows]
    state_counts = {state: 0 for state in REVIEW_STATES}
    for row in state_rows:
        state_counts[str(row["review_state"])] = int(row["item_count"])

    validation_counts = {status: 0 for status in VALIDATION_STATES}
    for row in validation_rows:
        validation_counts[str(row["validation_status"])] = int(row["item_count"])

    total_pages = (total_items + filters.page_size - 1) // filters.page_size if total_items else 0
    return {
        "items": items,
        "summary": {
            "total_items": total_items,
            "active_items": state_counts["queued"] + state_counts["deferred"],
            "state_counts": state_counts,
            "validation_counts": validation_counts,
        },
        "applied_filters": {
            "states": list(filters.states),
            "bank_code": filters.bank_code,
            "product_type": filters.product_type,
            "validation_status": filters.validation_status,
            "created_from": filters.created_from.isoformat() if filters.created_from else None,
            "created_to": filters.created_to.isoformat() if filters.created_to else None,
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


def _build_where_clause(filters: ReviewQueueFilters) -> tuple[str, dict[str, Any]]:
    clauses = ["rt.review_state = ANY(%(states)s)"]
    params: dict[str, Any] = {"states": list(filters.states)}

    if filters.bank_code:
        clauses.append("nc.bank_code = %(bank_code)s")
        params["bank_code"] = filters.bank_code
    if filters.product_type:
        clauses.append("nc.product_type = %(product_type)s")
        params["product_type"] = filters.product_type
    if filters.validation_status:
        clauses.append("nc.validation_status = %(validation_status)s")
        params["validation_status"] = filters.validation_status
    if filters.created_from:
        clauses.append("rt.created_at >= %(created_from)s")
        params["created_from"] = filters.created_from
    if filters.created_to:
        clauses.append("rt.created_at <= %(created_to)s")
        params["created_to"] = filters.created_to
    if filters.search:
        clauses.append(
            """
            (
                rt.review_task_id ILIKE %(search)s
                OR rt.candidate_id ILIKE %(search)s
                OR rt.run_id ILIKE %(search)s
                OR nc.product_name ILIKE %(search)s
                OR nc.bank_code ILIKE %(search)s
                OR COALESCE(b.bank_name, '') ILIKE %(search)s
            )
            """
        )
        params["search"] = f"%{filters.search}%"

    return " AND ".join(clause.strip() for clause in clauses), params


def _build_order_by_clause(filters: ReviewQueueFilters) -> str:
    direction = "ASC" if filters.sort_order == "asc" else "DESC"
    if filters.sort_by == "created_at":
        return f"rt.created_at {direction}, rt.review_task_id ASC"
    if filters.sort_by == "updated_at":
        return f"rt.updated_at {direction}, rt.review_task_id ASC"
    if filters.sort_by == "source_confidence":
        return f"nc.source_confidence {direction} NULLS LAST, rt.created_at DESC, rt.review_task_id ASC"
    if filters.sort_by == "product_name":
        return f"nc.product_name {direction}, rt.created_at DESC, rt.review_task_id ASC"
    return """
    CASE rt.review_state
        WHEN 'queued' THEN 0
        WHEN 'deferred' THEN 1
        ELSE 2
    END ASC,
    CASE nc.validation_status
        WHEN 'error' THEN 0
        WHEN 'warning' THEN 1
        ELSE 2
    END ASC,
    nc.source_confidence ASC NULLS LAST,
    rt.created_at DESC,
    rt.review_task_id ASC
    """.strip()


def _serialize_review_task_row(row: dict[str, Any]) -> dict[str, Any]:
    issue_items = _coerce_issue_items(row.get("issue_summary"))
    return {
        "review_task_id": str(row["review_task_id"]),
        "candidate_id": str(row["candidate_id"]),
        "run_id": str(row["run_id"]),
        "country_code": str(row["country_code"]),
        "bank_code": str(row["bank_code"]),
        "bank_name": str(row["bank_name"]),
        "product_type": str(row["product_type"]),
        "product_name": str(row["product_name"]),
        "review_state": str(row["review_state"]),
        "candidate_state": str(row["candidate_state"]),
        "validation_status": str(row["validation_status"]),
        "validation_issue_codes": _coerce_string_list(row.get("validation_issue_codes")),
        "source_confidence": _serialize_confidence(row.get("source_confidence")),
        "queue_reason_code": str(row["queue_reason_code"]),
        "issue_summary": _summarize_issue_items(issue_items, fallback_reason=str(row["queue_reason_code"])),
        "issue_summary_items": issue_items,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


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
    return [str(item) for item in value]


def _serialize_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
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


def _normalize_search(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None
