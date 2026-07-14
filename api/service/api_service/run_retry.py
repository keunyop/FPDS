from __future__ import annotations

import argparse
import json
from typing import Any

from api_service.source_catalog import _record_catalog_audit_event, start_source_catalog_collection
from api_service.source_registry import _record_source_registry_audit_event, start_source_collection
from api_service.security import utc_now
from api_service.config import Settings
from api_service.db import open_connection

SUPPORTED_RETRY_RUN_TYPES = {"source_catalog_collection", "source_collection", "admin_source_collection"}


class RunRetryError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def describe_run_retry_action(
    *,
    run_state: str,
    partial_completion_flag: bool = False,
    retried_by_run_id: str | None,
    run_type: str,
    run_metadata: dict[str, Any],
) -> dict[str, Any]:
    if retried_by_run_id:
        return {
            "available": False,
            "reason": "This run already has a later retry attempt.",
        }
    if run_state != "failed" and not (run_state == "completed" and partial_completion_flag):
        return {
            "available": False,
            "reason": "Only failed or partially completed runs can be retried.",
        }

    normalized_run_type = (run_type or "").strip().lower()
    if normalized_run_type == "source_catalog_collection":
        if str(run_metadata.get("catalog_item_id") or "").strip():
            return {"available": True, "reason": None}
        return {
            "available": False,
            "reason": "This source-catalog run is missing its catalog item context.",
        }

    if normalized_run_type in {"source_collection", "admin_source_collection"}:
        source_ids = _collection_retry_source_ids(run_metadata)
        if source_ids:
            return {"available": True, "reason": None}
        return {
            "available": False,
            "reason": "This source-collection run is missing its selected source context.",
        }

    return {
        "available": False,
        "reason": "Retry is currently available only for failed or partially completed collection runs.",
    }


