from __future__ import annotations

from datetime import UTC, datetime
import json
from unittest import TestCase
from unittest.mock import patch

from api_service.review_ai_correction import (
    apply_review_ai_corrections,
    assess_review_ai_auto_approval,
    persist_review_ai_auto_approval_assessment,
)
from api_service.review_detail import ReviewTaskError


class _Cursor:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _RecordingConnection:
    def __init__(self, *, review_state="queued", execution_status="completed"):
        self.calls: list[tuple[str, dict]] = []
        self.row = {
            "review_task_id": "review-001",
            "candidate_id": "candidate-001",
            "run_id": "run-001",
            "product_id": None,
            "review_state": review_state,
            "candidate_state": "in_review",
            "product_name": "Example Savings",
            "candidate_payload": {
                "product_name": "Example Savings",
                "standard_rate": 2.5,
                "monthly_fee": 0.0,
            },
            "field_mapping_metadata": {
                "standard_rate": {"extraction_method": "regex", "normalized_value": 2.5},
            },
            "stage_name": "ai_verification",
            "execution_status": execution_status,
            "execution_metadata": {
                "review_task_id": "review-001",
                "candidate_id": "candidate-001",
                "verification_contract_version": "review-ai-verification-v19",
                "verification_result": {
                    "overall_status": "differences_found",
                    "fields": [
                        {
                            "field_name": "standard_rate",
                            "status": "mismatch",
                            "confidence": 0.97,
                            "rationale": "Current official rate.",
                            "evidence_quote": "Example Savings APY is 3.25%.",
                            "sources": [
                                {"url": "https://bank.example/rates", "title": "Official rates"},
                            ],
                            "can_apply": True,
                            "proposed_value": 3.25,
                        },
                    ],
                    "proposed_corrections": {"standard_rate": 3.25},
                },
            },
        }

    def execute(self, sql, params=None):
        normalized_sql = " ".join(str(sql).split())
        params = params or {}
        self.calls.append((normalized_sql, params))
        if "FROM review_task AS rt" in normalized_sql and "FOR UPDATE OF rt, nc, me" in normalized_sql:
            return _Cursor(self.row)
        return _Cursor()


