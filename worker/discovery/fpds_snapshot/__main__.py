from __future__ import annotations

import argparse
import json
from pathlib import Path

from worker.discovery.env import load_env_file, resolve_default_env_file
from worker.discovery.fpds_discovery.drift import RegistryPreflightDriftService
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
from worker.discovery.fpds_discovery.registry import load_registry

from .capture import CaptureSource, ExistingSnapshotRecord, SnapshotCaptureService
from .persistence import PsqlSnapshotRepository, SnapshotDatabaseConfig, utc_now_iso
from .storage import SnapshotStorageConfig, build_object_store


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS snapshot capture")
    parser.add_argument("--run-id", required=True, help="Run identifier.")
    parser.add_argument("--correlation-id", default=None, help="Optional correlation identifier.")
    parser.add_argument("--request-id", default=None, help="Optional request identifier.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file to load before execution.")
    parser.add_argument(
        "--no-default-env-file",
        action="store_true",
        help="Disable automatic loading of .env.dev or .env when --env-file is not provided.",
    )
    parser.add_argument(
        "--persist-db",
        action="store_true",
        help="Persist source documents, snapshots, run items, and run summary to Postgres.",
    )
    parser.add_argument(
        "--trigger-type",
        default="manual",
        help="ingestion_run.trigger_type value for persisted runs.",
    )
    parser.add_argument(
        "--triggered-by",
        default="codex",
        help="Optional operator or service label for persisted runs.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Registry source id to capture. Repeat as needed. Defaults to all registry sources.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--existing-snapshots-path",
        type=Path,
        default=None,
        help="Optional JSON file with previously stored snapshot records for reuse decisions.",
    )
    parser.add_argument(
        "--skip-preflight-drift-check",
        action="store_true",
        help="Disable lightweight source drift checks before snapshot capture.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    registry = load_registry(args.registry_path)
    selected_sources = args.source_id or [source.source_id for source in registry.sources]
    sources = [CaptureSource.from_registry_source(registry.by_source_id(source_id)) for source_id in selected_sources]

    existing_snapshots = []
    if args.existing_snapshots_path is not None:
        payload = json.loads(args.existing_snapshots_path.read_text(encoding="utf-8"))
        existing_snapshots = [ExistingSnapshotRecord(**item) for item in payload]

    repository = None
    started_at = utc_now_iso()
    if args.persist_db:
        repository = PsqlSnapshotRepository(SnapshotDatabaseConfig.from_env())
        repository.start_ingestion_run(
            run_id=args.run_id,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            source_scope_count=len(sources),
            correlation_id=args.correlation_id,
            request_id=args.request_id,
            source_ids=[source.source_id for source in sources],
            started_at=started_at,
        )
        existing_snapshots.extend(
            repository.load_existing_snapshots(
                source_document_ids=[source.source_document_id for source in sources],
            )
        )

    storage_config = SnapshotStorageConfig.from_env()
    fetch_policy = DiscoveryFetchPolicy.from_env(extra_allowed_domains=registry.allowed_domains)
    preflight_result = None
    if not args.skip_preflight_drift_check:
        preflight_service = RegistryPreflightDriftService(fetch_policy=fetch_policy)
        preflight_result = preflight_service.check_sources(
            run_id=args.run_id,
            correlation_id=args.correlation_id,
            request_id=args.request_id,
            sources=sources,
        )
    service = SnapshotCaptureService(
        fetch_policy=fetch_policy,
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    result = service.capture_sources(
        run_id=args.run_id,
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        sources=sources,
        existing_snapshots=existing_snapshots,
        preflight_result=preflight_result,
    )
    output = result.to_dict()
    output["runtime"] = {
        "env_file": str(env_file) if env_file is not None else None,
        "loaded_env_key_count": len(loaded_env_keys),
        "persist_db": args.persist_db,
        "trigger_type": args.trigger_type,
        "triggered_by": args.triggered_by,
        "database_schema": repository.active_schema if repository is not None else None,
        "storage_driver": storage_config.driver,
        "source_fetch_timeout_seconds": fetch_policy.timeout_seconds,
        "source_fetch_concurrency": service.max_concurrency,
        "preflight_drift_check_enabled": not args.skip_preflight_drift_check,
    }
    if repository is not None:
        persistence_result = repository.persist_capture_result(
            run_id=args.run_id,
            sources=sources,
            capture_result=result,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            started_at=started_at,
            completed_at=utc_now_iso(),
        )
        output["persistence"] = persistence_result.to_dict()

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
