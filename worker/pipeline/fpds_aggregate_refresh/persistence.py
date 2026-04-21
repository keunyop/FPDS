from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Sequence

from worker.psql_cli import run_psql_command

from .models import AggregateRefreshResult, CanonicalAggregateRow

_SCHEMA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class AggregateRefreshDatabaseConfig:
    database_url: str
    schema: str

    @classmethod
    def from_env(cls) -> "AggregateRefreshDatabaseConfig":
        database_url = os.getenv("FPDS_DATABASE_URL")
        if not database_url:
            raise ValueError("FPDS_DATABASE_URL is required for aggregate refresh DB access")
        schema = os.getenv("FPDS_DATABASE_SCHEMA", "public")
        if not _SCHEMA_IDENTIFIER_RE.match(schema):
            raise ValueError(f"Unsupported FPDS_DATABASE_SCHEMA: {schema}")
        return cls(database_url=database_url, schema=schema)


class PsqlAggregateRefreshRepository:
    def __init__(
        self,
        config: AggregateRefreshDatabaseConfig,
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

    def ensure_refresh_run(
        self,
        *,
        snapshot_id: str,
        triggered_by_run_id: str | None,
        refresh_scope: str,
        country_code: str,
        filter_scope: dict[str, object],
        attempted_at: str,
    ) -> None:
        schema = self.active_schema
        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

INSERT INTO aggregate_refresh_run (
    snapshot_id,
    triggered_by_run_id,
    refresh_scope,
    country_code,
    filter_scope,
    refresh_status,
    source_change_cutoff_at,
    attempted_at,
    refreshed_at,
    stale_flag,
    error_summary,
    refresh_metadata
)
VALUES (
    :'snapshot_id',
    NULLIF(:'triggered_by_run_id', ''),
    :'refresh_scope',
    :'country_code',
    :'filter_scope'::jsonb,
    'started',
    NULL,
    :'attempted_at'::timestamptz,
    NULL,
    false,
    NULL,
    '{{}}'::jsonb
)
ON CONFLICT (snapshot_id) DO UPDATE SET
    triggered_by_run_id = COALESCE(EXCLUDED.triggered_by_run_id, aggregate_refresh_run.triggered_by_run_id),
    refresh_scope = EXCLUDED.refresh_scope,
    country_code = EXCLUDED.country_code,
    filter_scope = EXCLUDED.filter_scope,
    refresh_status = 'started',
    attempted_at = EXCLUDED.attempted_at,
    refreshed_at = NULL,
    stale_flag = false,
    error_summary = NULL,
    refresh_metadata = '{{}}'::jsonb;

COMMIT;
"""
        self._execute(
            sql,
            variables={
                "snapshot_id": snapshot_id,
                "triggered_by_run_id": triggered_by_run_id or "",
                "refresh_scope": refresh_scope,
                "country_code": country_code,
                "filter_scope": json.dumps(filter_scope, ensure_ascii=True),
                "attempted_at": attempted_at,
            },
        )

    def load_current_canonical_rows(
        self,
        *,
        country_code: str,
        bank_codes: list[str],
        product_types: list[str],
    ) -> list[CanonicalAggregateRow]:
        schema = self.active_schema
        sql = f"""
SET search_path TO {schema};

SELECT COALESCE(json_agg(row_to_json(canonical_rows)), '[]'::json)::text
FROM (
    SELECT
        cp.product_id,
        cp.bank_code,
        COALESCE(b.bank_name, cp.bank_code) AS bank_name,
        cp.country_code,
        cp.product_family,
        cp.product_type,
        cp.subtype_code,
        cp.product_name,
        cp.source_language,
        cp.currency,
        cp.status,
        cp.last_verified_at,
        cp.last_changed_at,
        pv.product_version_id,
        CASE
            WHEN pv.normalized_payload IS NOT NULL AND pv.normalized_payload <> '{{}}'::jsonb THEN pv.normalized_payload
            WHEN cp.current_snapshot_payload IS NOT NULL THEN cp.current_snapshot_payload
            ELSE '{{}}'::jsonb
        END AS canonical_payload
    FROM canonical_product AS cp
    LEFT JOIN bank AS b
      ON b.bank_code = cp.bank_code
    LEFT JOIN product_version AS pv
      ON pv.product_id = cp.product_id
     AND pv.version_no = cp.current_version_no
    WHERE cp.country_code = :'country_code'
      AND cp.product_family = 'deposit'
      AND (
            jsonb_array_length(:'bank_codes_json'::jsonb) = 0
            OR cp.bank_code IN (SELECT jsonb_array_elements_text(:'bank_codes_json'::jsonb))
      )
      AND (
            jsonb_array_length(:'product_types_json'::jsonb) = 0
            OR cp.product_type IN (SELECT jsonb_array_elements_text(:'product_types_json'::jsonb))
      )
    ORDER BY cp.bank_code, cp.product_type, cp.product_name, cp.product_id
) AS canonical_rows;
"""
        payload = json.loads(
            self._execute(
                sql,
                variables={
                    "country_code": country_code,
                    "bank_codes_json": json.dumps(bank_codes, ensure_ascii=True),
                    "product_types_json": json.dumps(product_types, ensure_ascii=True),
                },
            )
            or "[]"
        )
        return [CanonicalAggregateRow(**item) for item in payload]

    def persist_refresh_result(
        self,
        *,
        result: AggregateRefreshResult,
        triggered_by_run_id: str | None,
    ) -> None:
        schema = self.active_schema
        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

DELETE FROM dashboard_scatter_snapshot
WHERE snapshot_id = {_sql_literal(result.snapshot_id)};

DELETE FROM dashboard_ranking_snapshot
WHERE snapshot_id = {_sql_literal(result.snapshot_id)};

DELETE FROM dashboard_metric_snapshot
WHERE snapshot_id = {_sql_literal(result.snapshot_id)};

DELETE FROM public_product_projection
WHERE snapshot_id = {_sql_literal(result.snapshot_id)};

INSERT INTO aggregate_refresh_run (
    snapshot_id,
    triggered_by_run_id,
    refresh_scope,
    country_code,
    filter_scope,
    refresh_status,
    source_change_cutoff_at,
    attempted_at,
    refreshed_at,
    stale_flag,
    error_summary,
    refresh_metadata
)
VALUES (
    {_sql_literal(result.snapshot_id)},
    {_sql_literal(triggered_by_run_id)},
    {_sql_literal(result.refresh_scope)},
    {_sql_literal(result.country_code)},
    {_json_sql_literal(result.filter_scope)}::jsonb,
    'completed',
    {_sql_literal(result.source_change_cutoff_at)}::timestamptz,
    {_sql_literal(result.refreshed_at)}::timestamptz,
    {_sql_literal(result.refreshed_at)}::timestamptz,
    false,
    NULL,
    {_json_sql_literal(result.refresh_metadata)}::jsonb
)
ON CONFLICT (snapshot_id) DO UPDATE SET
    triggered_by_run_id = COALESCE(EXCLUDED.triggered_by_run_id, aggregate_refresh_run.triggered_by_run_id),
    refresh_scope = EXCLUDED.refresh_scope,
    country_code = EXCLUDED.country_code,
    filter_scope = EXCLUDED.filter_scope,
    refresh_status = 'completed',
    source_change_cutoff_at = EXCLUDED.source_change_cutoff_at,
    attempted_at = EXCLUDED.attempted_at,
    refreshed_at = EXCLUDED.refreshed_at,
    stale_flag = false,
    error_summary = NULL,
    refresh_metadata = EXCLUDED.refresh_metadata;

INSERT INTO public_product_projection (
    snapshot_id,
    product_id,
    bank_code,
    bank_name,
    country_code,
    product_family,
    product_type,
    subtype_code,
    product_name,
    source_language,
    currency,
    status,
    public_display_rate,
    public_display_fee,
    monthly_fee,
    effective_fee,
    minimum_balance,
    minimum_deposit,
    term_length_days,
    product_highlight_badge_code,
    target_customer_tags,
    fee_bucket,
    minimum_balance_bucket,
    minimum_deposit_bucket,
    term_bucket,
    last_verified_at,
    last_changed_at,
    refresh_metadata
)
SELECT
    row ->> 'snapshot_id',
    row ->> 'product_id',
    row ->> 'bank_code',
    row ->> 'bank_name',
    row ->> 'country_code',
    row ->> 'product_family',
    row ->> 'product_type',
    NULLIF(row ->> 'subtype_code', ''),
    row ->> 'product_name',
    row ->> 'source_language',
    row ->> 'currency',
    row ->> 'status',
    NULLIF(row ->> 'public_display_rate', '')::numeric(12,4),
    NULLIF(row ->> 'public_display_fee', '')::numeric(12,2),
    NULLIF(row ->> 'monthly_fee', '')::numeric(12,2),
    NULLIF(row ->> 'effective_fee', '')::numeric(12,2),
    NULLIF(row ->> 'minimum_balance', '')::numeric(12,2),
    NULLIF(row ->> 'minimum_deposit', '')::numeric(12,2),
    NULLIF(row ->> 'term_length_days', '')::integer,
    NULLIF(row ->> 'product_highlight_badge_code', ''),
    COALESCE(row -> 'target_customer_tags', '[]'::jsonb),
    NULLIF(row ->> 'fee_bucket', ''),
    NULLIF(row ->> 'minimum_balance_bucket', ''),
    NULLIF(row ->> 'minimum_deposit_bucket', ''),
    NULLIF(row ->> 'term_bucket', ''),
    NULLIF(row ->> 'last_verified_at', '')::timestamptz,
    NULLIF(row ->> 'last_changed_at', '')::timestamptz,
    COALESCE(row -> 'refresh_metadata', '{{}}'::jsonb)
FROM jsonb_array_elements({_json_sql_literal(result.projection_rows)}::jsonb) AS row;

INSERT INTO dashboard_metric_snapshot (
    snapshot_id,
    scope_key,
    total_active_products,
    banks_in_scope,
    highest_display_rate,
    recently_changed_products_30d,
    breakdown_payload,
    freshness_payload,
    completeness_note
)
SELECT
    row ->> 'snapshot_id',
    row ->> 'scope_key',
    (row ->> 'total_active_products')::integer,
    (row ->> 'banks_in_scope')::integer,
    NULLIF(row ->> 'highest_display_rate', '')::numeric(12,4),
    (row ->> 'recently_changed_products_30d')::integer,
    COALESCE(row -> 'breakdown_payload', '{{}}'::jsonb),
    COALESCE(row -> 'freshness_payload', '{{}}'::jsonb),
    NULLIF(row ->> 'completeness_note', '')
FROM jsonb_array_elements({_json_sql_literal(result.metric_snapshots)}::jsonb) AS row;

INSERT INTO dashboard_ranking_snapshot (
    snapshot_id,
    ranking_key,
    scope_key,
    rank,
    product_id,
    bank_code,
    bank_name,
    product_name,
    product_type,
    metric_value,
    metric_unit,
    last_changed_at,
    ranking_metadata
)
SELECT
    row ->> 'snapshot_id',
    row ->> 'ranking_key',
    row ->> 'scope_key',
    (row ->> 'rank')::integer,
    row ->> 'product_id',
    row ->> 'bank_code',
    row ->> 'bank_name',
    row ->> 'product_name',
    row ->> 'product_type',
    NULLIF(row ->> 'metric_value', '')::numeric(12,4),
    row ->> 'metric_unit',
    NULLIF(row ->> 'last_changed_at', '')::timestamptz,
    COALESCE(row -> 'ranking_metadata', '{{}}'::jsonb)
FROM jsonb_array_elements({_json_sql_literal(result.ranking_rows)}::jsonb) AS row;

INSERT INTO dashboard_scatter_snapshot (
    snapshot_id,
    axis_preset,
    scope_key,
    product_id,
    bank_code,
    bank_name,
    product_name,
    product_type,
    x_value,
    y_value,
    highlight_badge_code,
    last_changed_at,
    point_metadata
)
SELECT
    row ->> 'snapshot_id',
    row ->> 'axis_preset',
    row ->> 'scope_key',
    row ->> 'product_id',
    row ->> 'bank_code',
    row ->> 'bank_name',
    row ->> 'product_name',
    row ->> 'product_type',
    (row ->> 'x_value')::numeric(12,4),
    (row ->> 'y_value')::numeric(12,4),
    NULLIF(row ->> 'highlight_badge_code', ''),
    NULLIF(row ->> 'last_changed_at', '')::timestamptz,
    COALESCE(row -> 'point_metadata', '{{}}'::jsonb)
FROM jsonb_array_elements({_json_sql_literal(result.scatter_rows)}::jsonb) AS row;

COMMIT;
"""
        self._execute(sql, variables={})

    def mark_refresh_failed(
        self,
        *,
        snapshot_id: str,
        error_summary: str,
        completed_at: str,
    ) -> None:
        schema = self.active_schema
        sql = f"""
BEGIN;
SET LOCAL search_path TO {schema};

UPDATE aggregate_refresh_run
SET refresh_status = 'failed',
    refreshed_at = {_sql_literal(completed_at)}::timestamptz,
    stale_flag = true,
    error_summary = {_sql_literal(error_summary)},
    refresh_metadata = COALESCE(refresh_metadata, '{{}}'::jsonb) || jsonb_build_object('failed_at', {_sql_literal(completed_at)}::text)
WHERE snapshot_id = {_sql_literal(snapshot_id)};

COMMIT;
"""
        self._execute(sql, variables={})

    def _resolve_active_schema(self) -> str:
        preferred = self.config.schema
        sql = """
SELECT COALESCE((
    SELECT schemaname
    FROM pg_tables
    WHERE tablename IN ('canonical_product', 'product_version', 'bank')
    GROUP BY schemaname
    HAVING count(DISTINCT tablename) = 3
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
        raise RuntimeError("Could not find aggregate refresh source tables in the configured schema or in public.")

    def _execute(self, sql: str, *, variables: dict[str, str]) -> str:
        command = ["psql", self.config.database_url]
        for key, value in variables.items():
            command.extend(["-v", f"{key}={value}"])
        return self.command_runner(command, sql)

    @staticmethod
    def _run_psql(command: Sequence[str], sql: str) -> str:
        return run_psql_command(command, sql, force_utf8=True)


def _sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _json_sql_literal(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=True)
    return "'" + serialized.replace("'", "''") + "'"
