from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Sequence

from worker.psql_cli import run_psql_command

from .models import ExtractionDocumentContext, ExtractionResult

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ExtractionDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "ExtractionDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for extraction DB persistence")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


@dataclass(frozen=True)
class ExtractionPersistenceResult:
    run_id: str
    run_state: str
    model_execution_count: int
    usage_record_count: int
    run_source_item_count: int
    extracted_draft_count: int
    source_success_count: int
    source_failure_count: int
    partial_completion_flag: bool
    completed_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_state": self.run_state,
            "model_execution_count": self.model_execution_count,
            "usage_record_count": self.usage_record_count,
            "run_source_item_count": self.run_source_item_count,
            "extracted_draft_count": self.extracted_draft_count,
            "source_success_count": self.source_success_count,
            "source_failure_count": self.source_failure_count,
            "partial_completion_flag": self.partial_completion_flag,
            "completed_at": self.completed_at,
        }


class PsqlExtractionRepository:
    def __init__(
        self,
        config: ExtractionDatabaseConfig,
        *,
        command_runner: Callable[[Sequence[str], str], str] | None = None,
    ) -> None:
        self.config = config
        self.command_runner = command_runner or self._run_psql
        self._resolved_schema: str | None = None

    @property
    def active_schema(self) -> str:
        if self._resolved_schema is None:
            self._resolved_schema = self._resolve_active_schema()
        return self._resolved_schema

    def ensure_ingestion_run(
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
            "pipeline_stage": "extraction",
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
    triggered_by = COALESCE(EXCLUDED.triggered_by, ingestion_run.triggered_by),
    source_scope_count = GREATEST(ingestion_run.source_scope_count, EXCLUDED.source_scope_count),
    run_metadata = ingestion_run.run_metadata || EXCLUDED.run_metadata,
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

    def load_latest_document_contexts(
        self,
        *,
        source_document_ids: list[str],
    ) -> list[ExtractionDocumentContext]:
        if not source_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(context_rows)), '[]'::json)::text
