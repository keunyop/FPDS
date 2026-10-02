"""Read-only collection eligibility shared by launch, retry and source reuse.

A human hold is reversible through explicit precision rediscovery. It is not
proof of product retirement. Unknown or transient outcomes remain collectable.
"""
from __future__ import annotations

import re
from typing import Any

BOUNDARY_REASONS = frozenset({
    "multi_product_family_overview", "hub_page_not_detail",
    "verified_coverage_review_source", "verified_coverage_lending_review_source",
})


def source_block_reason(row: dict[str, Any], *, revalidate: bool = False) -> str | None:
    if revalidate:
        return None
    if str(row.get("latest_stage_status") or "").lower() == "failed":
        error = str(row.get("latest_error_summary") or "").lower()
        # The format-aware probe/capture now supports real PDF responses on
        # HTML registry hints. Recheck this precise old format mismatch once
        # through normal bounded preflight, without relaxing other failures.
        if (row.get("source_type") == "html" and re.search(
                r"text fetch expected html content but received application/pdf(?:\s|;|$)", error)):
            return None
        if any(marker in error for marker in (
            "html access challenge remained after bounded browser fallback",
            "pdf source returned non-pdf content after bounded fetch recovery",
            "host not in discovery fetch allowlist",
            "text fetch expected html content but received",
        )):
            return "terminal_source_failure"
        if re.search(r"(?:http(?: error)?|status)\s*[:=]?\s*(?:404|410)\b", error):
            return "source_not_found"
        if (row.get("source_type") == "pdf"
                and not str(row.get("latest_snapshot_content_type") or "").startswith("application/pdf")
                and row.get("latest_browser_fallback_reason") == "html_access_challenge"):
            return "terminal_source_failure"
    if row.get("discovery_role") != "detail":
        return None
    # The newest candidate and decision are selected in SQL. A newer pass or
    # approval must supersede an older hold; system deduplication is not a veto.
    state = row.get("latest_review_state")
    action = row.get("latest_review_action")
    if ((state == "deferred" and action == "defer") or (state == "rejected" and action == "reject")):
        if row.get("latest_review_actor") and int(row.get("latest_candidate_count") or 1) == 1:
            return "review_deferred" if state == "deferred" else "review_rejected"
    if ((state in {"approved", "edited"} and action in {"approve", "edit_approve"})
            or row.get("latest_candidate_state") == "approved"):
        return None
    metadata = row.get("discovery_metadata") or {}
    if not isinstance(metadata, dict):
        return None
    reasons = set(metadata.get("selection_reason_codes") or []) | set(metadata.get("page_evidence_reason_codes") or [])
    if reasons.intersection(BOUNDARY_REASONS):
        return "unresolved_product_boundary"
    return None


def no_detail_result_is_structural(notes: list[str]) -> bool:
    """Classify each fetch failure before judging the whole zero-detail scope.

    A format mismatch or allowlist denial cannot be fixed by repeating the same
    request. An unrelated timeout must still keep the overall result retryable.
    """
    meaningful = []
    for note in notes:
        text = str(note).strip().lower()
        structural_fetch = any(marker in text for marker in (
            "text fetch expected html content but received",
            "host not in discovery fetch allowlist",
            "html access challenge remained after bounded browser fallback",
            "pdf source returned non-pdf content after bounded fetch recovery",
        ))
        if structural_fetch:
            continue
        meaningful.append(text)
    normalized = " ".join(meaningful)
    if any(marker in normalized for marker in (
        "timed out", "timeout", "fetch was unavailable", "evidence was unavailable",
        "could not resolve", "connection reset", "connection refused", "temporary",
        "certificate_verify_failed", "browser fallback was unavailable",
        "http 408", "http 425", "http 429", "http 500", "http 502", "http 503", "http 504",
    )):
        return False
    return any(marker in " ".join(str(n).lower() for n in notes) for marker in (
        "detail rejection summary", "candidate validation did not promote",
        "no candidate-producing detail sources", "no detail sources",
        "html access challenge remained after bounded browser fallback",
    ))


