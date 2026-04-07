BEGIN;

CREATE TABLE IF NOT EXISTS migration_history (
    migration_name text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bank (
    bank_code text PRIMARY KEY,
    country_code text NOT NULL,
    bank_name text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS taxonomy_registry (
    taxonomy_id text PRIMARY KEY,
    country_code text NOT NULL,
    product_family text NOT NULL,
    product_type text NOT NULL,
    subtype_code text NOT NULL,
    display_order integer NOT NULL DEFAULT 0,
    active_flag boolean NOT NULL DEFAULT true,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (country_code, product_family, product_type, subtype_code)
);

CREATE TABLE IF NOT EXISTS processing_policy_config (
    policy_config_id text PRIMARY KEY,
    policy_key text NOT NULL,
    version_no integer NOT NULL,
    policy_value jsonb NOT NULL DEFAULT '{}'::jsonb,
    active_flag boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by text,
    notes text,
    UNIQUE (policy_key, version_no)
);

CREATE TABLE IF NOT EXISTS ingestion_run (
    run_id text PRIMARY KEY,
    run_state text NOT NULL CHECK (run_state IN ('started', 'completed', 'failed', 'retried')),
    trigger_type text NOT NULL,
    triggered_by text,
    source_scope_count integer NOT NULL DEFAULT 0,
    source_success_count integer NOT NULL DEFAULT 0,
    source_failure_count integer NOT NULL DEFAULT 0,
    candidate_count integer NOT NULL DEFAULT 0,
    review_queued_count integer NOT NULL DEFAULT 0,
    error_summary text,
    partial_completion_flag boolean NOT NULL DEFAULT false,
    retry_of_run_id text REFERENCES ingestion_run(run_id),
    retried_by_run_id text REFERENCES ingestion_run(run_id),
    run_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at timestamptz NOT NULL,
    completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS source_document (
    source_document_id text PRIMARY KEY,
    bank_code text NOT NULL REFERENCES bank(bank_code),
    country_code text NOT NULL,
    normalized_source_url text NOT NULL,
    source_type text NOT NULL,
    source_language text NOT NULL,
    registry_managed_flag boolean NOT NULL DEFAULT false,
    source_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    discovered_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bank_code, normalized_source_url, source_type)
);

CREATE TABLE IF NOT EXISTS source_snapshot (
    snapshot_id text PRIMARY KEY,
    source_document_id text NOT NULL REFERENCES source_document(source_document_id),
    object_storage_key text NOT NULL,
    content_type text NOT NULL,
    checksum text NOT NULL,
    fingerprint text NOT NULL,
    fetch_status text NOT NULL,
    response_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    retention_class text NOT NULL DEFAULT 'hot',
    fetched_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_document_id, fingerprint)
);

CREATE TABLE IF NOT EXISTS run_source_item (
    run_source_item_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES ingestion_run(run_id),
    source_document_id text NOT NULL REFERENCES source_document(source_document_id),
    selected_snapshot_id text REFERENCES source_snapshot(snapshot_id),
    stage_status text NOT NULL,
    warning_count integer NOT NULL DEFAULT 0,
    error_count integer NOT NULL DEFAULT 0,
    error_summary text,
    stage_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, source_document_id)
);

