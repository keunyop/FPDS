from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Sequence

from worker.psql_cli import run_psql_command
from worker.pipeline.fpds_vector_embedding import (
    VectorEmbeddingConfig,
    build_embedding_source_hash,
    build_evidence_chunk_embedding_id,
    build_retrieval_embedding,
    format_pgvector_literal,
)

from .models import ExistingParsedDocumentRecord, ParseChunkResult, ParseSourceSnapshot

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ParseChunkDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "ParseChunkDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for parse/chunk DB persistence")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


@dataclass(frozen=True)
class ParseChunkPersistenceResult:
    run_id: str
    run_state: str
    parsed_document_count: int
    evidence_chunk_count: int
    run_source_item_count: int
    source_success_count: int
    source_failure_count: int
    partial_completion_flag: bool
    completed_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_state": self.run_state,
            "parsed_document_count": self.parsed_document_count,
            "evidence_chunk_count": self.evidence_chunk_count,
            "run_source_item_count": self.run_source_item_count,
            "source_success_count": self.source_success_count,
            "source_failure_count": self.source_failure_count,
            "partial_completion_flag": self.partial_completion_flag,
            "completed_at": self.completed_at,
        }


class PsqlParseChunkRepository:
    def __init__(
        self,
        config: ParseChunkDatabaseConfig,
        *,
        command_runner: Callable[[Sequence[str], str], str] | None = None,
    ):
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
            "pipeline_stage": "parse_chunk",
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

    def load_latest_snapshots(self, *, source_document_ids: list[str]) -> list[ParseSourceSnapshot]:
        if not source_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(snapshot_rows)), '[]'::json)::text
FROM (
    SELECT DISTINCT ON (ss.source_document_id)
        ss.snapshot_id,
        ss.source_document_id,
        ss.object_storage_key,
        ss.content_type,
        sd.source_language,
        sd.bank_code,
        sd.country_code
    FROM source_snapshot AS ss
    JOIN source_document AS sd
      ON sd.source_document_id = ss.source_document_id
    WHERE ss.source_document_id IN (
        SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb)
    )
    ORDER BY ss.source_document_id, ss.fetched_at DESC, ss.created_at DESC
) AS snapshot_rows;
"""
        output = self._execute(
            sql,
            variables={
                "source_document_ids_json": json.dumps(source_document_ids, ensure_ascii=True),
            },
        )
        payload = json.loads(output or "[]")
        return [ParseSourceSnapshot(**item) for item in payload]

    def load_existing_parsed_documents(
        self,
        *,
        snapshot_ids: list[str],
    ) -> list[ExistingParsedDocumentRecord]:
        if not snapshot_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(parsed_rows)), '[]'::json)::text
FROM (
    SELECT
        pd.parsed_document_id,
        pd.snapshot_id,
        pd.parsed_storage_key,
        pd.parser_version,
        pd.parse_quality_note,
        pd.parser_metadata,
        pd.retention_class,
        replace(pd.parsed_at::text, ' ', 'T') AS parsed_at,
        COALESCE(chunk_counts.chunk_count, 0) AS chunk_count
    FROM parsed_document AS pd
    LEFT JOIN (
        SELECT parsed_document_id, count(*)::integer AS chunk_count
        FROM evidence_chunk
        GROUP BY parsed_document_id
    ) AS chunk_counts
      ON chunk_counts.parsed_document_id = pd.parsed_document_id
    WHERE pd.snapshot_id IN (
        SELECT jsonb_array_elements_text(:'snapshot_ids_json'::jsonb)
    )
) AS parsed_rows;
"""
        output = self._execute(
            sql,
            variables={
                "snapshot_ids_json": json.dumps(snapshot_ids, ensure_ascii=True),
            },
        )
        payload = json.loads(output or "[]")
        return [ExistingParsedDocumentRecord(**item) for item in payload]

    def persist_parse_chunk_result(
        self,
        *,
        run_id: str,
        parse_result: ParseChunkResult,
        trigger_type: str,
        triggered_by: str | None,
        completed_at: str,
    ) -> ParseChunkPersistenceResult:
        schema = self.active_schema
        parsed_documents = [
            item.parsed_document_record
            for item in parse_result.source_results
            if item.parsed_document_record is not None
        ]
        evidence_chunks = [
            chunk
            for item in parse_result.source_results
            for chunk in item.evidence_chunk_records
        ]
        embedding_config = VectorEmbeddingConfig.from_env()
        evidence_chunk_embeddings = [
            _build_embedding_record(chunk=chunk, config=embedding_config)
            for chunk in evidence_chunks
        ]
        run_source_items = [item.run_source_item_record for item in parse_result.source_results]
        source_failure_count = sum(1 for item in parse_result.source_results if item.parse_action == "failed")
        source_success_count = len(parse_result.source_results) - source_failure_count
        run_state = "failed" if source_failure_count == len(parse_result.source_results) else "completed"
        error_summary = _build_run_error_summary(
            total=len(parse_result.source_results),
            failures=source_failure_count,
        )
        run_metadata = {
            "pipeline_stage": "parse_chunk",
            "trigger_type": trigger_type,
            "triggered_by": triggered_by,
            "correlation_id": parse_result.correlation_id,
            "request_id": parse_result.request_id,
            "parse_stats": parse_result.to_dict()["stats"],
        }
        parsed_documents_json_literal = _json_sql_literal(parsed_documents)
        evidence_chunks_json_literal = _json_sql_literal(evidence_chunks)
        evidence_chunk_embeddings_json_literal = _json_sql_literal(evidence_chunk_embeddings)
        run_source_items_json_literal = _json_sql_literal(run_source_items)
        run_metadata_json_literal = _json_sql_literal(run_metadata)

        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

