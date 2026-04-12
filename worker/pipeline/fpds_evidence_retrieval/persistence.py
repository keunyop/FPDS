from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from .models import EvidenceChunkCandidate, ParsedDocumentLookup

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
