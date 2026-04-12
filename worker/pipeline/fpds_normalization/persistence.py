from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from .models import NormalizationArtifactLookup, NormalizationResult

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class NormalizationDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "NormalizationDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for normalization DB persistence")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


@dataclass(frozen=True)
class NormalizationPersistenceResult:
    run_id: str
    run_state: str
    candidate_count: int
    field_evidence_link_count: int
    model_execution_count: int
    usage_record_count: int
    run_source_item_count: int
    source_success_count: int
    source_failure_count: int
    partial_completion_flag: bool
    completed_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_state": self.run_state,
            "candidate_count": self.candidate_count,
            "field_evidence_link_count": self.field_evidence_link_count,
            "model_execution_count": self.model_execution_count,
            "usage_record_count": self.usage_record_count,
            "run_source_item_count": self.run_source_item_count,
            "source_success_count": self.source_success_count,
            "source_failure_count": self.source_failure_count,
            "partial_completion_flag": self.partial_completion_flag,
            "completed_at": self.completed_at,
        }


class PsqlNormalizationRepository:
    def __init__(
        self,
        config: NormalizationDatabaseConfig,
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
            "pipeline_stage": "normalization",
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

    def load_latest_extraction_artifacts(
        self,
        *,
        source_document_ids: list[str],
    ) -> list[NormalizationArtifactLookup]:
        if not source_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(artifact_rows)), '[]'::json)::text
