from __future__ import annotations

import unittest
from unittest.mock import patch

from api_service.run_retry import RunRetryError, describe_run_retry_action, retry_failed_run


class _QueuedCursor:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def fetchone(self) -> dict[str, object] | None:
        if isinstance(self.payload, list):
            return self.payload[0] if self.payload else None
        return self.payload if isinstance(self.payload, dict) else None


class _QueuedConnection:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _QueuedCursor:
        self.calls.append((sql, params or {}))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _QueuedCursor(self._responses.pop(0))


class RunRetryTests(unittest.TestCase):
    def test_describe_run_retry_action_allows_failed_source_catalog_run(self) -> None:
        result = describe_run_retry_action(
            run_state="failed",
            retried_by_run_id=None,
            run_type="source_catalog_collection",
            run_metadata={"catalog_item_id": "catalog-ca-cibc-savings"},
        )

        self.assertEqual(result, {"available": True, "reason": None})

    def test_retry_failed_run_requeues_source_catalog_run(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "run_id": "run-failed-001",
                    "run_state": "failed",
                    "trigger_type": "admin_source_catalog_collection",
                    "triggered_by": "admin@example.com",
                    "retry_of_run_id": None,
                    "retried_by_run_id": None,
                    "run_metadata": {
                        "pipeline_stage": "source_catalog_collection",
                        "catalog_item_id": "catalog-ca-cibc-savings",
                        "bank_code": "CIBC",
                        "product_type": "savings",
                    },
                    "run_type": "source_catalog_collection",
                },
                None,
            ]
        )

        with (
            patch(
                "api_service.run_retry.start_source_catalog_collection",
                return_value={
                    "collection_id": "collection-002",
                    "correlation_id": "corr-002",
                    "run_ids": ["run-retry-001"],
                },
            ) as start_retry,
            patch("api_service.run_retry._record_retry_audit_event") as record_audit,
        ):
            result = retry_failed_run(
                connection,
                run_id="run-failed-001",
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["retry_run_id"], "run-retry-001")
        start_retry.assert_called_once_with(
            connection,
            catalog_item_ids=["catalog-ca-cibc-savings"],
            actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            retry_of_run_id="run-failed-001",
        )
        self.assertTrue(any("UPDATE ingestion_run" in sql for sql, _ in connection.calls))
        update_params = next(params for sql, params in connection.calls if "UPDATE ingestion_run" in sql)
        self.assertEqual(update_params["run_id"], "run-failed-001")
        self.assertEqual(update_params["retry_run_id"], "run-retry-001")
        record_audit.assert_called_once()

    def test_retry_failed_run_requeues_source_collection_run_using_selected_source_ids(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "run_id": "run-failed-002",
                    "run_state": "failed",
                    "trigger_type": "admin_source_collection",
                    "triggered_by": "admin@example.com",
                    "retry_of_run_id": None,
                    "retried_by_run_id": None,
                    "run_metadata": {
                        "pipeline_stage": "source_collection",
                        "selected_source_ids": ["CIBC-SAV-002"],
                        "target_source_ids": ["CIBC-SAV-002"],
                    },
                    "run_type": "source_collection",
                },
                None,
            ]
        )

        with (
            patch(
                "api_service.run_retry.start_source_collection",
                return_value={
                    "collection_id": "collection-003",
                    "correlation_id": "corr-003",
                    "run_ids": ["run-retry-002"],
                },
            ) as start_retry,
            patch("api_service.run_retry._record_retry_audit_event"),
        ):
            result = retry_failed_run(
                connection,
                run_id="run-failed-002",
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["retry_run_id"], "run-retry-002")
        start_retry.assert_called_once_with(
            connection,
            source_ids=["CIBC-SAV-002"],
            actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            retry_of_run_id="run-failed-002",
        )

    def test_retry_failed_run_rejects_non_failed_runs(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "run_id": "run-completed-001",
                    "run_state": "completed",
                    "trigger_type": "admin_source_collection",
                    "triggered_by": "admin@example.com",
                    "retry_of_run_id": None,
                    "retried_by_run_id": None,
                    "run_metadata": {"pipeline_stage": "source_collection", "selected_source_ids": ["TD-SAV-002"]},
                    "run_type": "source_collection",
                }
            ]
        )

        with self.assertRaises(RunRetryError) as captured:
            retry_failed_run(
                connection,
                run_id="run-completed-001",
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(captured.exception.code, "run_retry_not_supported")


if __name__ == "__main__":
    unittest.main()
