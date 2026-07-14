from __future__ import annotations

import argparse
import json
from typing import Any

from api_service.aggregate_refresh import request_manual_aggregate_refresh
from api_service.config import Settings
from api_service.db import open_connection
from api_service.security import new_id, utc_now


def retract_invalid_candidates(
    connection: Any,
    *,
    candidate_ids: list[str],
    reason_code: str,
    reason_text: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    normalized_ids = list(dict.fromkeys(item.strip() for item in candidate_ids if item.strip()))
    rows = connection.execute(
        """
        SELECT
            nc.candidate_id,
            nc.run_id,
            nc.candidate_state,
            nc.product_name,
            sd.normalized_source_url,
            rt.review_task_id,
            rt.review_state,
            pv.product_version_id,
            cp.product_id,
            cp.status AS product_status
        FROM normalized_candidate AS nc
        JOIN source_document AS sd
          ON sd.source_document_id = nc.source_document_id
        LEFT JOIN review_task AS rt
          ON rt.candidate_id = nc.candidate_id
        LEFT JOIN product_version AS pv
          ON pv.approved_candidate_id = nc.candidate_id
        LEFT JOIN canonical_product AS cp
          ON cp.product_id = pv.product_id
         AND cp.current_version_no = pv.version_no
        WHERE nc.candidate_id = ANY(%(candidate_ids)s)
        ORDER BY nc.candidate_id
        FOR UPDATE OF nc
        """,
        {"candidate_ids": normalized_ids},
    ).fetchall()
    found_ids = {str(row["candidate_id"]) for row in rows}
    missing_ids = [candidate_id for candidate_id in normalized_ids if candidate_id not in found_ids]
    if missing_ids:
        raise ValueError("Candidate safety remediation could not find: " + ", ".join(missing_ids))

    remediated_at = utc_now()
    deactivated_product_ids: list[str] = []
    items: list[dict[str, Any]] = []
    for raw_row in rows:
        row = dict(raw_row)
        candidate_id = str(row["candidate_id"])
        previous_candidate_state = str(row["candidate_state"])
        connection.execute(
            """
            UPDATE normalized_candidate
            SET
                candidate_state = 'rejected',
                review_reason_code = %(reason_code)s,
                updated_at = %(remediated_at)s
            WHERE candidate_id = %(candidate_id)s
            """,
            {
                "candidate_id": candidate_id,
                "reason_code": reason_code,
                "remediated_at": remediated_at,
            },
        )
        if row.get("review_task_id") is not None:
            connection.execute(
                """
                UPDATE review_task
                SET review_state = 'rejected', updated_at = %(remediated_at)s
                WHERE review_task_id = %(review_task_id)s
                  AND review_state IN ('queued', 'deferred', 'approved', 'edited')
                """,
                {"review_task_id": str(row["review_task_id"]), "remediated_at": remediated_at},
            )

        product_id = str(row["product_id"]) if row.get("product_id") is not None else None
        product_deactivated = product_id is not None and str(row.get("product_status") or "") not in {"inactive", "discontinued"}
        if product_deactivated:
            connection.execute(
                """
                UPDATE canonical_product
                SET
                    status = 'inactive',
                    last_changed_at = %(remediated_at)s,
                    updated_at = %(remediated_at)s,
                    current_snapshot_payload = current_snapshot_payload || '{"status":"inactive"}'::jsonb
                WHERE product_id = %(product_id)s
                """,
                {"product_id": product_id, "remediated_at": remediated_at},
            )
            connection.execute(
                """
                INSERT INTO change_event (
                    change_event_id, product_id, product_version_id, run_id, review_task_id,
                    event_type, event_reason_code, event_metadata, detected_at
                )
                VALUES (
                    %(change_event_id)s, %(product_id)s, %(product_version_id)s, %(run_id)s, %(review_task_id)s,
                    'Discontinued', %(reason_code)s, %(event_metadata)s::jsonb, %(remediated_at)s
                )
                """,
                {
                    "change_event_id": new_id("change"),
                    "product_id": product_id,
                    "product_version_id": row.get("product_version_id"),
                    "run_id": str(row["run_id"]),
                    "review_task_id": row.get("review_task_id"),
                    "reason_code": reason_code,
                    "event_metadata": json.dumps(
                        {"candidate_id": candidate_id, "reason_text": reason_text, "remediation_type": "candidate_safety_retraction"},
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                    "remediated_at": remediated_at,
                },
            )
            deactivated_product_ids.append(product_id)

        connection.execute(
            """
            INSERT INTO audit_event (
                audit_event_id, event_category, event_type, actor_type, actor_id, actor_role_snapshot,
                target_type, target_id, previous_state, new_state, reason_code, reason_text,
                run_id, candidate_id, review_task_id, product_id, request_id, diff_summary,
                source_ref, ip_address, user_agent, event_payload, occurred_at
            )
            VALUES (
                %(audit_event_id)s, 'review', 'candidate_safety_retracted', %(actor_type)s, %(actor_id)s, %(actor_role)s,
                'candidate', %(candidate_id)s, %(previous_state)s, 'rejected', %(reason_code)s, %(reason_text)s,
                %(run_id)s, %(candidate_id)s, %(review_task_id)s, %(product_id)s, %(request_id)s, %(diff_summary)s,
                %(source_ref)s, %(ip_address)s, %(user_agent)s, %(event_payload)s::jsonb, %(occurred_at)s
            )
            """,
            {
                "audit_event_id": new_id("audit"),
                "actor_type": str(actor.get("actor_type") or "system"),
                "actor_id": actor.get("user_id") or actor.get("email") or actor.get("display_name"),
                "actor_role": actor.get("role"),
                "candidate_id": candidate_id,
                "previous_state": previous_candidate_state,
                "reason_code": reason_code,
                "reason_text": reason_text,
                "run_id": str(row["run_id"]),
                "review_task_id": row.get("review_task_id"),
                "product_id": product_id,
                "request_id": request_context.get("request_id"),
                "diff_summary": f"Rejected invalid candidate {candidate_id}" + (f" and inactivated product {product_id}." if product_deactivated else "."),
                "source_ref": row.get("normalized_source_url"),
                "ip_address": request_context.get("ip_address"),
                "user_agent": request_context.get("user_agent"),
                "event_payload": json.dumps(
                    {
                        "product_name": str(row["product_name"]),
                        "previous_review_state": row.get("review_state"),
                        "product_deactivated": product_deactivated,
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                ),
                "occurred_at": remediated_at,
            },
        )
        items.append({"candidate_id": candidate_id, "product_id": product_id, "product_deactivated": product_deactivated})

    aggregate_refresh = None
    if deactivated_product_ids:
        aggregate_refresh = request_manual_aggregate_refresh(
            connection,
            actor=actor,
            request_context={**request_context, "remediation_candidate_ids": normalized_ids},
        )
    return {
        "remediated_count": len(items),
        "deactivated_product_ids": sorted(set(deactivated_product_ids)),
        "items": items,
        "aggregate_refresh": aggregate_refresh,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and retract invalid normalized candidates and their current canonical products.")
    parser.add_argument("--candidate-id", action="append", required=True)
    parser.add_argument("--reason-code", required=True)
    parser.add_argument("--reason-text", required=True)
    parser.add_argument("--request-id", default="candidate-safety-remediation")
    args = parser.parse_args()
    actor = {"actor_type": "system", "role": "admin", "display_name": "FPDS safety remediation"}
    with open_connection(Settings.from_env()) as connection:
        result = retract_invalid_candidates(
            connection,
            candidate_ids=args.candidate_id,
            reason_code=args.reason_code,
            reason_text=args.reason_text,
            actor=actor,
            request_context={"request_id": args.request_id, "user_agent": "fpds-candidate-safety-remediation"},
        )
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
