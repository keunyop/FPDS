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
                "verification_contract_version": "review-ai-verification-v1",
                "verification_result": {
                    "overall_status": "differences_found",
                    "fields": [
                        {
                            "field_name": "standard_rate",
                            "status": "mismatch",
                            "confidence": 0.97,
                            "rationale": "Current official rate.",
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

    def test_auto_approval_accepts_exactly_eighty_percent_with_verified_identity(self):
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
        self.assertTrue(assessment["eligible"])
        self.assertEqual(assessment["pass_rate"], 0.8)
        self.assertEqual(assessment["passed_field_count"], 4)

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
