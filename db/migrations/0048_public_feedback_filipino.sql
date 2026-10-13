BEGIN;

-- Preserve existing feedback, country/product isolation and retention controls.
ALTER TABLE public_feedback_submission
    DROP CONSTRAINT public_feedback_submission_locale_check;
ALTER TABLE public_feedback_submission
    ADD CONSTRAINT public_feedback_submission_locale_check
    CHECK (locale IN ('en', 'ko', 'ja', 'fil'));

INSERT INTO migration_history (migration_name)
VALUES ('0048_public_feedback_filipino.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
