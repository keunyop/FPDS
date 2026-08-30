from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from api_service import source_collection_runner
from api_service.config import Settings
from api_service.db import open_connection
from api_service.source_catalog import (
    CatalogItemMaterializationResult,
    _canonical_product_type_code,
    _has_unrelated_product_type_signal,
    _materialize_sources_for_catalog_item,
    _product_type_scope_codes,
    _record_catalog_audit_event,
    _url_country_scope_conflicts,
    _url_locale_conflicts_source_language,
    repair_catalog_coverage_route,
)
from api_service.source_registry import (
    _insert_collection_run_row,
    _is_candidate_producing_collection_source,
    prepare_source_collection,
)


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
            _mark_run_failure_best_effort(
                run_id=str(group["run_id"]),
                run_metadata=_catalog_run_metadata(
                    plan=plan,
                    group=group,
                    discovery_status="materialization_failed",
                    discovery_notes=[str(exc)],
                    generated_source_ids=[],
                    collection_source_ids=[],
                    target_source_ids=[],
                    failure=exc,
                ),
                failure=exc,
            )
    return 0


def _mark_run_failure_best_effort(
    *,
    run_id: str,
    run_metadata: dict[str, Any],
    failure: Exception,
) -> None:
    """Keep the multi-group runner alive when failure persistence is unavailable."""

    try:
        _mark_run_finished(
            run_id=run_id,
            run_state="failed",
            partial_completion_flag=True,
            error_summary=str(failure),
            run_metadata=run_metadata,
        )
    except Exception as persistence_error:  # pragma: no cover - last-resort background resilience
        print(
            f"[source-catalog-runner] could not persist failure for {run_id}: {persistence_error}",
            flush=True,
        )


def _no_detail_result_is_structural(discovery_notes: list[str]) -> bool:
    normalized = " ".join(str(note).strip().lower() for note in discovery_notes if str(note).strip())
    transient_markers = (
        "timed out",
        "timeout",
        "fetch was unavailable",
        "could not resolve",
        "connection reset",
        "temporary",
        "http 408",
        "http 425",
        "http 429",
        "http 500",
        "http 502",
        "http 503",
        "http 504",
    )
    if any(marker in normalized for marker in transient_markers):
        return False
    return any(
        marker in normalized
        for marker in (
            "detail rejection summary",
            "candidate validation did not promote",
            "no candidate-producing detail sources",
            "no detail sources",
        )
    )


def _quarantine_catalog_scope_after_no_detail(
    connection: Any,
    *,
    plan: dict[str, Any],
    group: dict[str, Any],
    discovery_notes: list[str],
) -> dict[str, Any]:
    quarantined_at = datetime.now(UTC)
    run_id = str(group["run_id"])
    quarantine_metadata = {
        "status": "quarantined",
        "reason": "structural_zero_detail_collection_result",
        "run_id": run_id,
        "quarantined_at": quarantined_at.isoformat(),
        "not_currently_offered_asserted": False,
        "reactivation_requirement": "verified_coverage_route_or_active_detail_source",
    }
    connection.execute(
        """
        UPDATE source_registry_catalog_item
        SET
            status = 'inactive',
            coverage_source_metadata = COALESCE(coverage_source_metadata, '{}'::jsonb)
                || %(quarantine_metadata)s::jsonb,
            change_reason = 'structural_zero_detail_scope_quarantined:' || %(run_id)s,
            updated_at = %(updated_at)s
        WHERE catalog_item_id = %(catalog_item_id)s
          AND bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND status = 'active'
        """,
        {
            "quarantine_metadata": json.dumps(
                {"collection_eligibility": quarantine_metadata},
                ensure_ascii=True,
            ),
            "run_id": run_id,
            "updated_at": quarantined_at,
            "catalog_item_id": str(group["catalog_item_id"]),
            "bank_code": str(group["bank_code"]),
            "country_code": str(group["country_code"]),
            "product_type_scope": _product_type_scope_codes(str(group["product_type"])),
        },
    )
    connection.execute(
        """
        UPDATE source_registry_item
        SET
            status = 'inactive',
            change_reason = 'catalog_scope_quarantined_after_zero_detail:' || %(run_id)s,
            updated_at = %(updated_at)s
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND status = 'active'
        """,
        {
            "run_id": run_id,
            "updated_at": quarantined_at,
            "bank_code": str(group["bank_code"]),
            "country_code": str(group["country_code"]),
            "product_type_scope": _product_type_scope_codes(str(group["product_type"])),
        },
    )
    _record_catalog_audit_event(
        connection,
        actor=_actor_from_plan(plan),
        request_context={"request_id": plan.get("request_id")},
        event_type="source_catalog_scope_quarantined",
        target_id=str(group["catalog_item_id"]),
        target_type="source_registry_catalog_item",
        diff_summary=(
            "Inactivated a catalog scope after structural discovery produced no "
            "candidate-producing detail source."
        ),
        metadata={
            "bank_code": str(group["bank_code"]),
            "country_code": str(group["country_code"]),
            "product_type": str(group["product_type"]),
            "run_id": run_id,
            "discovery_notes": discovery_notes[:8],
            **quarantine_metadata,
        },
    )
    return quarantine_metadata


