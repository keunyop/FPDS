BEGIN;

CREATE TABLE IF NOT EXISTS aggregate_refresh_run (
    snapshot_id text PRIMARY KEY,
    triggered_by_run_id text REFERENCES ingestion_run(run_id),
    refresh_scope text NOT NULL,
    country_code text NOT NULL,
    filter_scope jsonb NOT NULL DEFAULT '{}'::jsonb,
    refresh_status text NOT NULL CHECK (refresh_status IN ('started', 'completed', 'failed')),
    source_change_cutoff_at timestamptz,
    attempted_at timestamptz NOT NULL,
    refreshed_at timestamptz,
    stale_flag boolean NOT NULL DEFAULT false,
    error_summary text,
    refresh_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public_product_projection (
    snapshot_id text NOT NULL REFERENCES aggregate_refresh_run(snapshot_id) ON DELETE CASCADE,
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    bank_code text NOT NULL REFERENCES bank(bank_code),
    bank_name text NOT NULL,
    country_code text NOT NULL,
    product_family text NOT NULL,
    product_type text NOT NULL,
    subtype_code text,
    product_name text NOT NULL,
    source_language text NOT NULL,
    currency text NOT NULL,
    status text NOT NULL,
    public_display_rate numeric(12,4),
    public_display_fee numeric(12,2),
    monthly_fee numeric(12,2),
    effective_fee numeric(12,2),
    minimum_balance numeric(12,2),
    minimum_deposit numeric(12,2),
    term_length_days integer,
    product_highlight_badge_code text,
    target_customer_tags jsonb NOT NULL DEFAULT '[]'::jsonb,
    fee_bucket text,
    minimum_balance_bucket text,
    minimum_deposit_bucket text,
    term_bucket text,
    last_verified_at timestamptz,
    last_changed_at timestamptz,
    refresh_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (snapshot_id, product_id)
);

CREATE TABLE IF NOT EXISTS dashboard_metric_snapshot (
    snapshot_id text NOT NULL REFERENCES aggregate_refresh_run(snapshot_id) ON DELETE CASCADE,
    scope_key text NOT NULL,
    total_active_products integer NOT NULL,
    banks_in_scope integer NOT NULL,
    highest_display_rate numeric(12,4),
    recently_changed_products_30d integer NOT NULL,
    breakdown_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    freshness_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    completeness_note text,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (snapshot_id, scope_key)
);

CREATE TABLE IF NOT EXISTS dashboard_ranking_snapshot (
    snapshot_id text NOT NULL REFERENCES aggregate_refresh_run(snapshot_id) ON DELETE CASCADE,
    ranking_key text NOT NULL,
    scope_key text NOT NULL,
    rank integer NOT NULL,
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    bank_code text NOT NULL REFERENCES bank(bank_code),
    bank_name text NOT NULL,
    product_name text NOT NULL,
    product_type text NOT NULL,
    metric_value numeric(12,4),
    metric_unit text NOT NULL,
    last_changed_at timestamptz,
    ranking_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (snapshot_id, ranking_key, scope_key, product_id)
);

CREATE TABLE IF NOT EXISTS dashboard_scatter_snapshot (
    snapshot_id text NOT NULL REFERENCES aggregate_refresh_run(snapshot_id) ON DELETE CASCADE,
    axis_preset text NOT NULL,
    scope_key text NOT NULL,
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    bank_code text NOT NULL REFERENCES bank(bank_code),
    bank_name text NOT NULL,
    product_name text NOT NULL,
    product_type text NOT NULL,
    x_value numeric(12,4) NOT NULL,
    y_value numeric(12,4) NOT NULL,
    highlight_badge_code text,
    last_changed_at timestamptz,
    point_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (snapshot_id, axis_preset, scope_key, product_id)
);

CREATE INDEX IF NOT EXISTS idx_aggregate_refresh_run_status_attempted_at
    ON aggregate_refresh_run (refresh_status, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_aggregate_refresh_run_scope_refreshed_at
    ON aggregate_refresh_run (refresh_scope, refreshed_at DESC);

CREATE INDEX IF NOT EXISTS idx_public_product_projection_scope
    ON public_product_projection (snapshot_id, country_code, product_type, bank_code, status);

CREATE INDEX IF NOT EXISTS idx_public_product_projection_filters
    ON public_product_projection (
        snapshot_id,
        fee_bucket,
        minimum_balance_bucket,
        minimum_deposit_bucket,
        term_bucket
    );

CREATE INDEX IF NOT EXISTS idx_dashboard_ranking_snapshot_lookup
    ON dashboard_ranking_snapshot (snapshot_id, scope_key, ranking_key, rank);

CREATE INDEX IF NOT EXISTS idx_dashboard_scatter_snapshot_lookup
    ON dashboard_scatter_snapshot (snapshot_id, scope_key, axis_preset);

INSERT INTO migration_history (migration_name)
VALUES ('0003_aggregate_refresh.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