WITH parsed_document_payload AS (
    SELECT *
    FROM jsonb_to_recordset({parsed_documents_json_literal}::jsonb) AS payload(
        parsed_document_id text,
        snapshot_id text,
        parsed_storage_key text,
        parser_version text,
        parse_quality_note text,
        parser_metadata jsonb,
        retention_class text,
        parsed_at timestamptz
    )
)
INSERT INTO parsed_document (
    parsed_document_id,
    snapshot_id,
    parsed_storage_key,
    parser_version,
    parse_quality_note,
    parser_metadata,
    retention_class,
    parsed_at
)
SELECT
    parsed_document_id,
    snapshot_id,
    parsed_storage_key,
    parser_version,
    parse_quality_note,
    parser_metadata,
    retention_class,
    parsed_at
FROM parsed_document_payload
ON CONFLICT (snapshot_id) DO NOTHING;

WITH evidence_chunk_payload AS (
    SELECT *
    FROM jsonb_to_recordset({evidence_chunks_json_literal}::jsonb) AS payload(
        evidence_chunk_id text,
        parsed_document_id text,
        chunk_index integer,
        anchor_type text,
        anchor_value text,
        page_no integer,
        source_language text,
        chunk_char_start integer,
        chunk_char_end integer,
        evidence_excerpt text,
        retrieval_metadata jsonb
    )
)
INSERT INTO evidence_chunk (
    evidence_chunk_id,
    parsed_document_id,
    chunk_index,
    anchor_type,
    anchor_value,
    page_no,
    source_language,
    chunk_char_start,
    chunk_char_end,
    evidence_excerpt,
    retrieval_metadata
)
SELECT
    evidence_chunk_id,
    parsed_document_id,
    chunk_index,
    anchor_type,
    anchor_value,
    page_no,
    source_language,
    chunk_char_start,
    chunk_char_end,
    evidence_excerpt,
    retrieval_metadata
FROM evidence_chunk_payload
ON CONFLICT (evidence_chunk_id) DO NOTHING;

