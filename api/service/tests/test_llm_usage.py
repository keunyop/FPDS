from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.llm_usage import load_llm_usage_dashboard, normalize_llm_usage_filters


class _FakeResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict[str, object]]:
        return self._rows


class _RecordingConnection:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> _FakeResult:
        self.calls.append((sql, params))
        return _FakeResult(self.rows)


class LLMUsageTests(unittest.TestCase):
    def test_filter_normalization_strips_and_lowercases_scope_fields(self) -> None:
        filters = normalize_llm_usage_filters(
            recorded_from=datetime(2026, 4, 13, 0, 0, tzinfo=UTC),
            recorded_to=datetime(2026, 4, 14, 0, 0, tzinfo=UTC),
            run_id=" run-001 ",
            agent_name=" FPDS_Extraction ",
            model_name=" GPT-4.1 ",
            provider_name=" OpenAI ",
            stage=" Validation_Routing ",
            search="  prompt   tokens  ",
        )

        self.assertEqual(filters.run_id, "run-001")
        self.assertEqual(filters.agent_name, "fpds_extraction")
        self.assertEqual(filters.model_name, "gpt-4.1")
        self.assertEqual(filters.provider_name, "openai")
        self.assertEqual(filters.stage, "validation_routing")
        self.assertEqual(filters.search, "prompt tokens")

    def test_load_llm_usage_dashboard_builds_totals_and_anomaly_sections(self) -> None:
        rows = [
            {
                "llm_usage_id": "usage-001",
                "recorded_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
                "run_id": "run-001",
                "model_execution_id": "me-001",
                "candidate_id": "cand-001",
                "provider_request_id": "provider-001",
                "prompt_tokens": 1200,
                "completion_tokens": 300,
                "estimated_cost": Decimal("0.620000"),
                "usage_metadata": {},
                "stage_name": "extraction",
                "agent_name": "fpds_extraction",
                "provider_name": "openai",
                "model_name": "gpt-4.1",
                "execution_status": "completed",
                "model_started_at": datetime(2026, 4, 13, 11, 59, tzinfo=UTC),
                "model_completed_at": datetime(2026, 4, 13, 12, 1, tzinfo=UTC),
                "run_state": "completed",
                "trigger_type": "manual",
                "run_stage": "extraction",
                "correlation_id": "corr-001",
                "request_id": "req-001",
                "product_name": "TD Every Day Savings",
                "bank_code": "TD",
                "product_type": "savings",
                "validation_status": "warning",
                "review_task_id": "rt-001",
                "review_state": "queued",
                "queue_reason_code": "manual_sampling_review",
            },
            {
                "llm_usage_id": "usage-002",
                "recorded_at": datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
                "run_id": "run-001",
                "model_execution_id": "me-002",
                "candidate_id": None,
                "provider_request_id": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "estimated_cost": Decimal("0.000000"),
                "usage_metadata": {},
                "stage_name": "validation",
                "agent_name": "fpds_validation",
                "provider_name": "anthropic",
                "model_name": "claude-3.5-sonnet",
                "execution_status": "completed",
                "model_started_at": datetime(2026, 4, 14, 11, 59, tzinfo=UTC),
                "model_completed_at": datetime(2026, 4, 14, 12, 1, tzinfo=UTC),
                "run_state": "completed",
                "trigger_type": "manual",
                "run_stage": "validation_routing",
                "correlation_id": "corr-001",
                "request_id": "req-001",
                "product_name": None,
                "bank_code": None,
                "product_type": None,
                "validation_status": None,
                "review_task_id": None,
                "review_state": None,
                "queue_reason_code": None,
            },
        ]
        connection = _RecordingConnection(rows)
        filters = normalize_llm_usage_filters(
            recorded_from=datetime(2026, 4, 13, 0, 0, tzinfo=UTC),
            recorded_to=datetime(2026, 4, 14, 23, 59, tzinfo=UTC),
            run_id=None,
            agent_name=None,
            model_name=None,
            provider_name=None,
            stage=None,
            search=None,
        )

        payload = load_llm_usage_dashboard(connection, filters=filters)

        self.assertEqual(len(connection.calls), 1)
        self.assertEqual(payload["totals"]["usage_record_count"], 2)
        self.assertEqual(payload["totals"]["run_count"], 1)
        self.assertEqual(payload["totals"]["total_tokens"], 1500)
        self.assertEqual(len(payload["by_model"]), 2)
        self.assertEqual(len(payload["by_agent"]), 2)
        self.assertEqual(len(payload["by_run"]), 1)
        self.assertEqual(len(payload["usage_trend"]), 2)
        self.assertGreaterEqual(payload["totals"]["anomaly_candidate_count"], 1)
        self.assertEqual(payload["anomaly_candidates"][0]["llm_usage_id"], "usage-001")
        self.assertIn("high_token_usage", payload["anomaly_candidates"][0]["anomaly_reasons"])


if __name__ == "__main__":
    unittest.main()
