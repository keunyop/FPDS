from __future__ import annotations

from datetime import UTC, datetime
import unittest

from api_service.change_history import _build_change_summary, _serialize_change_row, normalize_change_history_filters


class ChangeHistoryTests(unittest.TestCase):
    def test_filter_normalization_canonicalizes_change_type_and_sort(self) -> None:
        filters = normalize_change_history_filters(
            product_id="  prod-001 ",
            bank_code=" td ",
            product_type=" Savings ",
            change_type=" manualoverride ",
            changed_from=None,
            changed_to=None,
            search="  td   savings  ",
            sort_by="product_name",
            sort_order="asc",
            page=2,
            page_size=25,
        )

        self.assertEqual(filters.product_id, "prod-001")
        self.assertEqual(filters.bank_code, "TD")
        self.assertEqual(filters.product_type, "savings")
        self.assertEqual(filters.change_type, "ManualOverride")
        self.assertEqual(filters.search, "td savings")
        self.assertEqual(filters.sort_by, "product_name")
        self.assertEqual(filters.sort_order, "asc")
        self.assertEqual(filters.page, 2)
        self.assertEqual(filters.page_size, 25)

    def test_build_change_summary_mentions_version_and_field_count(self) -> None:
        summary = _build_change_summary(
            change_type="Updated",
            product_name="TD Every Day Savings Account",
            changed_fields=["standard_rate", "monthly_fee", "bonus_rate", "minimum_balance"],
            previous_version_no=2,
            current_version_no=3,
        )

        self.assertIn("Version 3 replaced version 2", summary)
        self.assertIn("standard_rate, monthly_fee, bonus_rate, and 1 more", summary)

    def test_serialize_change_row_exposes_manual_override_audit_context(self) -> None:
        serialized = _serialize_change_row(
            {
                "change_event_id": "chg-001",
                "product_id": "prod-001",
                "product_version_id": "pver-003",
                "run_id": "run-001",
                "review_task_id": "rt-001",
                "event_type": "ManualOverride",
                "event_reason_code": "manual_override",
                "event_metadata": {
                    "previous_version_no": 2,
                    "current_version_no": 3,
                    "changed_field_names": ["monthly_fee", "notes"],
                    "actor_user_id": "usr-001",
                },
                "detected_at": datetime(2026, 4, 13, 22, 15, tzinfo=UTC),
                "bank_code": "TD",
                "bank_name": "TD Bank",
                "product_name": "TD Every Day Savings Account",
                "product_type": "savings",
                "subtype_code": "high_interest",
                "review_state": "edited",
                "review_action_type": "edit_approve",
                "review_reason_code": "evidence_clarified",
                "review_reason_text": "Corrected the monthly fee",
                "review_diff_summary": "Monthly Fee: 5 -> 0",
                "review_decided_at": datetime(2026, 4, 13, 22, 14, tzinfo=UTC),
                "decision_actor_user_id": "usr-001",
                "actor_display_name": "Admin Operator",
                "actor_email": "admin@example.com",
                "actor_role": "admin",
                "run_type": "validation_routing",
                "run_state": "completed",
                "correlation_id": "corr-001",
                "audit_event_id": "audit-001",
                "audit_diff_summary": "Manual override fields: monthly_fee, notes",
                "audit_occurred_at": datetime(2026, 4, 13, 22, 15, tzinfo=UTC),
                "audit_actor_id": "usr-001",
                "audit_actor_display_name": "Admin Operator",
                "audit_actor_email": "admin@example.com",
                "audit_actor_role": "admin",
            }
        )

        self.assertEqual(serialized["actor_type"], "user")
        self.assertEqual(serialized["changed_fields"], ["monthly_fee", "notes"])
        self.assertEqual(serialized["review_context"]["action_type"], "edit_approve")
        self.assertEqual(serialized["audit_context"]["audit_event_id"], "audit-001")
        self.assertEqual(serialized["run_context"]["run_id"], "run-001")


if __name__ == "__main__":
    unittest.main()
