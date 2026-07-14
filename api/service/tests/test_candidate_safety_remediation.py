from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch

from api_service.candidate_safety_remediation import retract_invalid_candidates


class _Cursor:
    def __init__(self, payload=None):
        self.payload = payload

    def fetchall(self):
        return self.payload if isinstance(self.payload, list) else []


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params or {}))
        if "SELECT" in sql and "FROM normalized_candidate" in sql:
            return _Cursor(self.rows)
        return _Cursor()


class CandidateSafetyRemediationTests(unittest.TestCase):
    def test_retracts_candidate_inactivates_current_product_and_queues_refresh(self) -> None:
        connection = _Connection(
            [
                {
                    "candidate_id": "cand-bad",
                    "run_id": "run-bad",
                    "candidate_state": "approved",
                    "product_name": "Not a product",
                    "normalized_source_url": "https://bank.example/terms.pdf",
                    "review_task_id": None,
                    "review_state": None,
                    "product_version_id": "pv-bad",
                    "product_id": "prod-bad",
                    "product_status": "active",
                }
            ]
        )
        decided_at = datetime(2026, 7, 14, 6, 0, tzinfo=UTC)
        with (
            patch("api_service.candidate_safety_remediation.utc_now", return_value=decided_at),
            patch(
                "api_service.candidate_safety_remediation.request_manual_aggregate_refresh",
                return_value={"request_status": "queued"},
            ) as queue_refresh,
        ):
            result = retract_invalid_candidates(
                connection,
                candidate_ids=["cand-bad"],
                reason_code="invalid_source_role",
                reason_text="Supporting terms were not a product.",
                actor={"actor_type": "system", "role": "admin"},
                request_context={"request_id": "req-remediate"},
            )

        self.assertEqual(result["deactivated_product_ids"], ["prod-bad"])
        self.assertTrue(any("status = 'inactive'" in sql for sql, _params in connection.calls))
        self.assertTrue(any("candidate_safety_retracted" in sql for sql, _params in connection.calls))
        queue_refresh.assert_called_once()


if __name__ == "__main__":
    unittest.main()
