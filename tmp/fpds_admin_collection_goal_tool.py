from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
API_SERVICE_ROOT = REPO_ROOT / "api" / "service"
if str(API_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api_service.config import Settings
from api_service.db import open_connection
from api_service.source_catalog import start_source_catalog_collection

GOLDEN_PATH = REPO_ROOT / "worker" / "pipeline" / "tests" / "fixtures" / "golden" / "canada_big5_deposit_products_golden_2026-05-23.json"
COMPARE_FIELDS = (
    "bank_name",
    "product_name",
    "highest_rate",
    "base_12_month_rate",
    "tags",
    "product_page_url",
    "signup_amount",
    "eligibility",
    "application_method",
    "post_maturity_interest_rate",
    "tax_benefits",
    "deposit_insurance",
    "term_rates",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS admin collection golden-match helper.")
    parser.add_argument("--env-file", default=".env.dev")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("state")
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--only-bank", action="append", default=[])
    launch_parser.add_argument("--only-product-type", action="append", default=[])

    poll_parser = subparsers.add_parser("poll")
    poll_parser.add_argument("--collection-id", required=True)
    poll_parser.add_argument("--brief", action="store_true")

    wait_parser = subparsers.add_parser("wait")
    wait_parser.add_argument("--collection-id", required=True)
    wait_parser.add_argument("--timeout-seconds", type=int, default=60)
    wait_parser.add_argument("--poll-seconds", type=int, default=10)
    wait_parser.add_argument("--brief", action="store_true")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--collection-id", required=True)
    compare_parser.add_argument("--report-path")

    args = parser.parse_args()
    settings = Settings.from_env(args.env_file)

    if args.command == "state":
        _print_json(load_state(settings))
        return 0
    if args.command == "launch":
        _print_json(launch_collection(settings, only_banks=args.only_bank, only_product_types=args.only_product_type))
        return 0
    if args.command == "poll":
        _print_json(_brief_status(load_collection_status(settings, collection_id=args.collection_id), brief=args.brief))
        return 0
    if args.command == "wait":
        _print_json(_brief_status(wait_for_collection(settings, collection_id=args.collection_id, timeout_seconds=args.timeout_seconds, poll_seconds=args.poll_seconds), brief=args.brief))
        return 0
    if args.command == "compare":
        result = compare_collection(settings, collection_id=args.collection_id)
        if args.report_path:
            report_path = Path(args.report_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
        _print_json(result)
        return 0
    raise AssertionError(args.command)


def load_state(settings: Settings) -> dict[str, Any]:
    with open_connection(settings) as connection:
        return {
            "registered": _registered_scope(connection),
            "artifact_counts": _artifact_counts(connection),
            "latest_collections": _latest_collections(connection),
        }


def launch_collection(settings: Settings, *, only_banks: list[str], only_product_types: list[str]) -> dict[str, Any]:
    only_bank_set = {item.strip().upper() for item in only_banks if item.strip()}
    only_product_type_set = {item.strip().lower() for item in only_product_types if item.strip()}
    with open_connection(settings) as connection:
        rows = _active_catalog_rows(connection)
        if only_bank_set:
            rows = [row for row in rows if str(row["bank_code"]).upper() in only_bank_set]
        if only_product_type_set:
            rows = [row for row in rows if str(row["product_type"]).lower() in only_product_type_set]
        catalog_item_ids = [str(row["catalog_item_id"]) for row in rows]
        if not catalog_item_ids:
            raise RuntimeError("No active source catalog items matched the requested admin bank/product-type scope.")

        result = start_source_catalog_collection(
            connection,
            catalog_item_ids=catalog_item_ids,
            actor=_actor(),
            request_context={
                "request_id": f"req_codex_goal_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                "ip_address": "127.0.0.1",
                "user_agent": "codex-admin-collection-goal-tool",
            },
        )
        result["catalog_scope"] = [
            {
                "catalog_item_id": str(row["catalog_item_id"]),
                "bank_code": str(row["bank_code"]),
                "bank_name": str(row["bank_name"]),
                "product_type": str(row["product_type"]),
            }
            for row in rows
        ]
        return result


def wait_for_collection(settings: Settings, *, collection_id: str, timeout_seconds: int, poll_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    status = load_collection_status(settings, collection_id=collection_id)
    while not status["terminal"] and time.monotonic() < deadline:
        time.sleep(max(1, poll_seconds))
        status = load_collection_status(settings, collection_id=collection_id)
    return status


def _brief_status(status: dict[str, Any], *, brief: bool) -> dict[str, Any]:
    if not brief:
        return status
    runs = status.get("runs") or []
    active_runs = [
        {
            "run_id": item["run_id"],
            "bank_code": item["bank_code"],
            "product_type": item["product_type"],
            "run_state": item["run_state"],
            "discovery_status": item["discovery_status"],
            "pipeline_stage": item["pipeline_stage"],
            "candidate_count": item["candidate_count"],
            "review_queued_count": item["review_queued_count"],
            "error_summary": item["error_summary"],
        }
        for item in runs
        if item.get("run_state") == "started" or item.get("error_summary")
    ]
    return {
        key: value
        for key, value in status.items()
        if key != "runs"
    } | {"active_or_error_runs": active_runs[:5]}


def load_collection_status(settings: Settings, *, collection_id: str) -> dict[str, Any]:
    with open_connection(settings) as connection:
        rows = connection.execute(
            """
            SELECT
                run_id,
                run_state,
                trigger_type,
                source_scope_count,
                source_success_count,
                source_failure_count,
                candidate_count,
                review_queued_count,
                partial_completion_flag,
                error_summary,
                run_metadata ->> 'bank_code' AS bank_code,
                run_metadata ->> 'product_type' AS product_type,
                run_metadata ->> 'discovery_status' AS discovery_status,
                run_metadata ->> 'pipeline_stage' AS pipeline_stage,
                run_metadata ? 'validation_stats' AS validation_done,
                started_at,
                completed_at
            FROM ingestion_run
            WHERE run_metadata ->> 'collection_id' = %(collection_id)s
            ORDER BY started_at, run_id
            """,
            {"collection_id": collection_id},
        ).fetchall()
        candidate_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
            """,
            {"collection_id": collection_id},
        ).fetchone()
        review_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM review_task AS rt
            JOIN ingestion_run AS ir
              ON ir.run_id = rt.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
            """,
            {"collection_id": collection_id},
        ).fetchone()
    state_counts = Counter(str(row["run_state"]) for row in rows)
    terminal = bool(rows) and all(_run_is_final(row) for row in rows)
    return {
        "collection_id": collection_id,
        "run_count": len(rows),
        "terminal": terminal,
        "state_counts": dict(sorted(state_counts.items())),
        "candidate_count": int(candidate_count["count"] or 0),
        "review_task_count": int(review_count["count"] or 0),
        "runs": [_serialize_run(row) for row in rows],
    }


def compare_collection(settings: Settings, *, collection_id: str) -> dict[str, Any]:
    golden_rows = _load_golden_products()
    actual_rows = _load_actual_products(settings, collection_id=collection_id)

    golden_by_key = {_identity_key(row): _project_compare_row(row) for row in golden_rows}
    actual_by_key = {_identity_key(row): _project_compare_row(row) for row in actual_rows}
    duplicate_actual_keys = _duplicate_keys(actual_rows)
    duplicate_golden_keys = _duplicate_keys(golden_rows)

    missing_keys = sorted(set(golden_by_key) - set(actual_by_key))
    extra_keys = sorted(set(actual_by_key) - set(golden_by_key))
    mismatches = []
    for key in sorted(set(golden_by_key) & set(actual_by_key)):
        field_diffs = {}
        golden = golden_by_key[key]
        actual = actual_by_key[key]
        for field_name in COMPARE_FIELDS:
            if actual.get(field_name) != golden.get(field_name):
                field_diffs[field_name] = {
                    "golden": golden.get(field_name),
                    "actual": actual.get(field_name),
                }
        if field_diffs:
            mismatches.append(
                {
                    "identity": _key_to_payload(key),
                    "fields": field_diffs,
                }
            )

    return {
        "collection_id": collection_id,
        "pass": not missing_keys and not extra_keys and not mismatches and not duplicate_actual_keys and not duplicate_golden_keys,
        "actual_count": len(actual_rows),
        "golden_count": len(golden_rows),
        "missing_count": len(missing_keys),
        "extra_count": len(extra_keys),
        "mismatch_count": len(mismatches),
        "duplicate_actual_count": len(duplicate_actual_keys),
        "duplicate_golden_count": len(duplicate_golden_keys),
        "missing": [_key_to_payload(key) for key in missing_keys[:50]],
        "extra": [_key_to_payload(key) for key in extra_keys[:50]],
        "mismatches": mismatches[:50],
        "duplicate_actual": [_key_to_payload(key) for key in duplicate_actual_keys[:50]],
        "duplicate_golden": [_key_to_payload(key) for key in duplicate_golden_keys[:50]],
        "compared_fields": list(COMPARE_FIELDS),
    }


def _active_catalog_rows(connection: Any) -> list[dict[str, Any]]:
    return list(
        connection.execute(
            """
            SELECT
                sci.catalog_item_id,
                sci.bank_code,
                b.bank_name,
                sci.product_type
            FROM source_registry_catalog_item AS sci
            JOIN bank AS b
              ON b.bank_code = sci.bank_code
            JOIN product_type_registry AS ptr
              ON ptr.product_family = 'deposit'
             AND ptr.product_type_code = sci.product_type
            WHERE sci.status = 'active'
              AND b.status = 'active'
              AND ptr.status = 'active'
            ORDER BY b.bank_name, sci.product_type, sci.catalog_item_id
            """
        ).fetchall()
    )


def _registered_scope(connection: Any) -> dict[str, Any]:
    bank_rows = connection.execute(
        """
        SELECT bank_code, bank_name, status
        FROM bank
        ORDER BY bank_name, bank_code
        """
    ).fetchall()
    product_type_rows = connection.execute(
        """
        SELECT product_type_code, display_name, status
        FROM product_type_registry
        WHERE product_family = 'deposit'
        ORDER BY display_name, product_type_code
        """
    ).fetchall()
    catalog_rows = _active_catalog_rows(connection)
    return {
        "banks": [dict(row) for row in bank_rows],
        "product_types": [dict(row) for row in product_type_rows],
        "active_catalog_item_count": len(catalog_rows),
        "active_catalog_items": [dict(row) for row in catalog_rows],
    }


def _artifact_counts(connection: Any) -> dict[str, int]:
    table_names = (
        "source_registry_item",
        "ingestion_run",
        "source_document",
        "source_snapshot",
        "parsed_document",
        "evidence_chunk",
        "evidence_chunk_embedding",
        "model_execution",
        "llm_usage_record",
        "normalized_candidate",
        "field_evidence_link",
        "review_task",
        "canonical_product",
        "product_version",
        "aggregate_refresh_run",
        "public_product_projection",
    )
    counts = {}
    for table_name in table_names:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        counts[table_name] = int(row["count"] or 0)
    return counts


def _latest_collections(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            run_metadata ->> 'collection_id' AS collection_id,
            MIN(started_at) AS started_at,
            MAX(completed_at) AS completed_at,
            COUNT(*) AS run_count,
            COUNT(*) FILTER (WHERE run_state = 'completed') AS completed_count,
            COUNT(*) FILTER (WHERE run_state = 'failed') AS failed_count,
            SUM(candidate_count) AS candidate_count,
            SUM(review_queued_count) AS review_queued_count
        FROM ingestion_run
        WHERE run_metadata ? 'collection_id'
        GROUP BY run_metadata ->> 'collection_id'
        ORDER BY MIN(started_at) DESC
        LIMIT 5
        """
    ).fetchall()
    return [_serialize_collection(row) for row in rows]


def _load_golden_products() -> list[dict[str, Any]]:
    payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return [dict(row) for row in payload["products"]]


def _load_actual_products(settings: Settings, *, collection_id: str) -> list[dict[str, Any]]:
    with open_connection(settings) as connection:
        rows = connection.execute(
            """
            SELECT
                nc.bank_code,
                nc.product_type,
                nc.product_name,
                nc.candidate_state,
                nc.candidate_payload
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
              AND nc.candidate_state NOT IN ('rejected', 'superseded')
            ORDER BY nc.bank_code, nc.product_type, nc.product_name, nc.candidate_id
            """,
            {"collection_id": collection_id},
        ).fetchall()
    actual_rows = []
    for row in rows:
        payload = dict(row["candidate_payload"] or {})
        payload.setdefault("bank_code", row["bank_code"])
        payload.setdefault("product_type", row["product_type"])
        payload.setdefault("product_name", row["product_name"])
        actual_rows.append(payload)
    return actual_rows


def _project_compare_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field_name: row.get(field_name) for field_name in COMPARE_FIELDS}


def _identity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _normalize_identity_text(row.get("bank_name")),
        _normalize_identity_text(row.get("product_type")),
        _normalize_identity_text(row.get("product_name")),
    )


def _normalize_identity_text(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _duplicate_keys(rows: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    counts = Counter(_identity_key(row) for row in rows)
    return sorted(key for key, count in counts.items() if count > 1)


def _key_to_payload(key: tuple[str, str, str]) -> dict[str, str]:
    bank_name, product_type, product_name = key
    return {
        "bank_name": bank_name,
        "product_type": product_type,
        "product_name": product_name,
    }


def _actor() -> dict[str, Any]:
    return {
        "user_id": "codex-admin-collection-test",
        "email": "codex@local",
        "display_name": "Codex Admin Collection Test",
        "role": "admin",
    }


def _serialize_collection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "collection_id": row["collection_id"],
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row["completed_at"]),
        "run_count": int(row["run_count"] or 0),
        "completed_count": int(row["completed_count"] or 0),
        "failed_count": int(row["failed_count"] or 0),
        "candidate_count": int(row["candidate_count"] or 0),
        "review_queued_count": int(row["review_queued_count"] or 0),
    }


def _serialize_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "run_state": row["run_state"],
        "trigger_type": row["trigger_type"],
        "bank_code": row["bank_code"],
        "product_type": row["product_type"],
        "discovery_status": row["discovery_status"],
        "pipeline_stage": row["pipeline_stage"],
        "validation_done": bool(row["validation_done"]),
        "source_scope_count": int(row["source_scope_count"] or 0),
        "source_success_count": int(row["source_success_count"] or 0),
        "source_failure_count": int(row["source_failure_count"] or 0),
        "candidate_count": int(row["candidate_count"] or 0),
        "review_queued_count": int(row["review_queued_count"] or 0),
        "partial_completion_flag": bool(row["partial_completion_flag"]),
        "error_summary": row["error_summary"],
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row["completed_at"]),
    }


def _run_is_final(row: dict[str, Any]) -> bool:
    run_state = str(row["run_state"])
    if run_state in {"failed", "retried"}:
        return True
    if run_state != "completed":
        return False
    return bool(row["validation_done"]) or row["pipeline_stage"] == "validation_routing"


def _iso(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True, default=str))


if __name__ == "__main__":
    raise SystemExit(main())
