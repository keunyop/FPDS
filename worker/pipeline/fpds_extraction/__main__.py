from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.discovery.fpds_discovery.catalog import resolve_sources_by_id
from worker.env import load_env_file, resolve_default_env_file
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate

from .models import ExtractionDocumentContext, ExtractionInput
from .persistence import ExtractionDatabaseConfig, PsqlExtractionRepository
from .service import ExtractionService
from .storage import ExtractionStorageConfig, build_object_store


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS extraction flow")
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
        help="Persist model_execution, llm_usage_record, and updated run_source_item rows to Postgres.",
    )
    parser.add_argument("--trigger-type", default="manual", help="ingestion_run.trigger_type value for persisted runs.")
    parser.add_argument("--triggered-by", default="codex", help="Optional operator or service label for persisted runs.")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Registry source id to extract. Repeat as needed.",
    )
    parser.add_argument(
        "--parsed-document-id",
        action="append",
        default=[],
        help="Parsed document id to extract directly. Repeat as needed.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--field-name",
        action="append",
        default=[],
        help="Optional override field names. When omitted, expected_fields plus extraction defaults are used.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    repository = PsqlExtractionRepository(ExtractionDatabaseConfig.from_env())
    contexts = _load_contexts(repository=repository, args=args)
    inputs = []
    for context in contexts:
        payload = repository.load_chunk_candidates(parsed_document_id=context.parsed_document_id)
        candidates = [EvidenceChunkCandidate(**item) for item in payload]
        inputs.append(ExtractionInput(context=context, candidates=candidates))

    storage_config = ExtractionStorageConfig.from_env()
    service = ExtractionService(
        storage_config=storage_config,
        object_store=build_object_store(storage_config),
    )
    result = service.extract_documents(
        run_id=args.run_id,
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        inputs=inputs,
        override_field_names=args.field_name or None,
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
        persistence = repository.persist_extraction_result(
            run_id=args.run_id,
            extraction_result=result,
            trigger_type=args.trigger_type,
            triggered_by=args.triggered_by,
            completed_at=_utc_now_iso(),
        )
        output["persistence"] = persistence.to_dict()

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


def _load_contexts(
    *,
    repository: PsqlExtractionRepository,
    args,
) -> list[ExtractionDocumentContext]:
    if args.source_id:
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
        loaded_contexts = repository.load_latest_document_contexts(source_document_ids=source_document_ids)
        context_by_source_document_id = {item.source_document_id: item for item in loaded_contexts}
        missing_source_ids = [
            source_id
            for source_id in args.source_id
            if selected_sources_by_id[source_id].source_document_id not in context_by_source_document_id
        ]
        if missing_source_ids:
            raise ValueError(
                "No parsed document was found for source ids: "
                + ", ".join(missing_source_ids)
                + ". Run WBS 3.3 parse/chunk first."
            )

        contexts: list[ExtractionDocumentContext] = []
        for source_id in args.source_id:
            source_document_id = selected_sources_by_id[source_id].source_document_id
            context = context_by_source_document_id[source_document_id]
            contexts.append(
                ExtractionDocumentContext(
                    **{
                        **context.__dict__,
                        "source_id": source_id,
                    }
                )
            )
        return contexts

    if not args.parsed_document_id:
        raise ValueError("At least one --source-id or --parsed-document-id is required.")

    repository.ensure_ingestion_run(
        run_id=args.run_id,
        trigger_type=args.trigger_type,
        triggered_by=args.triggered_by,
        source_scope_count=len(args.parsed_document_id),
        correlation_id=args.correlation_id,
        request_id=args.request_id,
        source_ids=[],
        started_at=_utc_now_iso(),
    )
    contexts = repository.load_document_contexts_by_parsed_document_ids(parsed_document_ids=args.parsed_document_id)
    found = {item.parsed_document_id for item in contexts}
    missing_parsed_document_ids = [item for item in args.parsed_document_id if item not in found]
    if missing_parsed_document_ids:
        raise ValueError(
            "No parsed document context was found for parsed_document_id values: "
            + ", ".join(missing_parsed_document_ids)
        )
    return contexts


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
