BEGIN;

CREATE TABLE IF NOT EXISTS public_product_engagement_daily (
    event_date date NOT NULL,
    country_code text NOT NULL REFERENCES country_registry(country_code),
    product_id text NOT NULL REFERENCES canonical_product(product_id),
    event_type text NOT NULL CHECK (
        event_type IN (
            'product_detail_click',
            'official_bank_click',
            'finder_product_selected'
        )
    ),
    event_count bigint NOT NULL DEFAULT 1 CHECK (event_count > 0),
    first_recorded_at timestamptz NOT NULL DEFAULT now(),
    last_recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_date, country_code, product_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_public_product_engagement_scope
    ON public_product_engagement_daily (
        country_code,
        event_date DESC,
        event_type,
        product_id
    );

CREATE INDEX IF NOT EXISTS idx_public_product_engagement_retention
    ON public_product_engagement_daily (event_date);

CREATE OR REPLACE FUNCTION fpds_trim_public_product_engagement_daily()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM public_product_engagement_daily
    WHERE event_date < current_date - 399;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_trim_public_product_engagement_daily
    ON public_product_engagement_daily;

CREATE TRIGGER trg_trim_public_product_engagement_daily
AFTER INSERT ON public_product_engagement_daily
FOR EACH STATEMENT
EXECUTE FUNCTION fpds_trim_public_product_engagement_daily();

COMMENT ON TABLE public_product_engagement_daily IS
    'Anonymous product-level daily counters only. No visitor, query, cookie, IP, or profile values are retained; rows are bounded to 400 days.';

INSERT INTO migration_history (migration_name)
VALUES ('0045_public_product_engagement.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
