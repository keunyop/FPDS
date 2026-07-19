from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

from api_service.aggregate_refresh import launch_aggregate_refresh_runner
from api_service.candidate_auto_promotion import promote_auto_validated_candidates
from api_service.config import Settings
from api_service.db import open_connection
from api_service.security import new_id

REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DB-backed source collection plans.")
    parser.add_argument("--plan-path", type=Path, required=True, help="JSON plan file emitted by the admin API.")
    args = parser.parse_args()

    plan = json.loads(args.plan_path.read_text(encoding="utf-8"))
    for group in plan.get("groups", []):
        try:
            _run_group(plan=plan, group=group)
        except Exception as exc:  # pragma: no cover - defensive background-path handling
            _mark_run_failed(run_id=str(group["run_id"]), stage_name="source_collection", error_summary=str(exc))
    return 0


def _run_group(*, plan: dict[str, Any], group: dict[str, Any]) -> None:
    temp_dir = args_temp_dir(plan_path=None)
    temp_dir.mkdir(parents=True, exist_ok=True)
    registry_path = temp_dir / f"{group['run_id']}.registry.json"
    registry_path.write_text(json.dumps(_build_registry_payload(group), indent=2, ensure_ascii=True), encoding="utf-8")

    run_id = str(group["run_id"])
    env_file = _resolve_env_file()
    trigger_type = str(plan.get("trigger_type", "admin_source_collection"))
    triggered_by = str(plan.get("triggered_by", "admin"))
    base_args = ["--run-id", run_id, "--registry-path", str(registry_path), "--persist-db", "--trigger-type", trigger_type, "--triggered-by", triggered_by]
    if env_file is not None:
        base_args.extend(["--env-file", str(env_file)])
    if plan.get("correlation_id"):
        base_args.extend(["--correlation-id", str(plan["correlation_id"])])
    if plan.get("request_id"):
        base_args.extend(["--request-id", str(plan["request_id"])])

    included_source_ids = [str(item) for item in group.get("included_source_ids", [])]
    target_source_ids = [str(item) for item in group.get("target_source_ids", [])]

    print(
        f"[source-collection-runner] run {run_id} starting snapshot for {len(included_source_ids)} source(s)",
        flush=True,
    )
    snapshot_output = _run_stage("worker.discovery.fpds_snapshot", base_args + _source_args(included_source_ids))
    successful_source_ids = _successful_source_ids(snapshot_output)
    if not successful_source_ids:
        raise RuntimeError("Snapshot capture failed for all selected sources.")

    successful_target_source_ids = _filter_requested_source_ids(
        requested_source_ids=target_source_ids,
        successful_source_ids=successful_source_ids,
    )
    successful_target_source_ids, duplicate_target_source_ids = _dedupe_target_sources_by_snapshot_checksum(
        snapshot_output=snapshot_output,
        target_source_ids=successful_target_source_ids,
    )
    if duplicate_target_source_ids:
        print(
            (
                f"[source-collection-runner] run {run_id} skipped {len(duplicate_target_source_ids)} "
                "duplicate target source(s) with byte-identical snapshots"
            ),
            flush=True,
        )
    if not successful_target_source_ids:
        raise RuntimeError("Snapshot capture produced no target sources eligible for normalization.")

    print(
        f"[source-collection-runner] run {run_id} continuing with {len(successful_source_ids)} successful snapshot source(s)",
        flush=True,
    )
    parse_output = _run_stage("worker.pipeline.fpds_parse_chunk", base_args + _source_args(successful_source_ids))
    parse_successful_source_ids = _successful_stage_source_ids(
        stage_output=parse_output,
        action_field="parse_action",
        success_actions={"stored", "reused"},
    )
    if not parse_successful_source_ids:
        raise RuntimeError("Parse/chunk failed for all successful snapshot sources.")

    parse_successful_target_source_ids = _filter_requested_source_ids(
        requested_source_ids=successful_target_source_ids,
        successful_source_ids=parse_successful_source_ids,
    )
    if not parse_successful_target_source_ids:
        raise RuntimeError("Parse/chunk produced no target sources eligible for extraction.")

    extraction_output = _run_stage("worker.pipeline.fpds_extraction", base_args + _source_args(parse_successful_source_ids))
    extraction_successful_source_ids = _successful_stage_source_ids(
        stage_output=extraction_output,
        action_field="extraction_action",
        success_actions={"stored"},
    )
    if not extraction_successful_source_ids:
        raise RuntimeError("Extraction failed for all parsed sources.")

    extraction_successful_target_source_ids = _filter_requested_source_ids(
        requested_source_ids=parse_successful_target_source_ids,
        successful_source_ids=extraction_successful_source_ids,
    )
    if not extraction_successful_target_source_ids:
        raise RuntimeError("Extraction produced no target sources eligible for normalization.")

    normalization_output = _run_stage(
        "worker.pipeline.fpds_normalization",
        base_args + _source_args(extraction_successful_target_source_ids),
    )
    normalization_successful_target_source_ids = _successful_stage_source_ids(
        stage_output=normalization_output,
        action_field="normalization_action",
        success_actions={"stored"},
    )
    if not normalization_successful_target_source_ids:
        raise RuntimeError("Normalization failed for all extracted target sources.")

    validation_output = _run_stage(
        "worker.pipeline.fpds_validation_routing",
        base_args + ["--routing-mode", "phase1"] + _source_args(normalization_successful_target_source_ids),
    )
    validation_successful_target_source_ids = _successful_stage_source_ids(
        stage_output=validation_output,
        action_field="validation_action",
        success_actions={"review_queued", "auto_validated"},
    )
    superseded_review_count = _supersede_stale_logical_reviews_for_run(run_id=run_id, plan=plan)
    if superseded_review_count:
        print(
            f"[source-collection-runner] run {run_id} superseded {superseded_review_count} older logical duplicate review(s)",
            flush=True,
        )
    run_summary = _build_end_to_end_source_summary(
        included_source_ids=included_source_ids,
        target_source_ids=target_source_ids,
        duplicate_target_source_ids=duplicate_target_source_ids,
        extraction_successful_source_ids=extraction_successful_source_ids,
        validation_successful_target_source_ids=validation_successful_target_source_ids,
    )
    _persist_end_to_end_source_summary(run_id=run_id, summary=run_summary)
    promotion_result = _promote_auto_validated_candidates_for_run(run_id=run_id, plan=plan)
    if promotion_result["promoted_count"]:
        launch_result = launch_aggregate_refresh_runner()
        print(
            (
                f"[source-collection-runner] run {run_id} auto-promoted "
                f"{promotion_result['promoted_count']} candidate(s); aggregate refresh launch={launch_result['launched']}"
            ),
            flush=True,
        )
    print(f"[source-collection-runner] run {run_id} completed downstream stages", flush=True)


