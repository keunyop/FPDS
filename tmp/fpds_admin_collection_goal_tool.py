from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
API_SERVICE_ROOT = REPO_ROOT / "api" / "service"
if str(API_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api_service.aggregate_refresh import launch_aggregate_refresh_runner, request_manual_aggregate_refresh
from api_service.ai_verification import run_review_ai_verification
from api_service.config import Settings
from api_service.candidate_safety_remediation import retract_invalid_candidates
from api_service.collection_ai_autopilot import (
    load_collection_ai_autopilot_policy,
    remediate_collection_review_task,
)
from api_service.collection_automation import run_collection_automation_cycle
from api_service.db import open_connection
from api_service.public_products import load_public_products, normalize_public_products_query
from api_service.review_detail import load_review_task_detail
from api_service.review_queue import load_review_queue, normalize_review_queue_filters
from api_service.source_catalog import start_source_catalog_collection
from api_service.source_catalog import _deactivate_rejected_generated_detail_sources
from api_service.source_catalog import _url_country_scope_conflicts
from api_service.source_collection_runner import _supersede_stale_logical_reviews_for_run
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_normalization.supporting_merge import _extract_current_gic_rate_values

GOLDEN_PATH = REPO_ROOT / "worker" / "pipeline" / "tests" / "fixtures" / "golden" / "canada_big5_deposit_products_golden_2026-05-23.json"
COMPARE_FIELDS = (
    "bank_name",
    "product_name",
    "highest_rate",
    "base_12_month_rate",
    "tags",
    "product_page_url",
    "signup_amount",
    "eligibility",
    "application_method",
    "post_maturity_interest_rate",
    "tax_benefits",
    "deposit_insurance",
    "term_rates",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS admin collection audit and recollection helper.")
    parser.add_argument("--env-file", default=".env.dev")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("state")
    subparsers.add_parser("apply-country-market-profiles")
    subparsers.add_parser("apply-publication-automation")
    subparsers.add_parser("apply-us-pricing-evidence")
    subparsers.add_parser("apply-us-pricing-scope-cleanup")
    subparsers.add_parser("apply-us-cross-product-support-cleanup")
    subparsers.add_parser("apply-us-card-apr-contract")
    subparsers.add_parser("automation-cycle")
    targeted_review_parser = subparsers.add_parser("review-ai-remediate")
    targeted_review_parser.add_argument("--review-task-id", action="append", required=True)
    targeted_review_parser.add_argument("--force-new-verification", action="store_true")
    model_execution_parser = subparsers.add_parser("model-execution")
    model_execution_parser.add_argument("--model-execution-id", required=True)
    cross_country_parser = subparsers.add_parser("cross-country-source-audit")
    cross_country_parser.add_argument("--country-code", required=True)
    cross_country_parser.add_argument("--execute", action="store_true")
    public_audit_parser = subparsers.add_parser("public-audit")
    public_audit_parser.add_argument("--product-id", action="append", default=[])
    essential_audit_parser = subparsers.add_parser("essential-audit")
    essential_audit_parser.add_argument("--brief", action="store_true")
    readiness_parser = subparsers.add_parser("candidate-readiness-audit")
    readiness_parser.add_argument("--country-code", action="append", default=[])
    readiness_parser.add_argument("--brief", action="store_true")
    aggregate_audit_parser = subparsers.add_parser("aggregate-audit")
    aggregate_audit_parser.add_argument("--snapshot-id", required=True)
    aggregate_audit_parser.add_argument("--product-id", action="append", default=[])
    remediate_parser = subparsers.add_parser("remediate")
    remediate_parser.add_argument("--candidate-id", action="append", required=True)
    remediate_parser.add_argument("--reason-code", required=True)
    remediate_parser.add_argument("--reason-text", required=True)
    deactivate_parser = subparsers.add_parser("deactivate-generated-detail")
    deactivate_parser.add_argument("--bank-code", required=True)
    deactivate_parser.add_argument("--product-type", required=True)
    deactivate_parser.add_argument("--url", action="append", required=True)
    supersede_parser = subparsers.add_parser("supersede-stale")
    supersede_parser.add_argument("--run-id", action="append", required=True)
    gic_check_parser = subparsers.add_parser("gic-evidence-check")
    gic_check_parser.add_argument("--review-task-id", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--collection-id", action="append", default=[])
    audit_parser.add_argument("--brief", action="store_true")
    collection_summary_parser = subparsers.add_parser("collection-summary")
    collection_summary_parser.add_argument("--collection-id", required=True)
    collection_summary_parser.add_argument("--brief", action="store_true")
    collection_summary_parser.add_argument("--bank-code", action="append", default=[])
    collection_summary_parser.add_argument("--product-type", action="append", default=[])
    collection_summary_parser.add_argument("--candidate-state", action="append", default=[])
    run_activity_parser = subparsers.add_parser("run-activity")
    run_activity_parser.add_argument("--run-id", required=True)
    source_search_parser = subparsers.add_parser("source-search")
    source_search_parser.add_argument("--source-document-id", required=True)
    source_search_parser.add_argument("--term", action="append", required=True)
    candidate_evidence_parser = subparsers.add_parser("candidate-evidence")
    candidate_evidence_parser.add_argument("--candidate-id", required=True)
    candidate_evidence_parser.add_argument("--field-name", action="append", default=[])
    public_api_parser = subparsers.add_parser("public-api-check")
    public_api_parser.add_argument("--country-code", action="append", default=[])
    public_api_parser.add_argument("--product-id", action="append", default=[])
    public_refresh_parser = subparsers.add_parser("refresh-public")
    public_refresh_parser.add_argument("--country-code", required=True)
    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--review-task-id", required=True)
    review_parser.add_argument("--section", choices=("all", "candidate", "candidate-summary", "evidence", "source"), default="all")
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--country-code")
    launch_parser.add_argument("--only-bank", action="append", default=[])
    launch_parser.add_argument("--only-product-type", action="append", default=[])
    launch_parser.add_argument("--scope", action="append", default=[], help="Exact BANK:product-type scope; repeatable.")
    launch_parser.add_argument("--precision-rediscovery", action="store_true")

    poll_parser = subparsers.add_parser("poll")
    poll_parser.add_argument("--collection-id", required=True)
    poll_parser.add_argument("--brief", action="store_true")

    wait_parser = subparsers.add_parser("wait")
    wait_parser.add_argument("--collection-id", required=True)
    wait_parser.add_argument("--timeout-seconds", type=int, default=60)
    wait_parser.add_argument("--poll-seconds", type=int, default=10)
    wait_parser.add_argument("--brief", action="store_true")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--collection-id", required=True)
    compare_parser.add_argument("--report-path")

    args = parser.parse_args()
    settings = Settings.from_env(args.env_file)

    if args.command == "state":
        _print_json(load_state(settings))
        return 0
    if args.command == "apply-country-market-profiles":
        migration_path = REPO_ROOT / "db" / "migrations" / "0034_country_product_market_profiles.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT
                    product_type,
                    discovery_role,
                    status,
                    count(*) AS source_count,
                    count(*) FILTER (
                        WHERE discovery_metadata ->> 'market_profile_version' = '2026-08-09'
                    ) AS profiled_count
                FROM source_registry_item
                WHERE country_code = 'US'
                GROUP BY product_type, discovery_role, status
                ORDER BY product_type, discovery_role, status
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "us_source_registry": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "apply-publication-automation":
        migration_path = REPO_ROOT / "db" / "migrations" / "0035_collection_publication_automation.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT policy_key, version_no, policy_value, active_flag
                FROM processing_policy_config
                WHERE policy_key LIKE 'COLLECTION_AUTOMATION_%'
                ORDER BY policy_key, version_no DESC
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "policies": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "apply-us-pricing-evidence":
        migration_path = REPO_ROOT / "db" / "migrations" / "0036_us_pricing_evidence_companions.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT
                    product_type,
                    count(*) AS active_source_count,
                    count(*) FILTER (
                        WHERE expected_fields ? 'purchase_interest_rate_summary'
                    ) AS purchase_apr_summary_source_count,
                    count(*) FILTER (
                        WHERE discovery_metadata ->> 'market_profile_version' = '2026-08-12-v2'
                    ) AS current_profile_count
                FROM source_registry_item
                WHERE country_code = 'US'
                  AND status = 'active'
                  AND product_type = 'credit-card'
                GROUP BY product_type
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "us_credit_card_source_registry": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "apply-us-pricing-scope-cleanup":
        migration_path = REPO_ROOT / "db" / "migrations" / "0037_us_pricing_companion_scope_cleanup.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT source_id, status, change_reason
                FROM source_registry_item
                WHERE country_code = 'US'
                  AND change_reason = 'excluded_generic_service_agreement_companion_2026_08_12'
                ORDER BY source_id
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "inactivated_sources": [dict(row) for row in rows],
            }
        )
        return 0
    if args.command == "apply-us-cross-product-support-cleanup":
        migration_path = REPO_ROOT / "db" / "migrations" / "0038_us_cross_product_support_cleanup.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT source_id, product_type, status, change_reason
                FROM source_registry_item
                WHERE country_code = 'US'
                  AND change_reason = 'excluded_cross_product_support_2026_08_12'
                ORDER BY source_id
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "inactivated_sources": [dict(row) for row in rows],
            }
        )
        return 0
    if args.command == "apply-us-card-apr-contract":
        migration_path = REPO_ROOT / "db" / "migrations" / "0039_us_credit_card_apr_range_contract.sql"
        with open_connection(settings) as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"))
            rows = connection.execute(
                """
                SELECT
                    count(*) AS active_source_count,
                    count(*) FILTER (
                        WHERE expected_fields ? 'purchase_interest_rate_summary'
                    ) AS purchase_apr_summary_source_count,
                    count(*) FILTER (
                        WHERE discovery_metadata ->> 'market_profile_version' = '2026-08-12-v2'
                    ) AS current_profile_count
                FROM source_registry_item
                WHERE country_code = 'US'
                  AND status = 'active'
                  AND product_type = 'credit-card'
                """
            ).fetchall()
        _print_json(
            {
                "migration": migration_path.name,
                "applied": True,
                "us_credit_card_source_registry": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "automation-cycle":
        with open_connection(settings) as connection:
            result = run_collection_automation_cycle(connection)
        _print_json(result)
        return 0
    if args.command == "review-ai-remediate":
        outcomes = []
        approved = False
        with open_connection(settings) as connection:
            policy = load_collection_ai_autopilot_policy(connection)
            for review_task_id in args.review_task_id:
                if args.force_new_verification:
                    detail = load_review_task_detail(
                        connection,
                        review_task_id=review_task_id,
                        actor_role="admin",
                    )
                    if detail:
                        run_review_ai_verification(
                            connection,
                            detail=detail,
                            actor={
                                "actor_type": "system",
                                "role": "admin",
                                "display_name": "FPDS targeted collection remediation",
                            },
                            request_context={
                                "request_id": f"forced-review-ai-{review_task_id}",
                                "ip_address": None,
                                "user_agent": "fpds-admin-collection-goal-tool",
                            },
                        )
                        connection.commit()
                result = remediate_collection_review_task(
                    connection,
                    review_task_id=review_task_id,
                    approval_threshold=float(policy["approval_threshold"]),
                    request_context={
                        "request_id": f"targeted-review-ai-{review_task_id}",
                        "ip_address": None,
                        "user_agent": "fpds-admin-collection-goal-tool",
                    },
                )
                connection.commit()
                outcomes.append(result)
                approved = approved or bool(result.get("approved"))
        aggregate_launch = launch_aggregate_refresh_runner() if approved else None
        _print_json(
            {
                "policy": policy,
                "outcomes": outcomes,
                "aggregate_refresh_launch": aggregate_launch,
            }
        )
        return 0
    if args.command == "model-execution":
        with open_connection(settings) as connection:
            row = connection.execute(
                """
                SELECT
                    model_execution_id,
                    run_id,
                    source_document_id,
                    stage_name,
                    agent_name,
                    model_id,
                    execution_status,
                    execution_metadata,
                    started_at,
                    completed_at
                FROM model_execution
                WHERE model_execution_id = %(model_execution_id)s
                """,
                {"model_execution_id": args.model_execution_id},
            ).fetchone()
        _print_json(_json_safe_row(row) if row else None)
        return 0
    if args.command == "cross-country-source-audit":
        country_code = str(args.country_code).strip().upper()
        with open_connection(settings) as connection:
            rows = connection.execute(
                """
                SELECT source_id, bank_code, product_type, discovery_role, normalized_url
                FROM source_registry_item
                WHERE country_code = %(country_code)s
                  AND status = 'active'
                ORDER BY bank_code, product_type, source_id
                """,
                {"country_code": country_code},
            ).fetchall()
            conflicts = [
                _json_safe_row(row)
                for row in rows
                if _url_country_scope_conflicts(
                    country_code=country_code,
                    normalized_url=str(row.get("normalized_url") or ""),
                )
            ]
            updated_count = 0
            if args.execute and conflicts:
                source_ids = [str(row["source_id"]) for row in conflicts]
                result = connection.execute(
                    """
                    UPDATE source_registry_item
                    SET
                        status = 'inactive',
                        change_reason = 'other_country_market_route',
                        updated_at = now()
                    WHERE country_code = %(country_code)s
                      AND status = 'active'
                      AND source_id = ANY(%(source_ids)s::text[])
                    """,
                    {"country_code": country_code, "source_ids": source_ids},
                )
                updated_count = max(0, int(result.rowcount or 0))
        _print_json(
            {
                "country_code": country_code,
                "execute": bool(args.execute),
                "conflict_count": len(conflicts),
                "updated_count": updated_count,
                "conflicts": conflicts,
            }
        )
        return 0
    if args.command == "public-audit":
        _print_json(load_public_safety_audit(settings, product_ids=args.product_id))
        return 0
    if args.command == "essential-audit":
        audit = load_essential_public_audit(settings)
        _print_json(_brief_essential_public_audit(audit) if args.brief else audit)
        return 0
    if args.command == "candidate-readiness-audit":
        audit = load_candidate_readiness_audit(
            settings,
            country_codes=args.country_code,
        )
        _print_json(_brief_candidate_readiness_audit(audit) if args.brief else audit)
        return 0
    if args.command == "aggregate-audit":
        _print_json(
            load_aggregate_audit(
                settings,
                snapshot_id=args.snapshot_id,
                product_ids=args.product_id,
            )
        )
        return 0
    if args.command == "remediate":
        with open_connection(settings) as connection:
            result = retract_invalid_candidates(
                connection,
                candidate_ids=args.candidate_id,
                reason_code=args.reason_code,
                reason_text=args.reason_text,
                actor={"actor_type": "system", "role": "admin", "display_name": "FPDS accuracy remediation"},
                request_context={
                    "request_id": f"accuracy-remediation-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    "user_agent": "fpds-admin-collection-goal-tool",
                },
            )
        _print_json(result)
        return 0
    if args.command == "deactivate-generated-detail":
        with open_connection(settings) as connection:
            count = _deactivate_rejected_generated_detail_sources(
                connection,
                bank_code=args.bank_code,
                product_type=args.product_type,
                normalized_urls=args.url,
            )
        _print_json({"deactivated_count": count, "urls": args.url})
        return 0
    if args.command == "supersede-stale":
        request_id = f"stale-review-supersession-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        counts = {
            run_id: _supersede_stale_logical_reviews_for_run(
                run_id=run_id,
                plan={"request_id": request_id},
            )
            for run_id in args.run_id
        }
        _print_json(
            {
                "request_id": request_id,
                "superseded_by_run": counts,
                "superseded_count": sum(counts.values()),
            }
        )
        return 0
    if args.command == "gic-evidence-check":
        with open_connection(settings) as connection:
            detail = load_review_task_detail(connection, review_task_id=args.review_task_id, actor_role="admin")
        results = []
        for link in (detail or {}).get("evidence_links", []):
            values = _extract_current_gic_rate_values(str(link.get("evidence_text_excerpt") or ""))
            if values:
                results.append(values)
        _print_json({"review_task_id": args.review_task_id, "parsed_tables": results})
        return 0
    if args.command == "audit":
        audit = load_accuracy_audit(settings, collection_ids=args.collection_id)
        _print_json(_brief_accuracy_audit(audit) if args.brief else audit)
        return 0
    if args.command == "collection-summary":
        summary = load_collection_outcome_summary(settings, collection_id=args.collection_id)
        bank_codes = {item.strip().upper() for item in args.bank_code if item.strip()}
        product_types = {item.strip().lower() for item in args.product_type if item.strip()}
        candidate_states = {item.strip().lower() for item in args.candidate_state if item.strip()}
        if bank_codes or product_types or candidate_states:
            selected = [
                item
                for item in summary["candidates"]
                if (not bank_codes or str(item["bank_code"]).upper() in bank_codes)
                and (not product_types or str(item["product_type"]).lower() in product_types)
                and (not candidate_states or str(item["candidate_state"]).lower() in candidate_states)
            ]
            summary = {
                **summary,
                "selected_candidate_count": len(selected),
                "candidates": selected,
            }
        _print_json(_brief_collection_outcome_summary(summary) if args.brief else summary)
        return 0
    if args.command == "run-activity":
        _print_json(load_run_activity(settings, run_id=args.run_id))
        return 0
    if args.command == "source-search":
        with open_connection(settings) as connection:
            rows = connection.execute(
                """
                SELECT
                    ec.evidence_chunk_id,
                    ec.anchor_type,
                    ec.anchor_value,
                    ec.page_no,
                    ec.chunk_index,
                    ec.evidence_excerpt
                FROM evidence_chunk AS ec
                JOIN parsed_document AS pd
                  ON pd.parsed_document_id = ec.parsed_document_id
                JOIN source_snapshot AS ss
                  ON ss.snapshot_id = pd.snapshot_id
                WHERE ss.source_document_id = %(source_document_id)s
                  AND lower(ec.evidence_excerpt) LIKE ANY(%(patterns)s::text[])
                ORDER BY ec.chunk_index
                LIMIT 30
                """,
                {
                    "source_document_id": args.source_document_id,
                    "patterns": [f"%{term.strip().lower()}%" for term in args.term if term.strip()],
                },
            ).fetchall()
        _print_json(
            {
                "source_document_id": args.source_document_id,
                "terms": args.term,
                "matches": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "candidate-evidence":
        field_names = [item.strip() for item in args.field_name if item.strip()]
        with open_connection(settings) as connection:
            rows = connection.execute(
                """
                SELECT
                    fel.field_name,
                    fel.candidate_value,
                    fel.citation_confidence,
                    fel.evidence_chunk_id,
                    fel.source_document_id,
                    ec.anchor_type,
                    ec.anchor_value,
                    ec.page_no,
                    ec.chunk_index,
                    ec.evidence_excerpt,
                    sd.normalized_source_url AS source_url,
                    sd.source_type
                FROM field_evidence_link AS fel
                JOIN evidence_chunk AS ec
                  ON ec.evidence_chunk_id = fel.evidence_chunk_id
                JOIN source_document AS sd
                  ON sd.source_document_id = fel.source_document_id
                WHERE fel.candidate_id = %(candidate_id)s
                  AND (
                    cardinality(%(field_names)s::text[]) = 0
                    OR fel.field_name = ANY(%(field_names)s::text[])
                  )
                ORDER BY fel.field_name, ec.chunk_index
                """,
                {"candidate_id": args.candidate_id, "field_names": field_names},
            ).fetchall()
            candidate_row = connection.execute(
                """
                SELECT field_mapping_metadata
                FROM normalized_candidate
                WHERE candidate_id = %(candidate_id)s
                """,
                {"candidate_id": args.candidate_id},
            ).fetchone()
        mapping_metadata = dict(candidate_row["field_mapping_metadata"] or {}) if candidate_row else {}
        if field_names:
            mapping_metadata = {
                field_name: mapping_metadata[field_name]
                for field_name in field_names
                if field_name in mapping_metadata
            }
        _print_json(
            {
                "candidate_id": args.candidate_id,
                "field_names": field_names,
                "field_mapping_metadata": mapping_metadata,
                "evidence": [_json_safe_row(row) for row in rows],
            }
        )
        return 0
    if args.command == "public-api-check":
        _print_json(
            load_public_api_check(
                settings,
                country_codes=args.country_code,
                product_ids=args.product_id,
            )
        )
        return 0
    if args.command == "refresh-public":
        with open_connection(settings) as connection:
            request = request_manual_aggregate_refresh(
                connection,
                actor={
                    "actor_type": "system",
                    "role": "admin",
                    "display_name": "FPDS country-profile refresh",
                },
                request_context={
                    "request_id": f"req_codex_public_refresh_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    "user_agent": "codex-admin-collection-goal-tool",
                },
                country_code=args.country_code,
            )
        _print_json({"request": request, "launch": launch_aggregate_refresh_runner()})
        return 0
    if args.command == "review":
        with open_connection(settings) as connection:
            detail = load_review_task_detail(
                connection,
                review_task_id=args.review_task_id,
                actor_role="admin",
            )
        if not detail:
            raise RuntimeError(f"Review task not found: {args.review_task_id}")
        if args.section == "candidate-summary":
            detail = {
                "review_task": detail["review_task"],
                "candidate": {
                    key: detail["candidate"][key]
                    for key in (
                        "source_document_id", "bank_code", "bank_name", "product_family", "product_type",
                        "subtype_code", "product_name", "candidate_state", "validation_status",
                        "validation_issue_codes", "source_confidence", "review_reason_code", "candidate_payload",
                    )
                },
                "review_diagnosis": detail["review_diagnosis"],
                "source_context": detail["source_context"],
            }
        elif args.section == "candidate":
            detail = {
                "review_task": detail["review_task"],
                "candidate": detail["candidate"],
                "review_diagnosis": detail["review_diagnosis"],
                "source_context": detail["source_context"],
            }
        elif args.section == "evidence":
            detail = {
                "review_task": detail["review_task"],
                "evidence_summary": detail["evidence_summary"],
                "evidence_links": detail["evidence_links"],
            }
        elif args.section == "source":
            detail = {
                "review_task": detail["review_task"],
                "source_context": detail["source_context"],
                "model_executions": detail["model_executions"],
            }
        _print_json(detail)
        return 0
    if args.command == "launch":
        _print_json(
            launch_collection(
                settings,
                only_banks=args.only_bank,
                only_product_types=args.only_product_type,
                exact_scopes=args.scope,
                country_code=args.country_code,
                precision_rediscovery=args.precision_rediscovery,
            )
        )
        return 0
    if args.command == "poll":
        _print_json(_brief_status(load_collection_status(settings, collection_id=args.collection_id), brief=args.brief))
        return 0
    if args.command == "wait":
        _print_json(_brief_status(wait_for_collection(settings, collection_id=args.collection_id, timeout_seconds=args.timeout_seconds, poll_seconds=args.poll_seconds), brief=args.brief))
        return 0
    if args.command == "compare":
        result = compare_collection(settings, collection_id=args.collection_id)
        if args.report_path:
            report_path = Path(args.report_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
        _print_json(result)
        return 0
    raise AssertionError(args.command)


def load_state(settings: Settings) -> dict[str, Any]:
    with open_connection(settings) as connection:
        return {
            "registered": _registered_scope(connection),
            "artifact_counts": _artifact_counts(connection),
            "latest_collections": _latest_collections(connection),
        }


def load_public_safety_audit(settings: Settings, *, product_ids: list[str]) -> dict[str, Any]:
    with open_connection(settings) as connection:
        params = {"product_ids": product_ids}
        rows = connection.execute(
            """
            SELECT
                cp.product_id,
                cp.bank_code,
                cp.product_type,
                cp.product_name,
                cp.status,
                cp.current_version_no,
                pv.product_version_id,
                pv.approved_candidate_id,
                nc.candidate_state,
                sd.normalized_source_url,
                cp.current_snapshot_payload
            FROM canonical_product AS cp
            JOIN product_version AS pv
              ON pv.product_id = cp.product_id
             AND pv.version_no = cp.current_version_no
            LEFT JOIN normalized_candidate AS nc
              ON nc.candidate_id = pv.approved_candidate_id
            LEFT JOIN source_document AS sd
              ON sd.source_document_id = nc.source_document_id
            WHERE cp.status = 'active'
              AND (cardinality(%(product_ids)s::text[]) = 0 OR cp.product_id = ANY(%(product_ids)s))
            ORDER BY cp.bank_code, cp.product_type, cp.product_name, cp.product_id
            """,
            params,
        ).fetchall()
        products = [_json_safe_row(row) for row in rows]
        duplicate_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
        for product in products:
            key = (
                str(product["bank_code"]),
                str(product["product_type"]),
                " ".join(str(product["product_name"]).casefold().split()),
                str(product.get("normalized_source_url") or "").rstrip("/"),
            )
            duplicate_groups.setdefault(key, []).append(product)
        duplicates = [group for group in duplicate_groups.values() if len(group) > 1]
        numeric_fields = (
            "standard_rate", "public_display_rate", "base_12_month_rate", "promotional_rate",
            "annual_fee", "monthly_fee", "public_display_fee", "minimum_balance", "minimum_deposit",
            "interest_rate", "mortgage_rate", "purchase_interest_rate", "cash_advance_rate", "balance_transfer_rate",
        )
        violations: list[dict[str, Any]] = []
        for product in products:
            payload = dict(product.get("current_snapshot_payload") or {})
            for field_name in numeric_fields:
                value = payload.get(field_name)
                if value is None or isinstance(value, (int, float)) and not isinstance(value, bool):
                    continue
                violations.append(
                    {
                        "product_id": product["product_id"],
                        "approved_candidate_id": product["approved_candidate_id"],
                        "bank_code": product["bank_code"],
                        "product_type": product["product_type"],
                        "product_name": product["product_name"],
                        "field_name": field_name,
                        "value": value,
                    }
                )
        return {
            "active_product_count": len(products),
            "products": products if product_ids else [],
            "duplicate_groups": duplicates,
            "numeric_type_violation_count": len(violations),
            "numeric_type_violation_product_count": len({item["product_id"] for item in violations}),
            "numeric_type_violations": violations,
        }


def load_essential_public_audit(settings: Settings) -> dict[str, Any]:
    """Compare active canonical and latest Public rows with the essential contract."""

    with open_connection(settings) as connection:
        canonical_rows = connection.execute(
            """
            SELECT
                cp.product_id,
                cp.bank_code,
                cp.country_code,
                cp.product_family,
                cp.product_type,
                cp.product_name,
                cp.status,
                COALESCE(NULLIF(pv.normalized_payload, '{}'::jsonb), cp.current_snapshot_payload, '{}'::jsonb)
                    AS canonical_payload
            FROM canonical_product AS cp
            LEFT JOIN product_version AS pv
              ON pv.product_id = cp.product_id
             AND pv.version_no = cp.current_version_no
            WHERE cp.status = 'active'
              AND (
                    cp.product_family = 'deposit'
                    OR cp.product_type IN ('credit-card', 'mortgage', 'personal-loan', 'line-of-credit')
                  )
            ORDER BY cp.country_code, cp.bank_code, cp.product_type, cp.product_name, cp.product_id
            """
        ).fetchall()
        public_rows = connection.execute(
            """
            WITH latest AS (
                SELECT DISTINCT ON (country_code)
                    country_code,
                    snapshot_id,
                    refreshed_at,
                    refresh_metadata
                FROM aggregate_refresh_run
                WHERE refresh_status = 'completed'
                ORDER BY country_code, refreshed_at DESC NULLS LAST, attempted_at DESC
            )
            SELECT
                latest.country_code,
                latest.snapshot_id,
                latest.refreshed_at,
                latest.refresh_metadata,
                ppp.product_id,
                ppp.bank_code,
                ppp.product_type,
                ppp.product_name,
                ppp.status
            FROM latest
            LEFT JOIN public_product_projection AS ppp
              ON ppp.snapshot_id = latest.snapshot_id
            ORDER BY latest.country_code, ppp.bank_code, ppp.product_type, ppp.product_name, ppp.product_id
            """
        ).fetchall()
        catalog_rows = _active_catalog_rows(connection)

    canonical_assessments = []
    for row in canonical_rows:
        payload = dict(row["canonical_payload"] or {})
        quality = comparison_quality(
            product_type=str(row["product_type"]),
            country_code=str(row["country_code"]),
            expected_fields=(),
            candidate_payload=payload,
        )
        anomalies = _essential_value_anomalies(payload, fields=quality.satisfied_fields)
        canonical_assessments.append(
            {
                "product_id": str(row["product_id"]),
                "bank_code": str(row["bank_code"]),
                "country_code": str(row["country_code"]),
                "product_type": str(row["product_type"]),
                "product_name": str(row["product_name"]),
                "complete": bool(quality.contract_defined and quality.complete and not anomalies),
                "essential_values": {
                    field_name: payload.get(field_name)
                    for field_name in quality.satisfied_fields
                },
                "missing_fields": list(quality.missing_fields),
                "anomalies": anomalies,
            }
        )

    public_product_ids = {
        str(row["product_id"])
        for row in public_rows
        if row.get("product_id") and str(row.get("status")) == "active"
    }
    public_assessments = [
        {**item, "visible_in_latest_public": item["product_id"] in public_product_ids}
        for item in canonical_assessments
        if item["product_id"] in public_product_ids
    ]
    affected_scopes = sorted(
        {
            (item["bank_code"], item["product_type"])
            for item in public_assessments
            if not item["complete"]
        }
    )
    active_catalog_scopes = {
        (str(row["bank_code"]), str(row["product_type"]))
        for row in catalog_rows
    }
    return {
        "latest_public_snapshots": [
            {
                "country_code": str(row["country_code"]),
                "snapshot_id": str(row["snapshot_id"]),
                "refreshed_at": row["refreshed_at"],
                "refresh_metadata": row["refresh_metadata"],
            }
            for row in public_rows
            if not row.get("product_id")
            or not any(
                prior["country_code"] == row["country_code"]
                for prior in public_rows[: public_rows.index(row)]
            )
        ],
        "canonical": _quality_summary(canonical_assessments),
        "public": _quality_summary(public_assessments),
        "public_products": public_assessments,
        "incomplete_public_products": [item for item in public_assessments if not item["complete"]],
        "affected_scopes": [
            {
                "bank_code": bank_code,
                "product_type": product_type,
                "active_collection_route": (bank_code, product_type) in active_catalog_scopes,
            }
            for bank_code, product_type in affected_scopes
        ],
    }


def load_candidate_readiness_audit(
    settings: Settings,
    *,
    country_codes: list[str],
) -> dict[str, Any]:
    """Summarize active candidate blockers under the current market profile."""

    normalized_countries = sorted(
        {
            str(country_code).strip().upper()
            for country_code in country_codes
            if str(country_code).strip()
        }
    )
    country_filter = "AND nc.country_code = ANY(%(country_codes)s::text[])" if normalized_countries else ""
    with open_connection(settings) as connection:
        rows = connection.execute(
            f"""
            SELECT
                nc.candidate_id,
                nc.run_id,
                nc.country_code,
                nc.bank_code,
                nc.product_type,
                nc.product_name,
                nc.candidate_state,
                nc.validation_status,
                nc.validation_issue_codes,
                nc.candidate_payload,
                sd.source_metadata,
                active_review.review_task_id,
                active_review.review_state,
                active_review.queue_reason_code,
                verification.model_execution_id,
                verification.execution_status AS verification_status,
                verification.execution_metadata -> 'auto_approval_assessment' AS auto_approval_assessment
            FROM normalized_candidate AS nc
            JOIN source_document AS sd
              ON sd.source_document_id = nc.source_document_id
            LEFT JOIN LATERAL (
                SELECT rt.review_task_id, rt.review_state, rt.queue_reason_code
                FROM review_task AS rt
                WHERE rt.candidate_id = nc.candidate_id
                  AND rt.review_state IN ('queued', 'deferred')
                ORDER BY rt.created_at DESC, rt.review_task_id DESC
                LIMIT 1
            ) AS active_review ON true
            LEFT JOIN LATERAL (
                SELECT me.model_execution_id, me.execution_status, me.execution_metadata
                FROM model_execution AS me
                WHERE me.stage_name = 'ai_verification'
                  AND me.execution_metadata ->> 'review_task_id' = active_review.review_task_id
                  AND me.execution_metadata ->> 'verification_contract_version' = 'review-ai-verification-v17'
                ORDER BY me.started_at DESC, me.model_execution_id DESC
                LIMIT 1
            ) AS verification ON true
            WHERE nc.candidate_state IN ('auto_validated', 'in_review')
              {country_filter}
            ORDER BY nc.country_code, nc.bank_code, nc.product_type, nc.product_name, nc.candidate_id
            """,
            {"country_codes": normalized_countries},
        ).fetchall()
        canonical_rows = connection.execute(
            """
            SELECT country_code, product_type, status, COUNT(*) AS product_count
            FROM canonical_product
            WHERE (%(country_codes)s::text[] IS NULL OR country_code = ANY(%(country_codes)s::text[]))
            GROUP BY country_code, product_type, status
            ORDER BY country_code, product_type, status
            """,
            {"country_codes": normalized_countries or None},
        ).fetchall()
        active_canonical_rows = connection.execute(
            """
            SELECT
                cp.product_id,
                cp.country_code,
                cp.bank_code,
                cp.product_type,
                cp.product_name,
                COALESCE(NULLIF(pv.normalized_payload, '{}'::jsonb), cp.current_snapshot_payload, '{}'::jsonb)
                    AS canonical_payload
            FROM canonical_product AS cp
            LEFT JOIN product_version AS pv
              ON pv.product_id = cp.product_id
             AND pv.version_no = cp.current_version_no
            WHERE cp.status = 'active'
              AND (%(country_codes)s::text[] IS NULL OR cp.country_code = ANY(%(country_codes)s::text[]))
            ORDER BY cp.country_code, cp.bank_code, cp.product_type, cp.product_name, cp.product_id
            """,
            {"country_codes": normalized_countries or None},
        ).fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row.get("candidate_payload") or {})
        source_metadata = dict(row.get("source_metadata") or {})
        quality = comparison_quality(
            product_type=str(row.get("product_type") or ""),
            country_code=str(row.get("country_code") or ""),
            expected_fields=_coerce_string_list(source_metadata.get("expected_fields")),
            candidate_payload=payload,
        )
        issue_codes = _coerce_string_list(row.get("validation_issue_codes"))
        hard_blockers = sorted(
            set(issue_codes)
            - {"partial_source_failure", "low_confidence", "required_field_missing"}
        )
        assessment = dict(row.get("auto_approval_assessment") or {})
        items.append(
            {
                "candidate_id": str(row["candidate_id"]),
                "run_id": str(row["run_id"]),
                "country_code": str(row["country_code"]),
                "bank_code": str(row["bank_code"]),
                "product_type": str(row["product_type"]),
                "product_name": str(row["product_name"]),
                "candidate_state": str(row["candidate_state"]),
                "validation_status": str(row["validation_status"]),
                "issue_codes": issue_codes,
                "hard_blockers": hard_blockers,
                "review_task_id": row.get("review_task_id"),
                "review_state": row.get("review_state"),
                "queue_reason_code": row.get("queue_reason_code"),
                "comparison_contract_defined": quality.contract_defined,
                "comparison_complete": quality.complete,
                "satisfied_fields": list(quality.satisfied_fields),
                "missing_fields": list(quality.missing_fields),
                "model_execution_id": row.get("model_execution_id"),
                "verification_status": row.get("verification_status"),
                "auto_approval_eligible": bool(assessment.get("eligible")),
                "auto_approval_blockers": list(assessment.get("blockers") or []),
            }
        )

    group_counts = Counter(
        (
            item["country_code"],
            item["product_type"],
            item["candidate_state"],
            item["queue_reason_code"] or "none",
        )
        for item in items
    )
    missing_counts = Counter(
        (item["country_code"], item["product_type"], missing_field)
        for item in items
        for missing_field in item["missing_fields"]
    )
    hard_blocker_counts = Counter(
        (item["country_code"], item["product_type"], blocker)
        for item in items
        for blocker in item["hard_blockers"]
    )
    canonical_quality_counts: Counter[tuple[str, str, str]] = Counter()
    incomplete_canonical_products: list[dict[str, Any]] = []
    for row in active_canonical_rows:
        quality = comparison_quality(
            product_type=str(row["product_type"]),
            country_code=str(row["country_code"]),
            expected_fields=(),
            candidate_payload=dict(row.get("canonical_payload") or {}),
        )
        complete = bool(quality.contract_defined and quality.complete)
        canonical_quality_counts[
            (
                str(row["country_code"]),
                str(row["product_type"]),
                "complete" if complete else "incomplete",
            )
        ] += 1
        if not complete:
            incomplete_canonical_products.append(
                {
                    "product_id": str(row["product_id"]),
                    "country_code": str(row["country_code"]),
                    "bank_code": str(row["bank_code"]),
                    "product_type": str(row["product_type"]),
                    "product_name": str(row["product_name"]),
                    "missing_fields": list(quality.missing_fields),
                }
            )
    return {
        "country_codes": normalized_countries or ["ALL"],
        "active_candidate_count": len(items),
        "candidate_state_counts": dict(sorted(Counter(item["candidate_state"] for item in items).items())),
        "comparison_complete_count": sum(1 for item in items if item["comparison_complete"]),
        "comparison_incomplete_count": sum(1 for item in items if not item["comparison_complete"]),
        "complete_without_hard_blocker_count": sum(
            1 for item in items if item["comparison_complete"] and not item["hard_blockers"]
        ),
        "current_verification_count": sum(1 for item in items if item["model_execution_id"]),
        "auto_approval_eligible_count": sum(1 for item in items if item["auto_approval_eligible"]),
        "canonical_state_counts": [
            {
                "country_code": str(row["country_code"]),
                "product_type": str(row["product_type"]),
                "status": str(row["status"]),
                "count": int(row["product_count"]),
            }
            for row in canonical_rows
        ],
        "active_canonical_quality_counts": [
            {
                "country_code": key[0],
                "product_type": key[1],
                "quality": key[2],
                "count": count,
            }
            for key, count in sorted(canonical_quality_counts.items())
        ],
        "incomplete_canonical_products": incomplete_canonical_products,
        "groups": [
            {
                "country_code": key[0],
                "product_type": key[1],
                "candidate_state": key[2],
                "queue_reason_code": key[3],
                "count": count,
            }
            for key, count in sorted(group_counts.items())
        ],
        "missing_field_counts": [
            {
                "country_code": key[0],
                "product_type": key[1],
                "field": key[2],
                "count": count,
            }
            for key, count in sorted(missing_counts.items())
        ],
        "hard_blocker_counts": [
            {
                "country_code": key[0],
                "product_type": key[1],
                "issue_code": key[2],
                "count": count,
            }
            for key, count in sorted(hard_blocker_counts.items())
        ],
        "complete_candidates": [
            item for item in items if item["comparison_complete"]
        ],
    }


def _quality_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for item in items:
        key = f"{item['country_code']}:{item['bank_code']}:{item['product_type']}"
        bucket = grouped.setdefault(key, {"total": 0, "complete": 0, "incomplete": 0})
        bucket["total"] += 1
        bucket["complete" if item["complete"] else "incomplete"] += 1
    return {
        "total": len(items),
        "complete": sum(1 for item in items if item["complete"]),
        "incomplete": sum(1 for item in items if not item["complete"]),
        "by_scope": grouped,
    }


def _brief_essential_public_audit(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "latest_public_snapshots": audit["latest_public_snapshots"],
        "canonical": {
            key: audit["canonical"][key]
            for key in ("total", "complete", "incomplete")
        },
        "public": {
            key: audit["public"][key]
            for key in ("total", "complete", "incomplete")
        },
        "incomplete_public_products": audit["incomplete_public_products"],
        "affected_scopes": audit["affected_scopes"],
    }


def _brief_candidate_readiness_audit(audit: dict[str, Any]) -> dict[str, Any]:
    canonical_quality_counts = list(audit["active_canonical_quality_counts"])
    return {
        key: audit[key]
        for key in (
            "country_codes",
            "active_candidate_count",
            "candidate_state_counts",
            "comparison_complete_count",
            "comparison_incomplete_count",
            "complete_without_hard_blocker_count",
            "current_verification_count",
            "auto_approval_eligible_count",
        )
    } | {
        "active_canonical_complete_count": sum(
            int(item["count"])
            for item in canonical_quality_counts
            if item["quality"] == "complete"
        ),
        "active_canonical_incomplete_count": sum(
            int(item["count"])
            for item in canonical_quality_counts
            if item["quality"] == "incomplete"
        ),
        "active_canonical_quality_counts": canonical_quality_counts,
        "missing_field_counts": audit["missing_field_counts"],
        "hard_blocker_counts": audit["hard_blocker_counts"],
    }


def _essential_value_anomalies(payload: dict[str, Any], *, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    anomalies = []
    placeholder_values = {"n/a", "na", "none", "null", "unknown", "unavailable", "not available", "-", "--"}
    for field_name in fields:
        value = payload.get(field_name)
        if isinstance(value, str) and value.strip().casefold() in placeholder_values:
            anomalies.append({"field_name": field_name, "reason": "placeholder_value", "value": value})
            continue
        if field_name in {
            "standard_rate", "base_12_month_rate", "public_display_rate", "highest_rate",
            "mortgage_rate", "interest_rate", "purchase_interest_rate",
        } and isinstance(value, (int, float)) and not isinstance(value, bool) and not 0 <= value <= 100:
            anomalies.append({"field_name": field_name, "reason": "rate_out_of_range", "value": value})
        if field_name in {
            "standard_rate", "base_12_month_rate", "public_display_rate", "highest_rate",
        } and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 10:
            anomalies.append({"field_name": field_name, "reason": "implausible_deposit_rate", "value": value})
        if field_name in {
            "annual_fee", "monthly_fee", "public_display_fee", "minimum_balance", "minimum_deposit",
        } and isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
            anomalies.append({"field_name": field_name, "reason": "negative_money", "value": value})
        if field_name == "term_length_days" and isinstance(value, (int, float)) and value <= 0:
            anomalies.append({"field_name": field_name, "reason": "nonpositive_term", "value": value})
    return anomalies


def load_aggregate_audit(
    settings: Settings,
    *,
    snapshot_id: str,
    product_ids: list[str],
) -> dict[str, Any]:
    with open_connection(settings) as connection:
        refresh = connection.execute(
            """
            SELECT
                snapshot_id,
                refresh_status,
                country_code,
                refresh_scope,
                attempted_at,
                refreshed_at,
                stale_flag,
                error_summary,
                refresh_metadata
            FROM aggregate_refresh_run
            WHERE snapshot_id = %(snapshot_id)s
            """,
            {"snapshot_id": snapshot_id},
        ).fetchone()
        counts = connection.execute(
            """
            SELECT
                COUNT(*) AS projection_count,
                COUNT(*) FILTER (WHERE status = 'active') AS active_projection_count,
                COUNT(*) FILTER (WHERE status <> 'active') AS inactive_projection_count
            FROM public_product_projection
            WHERE snapshot_id = %(snapshot_id)s
            """,
            {"snapshot_id": snapshot_id},
        ).fetchone()
        selected = connection.execute(
            """
            SELECT snapshot_id, product_id, bank_code, product_type, product_name, status
            FROM public_product_projection
            WHERE snapshot_id = %(snapshot_id)s
              AND product_id = ANY(%(product_ids)s)
            ORDER BY product_id
            """,
            {"snapshot_id": snapshot_id, "product_ids": product_ids},
        ).fetchall()
    return {
        "refresh": _json_safe_row(refresh) if refresh else None,
        "projection_counts": _json_safe_row(counts),
        "selected_products": [_json_safe_row(row) for row in selected],
    }


def load_accuracy_audit(settings: Settings, *, collection_ids: list[str]) -> dict[str, Any]:
    with open_connection(settings) as connection:
        queue = load_review_queue(
            connection,
            filters=normalize_review_queue_filters(
                states=("queued", "deferred"),
                bank_code=None,
                product_type=None,
                validation_status=None,
                created_from=None,
                created_to=None,
                search=None,
                sort_by="priority",
                sort_order="desc",
                page=1,
                page_size=200,
            ),
        )
        review_items = []
        for item in queue["items"]:
            detail = load_review_task_detail(
                connection,
                review_task_id=item["review_task_id"],
                actor_role="admin",
            )
            if not detail:
                continue
            evidence_sources_by_field: dict[str, list[str]] = {}
            for evidence in detail["evidence_links"]:
                field_name = str(evidence["field_name"])
                source_url = str(evidence.get("source_url") or "")
                if source_url and source_url not in evidence_sources_by_field.setdefault(field_name, []):
                    evidence_sources_by_field[field_name].append(source_url)
            review_items.append(
                {
                    **item,
                    "candidate_payload": detail["candidate"]["candidate_payload"],
                    "source_context": detail["source_context"],
                    "evidence_sources_by_field": evidence_sources_by_field,
                    "evidence_summary": detail["evidence_summary"],
                }
            )

        selected_collection_ids = [item.strip() for item in collection_ids if item.strip()]
        if not selected_collection_ids:
            selected_collection_ids = [
                str(row["collection_id"])
                for row in _latest_collections(connection)
            ]
        run_rows = connection.execute(
            """
            SELECT
                ir.run_id,
                ir.run_state,
                ir.source_scope_count,
                ir.source_success_count,
                ir.source_failure_count,
                ir.candidate_count,
                ir.review_queued_count,
                ir.partial_completion_flag,
                ir.error_summary,
                ir.run_metadata ->> 'collection_id' AS collection_id,
                ir.run_metadata ->> 'bank_code' AS bank_code,
                ir.run_metadata ->> 'product_type' AS product_type,
                ir.started_at,
                ir.completed_at
            FROM ingestion_run AS ir
            WHERE ir.run_metadata ->> 'collection_id' = ANY(%(collection_ids)s)
            ORDER BY ir.started_at, ir.run_id
            """,
            {"collection_ids": selected_collection_ids},
        ).fetchall()
        run_source_failure_rows = connection.execute(
            """
            SELECT
                ir.run_metadata ->> 'collection_id' AS collection_id,
                rsi.run_id,
                ir.run_metadata ->> 'bank_code' AS bank_code,
                ir.run_metadata ->> 'product_type' AS product_type,
                sd.normalized_source_url,
                COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') AS discovery_role,
                rsi.stage_status,
                rsi.error_summary,
                rsi.stage_metadata
            FROM run_source_item AS rsi
            JOIN ingestion_run AS ir
              ON ir.run_id = rsi.run_id
            JOIN source_document AS sd
              ON sd.source_document_id = rsi.source_document_id
            WHERE ir.run_metadata ->> 'collection_id' = ANY(%(collection_ids)s)
              AND (
                  rsi.error_count > 0
                  OR rsi.error_summary IS NOT NULL
                  OR rsi.stage_status IN ('failed', 'partial')
              )
            ORDER BY ir.started_at, rsi.run_id, sd.normalized_source_url
            """,
            {"collection_ids": selected_collection_ids},
        ).fetchall()
        candidate_rows = connection.execute(
            """
            SELECT
                ir.run_metadata ->> 'collection_id' AS collection_id,
                nc.candidate_id,
                nc.run_id,
                nc.candidate_state,
                nc.validation_status,
                nc.validation_issue_codes,
                nc.source_confidence,
                nc.bank_code,
                nc.product_type,
                nc.product_name,
                nc.candidate_payload,
                sd.normalized_source_url,
                COALESCE(sd.source_metadata ->> 'discovery_role', 'unknown') AS discovery_role
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            JOIN source_document AS sd
              ON sd.source_document_id = nc.source_document_id
            WHERE ir.run_metadata ->> 'collection_id' = ANY(%(collection_ids)s)
            ORDER BY ir.started_at, nc.bank_code, nc.product_type, nc.product_name, nc.candidate_id
            """,
            {"collection_ids": selected_collection_ids},
        ).fetchall()
    return {
        "collection_ids": selected_collection_ids,
        "runs": [_serialize_accuracy_run(row) for row in run_rows],
        "run_source_failures": [_json_safe_row(row) for row in run_source_failure_rows],
        "candidates": [_json_safe_row(row) for row in candidate_rows],
        "active_review_summary": queue["summary"],
        "active_reviews": review_items,
    }


def load_collection_outcome_summary(settings: Settings, *, collection_id: str) -> dict[str, Any]:
    """Summarize only one collection's terminal routing and canonical outcomes."""

    status = load_collection_status(settings, collection_id=collection_id)
    with open_connection(settings) as connection:
        candidate_rows = connection.execute(
            """
            SELECT
                nc.candidate_id,
                nc.run_id,
                nc.country_code,
                nc.bank_code,
                nc.product_type,
                nc.product_name,
                nc.candidate_state,
                nc.validation_status,
                nc.validation_issue_codes,
                nc.review_reason_code,
                nc.candidate_payload,
                rt.review_task_id,
                rt.review_state,
                rt.queue_reason_code,
                cp.product_id AS promoted_product_id,
                cp.status AS promoted_product_status
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            LEFT JOIN review_task AS rt
              ON rt.candidate_id = nc.candidate_id
            LEFT JOIN product_version AS pv
              ON pv.approved_candidate_id = nc.candidate_id
            LEFT JOIN canonical_product AS cp
              ON cp.product_id = pv.product_id
             AND cp.current_version_no = pv.version_no
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
            ORDER BY nc.bank_code, nc.product_type, nc.product_name, nc.candidate_id, rt.created_at
            """,
            {"collection_id": collection_id},
        ).fetchall()

    candidates: dict[str, dict[str, Any]] = {}
    review_reason_counts: Counter[str] = Counter()
    for row in candidate_rows:
        candidate_id = str(row["candidate_id"])
        payload = dict(row["candidate_payload"] or {})
        quality = comparison_quality(
            product_type=str(row["product_type"]),
            country_code=str(row["country_code"]),
            expected_fields=(),
            candidate_payload=payload,
        )
        item = candidates.setdefault(
            candidate_id,
            {
                "candidate_id": candidate_id,
                "run_id": str(row["run_id"]),
                "country_code": str(row["country_code"]),
                "bank_code": str(row["bank_code"]),
                "product_type": str(row["product_type"]),
                "product_name": str(row["product_name"]),
                "candidate_state": str(row["candidate_state"]),
                "validation_status": str(row["validation_status"]),
                "validation_issue_codes": list(row["validation_issue_codes"] or []),
                "review_reason_code": row["review_reason_code"],
                "promoted_product_id": row["promoted_product_id"],
                "promoted_product_status": row["promoted_product_status"],
                "comparison_complete": bool(quality.contract_defined and quality.complete),
                "comparison_satisfied_fields": list(quality.satisfied_fields),
                "comparison_missing_fields": list(quality.missing_fields),
                "payload_fields": sorted(str(key) for key in payload),
                "reviews": [],
            },
        )
        if row["review_task_id"]:
            review = {
                "review_task_id": str(row["review_task_id"]),
                "review_state": str(row["review_state"]),
                "queue_reason_code": str(row["queue_reason_code"]),
            }
            if review not in item["reviews"]:
                item["reviews"].append(review)
                review_reason_counts[str(row["queue_reason_code"])] += 1

    candidate_items = list(candidates.values())
    return {
        "collection_id": collection_id,
        "terminal": status["terminal"],
        "run_count": status["run_count"],
        "run_state_counts": status["state_counts"],
        "failed_or_partial_runs": [
            row
            for row in status["runs"]
            if row["run_state"] != "completed" or row["partial_completion_flag"] or row["error_summary"]
        ],
        "candidate_count": len(candidate_items),
        "candidate_state_counts": dict(sorted(Counter(item["candidate_state"] for item in candidate_items).items())),
        "validation_status_counts": dict(sorted(Counter(item["validation_status"] for item in candidate_items).items())),
        "promoted_candidate_count": sum(1 for item in candidate_items if item["promoted_product_id"]),
        "active_promoted_product_count": len(
            {
                str(item["promoted_product_id"])
                for item in candidate_items
                if item["promoted_product_id"] and item["promoted_product_status"] == "active"
            }
        ),
        "review_task_count": sum(len(item["reviews"]) for item in candidate_items),
        "review_reason_counts": dict(sorted(review_reason_counts.items())),
        "candidates": candidate_items,
    }


def _brief_collection_outcome_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Keep long-running collection checks small and decision-oriented."""

    failed_or_partial_runs = list(summary["failed_or_partial_runs"])
    terminal_problem_runs = [
        row
        for row in failed_or_partial_runs
        if row.get("run_state") != "started"
        or row.get("partial_completion_flag")
        or row.get("error_summary")
    ]
    return {
        key: value
        for key, value in summary.items()
        if key not in {"failed_or_partial_runs", "candidates"}
    } | {
        "non_completed_run_count": sum(
            count
            for state, count in dict(summary["run_state_counts"]).items()
            if state != "completed"
        ),
        "failed_or_partial_run_count": len(terminal_problem_runs),
        "failed_or_partial_runs": [
            {
                key: row.get(key)
                for key in (
                    "run_id",
                    "bank_code",
                    "product_type",
                    "run_state",
                    "partial_completion_flag",
                    "error_summary",
                )
            }
            for row in terminal_problem_runs
        ],
        "candidates": list(summary["candidates"]),
    }


def load_run_activity(settings: Settings, *, run_id: str) -> dict[str, Any]:
    """Expose timestamped stage activity for diagnosing a long-running collection run."""

    with open_connection(settings) as connection:
        run = connection.execute(
            """
            SELECT run_id, run_state, run_metadata, started_at, completed_at, error_summary
            FROM ingestion_run
            WHERE run_id = %(run_id)s
            """,
            {"run_id": run_id},
        ).fetchone()
        source_rows = connection.execute(
            """
            SELECT
                rsi.source_document_id,
                sd.normalized_source_url,
                rsi.stage_status,
                rsi.error_count,
                rsi.error_summary,
                rsi.updated_at
            FROM run_source_item AS rsi
            JOIN source_document AS sd
              ON sd.source_document_id = rsi.source_document_id
            WHERE rsi.run_id = %(run_id)s
            ORDER BY rsi.updated_at DESC, rsi.source_document_id
            """,
            {"run_id": run_id},
        ).fetchall()
        model_rows = connection.execute(
            """
            SELECT
                model_execution_id,
                source_document_id,
                stage_name,
                model_id,
                execution_status,
                started_at,
                completed_at
            FROM model_execution
            WHERE run_id = %(run_id)s
            ORDER BY started_at, model_execution_id
            """,
            {"run_id": run_id},
        ).fetchall()
    return {
        "run": _json_safe_row(run) if run else None,
        "source_count": len(source_rows),
        "source_status_counts": dict(sorted(Counter(str(row["stage_status"]) for row in source_rows).items())),
        "sources": [_json_safe_row(row) for row in source_rows],
        "model_execution_count": len(model_rows),
        "model_status_counts": dict(sorted(Counter(str(row["execution_status"]) for row in model_rows).items())),
        "model_executions": [_json_safe_row(row) for row in model_rows],
    }


def load_public_api_check(
    settings: Settings,
    *,
    country_codes: list[str],
    product_ids: list[str] | None = None,
) -> dict[str, Any]:
    results = []
    selected_product_ids = {str(item) for item in product_ids or []}
    with open_connection(settings) as connection:
        for country_code in country_codes or ["CA", "US"]:
            query = normalize_public_products_query(
                locale="en",
                country_code=country_code,
                bank_codes=None,
                product_types=None,
                subtype_codes=None,
                target_customer_tags=None,
                fee_bucket=None,
                minimum_balance_bucket=None,
                minimum_deposit_bucket=None,
                term_bucket=None,
                sort_by="default",
                sort_order="desc",
                page=1,
                page_size=200,
            )
            payload = load_public_products(connection, query=query)
            items = list(payload["items"])
            results.append(
                {
                    "country_code": country_code,
                    "total": int(payload["total_items"]),
                    "returned_count": len(items),
                    "freshness": payload["freshness"],
                    "product_type_counts": dict(
                        sorted(Counter(str(item["product_type"]) for item in items).items())
                    ),
                    "unavailable_value_count": sum(_count_unavailable_values(item) for item in items),
                    "selected_items": [
                        item
                        for item in items
                        if not selected_product_ids
                        or str(item.get("product_id")) in selected_product_ids
                    ],
                }
            )
    return {"countries": results, "total": sum(item["total"] for item in results)}


def _count_unavailable_values(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_count_unavailable_values(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_count_unavailable_values(item) for item in value)
    return int(isinstance(value, str) and value.strip().casefold() == "unavailable")


def _brief_accuracy_audit(audit: dict[str, Any]) -> dict[str, Any]:
    runs = list(audit["runs"])
    candidates = list(audit["candidates"])
    return {
        "collection_ids": audit["collection_ids"],
        "run_summary": {
            "run_count": len(runs),
            "partial_count": sum(1 for row in runs if row["partial_completion_flag"]),
            "source_scope_count": sum(int(row["source_scope_count"]) for row in runs),
            "source_success_count": sum(int(row["source_success_count"]) for row in runs),
            "source_failure_count": sum(int(row["source_failure_count"]) for row in runs),
            "candidate_count": sum(int(row["candidate_count"]) for row in runs),
            "review_queued_count": sum(int(row["review_queued_count"]) for row in runs),
        },
        "partial_or_failed_runs": [
            {
                key: row[key]
                for key in (
                    "collection_id", "run_id", "bank_code", "product_type", "source_scope_count",
                    "source_success_count", "source_failure_count", "candidate_count",
                    "review_queued_count", "error_summary",
                )
            }
            for row in runs
            if row["partial_completion_flag"] or row["run_state"] != "completed"
        ],
        "run_source_failures": [
            {
                key: row.get(key)
                for key in (
                    "collection_id", "run_id", "bank_code", "product_type", "normalized_source_url",
                    "discovery_role", "stage_status", "error_summary",
                )
            }
            for row in audit["run_source_failures"]
        ],
        "candidate_state_counts": dict(
            Counter(str(row["candidate_state"]) for row in candidates)
        ),
        "validation_status_counts": dict(
            Counter(str(row["validation_status"]) for row in candidates)
        ),
        "active_collection_review_count": sum(
            1 for row in candidates if str(row["candidate_state"]) == "in_review"
        ),
    }


def launch_collection(
    settings: Settings,
    *,
    only_banks: list[str],
    only_product_types: list[str],
    exact_scopes: list[str] | None = None,
    country_code: str | None = None,
    precision_rediscovery: bool = False,
) -> dict[str, Any]:
    only_bank_set = {item.strip().upper() for item in only_banks if item.strip()}
    only_product_type_set = {item.strip().lower() for item in only_product_types if item.strip()}
    normalized_country = str(country_code or "").strip().upper()
    exact_scope_set: set[tuple[str, str]] = set()
    for raw_scope in exact_scopes or []:
        bank_code, separator, product_type = raw_scope.partition(":")
        if not separator or not bank_code.strip() or not product_type.strip():
            raise ValueError(f"Invalid --scope {raw_scope!r}; expected BANK:product-type.")
        exact_scope_set.add((bank_code.strip().upper(), product_type.strip().lower()))
    with open_connection(settings) as connection:
        rows = _active_catalog_rows(connection)
        if normalized_country:
            rows = [row for row in rows if str(row["country_code"]).upper() == normalized_country]
        if exact_scope_set:
            rows = [
                row
                for row in rows
                if (str(row["bank_code"]).upper(), str(row["product_type"]).lower()) in exact_scope_set
            ]
        if only_bank_set:
            rows = [row for row in rows if str(row["bank_code"]).upper() in only_bank_set]
        if only_product_type_set:
            rows = [row for row in rows if str(row["product_type"]).lower() in only_product_type_set]
        catalog_item_ids = [str(row["catalog_item_id"]) for row in rows]
        if not catalog_item_ids:
            raise RuntimeError("No active source catalog items matched the requested admin bank/product-type scope.")

        result = start_source_catalog_collection(
            connection,
            catalog_item_ids=catalog_item_ids,
            actor=_actor(),
            request_context={
                "request_id": f"req_codex_goal_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                "ip_address": "127.0.0.1",
                "user_agent": "codex-admin-collection-goal-tool",
            },
            precision_rediscovery=precision_rediscovery,
        )
        result["catalog_scope"] = [
            {
                "catalog_item_id": str(row["catalog_item_id"]),
                "country_code": str(row["country_code"]),
                "bank_code": str(row["bank_code"]),
                "bank_name": str(row["bank_name"]),
                "product_type": str(row["product_type"]),
            }
            for row in rows
        ]
        return result


def wait_for_collection(settings: Settings, *, collection_id: str, timeout_seconds: int, poll_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    status = load_collection_status(settings, collection_id=collection_id)
    while not status["terminal"] and time.monotonic() < deadline:
        time.sleep(max(1, poll_seconds))
        status = load_collection_status(settings, collection_id=collection_id)
    return status


def _brief_status(status: dict[str, Any], *, brief: bool) -> dict[str, Any]:
    if not brief:
        return status
    runs = status.get("runs") or []
    active_runs = [
        {
            "run_id": item["run_id"],
            "bank_code": item["bank_code"],
            "product_type": item["product_type"],
            "run_state": item["run_state"],
            "discovery_status": item["discovery_status"],
            "pipeline_stage": item["pipeline_stage"],
            "candidate_count": item["candidate_count"],
            "review_queued_count": item["review_queued_count"],
            "error_summary": item["error_summary"],
        }
        for item in runs
        if item.get("run_state") == "started" or item.get("error_summary")
    ]
    return {
        key: value
        for key, value in status.items()
        if key != "runs"
    } | {"active_or_error_runs": active_runs[:5]}


def load_collection_status(settings: Settings, *, collection_id: str) -> dict[str, Any]:
    with open_connection(settings) as connection:
        rows = connection.execute(
            """
            SELECT
                run_id,
                run_state,
                trigger_type,
                source_scope_count,
                source_success_count,
                source_failure_count,
                candidate_count,
                review_queued_count,
                partial_completion_flag,
                error_summary,
                run_metadata ->> 'bank_code' AS bank_code,
                run_metadata ->> 'product_type' AS product_type,
                run_metadata ->> 'discovery_status' AS discovery_status,
                run_metadata ->> 'pipeline_stage' AS pipeline_stage,
                run_metadata ? 'validation_stats' AS validation_done,
                started_at,
                completed_at
            FROM ingestion_run
            WHERE run_metadata ->> 'collection_id' = %(collection_id)s
            ORDER BY started_at, run_id
            """,
            {"collection_id": collection_id},
        ).fetchall()
        candidate_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
            """,
            {"collection_id": collection_id},
        ).fetchone()
        review_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM review_task AS rt
            JOIN ingestion_run AS ir
              ON ir.run_id = rt.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
            """,
            {"collection_id": collection_id},
        ).fetchone()
    state_counts = Counter(str(row["run_state"]) for row in rows)
    terminal = bool(rows) and all(_run_is_final(row) for row in rows)
    return {
        "collection_id": collection_id,
        "run_count": len(rows),
        "terminal": terminal,
        "state_counts": dict(sorted(state_counts.items())),
        "candidate_count": int(candidate_count["count"] or 0),
        "review_task_count": int(review_count["count"] or 0),
        "runs": [_serialize_run(row) for row in rows],
    }


def compare_collection(settings: Settings, *, collection_id: str) -> dict[str, Any]:
    golden_rows = _load_golden_products()
    actual_rows = _load_actual_products(settings, collection_id=collection_id)

    golden_by_key = {_identity_key(row): _project_compare_row(row) for row in golden_rows}
    actual_by_key = {_identity_key(row): _project_compare_row(row) for row in actual_rows}
    duplicate_actual_keys = _duplicate_keys(actual_rows)
    duplicate_golden_keys = _duplicate_keys(golden_rows)

    missing_keys = sorted(set(golden_by_key) - set(actual_by_key))
    extra_keys = sorted(set(actual_by_key) - set(golden_by_key))
    mismatches = []
    for key in sorted(set(golden_by_key) & set(actual_by_key)):
        field_diffs = {}
        golden = golden_by_key[key]
        actual = actual_by_key[key]
        for field_name in COMPARE_FIELDS:
            if actual.get(field_name) != golden.get(field_name):
                field_diffs[field_name] = {
                    "golden": golden.get(field_name),
                    "actual": actual.get(field_name),
                }
        if field_diffs:
            mismatches.append(
                {
                    "identity": _key_to_payload(key),
                    "fields": field_diffs,
                }
            )

    return {
        "collection_id": collection_id,
        "pass": not missing_keys and not extra_keys and not mismatches and not duplicate_actual_keys and not duplicate_golden_keys,
        "actual_count": len(actual_rows),
        "golden_count": len(golden_rows),
        "missing_count": len(missing_keys),
        "extra_count": len(extra_keys),
        "mismatch_count": len(mismatches),
        "duplicate_actual_count": len(duplicate_actual_keys),
        "duplicate_golden_count": len(duplicate_golden_keys),
        "missing": [_key_to_payload(key) for key in missing_keys[:50]],
        "extra": [_key_to_payload(key) for key in extra_keys[:50]],
        "mismatches": mismatches[:50],
        "duplicate_actual": [_key_to_payload(key) for key in duplicate_actual_keys[:50]],
        "duplicate_golden": [_key_to_payload(key) for key in duplicate_golden_keys[:50]],
        "compared_fields": list(COMPARE_FIELDS),
    }


def _active_catalog_rows(connection: Any) -> list[dict[str, Any]]:
    return list(
        connection.execute(
            """
            SELECT
                sci.catalog_item_id,
                sci.bank_code,
                sci.country_code,
                b.bank_name,
                sci.product_type
            FROM source_registry_catalog_item AS sci
            JOIN bank AS b
              ON b.bank_code = sci.bank_code
            JOIN product_type_registry AS ptr
              ON ptr.product_type_code = sci.product_type
            WHERE sci.status = 'active'
              AND b.status = 'active'
              AND ptr.status = 'active'
            ORDER BY b.bank_name, sci.product_type, sci.catalog_item_id
            """
        ).fetchall()
    )


def _registered_scope(connection: Any) -> dict[str, Any]:
    bank_rows = connection.execute(
        """
        SELECT bank_code, bank_name, status
        FROM bank
        ORDER BY bank_name, bank_code
        """
    ).fetchall()
    product_type_rows = connection.execute(
        """
        SELECT product_type_code, display_name, status
        FROM product_type_registry
        ORDER BY product_family, display_name, product_type_code
        """
    ).fetchall()
    catalog_rows = _active_catalog_rows(connection)
    return {
        "banks": [dict(row) for row in bank_rows],
        "product_types": [dict(row) for row in product_type_rows],
        "active_catalog_item_count": len(catalog_rows),
        "active_catalog_items": [dict(row) for row in catalog_rows],
    }


def _artifact_counts(connection: Any) -> dict[str, int]:
    table_names = (
        "source_registry_item",
        "ingestion_run",
        "source_document",
        "source_snapshot",
        "parsed_document",
        "evidence_chunk",
        "evidence_chunk_embedding",
        "model_execution",
        "llm_usage_record",
        "normalized_candidate",
        "field_evidence_link",
        "review_task",
        "canonical_product",
        "product_version",
        "aggregate_refresh_run",
        "public_product_projection",
    )
    counts = {}
    for table_name in table_names:
        relation = connection.execute(
            "SELECT to_regclass(%s) AS relation_name",
            (f"public.{table_name}",),
        ).fetchone()
        if not relation or relation["relation_name"] is None:
            continue
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        counts[table_name] = int(row["count"] or 0)
    return counts


def _latest_collections(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            run_metadata ->> 'collection_id' AS collection_id,
            MIN(started_at) AS started_at,
            MAX(completed_at) AS completed_at,
            COUNT(*) AS run_count,
            COUNT(*) FILTER (WHERE run_state = 'completed') AS completed_count,
            COUNT(*) FILTER (WHERE run_state = 'failed') AS failed_count,
            SUM(candidate_count) AS candidate_count,
            SUM(review_queued_count) AS review_queued_count
        FROM ingestion_run
        WHERE run_metadata ? 'collection_id'
        GROUP BY run_metadata ->> 'collection_id'
        ORDER BY MIN(started_at) DESC
        LIMIT 5
        """
    ).fetchall()
    return [_serialize_collection(row) for row in rows]


def _load_golden_products() -> list[dict[str, Any]]:
    payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return [dict(row) for row in payload["products"]]


def _load_actual_products(settings: Settings, *, collection_id: str) -> list[dict[str, Any]]:
    with open_connection(settings) as connection:
        rows = connection.execute(
            """
            SELECT
                nc.bank_code,
                nc.product_type,
                nc.product_name,
                nc.candidate_state,
                nc.candidate_payload
            FROM normalized_candidate AS nc
            JOIN ingestion_run AS ir
              ON ir.run_id = nc.run_id
            WHERE ir.run_metadata ->> 'collection_id' = %(collection_id)s
              AND nc.candidate_state NOT IN ('rejected', 'superseded')
            ORDER BY nc.bank_code, nc.product_type, nc.product_name, nc.candidate_id
            """,
            {"collection_id": collection_id},
        ).fetchall()
    actual_rows = []
    for row in rows:
        payload = dict(row["candidate_payload"] or {})
        payload.setdefault("bank_code", row["bank_code"])
        payload.setdefault("product_type", row["product_type"])
        payload.setdefault("product_name", row["product_name"])
        actual_rows.append(payload)
    return actual_rows


def _project_compare_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field_name: row.get(field_name) for field_name in COMPARE_FIELDS}


def _identity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _normalize_identity_text(row.get("bank_name")),
        _normalize_identity_text(row.get("product_type")),
        _normalize_identity_text(row.get("product_name")),
    )


