from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
API_SERVICE_ROOT = REPO_ROOT / "api" / "service"
if str(API_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api_service.config import Settings  # noqa: E402
from api_service.db import open_connection  # noqa: E402


PRESERVED_TABLES = (
    "bank",
    "product_type_registry",
    "taxonomy_registry",
    "source_registry_catalog_item",
    "processing_policy_config",
    "migration_history",
    "user_account",
    "admin_auth_session",
    "auth_login_attempt",
    "user_signup_request",
)

COLLECTION_TABLES = (
    "source_registry_item",
    "ingestion_run",
    "source_document",
    "source_snapshot",
    "run_source_item",
    "parsed_document",
    "evidence_chunk",
    "evidence_chunk_embedding",
    "model_execution",
    "llm_usage_record",
    "normalized_candidate",
    "field_evidence_link",
    "review_task",
    "review_decision",
    "canonical_product",
    "product_version",
    "change_event",
    "publish_item",
    "publish_attempt",
    "aggregate_refresh_request",
    "aggregate_refresh_run",
    "public_product_projection",
    "dashboard_metric_snapshot",
    "dashboard_ranking_snapshot",
    "dashboard_scatter_snapshot",
)

DELETE_STATEMENTS = (
    (
        "audit_event_collection_rows",
        """
        DELETE FROM audit_event
        WHERE event_category IN ('review', 'run', 'publish', 'usage')
           OR run_id IS NOT NULL
           OR candidate_id IS NOT NULL
           OR review_task_id IS NOT NULL
           OR product_id IS NOT NULL
           OR publish_item_id IS NOT NULL
           OR target_type IN (
                'run',
                'ingestion_run',
                'candidate',
                'normalized_candidate',
                'review_task',
                'product',
                'canonical_product',
                'product_version',
                'publish_item',
                'publish_attempt',
                'model_execution',
                'llm_usage_record',
                'source_document',
                'source_snapshot',
                'parsed_document',
                'evidence_chunk',
                'aggregate_refresh_request',
                'aggregate_refresh_run',
                'public_product_projection',
                'dashboard_metric_snapshot',
                'dashboard_ranking_snapshot',
                'dashboard_scatter_snapshot',
                'source_registry_item'
           )
        """,
    ),
    ("aggregate_refresh_request", "DELETE FROM aggregate_refresh_request"),
    ("dashboard_scatter_snapshot", "DELETE FROM dashboard_scatter_snapshot"),
    ("dashboard_ranking_snapshot", "DELETE FROM dashboard_ranking_snapshot"),
    ("dashboard_metric_snapshot", "DELETE FROM dashboard_metric_snapshot"),
    ("public_product_projection", "DELETE FROM public_product_projection"),
    ("aggregate_refresh_run", "DELETE FROM aggregate_refresh_run"),
    ("publish_attempt", "DELETE FROM publish_attempt"),
    ("publish_item", "DELETE FROM publish_item"),
    ("change_event", "DELETE FROM change_event"),
    ("field_evidence_link", "DELETE FROM field_evidence_link"),
    ("llm_usage_record", "DELETE FROM llm_usage_record"),
    ("review_decision", "DELETE FROM review_decision"),
    ("review_task", "DELETE FROM review_task"),
    ("product_version", "DELETE FROM product_version"),
    ("normalized_candidate", "DELETE FROM normalized_candidate"),
    ("canonical_product", "DELETE FROM canonical_product"),
    ("model_execution", "DELETE FROM model_execution"),
    ("evidence_chunk_embedding", "DELETE FROM evidence_chunk_embedding"),
    ("evidence_chunk", "DELETE FROM evidence_chunk"),
    ("parsed_document", "DELETE FROM parsed_document"),
    ("run_source_item", "DELETE FROM run_source_item"),
    ("source_snapshot", "DELETE FROM source_snapshot"),
    ("source_document", "DELETE FROM source_document"),
    ("ingestion_run", "DELETE FROM ingestion_run"),
    ("source_registry_item", "DELETE FROM source_registry_item"),
)


def load_settings(env_file: str) -> Settings:
    settings = Settings.from_env(env_file)
    _map_storage_env_for_aws()
    return settings


def collect_db_counts(settings: Settings) -> dict[str, Any]:
    with open_connection(settings) as connection:
        return {
            "preserved": count_tables(connection, PRESERVED_TABLES),
            "collection_artifacts": count_tables(connection, COLLECTION_TABLES),
            "audit_event": {
                "total": table_count(connection, "audit_event"),
                "by_category": grouped_counts(connection, "event_category"),
                "collection_related": collection_related_audit_count(connection),
            },
        }


def reset_db_collection_artifacts(settings: Settings) -> dict[str, Any]:
    with open_connection(settings) as connection:
        before = collect_counts_inside_connection(connection)
        deleted: dict[str, int] = {}
        for label, statement in DELETE_STATEMENTS:
            cursor = connection.execute(statement)
            deleted[label] = int(cursor.rowcount or 0)
        after = collect_counts_inside_connection(connection)
        return {"before": before, "deleted": deleted, "after": after}


def collect_counts_inside_connection(connection: Any) -> dict[str, Any]:
    return {
        "preserved": count_tables(connection, PRESERVED_TABLES),
        "collection_artifacts": count_tables(connection, COLLECTION_TABLES),
        "audit_event": {
            "total": table_count(connection, "audit_event"),
            "by_category": grouped_counts(connection, "event_category"),
            "collection_related": collection_related_audit_count(connection),
        },
    }


def count_tables(connection: Any, table_names: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in table_names:
        if table_exists(connection, table_name):
            counts[table_name] = table_count(connection, table_name)
    return counts


def table_exists(connection: Any, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT to_regclass(%(table_name)s) IS NOT NULL AS exists
        """,
        {"table_name": f"public.{table_name}"},
    ).fetchone()
    return bool(row["exists"])


def table_count(connection: Any, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"] or 0)


def grouped_counts(connection: Any, column_name: str) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT {column_name} AS key, COUNT(*) AS count
        FROM audit_event
        GROUP BY {column_name}
        ORDER BY {column_name}
        """
    ).fetchall()
    return {str(row["key"]): int(row["count"] or 0) for row in rows}


def collection_related_audit_count(connection: Any) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM audit_event
        WHERE event_category IN ('review', 'run', 'publish', 'usage')
           OR run_id IS NOT NULL
           OR candidate_id IS NOT NULL
           OR review_task_id IS NOT NULL
           OR product_id IS NOT NULL
           OR publish_item_id IS NOT NULL
           OR target_type IN (
                'run',
                'ingestion_run',
                'candidate',
                'normalized_candidate',
                'review_task',
                'product',
                'canonical_product',
                'product_version',
                'publish_item',
                'publish_attempt',
                'model_execution',
                'llm_usage_record',
                'source_document',
                'source_snapshot',
                'parsed_document',
                'evidence_chunk',
                'aggregate_refresh_request',
                'aggregate_refresh_run',
                'public_product_projection',
                'dashboard_metric_snapshot',
                'dashboard_ranking_snapshot',
                'dashboard_scatter_snapshot',
                'source_registry_item'
           )
        """
    ).fetchone()
    return int(row["count"] or 0)


def collect_s3_summary() -> dict[str, Any]:
    config = storage_config()
    if config["driver"] not in {"s3", "s3-compatible"}:
        return {"driver": config["driver"], "skipped": True, "reason": "non_s3_storage_driver"}
    objects = list_s3_objects(config)
    return {
        "driver": config["driver"],
        "bucket": config["bucket"],
        "prefix": config["prefix"],
        "object_count": len(objects),
        "total_bytes": sum(int(item.get("Size") or 0) for item in objects),
    }


def delete_s3_prefix() -> dict[str, Any]:
    config = storage_config()
    before = collect_s3_summary()
    if config["driver"] not in {"s3", "s3-compatible"}:
        return {"before": before, "deleted_objects": 0, "after": before}
    objects = list_s3_objects(config)
    deleted_objects = 0
    for start in range(0, len(objects), 1000):
        batch = objects[start : start + 1000]
        deleted_objects += delete_s3_batch(config, batch)
    after = collect_s3_summary()
    return {"before": before, "deleted_objects": deleted_objects, "after": after}


def storage_config() -> dict[str, str | None]:
    driver = os.getenv("FPDS_OBJECT_STORAGE_DRIVER", "s3-compatible").strip().lower()
    bucket = os.getenv("FPDS_OBJECT_STORAGE_BUCKET")
    prefix = os.getenv("FPDS_OBJECT_STORAGE_PREFIX", os.getenv("FPDS_EVIDENCE_PREFIX_ROOT", "dev"))
    if prefix:
        prefix = prefix.strip("/")
        if prefix:
            prefix = f"{prefix}/"
    endpoint = os.getenv("FPDS_OBJECT_STORAGE_ENDPOINT") or None
    region = os.getenv("FPDS_OBJECT_STORAGE_REGION") or None
    return {
        "driver": driver,
        "bucket": bucket,
        "prefix": prefix,
        "endpoint": endpoint,
        "region": region,
    }


def list_s3_objects(config: dict[str, str | None]) -> list[dict[str, Any]]:
    if not config["bucket"]:
        raise RuntimeError("FPDS_OBJECT_STORAGE_BUCKET is required for S3 reset")
    objects: list[dict[str, Any]] = []
    token: str | None = None
    while True:
        command = [
            "aws",
            "s3api",
            "list-objects-v2",
            "--bucket",
            str(config["bucket"]),
            "--prefix",
            str(config["prefix"] or ""),
            "--output",
            "json",
        ]
        if token:
            command.extend(["--continuation-token", token])
        add_aws_scope_args(command, config)
        completed = run_aws(command)
        payload = json.loads(completed.stdout or "{}")
        objects.extend(payload.get("Contents") or [])
        token = payload.get("NextContinuationToken")
        if not token:
            break
    return objects


def delete_s3_batch(config: dict[str, str | None], objects: list[dict[str, Any]]) -> int:
    if not objects:
        return 0
    delete_payload = {
        "Objects": [{"Key": item["Key"]} for item in objects],
        "Quiet": True,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(delete_payload, handle)
        tmp_path = Path(handle.name)
    try:
        command = [
            "aws",
            "s3api",
            "delete-objects",
            "--bucket",
            str(config["bucket"]),
            "--delete",
            f"file://{tmp_path}",
            "--output",
            "json",
        ]
        add_aws_scope_args(command, config)
        run_aws(command)
        return len(objects)
    finally:
        tmp_path.unlink(missing_ok=True)


def add_aws_scope_args(command: list[str], config: dict[str, str | None]) -> None:
    if config.get("region"):
        command.extend(["--region", str(config["region"])])
    if config.get("endpoint"):
        command.extend(["--endpoint-url", str(config["endpoint"])])


def run_aws(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False, env=os.environ.copy())
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown aws error"
        raise RuntimeError(f"AWS CLI failed: {stderr}")
    return completed


def _map_storage_env_for_aws() -> None:
    access_key = os.getenv("FPDS_STORAGE_ACCESS_KEY")
    secret_key = os.getenv("FPDS_STORAGE_SECRET_KEY")
    region = os.getenv("FPDS_OBJECT_STORAGE_REGION")
    if access_key:
        os.environ.setdefault("AWS_ACCESS_KEY_ID", access_key)
    if secret_key:
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", secret_key)
    if region:
        os.environ.setdefault("AWS_DEFAULT_REGION", region)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True, default=str))
