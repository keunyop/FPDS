from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

from api_service.aggregate_refresh import launch_aggregate_refresh_runner
from api_service.ai_verification import llm_provider_configured
from api_service.candidate_auto_promotion import promote_auto_validated_candidates
from api_service.collection_ai_autopilot import (
    load_active_collection_review_task_ids,
    load_collection_ai_autopilot_policy,
    remediate_collection_review_task,
)
from api_service.config import Settings
from api_service.db import open_connection
from api_service.security import new_id

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKER_DIAGNOSTIC_MAX_CHARS = 1_600
_CREDENTIAL_URL_RE = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)([^\s/@:]+):([^\s/@]+)@")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|access[_-]?key)\s*([=:])\s*([^\s|,;]+)"
)


class WorkerStageError(RuntimeError):
    def __init__(
        self,
        *,
        stage_name: str,
        failure_kind: str,
        diagnostic: str | None = None,
        return_code: int | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.stage_name = stage_name
        self.failure_kind = failure_kind
        self.diagnostic = diagnostic
        self.return_code = return_code
        self.timeout_seconds = timeout_seconds
        if failure_kind == "timeout":
            message = f"{stage_name} timed out after {timeout_seconds} seconds."
        else:
            message = f"{stage_name} failed with exit code {return_code}."
        if diagnostic:
            message = f"{message} Worker diagnostic: {diagnostic}"
        super().__init__(message)

    def to_run_metadata(self) -> dict[str, Any]:
        return {
            "failed_stage": self.stage_name,
            "stage_failure": {
                "stage_name": self.stage_name,
                "failure_kind": self.failure_kind,
                "return_code": self.return_code,
                "timeout_seconds": self.timeout_seconds,
                "diagnostic": self.diagnostic,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DB-backed source collection plans.")
    parser.add_argument("--plan-path", type=Path, required=True, help="JSON plan file emitted by the admin API.")
    args = parser.parse_args()

    plan = json.loads(args.plan_path.read_text(encoding="utf-8"))
    for group in plan.get("groups", []):
        try:
            _run_group(plan=plan, group=group)
        except Exception as exc:  # pragma: no cover - defensive background-path handling
            _mark_run_failed(
                run_id=str(group["run_id"]),
                stage_name="source_collection",
                error_summary=str(exc),
                failure_metadata=_stage_failure_metadata(exc),
            )
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
    ai_autopilot_result = _run_collection_review_ai_autopilot_for_run(run_id=run_id, plan=plan)
    approved_duplicate_review_count = _supersede_reviews_covered_by_approved_candidates_for_run(
        run_id=run_id,
        plan=plan,
    )
    if approved_duplicate_review_count:
        print(
            (
                f"[source-collection-runner] run {run_id} superseded "
                f"{approved_duplicate_review_count} in-run review duplicate(s) covered by an approved candidate"
            ),
            flush=True,
        )
    if promotion_result["promoted_count"] or ai_autopilot_result["approved_count"]:
        launch_result = launch_aggregate_refresh_runner()
        print(
            (
                f"[source-collection-runner] run {run_id} auto-promoted "
                f"{promotion_result['promoted_count']} validation candidate(s), AI-approved "
                f"{ai_autopilot_result['approved_count']} review candidate(s); "
                f"aggregate refresh launch={launch_result['launched']}"
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
        timeout_stdout = _subprocess_output_text(exc.stdout)
        timeout_stderr = _subprocess_output_text(exc.stderr)
        if timeout_stdout:
            print(_redact_worker_output(timeout_stdout), end="")
        if timeout_stderr:
            print(_redact_worker_output(timeout_stderr), end="", file=sys.stderr)
        recovered_output = _completed_stage_output(timeout_stdout)
        if recovered_output is not None:
            print(
                f"[source-collection-runner] stage {stage_name} emitted a completed persistence result before timeout; continuing",
                file=sys.stderr,
                flush=True,
            )
            return recovered_output
        raise WorkerStageError(
            stage_name=stage_name,
            failure_kind="timeout",
            timeout_seconds=timeout_seconds,
            diagnostic=_bounded_worker_diagnostic(timeout_stderr, timeout_stdout),
        ) from exc
    if completed.stdout:
        print(_redact_worker_output(completed.stdout), end="")
    if completed.stderr:
        print(_redact_worker_output(completed.stderr), end="", file=sys.stderr)
    if completed.returncode != 0:
        raise WorkerStageError(
            stage_name=stage_name,
            failure_kind="nonzero_exit",
            return_code=completed.returncode,
            diagnostic=_bounded_worker_diagnostic(completed.stderr, completed.stdout),
        )
    stdout = completed.stdout.strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


def _subprocess_output_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _bounded_worker_diagnostic(*values: str) -> str | None:
    raw_value = next((value for value in values if value and value.strip()), "")
    if not raw_value:
        return None
    redacted = _redact_worker_output(raw_value)
    lines = [" ".join(line.split()) for line in redacted.splitlines() if line.strip()]
    if not lines:
        return None
    diagnostic = " | ".join(lines[-8:])
    if len(diagnostic) > _WORKER_DIAGNOSTIC_MAX_CHARS:
        diagnostic = f"...{diagnostic[-(_WORKER_DIAGNOSTIC_MAX_CHARS - 3):]}"
    return diagnostic


def _redact_worker_output(value: str) -> str:
    redacted = _CREDENTIAL_URL_RE.sub(r"\1[redacted]@", value)
    return _SECRET_ASSIGNMENT_RE.sub(r"\1\2[redacted]", redacted)


def _stage_failure_metadata(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, WorkerStageError):
        return exc.to_run_metadata()
    diagnostic = _bounded_worker_diagnostic(str(exc))
    return {
        "failed_stage": "source_collection",
        "stage_failure": {
            "stage_name": "source_collection",
            "failure_kind": "runner_error",
            "return_code": None,
            "timeout_seconds": None,
            "diagnostic": diagnostic,
        },
    }


def _completed_stage_output(stdout: str) -> dict[str, Any] | None:
    if not stdout.strip():
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    persistence = payload.get("persistence")
    if not isinstance(persistence, dict) or persistence.get("run_state") != "completed":
        return None
    source_results = payload.get("source_results")
    if not isinstance(source_results, list):
        return None
    return payload


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


def _run_collection_review_ai_autopilot_for_run(*, run_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    if not llm_provider_configured():
        return {
            "status": "provider_unavailable",
            "run_id": run_id,
            "examined_count": 0,
            "approved_count": 0,
            "review_retained_count": 0,
            "failed_count": 0,
            "items": [],
        }

    settings = Settings.from_env()
    try:
        with open_connection(settings) as connection:
            policy = load_collection_ai_autopilot_policy(connection)
            if not policy["enabled"]:
                return {
                    "status": "disabled",
                    "run_id": run_id,
                    "examined_count": 0,
                    "approved_count": 0,
                    "review_retained_count": 0,
                    "failed_count": 0,
                    "items": [],
                    "policy": policy,
                }
            review_task_ids = load_active_collection_review_task_ids(
                connection,
                run_id=run_id,
                limit=int(policy["max_candidates"]),
            )
    except Exception as exc:  # pragma: no cover - fail-soft background DB boundary
        return {
            "status": "failed",
            "run_id": run_id,
            "examined_count": 0,
            "approved_count": 0,
            "review_retained_count": 0,
            "failed_count": 1,
            "items": [],
            "error_summary": str(exc),
        }

    items: list[dict[str, Any]] = []
    for review_task_id in review_task_ids:
        try:
            with open_connection(settings) as connection:
                items.append(
                    remediate_collection_review_task(
                        connection,
                        review_task_id=review_task_id,
                        approval_threshold=float(policy["approval_threshold"]),
                        request_context={
                            "request_id": plan.get("request_id"),
                            "user_agent": "source-collection-runner",
                        },
                    )
                )
        except Exception as exc:  # keep the candidate in Review and continue the run
            items.append(
                {
                    "review_task_id": review_task_id,
                    "status": "failed",
                    "approved": False,
                    "error_summary": str(exc),
                }
            )

    approved_count = sum(1 for item in items if item.get("approved") is True)
    failed_count = sum(1 for item in items if item.get("status") in {"failed", "verification_failed"})
    review_retained_count = sum(1 for item in items if item.get("status") == "review_retained")
    result = {
        "status": "completed",
        "run_id": run_id,
        "examined_count": len(items),
        "approved_count": approved_count,
        "review_retained_count": review_retained_count,
        "failed_count": failed_count,
        "items": items,
        "policy": policy,
    }
    try:
        with open_connection(settings) as connection:
            connection.execute(
                """
                UPDATE ingestion_run
                SET run_metadata = run_metadata || %(run_metadata)s::jsonb
                WHERE run_id = %(run_id)s
                """,
                {
                    "run_id": run_id,
                    "run_metadata": json.dumps(
                        {
                            "collection_ai_autopilot": {
                                "status": result["status"],
                                "examined_count": result["examined_count"],
                                "approved_count": result["approved_count"],
                                "review_retained_count": result["review_retained_count"],
                                "failed_count": result["failed_count"],
                                "policy": policy,
                            }
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                },
            )
    except Exception as exc:  # remediation outcome is safe even if run telemetry lags
        result["telemetry_persistence_error"] = str(exc)
    print(
        (
            f"[source-collection-runner] run {run_id} AI review autopilot examined {len(items)} candidate(s), "
            f"approved {approved_count}, retained {review_retained_count}, failed {failed_count}"
        ),
        flush=True,
    )
    return result


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
    """Keep one normalization target per byte-identical logical source document.

    Different URLs can return the same WAF, consent, or JavaScript shell bytes.
    Therefore checksum equality alone is not proof that two product pages are the
    same product. Supporting sources still pass through parse and extraction.
    """
    target_set = set(target_source_ids)
    identity_by_source_id = {
        str(item.get("source_id")): (
            str(item.get("source_document_id") or "").strip(),
            str(item.get("checksum") or "").strip(),
        )
        for item in snapshot_output.get("source_results", [])
        if str(item.get("source_id") or "") in target_set
    }
    retained: list[str] = []
    duplicates: list[str] = []
    seen_identities: set[tuple[str, str]] = set()
    for source_id in target_source_ids:
        source_document_id, checksum = identity_by_source_id.get(source_id, ("", ""))
        identity = (source_document_id, checksum)
        if source_document_id and checksum and identity in seen_identities:
            duplicates.append(source_id)
            continue
        retained.append(source_id)
        if source_document_id and checksum:
            seen_identities.add(identity)
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

    This coalesces detail-source tasks with the same logical name after either
    an approved candidate or an active Review candidate replaces them. It also
    accepts an exact source-URL match when the new run produced only one
    replacement candidate for that URL, allowing an authoritative name
    correction to replace the stale task without collapsing a multi-product
    page. It does not approve or reject the product proposal itself.
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
                    sd.normalized_source_url,
                    COUNT(*) OVER (
                        PARTITION BY
                            nc.country_code,
                            nc.bank_code,
                            nc.product_family,
                            nc.product_type,
                            sd.normalized_source_url
                    ) AS new_source_candidate_count,
                    nc.created_at
                FROM normalized_candidate AS nc
                JOIN source_document AS sd
                  ON sd.source_document_id = nc.source_document_id
                WHERE nc.run_id = %(run_id)s
                  AND (
                    nc.candidate_state = 'approved'
                    OR (
                        nc.candidate_state = 'in_review'
                        AND EXISTS (
                            SELECT 1
                            FROM review_task AS current_rt
                            WHERE current_rt.candidate_id = nc.candidate_id
                              AND current_rt.review_state IN ('queued', 'deferred')
                        )
                    )
                  )
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
                    newest.candidate_id AS replacement_candidate_id,
                    CASE
                        WHEN lower(nc.product_name) = newest.normalized_product_name
                        THEN 'exact_logical_name'
                        ELSE 'unique_normalized_source_url'
                    END AS supersession_basis
                FROM newest
                JOIN normalized_candidate AS nc
                  ON nc.country_code = newest.country_code
                 AND nc.bank_code = newest.bank_code
                 AND nc.product_family = newest.product_family
                 AND nc.product_type = newest.product_type
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
                  AND (
                    lower(nc.product_name) = newest.normalized_product_name
                    OR (
                        newest.new_source_candidate_count = 1
                        AND newest.normalized_source_url <> ''
                        AND sd.normalized_source_url = newest.normalized_source_url
                    )
                  )
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
                    'A newer detail-source candidate supersedes this stale logical or source-version review.',
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
                            "supersession_basis": str(stale["supersession_basis"]),
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                    "occurred_at": decided_at,
                },
            )
    return len(stale_rows)


def _supersede_reviews_covered_by_approved_candidates_for_run(
    *,
    run_id: str,
    plan: dict[str, Any],
) -> int:
    """Close same-run review duplicates after an exact logical peer is approved.

    Multiple official detail URLs can describe the same product. This guard is
    deliberately narrower than ordinary stale-review coalescing: bank, family,
    Product Type, subtype, normalized product name, and run must all match.
    """
    decided_at = datetime.now(UTC)
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        stale_rows = connection.execute(
            """
            WITH approved AS (
                SELECT DISTINCT ON (
                    country_code,
                    bank_code,
                    product_family,
                    product_type,
                    subtype_code,
                    lower(product_name)
                )
                    candidate_id,
                    country_code,
                    bank_code,
                    product_family,
                    product_type,
                    subtype_code,
                    lower(product_name) AS normalized_product_name
                FROM normalized_candidate
                WHERE run_id = %(run_id)s
                  AND candidate_state = 'approved'
                ORDER BY
                    country_code,
                    bank_code,
                    product_family,
                    product_type,
                    subtype_code,
                    lower(product_name),
                    updated_at DESC,
                    candidate_id DESC
            ),
            stale AS (
                SELECT
                    nc.candidate_id,
                    nc.candidate_state AS previous_candidate_state,
                    rt.review_task_id,
                    rt.review_state AS previous_review_state,
                    approved.candidate_id AS replacement_candidate_id
                FROM approved
                JOIN normalized_candidate AS nc
                  ON nc.run_id = %(run_id)s
                 AND nc.country_code = approved.country_code
                 AND nc.bank_code = approved.bank_code
                 AND nc.product_family = approved.product_family
                 AND nc.product_type = approved.product_type
                 AND nc.subtype_code = approved.subtype_code
                 AND lower(nc.product_name) = approved.normalized_product_name
                 AND nc.candidate_id <> approved.candidate_id
                JOIN review_task AS rt
                  ON rt.candidate_id = nc.candidate_id
                JOIN source_document AS sd
                  ON sd.source_document_id = nc.source_document_id
                WHERE nc.candidate_state = 'in_review'
                  AND rt.review_state IN ('queued', 'deferred')
                  AND COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') = 'detail'
                FOR UPDATE OF nc, rt
            ),
            superseded_candidates AS (
                UPDATE normalized_candidate AS nc
                SET
                    candidate_state = 'superseded',
                    review_reason_code = 'superseded_by_approved_logical_candidate',
                    updated_at = %(decided_at)s
                FROM stale
                WHERE nc.candidate_id = stale.candidate_id
                RETURNING nc.candidate_id
            ),
            resolved_reviews AS (
                UPDATE review_task AS rt
                SET
                    review_state = 'rejected',
                    queue_reason_code = 'superseded_by_approved_logical_candidate',
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
                    %(audit_event_id)s, 'review', 'approved_duplicate_review_auto_superseded', 'system',
                    'review_task', %(review_task_id)s, %(previous_state)s, 'rejected',
                    'superseded_by_approved_logical_candidate',
                    'An approved candidate from the same run covers this exact logical product review.',
                    %(run_id)s, %(candidate_id)s, %(review_task_id)s,
                    %(request_id)s, 'Resolved a same-run logical duplicate review task.',
                    %(request_id)s, %(event_payload)s::jsonb, %(occurred_at)s
                )
                """,
                {
                    "audit_event_id": new_id("audit"),
                    "review_task_id": str(stale["review_task_id"]),
                    "previous_state": str(stale["previous_review_state"]),
                    "run_id": run_id,
                    "candidate_id": str(stale["candidate_id"]),
                    "request_id": plan.get("request_id"),
                    "event_payload": json.dumps(
                        {
                            "replacement_candidate_id": str(stale["replacement_candidate_id"]),
                            "replacement_run_id": run_id,
                            "previous_candidate_state": str(stale["previous_candidate_state"]),
                            "supersession_basis": "same_run_exact_logical_identity",
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
                "normalized_source_url": item["source_url"],
                "official_domain_allowlist": allowed_domains,
            }
            for item in sources
        ],
    }


def _mark_run_failed(
    *,
    run_id: str,
    stage_name: str,
    error_summary: str,
    failure_metadata: dict[str, Any] | None = None,
) -> None:
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
                "run_metadata": json.dumps(
                    {"pipeline_stage": stage_name, **(failure_metadata or {})},
                    ensure_ascii=True,
                ),
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
