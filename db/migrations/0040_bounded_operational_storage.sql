BEGIN;

-- These datasets were append-only operational telemetry. Keep their relation
-- names as zero-storage compatibility views so current read joins and
-- discard-only writes keep a stable shape without recreating log data. Writers
-- must use plain INSERT because a view cannot arbitrate ON CONFLICT.
DROP TABLE IF EXISTS audit_event;
DROP TABLE IF EXISTS llm_usage_record;

CREATE OR REPLACE FUNCTION fpds_discard_obsolete_log_write()
RETURNS trigger
LANGUAGE plpgsql
AS $fpds$
BEGIN
    RETURN NULL;
END
$fpds$;

CREATE VIEW audit_event AS
SELECT
    NULL::text AS audit_event_id,
    NULL::text AS event_category,
    NULL::text AS event_type,
    NULL::text AS actor_type,
    NULL::text AS actor_id,
    NULL::text AS actor_role_snapshot,
    NULL::text AS target_type,
    NULL::text AS target_id,
    NULL::text AS previous_state,
    NULL::text AS new_state,
    NULL::text AS reason_code,
    NULL::text AS reason_text,
    NULL::text AS run_id,
    NULL::text AS candidate_id,
    NULL::text AS review_task_id,
    NULL::text AS product_id,
    NULL::text AS publish_item_id,
    NULL::text AS request_id,
    NULL::text AS diff_summary,
    NULL::text AS source_ref,
    NULL::text AS ip_address,
    NULL::text AS user_agent,
    NULL::text AS retention_class,
    NULL::jsonb AS event_payload,
    NULL::timestamptz AS occurred_at
WHERE false;

CREATE TRIGGER trg_discard_audit_event_write
INSTEAD OF INSERT OR UPDATE OR DELETE ON audit_event
FOR EACH ROW
EXECUTE FUNCTION fpds_discard_obsolete_log_write();

CREATE VIEW llm_usage_record AS
SELECT
    NULL::text AS llm_usage_id,
    NULL::text AS model_execution_id,
    NULL::text AS run_id,
    NULL::text AS candidate_id,
    NULL::text AS provider_request_id,
    NULL::integer AS prompt_tokens,
    NULL::integer AS completion_tokens,
    NULL::numeric(12, 6) AS estimated_cost,
    NULL::jsonb AS usage_metadata,
    NULL::timestamptz AS recorded_at
WHERE false;

CREATE TRIGGER trg_discard_llm_usage_record_write
INSTEAD OF INSERT OR UPDATE OR DELETE ON llm_usage_record
FOR EACH ROW
EXECUTE FUNCTION fpds_discard_obsolete_log_write();

-- Vector rows duplicate evidence text and are not required for correctness;
-- retrieval already has a metadata-scored fallback. Dashboard aggregates are
-- derived from public_product_projection at request time.
DROP TABLE IF EXISTS evidence_chunk_embedding;
DROP TABLE IF EXISTS dashboard_metric_snapshot;
DROP TABLE IF EXISTS dashboard_ranking_snapshot;
DROP TABLE IF EXISTS dashboard_scatter_snapshot;

-- Old aggregate requests may point at snapshots that are intentionally aged
-- out. Preserve the request row only while it is inside its own retention
-- window and make the snapshot reference nullable on deletion.
ALTER TABLE aggregate_refresh_request
    DROP CONSTRAINT IF EXISTS aggregate_refresh_request_snapshot_id_fkey;