FROM (
    SELECT DISTINCT ON (me.source_document_id)
        me.source_document_id,
        me.execution_metadata ->> 'snapshot_id' AS snapshot_id,
        me.execution_metadata ->> 'parsed_document_id' AS parsed_document_id,
        me.model_execution_id AS extraction_model_execution_id,
        me.execution_metadata ->> 'extracted_storage_key' AS extracted_storage_key,
        me.execution_metadata ->> 'metadata_storage_key' AS extraction_metadata_storage_key,
        sd.bank_code,
        sd.country_code,
        sd.source_type,
        sd.source_language,
        sd.source_metadata
    FROM model_execution AS me
    JOIN source_document AS sd
      ON sd.source_document_id = me.source_document_id
    WHERE me.stage_name = 'extraction'
      AND me.execution_status = 'completed'
      AND me.source_document_id IN (
        SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb)
      )
    ORDER BY me.source_document_id, me.completed_at DESC NULLS LAST, me.started_at DESC
) AS artifact_rows;
"""
        output = self._execute(
            sql,
            variables={"source_document_ids_json": json.dumps(source_document_ids, ensure_ascii=True)},
        )
        payload = json.loads(output or "[]")
        return [NormalizationArtifactLookup(**item) for item in payload]

    def persist_normalization_result(
        self,
        *,
        run_id: str,
        normalization_result: NormalizationResult,
        trigger_type: str,
        triggered_by: str | None,
        completed_at: str,
    ) -> NormalizationPersistenceResult:
        schema = self.active_schema
        candidates = [
            item.normalized_candidate_record
            for item in normalization_result.source_results
            if item.normalized_candidate_record is not None
        ]
        field_evidence_links = [
            row
            for item in normalization_result.source_results
            for row in item.field_evidence_link_records
        ]
        model_executions = [item.model_execution_record for item in normalization_result.source_results]
        usage_records = [item.usage_record for item in normalization_result.source_results if item.usage_record is not None]
        run_source_items = [item.run_source_item_record for item in normalization_result.source_results]
        source_failure_count = sum(1 for item in normalization_result.source_results if item.normalization_action == "failed")
        source_success_count = len(normalization_result.source_results) - source_failure_count
        run_state = "failed" if source_failure_count == len(normalization_result.source_results) else "completed"
        error_summary = _build_run_error_summary(total=len(normalization_result.source_results), failures=source_failure_count)
        run_metadata = {
            "pipeline_stage": "normalization",
            "trigger_type": trigger_type,
            "triggered_by": triggered_by,
            "correlation_id": normalization_result.correlation_id,
            "request_id": normalization_result.request_id,
            "normalization_stats": normalization_result.to_dict()["stats"],
        }
        candidates_json_literal = _json_sql_literal(candidates)
        field_evidence_links_json_literal = _json_sql_literal(field_evidence_links)
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

WITH candidate_payload AS (
    SELECT *
    FROM jsonb_to_recordset({candidates_json_literal}::jsonb) AS payload(
        candidate_id text,
        run_id text,
        source_document_id text,
        model_execution_id text,
        candidate_state text,
        validation_status text,
        source_confidence numeric(5,4),
        review_reason_code text,
        country_code text,
        bank_code text,
        product_family text,
        product_type text,
        subtype_code text,
        product_name text,
        source_language text,
        currency text,
        validation_issue_codes jsonb,
        candidate_payload jsonb,
        field_mapping_metadata jsonb
    )
)
INSERT INTO normalized_candidate (
    candidate_id,
    run_id,
    source_document_id,
    model_execution_id,
    candidate_state,
    validation_status,
    source_confidence,
    review_reason_code,
    country_code,
    bank_code,
    product_family,
    product_type,
    subtype_code,
    product_name,
    source_language,
    currency,
    validation_issue_codes,
    candidate_payload,
    field_mapping_metadata
)
SELECT
    candidate_id,
    run_id,
    source_document_id,
    model_execution_id,
    candidate_state,
    validation_status,
    source_confidence,
    review_reason_code,
    country_code,
    bank_code,
    product_family,
    product_type,
    subtype_code,
    product_name,
    source_language,
    currency,
    validation_issue_codes,
    candidate_payload,
    field_mapping_metadata
FROM candidate_payload
ON CONFLICT (candidate_id) DO UPDATE SET
    model_execution_id = EXCLUDED.model_execution_id,
    candidate_state = EXCLUDED.candidate_state,
    validation_status = EXCLUDED.validation_status,
    source_confidence = EXCLUDED.source_confidence,
    review_reason_code = EXCLUDED.review_reason_code,
    country_code = EXCLUDED.country_code,
    bank_code = EXCLUDED.bank_code,
    product_family = EXCLUDED.product_family,
    product_type = EXCLUDED.product_type,
    subtype_code = EXCLUDED.subtype_code,
    product_name = EXCLUDED.product_name,
    source_language = EXCLUDED.source_language,
    currency = EXCLUDED.currency,
    validation_issue_codes = EXCLUDED.validation_issue_codes,
    candidate_payload = EXCLUDED.candidate_payload,
    field_mapping_metadata = EXCLUDED.field_mapping_metadata,
    updated_at = now();

WITH field_evidence_link_payload AS (
    SELECT *
    FROM jsonb_to_recordset({field_evidence_links_json_literal}::jsonb) AS payload(
        field_evidence_link_id text,
        candidate_id text,
        product_version_id text,
        evidence_chunk_id text,
        source_document_id text,
        field_name text,
        candidate_value text,
        citation_confidence numeric(5,4)
    )
)
INSERT INTO field_evidence_link (
    field_evidence_link_id,
    candidate_id,
    product_version_id,
    evidence_chunk_id,
    source_document_id,
    field_name,
    candidate_value,
    citation_confidence
)
SELECT
    field_evidence_link_id,
    candidate_id,
    product_version_id,
    evidence_chunk_id,
    source_document_id,
    field_name,
    candidate_value,
    citation_confidence
FROM field_evidence_link_payload
ON CONFLICT (field_evidence_link_id) DO UPDATE SET
    candidate_value = EXCLUDED.candidate_value,
    citation_confidence = EXCLUDED.citation_confidence;

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
                "source_scope_count": str(len(normalization_result.source_results)),
                "source_success_count": str(source_success_count),
                "source_failure_count": str(source_failure_count),
                "candidate_count": str(len(candidates)),
                "error_summary": error_summary or "",
                "partial_completion_flag": str(normalization_result.partial_completion_flag).lower(),
                "completed_at": completed_at,
            },
        )
        return NormalizationPersistenceResult(
            run_id=run_id,
            run_state=run_state,
            candidate_count=len(candidates),
            field_evidence_link_count=len(field_evidence_links),
            model_execution_count=len(model_executions),
            usage_record_count=len(usage_records),
            run_source_item_count=len(run_source_items),
            source_success_count=source_success_count,
            source_failure_count=source_failure_count,
            partial_completion_flag=normalization_result.partial_completion_flag,
            completed_at=completed_at,
        )

    def _resolve_active_schema(self) -> str:
        preferred = self.config.schema
        sql = """
SELECT COALESCE((
    SELECT schemaname
    FROM pg_tables
    WHERE tablename IN (
        'bank',
        'ingestion_run',
        'run_source_item',
        'source_document',
        'model_execution',
        'llm_usage_record',
        'normalized_candidate',
        'field_evidence_link'
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
        raise RuntimeError("Could not find normalization tables in the configured schema or in public.")

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        env = dict(os.environ)
        env["PGCLIENTENCODING"] = "UTF8"
        completed = subprocess.run(
            [*command, "-v", "ON_ERROR_STOP=1", "-X", "-q", "-A", "-t"],
            input=sql,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown psql error"
            raise RuntimeError(f"psql command failed: {stderr}")
        return completed.stdout.strip()


def _build_run_error_summary(*, total: int, failures: int) -> str | None:
    if failures == 0:
        return None
    if failures == total:
        return f"Normalization failed for all {total} sources."
    return f"Normalization failed for {failures} of {total} sources."


def _json_sql_literal(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True)
    tag = f"$fpds_{abs(hash(payload))}$"
    while tag in payload:
        tag = f"{tag}_x$"
    return f"{tag}{payload}{tag}"
