from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection


EVENT_CATEGORIES = ("review", "run", "publish", "auth", "config", "usage")
ACTOR_TYPES = ("system", "user", "service", "scheduler")
_PRODUCT_NAME_SQL = """
COALESCE(
    NULLIF(cp.product_name, ''),
    NULLIF(nc.product_name, ''),
    ''
)
"""
_TARGET_DISPLAY_SQL = f"""
CASE
    WHEN ae.target_type = 'review_task' THEN COALESCE(NULLIF({_PRODUCT_NAME_SQL}, ''), ae.target_id)
    WHEN ae.target_type = 'run' THEN COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), NULLIF(ir.trigger_type, ''), ae.target_id)
    WHEN ae.target_type = 'product' THEN COALESCE(NULLIF(cp.product_name, ''), ae.target_id)
    ELSE ae.target_id
END
"""


@dataclass(frozen=True)
class AuditLogFilters:
    event_category: str | None
    event_type: str | None
    actor_type: str | None
    target_type: str | None
    actor_id: str | None
    target_id: str | None
    run_id: str | None
    review_task_id: str | None
    product_id: str | None
    publish_item_id: str | None
    occurred_from: datetime | None
    occurred_to: datetime | None
    search: str | None
    sort_by: str
    sort_order: str
    page: int
    page_size: int