def _normalize_identity_text(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _duplicate_keys(rows: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    counts = Counter(_identity_key(row) for row in rows)
    return sorted(key for key, count in counts.items() if count > 1)


def _key_to_payload(key: tuple[str, str, str]) -> dict[str, str]:
    bank_name, product_type, product_name = key
    return {
        "bank_name": bank_name,
        "product_type": product_type,
        "product_name": product_name,
    }


def _actor() -> dict[str, Any]:
    return {
        "user_id": "codex-admin-collection-test",
        "email": "codex@local",
        "display_name": "Codex Admin Collection Test",
        "role": "admin",
    }


def _serialize_collection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "collection_id": row["collection_id"],
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row["completed_at"]),
        "run_count": int(row["run_count"] or 0),
        "completed_count": int(row["completed_count"] or 0),
        "failed_count": int(row["failed_count"] or 0),
        "candidate_count": int(row["candidate_count"] or 0),
        "review_queued_count": int(row["review_queued_count"] or 0),
    }


def _serialize_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "run_state": row["run_state"],
        "trigger_type": row["trigger_type"],
        "bank_code": row["bank_code"],
        "product_type": row["product_type"],
        "discovery_status": row["discovery_status"],
        "pipeline_stage": row["pipeline_stage"],
        "validation_done": bool(row["validation_done"]),
        "source_scope_count": int(row["source_scope_count"] or 0),
        "source_success_count": int(row["source_success_count"] or 0),
        "source_failure_count": int(row["source_failure_count"] or 0),
        "candidate_count": int(row["candidate_count"] or 0),
        "review_queued_count": int(row["review_queued_count"] or 0),
        "partial_completion_flag": bool(row["partial_completion_flag"]),
        "error_summary": row["error_summary"],
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row["completed_at"]),
    }


