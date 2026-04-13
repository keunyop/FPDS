from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection

CHANGE_TYPES = ("New", "Updated", "Discontinued", "Reclassified", "ManualOverride")
_PRODUCT_NAME_SQL = """
COALESCE(
    NULLIF(pv.normalized_payload ->> 'product_name', ''),
    NULLIF(cp.product_name, ''),
    NULLIF(nc.product_name, ''),
    ce.product_id
)
"""
_PRODUCT_TYPE_SQL = """
LOWER(
    COALESCE(
        NULLIF(pv.normalized_payload ->> 'product_type', ''),
        NULLIF(cp.product_type, ''),
        NULLIF(nc.product_type, ''),
        ''
    )
)
"""


@dataclass(frozen=True)
class ChangeHistoryFilters:
    product_id: str | None
    bank_code: str | None
    product_type: str | None
    change_type: str | None
    changed_from: datetime | None
    changed_to: datetime | None
    search: str | None
    sort_by: str
    sort_order: str
    page: int
    page_size: int


def normalize_change_history_filters(
    *,
    product_id: str | None,
    bank_code: str | None,
    product_type: str | None,
    change_type: str | None,
    changed_from: datetime | None,
    changed_to: datetime | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> ChangeHistoryFilters:
    normalized_change_type = None
    if change_type and change_type.strip():
        requested = change_type.strip().lower()
        for supported in CHANGE_TYPES:
            if supported.lower() == requested:
                normalized_change_type = supported
                break

    normalized_sort_by = sort_by.strip().lower() if sort_by else "detected_at"
    if normalized_sort_by not in {"detected_at", "change_type", "product_name", "bank_code"}:
        normalized_sort_by = "detected_at"

    return ChangeHistoryFilters(
        product_id=_normalize_text(product_id),
        bank_code=_normalize_text(bank_code).upper() if _normalize_text(bank_code) else None,
        product_type=_normalize_text(product_type).lower() if _normalize_text(product_type) else None,
        change_type=normalized_change_type,
        changed_from=changed_from,
        changed_to=changed_to,
        search=_normalize_search(search),
        sort_by=normalized_sort_by,
        sort_order="asc" if sort_order == "asc" else "desc",
        page=page,
        page_size=page_size,
    )


def load_change_history_list(connection: Connection, *, filters: ChangeHistoryFilters) -> dict[str, Any]:
    where_sql, params = _build_where_clause(filters)

    total_row = connection.execute(
        f"""
        SELECT COUNT(*) AS total_items, COUNT(DISTINCT ce.product_id) AS affected_product_count
        FROM change_event AS ce
        JOIN canonical_product AS cp
          ON cp.product_id = ce.product_id
        LEFT JOIN product_version AS pv
          ON pv.product_version_id = ce.product_version_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ce.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        LEFT JOIN bank AS b
          ON b.bank_code = cp.bank_code
        WHERE {where_sql}
        """,
        params,
    ).fetchone()
    total_items = int(total_row["total_items"]) if total_row else 0
    affected_product_count = int(total_row["affected_product_count"]) if total_row else 0

    type_rows = connection.execute(
        f"""
        SELECT ce.event_type, COUNT(*) AS item_count
        FROM change_event AS ce
        JOIN canonical_product AS cp
          ON cp.product_id = ce.product_id
        LEFT JOIN product_version AS pv
          ON pv.product_version_id = ce.product_version_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ce.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        LEFT JOIN bank AS b
          ON b.bank_code = cp.bank_code
        WHERE {where_sql}
        GROUP BY ce.event_type
        """,
        params,
    ).fetchall()

    rows = connection.execute(
        f"""
        SELECT
            ce.change_event_id,
            ce.product_id,
            ce.product_version_id,
            ce.run_id,
            ce.review_task_id,
            ce.event_type,
            ce.event_reason_code,
            COALESCE(ce.event_metadata, '{{}}'::jsonb) AS event_metadata,
            ce.detected_at,
            cp.bank_code,
            COALESCE(b.bank_name, cp.bank_code) AS bank_name,
            {_PRODUCT_NAME_SQL} AS product_name,
            {_PRODUCT_TYPE_SQL} AS product_type,
            COALESCE(
                NULLIF(pv.normalized_payload ->> 'subtype_code', ''),
                NULLIF(cp.subtype_code, ''),
                NULLIF(nc.subtype_code, '')
            ) AS subtype_code,
            rt.review_state,
            decision.review_decision_id,
            decision.action_type AS review_action_type,
            decision.reason_code AS review_reason_code,
            decision.reason_text AS review_reason_text,
            decision.diff_summary AS review_diff_summary,
            decision.decided_at AS review_decided_at,
            decision.actor_user_id AS decision_actor_user_id,
            decision.actor_display_name,
            decision.actor_email,
            decision.actor_role,
            run_info.run_type,
            run_info.run_state,
            run_info.correlation_id,
            audit_ctx.audit_event_id,
            audit_ctx.audit_diff_summary,
            audit_ctx.audit_occurred_at,
            audit_ctx.audit_actor_id,
            audit_ctx.audit_actor_display_name,
            audit_ctx.audit_actor_email,
            audit_ctx.audit_actor_role
        FROM change_event AS ce
        JOIN canonical_product AS cp
          ON cp.product_id = ce.product_id
        LEFT JOIN product_version AS pv
          ON pv.product_version_id = ce.product_version_id
        LEFT JOIN review_task AS rt
          ON rt.review_task_id = ce.review_task_id
        LEFT JOIN normalized_candidate AS nc
          ON nc.candidate_id = rt.candidate_id
        LEFT JOIN bank AS b
          ON b.bank_code = cp.bank_code
        LEFT JOIN LATERAL (
            SELECT
                rd.review_decision_id,
                rd.action_type,
                rd.reason_code,
                rd.reason_text,
                rd.diff_summary,
                rd.decided_at,
                rd.actor_user_id,
                ua.display_name AS actor_display_name,
                ua.email AS actor_email,
                ua.role AS actor_role
            FROM review_decision AS rd
            LEFT JOIN user_account AS ua
              ON ua.user_id = rd.actor_user_id
            WHERE rd.review_task_id = ce.review_task_id
            ORDER BY rd.decided_at DESC, rd.review_decision_id DESC
            LIMIT 1
        ) AS decision
          ON true
        LEFT JOIN LATERAL (
            SELECT
                ir.run_id,
                COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), ir.trigger_type) AS run_type,
                ir.run_state,
                COALESCE(ir.run_metadata ->> 'correlation_id', '') AS correlation_id
            FROM ingestion_run AS ir
            WHERE ir.run_id = ce.run_id
        ) AS run_info
          ON true
        LEFT JOIN LATERAL (
            SELECT
                ae.audit_event_id,
                ae.diff_summary AS audit_diff_summary,
                ae.occurred_at AS audit_occurred_at,
                ae.actor_id AS audit_actor_id,
                ua.display_name AS audit_actor_display_name,
                ua.email AS audit_actor_email,
                ua.role AS audit_actor_role
            FROM audit_event AS ae
            LEFT JOIN user_account AS ua
              ON ua.user_id = ae.actor_id
            WHERE ae.event_type = 'manual_override_recorded'
              AND ae.review_task_id = ce.review_task_id
              AND ae.product_id = ce.product_id
            ORDER BY ae.occurred_at DESC, ae.audit_event_id DESC
            LIMIT 1
        ) AS audit_ctx
          ON ce.event_type = 'ManualOverride'
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

    change_type_counts = {change_type: 0 for change_type in CHANGE_TYPES}
    for row in type_rows:
        event_type = str(row["event_type"])
        change_type_counts[event_type] = int(row["item_count"])

    total_pages = (total_items + filters.page_size - 1) // filters.page_size if total_items else 0
    return {
        "items": [_serialize_change_row(row) for row in rows],
        "summary": {
            "total_items": total_items,
            "affected_product_count": affected_product_count,
            "change_type_counts": change_type_counts,
            "manual_override_items": change_type_counts.get("ManualOverride", 0),
        },
        "applied_filters": {
            "product_id": filters.product_id,
            "bank_code": filters.bank_code,
            "product_type": filters.product_type,
            "change_type": filters.change_type,
            "changed_from": filters.changed_from.isoformat() if filters.changed_from else None,
            "changed_to": filters.changed_to.isoformat() if filters.changed_to else None,
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


def _build_where_clause(filters: ChangeHistoryFilters) -> tuple[str, dict[str, Any]]:
    clauses = ["1 = 1"]
    params: dict[str, Any] = {}

    if filters.product_id:
        clauses.append("ce.product_id = %(product_id)s")
        params["product_id"] = filters.product_id
    if filters.bank_code:
        clauses.append("cp.bank_code = %(bank_code)s")
        params["bank_code"] = filters.bank_code
    if filters.product_type:
        clauses.append(f"{_PRODUCT_TYPE_SQL} = %(product_type)s")
        params["product_type"] = filters.product_type
    if filters.change_type:
        clauses.append("ce.event_type = %(change_type)s")
        params["change_type"] = filters.change_type
    if filters.changed_from:
        clauses.append("ce.detected_at >= %(changed_from)s")
        params["changed_from"] = filters.changed_from
    if filters.changed_to:
        clauses.append("ce.detected_at <= %(changed_to)s")
        params["changed_to"] = filters.changed_to
    if filters.search:
        clauses.append(
            f"""
            (
                ce.change_event_id ILIKE %(search)s
                OR ce.product_id ILIKE %(search)s
                OR {_PRODUCT_NAME_SQL} ILIKE %(search)s
                OR cp.bank_code ILIKE %(search)s
                OR COALESCE(b.bank_name, '') ILIKE %(search)s
                OR COALESCE(ce.review_task_id, '') ILIKE %(search)s
                OR COALESCE(ce.run_id, '') ILIKE %(search)s
            )
            """
        )
        params["search"] = f"%{filters.search}%"

    return " AND ".join(clause.strip() for clause in clauses), params


def _build_order_by_clause(filters: ChangeHistoryFilters) -> str:
    direction = "ASC" if filters.sort_order == "asc" else "DESC"
    if filters.sort_by == "change_type":
        return f"ce.event_type {direction}, ce.detected_at DESC, ce.change_event_id DESC"
    if filters.sort_by == "product_name":
        return f"{_PRODUCT_NAME_SQL} {direction}, ce.detected_at DESC, ce.change_event_id DESC"
    if filters.sort_by == "bank_code":
        return f"cp.bank_code {direction}, ce.detected_at DESC, ce.change_event_id DESC"
    return f"ce.detected_at {direction}, ce.change_event_id DESC"


def _serialize_change_row(row: dict[str, Any]) -> dict[str, Any]:
    event_metadata = _coerce_mapping(row.get("event_metadata"))
    changed_fields = _coerce_string_list(event_metadata.get("changed_field_names"))
    actor = _serialize_actor(
        user_id=_string_or_none(row.get("audit_actor_id")) or _string_or_none(row.get("decision_actor_user_id")) or _string_or_none(event_metadata.get("actor_user_id")),
        display_name=_string_or_none(row.get("audit_actor_display_name")) or _string_or_none(row.get("actor_display_name")),
        email=_string_or_none(row.get("audit_actor_email")) or _string_or_none(row.get("actor_email")),
        role=_string_or_none(row.get("audit_actor_role")) or _string_or_none(row.get("actor_role")),
    )
    audit_context = None
    if row.get("audit_event_id"):
        audit_context = {
            "audit_event_id": str(row["audit_event_id"]),
            "event_type": "manual_override_recorded",
            "diff_summary": _string_or_none(row.get("audit_diff_summary")),
            "occurred_at": row["audit_occurred_at"].isoformat() if row.get("audit_occurred_at") else None,
            "actor": actor,
        }

    previous_version_no = _int_or_none(event_metadata.get("previous_version_no"))
    current_version_no = _int_or_none(event_metadata.get("current_version_no"))
    return {
        "change_event_id": str(row["change_event_id"]),
        "canonical_product_id": str(row["product_id"]),
        "product_version_id": _string_or_none(row.get("product_version_id")),
        "product_name": str(row["product_name"]),
        "bank_code": str(row["bank_code"]),
        "bank_name": str(row["bank_name"]),
        "product_type": str(row["product_type"]),
        "subtype_code": _string_or_none(row.get("subtype_code")),
        "change_type": str(row["event_type"]),
        "change_reason_code": _string_or_none(row.get("event_reason_code")),
        "change_summary": _build_change_summary(
            change_type=str(row["event_type"]),
            product_name=str(row["product_name"]),
            changed_fields=changed_fields,
            previous_version_no=previous_version_no,
            current_version_no=current_version_no,
        ),
        "changed_fields": changed_fields,
        "detected_at": row["detected_at"].isoformat(),
        "actor_type": "user" if _actor_has_user_context(actor) else "system",
        "actor": actor,
        "version_info": {
            "previous_version_no": previous_version_no,
            "current_version_no": current_version_no,
        },
        "review_context": {
            "review_task_id": _string_or_none(row.get("review_task_id")),
            "review_state": _string_or_none(row.get("review_state")),
            "action_type": _string_or_none(row.get("review_action_type")),
            "reason_code": _string_or_none(row.get("review_reason_code")),
            "reason_text": _string_or_none(row.get("review_reason_text")),
            "diff_summary": _string_or_none(row.get("review_diff_summary")),
            "decided_at": row["review_decided_at"].isoformat() if row.get("review_decided_at") else None,
        },
        "run_context": {
            "run_id": _string_or_none(row.get("run_id")),
            "run_type": _string_or_none(row.get("run_type")),
            "run_status": _string_or_none(row.get("run_state")),
            "correlation_id": _string_or_none(row.get("correlation_id")),
        },
        "audit_context": audit_context,
    }


def _build_change_summary(
    *,
    change_type: str,
    product_name: str,
    changed_fields: list[str],
    previous_version_no: int | None,
    current_version_no: int | None,
) -> str:
    field_summary = _summarize_changed_fields(changed_fields)
    if change_type == "New":
        version_label = f"version {current_version_no}" if current_version_no else "the first approved version"
        return f"{version_label.capitalize()} created for {product_name}."
    if change_type == "Updated":
        if previous_version_no and current_version_no:
            return f"Version {current_version_no} replaced version {previous_version_no} for {product_name}. {field_summary}".strip()
        return f"{product_name} was updated. {field_summary}".strip()
    if change_type == "Discontinued":
        return f"{product_name} was marked as discontinued."
    if change_type == "Reclassified":
        if previous_version_no and current_version_no:
            return f"{product_name} was reclassified in version {current_version_no}. {field_summary}".strip()
        return f"{product_name} was reclassified. {field_summary}".strip()
    if change_type == "ManualOverride":
        return f"Operator override adjusted {_summarize_changed_fields_inline(changed_fields)}."
    return f"{product_name} change recorded."


def _summarize_changed_fields(changed_fields: list[str]) -> str:
    if not changed_fields:
        return "No stored field diff."
    if len(changed_fields) == 1:
        return f"Changed field: {changed_fields[0]}."
    if len(changed_fields) == 2:
        return f"Changed fields: {changed_fields[0]}, {changed_fields[1]}."
    preview = ", ".join(changed_fields[:3])
    return f"Changed fields: {preview}, and {len(changed_fields) - 3} more."


def _summarize_changed_fields_inline(changed_fields: list[str]) -> str:
    if not changed_fields:
        return "the approved payload"
    if len(changed_fields) <= 3:
        return ", ".join(changed_fields)
    preview = ", ".join(changed_fields[:3])
    return f"{preview}, and {len(changed_fields) - 3} more fields"


def _serialize_actor(*, user_id: str | None, display_name: str | None, email: str | None, role: str | None) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "display_name": display_name,
        "email": email,
        "role": role,
    }


def _actor_has_user_context(actor: dict[str, Any]) -> bool:
    return any(
        actor.get(field)
        for field in ("user_id", "display_name", "email", "role")
    )


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


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
