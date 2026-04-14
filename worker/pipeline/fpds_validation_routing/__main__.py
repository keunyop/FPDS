from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.discovery.fpds_discovery.catalog import resolve_sources_by_id
from worker.env import load_env_file, resolve_default_env_file

from .models import ValidationEvidenceLink, ValidationInput
from .persistence import PsqlValidationRoutingRepository, ValidationRoutingDatabaseConfig
from .service import ValidationRoutingService
from .storage import ValidationRoutingStorageConfig, build_object_store


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS validation and confidence routing flow")
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
        help="Persist review_task, updated normalized_candidate rows, model_execution, llm_usage_record, and run_source_item rows to Postgres.",
    )
    parser.add_argument("--trigger-type", default="manual", help="ingestion_run.trigger_type value for persisted runs.")
    parser.add_argument("--triggered-by", default="codex", help="Optional operator or service label for persisted runs.")
    parser.add_argument(
        "--routing-mode",
        choices=["prototype", "phase1"],
        default="prototype",
        help="Routing policy mode. Prototype keeps all candidates in review by default.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Registry source id to validate and route from the latest normalization artifact. Repeat as needed.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    args = parser.parse_args()

    if not args.source_id:
        raise ValueError("At least one --source-id is required.")

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    repository = PsqlValidationRoutingRepository(ValidationRoutingDatabaseConfig.from_env())
    selected_sources_by_id = resolve_sources_by_id(args.source_id, registry_path=args.registry_path)
    source_document_ids = [selected_sources_by_id[source_id].source_document_id for source_id in args.source_id]
    repository.ensure_ingestion_run(
        run_id=args.run_id,
        trigger_type=args.trigger_type,
        triggered_by=args.triggered_by,
        source_scope_count=len(source_document_ids),
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        source_ids=args.source_id,
        started_at=_utc_now_iso(),
    )

    lookups = repository.load_latest_normalization_artifacts(source_document_ids=source_document_ids)
    lookup_by_source_document_id = {item.source_document_id: item for item in lookups}
    missing_source_ids = [
        source_id
        for source_id in args.source_id
        if selected_sources_by_id[source_id].source_document_id not in lookup_by_source_document_id
    ]
    if missing_source_ids:
        raise ValueError(
            "No completed normalization artifact was found for source ids: "
            + ", ".join(missing_source_ids)
            + ". Run WBS 3.6 normalization first."
        )

    taxonomy_registry = repository.load_taxonomy_registry()
    routing_config = repository.load_routing_config(routing_mode=args.routing_mode)
    storage_config = ValidationRoutingStorageConfig.from_env()
    object_store = build_object_store(storage_config)

    inputs: list[ValidationInput] = []
    for source_id in args.source_id:
        source_document_id = selected_sources_by_id[source_id].source_document_id
        lookup = lookup_by_source_document_id[source_document_id]
        artifact = json.loads(object_store.get_object_bytes(object_key=lookup.normalized_storage_key).decode("utf-8"))
        inputs.append(
            _build_validation_input(
                source_id=source_id,
                lookup=lookup,
                artifact=artifact,
            )
        )

    service = ValidationRoutingService(
        storage_config=storage_config,
        object_store=object_store,
    )
    result = service.validate_and_route_inputs(
        run_id=args.run_id,
        inputs=inputs,
        taxonomy_registry=taxonomy_registry,
        routing_config=routing_config,
        correlation_id=args.correlation_id,
        request_id=args.request_id,
    )
    output = result.to_dict()
    output["runtime"] = {
        "env_file": str(env_file) if env_file is not None else None,
        "loaded_env_key_count": len(loaded_env_keys),
        "persist_db": args.persist_db,
        "trigger_type": args.trigger_type,
        "triggered_by": args.triggered_by,
        "routing_mode": args.routing_mode,
        "database_schema": repository.active_schema,
        "storage_driver": storage_config.driver,
    }
    if args.persist_db:
        persistence = repository.persist_validation_result(
            run_id=args.run_id,
            validation_result=result,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            completed_at=_utc_now_iso(),
        )
        output["persistence"] = persistence.to_dict()

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


def _build_validation_input(
    *,
    source_id: str,
    lookup,
    artifact: dict[str, object],
) -> ValidationInput:
    candidate_record = dict(artifact.get("normalized_candidate", {}))
    return ValidationInput(
        source_id=source_id,
        source_document_id=lookup.source_document_id,
        snapshot_id=lookup.snapshot_id,
        parsed_document_id=lookup.parsed_document_id,
        candidate_id=str(candidate_record["candidate_id"]),
        candidate_run_id=str(candidate_record["run_id"]),
        normalization_model_execution_id=lookup.normalization_model_execution_id,
        normalized_storage_key=lookup.normalized_storage_key,
        metadata_storage_key=lookup.normalization_metadata_storage_key,
        bank_code=lookup.bank_code,
        country_code=lookup.country_code,
        source_type=lookup.source_type,
        source_language=lookup.source_language,
        source_metadata=dict(lookup.source_metadata),
        normalized_candidate_record=candidate_record,
        field_evidence_links=[ValidationEvidenceLink(**item) for item in artifact.get("field_evidence_links", [])],
        runtime_notes=list(artifact.get("runtime_notes", [])),
    )


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
