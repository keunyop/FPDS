from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Sequence

from .capture import CaptureSource, ExistingSnapshotRecord, SnapshotCaptureResult

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class SnapshotDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "SnapshotDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for snapshot DB persistence")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


@dataclass(frozen=True)
class SnapshotPersistenceResult:
    run_id: str
    run_state: str
    source_document_count: int
    stored_snapshot_count: int
    run_source_item_count: int
    source_success_count: int
    source_failure_count: int
    partial_completion_flag: bool
    started_at: str
    completed_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_state": self.run_state,
            "source_document_count": self.source_document_count,
            "stored_snapshot_count": self.stored_snapshot_count,
            "run_source_item_count": self.run_source_item_count,
            "source_success_count": self.source_success_count,
            "source_failure_count": self.source_failure_count,
            "partial_completion_flag": self.partial_completion_flag,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class PsqlSnapshotRepository:
    def __init__(
        self,
        config: SnapshotDatabaseConfig,
        *,
        command_runner: Callable[[Sequence[str], str], str] | None = None,
    ):
        self.config = config
        self.command_runner = command_runner or self._run_psql
        self._resolved_schema: str | None = None

    def start_ingestion_run(
        self,
        *,
        run_id: str,
        trigger_type: str,
        triggered_by: str | None,
        source_scope_count: int,
        correlation_id: str | None,
        request_id: str | None,
        source_ids: list[str],
        started_at: str,
    ) -> None:
        schema = self.active_schema
        run_metadata = {
            "pipeline_stage": "snapshot_capture",
            "correlation_id": correlation_id,
            "request_id": request_id,
            "source_ids": source_ids,
        }
        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

INSERT INTO ingestion_run (
    run_id,
    run_state,
    trigger_type,
    triggered_by,
    source_scope_count,
    source_success_count,
    source_failure_count,
    candidate_count,
    review_queued_count,
    error_summary,
    partial_completion_flag,
    retry_of_run_id,
    retried_by_run_id,
    run_metadata,
    started_at,
    completed_at
)
VALUES (
    :'run_id',
    'started',
    :'trigger_type',
    NULLIF(:'triggered_by', ''),
    :'source_scope_count'::integer,
    0,
    0,
    0,
    0,
    NULL,
    false,
    NULL,
    NULL,
    :'run_metadata'::jsonb,
    :'started_at'::timestamptz,
    NULL
)
ON CONFLICT (run_id) DO UPDATE SET
    run_state = 'started',
    trigger_type = EXCLUDED.trigger_type,
    triggered_by = EXCLUDED.triggered_by,
    source_scope_count = EXCLUDED.source_scope_count,
    source_success_count = 0,
    source_failure_count = 0,
    candidate_count = 0,
    review_queued_count = 0,
    error_summary = NULL,
    partial_completion_flag = false,
    run_metadata = ingestion_run.run_metadata || EXCLUDED.run_metadata,
    started_at = LEAST(ingestion_run.started_at, EXCLUDED.started_at),
    completed_at = NULL;

