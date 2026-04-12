from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.discovery.fpds_discovery.registry import load_registry
from worker.env import load_env_file, resolve_default_env_file

from .models import (
    NormalizationArtifactLookup,
    NormalizationEvidenceLink,
    NormalizationExtractedField,
    NormalizationInput,
)
from .persistence import NormalizationDatabaseConfig, PsqlNormalizationRepository
from .service import NormalizationService
from .storage import NormalizationStorageConfig, build_object_store
from .supporting_merge import merge_supporting_artifacts, supporting_source_ids_for_target


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS normalization flow")
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
        help="Persist normalized_candidate, field_evidence_link, model_execution, llm_usage_record, and updated run_source_item rows to Postgres.",
    )
    parser.add_argument("--trigger-type", default="manual", help="ingestion_run.trigger_type value for persisted runs.")
    parser.add_argument("--triggered-by", default="codex", help="Optional operator or service label for persisted runs.")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Registry source id to normalize from the latest extraction artifact. Repeat as needed.",
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

    repository = PsqlNormalizationRepository(NormalizationDatabaseConfig.from_env())
    registry = load_registry(args.registry_path)
    target_source_document_ids = [registry.by_source_id(source_id).source_document_id for source_id in args.source_id]
    supporting_source_ids = sorted(
        {
            support_source_id
            for source_id in args.source_id
            for support_source_id in supporting_source_ids_for_target(source_id)
        }
    )
    supporting_source_document_ids = [registry.by_source_id(source_id).source_document_id for source_id in supporting_source_ids]
    lookup_source_document_ids = [*target_source_document_ids, *supporting_source_document_ids]
    repository.ensure_ingestion_run(
        run_id=args.run_id,
        trigger_type=args.trigger_type,
        triggered_by=args.triggered_by,
        source_scope_count=len(target_source_document_ids),
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        source_ids=args.source_id,
        started_at=_utc_now_iso(),
    )

    lookups = repository.load_latest_extraction_artifacts(source_document_ids=lookup_source_document_ids)
    lookup_by_source_document_id = {item.source_document_id: item for item in lookups}
    missing_source_ids = [
        source_id
        for source_id in args.source_id
        if registry.by_source_id(source_id).source_document_id not in lookup_by_source_document_id
    ]
    if missing_source_ids:
        raise ValueError(
            "No completed extraction artifact was found for source ids: "
            + ", ".join(missing_source_ids)
            + ". Run WBS 3.5 extraction first."
        )

    storage_config = NormalizationStorageConfig.from_env()
    object_store = build_object_store(storage_config)
    supporting_artifacts_by_source_id: dict[str, dict[str, object]] = {}
    for support_source_id in supporting_source_ids:
        source_document_id = registry.by_source_id(support_source_id).source_document_id
        lookup = lookup_by_source_document_id.get(source_document_id)
        if lookup is None:
            continue
        supporting_artifacts_by_source_id[support_source_id] = json.loads(
            object_store.get_object_bytes(object_key=lookup.extracted_storage_key).decode("utf-8")
        )
    inputs: list[NormalizationInput] = []
    for source_id in args.source_id:
        source_document_id = registry.by_source_id(source_id).source_document_id
        lookup = lookup_by_source_document_id[source_document_id]
        artifact = json.loads(object_store.get_object_bytes(object_key=lookup.extracted_storage_key).decode("utf-8"))
        target_supporting_source_ids = supporting_source_ids_for_target(source_id)
        available_supporting_artifacts = {
            support_source_id: supporting_artifacts_by_source_id[support_source_id]
            for support_source_id in target_supporting_source_ids
            if support_source_id in supporting_artifacts_by_source_id
        }
        missing_supporting_source_ids = [
            support_source_id
            for support_source_id in target_supporting_source_ids
            if support_source_id not in available_supporting_artifacts
        ]
        merged_artifact = merge_supporting_artifacts(
            target_source_id=source_id,
            base_artifact=artifact,
            supporting_artifacts=available_supporting_artifacts,
            missing_support_source_ids=missing_supporting_source_ids,
        )
        inputs.append(
            _build_normalization_input(
                source_id=source_id,
                lookup=lookup,
                artifact=merged_artifact,
            )
        )

    service = NormalizationService(
        storage_config=storage_config,
        object_store=object_store,
    )
    result = service.normalize_inputs(
        run_id=args.run_id,
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        inputs=inputs,
    )
    output = result.to_dict()
    output["runtime"] = {
        "env_file": str(env_file) if env_file is not None else None,
        "loaded_env_key_count": len(loaded_env_keys),
        "persist_db": args.persist_db,
        "trigger_type": args.trigger_type,
        "triggered_by": args.triggered_by,
        "database_schema": repository.active_schema,
        "storage_driver": storage_config.driver,
    }
    if args.persist_db:
        persistence = repository.persist_normalization_result(
            run_id=args.run_id,
            normalization_result=result,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            completed_at=_utc_now_iso(),
        )
        output["persistence"] = persistence.to_dict()

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


def _build_normalization_input(
    *,
    source_id: str,
    lookup: NormalizationArtifactLookup,
    artifact: dict[str, object],
) -> NormalizationInput:
    return NormalizationInput(
        source_id=source_id,
        source_document_id=lookup.source_document_id,
        snapshot_id=lookup.snapshot_id,
        parsed_document_id=lookup.parsed_document_id,
        extraction_model_execution_id=lookup.extraction_model_execution_id,
        extracted_storage_key=lookup.extracted_storage_key,
        metadata_storage_key=lookup.extraction_metadata_storage_key,
        bank_code=lookup.bank_code,
        country_code=lookup.country_code,
        source_type=lookup.source_type,
        source_language=lookup.source_language,
        source_metadata=dict(lookup.source_metadata),
        schema_context=dict(artifact.get("schema_context", {})),
        extracted_fields=[NormalizationExtractedField(**item) for item in artifact.get("extracted_fields", [])],
        evidence_links=[NormalizationEvidenceLink(**item) for item in artifact.get("evidence_links", [])],
        runtime_notes=list(artifact.get("runtime_notes", [])),
    )


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