def _run_group(*, plan: dict[str, Any], group: dict[str, Any]) -> None:
    source_catalog_product_type = str(group.get("source_catalog_product_type") or group["product_type"])
    group = {
        **group,
        "product_type": _canonical_product_type_code(group["product_type"]),
        "source_catalog_product_type": source_catalog_product_type,
    }
    group["product_family"] = _catalog_product_family(group)
    settings = Settings.from_env()
    collection_plan: dict[str, Any] | None = None
    collection_group: dict[str, Any] | None = None
    materialized_metadata: dict[str, Any] | None = None

    with open_connection(settings) as connection:
        _insert_collection_run_row(
            connection,
            run_id=str(group["run_id"]),
            triggered_by=str(plan.get("triggered_by", "admin")),
            request_id=plan.get("request_id"),
            correlation_id=str(plan["correlation_id"]),
            collection_id=str(plan["collection_id"]),
            group=_run_group_with_empty_collection_scope(group),
            pipeline_stage="source_catalog_collection",
            trigger_type="admin_source_collection",
        )
        catalog_row = {
            "catalog_item_id": group["catalog_item_id"],
            "bank_code": group["bank_code"],
            "bank_name": group["bank_name"],
            "country_code": group["country_code"],
            "product_type": group["product_type"],
            "homepage_url": group["homepage_url"],
            "normalized_homepage_url": group["normalized_homepage_url"],
            "coverage_source_url": group.get("coverage_source_url"),
            "coverage_source_metadata": group.get("coverage_source_metadata") or {},
            "source_language": group["source_language"],
        }
        requested_coverage_mode = str(group.get("source_coverage_mode") or "precision")
        has_completed_collection = bool(group.get("has_completed_collection", False))
        source_coverage_mode = (
            requested_coverage_mode
            if has_completed_collection or requested_coverage_mode != "standard"
            else "precision"
        )
        group["source_coverage_mode"] = source_coverage_mode
        existing_scope_before_repair: dict[str, list[str]] | None = None
        if source_coverage_mode == "standard":
            existing_scope_before_repair = _load_active_collection_scope(
                connection,
                bank_code=str(group["bank_code"]),
                country_code=str(group["country_code"]),
                product_type=str(group["product_type"]),
                source_language=str(group["source_language"]),
            )
        if (
            source_coverage_mode == "standard"
            and existing_scope_before_repair
            and existing_scope_before_repair["target_source_ids"]
        ):
            materialized = CatalogItemMaterializationResult(
                generated_rows=[],
                discovery_notes=[
                    "Precision source rediscovery was skipped by operator choice; collection reused the current active source scope."
                ],
                detail_source_ids=[],
                discovery_metrics={
                    "mode": "standard",
                    "reused_collection_source_count": len(existing_scope_before_repair["collection_source_ids"]),
                    "reused_detail_source_count": len(existing_scope_before_repair["target_source_ids"]),
                },
            )
        else:
            if source_coverage_mode == "standard":
                source_coverage_mode = "precision_fallback"
                group["source_coverage_mode"] = source_coverage_mode
            materialized = _materialize_sources_for_catalog_item(
                connection,
                row=catalog_row,
                run_id=str(group["run_id"]),
                correlation_id=str(plan["correlation_id"]),
                request_id=plan.get("request_id"),
            )
            initial_discovery_notes = list(materialized.discovery_notes)
            if source_coverage_mode == "precision_fallback":
                initial_discovery_notes.insert(
                    0,
                    "The completed collection no longer had an active detail source, so precision source rediscovery was forced.",
                )
            existing_scope_before_repair = _load_active_collection_scope(
                connection,
                bank_code=str(group["bank_code"]),
                country_code=str(group["country_code"]),
                product_type=str(group["product_type"]),
                source_language=str(group["source_language"]),
            )
            if source_coverage_mode == "precision_fallback":
                materialized = type(materialized)(
                    generated_rows=materialized.generated_rows,
                    discovery_notes=_dedupe_preserve_order(initial_discovery_notes),
                    detail_source_ids=materialized.detail_source_ids,
                    model_execution_records=materialized.model_execution_records,
                    usage_records=materialized.usage_records,
                    discovery_metrics=materialized.discovery_metrics,
                )
            if not materialized.detail_source_ids and not existing_scope_before_repair["target_source_ids"]:
                repair = repair_catalog_coverage_route(
                    connection,
                    row=catalog_row,
                    actor=_actor_from_plan(plan),
                    request_context={"request_id": plan.get("request_id")},
                    run_id=str(group["run_id"]),
                    correlation_id=str(plan["correlation_id"]),
                )
                initial_discovery_notes.extend(repair.notes)
                if repair.status == "current_offering" and repair.coverage_source_url:
                    catalog_row = {
                        **catalog_row,
                        "coverage_source_url": repair.coverage_source_url,
                        "coverage_source_metadata": repair.coverage_source_metadata,
                    }
                    materialized = _materialize_sources_for_catalog_item(
                        connection,
                        row=catalog_row,
                        run_id=str(group["run_id"]),
                        correlation_id=str(plan["correlation_id"]),
                        request_id=plan.get("request_id"),
                    )
                    materialized = type(materialized)(
                        generated_rows=materialized.generated_rows,
                        discovery_notes=_dedupe_preserve_order(
                            [*initial_discovery_notes, *materialized.discovery_notes]
                        ),
                        detail_source_ids=materialized.detail_source_ids,
                        model_execution_records=materialized.model_execution_records,
                        usage_records=materialized.usage_records,
                        discovery_metrics=materialized.discovery_metrics,
                    )
                elif repair.status == "not_currently_offered":
                    materialized_metadata = _catalog_run_metadata(
                        plan=plan,
                        group=group,
                        discovery_status="product_not_currently_offered",
                        discovery_notes=_dedupe_preserve_order(initial_discovery_notes),
                        generated_source_ids=[],
                        collection_source_ids=[],
                        target_source_ids=[],
                        coverage_metrics=materialized.discovery_metrics,
                    )
                    _mark_run_finished(
                        connection=connection,
                        run_id=str(group["run_id"]),
                        run_state="completed",
                        partial_completion_flag=False,
                        error_summary=None,
                        run_metadata=materialized_metadata,
                    )
                    return
                else:
                    materialized = type(materialized)(
                        generated_rows=materialized.generated_rows,
                        discovery_notes=_dedupe_preserve_order(initial_discovery_notes),
                        detail_source_ids=materialized.detail_source_ids,
                        model_execution_records=materialized.model_execution_records,
                        usage_records=materialized.usage_records,
                        discovery_metrics=materialized.discovery_metrics,
                    )
        discovery_notes = list(materialized.discovery_notes)
        generated_rows = list(materialized.generated_rows)
        generated_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if str(item["status"]) != "removed"
        ]
        collection_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if (
                str(item["discovery_role"]) != "entry"
                or _is_candidate_producing_source(item, product_type=str(group["product_type"]))
            )
            and str(item["status"]) != "removed"
            and not _url_country_scope_conflicts(
                country_code=str(group["country_code"]),
                normalized_url=str(item.get("normalized_url") or item.get("source_url") or ""),
            )
            and not _url_locale_conflicts_source_language(
                normalized_url=str(item.get("normalized_url") or item.get("source_url") or ""),
                source_language=str(group["source_language"]),
            )
        ]
        target_source_ids = [
            str(item["source_id"])
            for item in generated_rows
            if _is_candidate_producing_source(item, product_type=str(group["product_type"]))
            and str(item["status"]) != "removed"
            and not _url_country_scope_conflicts(
                country_code=str(group["country_code"]),
                normalized_url=str(item.get("normalized_url") or item.get("source_url") or ""),
            )
            and not _url_locale_conflicts_source_language(
                normalized_url=str(item.get("normalized_url") or item.get("source_url") or ""),
                source_language=str(group["source_language"]),
            )
        ]
        generated_target_source_ids = list(target_source_ids)
        active_scope = (
            existing_scope_before_repair
            if source_coverage_mode == "standard" and existing_scope_before_repair
            else _load_active_collection_scope(
                connection,
                bank_code=str(group["bank_code"]),
                country_code=str(group["country_code"]),
                product_type=str(group["product_type"]),
                source_language=str(group["source_language"]),
            )
        )
        collection_source_ids = _dedupe_preserve_order(
            [*collection_source_ids, *target_source_ids, *active_scope["collection_source_ids"]]
        )
        target_source_ids = _dedupe_preserve_order(
            [*target_source_ids, *active_scope["target_source_ids"]]
        )
        if generated_target_source_ids:
            discovery_status = "detail_sources_ready"
        else:
            if active_scope["target_source_ids"]:
                collection_source_ids = active_scope["collection_source_ids"]
                target_source_ids = active_scope["target_source_ids"]
                discovery_status = (
                    "reused_existing_detail_scope"
                    if source_coverage_mode == "standard"
                    else "preserved_existing_detail_scope"
                )
            else:
                discovery_status = "no_detail_sources_discovered"
        materialized_metadata = _catalog_run_metadata(
            plan=plan,
            group=group,
            discovery_status=discovery_status,
            discovery_notes=discovery_notes,
            generated_source_ids=generated_source_ids,
            collection_source_ids=collection_source_ids,
            target_source_ids=target_source_ids,
            coverage_metrics=materialized.discovery_metrics,
        )

        if not target_source_ids:
            if _no_detail_result_is_structural(discovery_notes):
                materialized_metadata = {
                    **materialized_metadata,
                    "catalog_scope_quarantine": _quarantine_catalog_scope_after_no_detail(
                        connection,
                        plan=plan,
                        group=group,
                        discovery_notes=discovery_notes,
                    ),
                }
            _mark_run_finished(
                connection=connection,
                run_id=str(group["run_id"]),
                run_state="completed",
                partial_completion_flag=True,
                error_summary=_no_detail_sources_summary(discovery_notes),
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


def _load_active_collection_scope(
    connection: Any,
    *,
    bank_code: str,
    country_code: str,
    product_type: str,
    source_language: str,
) -> dict[str, list[str]]:
    product_type = _canonical_product_type_code(product_type)
    rows = connection.execute(
        """
        SELECT
            source_id,
            discovery_role,
            source_name,
            source_url,
            purpose,
            expected_fields
        FROM source_registry_item
        WHERE bank_code = %(bank_code)s
          AND country_code = %(country_code)s
          AND product_type = ANY(%(product_type_scope)s)
          AND status = 'active'
        ORDER BY source_id
        """,
        {
            "bank_code": bank_code,
            "country_code": country_code,
            "product_type_scope": _product_type_scope_codes(product_type),
        },
    ).fetchall()
    collection_source_ids = [
        str(row["source_id"])
        for row in rows
        if str(row["discovery_role"]) != "entry" or _is_candidate_producing_source(row, product_type=product_type)
        if _source_matches_active_product_scope(
            row,
            product_type=product_type,
            country_code=country_code,
            source_language=source_language,
        )
    ]
    target_source_ids = [
        str(row["source_id"])
        for row in rows
        if _is_candidate_producing_source(row, product_type=product_type)
        and _source_matches_active_product_scope(
            row,
            product_type=product_type,
            country_code=country_code,
            source_language=source_language,
        )
    ]
    return {
        "collection_source_ids": collection_source_ids,
        "target_source_ids": target_source_ids,
    }


def _source_matches_active_product_scope(
    row: Any,
    *,
    product_type: str,
    country_code: str,
    source_language: str,
) -> bool:
    normalized_row = dict(row) if not isinstance(row, dict) else row
    source_url = str(normalized_row.get("source_url") or "")
    if _url_country_scope_conflicts(
        country_code=country_code,
        normalized_url=source_url,
    ):
        return False
    if _url_locale_conflicts_source_language(
        normalized_url=source_url,
        source_language=source_language,
    ):
        return False
    fingerprint = " ".join(
        str(normalized_row.get(key) or "")
        for key in ("source_url", "source_name", "purpose")
    ).lower()
    return not _has_unrelated_product_type_signal(
        product_type=product_type,
        fingerprint=fingerprint,
    )


def _is_candidate_producing_source(row: Any, *, product_type: str) -> bool:
    del product_type
    normalized_row = dict(row) if not isinstance(row, dict) else row
    return _is_candidate_producing_collection_source(normalized_row)


def _no_detail_sources_summary(discovery_notes: list[str]) -> str:
    base = "Homepage discovery produced no detail sources eligible for collection."
    notable_notes = [
        str(note).strip()
        for note in discovery_notes
        if str(note).strip()
        and "Existing active detail sources were preserved" not in str(note)
    ]
    if not notable_notes:
        return base
    priority_prefixes = (
        "Detail rejection summary:",
        "Rejected detail ",
        "Homepage discovery candidate validation rejected all tentative detail pages.",
    )
    decisive_notes = [
        note
        for prefix in priority_prefixes
        for note in notable_notes
        if note.startswith(prefix)
    ]
    selected_notes = _dedupe_preserve_order(decisive_notes)[:2] or notable_notes[:1]
    return f"{base} {' '.join(selected_notes)}"


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _run_group_with_empty_collection_scope(group: dict[str, Any]) -> dict[str, Any]:
    return {
        **group,
        "selected_source_ids": list(group.get("selected_source_ids") or []),
        "included_source_ids": list(group.get("included_source_ids") or []),
        "target_source_ids": list(group.get("target_source_ids") or []),
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
    failure: BaseException | None = None,
    coverage_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "pipeline_stage": "source_catalog_collection",
        "collection_id": str(plan["collection_id"]),
        "correlation_id": str(plan["correlation_id"]),
        "request_id": plan.get("request_id"),
        "catalog_item_id": str(group["catalog_item_id"]),
        "bank_code": str(group["bank_code"]),
        "country_code": str(group["country_code"]),
        "product_type": str(group["product_type"]),
        "product_family": _catalog_product_family(group),
        "source_language": str(group["source_language"]),
        "has_completed_collection": bool(group.get("has_completed_collection", False)),
        "source_coverage_mode": str(group.get("source_coverage_mode") or "precision"),
        "precision_rediscovery_requested": bool(plan.get("precision_rediscovery_requested", False)),
        "discovery_status": discovery_status,
        "discovery_notes": discovery_notes,
        "generated_source_ids": generated_source_ids,
        "collection_source_ids": collection_source_ids,
        "target_source_ids": target_source_ids,
        "source_ids": collection_source_ids,
        "source_coverage_metrics": coverage_metrics or {},
    }
    if failure is not None:
        metadata.update(source_collection_runner._stage_failure_metadata(failure))
    return metadata


def _actor_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    actor = plan.get("actor")
    if isinstance(actor, dict):
        return actor
    return {}


def _catalog_product_family(group: dict[str, Any]) -> str:
    explicit = str(group.get("product_family") or "").strip().lower().replace("_", "-")
    if explicit in {"deposit", "lending"}:
        return explicit
    product_type = _canonical_product_type_code(group.get("product_type") or "")
    if product_type in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        return "lending"
    if any(token in product_type for token in ("credit-card", "mortgage", "loan", "line-of-credit", "heloc")):
        return "lending"
    return "deposit"


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