def normalize_audit_log_filters(
    *,
    event_category: str | None,
    event_type: str | None,
    actor_type: str | None,
    target_type: str | None,
    actor_id: str | None,
    target_id: str | None,
    run_id: str | None,
    review_task_id: str | None,
    product_id: str | None,
    publish_item_id: str | None,
    occurred_from: datetime | None,
    occurred_to: datetime | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> AuditLogFilters:
    normalized_category = _normalize_enum(event_category, EVENT_CATEGORIES)
    normalized_actor_type = _normalize_enum(actor_type, ACTOR_TYPES)
    normalized_sort_by = sort_by.strip().lower() if sort_by else "occurred_at"
    if normalized_sort_by not in {"occurred_at", "event_category", "event_type", "target_type"}:
        normalized_sort_by = "occurred_at"

    return AuditLogFilters(
        event_category=normalized_category,
        event_type=_normalize_text(event_type),
        actor_type=normalized_actor_type,
        target_type=_normalize_text(target_type).lower() if _normalize_text(target_type) else None,
        actor_id=_normalize_text(actor_id),
        target_id=_normalize_text(target_id),
        run_id=_normalize_text(run_id),
        review_task_id=_normalize_text(review_task_id),
        product_id=_normalize_text(product_id),
        publish_item_id=_normalize_text(publish_item_id),
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        search=_normalize_search(search),
        sort_by=normalized_sort_by,
        sort_order="asc" if sort_order == "asc" else "desc",
        page=page,
        page_size=page_size,
    )


def load_audit_log_list(connection: Connection, *, filters: AuditLogFilters) -> dict[str, Any]:
    where_sql, params = _build_where_clause(filters)

    total_row = connection.execute(
        f"""
        SELECT COUNT(*) AS total_items
        FROM audit_event AS ae
        LEFT JOIN user_account AS ua
          ON ua.user_id = ae.actor_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ae.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = COALESCE(ae.candidate_id, rt.candidate_id)
        LEFT JOIN canonical_product AS cp
          ON cp.product_id = ae.product_id
        LEFT JOIN bank AS b
          ON b.bank_code = COALESCE(cp.bank_code, nc.bank_code)
        LEFT JOIN ingestion_run AS ir
          ON ir.run_id = ae.run_id
        WHERE {where_sql}
        """,
        params,
    ).fetchone()
    total_items = int(total_row["total_items"]) if total_row else 0

    category_rows = connection.execute(
        f"""
        SELECT ae.event_category, COUNT(*) AS item_count
        FROM audit_event AS ae
        LEFT JOIN user_account AS ua
          ON ua.user_id = ae.actor_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ae.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = COALESCE(ae.candidate_id, rt.candidate_id)
        LEFT JOIN canonical_product AS cp
          ON cp.product_id = ae.product_id
        LEFT JOIN bank AS b
          ON b.bank_code = COALESCE(cp.bank_code, nc.bank_code)
        LEFT JOIN ingestion_run AS ir
          ON ir.run_id = ae.run_id
        WHERE {where_sql}
        GROUP BY ae.event_category
        """,
        params,
    ).fetchall()

    actor_rows = connection.execute(
        f"""
        SELECT ae.actor_type, COUNT(*) AS item_count
        FROM audit_event AS ae
        LEFT JOIN user_account AS ua
          ON ua.user_id = ae.actor_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ae.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = COALESCE(ae.candidate_id, rt.candidate_id)
        LEFT JOIN canonical_product AS cp
          ON cp.product_id = ae.product_id
        LEFT JOIN bank AS b
          ON b.bank_code = COALESCE(cp.bank_code, nc.bank_code)
        LEFT JOIN ingestion_run AS ir
          ON ir.run_id = ae.run_id
        WHERE {where_sql}
        GROUP BY ae.actor_type
        """,
        params,
    ).fetchall()

    rows = connection.execute(
        f"""
        SELECT
            ae.audit_event_id,
            ae.event_category,
            ae.event_type,
            ae.occurred_at,
            ae.actor_type,
            ae.actor_id,
            ae.actor_role_snapshot,
            ae.target_type,
            ae.target_id,
            {_TARGET_DISPLAY_SQL} AS target_display_name,
            ae.previous_state,
            ae.new_state,
            ae.reason_code,
            ae.reason_text,
            ae.run_id,
            ae.candidate_id,
            ae.review_task_id,
            ae.product_id,
            ae.publish_item_id,
            ae.request_id,
            ae.diff_summary,
            ae.source_ref,
            ae.ip_address,
            ae.user_agent,
            ae.retention_class,
            COALESCE(ae.event_payload, '{{}}'::jsonb) AS event_payload,
            ua.display_name AS actor_display_name,
            ua.email AS actor_email,
            ua.role AS actor_current_role,
            COALESCE(NULLIF(cp.bank_code, ''), NULLIF(nc.bank_code, '')) AS bank_code,
            COALESCE(NULLIF(b.bank_name, ''), NULLIF(cp.bank_code, ''), NULLIF(nc.bank_code, '')) AS bank_name,
            NULLIF({_PRODUCT_NAME_SQL}, '') AS product_name,
            COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), NULLIF(ir.trigger_type, '')) AS run_type,
            ir.run_state
        FROM audit_event AS ae
        LEFT JOIN user_account AS ua
          ON ua.user_id = ae.actor_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ae.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = COALESCE(ae.candidate_id, rt.candidate_id)
        LEFT JOIN canonical_product AS cp
          ON cp.product_id = ae.product_id
        LEFT JOIN bank AS b
          ON b.bank_code = COALESCE(cp.bank_code, nc.bank_code)
        LEFT JOIN ingestion_run AS ir
          ON ir.run_id = ae.run_id
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

    category_counts = {category: 0 for category in EVENT_CATEGORIES}
    for row in category_rows:
        category_counts[str(row["event_category"])] = int(row["item_count"])

    actor_type_counts = {actor_type: 0 for actor_type in ACTOR_TYPES}
    for row in actor_rows:
        actor_type_counts[str(row["actor_type"])] = int(row["item_count"])

    total_pages = (total_items + filters.page_size - 1) // filters.page_size if total_items else 0
    return {
        "items": [_serialize_audit_row(row) for row in rows],
        "summary": {
            "total_items": total_items,
            "category_counts": category_counts,
            "actor_type_counts": actor_type_counts,
            "user_actor_items": actor_type_counts.get("user", 0),
        },
        "applied_filters": {
            "event_category": filters.event_category,
            "event_type": filters.event_type,
            "actor_type": filters.actor_type,
            "target_type": filters.target_type,
            "actor_id": filters.actor_id,
            "target_id": filters.target_id,
            "run_id": filters.run_id,
            "review_task_id": filters.review_task_id,
            "product_id": filters.product_id,
            "publish_item_id": filters.publish_item_id,
            "occurred_from": filters.occurred_from.isoformat() if filters.occurred_from else None,
            "occurred_to": filters.occurred_to.isoformat() if filters.occurred_to else None,
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


def _build_where_clause(filters: AuditLogFilters) -> tuple[str, dict[str, Any]]:
    clauses = ["1 = 1"]
    params: dict[str, Any] = {}

    if filters.event_category:
        clauses.append("ae.event_category = %(event_category)s")
        params["event_category"] = filters.event_category
    if filters.event_type:
        clauses.append("ae.event_type = %(event_type)s")
        params["event_type"] = filters.event_type
    if filters.actor_type:
        clauses.append("ae.actor_type = %(actor_type)s")
        params["actor_type"] = filters.actor_type
    if filters.target_type:
        clauses.append("lower(ae.target_type) = %(target_type)s")
        params["target_type"] = filters.target_type
    if filters.actor_id:
        clauses.append("ae.actor_id = %(actor_id)s")
        params["actor_id"] = filters.actor_id
    if filters.target_id:
        clauses.append("ae.target_id = %(target_id)s")
        params["target_id"] = filters.target_id
    if filters.run_id:
        clauses.append("ae.run_id = %(run_id)s")
        params["run_id"] = filters.run_id
    if filters.review_task_id:
        clauses.append("ae.review_task_id = %(review_task_id)s")
        params["review_task_id"] = filters.review_task_id
    if filters.product_id:
        clauses.append("ae.product_id = %(product_id)s")
        params["product_id"] = filters.product_id
    if filters.publish_item_id:
        clauses.append("ae.publish_item_id = %(publish_item_id)s")
        params["publish_item_id"] = filters.publish_item_id
    if filters.occurred_from:
        clauses.append("ae.occurred_at >= %(occurred_from)s")
        params["occurred_from"] = filters.occurred_from
    if filters.occurred_to:
        clauses.append("ae.occurred_at <= %(occurred_to)s")
        params["occurred_to"] = filters.occurred_to
    if filters.search:
        clauses.append(
            f"""
            (
                ae.audit_event_id ILIKE %(search)s
                OR ae.event_type ILIKE %(search)s
                OR ae.target_id ILIKE %(search)s
                OR COALESCE(ae.reason_code, '') ILIKE %(search)s
                OR COALESCE(ae.reason_text, '') ILIKE %(search)s
                OR COALESCE(ae.request_id, '') ILIKE %(search)s
                OR COALESCE(ae.diff_summary, '') ILIKE %(search)s
                OR COALESCE(ua.display_name, '') ILIKE %(search)s
                OR COALESCE(ua.email, '') ILIKE %(search)s
                OR COALESCE({_PRODUCT_NAME_SQL}, '') ILIKE %(search)s
                OR COALESCE(b.bank_name, '') ILIKE %(search)s
                OR COALESCE(ae.review_task_id, '') ILIKE %(search)s
                OR COALESCE(ae.run_id, '') ILIKE %(search)s
                OR COALESCE(ae.product_id, '') ILIKE %(search)s
            )
            """
        )
        params["search"] = f"%{filters.search}%"

    return " AND ".join(clause.strip() for clause in clauses), params


def _build_order_by_clause(filters: AuditLogFilters) -> str:
    direction = "ASC" if filters.sort_order == "asc" else "DESC"
    if filters.sort_by == "event_category":
        return f"ae.event_category {direction}, ae.occurred_at DESC, ae.audit_event_id DESC"
    if filters.sort_by == "event_type":
        return f"ae.event_type {direction}, ae.occurred_at DESC, ae.audit_event_id DESC"
    if filters.sort_by == "target_type":
        return f"ae.target_type {direction}, ae.occurred_at DESC, ae.audit_event_id DESC"
    return f"ae.occurred_at {direction}, ae.audit_event_id DESC"


def _serialize_audit_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_event_id": str(row["audit_event_id"]),
        "event_category": str(row["event_category"]),
        "event_type": str(row["event_type"]),
        "occurred_at": row["occurred_at"].isoformat(),
        "actor_type": str(row["actor_type"]),
        "actor": {
            "actor_id": _string_or_none(row.get("actor_id")),
            "display_name": _string_or_none(row.get("actor_display_name")),
            "email": _string_or_none(row.get("actor_email")),
            "role_snapshot": _string_or_none(row.get("actor_role_snapshot")),
            "current_role": _string_or_none(row.get("actor_current_role")),
        },
        "target": {
            "target_type": str(row["target_type"]),
            "target_id": str(row["target_id"]),
            "display_name": _string_or_none(row.get("target_display_name")),
        },
        "state_transition": {
            "previous_state": _string_or_none(row.get("previous_state")),
            "new_state": _string_or_none(row.get("new_state")),
        },
        "reason": {
            "reason_code": _string_or_none(row.get("reason_code")),
            "reason_text": _string_or_none(row.get("reason_text")),
        },
        "request_context": {
            "request_id": _string_or_none(row.get("request_id")),
            "ip_address": _string_or_none(row.get("ip_address")),
            "user_agent": _string_or_none(row.get("user_agent")),
        },
        "related_context": {
            "run_id": _string_or_none(row.get("run_id")),
            "run_type": _string_or_none(row.get("run_type")),
            "run_status": _string_or_none(row.get("run_state")),
            "candidate_id": _string_or_none(row.get("candidate_id")),
            "review_task_id": _string_or_none(row.get("review_task_id")),
            "product_id": _string_or_none(row.get("product_id")),
            "publish_item_id": _string_or_none(row.get("publish_item_id")),
            "product_name": _string_or_none(row.get("product_name")),
            "bank_code": _string_or_none(row.get("bank_code")),
            "bank_name": _string_or_none(row.get("bank_name")),
        },
        "diff_summary": _string_or_none(row.get("diff_summary")),
        "source_ref": _string_or_none(row.get("source_ref")),
        "retention_class": str(row["retention_class"]),
        "event_payload": _coerce_mapping(row.get("event_payload")),
    }


def _normalize_enum(value: str | None, allowed: tuple[str, ...]) -> str | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    lowered = normalized.lower()
    for item in allowed:
        if item.lower() == lowered:
            return item
    return None


def _normalize_search(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
