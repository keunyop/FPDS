from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.review_queue import _serialize_review_task_row, normalize_review_queue_filters


class ReviewQueueTests(unittest.TestCase):
    def test_filter_normalization_defaults_to_active_states_and_normalizes_case(self) -> None:
        filters = normalize_review_queue_filters(
            states=None,
            bank_code=" td ",
            product_type=" Savings ",
            validation_status="warning",
            created_from=None,
            created_to=None,
            search="  td  epremium  ",
            sort_by="priority",
            sort_order="desc",
            page=2,
            page_size=25,
        )

        self.assertEqual(filters.states, ("queued", "deferred"))
        self.assertEqual(filters.bank_code, "TD")
        self.assertEqual(filters.product_type, "savings")
        self.assertEqual(filters.validation_status, "warning")
        self.assertEqual(filters.search, "td epremium")
        self.assertEqual(filters.page, 2)
        self.assertEqual(filters.page_size, 25)

    def test_serialize_review_task_row_builds_stable_issue_summary(self) -> None:
        row = {
            "review_task_id": "review-001",
            "candidate_id": "cand-001",
            "run_id": "run-001",
            "country_code": "CA",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "product_type": "savings",
            "product_name": "TD ePremium Savings Account",
            "review_state": "queued",
            "candidate_state": "in_review",
            "validation_status": "warning",
            "validation_issue_codes": ["ambiguous_mapping", "manual_sampling_review"],
            "source_confidence": Decimal("0.8123"),
            "queue_reason_code": "ambiguous_mapping",
            "issue_summary": [
                {"code": "ambiguous_mapping", "severity": "warning", "summary": "A field could not be mapped with enough certainty."},
                {"code": "manual_sampling_review", "severity": "warning", "summary": "Prototype routing keeps all candidates in review."},
                {"code": "low_confidence", "severity": "warning", "summary": "The overall source confidence was below the routing threshold."},
            ],
            "created_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
            "updated_at": datetime(2026, 4, 13, 12, 30, tzinfo=UTC),
        }

        serialized = _serialize_review_task_row(row)

        self.assertEqual(serialized["review_task_id"], "review-001")
        self.assertEqual(serialized["validation_issue_codes"], ["ambiguous_mapping", "manual_sampling_review"])
        self.assertEqual(serialized["source_confidence"], 0.8123)
        self.assertEqual(
            serialized["issue_summary"],
            "A field could not be mapped with enough certainty. Prototype routing keeps all candidates in review. (+1 more)",
        )
        self.assertEqual(serialized["created_at"], "2026-04-13T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
