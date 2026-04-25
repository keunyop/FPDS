from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Sequence

from worker.psql_cli import run_psql_command
from worker.pipeline.fpds_vector_embedding import (
    VectorEmbeddingConfig,
    build_retrieval_embedding,
    format_pgvector_literal,
)

from .models import EvidenceChunkCandidate, MetadataFilters, ParsedDocumentLookup

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RetrievalDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "RetrievalDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for evidence retrieval DB access")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


class PsqlEvidenceRetrievalRepository:
    def __init__(
        self,
        config: RetrievalDatabaseConfig,
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

    def load_latest_parsed_documents(
        self,
        *,
        source_document_ids: list[str],
    ) -> list[ParsedDocumentLookup]:
        if not source_document_ids:
            return []
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(parsed_rows)), '[]'::json)::text
FROM (
    SELECT DISTINCT ON (pd.snapshot_id)
        pd.parsed_document_id,
        pd.snapshot_id,
        ss.source_document_id
    FROM parsed_document AS pd
    JOIN source_snapshot AS ss
      ON ss.snapshot_id = pd.snapshot_id
    WHERE ss.source_document_id IN (
        SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb)
    )
    ORDER BY pd.snapshot_id, pd.parsed_at DESC, pd.created_at DESC
) AS parsed_rows;
"""
        output = self._execute(
            sql,
            variables={
                "source_document_ids_json": json.dumps(source_document_ids, ensure_ascii=True),
            },
        )
        payload = json.loads(output or "[]")
        return [ParsedDocumentLookup(**item) for item in payload]

    def load_chunk_candidates(self, *, parsed_document_id: str) -> list[EvidenceChunkCandidate]:
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
        payload = json.loads(output or "[]")
        return [EvidenceChunkCandidate(**item) for item in payload]

    def load_vector_chunk_candidates(
        self,
        *,
        parsed_document_id: str,
        field_query_text: str,
        metadata_filters: MetadataFilters,
        max_matches: int,
        embedding_config: VectorEmbeddingConfig | None = None,
    ) -> list[EvidenceChunkCandidate]:
        if not self.vector_index_available():
            return []

        config = embedding_config or VectorEmbeddingConfig.from_env()
        query_vector = format_pgvector_literal(
            build_retrieval_embedding(field_query_text, dimensions=config.dimensions)
        )
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
        sd.source_type,
        GREATEST(0, LEAST(0.99, 1 - (ece.embedding <=> :'query_vector'::vector)))::float AS vector_score
    FROM evidence_chunk AS ec
    JOIN evidence_chunk_embedding AS ece
      ON ece.evidence_chunk_id = ec.evidence_chunk_id
    JOIN parsed_document AS pd
      ON pd.parsed_document_id = ec.parsed_document_id
    JOIN source_snapshot AS ss
      ON ss.snapshot_id = pd.snapshot_id
    JOIN source_document AS sd
      ON sd.source_document_id = ss.source_document_id
    WHERE ec.parsed_document_id = :'parsed_document_id'
      AND ece.vector_namespace = :'vector_namespace'
      AND ece.embedding_model_id = :'embedding_model_id'
      AND (:'bank_code' = '' OR sd.bank_code = :'bank_code')
      AND (:'country_code' = '' OR sd.country_code = :'country_code')
      AND (:'source_language' = '' OR ec.source_language = :'source_language')
      AND (
          :'source_types_json'::jsonb = '[]'::jsonb
          OR sd.source_type IN (SELECT jsonb_array_elements_text(:'source_types_json'::jsonb))
      )
      AND (
          :'source_document_ids_json'::jsonb = '[]'::jsonb
          OR sd.source_document_id IN (SELECT jsonb_array_elements_text(:'source_document_ids_json'::jsonb))
      )
      AND (
          :'anchor_types_json'::jsonb = '[]'::jsonb
          OR ec.anchor_type IN (SELECT jsonb_array_elements_text(:'anchor_types_json'::jsonb))
      )
    ORDER BY ece.embedding <=> :'query_vector'::vector, ec.chunk_index, ec.evidence_chunk_id
    LIMIT :'max_matches'::integer
) AS candidate_rows;
"""
        try:
            output = self._execute(
                sql,
                variables={
                    "parsed_document_id": parsed_document_id,
                    "query_vector": query_vector,
                    "vector_namespace": config.namespace,
                    "embedding_model_id": config.model_id,
                    "bank_code": metadata_filters.bank_code or "",
                    "country_code": metadata_filters.country_code or "",
                    "source_language": metadata_filters.source_language or "",
                    "source_types_json": json.dumps(list(metadata_filters.source_types), ensure_ascii=True),
                    "source_document_ids_json": json.dumps(
                        list(metadata_filters.source_document_ids),
                        ensure_ascii=True,
                    ),
                    "anchor_types_json": json.dumps(list(metadata_filters.anchor_types), ensure_ascii=True),
                    "max_matches": str(max_matches),
                },
            )
        except RuntimeError:
            return []
        payload = json.loads(output or "[]")
        return [EvidenceChunkCandidate(**item) for item in payload]

    def vector_index_available(self) -> bool:
        schema = self.active_schema
        sql = """
SELECT COALESCE((
    SELECT 'true'
    FROM pg_tables
    WHERE schemaname = :'schema'
      AND tablename = 'evidence_chunk_embedding'
    LIMIT 1
), 'false');
"""
        try:
            output = self._execute(sql, variables={"schema": schema})
        except RuntimeError:
            return False
        return output.strip().lower() == "true"

    def _resolve_active_schema(self) -> str:
        preferred = self.config.schema
        sql = """
SELECT COALESCE((
    SELECT schemaname
    FROM pg_tables
    WHERE tablename IN ('source_document', 'source_snapshot', 'parsed_document', 'evidence_chunk')
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
        raise RuntimeError("Could not find retrieval tables in the configured schema or in public.")

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        return run_psql_command(command, sql, force_utf8=True)
