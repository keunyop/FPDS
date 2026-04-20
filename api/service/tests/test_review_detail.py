from __future__ import annotations

import unittest

from api_service.review_detail import (
    _available_actions,
    _build_diff_summary,
    _build_field_trace_groups,
    _build_validation_issues,
    _changed_field_names,
    _collect_model_execution_ids,
    _is_empty_review_value,
    _normalize_override_payload,
    _serialize_field_mapping,
    record_evidence_trace_viewed,
)


class _RecordingConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.calls.append((sql, params))


class ReviewDetailTests(unittest.TestCase):
    def test_normalize_override_payload_keeps_only_real_changes(self) -> None:
        normalized = _normalize_override_payload(
            override_payload={
                "monthly_fee": 0,
                "notes": "Reviewer supplied note",
                "review_task_id": "should-be-ignored",
                "status": "active",
            },
            base_payload={
                "monthly_fee": 5,
                "notes": None,
                "status": "active",
            },
        )

        self.assertEqual(
            normalized,
            {
                "monthly_fee": 0,
                "notes": "Reviewer supplied note",
            },
        )

    def test_normalize_override_payload_trims_product_name_override(self) -> None:
        normalized = _normalize_override_payload(
            override_payload={
                "product_name": "  TD Every Day Savings Plus  ",
            },
            base_payload={
                "product_name": "TD Every Day Savings Account",
            },
        )

        self.assertEqual(
            normalized,
            {
                "product_name": "TD Every Day Savings Plus",
            },
        )

    def test_changed_field_names_and_diff_summary_cover_edit_preview(self) -> None:
        changed_fields = _changed_field_names(
            before={"monthly_fee": 5, "notes": None},
            after={"monthly_fee": 0, "notes": "No monthly fee"},
        )
        summary = _build_diff_summary(
            changed_fields=changed_fields,
            before_payload={"monthly_fee": 5, "notes": None},
            after_payload={"monthly_fee": 0, "notes": "No monthly fee"},
        )

        self.assertEqual(changed_fields, ["monthly_fee", "notes"])
        self.assertIn("Monthly Fee: 5 -> 0", summary)
        self.assertIn("Notes: empty -> No monthly fee", summary)

    def test_available_actions_hide_mutations_for_read_only_and_closed_tasks(self) -> None:
        self.assertEqual(_available_actions(review_state="queued", actor_role="admin"), ["approve", "reject", "edit_approve", "defer"])
        self.assertEqual(_available_actions(review_state="queued", actor_role="read_only"), [])
        self.assertEqual(_available_actions(review_state="approved", actor_role="admin"), ["edit_approve"])
        self.assertEqual(_available_actions(review_state="edited", actor_role="admin"), ["edit_approve"])
        self.assertEqual(_available_actions(review_state="rejected", actor_role="admin"), [])

    def test_build_validation_issues_merges_summary_items_with_fallback_codes(self) -> None:
        issues = _build_validation_issues(
            issue_items=[{"code": "required_field_missing", "severity": "error", "summary": "Missing standard rate."}],
            validation_issue_codes=["required_field_missing", "conflicting_evidence"],
            validation_status="error",
        )

        self.assertEqual(issues[0]["code"], "required_field_missing")
        self.assertEqual(issues[1]["code"], "conflicting_evidence")
        self.assertEqual(issues[1]["severity"], "error")

    def test_is_empty_review_value_handles_list_without_hash_error(self) -> None:
        self.assertTrue(_is_empty_review_value(None))
        self.assertTrue(_is_empty_review_value(""))
        self.assertFalse(_is_empty_review_value([]))
        self.assertFalse(_is_empty_review_value(["bonus_rate"]))

    def test_collect_model_execution_ids_keeps_stage_order_and_deduplicates(self) -> None:
        model_execution_ids = _collect_model_execution_ids(
            candidate_model_execution_id="modelexec-normalize-001",
            stage_metadata={
                "extraction_model_execution_id": "modelexec-extract-001",
                "normalization_model_execution_id": "modelexec-normalize-001",
                "validation_model_execution_id": "modelexec-validate-001",
            },
        )

        self.assertEqual(
            model_execution_ids,
            ["modelexec-extract-001", "modelexec-normalize-001", "modelexec-validate-001"],
        )

    def test_serialize_field_mapping_returns_trace_safe_shape(self) -> None:
        field_mapping = _serialize_field_mapping(
            {
                "source_field_name": "monthly_fee",
                "normalized_value": 0,
                "value_type": "decimal",
                "extraction_method": "table_parse",
                "extraction_confidence": 0.84,
                "evidence_chunk_id": "chunk-fee",
                "normalization_method": "heuristic_canonical_mapping",
            }
        )

        self.assertEqual(field_mapping["source_field_name"], "monthly_fee")
        self.assertEqual(field_mapping["normalized_value"], 0)
        self.assertEqual(field_mapping["extraction_confidence"], 0.84)

    def test_build_field_trace_groups_keeps_non_empty_list_values(self) -> None:
        groups = _build_field_trace_groups(
            candidate_payload={
                "bonus_rate_conditions": ["keep_balance", "new_deposit"],
                "monthly_fee": 0,
                "notes": "",
            },
            field_mapping_metadata={},
            evidence_links=[
                {
                    "field_name": "bonus_rate_conditions",
                    "evidence_chunk_id": "chunk-conditions",
                }
            ],
        )

        self.assertEqual([item["field_name"] for item in groups], ["bonus_rate_conditions", "monthly_fee"])
        self.assertEqual(groups[0]["value"], ["keep_balance", "new_deposit"])
        self.assertEqual(groups[0]["evidence_count"], 1)

    def test_record_evidence_trace_viewed_emits_review_audit_event(self) -> None:
        connection = _RecordingConnection()

        record_evidence_trace_viewed(
            connection,
            actor={"user_id": "usr-001", "role": "reviewer"},
            review_task_id="rt-001",
            run_id="run-001",
            candidate_id="cand-001",
            product_id="prod-001",
            request_id="req-001",
            ip_address="127.0.0.1",
            user_agent="unit-test",
            field_count=3,
            evidence_item_count=5,
        )

        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("evidence_trace_viewed", sql)
        self.assertEqual(params["target_id"], "rt-001")
        self.assertEqual(params["actor_role_snapshot"], "reviewer")
        self.assertIn('"field_count": 3', str(params["event_payload"]))


if __name__ == "__main__":
    unittest.main()
