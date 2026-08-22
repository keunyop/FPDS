from __future__ import annotations

from unittest import TestCase
from unittest.mock import MagicMock, patch

from api_service.collection_automation import (
    AUTOMATED_PRODUCT_TYPES,
    load_collection_automation_policy,
    load_due_catalog_item_ids,
    load_recoverable_collection_review_task_ids,
    run_collection_automation_cycle,
)


class _Cursor:
    def __init__(self, *, rows=None, row=None):
        self._rows = rows or []
        self._row = row

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._row


class _QueryConnection:
    def __init__(self, *, rows=None, row=None):
        self.rows = rows or []
        self.row = row
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(str(sql).split()), params or {}))
        return _Cursor(rows=self.rows, row=self.row)


class CollectionAutomationTests(TestCase):
    def test_policy_is_fail_closed_without_migration_and_bounds_values(self):
        connection = _QueryConnection(
            rows=[
                {"policy_key": "COLLECTION_AUTOMATION_ENABLED", "policy_value": {"value": True}},
                {"policy_key": "COLLECTION_AUTOMATION_INTERVAL_HOURS", "policy_value": {"value": 0}},
                {"policy_key": "COLLECTION_AUTOMATION_RETRY_HOURS", "policy_value": {"value": 1000}},
                {"policy_key": "COLLECTION_AUTOMATION_BATCH_SIZE", "policy_value": {"value": 500}},
                {"policy_key": "COLLECTION_AUTOMATION_REVIEW_RECOVERY_LIMIT", "policy_value": {"value": 0}},
                {"policy_key": "COLLECTION_AUTOMATION_STALE_RUN_HOURS", "policy_value": {"value": 1000}},
            ]
        )

        policy = load_collection_automation_policy(connection)

        self.assertTrue(policy["enabled"])
        self.assertEqual(policy["interval_hours"], 1)
        self.assertEqual(policy["retry_hours"], 168)
        self.assertEqual(policy["batch_size"], 50)
        self.assertEqual(policy["review_recovery_limit"], 1)
        self.assertEqual(policy["stale_run_hours"], 168)
        self.assertFalse(load_collection_automation_policy(_QueryConnection())["enabled"])

    def test_recovery_query_skips_live_runs_and_assessed_current_verifications(self):
        connection = _QueryConnection(rows=[{"review_task_id": "review-001"}])

        task_ids = load_recoverable_collection_review_task_ids(connection, limit=999)

        self.assertEqual(task_ids, ["review-001"])
        sql, params = connection.calls[0]
        self.assertEqual(params, {"limit": 200})
        self.assertIn("ir.run_state IN ('completed', 'failed', 'retried')", sql)
        self.assertIn("review-ai-verification-v19", sql)
        self.assertIn("auto_approval_assessment", sql)

    def test_due_catalog_query_is_country_bank_type_scoped_and_bounded(self):
        connection = _QueryConnection(
            rows=[{"catalog_item_id": "catalog-ca-bank-savings"}]
        )

        item_ids = load_due_catalog_item_ids(
            connection,
            interval_hours=0,
            retry_hours=0,
            limit=500,
        )

        self.assertEqual(item_ids, ["catalog-ca-bank-savings"])
        sql, params = connection.calls[0]
        self.assertEqual(params["interval_hours"], 1)
        self.assertEqual(params["retry_hours"], 1)
        self.assertEqual(params["limit"], 50)
        self.assertEqual(tuple(params["product_types"]), AUTOMATED_PRODUCT_TYPES)
        self.assertIn("country_registry", sql)
        self.assertIn("latest_started_at", sql)
        self.assertIn("latest_partial_completion_flag", sql)

    def test_cycle_recovers_promotes_refreshes_and_starts_due_collection(self):
        connection = MagicMock()
        policy = {
            "enabled": True,
            "interval_hours": 168,
            "retry_hours": 24,
            "batch_size": 6,
            "review_recovery_limit": 10,
            "stale_run_hours": 12,
        }
        with (
            patch("api_service.collection_automation.load_collection_automation_policy", return_value=policy),
            patch("api_service.collection_automation.recover_stale_collection_runs", return_value=["run-stale"]),
            patch(
                "api_service.collection_automation.promote_auto_validated_candidates",
                return_value={"promoted_count": 1, "skipped_count": 2},
            ) as promote,
            patch(
                "api_service.collection_automation.load_collection_ai_autopilot_policy",
                return_value={"enabled": True, "approval_threshold": 1.0},
            ),
            patch("api_service.collection_automation.llm_provider_configured", return_value=False),
            patch("api_service.collection_automation.has_pending_aggregate_refresh", return_value=True),
            patch(
                "api_service.collection_automation.launch_aggregate_refresh_runner",
                return_value={"launched": True},
            ),
            patch("api_service.collection_automation.has_active_source_catalog_collection", return_value=False),
            patch(
                "api_service.collection_automation.load_due_catalog_item_ids",
                return_value=["catalog-001"],
            ),
            patch(
                "api_service.collection_automation.start_source_catalog_collection",
                return_value={"collection_id": "collection-001"},
            ) as start_collection,
        ):
            result = run_collection_automation_cycle(connection)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stale_run_count"], 1)
        self.assertEqual(result["promotion"]["promoted_count"], 1)
        promote_kwargs = promote.call_args.kwargs
        self.assertEqual(promote_kwargs["actor"]["actor_type"], "scheduler")
        start_kwargs = start_collection.call_args.kwargs
        self.assertEqual(start_kwargs["catalog_item_ids"], ["catalog-001"])
        self.assertEqual(start_kwargs["actor"]["actor_type"], "scheduler")
        self.assertGreaterEqual(connection.commit.call_count, 3)
