from __future__ import annotations

import unittest

from api_service.review_diagnosis import build_review_diagnosis, build_review_field_items
from api_service.review_detail import (
    ReviewTaskError,
    _available_actions,
    _build_diff_summary,
    _build_field_trace_groups,
    _build_source_review_context,
    _build_validation_issues,
    _changed_field_names,
    _collect_model_execution_ids,
    _is_empty_review_value,
    _normalize_override_payload,
    _serialize_field_mapping,
    record_evidence_trace_viewed,
    record_evidence_trace_viewed_best_effort,
)


class _RecordingConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.calls.append((sql, params))


class _FailingAuditConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.rollback_called = False

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.calls.append((sql, params))
        if not sql.strip().upper().startswith("SET LOCAL"):
            raise TimeoutError("audit insert timed out")

    def rollback(self) -> None:
        self.rollback_called = True


class ReviewDetailTests(unittest.TestCase):
    def test_review_diagnosis_prioritizes_suspect_fields_and_direct_edit(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "mortgage_rate"],
            candidate_payload={
                "product_name": "Example Mortgage",
                "mortgage_rate": "Competitive mortgage rates help you find a flexible solution for your goals.",
            },
            validation_status="pass",
            validation_issue_codes=[],
        )

        self.assertEqual(diagnosis["category"], "suspect_fields")
        self.assertEqual(diagnosis["recommended_action"], "edit_approve")
        self.assertEqual(diagnosis["affected_fields"][0]["field_name"], "mortgage_rate")

    def test_review_diagnosis_flags_types_placeholders_and_term_conflicts(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "interest_rate", "credit_limit_text", "secured_flag", "notes"],
            candidate_payload={
                "product_name": "Home Equity Line of Credit",
                "interest_rate": "Prime plus a variable margin",
                "credit_limit_text": "Available credit RDS%rate_placeholder%",
                "secured_flag": "Document Residential Mortgages",
                "term_length_text": "Terms from 12 months to 96 months",
                "term_length_days": 30,
            },
            validation_status="pass",
            validation_issue_codes=[],
            product_type="line-of-credit",
        )

        self.assertEqual(diagnosis["category"], "suspect_fields")
        self.assertEqual(
            {item["issue_type"] for item in diagnosis["affected_fields"]},
            {"unresolved_placeholder", "invalid_type", "cross_field_conflict"},
        )

    def test_review_diagnosis_ignores_brand_suffix_when_checking_source_identity(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "mortgage_rate", "rate_type", "term_length_text"],
            candidate_payload={
                "product_name": "CIBC Fixed-Rate Closed Mortgage",
                "mortgage_rate": "Prime - 0.20%",
                "rate_type": "Fixed",
                "term_length_text": "5 years",
            },
            validation_status="pass",
            validation_issue_codes=[],
            product_type="mortgage",
            source_metadata={
                "discovery_metadata": {
                    "page_title": "CIBC Home Power Plan Mortgages | CIBC Mortgages",
                    "primary_heading": "CIBC Home Power Plan. Your all-in-one borrowing solution.",
                }
            },
        )

        self.assertEqual(diagnosis["category"], "suspect_fields")
        self.assertEqual(diagnosis["affected_fields"][0]["field_name"], "product_name")
        self.assertEqual(diagnosis["affected_fields"][0]["issue_type"], "source_identity_mismatch")

    def test_review_diagnosis_recommends_reject_for_editorial_source(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "mortgage_rate", "term_length_text"],
            candidate_payload={"product_name": "Mortgage refinancing"},
            validation_status="error",
            validation_issue_codes=["required_field_missing"],
            product_type="mortgage",
            source_metadata={
                "normalized_source_url": "https://www.examplebank.ca/mortgages/resource-centre/mortgage-refinancing.html"
            },
        )

        self.assertEqual(diagnosis["category"], "non_product_source")
        self.assertEqual(diagnosis["recommended_action"], "reject")

    def test_review_diagnosis_recommends_reject_for_mortgage_service_flow(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "mortgage_rate"],
            candidate_payload={"product_name": "Switch your mortgage", "mortgage_rate": 5.25},
            validation_status="pass",
            validation_issue_codes=[],
            product_type="mortgage",
            source_metadata={
                "normalized_source_url": "https://www.examplebank.ca/mortgages/switch-mortgage.html"
            },
        )

        self.assertEqual(diagnosis["category"], "non_product_source")
        self.assertEqual(diagnosis["recommended_action"], "reject")
        self.assertEqual(diagnosis["affected_fields"], [])

    def test_optional_expected_fields_do_not_force_edit(self) -> None:
        diagnosis = build_review_diagnosis(
            source_role="detail",
            expected_fields=["product_name", "annual_fee", "purchase_interest_rate", "notes", "application_method"],
            candidate_payload={"product_name": "Cash Back Card", "annual_fee": 0, "purchase_interest_rate": "20.99%"},
            validation_status="pass",
            validation_issue_codes=[],
            product_type="credit-card",
        )

        self.assertEqual(diagnosis["category"], "evidence_review")
        self.assertEqual(diagnosis["recommended_action"], "approve")

    def test_review_field_items_include_missing_expected_fields_first(self) -> None:
        items = build_review_field_items(
            expected_fields=["product_name", "standard_rate"],
            candidate_payload={"product_name": "Example GIC"},
            evidence_field_names=["product_name"],
            current_payload=None,
        )

        self.assertEqual(items[0]["field_name"], "standard_rate")
        self.assertTrue(items[0]["missing"])
        self.assertTrue(items[0]["editable"])

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

    def test_normalize_override_payload_enforces_canonical_rate_type(self) -> None:
        normalized = _normalize_override_payload(
            override_payload={"standard_rate": "3.30%"},
            base_payload={"standard_rate": None},
        )

        self.assertEqual(normalized, {"standard_rate": 3.3})

        with self.assertRaises(ReviewTaskError) as raised:
            _normalize_override_payload(
                override_payload={"standard_rate": "1 Year 3.30%, 5 Years 4.00%"},
                base_payload={"standard_rate": None},
            )
        self.assertEqual(raised.exception.code, "invalid_field_type")

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
        self.assertTrue(_is_empty_review_value([]))
        self.assertTrue(_is_empty_review_value({}))
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
                "field_contract_version": "2026-07-16",
                "canonical_value_type": "decimal",
                "canonical_unit": "currency_amount",
                "field_note": "Fee may be waived when the minimum balance is maintained.",
            }
        )

        self.assertEqual(field_mapping["source_field_name"], "monthly_fee")
        self.assertEqual(field_mapping["normalized_value"], 0)
        self.assertEqual(field_mapping["extraction_confidence"], 0.84)
        self.assertEqual(field_mapping["canonical_value_type"], "decimal")
        self.assertEqual(field_mapping["field_note"], "Fee may be waived when the minimum balance is maintained.")

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

    def test_build_field_trace_groups_prioritizes_requested_deposit_review_fields(self) -> None:
        groups = _build_field_trace_groups(
            candidate_payload={
                "notes": "Source note",
                "term_rate_table": [{"term_label": "12 months", "rate": 4.5}],
                "product_name": "BMO 1 Year GIC",
                "application_method": "Apply online or in branch.",
                "base_12_month_rate": 4.5,
            },
            field_mapping_metadata={},
            evidence_links=[],
        )

        self.assertEqual([item["field_name"] for item in groups[:4]], ["product_name", "base_12_month_rate", "application_method", "term_rate_table"])
        self.assertEqual(groups[1]["label"], "Base Rate, 12 Months")

    def test_build_source_review_context_exposes_actionable_discovery_and_missing_fields(self) -> None:
        context = _build_source_review_context(
            source_metadata={
                "discovery_role": "detail",
                "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                "discovery_metadata": {
                    "ai_predicted_role": "supporting_html",
                    "ai_parallel_score": 0.65,
                    "ai_reason_codes": ["not_product_detail"],
                    "ai_short_rationale": "This is a transfer support page.",
                    "page_evidence_score": 9,
                    "product_identity_match": False,
                    "selection_reason_codes": ["strong_page_evidence_detail_override"],
                },
            },
            candidate_payload={"product_name": "Online Banking", "monthly_fee": None},
        )

        self.assertEqual(context["discovery_role"], "detail")
        self.assertEqual(context["missing_expected_fields"], ["monthly_fee", "included_transactions"])
        self.assertEqual(context["discovery_assessment"]["ai_predicted_role"], "supporting_html")
        self.assertEqual(context["discovery_assessment"]["product_identity_match"], False)

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

    def test_record_evidence_trace_viewed_best_effort_rolls_back_audit_timeout(self) -> None:
        connection = _FailingAuditConnection()

        record_evidence_trace_viewed_best_effort(
            connection,
            actor={"user_id": "usr-001", "role": "reviewer"},
            review_task_id="rt-001",
            run_id="run-001",
            candidate_id="cand-001",
            product_id=None,
            request_id="req-001",
            ip_address="127.0.0.1",
            user_agent="unit-test",
            field_count=3,
            evidence_item_count=5,
            statement_timeout_ms=100,
        )

        self.assertEqual(len(connection.calls), 2)
        self.assertIn("SET LOCAL statement_timeout", connection.calls[0][0])
        self.assertTrue(connection.rollback_called)


if __name__ == "__main__":
    unittest.main()
