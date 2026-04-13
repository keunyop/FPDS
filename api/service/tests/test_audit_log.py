from __future__ import annotations

from datetime import UTC, datetime
import unittest

from api_service.audit_log import _serialize_audit_row, normalize_audit_log_filters


class AuditLogTests(unittest.TestCase):
    def test_filter_normalization_canonicalizes_category_and_sort(self) -> None:
        filters = normalize_audit_log_filters(
            event_category=" Review ",
            event_type=" evidence_trace_viewed ",
            actor_type=" User ",
            target_type=" Review_Task ",
            actor_id=" usr-001 ",
            target_id=" rt-001 ",
            run_id=" run-001 ",
            review_task_id=" rt-001 ",
            product_id=" prod-001 ",
            publish_item_id=" pub-001 ",
            occurred_from=None,
            occurred_to=None,
            search="  trace   viewed  ",
            sort_by="event_type",
            sort_order="asc",
            page=2,
            page_size=25,
        )

        self.assertEqual(filters.event_category, "review")
        self.assertEqual(filters.event_type, "evidence_trace_viewed")
        self.assertEqual(filters.actor_type, "user")
        self.assertEqual(filters.target_type, "review_task")
        self.assertEqual(filters.actor_id, "usr-001")
        self.assertEqual(filters.target_id, "rt-001")
        self.assertEqual(filters.search, "trace viewed")
        self.assertEqual(filters.sort_by, "event_type")
        self.assertEqual(filters.sort_order, "asc")
        self.assertEqual(filters.page, 2)
        self.assertEqual(filters.page_size, 25)

    def test_serialize_audit_row_exposes_nested_context(self) -> None:
        serialized = _serialize_audit_row(
            {
                "audit_event_id": "audit-001",
                "event_category": "review",
                "event_type": "review_task_edited",
                "occurred_at": datetime(2026, 4, 13, 23, 0, tzinfo=UTC),
                "actor_type": "user",
                "actor_id": "usr-001",
                "actor_display_name": "Admin Operator",
                "actor_email": "admin@example.com",
                "actor_role_snapshot": "admin",
                "actor_current_role": "admin",
                "target_type": "review_task",
                "target_id": "rt-001",
                "target_display_name": "TD Every Day Savings Account",
                "previous_state": "queued",
                "new_state": "edited",
                "reason_code": "manual_override",
                "reason_text": "Adjusted the monthly fee.",
                "run_id": "run-001",
                "candidate_id": "cand-001",
                "review_task_id": "rt-001",
                "product_id": "prod-001",
                "publish_item_id": None,
                "request_id": "req-001",
                "diff_summary": "Monthly Fee: 5 -> 0",
                "source_ref": "chunk-001",
                "ip_address": "127.0.0.1",
                "user_agent": "unit-test",
                "retention_class": "hot",
                "event_payload": {"changed_fields": ["monthly_fee"]},
                "run_type": "validation_routing",
                "run_state": "completed",
                "product_name": "TD Every Day Savings Account",
                "bank_code": "TD",
                "bank_name": "TD Bank",
            }
        )

        self.assertEqual(serialized["actor"]["display_name"], "Admin Operator")
        self.assertEqual(serialized["target"]["display_name"], "TD Every Day Savings Account")
        self.assertEqual(serialized["state_transition"]["new_state"], "edited")
        self.assertEqual(serialized["related_context"]["run_type"], "validation_routing")
        self.assertEqual(serialized["related_context"]["bank_name"], "TD Bank")
        self.assertEqual(serialized["event_payload"]["changed_fields"], ["monthly_fee"])


if __name__ == "__main__":
    unittest.main()
