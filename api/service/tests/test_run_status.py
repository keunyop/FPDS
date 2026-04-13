from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.run_status import (
    _build_error_events,
    _build_stage_summaries,
    _serialize_run_list_row,
    normalize_run_status_filters,
)


class RunStatusTests(unittest.TestCase):
    def test_filter_normalization_defaults_and_normalizes_values(self) -> None:
        filters = normalize_run_status_filters(
            states=None,
            run_type=" Validation_Routing ",
            partial_only=True,
            started_from=None,
            started_to=None,
            search="  run  3901  ",
            sort_by="review_queued_count",
            sort_order="asc",
            page=2,
            page_size=25,
        )

        self.assertEqual(filters.states, ("started", "completed", "failed"))
        self.assertEqual(filters.run_type, "validation_routing")
        self.assertTrue(filters.partial_only)
        self.assertEqual(filters.search, "run 3901")
        self.assertEqual(filters.sort_by, "review_queued_count")
        self.assertEqual(filters.sort_order, "asc")
        self.assertEqual(filters.page, 2)
        self.assertEqual(filters.page_size, 25)

    def test_serialize_run_list_row_aliases_schema_fields(self) -> None:
        row = {
            "run_id": "run-001",
            "run_type": "validation_routing",
            "run_state": "completed",
            "trigger_type": "manual",
            "triggered_by": "operator@example.com",
            "started_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
            "completed_at": datetime(2026, 4, 13, 12, 5, tzinfo=UTC),
            "source_item_count": 3,
            "candidate_count": 3,
            "review_queued_count": 3,
            "source_success_count": 3,
            "source_failure_count": 0,
            "partial_completion_flag": False,
            "error_summary": None,
            "pipeline_stage": "validation_routing",
            "correlation_id": "corr-001",
            "retry_of_run_id": None,
            "retried_by_run_id": None,
        }

        serialized = _serialize_run_list_row(row)

        self.assertEqual(serialized["run_status"], "completed")
        self.assertEqual(serialized["success_count"], 3)
        self.assertEqual(serialized["failure_count"], 0)
        self.assertEqual(serialized["correlation_id"], "corr-001")
        self.assertEqual(serialized["started_at"], "2026-04-13T12:00:00+00:00")

    def test_build_stage_summaries_marks_partial_completion_as_degraded(self) -> None:
        summaries = _build_stage_summaries(
            run_row={
                "run_type": "validation_routing",
                "run_state": "completed",
                "partial_completion_flag": True,
                "run_metadata": {"pipeline_stage": "validation_routing"},
                "source_scope_count": 3,
                "source_success_count": 2,
                "source_failure_count": 1,
                "started_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
                "completed_at": datetime(2026, 4, 13, 12, 5, tzinfo=UTC),
            },
            source_rows=[
                {"source_document_id": "src-001"},
                {"source_document_id": "src-002"},
                {"source_document_id": "src-003"},
            ],
            model_execution_rows=[],
        )

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["stage_status"], "degraded")
        self.assertEqual(summaries[0]["success_count"], 2)
        self.assertEqual(summaries[0]["failure_count"], 1)

    def test_build_error_events_orders_run_and_source_issues(self) -> None:
        events = _build_error_events(
            run_row={
                "run_state": "failed",
                "error_summary": "Run initialization failed.",
                "source_failure_count": 2,
            },
            source_rows=[
                {
                    "source_document_id": "src-001",
                    "source_id": "TD-SAV-002",
                    "stage_status": "failed",
                    "warning_count": 0,
                    "error_count": 1,
                    "error_summary": "Source fetch failed.",
                    "runtime_notes": ["HTTP 500"],
                    "source_url": "https://example.com/a",
                },
                {
                    "source_document_id": "src-002",
                    "source_id": "TD-SAV-003",
                    "stage_status": "completed",
                    "warning_count": 1,
                    "error_count": 0,
                    "error_summary": None,
                    "runtime_notes": ["Completed with one warning."],
                    "source_url": "https://example.com/b",
                },
            ],
        )

        self.assertEqual(events[0]["scope"], "run")
        self.assertEqual(events[1]["severity"], "error")
        self.assertEqual(events[2]["severity"], "warning")


if __name__ == "__main__":
    unittest.main()
