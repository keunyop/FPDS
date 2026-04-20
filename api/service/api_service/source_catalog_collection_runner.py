from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from api_service import source_collection_runner
from api_service.config import Settings
from api_service.db import open_connection
from api_service.source_catalog import _materialize_sources_for_catalog_item
from api_service.source_registry import _insert_collection_run_row, prepare_source_collection


def main() -> int:
    parser = argparse.ArgumentParser(description="Run background source-catalog collection plans.")
    parser.add_argument("--plan-path", type=Path, required=True, help="JSON plan file emitted by the admin API.")
    args = parser.parse_args()

    plan = json.loads(args.plan_path.read_text(encoding="utf-8"))
    for group in plan.get("groups", []):
        print(
            f"[source-catalog-runner] starting run {group['run_id']} for {group['bank_code']} {group['product_type']}",
            flush=True,
        )
        try:
            _run_group(plan=plan, group=group)
            print(
                f"[source-catalog-runner] finished run {group['run_id']}",
                flush=True,
            )
        except Exception as exc:  # pragma: no cover - defensive background-path handling
            print(
                f"[source-catalog-runner] failed run {group['run_id']}: {exc}",
                flush=True,
            )
            _mark_run_finished(
                run_id=str(group["run_id"]),
                run_state="failed",
                partial_completion_flag=True,
                error_summary=str(exc),
                run_metadata=_catalog_run_metadata(
                    plan=plan,
                    group=group,
                    discovery_status="materialization_failed",
                    discovery_notes=[str(exc)],
                    generated_source_ids=[],
                    collection_source_ids=[],
                    target_source_ids=[],
                ),
            )
    return 0


def _run_group(*, plan: dict[str, Any], group: dict[str, Any]) -> None:
    settings = Settings.from_env()
    collection_plan: dict[str, Any] | None = None
    collection_group: dict[str, Any] | None = None
    materialized_metadata: dict[str, Any] | None = None

    with open_connection(settings) as connection:
        materialized = _materialize_sources_for_catalog_item(
            connection,
            row={
                "catalog_item_id": group["catalog_item_id"],
                "bank_code": group["bank_code"],
                "bank_name": group["bank_name"],
                "country_code": group["country_code"],
                "product_type": group["product_type"],
                "homepage_url": group["homepage_url"],
                "normalized_homepage_url": group["normalized_homepage_url"],
                "source_language": group["source_language"],
            },
        )
        generated_rows = list(materialized.generated_rows)
        generated_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["status"]) != "removed"
        ]
        collection_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["discovery_role"]) != "entry" and str(item["status"]) != "removed"
        ]
        target_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["discovery_role"]) == "detail" and str(item["status"]) != "removed"
        ]
        if target_source_ids:
            discovery_status = "detail_sources_ready"
        else:
            preserved_scope = _load_active_collection_scope(
                connection,
                bank_code=str(group["bank_code"]),
                product_type=str(group["product_type"]),
            )
            if preserved_scope["target_source_ids"]:
                collection_source_ids = preserved_scope["collection_source_ids"]
                target_source_ids = preserved_scope["target_source_ids"]
                discovery_status = "preserved_existing_detail_scope"
            else:
                discovery_status = "no_detail_sources_discovered"
        materialized_metadata = _catalog_run_metadata(
            plan=plan,
            group=group,
            discovery_status=discovery_status,
            discovery_notes=list(materialized.discovery_notes),
            generated_source_ids=generated_source_ids,
            collection_source_ids=collection_source_ids,
            target_source_ids=target_source_ids,
        )

        if not target_source_ids:
            _mark_run_finished(
                connection=connection,
                run_id=str(group["run_id"]),
                run_state="completed",
                partial_completion_flag=True,
                error_summary="Homepage discovery produced no detail sources eligible for collection.",
                run_metadata=materialized_metadata,
            )
            return

        prepared = prepare_source_collection(
            connection,
            source_ids=collection_source_ids,
            actor=_actor_from_plan(plan),
            request_id=plan.get("request_id"),
            collection_id=str(plan["collection_id"]),
            correlation_id=str(plan["correlation_id"]),
            run_id_overrides={
                (
                    str(group["country_code"]),
                    str(group["bank_code"]),
                    str(group["product_type"]),
                    str(group["source_language"]),
                ): str(group["run_id"])
            },
        )
        collection_plan = prepared["plan"]
        collection_group = next(
            (item for item in collection_plan["groups"] if str(item["run_id"]) == str(group["run_id"])),
            None,
        )
        if collection_group is None:
            raise RuntimeError(f"Prepared collection group was not found for run {group['run_id']}.")

        _insert_collection_run_row(
            connection,
            run_id=str(collection_group["run_id"]),
            triggered_by=str(collection_plan["triggered_by"]),
            request_id=plan.get("request_id"),
            correlation_id=str(plan["correlation_id"]),
            collection_id=str(plan["collection_id"]),
            group=collection_group,
        )
        connection.execute(
            """
            UPDATE ingestion_run
            SET run_metadata = run_metadata || %(run_metadata)s::jsonb
            WHERE run_id = %(run_id)s
            """,
            {
                "run_id": str(group["run_id"]),
                "run_metadata": json.dumps(materialized_metadata, ensure_ascii=True),
            },
        )
        connection.commit()

    source_collection_runner._run_group(plan=collection_plan, group=collection_group)