COMMIT;
"""
        self._execute(
            sql,
            variables={
                "run_id": run_id,
                "trigger_type": trigger_type,
                "triggered_by": triggered_by or "",
                "source_scope_count": str(source_scope_count),
                "run_metadata": json.dumps(run_metadata, ensure_ascii=True),
                "started_at": started_at,
            },
        )

    def load_existing_snapshots(self, *, source_document_ids: list[str]) -> list[ExistingSnapshotRecord]:
        if not source_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(snapshot_rows)), '[]'::json)::text
FROM (
    SELECT
        snapshot_id,
        source_document_id,
        object_storage_key,
        content_type,
        checksum,
        fingerprint,
        fetch_status,
        response_metadata,
        retention_class,
        replace(fetched_at::text, ' ', 'T') AS fetched_at
    FROM source_snapshot
    WHERE source_document_id IN (
        SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb)
    )
) AS snapshot_rows;
"""
        output = self._execute(
            sql,
            variables={
                "source_document_ids_json": json.dumps(source_document_ids, ensure_ascii=True),
            },
        )
        payload = json.loads(output or "[]")
        return [ExistingSnapshotRecord(**item) for item in payload]

    def persist_capture_result(
        self,
        *,
        run_id: str,
        sources: list[CaptureSource],
        capture_result: SnapshotCaptureResult,
        trigger_type: str,
        triggered_by: str | None,
        started_at: str,
        completed_at: str,
    ) -> SnapshotPersistenceResult:
        schema = self.active_schema
        source_documents = [
            source.to_source_document_record(discovered_at=started_at)
            for source in sources
        ]
        source_snapshots = [
            item.source_snapshot_record
            for item in capture_result.source_results
            if item.source_snapshot_record is not None
        ]
        run_source_items = [item.run_source_item_record for item in capture_result.source_results]
        source_failure_count = sum(1 for item in capture_result.source_results if item.snapshot_action == "failed")
        source_success_count = len(capture_result.source_results) - source_failure_count
        run_state = "failed" if source_failure_count == len(capture_result.source_results) else "completed"
        error_summary = _build_run_error_summary(
            total=len(capture_result.source_results),
            failures=source_failure_count,
        )
        final_run_metadata = {
            "pipeline_stage": "snapshot_capture",
            "trigger_type": trigger_type,
            "triggered_by": triggered_by,
            "correlation_id": capture_result.correlation_id,
            "request_id": capture_result.request_id,
            "snapshot_stats": capture_result.to_dict()["stats"],
            "source_ids": [source.source_id for source in sources],
        }
        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

WITH source_document_payload AS (
    SELECT *
    FROM jsonb_to_recordset(:'source_documents_json'::jsonb) AS payload(
        source_document_id text,
        bank_code text,
        country_code text,
        normalized_source_url text,
        source_type text,
        source_language text,
        registry_managed_flag boolean,
        source_metadata jsonb,
        discovered_at timestamptz
    )
)
INSERT INTO source_document (
    source_document_id,
    bank_code,
    country_code,
    normalized_source_url,
    source_type,
    source_language,
    registry_managed_flag,
    source_metadata,
    discovered_at
)
SELECT
    source_document_id,
    bank_code,
    country_code,
    normalized_source_url,
    source_type,
    source_language,
    registry_managed_flag,
    source_metadata,
    discovered_at
FROM source_document_payload
ON CONFLICT (source_document_id) DO UPDATE SET
    bank_code = EXCLUDED.bank_code,
    country_code = EXCLUDED.country_code,
    normalized_source_url = EXCLUDED.normalized_source_url,
    source_type = EXCLUDED.source_type,
    source_language = EXCLUDED.source_language,
    registry_managed_flag = EXCLUDED.registry_managed_flag,
    source_metadata = EXCLUDED.source_metadata,
    discovered_at = LEAST(source_document.discovered_at, EXCLUDED.discovered_at),
    updated_at = now();

WITH source_snapshot_payload AS (
    SELECT *
    FROM jsonb_to_recordset(:'source_snapshots_json'::jsonb) AS payload(
        snapshot_id text,
        source_document_id text,
        object_storage_key text,
        content_type text,
        checksum text,
        fingerprint text,
        fetch_status text,
        response_metadata jsonb,
        retention_class text,
        fetched_at timestamptz
    )
)
INSERT INTO source_snapshot (
    snapshot_id,
    source_document_id,
    object_storage_key,
    content_type,
    checksum,
    fingerprint,
    fetch_status,
    response_metadata,
    retention_class,
    fetched_at
)
SELECT
    snapshot_id,
    source_document_id,
    object_storage_key,
    content_type,
    checksum,
    fingerprint,
    fetch_status,
    response_metadata,
    retention_class,
    fetched_at
FROM source_snapshot_payload
ON CONFLICT (snapshot_id) DO NOTHING;

WITH run_source_item_payload AS (
    SELECT *
    FROM jsonb_to_recordset(:'run_source_items_json'::jsonb) AS payload(
        run_source_item_id text,
        run_id text,
        source_document_id text,
        selected_snapshot_id text,
        stage_status text,
        warning_count integer,
        error_count integer,
        error_summary text,
        stage_metadata jsonb
    )
)
INSERT INTO run_source_item (
    run_source_item_id,
    run_id,
    source_document_id,
    selected_snapshot_id,
    stage_status,
    warning_count,
    error_count,
    error_summary,
    stage_metadata
)
SELECT
    run_source_item_id,
    run_id,
    source_document_id,
    selected_snapshot_id,
    stage_status,
    warning_count,
    error_count,
    error_summary,
    stage_metadata
