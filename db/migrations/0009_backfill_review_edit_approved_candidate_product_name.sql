BEGIN;

-- Backfill normalized candidate names from the latest stored edit-approve
-- decision override so older review tasks load the reviewer-corrected product
-- name directly from normalized_candidate and candidate_payload.
WITH latest_product_name_override AS (
    SELECT DISTINCT ON (rt.candidate_id)
        rt.candidate_id,
        NULLIF(BTRIM(rd.override_payload ->> 'product_name'), '') AS approved_product_name,
        rd.decided_at
    FROM review_task AS rt
    JOIN review_decision AS rd
      ON rd.review_task_id = rt.review_task_id
    WHERE rd.action_type = 'edit_approve'
      AND rd.override_payload ? 'product_name'
      AND NULLIF(BTRIM(rd.override_payload ->> 'product_name'), '') IS NOT NULL
    ORDER BY rt.candidate_id, rd.decided_at DESC, rd.review_decision_id DESC
),
backfilled_candidate_name AS (
    UPDATE normalized_candidate AS nc
    SET
        product_name = latest.approved_product_name,
        candidate_payload = jsonb_set(
            COALESCE(nc.candidate_payload, '{}'::jsonb),
            '{product_name}',
            to_jsonb(latest.approved_product_name),
            true
        ),
        updated_at = GREATEST(nc.updated_at, latest.decided_at)
    FROM latest_product_name_override AS latest
    WHERE nc.candidate_id = latest.candidate_id
      AND (
          nc.product_name IS DISTINCT FROM latest.approved_product_name
          OR nc.candidate_payload ->> 'product_name' IS DISTINCT FROM latest.approved_product_name
      )
    RETURNING nc.candidate_id
)
SELECT COUNT(*) AS backfilled_candidate_count
FROM backfilled_candidate_name;

COMMIT;