class ReviewAiCorrectionTests(TestCase):
    def test_persists_auto_approval_assessment_in_model_execution_metadata(self):
        class _AssessmentConnection:
            def __init__(self):
                self.updated = None

            def execute(self, sql, params=None):
                normalized_sql = " ".join(str(sql).split())
                if normalized_sql.startswith("SELECT execution_metadata"):
                    return _Cursor({"execution_metadata": {"review_task_id": "review-001"}})
                if normalized_sql.startswith("UPDATE model_execution"):
                    self.updated = params
                return _Cursor()

        connection = _AssessmentConnection()
        assessment = {"eligible": True, "pass_rate": 0.8, "requested_field_count": 5}
        persist_review_ai_auto_approval_assessment(
            connection,
            model_execution_id="modelexec-001",
            assessment=assessment,
        )
        metadata = json.loads(connection.updated["execution_metadata"])
        self.assertEqual(metadata["review_task_id"], "review-001")
        self.assertEqual(metadata["auto_approval_assessment"], assessment)

    def test_auto_approval_rejects_eighty_percent_when_one_essential_is_unverified(self):
        source = [{"url": "https://bank.example/product", "title": "Official product"}]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "requested_field_names": [
                    "product_name",
                    "standard_rate",
                    "monthly_fee",
                    "minimum_balance",
                    "eligibility_text",
                ],
                "verification_result": {
                    "source_count": 1,
                    "proposed_corrections": {},
                    "applied_corrections": {"standard_rate": 3.25},
                    "fields": [
                        {"field_name": "product_name", "status": "match", "sources": source},
                        {
                            "field_name": "standard_rate",
                            "status": "mismatch",
                            "sources": source,
                            "applied": True,
                        },
                        {"field_name": "monthly_fee", "status": "match", "sources": source},
                        {"field_name": "minimum_balance", "status": "match", "sources": source},
                        {"field_name": "eligibility_text", "status": "unverified", "sources": []},
                    ],
                },
            },
        )
        self.assertFalse(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 0.8)
        self.assertEqual(assessment["passed_field_count"], 4)
        self.assertIn("verification_pass_rate_below_threshold", assessment["reason_codes"])

    def test_auto_approval_rejects_missing_identity_and_omitted_model_fields(self):
        source = [{"url": "https://bank.example/product", "title": "Official product"}]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "requested_field_names": ["product_name", "standard_rate", "monthly_fee", "minimum_balance"],
                "verification_result": {
                    "source_count": 1,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": "standard_rate", "status": "match", "sources": source},
                        {"field_name": "monthly_fee", "status": "match", "sources": source},
                        {"field_name": "minimum_balance", "status": "match", "sources": source},
                    ],
                },
            },
        )
        self.assertFalse(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 0.75)
        self.assertIn("product_identity_unverified", assessment["reason_codes"])
        self.assertIn("verification_pass_rate_below_threshold", assessment["reason_codes"])

    def test_auto_approval_uses_current_approval_fields_not_legacy_optional_denominator(self):
        source = [{"url": "https://bank.example/product", "title": "Official product"}]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "requested_field_names": ["product_name", "annual_fee", "description_short", "notes"],
                "approval_field_names": ["product_name", "annual_fee"],
                "hard_blocking_issue_codes": [],
                "verification_result": {
                    "source_count": 1,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": "product_name", "status": "match", "sources": source},
                        {"field_name": "annual_fee", "status": "match", "sources": source},
                        {"field_name": "description_short", "status": "unverified", "sources": []},
                        {"field_name": "notes", "status": "unverified", "sources": []},
                    ],
                },
            },
        )

        self.assertTrue(assessment["eligible"])
        self.assertEqual(assessment["requested_field_count"], 2)
        self.assertEqual(assessment["pass_rate"], 1.0)

    def test_auto_approval_accepts_exact_official_detail_h1_when_search_leaves_identity_unverified(self):
        source = [{"url": "https://bank.example/card", "title": "Official card"}]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "approval_field_names": ["product_name", "annual_fee"],
                "hard_blocking_issue_codes": [],
                "authoritative_identity_evidence": {
                    "verified": True,
                    "basis": "exact_official_detail_h1",
                    "source_url": "https://bank.example/card",
                },
                "allowed_domains": ["bank.example"],
                "verification_result": {
                    "source_count": 1,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": "product_name", "status": "unverified", "sources": []},
                        {"field_name": "annual_fee", "status": "match", "sources": source},
                    ],
                },
            },
        )

        self.assertTrue(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 1.0)
        self.assertEqual(
            assessment["product_identity_verification_basis"],
            "exact_official_detail_h1",
        )

    def test_auto_approval_reuses_exact_origin_fee_when_review_ai_abstains(self):
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "approval_field_names": ["product_name", "annual_fee"],
                "hard_blocking_issue_codes": [],
                "authoritative_identity_evidence": {
                    "verified": True,
                    "basis": "exact_official_detail_h1",
                    "source_url": "https://cards.bank.example/card",
                },
                "authoritative_field_evidence": {
                    "annual_fee": {
                        "verified": True,
                        "basis": "exact_official_detail_labeled_fee",
                        "source_url": "https://cards.bank.example/card",
                    }
                },
                "allowed_domains": ["bank.example"],
                "verification_result": {
                    "source_count": 0,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": "product_name", "status": "unverified", "sources": []},
                        {"field_name": "annual_fee", "status": "unverified", "sources": []},
                    ],
                },
            },
        )

        self.assertTrue(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 1.0)
        self.assertEqual(assessment["authoritative_origin_fields"], ["annual_fee"])
        self.assertNotIn("official_source_missing", assessment["reason_codes"])

    def test_auto_approval_reuses_exact_origin_lending_fields_when_review_ai_abstains(self):
        requested_fields = [
            "product_name",
            "interest_rate_summary",
            "loan_amount_text",
            "term_length_text",
        ]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "approval_field_names": requested_fields,
                "hard_blocking_issue_codes": [],
                "authoritative_identity_evidence": {
                    "verified": True,
                    "basis": "exact_official_detail_h1",
                    "source_url": "https://bank.example/personal-loans",
                },
                "authoritative_field_evidence": {
                    field_name: {
                        "verified": True,
                        "basis": "exact_official_detail_lending_comparison",
                        "source_url": "https://bank.example/personal-loans",
                    }
                    for field_name in requested_fields[1:]
                },
                "allowed_domains": ["bank.example"],
                "verification_result": {
                    "source_count": 0,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": field_name, "status": "unverified", "sources": []}
                        for field_name in requested_fields
                    ],
                },
            },
        )

        self.assertTrue(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 1.0)
        self.assertEqual(
            assessment["authoritative_origin_fields"],
            ["interest_rate_summary", "loan_amount_text", "term_length_text"],
        )

    def test_auto_approval_rejects_non_field_resolvable_hard_issue(self):
        source = [{"url": "https://bank.example/product", "title": "Official product"}]
        assessment = assess_review_ai_auto_approval(
            execution_status="completed",
            execution_metadata={
                "approval_field_names": ["product_name", "annual_fee"],
                "hard_blocking_issue_codes": ["ambiguous_product_boundary"],
                "verification_result": {
                    "source_count": 1,
                    "proposed_corrections": {},
                    "fields": [
                        {"field_name": "product_name", "status": "match", "sources": source},
                        {"field_name": "annual_fee", "status": "match", "sources": source},
                    ],
                },
            },
        )

        self.assertFalse(assessment["eligible"])
        self.assertIn("hard_validation_issue_unresolved", assessment["reason_codes"])

    def test_applies_verified_mismatch_without_changing_review_or_candidate_state(self):
        connection = _RecordingConnection()
        corrected_at = datetime(2026, 8, 1, 18, 0, tzinfo=UTC)
        with patch("api_service.review_ai_correction.utc_now", return_value=corrected_at):
            result = apply_review_ai_corrections(
                connection,
                review_task_id="review-001",
                model_execution_id="modelexec-001",
                actor={"actor_type": "system", "role": "admin"},
                request_context={"request_id": "batch-001", "user_agent": "test"},
            )

        self.assertTrue(result["applied"])
        self.assertEqual(result["review_state"], "queued")
        self.assertEqual(result["changed_fields"], ["standard_rate"])
        candidate_update = next(
            params for sql, params in connection.calls if sql.startswith("UPDATE normalized_candidate")
        )
        payload = json.loads(candidate_update["candidate_payload"])
        self.assertEqual(payload["standard_rate"], 3.25)
        mapping = json.loads(candidate_update["field_mapping_metadata"])["standard_rate"]
        self.assertEqual(mapping["extraction_method"], "review_ai_verification")
        self.assertEqual(mapping["model_execution_id"], "modelexec-001")
        self.assertEqual(mapping["ai_verification_sources"][0]["url"], "https://bank.example/rates")
        self.assertEqual(mapping["official_evidence_quote"], "Example Savings APY is 3.25%.")
        self.assertNotIn("candidate_state", candidate_update)

        task_update = next(params for sql, params in connection.calls if sql.startswith("UPDATE review_task"))
        self.assertEqual(task_update["review_task_id"], "review-001")
        execution_update = next(
            params for sql, params in connection.calls if sql.startswith("UPDATE model_execution")
        )
        execution_metadata = json.loads(execution_update["execution_metadata"])
        verification_result = execution_metadata["verification_result"]
        self.assertEqual(verification_result["proposed_corrections"], {})
        self.assertEqual(verification_result["applied_corrections"], {"standard_rate": 3.25})
        self.assertFalse(verification_result["fields"][0]["can_apply"])

        audit = next(params for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit["actor_type"], "system")
        self.assertEqual(audit["review_state"], "queued")
        self.assertEqual(audit["diff_summary"], "standard_rate: 2.5 -> 3.25")
        audit_payload = json.loads(audit["event_payload"])
        self.assertTrue(audit_payload["review_state_preserved"])
        self.assertFalse(audit_payload["canonical_product_mutated"])
        self.assertFalse(audit_payload["public_projection_mutated"])

    def test_ignores_correction_without_applyable_mismatch_and_source(self):
        connection = _RecordingConnection()
        verification = connection.row["execution_metadata"]["verification_result"]
        verification["fields"][0]["can_apply"] = False
        verification["fields"][0]["sources"] = []

        result = apply_review_ai_corrections(
            connection,
            review_task_id="review-001",
            model_execution_id="modelexec-001",
            actor={"actor_type": "system", "role": "admin"},
            request_context={"request_id": "batch-001"},
        )

        self.assertFalse(result["applied"])
        self.assertFalse(any(sql.startswith("UPDATE normalized_candidate") for sql, _ in connection.calls))
        self.assertFalse(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_does_not_restore_mixed_scope_gic_redeemability_suppression(self):
        connection = _RecordingConnection()
        verification = connection.row["execution_metadata"]["verification_result"]
        verification["fields"][0].update(
            {
                "field_name": "redeemable_flag",
                "proposed_value": True,
            }
        )
        verification["proposed_corrections"] = {"redeemable_flag": True}
        connection.row["field_mapping_metadata"]["redeemable_flag"] = {
            "normalized_value": None,
            "suppressed_reason": "mixed_account_scope_redeemability",
            "normalization_method": "gic_mixed_scope_safety",
        }

        result = apply_review_ai_corrections(
            connection,
            review_task_id="review-001",
            model_execution_id="modelexec-001",
            actor={"actor_type": "system", "role": "admin"},
            request_context={"request_id": "batch-001"},
        )

        self.assertFalse(result["applied"])
        self.assertEqual(result["changed_fields"], [])
        self.assertFalse(any(sql.startswith("UPDATE normalized_candidate") for sql, _ in connection.calls))
        self.assertFalse(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_ignores_correction_without_exact_evidence_quote(self):
        connection = _RecordingConnection()
        verification = connection.row["execution_metadata"]["verification_result"]
        verification["fields"][0]["evidence_quote"] = ""

        result = apply_review_ai_corrections(
            connection,
            review_task_id="review-001",
            model_execution_id="modelexec-001",
            actor={"actor_type": "system", "role": "admin"},
            request_context={"request_id": "batch-001"},
        )

        self.assertFalse(result["applied"])
        self.assertFalse(any(sql.startswith("UPDATE normalized_candidate") for sql, _ in connection.calls))
        self.assertFalse(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_rejects_closed_review_task(self):
        connection = _RecordingConnection(review_state="approved")
        with self.assertRaises(ReviewTaskError) as raised:
            apply_review_ai_corrections(
                connection,
                review_task_id="review-001",
                model_execution_id="modelexec-001",
                actor={"actor_type": "system", "role": "admin"},
                request_context={"request_id": "batch-001"},
            )
        self.assertEqual(raised.exception.code, "review_task_not_correctable")

    def test_rejects_verification_for_another_candidate(self):
        connection = _RecordingConnection()
        connection.row["execution_metadata"]["candidate_id"] = "candidate-other"
        with self.assertRaises(ReviewTaskError) as raised:
            apply_review_ai_corrections(
                connection,
                review_task_id="review-001",
                model_execution_id="modelexec-001",
                actor={"actor_type": "system", "role": "admin"},
                request_context={"request_id": "batch-001"},
            )
        self.assertEqual(raised.exception.code, "review_ai_verification_mismatch")
