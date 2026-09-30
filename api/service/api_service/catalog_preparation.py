"""Bounded catalog preparation state, separate from candidate-producing runs."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import replace
import hashlib
import json
from typing import Any

from api_service.collection_preflight import source_block_reason

PREPARATION_VERSION = "catalog-preparation-v1"


def preparation_signature(row: dict[str, Any]) -> str:
    values = {key: row.get(key) for key in (
        "country_code", "bank_code", "product_type", "source_language",
        "homepage_url", "coverage_source_url",
    )}
    metadata = row.get("coverage_source_metadata") or {}
    values["coverage_verification"] = {key: metadata.get(key) for key in (
        "verification_status", "coverage_domain",
    )}
    values["version"] = PREPARATION_VERSION
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def preparation_state(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("coverage_source_metadata") or {}
    state = metadata.get("collection_preparation") if isinstance(metadata, dict) else None
    return state if isinstance(state, dict) else {}


def preparation_block_reason(row: dict[str, Any], *, explicit: bool) -> str | None:
    state = preparation_state(row)
    try:
        updated = datetime.fromisoformat(str(state.get("updated_at")))
        active = updated > datetime.now(UTC) - timedelta(hours=2)
    except (ValueError, TypeError):
        active = False
    if state.get("status") in {"queued", "checking", "collecting"} and active:
        return "collection_preparation_in_progress"
    if (not explicit and state.get("status") == "skipped" and not state.get("retryable")
            and state.get("signature") == preparation_signature(row)):
        return "preparation_requires_rediscovery"
    return None


def reserve_preparation(connection: Any, *, group: dict[str, Any], plan: dict[str, Any]) -> bool:
    state = {"operation_id": plan["collection_id"], "status": "queued",
             "signature": preparation_signature(group), "updated_at": datetime.now(UTC).isoformat(),
             "reason_codes": [], "run_id": None}
    row = connection.execute(
        """
        UPDATE source_registry_catalog_item
        SET coverage_source_metadata = jsonb_set(COALESCE(coverage_source_metadata, '{}'::jsonb),
            '{collection_preparation}', %(state)s::jsonb)
        WHERE catalog_item_id = %(catalog_item_id)s AND country_code = %(country_code)s
          AND status = 'active'
          AND (COALESCE(coverage_source_metadata #>> '{collection_preparation,status}', '')
                   NOT IN ('queued', 'checking', 'collecting')
               OR COALESCE(coverage_source_metadata #>> '{collection_preparation,updated_at}', '') < %(expired_before)s)
        RETURNING catalog_item_id
        """,
        {"catalog_item_id": group["catalog_item_id"], "country_code": group["country_code"],
         "state": json.dumps(state), "expired_before": (datetime.now(UTC) - timedelta(hours=2)).isoformat()},
    ).fetchone()
    return row is not None


def update_preparation(connection: Any, *, group: dict[str, Any], plan: dict[str, Any],
                       status: str, reasons: list[str] | None = None, notes: list[str] | None = None,
                       run_id: str | None = None, retryable: bool = False,
                       excluded_sources: list[dict[str, Any]] | None = None) -> bool:
    state = {"operation_id": plan["collection_id"], "status": status,
             "signature": preparation_signature(group), "updated_at": datetime.now(UTC).isoformat(),
             "reason_codes": list(reasons or []), "notes": [str(n)[:800] for n in (notes or [])[:12]],
             "run_id": run_id, "retryable": retryable,
             "excluded_sources": list(excluded_sources or [])[:40]}
    row = connection.execute(
        """
        UPDATE source_registry_catalog_item
        SET coverage_source_metadata = jsonb_set(COALESCE(coverage_source_metadata, '{}'::jsonb),
            '{collection_preparation}', %(state)s::jsonb)
        WHERE catalog_item_id = %(catalog_item_id)s AND country_code = %(country_code)s
          AND coverage_source_metadata #>> '{collection_preparation,operation_id}' = %(operation_id)s
        RETURNING catalog_item_id
        """,
        {"catalog_item_id": group["catalog_item_id"], "country_code": group["country_code"],
         "operation_id": plan["collection_id"], "state": json.dumps(state)},
    ).fetchone()
    return row is not None


def claim_preparation(connection: Any, *, group: dict[str, Any], plan: dict[str, Any]) -> bool:
    row = connection.execute(
        """SELECT sci.*, b.homepage_url, b.source_language FROM source_registry_catalog_item sci
        JOIN bank b USING (country_code, bank_code)
        WHERE sci.catalog_item_id = %(catalog_item_id)s AND sci.country_code = %(country_code)s
        FOR UPDATE OF sci""",
        {"catalog_item_id": group["catalog_item_id"], "country_code": group["country_code"]},
    ).fetchone()
    if not row or preparation_state(row).get("operation_id") != plan["collection_id"]:
        return False
    if row["status"] != "active" or preparation_signature(row) != preparation_signature(group):
        update_preparation(connection, group=group, plan=plan, status="skipped",
                           reasons=["coverage_changed"], retryable=True)
        return False
    return update_preparation(connection, group=group, plan=plan, status="checking")


def probe_sources(rows: list[dict[str, Any]], *, policy: Any,
                  cache: dict[str, dict[str, Any]] | None = None) -> tuple[list[str], list[dict[str, Any]]]:
    # Reuse the worker's safe-fetch policy; an official link never expands the allowlist.
    from worker.discovery.fpds_discovery.fetch import fetch_response
    cache = cache if cache is not None else {}
    policy = replace(policy, timeout_seconds=min(policy.timeout_seconds, 20),
                     browser_fallback_timeout_seconds=min(policy.browser_fallback_timeout_seconds, 45))
    available, excluded = [], []
    for row in rows:
        url = str(row.get("source_url") or row.get("normalized_url") or "")
        key = json.dumps([url, row.get("source_type"), sorted(policy.allowed_domains)])
        result = cache.get(key)
        if result is None:
            try:
                response = fetch_response(url, policy, browser_fallback_format="pdf" if row.get("source_type") == "pdf" else "html")
                content_type = response.content_type.lower()
                if row.get("source_type") == "pdf":
                    if not response.body.startswith(b"%PDF-"):
                        raise ValueError("PDF source returned non-PDF content after bounded fetch recovery")
                elif not content_type.startswith(("text/html", "application/xhtml+xml")):
                    raise ValueError("Text fetch expected HTML content but received " + content_type)
                result = {"reason_code": None}
            except Exception as exc:
                reason = source_block_reason({"source_type": row.get("source_type"), "latest_stage_status": "failed", "latest_error_summary": str(exc)})
                result = {"reason_code": reason or "source_temporarily_unavailable", "retryable": reason is None,
                          "detail": str(exc)[:500]}
            if result.get("reason_code") and not result.get("retryable"):
                cache[key] = result
        if result.get("reason_code"):
            excluded.append({"source_id": row["source_id"], **result})
        else:
            available.append(str(row["source_id"]))
    return available, excluded
