from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from worker.env import load_env_file, resolve_default_env_file

from .persistence import AggregateRefreshDatabaseConfig, PsqlAggregateRefreshRepository
from .service import AggregateRefreshService


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS aggregate refresh for WBS 5.6")
    parser.add_argument("--snapshot-id", required=True, help="Aggregate snapshot identifier.")
    parser.add_argument("--country-code", default="CA", help="Country code to aggregate.")
    parser.add_argument("--refresh-scope", default="phase1_public", help="Logical refresh scope label.")
    parser.add_argument("--triggered-by-run-id", default=None, help="Optional ingestion_run id that caused the refresh.")
    parser.add_argument("--bank-code", action="append", default=[], help="Optional bank filter. Repeat as needed.")
    parser.add_argument("--product-type", action="append", default=[], help="Optional product type filter. Repeat as needed.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file to load before execution.")
    parser.add_argument(
        "--no-default-env-file",
        action="store_true",
        help="Disable automatic loading of .env.dev or .env when --env-file is not provided.",
    )
    parser.add_argument(
        "--persist-db",
        action="store_true",
        help="Persist aggregate snapshot rows to Postgres. Without this flag the command runs in dry-run mode.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    attempted_at = _utc_now_iso()
    repository = PsqlAggregateRefreshRepository(AggregateRefreshDatabaseConfig.from_env())
    filter_scope = {
        "country_code": args.country_code,
        "bank_codes": sorted({item for item in args.bank_code if item}),
        "product_types": sorted({item for item in args.product_type if item}),
    }
    refresh_started = False
    if args.persist_db:
        repository.ensure_refresh_run(
            snapshot_id=args.snapshot_id,
            triggered_by_run_id=args.triggered_by_run_id,
            refresh_scope=args.refresh_scope,
            country_code=args.country_code,
            filter_scope=filter_scope,
            attempted_at=attempted_at,
        )
        refresh_started = True

    try:
        canonical_rows = repository.load_current_canonical_rows(
            country_code=args.country_code,
            bank_codes=list(filter_scope["bank_codes"]),
            product_types=list(filter_scope["product_types"]),
        )
        service = AggregateRefreshService()
        result = service.build_snapshot(
            snapshot_id=args.snapshot_id,
            refresh_scope=args.refresh_scope,
            country_code=args.country_code,
            canonical_rows=canonical_rows,
            bank_codes=list(filter_scope["bank_codes"]),
            product_types=list(filter_scope["product_types"]),
            refreshed_at=_utc_now_iso(),
        )
        if args.persist_db:
            repository.persist_refresh_result(
                result=result,
                triggered_by_run_id=args.triggered_by_run_id,
            )
        output = result.to_dict()
        output["runtime"] = {
            "env_file": str(env_file) if env_file is not None else None,
            "loaded_env_key_count": len(loaded_env_keys),
            "persist_db": args.persist_db,
            "database_schema": repository.active_schema,
            "canonical_row_count": len(canonical_rows),
        }
        print(json.dumps(output, indent=2, ensure_ascii=True))
        return 0
    except Exception as exc:
        if args.persist_db and refresh_started:
            repository.mark_refresh_failed(
                snapshot_id=args.snapshot_id,
                error_summary=str(exc),
                completed_at=_utc_now_iso(),
            )
        raise


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
