BEGIN;

CREATE TABLE IF NOT EXISTS public_feedback_submission (
    submission_id text PRIMARY KEY,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    country_code text NOT NULL REFERENCES country_registry(country_code),
    submission_type text NOT NULL CHECK (
        submission_type IN ('product_error', 'site_feedback')
    ),
    category text NOT NULL CHECK (
        category IN (
            'incorrect_rate_or_fee',
            'incorrect_product_details',
            'outdated_information',
            'missing_information',
            'broken_link',
            'content_issue',
            'usability_issue',
            'feature_suggestion',
            'accessibility_issue',
            'other'
        )
    ),
    details text CHECK (
        details IS NULL OR char_length(btrim(details)) BETWEEN 1 AND 2000
    ),
    locale text NOT NULL CHECK (locale IN ('en', 'ko', 'ja')),
    snapshot_id text,
    product_id text REFERENCES canonical_product(product_id),
    bank_code text,
    bank_name text,
    product_name text,
    product_type text,
    CHECK (
        (
            submission_type = 'product_error'
            AND category IN (
                'incorrect_rate_or_fee',
                'incorrect_product_details',
                'outdated_information',
                'missing_information',
                'broken_link',
                'other'
            )
            AND snapshot_id IS NOT NULL
            AND product_id IS NOT NULL
            AND bank_code IS NOT NULL
            AND bank_name IS NOT NULL
            AND product_name IS NOT NULL
            AND product_type IS NOT NULL
        )
        OR
        (
            submission_type = 'site_feedback'
            AND category IN (
                'content_issue',
                'usability_issue',
                'feature_suggestion',
                'accessibility_issue',
                'other'
            )
            AND snapshot_id IS NULL
            AND product_id IS NULL
            AND bank_code IS NULL
            AND bank_name IS NULL
            AND product_name IS NULL
            AND product_type IS NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_public_feedback_submission_scope
    ON public_feedback_submission (
        country_code,
        submitted_at DESC,
        submission_type,
        category
    );

CREATE INDEX IF NOT EXISTS idx_public_feedback_submission_retention
    ON public_feedback_submission (submitted_at);

CREATE OR REPLACE FUNCTION fpds_trim_public_feedback_submission()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM public_feedback_submission
    WHERE submitted_at < now() - interval '400 days';
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_trim_public_feedback_submission
    ON public_feedback_submission;

CREATE TRIGGER trg_trim_public_feedback_submission
AFTER INSERT ON public_feedback_submission
FOR EACH STATEMENT
EXECUTE FUNCTION fpds_trim_public_feedback_submission();

COMMENT ON TABLE public_feedback_submission IS
    'Anonymous Public product-error and site-feedback submissions retained for 400 days. No visitor, contact, IP, cookie, query, or profile value is stored.';

INSERT INTO migration_history (migration_name)
VALUES ('0046_public_feedback_submission.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
