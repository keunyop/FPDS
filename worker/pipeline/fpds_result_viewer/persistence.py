from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Sequence

from worker.psql_cli import run_psql_command

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ResultViewerDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "ResultViewerDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for result viewer DB access")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


class PsqlResultViewerRepository:
    def __init__(
        self,
        config: ResultViewerDatabaseConfig,
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

    def load_run_overview(self, *, run_id: str) -> dict[str, object]:
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE((
    SELECT json_build_object(
        'run_id', ir.run_id,
        'run_state', ir.run_state,
        'trigger_type', ir.trigger_type,
        'triggered_by', ir.triggered_by,
        'source_scope_count', ir.source_scope_count,
        'source_success_count', ir.source_success_count,
        'source_failure_count', ir.source_failure_count,
        'candidate_count', ir.candidate_count,
        'review_queued_count', ir.review_queued_count,
        'partial_completion_flag', ir.partial_completion_flag,
        'error_summary', ir.error_summary,
        'started_at', ir.started_at,
        'completed_at', ir.completed_at,
        'run_metadata', ir.run_metadata,
        'stage_status_counts', COALESCE((
            SELECT json_object_agg(status_rows.stage_status, status_rows.status_count)
            FROM (
                SELECT rsi.stage_status, count(*) AS status_count
                FROM run_source_item AS rsi
                WHERE rsi.run_id = ir.run_id
                GROUP BY rsi.stage_status
            ) AS status_rows
        ), '{{}}'::json)
    )::json
    FROM ingestion_run AS ir
    WHERE ir.run_id = :'run_id'
), '{{}}'::json)::text;
"""
        payload = json.loads(self._execute(sql, variables={"run_id": run_id}) or "{}")
        if not payload:
            raise ValueError(f"Run `{run_id}` was not found in the FPDS database.")
        return payload

    def load_candidate_rows(self, *, run_id: str) -> list[dict[str, object]]:
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(candidate_rows)), '[]'::json)::text
FROM (
    WITH scoped_candidate_ids AS (
        SELECT nc.candidate_id
        FROM normalized_candidate AS nc
        WHERE nc.run_id = :'run_id'
        UNION
        SELECT DISTINCT lur.candidate_id
        FROM llm_usage_record AS lur
        JOIN model_execution AS me
          ON me.model_execution_id = lur.model_execution_id
        WHERE lur.run_id = :'run_id'
          AND lur.candidate_id IS NOT NULL
          AND me.stage_name = 'validation_routing'
    )
    SELECT
        nc.candidate_id,
        rt.review_task_id,
        rt.review_state,
        rt.queue_reason_code,
        COALESCE(rt.issue_summary, '[]'::jsonb) AS issue_summary,
        nc.run_id,
        nc.source_document_id,
        nc.bank_code,
        b.bank_name,
        nc.country_code,
        nc.product_family,
        nc.product_type,
        nc.subtype_code,
        nc.product_name,
        nc.source_language,
        nc.currency,
        nc.candidate_state,
        nc.validation_status,
        nc.source_confidence,
        nc.review_reason_code,
        nc.validation_issue_codes,
        nc.candidate_payload,
        nc.field_mapping_metadata,
        sd.normalized_source_url AS source_url,
        sd.source_type,
        sd.source_metadata,
        ss.snapshot_id,
        ss.fetched_at,
        pd.parsed_document_id,
        pd.parse_quality_note,
        rsi.stage_status,
        rsi.warning_count,
        rsi.error_count,
        rsi.error_summary,
        COALESCE(rsi.stage_metadata -> 'runtime_notes', '[]'::jsonb) AS runtime_notes,
        COALESCE((
            SELECT json_agg(
                json_build_object(
                    'field_name', fel.field_name,
                    'candidate_value', fel.candidate_value,
                    'citation_confidence', fel.citation_confidence,
                    'evidence_chunk_id', fel.evidence_chunk_id,
                    'evidence_excerpt', ec.evidence_excerpt,
                    'anchor_type', ec.anchor_type,
                    'anchor_value', ec.anchor_value,
                    'page_no', ec.page_no,
                    'chunk_index', ec.chunk_index,
                    'anchor_label',
                        CASE
                            WHEN ec.page_no IS NOT NULL THEN 'Page ' || ec.page_no::text
                            WHEN ec.anchor_value IS NOT NULL AND ec.anchor_value <> '' THEN initcap(ec.anchor_type) || ' ' || ec.anchor_value
                            ELSE 'Chunk ' || ec.chunk_index::text
                        END
                )
                ORDER BY fel.field_name, ec.chunk_index
            )
            FROM field_evidence_link AS fel
            JOIN evidence_chunk AS ec
              ON ec.evidence_chunk_id = fel.evidence_chunk_id
            WHERE fel.candidate_id = nc.candidate_id
        ), '[]'::json) AS evidence_links
    FROM normalized_candidate AS nc
    LEFT JOIN review_task AS rt
      ON rt.candidate_id = nc.candidate_id
    JOIN source_document AS sd
      ON sd.source_document_id = nc.source_document_id
    LEFT JOIN bank AS b
      ON b.bank_code = nc.bank_code
    LEFT JOIN run_source_item AS rsi
      ON rsi.run_id = nc.run_id
     AND rsi.source_document_id = nc.source_document_id
    LEFT JOIN source_snapshot AS ss
      ON ss.snapshot_id = rsi.selected_snapshot_id
    LEFT JOIN parsed_document AS pd
      ON pd.snapshot_id = ss.snapshot_id
    WHERE nc.candidate_id IN (SELECT candidate_id FROM scoped_candidate_ids)
    ORDER BY
        CASE nc.validation_status
            WHEN 'error' THEN 0
            WHEN 'warning' THEN 1
            ELSE 2
        END,
        nc.source_confidence DESC NULLS LAST,
        nc.product_name
) AS candidate_rows;
"""
        return json.loads(self._execute(sql, variables={"run_id": run_id}) or "[]")

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
        'normalized_candidate',
        'review_task',
        'field_evidence_link'
    )
    GROUP BY schemaname
    HAVING count(DISTINCT tablename) = 9
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
        resolved = self._execute(sql, variables={"preferred_schema": preferred}).strip()
        if resolved:
            return resolved
        raise RuntimeError("Could not find result viewer tables in the configured schema or in public.")

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        return run_psql_command(command, sql, force_utf8=True)
