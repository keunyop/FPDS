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

from api_service.config import Settings
from api_service.db import open_connection

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

    _run_stage(
        "worker.pipeline.fpds_validation_routing",
        base_args + ["--routing-mode", "phase1"] + _source_args(normalization_successful_target_source_ids),
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
    for item in stage_output.get("source_results", []):
        if str(item.get(action_field)) in success_actions and item.get("source_id"):
            source_ids.append(str(item["source_id"]))
    return source_ids


def _filter_requested_source_ids(*, requested_source_ids: list[str], successful_source_ids: list[str]) -> list[str]:
    successful_source_id_set = set(successful_source_ids)
    return [source_id for source_id in requested_source_ids if source_id in successful_source_id_set]


def _build_registry_payload(group: dict[str, Any]) -> dict[str, Any]:
    sources = list(group.get("included_sources", []))
    entry_source = next((item for item in sources if str(item.get("discovery_role")) == "entry"), None) or sources[0]
    allowed_domains = sorted(
        {
            hostname
            for item in sources
            for hostname in [_hostname(str(item["source_url"]))]
            if hostname
        }
    )
    return {
        "registry_version": datetime.now(UTC).strftime("%Y-%m-%d"),
        "bank_code": group["bank_code"],
        "country_code": group["country_code"],
        "product_type": group["product_type"],
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
                "product_type_name": item.get("product_type_name"),
                "product_type_description": item.get("product_type_description"),
                "product_type_dynamic": item.get("product_type_dynamic"),
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


def _resolve_env_file() -> Path | None:
    candidate = Path.cwd() / ".env.dev"
    return candidate if candidate.exists() else None


def args_temp_dir(plan_path: Path | None) -> Path:
    if plan_path is not None:
        return plan_path.parent
    return Path.cwd() / "tmp" / "source-collections"


if __name__ == "__main__":
    raise SystemExit(main())
