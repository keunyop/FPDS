from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.discovery.fpds_discovery.catalog import load_all_registries
from worker.discovery.fpds_discovery.registry import load_registry
from worker.env import load_env_file, resolve_default_env_file

from .persistence import PsqlResultViewerRepository, ResultViewerDatabaseConfig
from .service import ResultViewerPayloadService


def main() -> int:
    parser = argparse.ArgumentParser(description="Export FPDS prototype internal result viewer payload")
    parser.add_argument("--run-id", required=True, help="Run identifier to export from the FPDS database.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file to load before execution.")
    parser.add_argument(
        "--no-default-env-file",
        action="store_true",
        help="Disable automatic loading of .env.dev or .env when --env-file is not provided.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("app/prototype/viewer-payload.json"),
        help="Destination JSON payload path.",
    )
    parser.add_argument(
        "--output-js",
        type=Path,
        default=Path("app/prototype/viewer-payload.js"),
        help="Destination JS payload path consumed by the static viewer.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    repository = PsqlResultViewerRepository(ResultViewerDatabaseConfig.from_env())
    registries = (load_registry(args.registry_path),) if args.registry_path is not None else load_all_registries()
    source_id_by_document_id = {
        source.source_document_id: source.source_id
        for registry in registries
        for source in registry.sources
    }
    run_overview = repository.load_run_overview(run_id=args.run_id)
    candidate_rows = repository.load_candidate_rows(run_id=args.run_id)
    service = ResultViewerPayloadService()
    generated_at = datetime.now(UTC).isoformat()
    payload = service.build_payload(
        run_overview=run_overview,
        candidate_rows=candidate_rows,
        source_id_by_document_id=source_id_by_document_id,
        generated_at=generated_at,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    args.output_js.parent.mkdir(parents=True, exist_ok=True)
    args.output_js.write_text(service.build_payload_js(payload=payload), encoding="utf-8")

    summary = {
        "run_id": args.run_id,
        "candidate_count": len(payload["candidates"]),
        "review_task_count": sum(1 for item in payload["candidates"] if item.get("review_task_id")),
        "evidence_link_count": sum(len(item["evidence_links"]) for item in payload["candidates"]),
        "output_json": str(args.output_json),
        "output_js": str(args.output_js),
        "runtime": {
            "env_file": str(env_file) if env_file is not None else None,
            "loaded_env_key_count": len(loaded_env_keys),
            "database_schema": repository.active_schema,
            "generated_at": generated_at,
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