def retry_failed_run(
    connection: Any,
    *,
    run_id: str,
    actor: dict[str, Any],
    request_context: dict[str, Any],
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            ir.run_id,
            ir.run_state,
            ir.partial_completion_flag,
            ir.trigger_type,
            ir.triggered_by,
            ir.retry_of_run_id,
            ir.retried_by_run_id,
            ir.run_metadata,
            COALESCE(NULLIF(ir.run_metadata ->> 'pipeline_stage', ''), ir.trigger_type) AS run_type
        FROM ingestion_run AS ir
        WHERE ir.run_id = %(run_id)s
        """,
        {"run_id": run_id},
    ).fetchone()
    if not row:
        raise RunRetryError(status_code=404, code="run_not_found", message="Run was not found.")

    run_metadata = _coerce_mapping(row.get("run_metadata"))
    retry_action = describe_run_retry_action(
        run_state=str(row["run_state"]),
        partial_completion_flag=bool(row.get("partial_completion_flag")),
        retried_by_run_id=_string_or_none(row.get("retried_by_run_id")),
        run_type=str(row["run_type"]),
        run_metadata=run_metadata,
    )
    if not bool(retry_action["available"]):
        raise RunRetryError(
            status_code=409,
            code="run_retry_not_supported",
            message=str(retry_action["reason"] or "This run cannot be retried."),
        )

    normalized_run_type = str(row["run_type"]).strip().lower()
    if normalized_run_type == "source_catalog_collection":
        result = start_source_catalog_collection(
            connection,
            catalog_item_ids=[str(run_metadata["catalog_item_id"])],
            actor=actor,
            request_context=request_context,
            retry_of_run_id=run_id,
        )
    elif normalized_run_type in {"source_collection", "admin_source_collection"}:
        result = start_source_collection(
            connection,
            source_ids=_collection_retry_source_ids(run_metadata),
            actor=actor,
            request_context=request_context,
            retry_of_run_id=run_id,
        )
    else:  # pragma: no cover - defensive branch after retry-action gate
        raise RunRetryError(
            status_code=409,
            code="run_retry_not_supported",
            message="Retry is currently available only for failed or partially completed collection runs.",
        )

    retry_run_ids = [str(item) for item in result.get("run_ids", []) if str(item).strip()]
    if len(retry_run_ids) != 1:
        raise RunRetryError(
            status_code=409,
            code="run_retry_multiple_groups",
            message="Retry expected a single replacement run but the reconstructed scope expanded to multiple groups.",
        )

    retry_run_id = retry_run_ids[0]
    retry_requested_at = utc_now()
    retry_requested_at_iso = retry_requested_at.isoformat()
    connection.execute(
        """
        UPDATE ingestion_run
        SET
            run_state = 'retried',
            retried_by_run_id = %(retry_run_id)s,
            completed_at = COALESCE(completed_at, %(retry_requested_at)s),
            run_metadata = run_metadata || %(retry_metadata)s::jsonb
        WHERE run_id = %(run_id)s
          AND (run_state = 'failed' OR (run_state = 'completed' AND partial_completion_flag = true))
          AND retried_by_run_id IS NULL
        """,
        {
            "run_id": run_id,
            "retry_run_id": retry_run_id,
            "retry_requested_at": retry_requested_at,
            "retry_metadata": json.dumps(
                {
                    "retry_requested_at": retry_requested_at_iso,
                    "retry_requested_by": actor.get("email") or actor.get("display_name") or actor.get("user_id"),
                },
                ensure_ascii=True,
            ),
        },
    )

    _record_retry_audit_event(
        connection,
        actor=actor,
        request_context=request_context,
        run_type=normalized_run_type,
        original_run_id=run_id,
        retry_run_id=retry_run_id,
        run_metadata=run_metadata,
        previous_state=str(row["run_state"]),
    )

    return {
        "original_run_id": run_id,
        "retry_run_id": retry_run_id,
        "run_type": normalized_run_type,
        "collection_id": result.get("collection_id"),
        "correlation_id": result.get("correlation_id"),
        "run_ids": retry_run_ids,
    }


def _record_retry_audit_event(
    connection: Any,
    *,
    actor: dict[str, Any],
    request_context: dict[str, Any],
    run_type: str,
    original_run_id: str,
    retry_run_id: str,
    run_metadata: dict[str, Any],
    previous_state: str,
) -> None:
    payload = {
        "original_run_id": original_run_id,
        "retry_run_id": retry_run_id,
        "bank_code": run_metadata.get("bank_code"),
        "country_code": run_metadata.get("country_code"),
        "product_type": run_metadata.get("product_type"),
    }
    if run_type == "source_catalog_collection":
        _record_catalog_audit_event(
            connection,
            actor=actor,
            request_context=request_context,
            event_type="source_catalog_collection_retried",
            target_id=retry_run_id,
            target_type="source_catalog_collection",
            diff_summary=f"Retried {previous_state} source-catalog run {original_run_id}.",
            metadata=payload,
        )
        return

    _record_source_registry_audit_event(
        connection,
        event_type="source_collection_retried",
        actor=actor,
        target_id=retry_run_id,
        request_context=request_context,
        previous_state=previous_state,
        new_state="started",
        reason_text=None,
        diff_summary=f"Retried {previous_state} source-collection run {original_run_id}.",
        payload=payload,
        event_category="run",
        target_type="source_collection",
    )


def _collection_retry_source_ids(run_metadata: dict[str, Any]) -> list[str]:
    for key in ("selected_source_ids", "target_source_ids", "source_ids"):
        value = _coerce_string_list(run_metadata.get(key))
        if value:
            return value
    return []


def _coerce_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return {str(key): item for key, item in parsed.items()}
    return {}


def _coerce_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _string_or_none(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def main() -> int:
    parser = argparse.ArgumentParser(description="Retry an eligible failed or partially completed FPDS collection run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--request-id", default="run-retry-cli")
    args = parser.parse_args()
    actor = {"actor_type": "system", "role": "admin", "display_name": "FPDS run retry"}
    with open_connection(Settings.from_env()) as connection:
        result = retry_failed_run(
            connection,
            run_id=args.run_id,
            actor=actor,
            request_context={"request_id": args.request_id, "user_agent": "fpds-run-retry-cli"},
        )
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