def _serialize_accuracy_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "collection_id": str(row["collection_id"]),
        "run_id": str(row["run_id"]),
        "bank_code": str(row["bank_code"]),
        "product_type": str(row["product_type"]),
        "run_state": str(row["run_state"]),
        "source_scope_count": int(row["source_scope_count"] or 0),
        "source_success_count": int(row["source_success_count"] or 0),
        "source_failure_count": int(row["source_failure_count"] or 0),
        "candidate_count": int(row["candidate_count"] or 0),
        "review_queued_count": int(row["review_queued_count"] or 0),
        "partial_completion_flag": bool(row["partial_completion_flag"]),
        "error_summary": row["error_summary"],
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row["completed_at"]),
    }


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in dict(row).items()}


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value.strip() else []
        return _coerce_string_list(parsed)
    return []


def _run_is_final(row: dict[str, Any]) -> bool:
    run_state = str(row["run_state"])
    if run_state in {"failed", "retried"}:
        return True
    if run_state != "completed":
        return False
    return (
        bool(row["validation_done"])
        or row["pipeline_stage"] == "validation_routing"
        or row["discovery_status"] in {"no_detail_sources_discovered", "materialization_failed"}
    )


def _iso(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True, default=str))


if __name__ == "__main__":
    raise SystemExit(main())
