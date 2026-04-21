from __future__ import annotations

from datetime import UTC, datetime
import unittest

from api_service.aggregate_refresh import (
    load_dashboard_health,
    queue_review_aggregate_refresh_request,
    request_manual_aggregate_refresh,
)


class _Cursor:
    def __init__(self, payload: object = None) -> None:
        self.payload = payload

    def fetchone(self):
        if isinstance(self.payload, list):
            return self.payload[0] if self.payload else None
        return self.payload if isinstance(self.payload, dict) else None

    def fetchall(self):
        if isinstance(self.payload, list):
            return self.payload
        if isinstance(self.payload, dict):
            return [self.payload]
        return []


class _Connection:
    def __init__(self, responses: list[object] | None = None) -> None:
        self._responses = list(responses or [])
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _Cursor:
        self.calls.append((sql, params or {}))
        payload = self._responses.pop(0) if self._responses else None
        return _Cursor(payload)


class AggregateRefreshTests(unittest.TestCase):
    def test_queue_review_refresh_request_persists_review_context(self) -> None:
        connection = _Connection()

        result = queue_review_aggregate_refresh_request(
            connection,
            actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            request_context={"request_id": "req-001"},
            review_task_id="rt-001",
            product_id="prod-001",
            action_type="approve",
            change_event_types=["Updated"],
        )

        self.assertEqual(result["request_status"], "queued")
        self.assertEqual(result["trigger_reason"], "review_approval")
        self.assertEqual(result["review_task_id"], "rt-001")
        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("INSERT INTO aggregate_refresh_request", sql)
        self.assertEqual(params["review_task_id"], "rt-001")
        self.assertEqual(params["product_id"], "prod-001")

    def test_manual_retry_reuses_existing_pending_request(self) -> None:
        connection = _Connection(
            [
                {
                    "aggregate_refresh_request_id": "aggreq-existing",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "request_status": "queued",
                    "trigger_reason": "review_approval",
                    "requested_by_label": "admin@example.com",
                    "requested_at": datetime(2026, 4, 21, 19, 0, tzinfo=UTC),
                    "started_at": None,
                    "completed_at": None,
                    "snapshot_id": None,
                    "error_summary": None,
                }
            ]
        )

        result = request_manual_aggregate_refresh(
            connection,
            actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            request_context={"request_id": "req-001"},
        )

        self.assertEqual(result["aggregate_refresh_request_id"], "aggreq-existing")
        self.assertTrue(result["already_pending"])
        self.assertEqual(len(connection.calls), 1)

    def test_load_dashboard_health_marks_scope_stale_when_canonical_is_newer_than_snapshot(self) -> None:
        connection = _Connection(
            [
                {
                    "snapshot_id": "agg-001",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "refresh_status": "completed",
                    "source_change_cutoff_at": datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
                    "attempted_at": datetime(2026, 4, 20, 12, 1, tzinfo=UTC),
                    "refreshed_at": datetime(2026, 4, 20, 12, 2, tzinfo=UTC),
                    "stale_flag": False,
                    "error_summary": None,
                    "refresh_metadata": {},
                },
                {
                    "snapshot_id": "agg-001",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "refresh_status": "completed",
                    "source_change_cutoff_at": datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
                    "attempted_at": datetime(2026, 4, 20, 12, 1, tzinfo=UTC),
                    "refreshed_at": datetime(2026, 4, 20, 12, 2, tzinfo=UTC),
                    "stale_flag": False,
                    "error_summary": None,
                    "refresh_metadata": {},
                },
                {
                    "aggregate_refresh_request_id": "aggreq-001",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "request_status": "completed",
                    "trigger_reason": "review_approval",
                    "requested_at": datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
                    "completed_at": datetime(2026, 4, 20, 12, 2, tzinfo=UTC),
                    "snapshot_id": "agg-001",
                },
                None,
                {"queued_count": 0, "started_count": 0},
                {
                    "active_product_count": 11,
                    "latest_canonical_change_at": datetime(2026, 4, 21, 18, 0, tzinfo=UTC),
                },
                {"active_product_count": 11},
            ]
        )

        payload = load_dashboard_health(connection)
        domain = payload["domains"][0]

        self.assertEqual(domain["status"], "stale")
        self.assertTrue(domain["stale_flag"])
        self.assertIn("Canonical product changes are newer", domain["stale_reason"])
        self.assertEqual(domain["missing_data_ratio"], 0.0)

    def test_load_dashboard_health_marks_failed_when_latest_request_failed_but_serving_success_remains(self) -> None:
        connection = _Connection(
            [
                {
                    "snapshot_id": "agg-001",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "refresh_status": "completed",
                    "source_change_cutoff_at": datetime(2026, 4, 21, 18, 0, tzinfo=UTC),
                    "attempted_at": datetime(2026, 4, 21, 18, 1, tzinfo=UTC),
                    "refreshed_at": datetime(2026, 4, 21, 18, 2, tzinfo=UTC),
                    "stale_flag": False,
                    "error_summary": None,
                    "refresh_metadata": {},
                },
                {
                    "snapshot_id": "agg-002",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "refresh_status": "failed",
                    "source_change_cutoff_at": None,
                    "attempted_at": datetime(2026, 4, 21, 18, 5, tzinfo=UTC),
                    "refreshed_at": None,
                    "stale_flag": False,
                    "error_summary": "worker timed out",
                    "refresh_metadata": {},
                },
                {
                    "aggregate_refresh_request_id": "aggreq-002",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "request_status": "failed",
                    "trigger_reason": "manual_retry",
                    "requested_at": datetime(2026, 4, 21, 18, 4, tzinfo=UTC),
                    "completed_at": datetime(2026, 4, 21, 18, 6, tzinfo=UTC),
                    "snapshot_id": None,
                    "error_summary": "worker timed out",
                },
                {
                    "aggregate_refresh_request_id": "aggreq-002",
                    "refresh_scope": "phase1_public",
                    "country_code": "CA",
                    "request_status": "failed",
                    "trigger_reason": "manual_retry",
                    "requested_at": datetime(2026, 4, 21, 18, 4, tzinfo=UTC),
                    "completed_at": datetime(2026, 4, 21, 18, 6, tzinfo=UTC),
                    "snapshot_id": None,
                    "error_summary": "worker timed out",
                },
                {"queued_count": 0, "started_count": 0},
                {
                    "active_product_count": 11,
                    "latest_canonical_change_at": datetime(2026, 4, 21, 18, 0, tzinfo=UTC),
                },
                {"active_product_count": 11},
            ]
        )

        payload = load_dashboard_health(connection)
        domain = payload["domains"][0]

        self.assertEqual(domain["status"], "failed")
        self.assertEqual(domain["latest_failure_at"], "2026-04-21T18:06:00+00:00")
        self.assertEqual(domain["serving_snapshot_id"], "agg-001")
        self.assertIn("latest successful aggregate snapshot", domain["serving_note"])


if __name__ == "__main__":
    unittest.main()