FROM run_source_item_payload
ON CONFLICT (run_id, source_document_id) DO UPDATE SET
    selected_snapshot_id = EXCLUDED.selected_snapshot_id,
    stage_status = EXCLUDED.stage_status,
    warning_count = EXCLUDED.warning_count,
    error_count = EXCLUDED.error_count,
    error_summary = EXCLUDED.error_summary,
    stage_metadata = EXCLUDED.stage_metadata,
    updated_at = now();

UPDATE ingestion_run
SET
    run_state = :'run_state',
    trigger_type = :'trigger_type',
    triggered_by = NULLIF(:'triggered_by', ''),
    source_scope_count = :'source_scope_count'::integer,
    source_success_count = :'source_success_count'::integer,
    source_failure_count = :'source_failure_count'::integer,
    error_summary = NULLIF(:'error_summary', ''),
    partial_completion_flag = :'partial_completion_flag'::boolean,
    run_metadata = run_metadata || :'run_metadata'::jsonb,
    completed_at = :'completed_at'::timestamptz
WHERE run_id = :'run_id';

COMMIT;
"""
        self._execute(
            sql,
            variables={
                "source_documents_json": json.dumps(source_documents, ensure_ascii=True),
                "source_snapshots_json": json.dumps(source_snapshots, ensure_ascii=True),
                "run_source_items_json": json.dumps(run_source_items, ensure_ascii=True),
                "run_id": run_id,
                "run_state": run_state,
                "trigger_type": trigger_type,
                "triggered_by": triggered_by or "",
                "source_scope_count": str(len(capture_result.source_results)),
                "source_success_count": str(source_success_count),
                "source_failure_count": str(source_failure_count),
                "error_summary": error_summary or "",
                "partial_completion_flag": str(capture_result.partial_completion_flag).lower(),
                "run_metadata": json.dumps(final_run_metadata, ensure_ascii=True),
                "completed_at": completed_at,
            },
        )
        return SnapshotPersistenceResult(
            run_id=run_id,
            run_state=run_state,
            source_document_count=len(source_documents),
            stored_snapshot_count=len(source_snapshots),
            run_source_item_count=len(run_source_items),
            source_success_count=source_success_count,
            source_failure_count=source_failure_count,
            partial_completion_flag=capture_result.partial_completion_flag,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @property
    def active_schema(self) -> str:
        if self._resolved_schema is None:
            self._resolved_schema = self._resolve_active_schema()
        return self._resolved_schema

    def _resolve_active_schema(self) -> str:
        preferred = self.config.schema
        sql = """
SELECT COALESCE((
    SELECT schemaname
    FROM pg_tables
    WHERE tablename IN ('ingestion_run', 'source_document', 'source_snapshot', 'run_source_item')
    GROUP BY schemaname
    HAVING count(DISTINCT tablename) = 4
    ORDER BY
        CASE
            WHEN schemaname = :'preferred_schema' THEN 0
            WHEN schemaname = 'public' THEN 1
            ELSE 2
        END,
        schemaname
    LIMIT 1
), '');
"""
        output = self._execute(sql, variables={"preferred_schema": preferred})
        resolved = output.strip()
        if resolved:
            return resolved
        raise RuntimeError(
            "Could not find ingestion snapshot tables in the configured schema or in public."
        )

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        completed = subprocess.run(
            [*command, "-X", "-q", "-A", "-t"],
            input=sql,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown psql error"
            raise RuntimeError(f"psql command failed: {stderr}")
        return completed.stdout.strip()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _build_run_error_summary(*, total: int, failures: int) -> str | None:
    if failures == 0:
        return None
    if failures == total:
        return f"Snapshot capture failed for all {total} sources."
    return f"Snapshot capture failed for {failures} of {total} sources."
