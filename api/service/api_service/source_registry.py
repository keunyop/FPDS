from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover - keeps unit tests lightweight when psycopg is unavailable.
    Connection = Any

from api_service.errors import SourceRegistryError
from api_service.product_types import load_product_type_definitions_map
from api_service.security import new_id, utc_now
from api_service.source_registry_utils import infer_source_type, normalize_source_url, repo_root


_ROLE_PRIORITY = {
    "detail": 0,
    "entry": 1,
    "supporting_html": 2,
    "supporting_pdf": 3,
    "linked_pdf": 3,
}
_AUTO_SUPPORT_SOURCE_IDS = {
    "TD-SAV-002": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-003": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-004": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
}


@dataclass(frozen=True)
class SourceRegistryFilters:
    bank_code: str | None
    country_code: str | None
    product_type: str | None
    status: str | None
    discovery_role: str | None
    search: str | None


def normalize_source_registry_filters(
    *,
    bank_code: str | None,
    country_code: str | None,
    product_type: str | None,
    status: str | None,
    discovery_role: str | None,
    search: str | None,
) -> SourceRegistryFilters:
    normalized_bank_code = _clean_text(bank_code)
    normalized_country_code = _clean_text(country_code)
    normalized_product_type = _clean_text(product_type)
    normalized_status = _clean_text(status)
    normalized_discovery_role = _clean_text(discovery_role)
    normalized_search = _normalize_search(search)

    return SourceRegistryFilters(
        bank_code=normalized_bank_code.upper() if normalized_bank_code else None,
        country_code=normalized_country_code.upper() if normalized_country_code else None,
        product_type=normalized_product_type.lower() if normalized_product_type else None,
        status=normalized_status.lower() if normalized_status else None,
        discovery_role=normalized_discovery_role.lower() if normalized_discovery_role else None,
        search=normalized_search,
    )


def load_source_registry_list(connection: Connection, *, filters: SourceRegistryFilters) -> dict[str, Any]:
    where_clauses = ["1 = 1"]
    query_params: dict[str, Any] = {}

    if filters.bank_code:
        where_clauses.append("bank_code = %(bank_code)s")
        query_params["bank_code"] = filters.bank_code
    if filters.country_code:
        where_clauses.append("country_code = %(country_code)s")
        query_params["country_code"] = filters.country_code
    if filters.product_type:
        where_clauses.append("product_type = %(product_type)s")
        query_params["product_type"] = filters.product_type
    if filters.status:
        where_clauses.append("status = %(status)s")
        query_params["status"] = filters.status
    if filters.discovery_role:
        where_clauses.append("discovery_role = %(discovery_role)s")
        query_params["discovery_role"] = filters.discovery_role
    if filters.search:
        query_params["search_pattern"] = f"%{filters.search}%"
        where_clauses.append(
            """
            (
                lower(source_id) LIKE %(search_pattern)s
                OR lower(source_name) LIKE %(search_pattern)s
                OR lower(source_url) LIKE %(search_pattern)s
                OR lower(normalized_url) LIKE %(search_pattern)s
                OR lower(COALESCE(product_key, '')) LIKE %(search_pattern)s
            )
            """
        )

    rows = connection.execute(
        f"""
        SELECT
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_item
        WHERE {" AND ".join(where_clauses)}
        ORDER BY bank_code, product_type, source_id
        """,
        query_params,
    ).fetchall()

    items = [_serialize_source_registry_row(row) for row in rows]
    status_counts = Counter(item["status"] for item in items)
    role_counts = Counter(item["discovery_role"] for item in items)

    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "status_counts": dict(status_counts),
            "role_counts": dict(role_counts),
            "candidate_producing_items": sum(1 for item in items if bool(item["candidate_producing_flag"])),
        },
        "facets": {
            "bank_codes": sorted({item["bank_code"] for item in items}),
            "product_types": sorted({item["product_type"] for item in items}),
            "statuses": sorted(status_counts),
            "discovery_roles": sorted(role_counts),
        },
        "applied_filters": {
            "bank_code": filters.bank_code,
            "country_code": filters.country_code,
            "product_type": filters.product_type,
            "status": filters.status,
            "discovery_role": filters.discovery_role,
            "search": filters.search,
        },
    }