CREATE TABLE IF NOT EXISTS parsed_document (
    parsed_document_id text PRIMARY KEY,
    snapshot_id text NOT NULL UNIQUE REFERENCES source_snapshot(snapshot_id),
    parsed_storage_key text NOT NULL,
    parser_version text NOT NULL,
    parse_quality_note text,
    parser_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    retention_class text NOT NULL DEFAULT 'hot',
    parsed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_chunk (
    evidence_chunk_id text PRIMARY KEY,
    parsed_document_id text NOT NULL REFERENCES parsed_document(parsed_document_id),
    chunk_index integer NOT NULL,
    anchor_type text NOT NULL,
    anchor_value text,
    page_no integer,
    source_language text NOT NULL,
    chunk_char_start integer,
    chunk_char_end integer,
    evidence_excerpt text NOT NULL,
    retrieval_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parsed_document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS model_execution (
    model_execution_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES ingestion_run(run_id),
    source_document_id text REFERENCES source_document(source_document_id),
    stage_name text NOT NULL,
    agent_name text NOT NULL,
    model_id text NOT NULL,
    execution_status text NOT NULL,
    execution_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at timestamptz NOT NULL,
    completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS normalized_candidate (
    candidate_id text PRIMARY KEY,
    run_id text NOT NULL REFERENCES ingestion_run(run_id),
    source_document_id text NOT NULL REFERENCES source_document(source_document_id),
    model_execution_id text REFERENCES model_execution(model_execution_id),
    candidate_state text NOT NULL CHECK (candidate_state IN ('draft', 'auto_validated', 'in_review', 'approved', 'rejected', 'superseded')),
    validation_status text NOT NULL CHECK (validation_status IN ('pass', 'warning', 'error')),
    source_confidence numeric(5,4) NOT NULL CHECK (source_confidence >= 0 AND source_confidence <= 1),
    review_reason_code text,
    country_code text NOT NULL,
    bank_code text NOT NULL REFERENCES bank(bank_code),
    product_family text NOT NULL DEFAULT 'deposit',
    product_type text NOT NULL,
    subtype_code text,
    product_name text NOT NULL,
    source_language text NOT NULL,
    currency text NOT NULL,
    validation_issue_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
    candidate_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    field_mapping_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS canonical_product (
    product_id text PRIMARY KEY,
    bank_code text NOT NULL REFERENCES bank(bank_code),
    country_code text NOT NULL,
    product_family text NOT NULL,
    product_type text NOT NULL,
    subtype_code text,
    product_name text NOT NULL,
    source_language text NOT NULL,
    currency text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive', 'discontinued', 'draft')),
    current_version_no integer NOT NULL DEFAULT 1,
    last_verified_at timestamptz NOT NULL,
    last_changed_at timestamptz,
    current_snapshot_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS review_task (
    review_task_id text PRIMARY KEY,
    candidate_id text NOT NULL UNIQUE REFERENCES normalized_candidate(candidate_id),
    run_id text NOT NULL REFERENCES ingestion_run(run_id),
    product_id text REFERENCES canonical_product(product_id),
    review_state text NOT NULL CHECK (review_state IN ('queued', 'approved', 'rejected', 'edited', 'deferred')),
    queue_reason_code text NOT NULL,
    issue_summary jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS review_decision (
    review_decision_id text PRIMARY KEY,
    review_task_id text NOT NULL REFERENCES review_task(review_task_id),
    actor_user_id text,
    action_type text NOT NULL CHECK (action_type IN ('approve', 'reject', 'edit_approve', 'defer', 'requeue')),
    reason_code text,
    reason_text text,
    diff_summary text,
    override_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    decided_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS product_version (
    product_version_id text PRIMARY KEY,
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    approved_candidate_id text UNIQUE REFERENCES normalized_candidate(candidate_id),
    version_no integer NOT NULL,
    version_status text NOT NULL CHECK (version_status IN ('approved', 'superseded')),
    normalized_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    approved_at timestamptz NOT NULL,
    superseded_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (product_id, version_no)
);

CREATE TABLE IF NOT EXISTS field_evidence_link (
    field_evidence_link_id text PRIMARY KEY,
    candidate_id text REFERENCES normalized_candidate(candidate_id),
    product_version_id text REFERENCES product_version(product_version_id),
    evidence_chunk_id text NOT NULL REFERENCES evidence_chunk(evidence_chunk_id),
    source_document_id text NOT NULL REFERENCES source_document(source_document_id),
    field_name text NOT NULL,
    candidate_value text NOT NULL,
    citation_confidence numeric(5,4) NOT NULL CHECK (citation_confidence >= 0 AND citation_confidence <= 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (candidate_id IS NOT NULL AND product_version_id IS NULL)
        OR (candidate_id IS NULL AND product_version_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS change_event (
    change_event_id text PRIMARY KEY,
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    product_version_id text REFERENCES product_version(product_version_id),
    run_id text REFERENCES ingestion_run(run_id),
    review_task_id text REFERENCES review_task(review_task_id),
    event_type text NOT NULL CHECK (event_type IN ('New', 'Updated', 'Discontinued', 'Reclassified', 'ManualOverride')),
    event_reason_code text,
    event_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    detected_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS publish_item (
    publish_item_id text PRIMARY KEY,
    product_version_id text NOT NULL REFERENCES product_version(product_version_id),
    target_system_code text NOT NULL,
    publish_state text NOT NULL CHECK (publish_state IN ('pending', 'published', 'retry', 'reconciliation')),
    pending_reason_code text,
    target_environment text NOT NULL CHECK (target_environment IN ('dev', 'prod')),
    target_master_id text,
    target_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (product_version_id, target_system_code)
);

CREATE TABLE IF NOT EXISTS publish_attempt (
    publish_attempt_id text PRIMARY KEY,
    publish_item_id text NOT NULL REFERENCES publish_item(publish_item_id),
    attempt_no integer NOT NULL,
    attempt_result_state text NOT NULL CHECK (attempt_result_state IN ('published', 'retry', 'reconciliation', 'failed')),
    error_code text,
    response_summary text,
    response_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    attempted_at timestamptz NOT NULL,
    UNIQUE (publish_item_id, attempt_no)
);

CREATE TABLE IF NOT EXISTS llm_usage_record (
    llm_usage_id text PRIMARY KEY,
    model_execution_id text NOT NULL REFERENCES model_execution(model_execution_id),
    run_id text NOT NULL REFERENCES ingestion_run(run_id),
    candidate_id text REFERENCES normalized_candidate(candidate_id),
    provider_request_id text,
    prompt_tokens integer NOT NULL DEFAULT 0,
    completion_tokens integer NOT NULL DEFAULT 0,
    estimated_cost numeric(12,6) NOT NULL DEFAULT 0,
    usage_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    recorded_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_event (
    audit_event_id text PRIMARY KEY,
    event_category text NOT NULL CHECK (event_category IN ('review', 'run', 'publish', 'auth', 'config', 'usage')),
    event_type text NOT NULL,
    actor_type text NOT NULL CHECK (actor_type IN ('system', 'user', 'service', 'scheduler')),
    actor_id text,
    actor_role_snapshot text,
    target_type text NOT NULL,
    target_id text NOT NULL,
    previous_state text,
    new_state text,
    reason_code text,
    reason_text text,
    run_id text REFERENCES ingestion_run(run_id),
    candidate_id text REFERENCES normalized_candidate(candidate_id),
    review_task_id text REFERENCES review_task(review_task_id),
    product_id text REFERENCES canonical_product(product_id),
    publish_item_id text REFERENCES publish_item(publish_item_id),
    request_id text,
    diff_summary text,
    source_ref text,
    ip_address text,
    user_agent text,
    retention_class text NOT NULL DEFAULT 'hot',
    event_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ingestion_run_state_started_at
    ON ingestion_run (run_state, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_source_document_bank_type
    ON source_document (bank_code, source_type, discovered_at DESC);

CREATE INDEX IF NOT EXISTS idx_source_snapshot_source_fetched_at
    ON source_snapshot (source_document_id, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_run_source_item_run_status
    ON run_source_item (run_id, stage_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_parsed_document_snapshot
    ON parsed_document (snapshot_id);

CREATE INDEX IF NOT EXISTS idx_evidence_chunk_parsed_anchor
    ON evidence_chunk (parsed_document_id, anchor_type, page_no, chunk_index);

CREATE INDEX IF NOT EXISTS idx_model_execution_run_stage
    ON model_execution (run_id, stage_name, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_candidate_run_state
    ON normalized_candidate (run_id, candidate_state, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_candidate_bank_product_type
    ON normalized_candidate (bank_code, product_type, validation_status);

CREATE INDEX IF NOT EXISTS idx_review_task_state_created_at
    ON review_task (review_state, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_review_decision_task_decided_at
    ON review_decision (review_task_id, decided_at DESC);

CREATE INDEX IF NOT EXISTS idx_product_bank_status
    ON canonical_product (bank_code, product_type, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_product_version_product_approved
    ON product_version (product_id, approved_at DESC);

CREATE INDEX IF NOT EXISTS idx_field_evidence_link_candidate_field
    ON field_evidence_link (candidate_id, field_name);

CREATE INDEX IF NOT EXISTS idx_field_evidence_link_product_field
    ON field_evidence_link (product_version_id, field_name);

CREATE INDEX IF NOT EXISTS idx_change_event_product_detected_at
    ON change_event (product_id, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_publish_item_state_updated_at
    ON publish_item (publish_state, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_publish_attempt_item_attempted_at
    ON publish_attempt (publish_item_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_llm_usage_run_recorded_at
    ON llm_usage_record (run_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_event_category_occurred_at
    ON audit_event (event_category, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_event_target
    ON audit_event (target_type, target_id, occurred_at DESC);

INSERT INTO bank (bank_code, country_code, bank_name, status)
VALUES
    ('RBC', 'CA', 'Royal Bank of Canada', 'active'),
    ('TD', 'CA', 'TD Bank', 'active'),
    ('BMO', 'CA', 'BMO', 'active'),
    ('SCOTIA', 'CA', 'Scotiabank', 'active'),
    ('CIBC', 'CA', 'CIBC', 'active')
ON CONFLICT (bank_code) DO NOTHING;

INSERT INTO taxonomy_registry (
    taxonomy_id,
    country_code,
    product_family,
    product_type,
    subtype_code,
    display_order,
    active_flag,
    notes
)
VALUES
    ('tax-ca-deposit-chequing-standard', 'CA', 'deposit', 'chequing', 'standard', 10, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-chequing-package', 'CA', 'deposit', 'chequing', 'package', 20, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-chequing-interest-bearing', 'CA', 'deposit', 'chequing', 'interest_bearing', 30, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-chequing-premium', 'CA', 'deposit', 'chequing', 'premium', 40, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-chequing-other', 'CA', 'deposit', 'chequing', 'other', 99, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-savings-standard', 'CA', 'deposit', 'savings', 'standard', 10, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-savings-high-interest', 'CA', 'deposit', 'savings', 'high_interest', 20, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-savings-youth', 'CA', 'deposit', 'savings', 'youth', 30, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-savings-foreign-currency', 'CA', 'deposit', 'savings', 'foreign_currency', 40, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-savings-other', 'CA', 'deposit', 'savings', 'other', 99, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-gic-redeemable', 'CA', 'deposit', 'gic', 'redeemable', 10, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-gic-non-redeemable', 'CA', 'deposit', 'gic', 'non_redeemable', 20, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-gic-market-linked', 'CA', 'deposit', 'gic', 'market_linked', 30, true, 'Canada deposit taxonomy v1'),
    ('tax-ca-deposit-gic-other', 'CA', 'deposit', 'gic', 'other', 99, true, 'Canada deposit taxonomy v1')
ON CONFLICT (country_code, product_family, product_type, subtype_code) DO NOTHING;

INSERT INTO processing_policy_config (
    policy_config_id,
    policy_key,
    version_no,
    policy_value,
    active_flag,
    created_by,
    notes
)
VALUES
    (
        'policy-auto-approve-min-confidence-v1',
        'AUTO_APPROVE_MIN_CONFIDENCE',
        1,
        '{"value": 1.0, "note": "Prototype keeps all candidates in review by default."}'::jsonb,
        true,
        'migration:0001_initial_baseline',
        'Initial placeholder baseline'
    ),
    (
        'policy-review-warning-confidence-floor-v1',
        'REVIEW_WARNING_CONFIDENCE_FLOOR',
        1,
        '{"value": 0.0}'::jsonb,
        true,
        'migration:0001_initial_baseline',
        'Initial placeholder baseline'
    ),
    (
        'policy-force-review-issue-codes-v1',
        'FORCE_REVIEW_ISSUE_CODES',
        1,
        '["required_field_missing", "invalid_taxonomy_code", "invalid_numeric_range", "invalid_term_value", "conflicting_evidence", "ambiguous_mapping", "partial_source_failure", "inconsistent_cross_field_logic"]'::jsonb,
        true,
        'migration:0001_initial_baseline',
        'Initial placeholder baseline'
    ),
    (
        'policy-discontinued-absence-run-threshold-v1',
        'DISCONTINUED_ABSENCE_RUN_THRESHOLD',
        1,
        '{"value": 3}'::jsonb,
        true,
        'migration:0001_initial_baseline',
        'Initial placeholder baseline'
    )
ON CONFLICT (policy_key, version_no) DO NOTHING;

INSERT INTO migration_history (migration_name)
VALUES ('0001_initial_baseline')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