DO $fpds_vector$
BEGIN
    IF to_regclass('evidence_chunk_embedding') IS NOT NULL THEN
        EXECUTE $fpds_sql$
            WITH embedding_payload AS (
                SELECT *
                FROM jsonb_to_recordset({evidence_chunk_embeddings_json_literal}::jsonb) AS payload(
                    evidence_chunk_embedding_id text,
                    evidence_chunk_id text,
                    vector_namespace text,
                    embedding_model_id text,
                    embedding_dimensions integer,
                    embedding_source text,
                    embedding_source_text_hash text,
                    embedding text,
                    embedding_metadata jsonb
                )
            )
            INSERT INTO evidence_chunk_embedding (
                evidence_chunk_embedding_id,
                evidence_chunk_id,
                vector_namespace,
                embedding_model_id,
                embedding_dimensions,
                embedding_source,
                embedding_source_text_hash,
                embedding,
                embedding_metadata
            )
            SELECT
                evidence_chunk_embedding_id,
                evidence_chunk_id,
                vector_namespace,
                embedding_model_id,
                embedding_dimensions,
                embedding_source,
                embedding_source_text_hash,
                embedding::vector(64),
                embedding_metadata
            FROM embedding_payload
            ON CONFLICT (evidence_chunk_id, vector_namespace, embedding_model_id) DO UPDATE SET
                embedding_dimensions = EXCLUDED.embedding_dimensions,
                embedding_source = EXCLUDED.embedding_source,
                embedding_source_text_hash = EXCLUDED.embedding_source_text_hash,
                embedding = EXCLUDED.embedding,
                embedding_metadata = EXCLUDED.embedding_metadata,
                updated_at = now();
        $fpds_sql$;
    END IF;
END
$fpds_vector$;

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
                "source_scope_count": str(len(parse_result.source_results)),
                "source_success_count": str(source_success_count),
                "source_failure_count": str(source_failure_count),
                "error_summary": error_summary or "",
                "partial_completion_flag": str(parse_result.partial_completion_flag).lower(),
                "completed_at": completed_at,
            },
        )
        return ParseChunkPersistenceResult(
            run_id=run_id,
            run_state=run_state,
            parsed_document_count=len(parsed_documents),
            evidence_chunk_count=len(evidence_chunks),
            run_source_item_count=len(run_source_items),
            source_success_count=source_success_count,
            source_failure_count=source_failure_count,
            partial_completion_flag=parse_result.partial_completion_flag,
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
        'evidence_chunk'
    )
    GROUP BY schemaname
    HAVING count(DISTINCT tablename) = 6
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
            "Could not find parse/chunk tables in the configured schema or in public."
        )

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        return run_psql_command(command, sql)


def _build_run_error_summary(*, total: int, failures: int) -> str | None:
    if failures == 0:
        return None
    if failures == total:
        return f"Parse/chunk failed for all {total} sources."
    return f"Parse/chunk failed for {failures} of {total} sources."


def _json_sql_literal(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True)
    tag = f"$fpds_{abs(hash(payload))}$"
    while tag in payload:
        tag = f"{tag}_x$"
    return f"{tag}{payload}{tag}"


def _build_embedding_record(*, chunk: dict[str, object], config: VectorEmbeddingConfig) -> dict[str, object]:
    evidence_excerpt = str(chunk.get("evidence_excerpt") or "")
    evidence_chunk_id = str(chunk["evidence_chunk_id"])
    vector = build_retrieval_embedding(evidence_excerpt, dimensions=config.dimensions)
    return {
        "evidence_chunk_embedding_id": build_evidence_chunk_embedding_id(
            evidence_chunk_id=evidence_chunk_id,
            namespace=config.namespace,
            model_id=config.model_id,
        ),
        "evidence_chunk_id": evidence_chunk_id,
        "vector_namespace": config.namespace,
        "embedding_model_id": config.model_id,
        "embedding_dimensions": config.dimensions,
        "embedding_source": config.source,
        "embedding_source_text_hash": build_embedding_source_hash(evidence_excerpt),
        "embedding": format_pgvector_literal(vector),
        "embedding_metadata": {
            "source": config.source,
            "chunk_index": chunk.get("chunk_index"),
            "source_language": chunk.get("source_language"),
        },
    }