ALTER TABLE aggregate_refresh_request
    ADD CONSTRAINT aggregate_refresh_request_snapshot_id_fkey
    FOREIGN KEY (snapshot_id)
    REFERENCES aggregate_refresh_run(snapshot_id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_field_evidence_link_chunk
    ON field_evidence_link (evidence_chunk_id);

CREATE OR REPLACE FUNCTION fpds_apply_data_retention()
RETURNS jsonb
LANGUAGE plpgsql
AS $fpds$
DECLARE
    recovered_stale_runs integer := 0;
    removed_evidence_chunks integer := 0;
    removed_model_executions integer := 0;
    removed_aggregate_snapshots integer := 0;
    removed_aggregate_requests integer := 0;
    removed_login_attempts integer := 0;
    removed_auth_sessions integer := 0;
    compacted_run_metadata integer := 0;
    compacted_source_metadata integer := 0;
BEGIN
    -- Pipeline stages have bounded subprocess timeouts. A run that is still
    -- marked started after twelve hours is abandoned state, not active work.
    UPDATE ingestion_run
    SET
        run_state = 'failed',
        partial_completion_flag = true,
        error_summary = COALESCE(
            NULLIF(error_summary, ''),
            'Data retention recovered an abandoned ingestion run.'
        ),
        run_metadata = COALESCE(run_metadata, '{}'::jsonb) || jsonb_build_object(
            'automation_recovered', true,
            'automation_recovery_reason', 'stale_started_run'
        ),
        completed_at = now()
    WHERE run_state = 'started'
      AND started_at < now() - interval '12 hours';
    GET DIAGNOSTICS recovered_stale_runs = ROW_COUNT;

    -- Keep every field-linked chunk, chunks belonging to the newest fetched
    -- snapshot for each source document, and chunks selected by a running job.
    -- Older unlinked chunks have already served parsing/retrieval and are not
    -- used by Admin or Public screens.
    WITH latest_snapshots AS MATERIALIZED (
        SELECT DISTINCT ON (source_document_id)
            snapshot_id
        FROM source_snapshot
        ORDER BY
            source_document_id,
            fetched_at DESC,
            created_at DESC,
            snapshot_id DESC
    ), protected_parsed_documents AS MATERIALIZED (
        SELECT pd.parsed_document_id
        FROM parsed_document AS pd
        JOIN latest_snapshots AS latest
          ON latest.snapshot_id = pd.snapshot_id
        UNION
        SELECT pd.parsed_document_id
        FROM parsed_document AS pd
        JOIN run_source_item AS rsi
          ON rsi.selected_snapshot_id = pd.snapshot_id
        JOIN ingestion_run AS ir
          ON ir.run_id = rsi.run_id
        WHERE ir.run_state = 'started'
    )
    DELETE FROM evidence_chunk AS ec
    WHERE NOT EXISTS (
        SELECT 1
        FROM field_evidence_link AS fel
        WHERE fel.evidence_chunk_id = ec.evidence_chunk_id
    )
      AND NOT EXISTS (
        SELECT 1
        FROM protected_parsed_documents AS protected
        WHERE protected.parsed_document_id = ec.parsed_document_id
      );
    GET DIAGNOSTICS removed_evidence_chunks = ROW_COUNT;

    -- model_execution remains the current AI result/cache store. Retain rows
    -- referenced by candidates, active runs, and the latest review verification;
    -- expire older diagnostic executions after fourteen days.
    DELETE FROM model_execution AS me
    WHERE me.execution_status <> 'started'
      AND me.started_at < now() - interval '14 days'
      AND NOT EXISTS (
          SELECT 1
          FROM normalized_candidate AS nc
          WHERE nc.model_execution_id = me.model_execution_id
      )
      AND NOT EXISTS (
          SELECT 1
          FROM ingestion_run AS ir
          WHERE ir.run_id = me.run_id
            AND ir.run_state = 'started'
      )
      AND NOT (
          me.stage_name = 'ai_verification'
          AND NULLIF(me.execution_metadata ->> 'review_task_id', '') IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM model_execution AS newer
              WHERE newer.stage_name = 'ai_verification'
                AND newer.execution_metadata ->> 'review_task_id'
                    = me.execution_metadata ->> 'review_task_id'
                AND (newer.started_at, newer.model_execution_id)
                    > (me.started_at, me.model_execution_id)
          )
      );
    GET DIAGNOSTICS removed_model_executions = ROW_COUNT;

    WITH ranked AS (
        SELECT
            snapshot_id,
            row_number() OVER (
                PARTITION BY refresh_scope, country_code
                ORDER BY COALESCE(refreshed_at, attempted_at) DESC,
                         attempted_at DESC,
                         snapshot_id DESC
            ) AS snapshot_rank
        FROM aggregate_refresh_run
        WHERE refresh_status = 'completed'
    ), removable AS (
        SELECT snapshot_id
        FROM ranked
        WHERE snapshot_rank > 2
        UNION ALL
        SELECT snapshot_id
        FROM aggregate_refresh_run
        WHERE refresh_status = 'failed'
          AND attempted_at < now() - interval '14 days'
    )
    DELETE FROM aggregate_refresh_run AS arr
    USING removable
    WHERE arr.snapshot_id = removable.snapshot_id;
    GET DIAGNOSTICS removed_aggregate_snapshots = ROW_COUNT;

    DELETE FROM aggregate_refresh_request
    WHERE request_status IN ('completed', 'failed')
      AND COALESCE(completed_at, requested_at) < now() - interval '14 days';
    GET DIAGNOSTICS removed_aggregate_requests = ROW_COUNT;

    DELETE FROM auth_login_attempt
    WHERE attempted_at < now() - interval '24 hours';
    GET DIAGNOSTICS removed_login_attempts = ROW_COUNT;

    DELETE FROM admin_auth_session
    WHERE COALESCE(revoked_at, absolute_expires_at) < now() - interval '7 days';
    GET DIAGNOSTICS removed_auth_sessions = ROW_COUNT;

    -- Keep only retry, identity, and correlation fields after the short-lived
    -- diagnostic window. Large discovery notes and duplicated stage payloads
    -- are not used by the Admin run screen.
    UPDATE ingestion_run AS ir
    SET run_metadata = COALESCE((
        SELECT jsonb_object_agg(entry.key, entry.value)
        FROM jsonb_each(ir.run_metadata) AS entry
        WHERE entry.key = ANY (ARRAY[
            'pipeline_stage', 'trigger_type', 'triggered_by',
            'country_code', 'bank_code', 'product_type', 'catalog_item_id',
            'correlation_id', 'request_id', 'source_ids',
            'selected_source_ids', 'target_source_ids', 'retry_request_id',
            'automation_recovered', 'automation_recovery_reason'
        ]::text[])
    ), '{}'::jsonb)
    WHERE ir.run_state IN ('completed', 'failed', 'retried')
      AND COALESCE(ir.completed_at, ir.started_at) < now() - interval '14 days'
      AND EXISTS (
          SELECT 1
          FROM jsonb_object_keys(ir.run_metadata) AS key_name
          WHERE key_name <> ALL (ARRAY[
              'pipeline_stage', 'trigger_type', 'triggered_by',
              'country_code', 'bank_code', 'product_type', 'catalog_item_id',
              'correlation_id', 'request_id', 'source_ids',
              'selected_source_ids', 'target_source_ids', 'retry_request_id',
              'automation_recovered', 'automation_recovery_reason'
          ]::text[])
      );
    GET DIAGNOSTICS compacted_run_metadata = ROW_COUNT;

    UPDATE run_source_item AS rsi
    SET stage_metadata = COALESCE((
        SELECT jsonb_object_agg(entry.key, entry.value)
        FROM jsonb_each(rsi.stage_metadata) AS entry
        WHERE entry.key = ANY (ARRAY[
            'attempt_count', 'candidate_id', 'candidate_run_id', 'chunk_count',
            'correlation_id', 'field_evidence_link_count',
            'normalization_action', 'parse_action', 'parser_version',
            'preflight_status', 'queue_reason_codes', 'request_id',
            'review_task_id', 'snapshot_action', 'source_confidence',
            'validation_action', 'validation_issue_codes',
            'validation_status'
        ]::text[])
    ), '{}'::jsonb)
    FROM ingestion_run AS ir
    WHERE ir.run_id = rsi.run_id
      AND ir.run_state IN ('completed', 'failed', 'retried')
      AND COALESCE(ir.completed_at, ir.started_at) < now() - interval '14 days'
      AND EXISTS (
          SELECT 1
          FROM jsonb_object_keys(rsi.stage_metadata) AS key_name
          WHERE key_name <> ALL (ARRAY[
              'attempt_count', 'candidate_id', 'candidate_run_id', 'chunk_count',
              'correlation_id', 'field_evidence_link_count',
              'normalization_action', 'parse_action', 'parser_version',
              'preflight_status', 'queue_reason_codes', 'request_id',
              'review_task_id', 'snapshot_action', 'source_confidence',
              'validation_action', 'validation_issue_codes',
              'validation_status'
          ]::text[])
      );
    GET DIAGNOSTICS compacted_source_metadata = ROW_COUNT;

    RETURN jsonb_build_object(
        'recovered_stale_runs', recovered_stale_runs,
        'evidence_chunks', removed_evidence_chunks,
        'model_executions', removed_model_executions,
        'aggregate_snapshots', removed_aggregate_snapshots,
        'aggregate_requests', removed_aggregate_requests,
        'login_attempts', removed_login_attempts,
        'auth_sessions', removed_auth_sessions,
        'compacted_run_metadata', compacted_run_metadata,
        'compacted_source_metadata', compacted_source_metadata
    );
END
$fpds$;

SELECT fpds_apply_data_retention();

INSERT INTO migration_history (migration_name)
VALUES ('0040_bounded_operational_storage.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