def _run_stage(module_name: str, args: list[str]) -> dict[str, Any]:
    command = _build_worker_command(module_name, args)
    stage_name = module_name.rsplit(".", 1)[-1]
    timeout_seconds = _stage_timeout_seconds_from_env()
    print(f"[source-collection-runner] launching stage {stage_name} with timeout {timeout_seconds}s", flush=True)
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        if exc.stdout:
            print(exc.stdout, end="")
        if exc.stderr:
            print(exc.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"{stage_name} timed out after {timeout_seconds} seconds.") from exc
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"{stage_name} failed with exit code {completed.returncode}.")
    stdout = completed.stdout.strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


def _build_worker_command(module_name: str, args: list[str]) -> list[str]:
    uv_executable = shutil.which("uv")
    if not uv_executable:
        raise RuntimeError("`uv` is required to launch worker stages from the source collection runner.")
    return [uv_executable, "run", "--project", str(REPO_ROOT), "python", "-m", module_name, *args]


def _promote_auto_validated_candidates_for_run(*, run_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        return promote_auto_validated_candidates(
            connection,
            run_id=run_id,
            request_context={"request_id": plan.get("request_id")},
        )


def _stage_timeout_seconds_from_env() -> int:
    import os

    raw = os.getenv("FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS", "1800").strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return 1800


def _successful_source_ids(snapshot_output: dict[str, Any]) -> list[str]:
    return _successful_stage_source_ids(
        stage_output=snapshot_output,
        action_field="snapshot_action",
        success_actions={"stored", "reused"},
    )


def _successful_stage_source_ids(
    *,
    stage_output: dict[str, Any],
    action_field: str,
    success_actions: set[str],
) -> list[str]:
    source_ids: list[str] = []
    seen: set[str] = set()
    for item in stage_output.get("source_results", []):
        source_id = str(item.get("source_id") or "")
        if str(item.get(action_field)) in success_actions and source_id and source_id not in seen:
            source_ids.append(source_id)
            seen.add(source_id)
    return source_ids


def _filter_requested_source_ids(*, requested_source_ids: list[str], successful_source_ids: list[str]) -> list[str]:
    successful_source_id_set = set(successful_source_ids)
    return [source_id for source_id in requested_source_ids if source_id in successful_source_id_set]


def _dedupe_target_sources_by_snapshot_checksum(
    *,
    snapshot_output: dict[str, Any],
    target_source_ids: list[str],
) -> tuple[list[str], list[str]]:
    """Keep one normalization target per byte-identical snapshot.

    Supporting sources still pass through parse and extraction. Targets without a
    checksum are retained because equivalence cannot be proven safely.
    """
    target_set = set(target_source_ids)
    checksum_by_source_id = {
        str(item.get("source_id")): str(item.get("checksum") or "").strip()
        for item in snapshot_output.get("source_results", [])
        if str(item.get("source_id") or "") in target_set
    }
    retained: list[str] = []
    duplicates: list[str] = []
    seen_checksums: set[str] = set()
    for source_id in target_source_ids:
        checksum = checksum_by_source_id.get(source_id, "")
        if checksum and checksum in seen_checksums:
            duplicates.append(source_id)
            continue
        retained.append(source_id)
        if checksum:
            seen_checksums.add(checksum)
    return retained, duplicates


def _build_end_to_end_source_summary(
    *,
    included_source_ids: list[str],
    target_source_ids: list[str],
    duplicate_target_source_ids: list[str],
    extraction_successful_source_ids: list[str],
    validation_successful_target_source_ids: list[str],
) -> dict[str, Any]:
    included_set = set(included_source_ids)
    target_set = set(target_source_ids)
    duplicate_set = set(duplicate_target_source_ids)
    supporting_set = included_set - target_set
    successful_set = (
        (supporting_set & set(extraction_successful_source_ids))
        | (target_set & set(validation_successful_target_source_ids))
        | duplicate_set
    )
    failed_source_ids = sorted(included_set - successful_set)
    success_count = len(included_set) - len(failed_source_ids)
    failure_count = len(failed_source_ids)
    error_summary = None
    if failure_count:
        error_summary = (
            f"{failure_count} of {len(included_set)} collection source(s) did not reach their required terminal stage."
        )
    return {
        "source_scope_count": len(included_set),
        "source_success_count": success_count,
        "source_failure_count": failure_count,
        "partial_completion_flag": failure_count > 0,
        "error_summary": error_summary,
        "failed_source_ids": failed_source_ids,
        "deduplicated_target_source_ids": sorted(duplicate_set),
    }


def _persist_end_to_end_source_summary(*, run_id: str, summary: dict[str, Any]) -> None:
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        connection.execute(
            """
            UPDATE ingestion_run
            SET
                run_state = CASE WHEN %(source_success_count)s = 0 THEN 'failed' ELSE 'completed' END,
                source_scope_count = %(source_scope_count)s,
                source_success_count = %(source_success_count)s,
                source_failure_count = %(source_failure_count)s,
                partial_completion_flag = %(partial_completion_flag)s,
                error_summary = %(error_summary)s,
                run_metadata = run_metadata || %(run_metadata)s::jsonb,
                completed_at = %(completed_at)s
            WHERE run_id = %(run_id)s
            """,
            {
                "run_id": run_id,
                "source_scope_count": summary["source_scope_count"],
                "source_success_count": summary["source_success_count"],
                "source_failure_count": summary["source_failure_count"],
                "partial_completion_flag": summary["partial_completion_flag"],
                "error_summary": summary["error_summary"],
                "run_metadata": json.dumps({"end_to_end_source_summary": summary}, ensure_ascii=True, sort_keys=True),
                "completed_at": datetime.now(UTC),
            },
        )


def _supersede_stale_logical_reviews_for_run(*, run_id: str, plan: dict[str, Any]) -> int:
    """Leave one active task per exact logical product after a newer rerun.

    This only coalesces detail-source tasks with the same bank, family, type, and
    product name. It does not approve or reject the product proposal itself.
    """
    decided_at = datetime.now(UTC)
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        stale_rows = connection.execute(
            """
            WITH newest AS (
                SELECT DISTINCT ON (
                    nc.country_code,
                    nc.bank_code,
                    nc.product_family,
                    nc.product_type,
                    lower(nc.product_name)
                )
                    nc.candidate_id,
                    nc.country_code,
                    nc.bank_code,
                    nc.product_family,
                    nc.product_type,
                    lower(nc.product_name) AS normalized_product_name,
                    nc.created_at
                FROM normalized_candidate AS nc
                JOIN review_task AS rt
                  ON rt.candidate_id = nc.candidate_id
                JOIN source_document AS sd
                  ON sd.source_document_id = nc.source_document_id
                WHERE nc.run_id = %(run_id)s
                  AND rt.review_state IN ('queued', 'deferred')
                  AND COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') = 'detail'
                ORDER BY
                    nc.country_code,
                    nc.bank_code,
                    nc.product_family,
                    nc.product_type,
                    lower(nc.product_name),
                    nc.created_at DESC,
                    nc.candidate_id DESC
            ),
            stale AS (
                SELECT
                    nc.candidate_id,
                    nc.run_id,
                    nc.candidate_state AS previous_candidate_state,
                    rt.review_task_id,
                    rt.review_state AS previous_review_state,
                    newest.candidate_id AS replacement_candidate_id
                FROM newest
                JOIN normalized_candidate AS nc
                  ON nc.country_code = newest.country_code
                 AND nc.bank_code = newest.bank_code
                 AND nc.product_family = newest.product_family
                 AND nc.product_type = newest.product_type
                 AND lower(nc.product_name) = newest.normalized_product_name
                 AND (
                    nc.created_at < newest.created_at
                    OR (nc.created_at = newest.created_at AND nc.candidate_id < newest.candidate_id)
                 )
                JOIN review_task AS rt
                  ON rt.candidate_id = nc.candidate_id
                JOIN source_document AS sd
                  ON sd.source_document_id = nc.source_document_id
                WHERE rt.review_state IN ('queued', 'deferred')
                  AND nc.candidate_state = 'in_review'
                  AND COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') = 'detail'
                FOR UPDATE OF nc, rt
            ),
            superseded_candidates AS (
                UPDATE normalized_candidate AS nc
                SET
                    candidate_state = 'superseded',
                    review_reason_code = 'superseded_by_newer_logical_candidate',
                    updated_at = %(decided_at)s
                FROM stale
                WHERE nc.candidate_id = stale.candidate_id
                RETURNING nc.candidate_id
            ),
            resolved_reviews AS (
                UPDATE review_task AS rt
                SET
                    review_state = 'rejected',
                    queue_reason_code = 'superseded_by_newer_logical_candidate',
                    updated_at = %(decided_at)s
                FROM stale
                WHERE rt.review_task_id = stale.review_task_id
                RETURNING rt.review_task_id
            )
            SELECT stale.*
            FROM stale
            JOIN superseded_candidates USING (candidate_id)
            JOIN resolved_reviews USING (review_task_id)
            ORDER BY stale.review_task_id
            """,
            {"run_id": run_id, "decided_at": decided_at},
        ).fetchall()
        for stale in stale_rows:
            connection.execute(
                """
                INSERT INTO audit_event (
                    audit_event_id, event_category, event_type, actor_type,
                    target_type, target_id, previous_state, new_state,
                    reason_code, reason_text, run_id, candidate_id,
                    review_task_id, request_id, diff_summary, source_ref,
                    event_payload, occurred_at
                )
                VALUES (
                    %(audit_event_id)s, 'review', 'stale_review_auto_superseded', 'system',
                    'review_task', %(review_task_id)s, %(previous_state)s, 'rejected',
                    'superseded_by_newer_logical_candidate',
                    'A newer detail-source candidate represents the same bank, product type, and product name.',
                    %(stale_run_id)s, %(candidate_id)s, %(review_task_id)s,
                    %(request_id)s, 'Resolved an older logical duplicate review task.',
                    %(request_id)s, %(event_payload)s::jsonb, %(occurred_at)s
                )
                """,
                {
                    "audit_event_id": new_id("audit"),
                    "review_task_id": str(stale["review_task_id"]),
                    "previous_state": str(stale["previous_review_state"]),
                    "stale_run_id": str(stale["run_id"]),
                    "candidate_id": str(stale["candidate_id"]),
                    "request_id": plan.get("request_id"),
                    "event_payload": json.dumps(
                        {
                            "replacement_candidate_id": str(stale["replacement_candidate_id"]),
                            "replacement_run_id": run_id,
                            "previous_candidate_state": str(stale["previous_candidate_state"]),
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                    "occurred_at": decided_at,
                },
            )
    return len(stale_rows)


def _build_registry_payload(group: dict[str, Any]) -> dict[str, Any]:
    sources = list(group.get("included_sources", []))
    entry_source = next((item for item in sources if str(item.get("discovery_role")) == "entry"), None) or sources[0]
    product_family = str(group.get("product_family") or entry_source.get("product_family") or "deposit")
    allowed_domains = sorted(
        {
            allowed_domain
            for item in sources
            for allowed_domain in [_registry_allowed_domain(str(item["source_url"]))]
            if allowed_domain
        }
    )
    return {
        "registry_version": datetime.now(UTC).strftime("%Y-%m-%d"),
        "bank_code": group["bank_code"],
        "country_code": group["country_code"],
        "product_type": group["product_type"],
        "product_family": product_family,
        "source_language": group["source_language"],
        "allowed_domains": allowed_domains,
        "entry_source_id": entry_source["source_id"],
        "sources": [
            {
                "source_id": item["source_id"],
                "priority": item["priority"],
                "seed_source_flag": item["seed_source_flag"],
                "source_type": item["source_type"],
                "discovery_role": item["discovery_role"],
                "purpose": item["purpose"],
                "url": item["source_url"],
                "expected_fields": item["expected_fields"],
                "source_language": item["source_language"],
                "product_family": item.get("product_family", product_family),
                "product_type_name": item.get("product_type_name"),
                "product_type_description": item.get("product_type_description"),
                "discovery_keywords": item.get("discovery_keywords", []),
                "fallback_policy": item.get("fallback_policy"),
                "discovery_metadata": item.get("discovery_metadata", {}),
            }
            for item in sources
        ],
    }


def _mark_run_failed(*, run_id: str, stage_name: str, error_summary: str) -> None:
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        connection.execute(
            """
            UPDATE ingestion_run
            SET
                run_state = 'failed',
                partial_completion_flag = true,
                error_summary = %(error_summary)s,
                run_metadata = run_metadata || %(run_metadata)s::jsonb,
                completed_at = %(completed_at)s
            WHERE run_id = %(run_id)s
            """,
            {
                "run_id": run_id,
                "error_summary": error_summary,
                "run_metadata": json.dumps({"pipeline_stage": stage_name}, ensure_ascii=True),
                "completed_at": datetime.now(UTC),
            },
        )


def _source_args(source_ids: list[str]) -> list[str]:
    args: list[str] = []
    for source_id in source_ids:
        args.extend(["--source-id", source_id])
    return args


def _hostname(url: str) -> str | None:
    return urlparse(url).hostname


def _registry_allowed_domain(url: str) -> str | None:
    hostname = _hostname(url)
    if not hostname:
        return None
    normalized = hostname.lower().rstrip(".")
    return normalized.removeprefix("www.")


def _resolve_env_file() -> Path | None:
    candidate = Path.cwd() / ".env.dev"
    return candidate if candidate.exists() else None


def args_temp_dir(plan_path: Path | None) -> Path:
    if plan_path is not None:
        return plan_path.parent
    return Path.cwd() / "tmp" / "source-collections"


if __name__ == "__main__":
    raise SystemExit(main())
