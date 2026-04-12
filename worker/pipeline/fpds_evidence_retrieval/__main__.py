from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from worker.env import load_env_file, resolve_default_env_file
from worker.discovery.fpds_discovery.registry import load_registry

from .models import EvidenceRetrievalRequest, MetadataFilters
from .persistence import PsqlEvidenceRetrievalRepository, RetrievalDatabaseConfig
from .service import EvidenceRetrievalService


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS evidence retrieval")
    parser.add_argument("--run-id", required=True, help="Run identifier.")
    parser.add_argument("--correlation-id", default=None, help="Optional correlation identifier.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file to load before execution.")
    parser.add_argument(
        "--no-default-env-file",
        action="store_true",
        help="Disable automatic loading of .env.dev or .env when --env-file is not provided.",
    )
    parser.add_argument("--parsed-document-id", default=None, help="Parsed document id to search.")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Registry source id to resolve to the latest parsed document. Repeat as needed.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--field-name",
        action="append",
        default=[],
        help="Canonical field name to retrieve evidence for. Repeat as needed.",
    )
    parser.add_argument(
        "--retrieval-mode",
        default="metadata-only",
        help="Requested retrieval mode. Supported values: metadata-only, vector-assisted.",
    )
    parser.add_argument("--max-matches-per-field", type=int, default=5, help="Maximum matches per field.")
    parser.add_argument("--bank-code", default=None, help="Optional metadata filter.")
    parser.add_argument("--country-code", default=None, help="Optional metadata filter.")
    parser.add_argument("--source-language", default=None, help="Optional metadata filter.")
    parser.add_argument("--source-type", action="append", default=[], help="Optional metadata filter. Repeat as needed.")
    parser.add_argument("--anchor-type", action="append", default=[], help="Optional metadata filter. Repeat as needed.")
    args = parser.parse_args()

    if not args.field_name:
        raise ValueError("At least one --field-name is required.")

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    repository = PsqlEvidenceRetrievalRepository(RetrievalDatabaseConfig.from_env())
    parsed_document_id = args.parsed_document_id
    if parsed_document_id is None:
        if not args.source_id:
            raise ValueError("Either --parsed-document-id or at least one --source-id is required.")
        if len(args.source_id) != 1:
            raise ValueError("When --parsed-document-id is omitted, pass exactly one --source-id.")
        registry = load_registry(args.registry_path)
        source_document_ids = [registry.by_source_id(source_id).source_document_id for source_id in args.source_id]
        parsed_documents = repository.load_latest_parsed_documents(source_document_ids=source_document_ids)
        parsed_by_source_document_id = {item.source_document_id: item for item in parsed_documents}
        missing_source_ids = [
            source_id
            for source_id in args.source_id
            if registry.by_source_id(source_id).source_document_id not in parsed_by_source_document_id
        ]
        if missing_source_ids:
            raise ValueError(
                "No parsed document was found for source ids: "
                + ", ".join(missing_source_ids)
                + ". Run WBS 3.3 parse/chunk first."
            )
        first_source_document_id = registry.by_source_id(args.source_id[0]).source_document_id
        parsed_document_id = parsed_by_source_document_id[first_source_document_id].parsed_document_id

    filters = MetadataFilters(
        bank_code=args.bank_code,
        country_code=args.country_code,
        source_language=args.source_language,
        source_types=tuple(args.source_type),
        source_document_ids=tuple(),
        anchor_types=tuple(args.anchor_type),
    )
    request = EvidenceRetrievalRequest(
        correlation_id=args.correlation_id,
        run_id=args.run_id,
        parsed_document_id=parsed_document_id,
        field_names=args.field_name,
        metadata_filters=filters,
        retrieval_mode=args.retrieval_mode,
        max_matches_per_field=args.max_matches_per_field,
    )

    service = EvidenceRetrievalService()
    result = service.retrieve(
        request=request,
        candidates=repository.load_chunk_candidates(parsed_document_id=parsed_document_id),
    )
    output = result.to_dict()
    output["runtime"] = {
        "env_file": str(env_file) if env_file is not None else None,
        "loaded_env_key_count": len(loaded_env_keys),
        "database_schema": repository.active_schema,
        "vector_backend": os.getenv("FPDS_VECTOR_BACKEND", "pgvector"),
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