def load_source_preflight_rows(connection: Any, *, source_ids: list[str] | None = None,
                               country_code: str | None = None, bank_code: str | None = None,
                               product_type: str | None = None,
                               source_language: str | None = None) -> list[dict[str, Any]]:
    """Match history by scoped URL, never by mutable source metadata alone.

    Scope reuse reads active sources. Explicit source retries also inspect the
    history of inactive sources, so changing status cannot erase a human hold.
    """
    return connection.execute(
        """
        SELECT sri.*, latest.stage_status AS latest_stage_status,
               latest.error_summary AS latest_error_summary,
               latest.snapshot_content_type AS latest_snapshot_content_type,
               latest.browser_fallback_reason AS latest_browser_fallback_reason,
               candidate.candidate_state AS latest_candidate_state,
               candidate.candidate_count AS latest_candidate_count,
               reviewed.review_state AS latest_review_state,
               reviewed.review_task_id AS latest_review_task_id,
               decision.action_type AS latest_review_action,
               decision.actor_user_id AS latest_review_actor
        FROM source_registry_item sri
        LEFT JOIN LATERAL (
            SELECT rsi.stage_status, rsi.error_summary, ss.content_type AS snapshot_content_type,
                   ss.response_metadata ->> 'browser_fallback_reason' AS browser_fallback_reason
            FROM run_source_item rsi
            JOIN source_document sd USING (source_document_id)
            LEFT JOIN source_snapshot ss ON ss.snapshot_id = rsi.selected_snapshot_id
            WHERE sd.country_code = sri.country_code AND sd.bank_code = sri.bank_code
              AND sd.normalized_source_url = sri.normalized_url
              AND sd.source_type = sri.source_type
            ORDER BY rsi.created_at DESC, rsi.run_source_item_id DESC LIMIT 1
        ) latest ON true
        LEFT JOIN LATERAL (
            SELECT nc.candidate_id, nc.candidate_state,
                   COUNT(*) OVER (PARTITION BY nc.run_id) AS candidate_count
            FROM normalized_candidate nc JOIN source_document sd USING (source_document_id)
            WHERE nc.country_code = sri.country_code AND nc.bank_code = sri.bank_code
              AND nc.product_type = sri.product_type
              AND nc.source_language = sri.source_language
              AND sd.country_code = sri.country_code AND sd.bank_code = sri.bank_code
              AND sd.normalized_source_url = sri.normalized_url
            ORDER BY nc.created_at DESC, nc.candidate_id DESC LIMIT 1
        ) candidate ON true
        LEFT JOIN LATERAL (
            SELECT rt.review_task_id, rt.review_state FROM review_task rt
            WHERE rt.candidate_id = candidate.candidate_id
            ORDER BY rt.created_at DESC, rt.review_task_id DESC LIMIT 1
        ) reviewed ON true
        LEFT JOIN LATERAL (
            SELECT rd.action_type, rd.actor_user_id FROM review_decision rd
            WHERE rd.review_task_id = reviewed.review_task_id
            ORDER BY rd.decided_at DESC, rd.review_decision_id DESC LIMIT 1
        ) decision ON true
        WHERE (%(source_ids)s::text[] IS NULL OR sri.source_id = ANY(%(source_ids)s))
          AND (%(country_code)s::text IS NULL OR sri.country_code = %(country_code)s)
          AND (%(bank_code)s::text IS NULL OR sri.bank_code = %(bank_code)s)
          AND (%(product_type)s::text IS NULL OR sri.product_type = %(product_type)s)
          AND (%(source_language)s::text IS NULL OR sri.source_language = %(source_language)s)
          AND (sri.status = 'active' OR %(source_ids)s::text[] IS NOT NULL)
        ORDER BY sri.source_id
        """,
        {"source_ids": source_ids, "country_code": country_code, "bank_code": bank_code,
         "product_type": product_type, "source_language": source_language},
    ).fetchall()