def _load_active_collection_scope(connection: Any, *, bank_code: str, product_type: str) -> dict[str, list[str]]:
    rows = connection.execute(
        """
        SELECT
            source_id,
            discovery_role
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND product_type = %(product_type)s
          AND status = 'active'
        ORDER BY source_id
        """,
        {
            "bank_code": bank_code,
            "product_type": product_type,
        },
    ).fetchall()
    collection_source_ids = [
        str(row["source_id"])
        for row in rows
        if str(row["discovery_role"]) != "entry"
    ]
    target_source_ids = [
        str(row["source_id"])
        for row in rows
        if str(row["discovery_role"]) == "detail"
    ]
    return {
        "collection_source_ids": collection_source_ids,
        "target_source_ids": target_source_ids,
    }


def _catalog_run_metadata(
    *,
    plan: dict[str, Any],
    group: dict[str, Any],
    discovery_status: str,
    discovery_notes: list[str],
    generated_source_ids: list[str],
    collection_source_ids: list[str],
    target_source_ids: list[str],
) -> dict[str, Any]:
    return {
        "pipeline_stage": "source_catalog_collection",
        "collection_id": str(plan["collection_id"]),
        "correlation_id": str(plan["correlation_id"]),
        "request_id": plan.get("request_id"),
        "catalog_item_id": str(group["catalog_item_id"]),
        "bank_code": str(group["bank_code"]),
        "country_code": str(group["country_code"]),
        "product_type": str(group["product_type"]),
        "source_language": str(group["source_language"]),
        "discovery_status": discovery_status,
        "discovery_notes": discovery_notes,
        "generated_source_ids": generated_source_ids,
        "collection_source_ids": collection_source_ids,
        "target_source_ids": target_source_ids,
        "source_ids": collection_source_ids,
    }


def _actor_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    actor = plan.get("actor")
    if isinstance(actor, dict):
        return actor
    return {}


def _mark_run_finished(
    *,
    run_id: str,
    run_state: str,
    partial_completion_flag: bool,
    error_summary: str | None,
    run_metadata: dict[str, Any],
    connection: Any | None = None,
) -> None:
    if connection is None:
        settings = Settings.from_env()
        with open_connection(settings) as managed_connection:
            _mark_run_finished(
                connection=managed_connection,
                run_id=run_id,
                run_state=run_state,
                partial_completion_flag=partial_completion_flag,
                error_summary=error_summary,
                run_metadata=run_metadata,
            )
        return

    connection.execute(
        """
        UPDATE ingestion_run
        SET
            run_state = %(run_state)s,
            partial_completion_flag = %(partial_completion_flag)s,
            error_summary = %(error_summary)s,
            run_metadata = run_metadata || %(run_metadata)s::jsonb,
            completed_at = %(completed_at)s
        WHERE run_id = %(run_id)s
        """,
        {
            "run_id": run_id,
            "run_state": run_state,
            "partial_completion_flag": partial_completion_flag,
            "error_summary": error_summary,
            "run_metadata": json.dumps(run_metadata, ensure_ascii=True),
            "completed_at": datetime.now(UTC),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