FROM (
    SELECT DISTINCT ON (ss.source_document_id)
        pd.parsed_document_id,
        pd.snapshot_id,
        ss.source_document_id,
        sd.bank_code,
        sd.country_code,
        sd.source_type,
        sd.source_language,
        sd.source_metadata
    FROM parsed_document AS pd
    JOIN source_snapshot AS ss
      ON ss.snapshot_id = pd.snapshot_id
    JOIN source_document AS sd
      ON sd.source_document_id = ss.source_document_id
    WHERE ss.source_document_id IN (
        SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb)
    )
    ORDER BY ss.source_document_id, pd.parsed_at DESC, pd.created_at DESC
) AS context_rows;
"""
        output = self._execute(
            sql,
            variables={"source_document_ids_json": json.dumps(source_document_ids, ensure_ascii=True)},
        )
        payload = json.loads(output or "[]")
        return [ExtractionDocumentContext(**item) for item in payload]

    def load_document_contexts_by_parsed_document_ids(
        self,
        *,
        parsed_document_ids: list[str],
    ) -> list[ExtractionDocumentContext]:
        if not parsed_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(context_rows)), '[]'::json)::text
FROM (
    SELECT
        pd.parsed_document_id,
        pd.snapshot_id,
        ss.source_document_id,
        sd.bank_code,
        sd.country_code,
        sd.source_type,
        sd.source_language,
        sd.source_metadata
    FROM parsed_document AS pd
    JOIN source_snapshot AS ss
      ON ss.snapshot_id = pd.snapshot_id
    JOIN source_document AS sd
      ON sd.source_document_id = ss.source_document_id
    WHERE pd.parsed_document_id IN (
        SELECT jsonb_array_elements_text(:'parsed_document_ids_json'::jsonb)
    )
    ORDER BY pd.parsed_document_id
) AS context_rows;
"""
        output = self._execute(
            sql,
            variables={"parsed_document_ids_json": json.dumps(parsed_document_ids, ensure_ascii=True)},
        )
        payload = json.loads(output or "[]")
        return [ExtractionDocumentContext(**item) for item in payload]

    def load_chunk_candidates(self, *, parsed_document_id: str) -> list[dict[str, object]]:
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(candidate_rows)), '[]'::json)::text
FROM (
    SELECT
        ec.evidence_chunk_id,
        ec.parsed_document_id,
        ec.chunk_index,
        ec.anchor_type,
        ec.anchor_value,
        ec.page_no,
        ec.source_language,
        ec.evidence_excerpt,
        ec.retrieval_metadata,
        ss.source_document_id,
        ss.snapshot_id AS source_snapshot_id,
        sd.bank_code,
        sd.country_code,
        sd.source_type
    FROM evidence_chunk AS ec
    JOIN parsed_document AS pd
      ON pd.parsed_document_id = ec.parsed_document_id
    JOIN source_snapshot AS ss
      ON ss.snapshot_id = pd.snapshot_id
    JOIN source_document AS sd
      ON sd.source_document_id = ss.source_document_id
    WHERE ec.parsed_document_id = :'parsed_document_id'
    ORDER BY ec.chunk_index
) AS candidate_rows;
"""
        output = self._execute(sql, variables={"parsed_document_id": parsed_document_id})
        return json.loads(output or "[]")

    def persist_extraction_result(
        self,
        *,
        run_id: str,
        extraction_result: ExtractionResult,
        trigger_type: str,
        triggered_by: str | None,
        completed_at: str,
    ) -> ExtractionPersistenceResult:
        schema = self.active_schema
        model_executions = [item.model_execution_record for item in extraction_result.source_results]
        usage_records = [item.usage_record for item in extraction_result.source_results if item.usage_record is not None]
        run_source_items = [item.run_source_item_record for item in extraction_result.source_results]
        source_failure_count = sum(1 for item in extraction_result.source_results if item.extraction_action == "failed")
        source_success_count = len(extraction_result.source_results) - source_failure_count
        extracted_draft_count = sum(1 for item in extraction_result.source_results if item.extraction_action == "stored")
        run_state = "failed" if source_failure_count == len(extraction_result.source_results) else "completed"
        error_summary = _build_run_error_summary(total=len(extraction_result.source_results), failures=source_failure_count)
        run_metadata = {
            "pipeline_stage": "extraction",
            "trigger_type": trigger_type,
            "triggered_by": triggered_by,
            "correlation_id": extraction_result.correlation_id,
            "request_id": extraction_result.request_id,
            "extraction_stats": extraction_result.to_dict()["stats"],
        }
        model_executions_json_literal = _json_sql_literal(model_executions)
        usage_records_json_literal = _json_sql_literal(usage_records)
        run_source_items_json_literal = _json_sql_literal(run_source_items)
        run_metadata_json_literal = _json_sql_literal(run_metadata)

        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

WITH model_execution_payload AS (
    SELECT *
    FROM jsonb_to_recordset({model_executions_json_literal}::jsonb) AS payload(
        model_execution_id text,
        run_id text,
        source_document_id text,
        stage_name text,
        agent_name text,
        model_id text,
        execution_status text,
        execution_metadata jsonb,
        started_at timestamptz,
        completed_at timestamptz
    )
)
INSERT INTO model_execution (
    model_execution_id,
    run_id,
    source_document_id,
    stage_name,
    agent_name,
    model_id,
    execution_status,
    execution_metadata,
    started_at,
    completed_at
)
SELECT
    model_execution_id,
    run_id,
    source_document_id,
    stage_name,
    agent_name,
    model_id,
    execution_status,
    execution_metadata,
    started_at,
    completed_at
FROM model_execution_payload
ON CONFLICT (model_execution_id) DO UPDATE SET
    execution_status = EXCLUDED.execution_status,
    execution_metadata = EXCLUDED.execution_metadata,
    completed_at = EXCLUDED.completed_at;

WITH llm_usage_payload AS (
    SELECT *
    FROM jsonb_to_recordset({usage_records_json_literal}::jsonb) AS payload(
        llm_usage_id text,
        model_execution_id text,
        run_id text,
        candidate_id text,
        provider_request_id text,
        prompt_tokens integer,
        completion_tokens integer,
        estimated_cost numeric(12,6),
        usage_metadata jsonb,
        recorded_at timestamptz
    )
)
INSERT INTO llm_usage_record (
    llm_usage_id,
    model_execution_id,
    run_id,
    candidate_id,
    provider_request_id,
    prompt_tokens,
    completion_tokens,
    estimated_cost,
    usage_metadata,
    recorded_at
)
SELECT
    llm_usage_id,
    model_execution_id,
    run_id,
    candidate_id,
    provider_request_id,
    prompt_tokens,
    completion_tokens,
    estimated_cost,
    usage_metadata,
    recorded_at
FROM llm_usage_payload
ON CONFLICT (llm_usage_id) DO UPDATE SET
    prompt_tokens = EXCLUDED.prompt_tokens,
    completion_tokens = EXCLUDED.completion_tokens,
    estimated_cost = EXCLUDED.estimated_cost,
    usage_metadata = EXCLUDED.usage_metadata,
    recorded_at = EXCLUDED.recorded_at;

WITH run_source_item_payload AS (
    SELECT *
    FROM jsonb_to_recordset({run_source_items_json_literal}::jsonb) AS payload(
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
    stage_metadata = run_source_item.stage_metadata || EXCLUDED.stage_metadata,
    updated_at = now();

UPDATE ingestion_run
SET
    run_state = :'run_state',
    trigger_type = :'trigger_type',
    triggered_by = NULLIF(:'triggered_by', ''),
    source_scope_count = :'source_scope_count'::integer,
    source_success_count = :'source_success_count'::integer,
    source_failure_count = :'source_failure_count'::integer,
    candidate_count = :'candidate_count'::integer,
    error_summary = NULLIF(:'error_summary', ''),
    partial_completion_flag = :'partial_completion_flag'::boolean,
    run_metadata = ingestion_run.run_metadata || {run_metadata_json_literal}::jsonb,
    completed_at = :'completed_at'::timestamptz
WHERE run_id = :'run_id';

COMMIT;
"""
        self._execute(
            sql,
            variables={
                "run_id": run_id,
                "run_state": run_state,
                "trigger_type": trigger_type,
                "triggered_by": triggered_by or "",
                "source_scope_count": str(len(extraction_result.source_results)),
                "source_success_count": str(source_success_count),
                "source_failure_count": str(source_failure_count),
                "candidate_count": str(extracted_draft_count),
                "error_summary": error_summary or "",
                "partial_completion_flag": str(extraction_result.partial_completion_flag).lower(),
                "completed_at": completed_at,
            },
        )
        return ExtractionPersistenceResult(
            run_id=run_id,
            run_state=run_state,
            model_execution_count=len(model_executions),
            usage_record_count=len(usage_records),
            run_source_item_count=len(run_source_items),
            extracted_draft_count=extracted_draft_count,
            source_success_count=source_success_count,
            source_failure_count=source_failure_count,
            partial_completion_flag=extraction_result.partial_completion_flag,
            completed_at=completed_at,
        )

    def _resolve_active_schema(self) -> str:
        preferred = self.config.schema
        sql = """
SELECT COALESCE((
    SELECT schemaname
    FROM pg_tables
    WHERE tablename IN (
        'ingestion_run',
        'run_source_item',
        'source_document',
        'source_snapshot',
        'parsed_document',
        'evidence_chunk',
        'model_execution',
        'llm_usage_record'
    )
    GROUP BY schemaname
    HAVING count(DISTINCT tablename) = 8
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
        raise RuntimeError("Could not find extraction tables in the configured schema or in public.")

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        return run_psql_command(command, sql, force_utf8=True)


def _build_run_error_summary(*, total: int, failures: int) -> str | None:
    if failures == 0:
        return None
    if failures == total:
        return f"Extraction failed for all {total} sources."
    return f"Extraction failed for {failures} of {total} sources."


def _json_sql_literal(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True)
    tag = f"$fpds_{abs(hash(payload))}$"
    while tag in payload:
        tag = f"{tag}_x$"
    return f"{tag}{payload}{tag}"