def load_source_registry_detail(connection: Connection, *, source_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_item
        WHERE source_id = %(source_id)s
        """,
        {"source_id": source_id},
    ).fetchone()
    if not row:
        return None

    recent_runs = connection.execute(
        """
        SELECT
            run_id,
            run_state,
            trigger_type,
            triggered_by,
            source_scope_count,
            candidate_count,
            review_queued_count,
            partial_completion_flag,
            error_summary,
            run_metadata,
            started_at,
            completed_at
        FROM ingestion_run
        WHERE EXISTS (
                SELECT 1
                FROM jsonb_array_elements_text(COALESCE(run_metadata -> 'collection_source_ids', '[]'::jsonb)) AS sid(source_id)
                WHERE sid.source_id = %(source_id)s
            )
           OR EXISTS (
                SELECT 1
                FROM jsonb_array_elements_text(COALESCE(run_metadata -> 'source_ids', '[]'::jsonb)) AS sid(source_id)
                WHERE sid.source_id = %(source_id)s
           )
        ORDER BY started_at DESC
        LIMIT 5
        """,
        {"source_id": source_id},
    ).fetchall()

    return {
        "source": _serialize_source_registry_row(row),
        "recent_runs": [_serialize_recent_run_row(run_row) for run_row in recent_runs],
    }


def create_source_registry_item(
    connection: Connection,
    *,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    prepared = _prepare_source_registry_payload(payload, existing_row=None)
    now = utc_now()
    connection.execute(
        """
        INSERT INTO source_registry_item (
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        )
        VALUES (
            %(source_id)s,
            %(bank_code)s,
            %(country_code)s,
            %(product_type)s,
            %(product_key)s,
            %(source_name)s,
            %(source_url)s,
            %(normalized_url)s,
            %(source_type)s,
            %(discovery_role)s,
            %(status)s,
            %(priority)s,
            %(source_language)s,
            %(purpose)s,
            %(expected_fields)s::jsonb,
            %(seed_source_flag)s,
            %(last_verified_at)s,
            %(last_seen_at)s,
            %(redirect_target_url)s,
            %(alias_urls)s::jsonb,
            %(discovery_metadata)s::jsonb,
            %(change_reason)s,
            %(created_at)s,
            %(updated_at)s
        )
        """,
        {
            **prepared,
            "expected_fields": json.dumps(prepared["expected_fields"], ensure_ascii=True),
            "alias_urls": json.dumps(prepared["alias_urls"], ensure_ascii=True),
            "discovery_metadata": json.dumps(prepared["discovery_metadata"], ensure_ascii=True),
            "created_at": now,
            "updated_at": now,
        },
    )
    _record_source_registry_audit_event(
        connection,
        event_type="source_registry_item_created",
        actor=actor,
        target_id=prepared["source_id"],
        request_context=request_context,
        previous_state=None,
        new_state=str(prepared["status"]),
        reason_text=_optional_text(prepared.get("change_reason")),
        diff_summary=f"Created source registry item `{prepared['source_id']}`.",
        payload={
            "bank_code": prepared["bank_code"],
            "product_type": prepared["product_type"],
            "discovery_role": prepared["discovery_role"],
        },
    )
    detail = load_source_registry_detail(connection, source_id=prepared["source_id"])
    assert detail is not None
    return detail["source"]


def update_source_registry_item(
    connection: Connection,
    *,
    source_id: str,
    payload: dict[str, Any],
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    existing_row = connection.execute(
        """
        SELECT
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_item
        WHERE source_id = %(source_id)s
        """,
        {"source_id": source_id},
    ).fetchone()
    if not existing_row:
        raise SourceRegistryError(status_code=404, code="source_registry_item_not_found", message="Source registry item was not found.")

    prepared = _prepare_source_registry_payload(payload, existing_row=existing_row)
    diff_summary = _build_source_registry_diff_summary(existing_row, prepared)
    connection.execute(
        """
        UPDATE source_registry_item
        SET
            bank_code = %(bank_code)s,
            country_code = %(country_code)s,
            product_type = %(product_type)s,
            product_key = %(product_key)s,
            source_name = %(source_name)s,
            source_url = %(source_url)s,
            normalized_url = %(normalized_url)s,
            source_type = %(source_type)s,
            discovery_role = %(discovery_role)s,
            status = %(status)s,
            priority = %(priority)s,
            source_language = %(source_language)s,
            purpose = %(purpose)s,
            expected_fields = %(expected_fields)s::jsonb,
            seed_source_flag = %(seed_source_flag)s,
            last_verified_at = %(last_verified_at)s,
            last_seen_at = %(last_seen_at)s,
            redirect_target_url = %(redirect_target_url)s,
            alias_urls = %(alias_urls)s::jsonb,
            discovery_metadata = %(discovery_metadata)s::jsonb,
            change_reason = %(change_reason)s,
            updated_at = %(updated_at)s
        WHERE source_id = %(source_id)s
        """,
        {
            **prepared,
            "source_id": source_id,
            "expected_fields": json.dumps(prepared["expected_fields"], ensure_ascii=True),
            "alias_urls": json.dumps(prepared["alias_urls"], ensure_ascii=True),
            "discovery_metadata": json.dumps(prepared["discovery_metadata"], ensure_ascii=True),
            "updated_at": utc_now(),
        },
    )
    _record_source_registry_audit_event(
        connection,
        event_type="source_registry_item_updated",
        actor=actor,
        target_id=source_id,
        request_context=request_context,
        previous_state=str(existing_row["status"]),
        new_state=str(prepared["status"]),
        reason_text=_optional_text(prepared.get("change_reason")),
        diff_summary=diff_summary,
        payload={
            "bank_code": prepared["bank_code"],
            "product_type": prepared["product_type"],
            "discovery_role": prepared["discovery_role"],
        },
    )
    detail = load_source_registry_detail(connection, source_id=source_id)
    assert detail is not None
    return detail["source"]


def delete_source_registry_item(
    connection: Connection,
    *,
    source_id: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    existing_row = connection.execute(
        """
        SELECT
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_item
        WHERE source_id = %(source_id)s
        """,
        {"source_id": source_id},
    ).fetchone()
    if not existing_row:
        raise SourceRegistryError(status_code=404, code="source_registry_item_not_found", message="Source registry item was not found.")

    if str(existing_row["status"]) != "removed":
        reason_text = "removed_by_operator"
        connection.execute(
            """
            UPDATE source_registry_item
            SET
                status = 'removed',
                change_reason = %(change_reason)s,
                updated_at = %(updated_at)s
            WHERE source_id = %(source_id)s
            """,
            {
                "source_id": source_id,
                "change_reason": reason_text,
                "updated_at": utc_now(),
            },
        )
        _record_source_registry_audit_event(
            connection,
            event_type="source_registry_item_removed",
            actor=actor,
            target_id=source_id,
            request_context=request_context,
            previous_state=str(existing_row["status"]),
            new_state="removed",
            reason_text=reason_text,
            diff_summary=f"Marked source registry item `{source_id}` as removed.",
            payload={
                "bank_code": existing_row["bank_code"],
                "product_type": existing_row["product_type"],
                "discovery_role": existing_row["discovery_role"],
                "source_url": existing_row["source_url"],
            },
        )

    detail = load_source_registry_detail(connection, source_id=source_id)
    assert detail is not None
    return detail["source"]


def start_source_collection(
    connection: Connection,
    *,
    source_ids: list[str],
    actor: dict[str, Any],
    request_context: dict[str, Any],
    retry_of_run_id: str | None = None,
) -> dict[str, Any]:
    prepared = prepare_source_collection(
        connection,
        source_ids=source_ids,
        actor=actor,
        request_id=request_context.get("request_id"),
    )
    collection_id = str(prepared["collection_id"])
    correlation_id = str(prepared["correlation_id"])
    plan = prepared["plan"]

    for group in plan["groups"]:
        _insert_collection_run_row(
            connection,
            run_id=str(group["run_id"]),
            triggered_by=str(plan["triggered_by"]),
            request_id=request_context.get("request_id"),
            correlation_id=correlation_id,
            collection_id=collection_id,
            group=group,
            retry_of_run_id=retry_of_run_id,
        )

    _record_source_registry_audit_event(
        connection,
        event_type="source_collection_started",
        actor=actor,
        target_id=collection_id,
        request_context=request_context,
        previous_state=None,
        new_state="started",
        reason_text=None,
        diff_summary="Launched source-selected collection run batch.",
        payload={
            "selected_source_ids": plan["selected_source_ids"],
            "auto_included_source_ids": plan["auto_included_source_ids"],
            "run_ids": [group["run_id"] for group in plan["groups"]],
            "retry_of_run_id": retry_of_run_id,
        },
        event_category="run",
        target_type="source_collection",
    )
    _launch_source_collection_runner(plan)

    return {
        "collection_id": collection_id,
        "correlation_id": correlation_id,
        "run_ids": [group["run_id"] for group in plan["groups"]],
        "selected_source_ids": plan["selected_source_ids"],
        "target_source_ids": plan["target_source_ids"],
        "auto_included_source_ids": plan["auto_included_source_ids"],
        "groups": [
            {
                "run_id": group["run_id"],
                "bank_code": group["bank_code"],
                "country_code": group["country_code"],
                "product_type": group["product_type"],
                "source_language": group["source_language"],
                "target_source_ids": group["target_source_ids"],
                "included_source_ids": group["included_source_ids"],
            }
            for group in plan["groups"]
        ],
    }


def prepare_source_collection(
    connection: Connection,
    *,
    source_ids: list[str],
    actor: dict[str, Any],
    request_id: str | None,
    collection_id: str | None = None,
    correlation_id: str | None = None,
    run_id_overrides: dict[tuple[str, str, str, str], str] | None = None,
) -> dict[str, Any]:
    selected_source_ids = _dedupe_preserve_order([item.strip() for item in source_ids if item and item.strip()])
    if not selected_source_ids:
        raise SourceRegistryError(status_code=400, code="source_collection_empty_selection", message="Select at least one source before starting collection.")

    selected_rows = connection.execute(
        """
        SELECT
            source_id,
            bank_code,
            country_code,
            product_type,
            product_key,
            source_name,
            source_url,
            normalized_url,
            source_type,
            discovery_role,
            status,
            priority,
            source_language,
            purpose,
            expected_fields,
            seed_source_flag,
            last_verified_at,
            last_seen_at,
            redirect_target_url,
            alias_urls,
            discovery_metadata,
            change_reason,
            created_at,
            updated_at
        FROM source_registry_item
        WHERE source_id = ANY(%(source_ids)s)
        """,
        {"source_ids": selected_source_ids},
    ).fetchall()
    selected_by_id = {str(row["source_id"]): row for row in selected_rows}
    missing_source_ids = [source_id for source_id in selected_source_ids if source_id not in selected_by_id]
    if missing_source_ids:
        raise SourceRegistryError(
            status_code=404,
            code="source_registry_item_not_found",
            message="Source registry item was not found for: " + ", ".join(missing_source_ids),
        )

    blocked_source_ids = [source_id for source_id in selected_source_ids if str(selected_by_id[source_id]["status"]) == "removed"]
    if blocked_source_ids:
        raise SourceRegistryError(
            status_code=400,
            code="source_collection_removed_source",
            message="Removed sources cannot be collected: " + ", ".join(blocked_source_ids),
        )

    target_rows = [selected_by_id[source_id] for source_id in selected_source_ids if str(selected_by_id[source_id]["discovery_role"]) == "detail"]
    if not target_rows:
        raise SourceRegistryError(
            status_code=400,
            code="source_collection_requires_detail_source",
            message="Select at least one detail source to create product candidates.",
        )

    auto_support_source_ids = _dedupe_preserve_order(
        [
            support_source_id
            for row in target_rows
            for support_source_id in _AUTO_SUPPORT_SOURCE_IDS.get(str(row["source_id"]), ())
            if support_source_id not in selected_by_id
        ]
    )
    auto_support_rows: list[dict[str, Any]] = []
    if auto_support_source_ids:
        auto_support_rows = connection.execute(
            """
            SELECT
                source_id,
                bank_code,
                country_code,
                product_type,
                product_key,
                source_name,
                source_url,
                normalized_url,
                source_type,
                discovery_role,
                status,
                priority,
                source_language,
                purpose,
                expected_fields,
                seed_source_flag,
                last_verified_at,
                last_seen_at,
                redirect_target_url,
                alias_urls,
                discovery_metadata,
                change_reason,
                created_at,
                updated_at
            FROM source_registry_item
            WHERE source_id = ANY(%(source_ids)s)
              AND status <> 'removed'
            """,
            {"source_ids": auto_support_source_ids},
        ).fetchall()

    auto_support_by_id = {str(row["source_id"]): row for row in auto_support_rows}
    included_rows_by_id = dict(selected_by_id)
    included_rows_by_id.update(auto_support_by_id)
    product_type_definitions = load_product_type_definitions_map(
        connection,
        codes=[str(row["product_type"]) for row in included_rows_by_id.values()],
        active_only=False,
    )

    resolved_collection_id = collection_id or new_id("collection")
    resolved_correlation_id = correlation_id or new_id("corr")
    plan = build_source_collection_plan(
        selected_rows=[selected_by_id[source_id] for source_id in selected_source_ids],
        included_rows=list(included_rows_by_id.values()),
        product_type_definitions=product_type_definitions,
        collection_id=resolved_collection_id,
        correlation_id=resolved_correlation_id,
        actor=actor,
        request_id=request_id,
        run_id_overrides=run_id_overrides,
    )
    return {
        "collection_id": resolved_collection_id,
        "correlation_id": resolved_correlation_id,
        "plan": plan,
    }


def build_source_collection_plan(
    *,
    selected_rows: list[dict[str, Any]],
    included_rows: list[dict[str, Any]],
    product_type_definitions: dict[str, dict[str, Any]] | None = None,
    collection_id: str,
    correlation_id: str,
    actor: dict[str, Any],
    request_id: str | None,
    run_id_overrides: dict[tuple[str, str, str, str], str] | None = None,
) -> dict[str, Any]:
    product_type_definitions = product_type_definitions or {}
    selected_rows_by_id = {str(row["source_id"]): row for row in selected_rows}
    selected_source_ids = [str(row["source_id"]) for row in _sort_source_rows(selected_rows)]
    target_source_ids = [
        str(row["source_id"])
        for row in _sort_source_rows(selected_rows)
        if str(row["discovery_role"]) == "detail"
    ]
    auto_included_source_ids = [
        source_id
        for source_id in [str(row["source_id"]) for row in _sort_source_rows(included_rows)]
        if source_id not in selected_rows_by_id
    ]

    grouped_selected_rows: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    grouped_included_rows: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in selected_rows:
        grouped_selected_rows[_registry_group_key(row)].append(row)
    for row in included_rows:
        grouped_included_rows[_registry_group_key(row)].append(row)

    groups: list[dict[str, Any]] = []
    for group_key in sorted(grouped_included_rows):
        included_group_rows = _sort_source_rows(grouped_included_rows[group_key])
        selected_group_rows = _sort_source_rows(grouped_selected_rows.get(group_key, []))
        target_group_rows = [row for row in selected_group_rows if str(row["discovery_role"]) == "detail"]
        if not target_group_rows:
            continue
        country_code, bank_code, product_type, source_language = group_key
        run_id = (run_id_overrides or {}).get(group_key) or _build_collection_run_id(bank_code=bank_code, product_type=product_type)
        groups.append(
            {
                "run_id": run_id,
                "country_code": country_code,
                "bank_code": bank_code,
                "product_type": product_type,
                "source_language": source_language,
                "selected_source_ids": [str(row["source_id"]) for row in selected_group_rows],
                "target_source_ids": [str(row["source_id"]) for row in target_group_rows],
                "included_source_ids": [str(row["source_id"]) for row in included_group_rows],
                "included_sources": [
                    _collection_source_record(
                        row,
                        product_type_definition=product_type_definitions.get(str(row["product_type"]), {}),
                    )
                    for row in included_group_rows
                ],
            }
        )

    if not groups:
        raise SourceRegistryError(
            status_code=400,
            code="source_collection_requires_detail_source",
            message="Select at least one detail source to create product candidates.",
        )

    triggered_by = str(actor.get("email") or actor.get("display_name") or actor.get("user_id") or "admin")
    return {
        "collection_id": collection_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "trigger_type": "admin_source_collection",
        "triggered_by": triggered_by,
        "selected_source_ids": selected_source_ids,
        "target_source_ids": target_source_ids,
        "auto_included_source_ids": auto_included_source_ids,
        "groups": groups,
    }


def _prepare_source_registry_payload(payload: dict[str, Any], *, existing_row: dict[str, Any] | None) -> dict[str, Any]:
    existing = existing_row or {}
    raw_source_url = _required_text(payload.get("source_url", existing.get("source_url")), "source_url")
    normalized_url = normalize_source_url(raw_source_url)
    source_type = _clean_text(payload.get("source_type", existing.get("source_type"))) or infer_source_type(raw_source_url)
    source_type = source_type.lower()
    if source_type not in {"html", "pdf"}:
        raise SourceRegistryError(status_code=422, code="invalid_source_type", message="source_type must be `html` or `pdf`.")

    discovery_role = (_clean_text(payload.get("discovery_role", existing.get("discovery_role"))) or "detail").lower()
    if discovery_role not in {"entry", "detail", "supporting_html", "supporting_pdf", "linked_pdf"}:
        raise SourceRegistryError(
            status_code=422,
            code="invalid_discovery_role",
            message="discovery_role must be entry, detail, supporting_html, supporting_pdf, or linked_pdf.",
        )

    status = (_clean_text(payload.get("status", existing.get("status"))) or "active").lower()
    if status not in {"active", "inactive", "deprecated", "removed"}:
        raise SourceRegistryError(status_code=422, code="invalid_status", message="status must be active, inactive, deprecated, or removed.")

    return {
        "source_id": _required_text(payload.get("source_id", existing.get("source_id")), "source_id"),
        "bank_code": _required_text(payload.get("bank_code", existing.get("bank_code")), "bank_code").upper(),
        "country_code": _required_text(payload.get("country_code", existing.get("country_code", "CA")), "country_code").upper(),
        "product_type": _required_text(payload.get("product_type", existing.get("product_type")), "product_type").lower(),
        "product_key": _optional_text(payload.get("product_key", existing.get("product_key"))),
        "source_name": _required_text(payload.get("source_name", existing.get("source_name")), "source_name"),
        "source_url": raw_source_url,
        "normalized_url": normalized_url,
        "source_type": source_type,
        "discovery_role": discovery_role,
        "status": status,
        "priority": (_clean_text(payload.get("priority", existing.get("priority"))) or "P1").upper(),
        "source_language": (_clean_text(payload.get("source_language", existing.get("source_language"))) or "en").lower(),
        "purpose": _optional_text(payload.get("purpose", existing.get("purpose"))) or "",
        "expected_fields": _normalize_string_list(payload.get("expected_fields", existing.get("expected_fields", []))),
        "seed_source_flag": bool(payload.get("seed_source_flag", existing.get("seed_source_flag", False))),
        "last_verified_at": _coerce_optional_timestamp(payload.get("last_verified_at", existing.get("last_verified_at"))),
        "last_seen_at": _coerce_optional_timestamp(payload.get("last_seen_at", existing.get("last_seen_at"))),
        "redirect_target_url": _normalize_optional_url(payload.get("redirect_target_url", existing.get("redirect_target_url"))),
        "alias_urls": [_normalize_optional_url(item) for item in _normalize_string_list(payload.get("alias_urls", existing.get("alias_urls", [])))],
        "discovery_metadata": _coerce_mapping(payload.get("discovery_metadata", existing.get("discovery_metadata"))),
        "change_reason": _optional_text(payload.get("change_reason", existing.get("change_reason"))),
    }


def _serialize_source_registry_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": str(row["source_id"]),
        "bank_code": str(row["bank_code"]),
        "country_code": str(row["country_code"]),
        "product_type": str(row["product_type"]),
        "product_key": row.get("product_key"),
        "source_name": str(row["source_name"]),
        "source_url": str(row["source_url"]),
        "normalized_url": str(row["normalized_url"]),
        "source_type": str(row["source_type"]),
        "discovery_role": str(row["discovery_role"]),
        "status": str(row["status"]),
        "priority": str(row.get("priority") or "P1"),
        "source_language": str(row.get("source_language") or "en"),
        "purpose": str(row.get("purpose") or ""),
        "expected_fields": list(row.get("expected_fields") or []),
        "seed_source_flag": bool(row.get("seed_source_flag")),
        "last_verified_at": _serialize_timestamp(row.get("last_verified_at")),
        "last_seen_at": _serialize_timestamp(row.get("last_seen_at")),
        "redirect_target_url": row.get("redirect_target_url"),
        "alias_urls": list(row.get("alias_urls") or []),
        "discovery_metadata": _coerce_mapping(row.get("discovery_metadata")),
        "change_reason": row.get("change_reason"),
        "created_at": _serialize_timestamp(row.get("created_at")),
        "updated_at": _serialize_timestamp(row.get("updated_at")),
        "candidate_producing_flag": str(row["discovery_role"]) == "detail",
    }


def _serialize_recent_run_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": str(row["run_id"]),
        "run_status": str(row["run_state"]),
        "trigger_type": str(row["trigger_type"]),
        "triggered_by": row.get("triggered_by"),
        "source_scope_count": int(row.get("source_scope_count") or 0),
        "candidate_count": int(row.get("candidate_count") or 0),
        "review_queued_count": int(row.get("review_queued_count") or 0),
        "partial_completion_flag": bool(row.get("partial_completion_flag")),
        "error_summary": row.get("error_summary"),
        "started_at": _serialize_timestamp(row.get("started_at")),
        "completed_at": _serialize_timestamp(row.get("completed_at")),
        "pipeline_stage": str((row.get("run_metadata") or {}).get("pipeline_stage") or ""),
    }


def _collection_source_record(row: dict[str, Any], *, product_type_definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": str(row["source_id"]),
        "bank_code": str(row["bank_code"]),
        "country_code": str(row["country_code"]),
        "product_type": str(row["product_type"]),
        "source_name": str(row["source_name"]),
        "source_url": str(row["source_url"]),
        "source_type": str(row["source_type"]),
        "discovery_role": str(row["discovery_role"]),
        "priority": str(row.get("priority") or "P1"),
        "source_language": str(row.get("source_language") or "en"),
        "purpose": str(row.get("purpose") or ""),
        "expected_fields": list(row.get("expected_fields") or []),
        "seed_source_flag": bool(row.get("seed_source_flag")),
        "product_type_name": str(product_type_definition.get("display_name") or row["product_type"]),
        "product_type_description": str(product_type_definition.get("description") or ""),
        "product_type_dynamic": bool(product_type_definition.get("dynamic_onboarding_enabled")),
        "discovery_keywords": list(product_type_definition.get("discovery_keywords") or []),
        "fallback_policy": str(product_type_definition.get("fallback_policy") or "generic_ai_review"),
        "discovery_metadata": _coerce_mapping(row.get("discovery_metadata")),
    }


def _insert_collection_run_row(
    connection: Connection,
    *,
    run_id: str,
    triggered_by: str,
    request_id: str | None,
    correlation_id: str,
    collection_id: str,
    group: dict[str, Any],
    pipeline_stage: str = "source_collection",
    retry_of_run_id: str | None = None,
) -> None:
    started_at = utc_now()
    run_metadata = {
        "pipeline_stage": pipeline_stage,
        "collection_id": collection_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "selected_source_ids": group["selected_source_ids"],
        "source_ids": group["included_source_ids"],
        "collection_source_ids": group["included_source_ids"],
        "target_source_ids": group["target_source_ids"],
        "bank_code": group["bank_code"],
        "country_code": group["country_code"],
        "product_type": group["product_type"],
        "source_language": group["source_language"],
    }
    connection.execute(
        """
        INSERT INTO ingestion_run (
            run_id,
            run_state,
            trigger_type,
            triggered_by,
            source_scope_count,
            source_success_count,
            source_failure_count,
            candidate_count,
            review_queued_count,
            error_summary,
            partial_completion_flag,
            retry_of_run_id,
            retried_by_run_id,
            run_metadata,
            started_at,
            completed_at
        )
        VALUES (
            %(run_id)s,
            'started',
            'admin_source_collection',
            %(triggered_by)s,
            %(source_scope_count)s,
            0,
            0,
            0,
            0,
            NULL,
            false,
            %(retry_of_run_id)s,
            NULL,
            %(run_metadata)s::jsonb,
            %(started_at)s,
            NULL
        )
        ON CONFLICT (run_id) DO UPDATE
        SET
            run_state = 'started',
            trigger_type = 'admin_source_collection',
            triggered_by = COALESCE(EXCLUDED.triggered_by, ingestion_run.triggered_by),
            source_scope_count = GREATEST(ingestion_run.source_scope_count, EXCLUDED.source_scope_count),
            source_success_count = 0,
            source_failure_count = 0,
            candidate_count = 0,
            review_queued_count = 0,
            error_summary = NULL,
            partial_completion_flag = false,
            run_metadata = ingestion_run.run_metadata || EXCLUDED.run_metadata,
            started_at = LEAST(ingestion_run.started_at, EXCLUDED.started_at),
            completed_at = NULL
        """,
        {
            "run_id": run_id,
            "triggered_by": triggered_by,
            "source_scope_count": len(group["included_source_ids"]),
            "retry_of_run_id": retry_of_run_id,
            "run_metadata": json.dumps(run_metadata, ensure_ascii=True),
            "started_at": started_at,
        },
    )


def _launch_source_collection_runner(plan: dict[str, Any]) -> None:
    root = repo_root()
    temp_dir = root / "tmp" / "source-collections"
    temp_dir.mkdir(parents=True, exist_ok=True)
    plan_path = temp_dir / f"{plan['collection_id']}.json"
    log_path = temp_dir / f"{plan['collection_id']}.log"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=True), encoding="utf-8")

    env = os.environ.copy()
    current_python_path = env.get("PYTHONPATH", "")
    api_service_path = str(root / "api" / "service")
    env["PYTHONPATH"] = os.pathsep.join([api_service_path, current_python_path]) if current_python_path else api_service_path

    with log_path.open("a", encoding="utf-8") as log_file:
        try:
            subprocess.Popen(  # noqa: S603
                [sys.executable, "-m", "api_service.source_collection_runner", "--plan-path", str(plan_path)],
                cwd=str(root),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        except OSError as exc:
            raise SourceRegistryError(
                status_code=500,
                code="source_collection_launch_failed",
                message=f"Source collection could not be launched: {exc}",
            ) from exc


def _record_source_registry_audit_event(
    connection: Connection,
    *,
    event_type: str,
    actor: dict[str, Any],
    target_id: str,
    request_context: dict[str, Any],
    previous_state: str | None,
    new_state: str | None,
    reason_text: str | None,
    diff_summary: str | None,
    payload: dict[str, Any],
    event_category: str = "config",
    target_type: str = "source_registry_item",
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
            %(event_category)s,
            %(event_type)s,
            'user',
            %(actor_id)s,
            %(actor_role_snapshot)s,
            %(target_type)s,
            %(target_id)s,
            %(previous_state)s,
            %(new_state)s,
            %(reason_code)s,
            %(reason_text)s,
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
            "event_category": event_category,
            "event_type": event_type,
            "actor_id": actor.get("user_id"),
            "actor_role_snapshot": actor.get("role"),
            "target_type": target_type,
            "target_id": target_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason_code": None,
            "reason_text": reason_text,
            "request_id": request_context.get("request_id"),
            "diff_summary": diff_summary,
            "source_ref": request_context.get("request_id"),
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "event_payload": json.dumps(payload, ensure_ascii=True),
            "occurred_at": utc_now(),
        },
    )


def _build_source_registry_diff_summary(existing_row: dict[str, Any], prepared: dict[str, Any]) -> str:
    field_labels = {
        "bank_code": "Bank",
        "country_code": "Country",
        "product_type": "Product type",
        "product_key": "Product key",
        "source_name": "Source name",
        "source_url": "Source URL",
        "source_type": "Source type",
        "discovery_role": "Discovery role",
        "status": "Status",
        "priority": "Priority",
        "source_language": "Language",
        "purpose": "Purpose",
        "expected_fields": "Expected fields",
        "redirect_target_url": "Redirect target URL",
        "alias_urls": "Alias URLs",
        "discovery_metadata": "Discovery metadata",
        "change_reason": "Change reason",
    }
    changes: list[str] = []
    for field_name, label in field_labels.items():
        before = existing_row.get(field_name)
        after = prepared.get(field_name)
        if _normalize_comparable(before) == _normalize_comparable(after):
            continue
        changes.append(f"{label}: {format_diff_value(before)} -> {format_diff_value(after)}")
    if not changes:
        return f"Updated source registry item `{prepared['source_id']}` with no material field changes."
    return "; ".join(changes[:8])


def _normalize_comparable(value: Any) -> Any:
    if isinstance(value, list):
        return [str(item) for item in value]
    return value


def _registry_group_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["country_code"]),
        str(row["bank_code"]),
        str(row["product_type"]),
        str(row.get("source_language") or "en"),
    )


def _sort_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
        priority_text = str(row.get("priority") or "P9").upper()
        priority_rank = int(priority_text[1:]) if priority_text.startswith("P") and priority_text[1:].isdigit() else 99
        role_rank = _ROLE_PRIORITY.get(str(row.get("discovery_role")), 99)
        return priority_rank, role_rank, str(row["source_id"])

    return sorted(rows, key=sort_key)


def _build_collection_run_id(*, bank_code: str, product_type: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    suffix = new_id("src").split("_", 1)[1][:8]
    return f"run_{timestamp}_{bank_code.lower()}_{product_type}_collect_{suffix}"


def _required_text(value: Any, field_name: str) -> str:
    normalized = _optional_text(value)
    if not normalized:
        raise SourceRegistryError(status_code=422, code="required_field_missing", message=f"{field_name} is required.")
    return normalized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _normalize_search(value: str | None) -> str | None:
    normalized = _clean_text(value)
    return normalized.lower() if normalized else None


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [item for item in (_clean_text(entry) for entry in value) if item]
    normalized = str(value).replace("\r", "\n")
    parts = [segment.strip() for chunk in normalized.split("\n") for segment in chunk.split(",")]
    return [item for item in parts if item]


def _normalize_optional_url(value: Any) -> str | None:
    normalized = _optional_text(value)
    if not normalized:
        return None
    return normalize_source_url(normalized)


def _coerce_optional_timestamp(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    normalized = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SourceRegistryError(status_code=422, code="invalid_timestamp", message=f"Invalid timestamp value: {value}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _serialize_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def format_diff_value(value: Any) -> str:
    if value is None or value == "":
        return "empty"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "empty"
    return str(value)


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
