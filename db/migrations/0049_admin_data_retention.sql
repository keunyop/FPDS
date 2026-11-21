BEGIN;

-- Register the Admin maintenance routine without executing it or modifying archived data.
CREATE FUNCTION fpds_apply_admin_data_retention()
RETURNS jsonb
LANGUAGE plpgsql
AS $fpds$
DECLARE
    recovered_stale_runs integer := 0;
    removed_evidence_chunks integer := 0;
    removed_model_executions integer := 0;
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
        'login_attempts', removed_login_attempts,
        'auth_sessions', removed_auth_sessions,
        'compacted_run_metadata', compacted_run_metadata,
        'compacted_source_metadata', compacted_source_metadata
    );
END
$fpds$;

INSERT INTO migration_history (migration_name)
VALUES ('0049_admin_data_retention.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
