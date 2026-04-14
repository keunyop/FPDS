from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.discovery.fpds_discovery.catalog import resolve_sources_by_id
from worker.env import load_env_file, resolve_default_env_file
from worker.discovery.fpds_discovery.registry import load_registry

from .models import ParseSourceSnapshot
from .persistence import PsqlParseChunkRepository, ParseChunkDatabaseConfig
from .service import ParseChunkService
from .storage import ParseChunkStorageConfig, build_object_store


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS parse and chunk pipeline")
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
        help="Persist parsed_document, evidence_chunk, and updated run_source_item rows to Postgres.",
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
        help="Registry source id to parse. Repeat as needed. Defaults to all registry sources when loading snapshots from DB.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--snapshot-records-path",
        type=Path,
        default=None,
        help="Optional JSON file with snapshot records for parse/chunk input when DB lookup is not used.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    repository = None
    registry = load_registry(args.registry_path)
    selected_source_ids = args.source_id or [source.source_id for source in registry.sources]
    selected_sources_by_id = (
        resolve_sources_by_id(selected_source_ids, registry_path=args.registry_path)
        if args.source_id
        else {source.source_id: source for source in registry.sources}
    )
    if args.snapshot_records_path is not None:
        payload = json.loads(args.snapshot_records_path.read_text(encoding="utf-8"))
        snapshots = [ParseSourceSnapshot(**item) for item in payload]
    else:
        if not args.persist_db:
            raise ValueError("Either --persist-db or --snapshot-records-path is required for parse/chunk input.")
        repository = PsqlParseChunkRepository(ParseChunkDatabaseConfig.from_env())
        source_document_ids = [selected_sources_by_id[source_id].source_document_id for source_id in selected_source_ids]
        repository.ensure_ingestion_run(
            run_id=args.run_id,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            source_scope_count=len(source_document_ids),
            correlation_id=args.correlation_id,
            request_id=args.request_id,
            source_ids=selected_source_ids,
            started_at=_utc_now_iso(),
        )
        loaded_snapshots = repository.load_latest_snapshots(source_document_ids=source_document_ids)
        snapshot_map = {snapshot.source_document_id: snapshot for snapshot in loaded_snapshots}
        missing_source_ids = [
            source_id
            for source_id in selected_source_ids
            if selected_sources_by_id[source_id].source_document_id not in snapshot_map
        ]
        if missing_source_ids:
            raise ValueError(
                "No stored snapshot was found for source ids: "
                + ", ".join(missing_source_ids)
                + ". Run WBS 3.2 snapshot capture first."
            )
        snapshots = [
            ParseSourceSnapshot(
                    **{
                    **snapshot_map[selected_sources_by_id[source_id].source_document_id].__dict__,
                    "source_id": source_id,
                }
            )
            for source_id in selected_source_ids
        ]

    existing_parsed_documents = []
    if repository is not None:
        existing_parsed_documents = repository.load_existing_parsed_documents(
            snapshot_ids=[snapshot.snapshot_id for snapshot in snapshots],
        )

    storage_config = ParseChunkStorageConfig.from_env()
    service = ParseChunkService(
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    result = service.parse_snapshots(
        run_id=args.run_id,
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        snapshots=snapshots,
        existing_parsed_documents=existing_parsed_documents,
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
    }

    if args.persist_db:
        if repository is None:
            repository = PsqlParseChunkRepository(ParseChunkDatabaseConfig.from_env())
        persistence_result = repository.persist_parse_chunk_result(
            run_id=args.run_id,
            parse_result=result,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            completed_at=_utc_now_iso(),
        )
        output["persistence"] = persistence_result.to_dict()

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
