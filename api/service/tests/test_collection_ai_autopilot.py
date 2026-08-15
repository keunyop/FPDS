from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from api_service.collection_ai_autopilot import (
    _load_latest_verification_execution,
    load_active_collection_review_task_ids,
    load_collection_ai_autopilot_policy,
    remediate_collection_review_task,
)


class _Cursor:
    def __init__(self, *, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _QueryConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(str(sql).split()), params or {}))
        return _Cursor(rows=self.rows)


def _detail():
    return {
        "review_task": {
            "review_task_id": "review-001",
            "candidate_id": "candidate-001",
            "run_id": "run-001",
            "review_state": "queued",
        },
        "candidate": {"product_name": "Example Mortgage"},
    }


def _us_savings_detail(*, monthly_fee: float):
    detail = _detail()
    detail["candidate"].update(
        {
            "country_code": "US",
            "product_type": "savings",
            "candidate_payload": {
                "standard_rate": 3.2,
                "monthly_fee": monthly_fee,
                "minimum_balance": 1500,
            },
        }
    )
    return detail


class CollectionAiAutopilotTests(TestCase):
    def test_reuses_only_current_essential_field_contract_execution(self):
        connection = _QueryConnection([])

        self.assertIsNone(
            _load_latest_verification_execution(connection, review_task_id="review-001")
        )

        sql, params = connection.calls[0]
        self.assertEqual(params, {"review_task_id": "review-001"})
        self.assertIn("review-ai-verification-v17", sql)
        self.assertIn("execution_status = 'completed'", sql)
        self.assertIn("interval '24 hours'", sql)

    def test_policy_defaults_enable_low_touch_review_and_bounds_values(self):
        connection = _QueryConnection(
            [
                {
                    "policy_key": "COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE",
                    "policy_value": {"value": 1.5},
                },
                {
                    "policy_key": "COLLECTION_AI_REVIEW_AUTOPILOT_MAX_CANDIDATES",
                    "policy_value": {"value": 5000},
                },
            ]
        )

        policy = load_collection_ai_autopilot_policy(connection)

        self.assertTrue(policy["enabled"])
        self.assertEqual(policy["approval_threshold"], 1.0)
        self.assertEqual(policy["max_candidates"], 1000)

    def test_loads_only_bounded_active_detail_review_ids_for_run(self):
        connection = _QueryConnection(
            [{"review_task_id": "review-001"}, {"review_task_id": "review-002"}]
        )

        result = load_active_collection_review_task_ids(connection, run_id="run-001", limit=5000)

        self.assertEqual(result, ["review-001", "review-002"])
        sql, params = connection.calls[0]
        self.assertEqual(params, {"run_id": "run-001", "limit": 1000})
        self.assertIn("hub_page_not_detail", sql)

    def test_verifies_corrects_assesses_and_approves_eligible_review(self):
        first_execution = {
            "model_execution_id": "modelexec-001",
            "execution_status": "completed",
            "execution_metadata": {"verification_result": {}},
        }
        corrected_execution = {
            "model_execution_id": "modelexec-001",
            "execution_status": "completed",
            "execution_metadata": {"verification_result": {"applied_corrections": {"mortgage_rate": 4.25}}},
        }
        assessment = {
            "eligible": True,
            "threshold": 0.8,
            "requested_field_count": 5,
            "passed_field_count": 4,
            "pass_rate": 0.8,
            "product_identity_verified": True,
            "reason_codes": [],
        }
        connection = object()
        with (
            patch("api_service.collection_ai_autopilot.load_review_task_detail", return_value=_detail()),
            patch("api_service.collection_ai_autopilot._load_latest_verification_execution", return_value=None),
            patch(
                "api_service.collection_ai_autopilot.run_review_ai_verification",
                return_value={
                    "ok": True,
                    "ai_verification": {"latest_attempt": {"model_execution_id": "modelexec-001"}},
                },
            ) as verify,
            patch(
                "api_service.collection_ai_autopilot._load_verification_execution",
                side_effect=[first_execution, corrected_execution],
            ),
            patch(
                "api_service.collection_ai_autopilot.apply_review_ai_corrections",
                return_value={"applied": True, "changed_fields": ["mortgage_rate"]},
            ) as correct,
            patch(
                "api_service.collection_ai_autopilot.assess_review_ai_auto_approval",
                return_value=assessment,
            ) as assess,
            patch("api_service.collection_ai_autopilot.persist_review_ai_auto_approval_assessment") as persist,
            patch(
                "api_service.collection_ai_autopilot.apply_review_decision",
                return_value={
                    "review_task_id": "review-001",
                    "review_state": "approved",
                    "country_code": "CA",
                    "product_id": "product-001",
                    "product_version_id": "version-001",
                    "change_event_types": ["New"],
                },
            ) as decide,
            patch(
                "api_service.collection_ai_autopilot.queue_review_aggregate_refresh_request",
                return_value={"aggregate_refresh_request_id": "aggreq-001"},
            ) as queue_refresh,
        ):
            result = remediate_collection_review_task(
                connection,
                review_task_id="review-001",
                approval_threshold=0.8,
                request_context={"request_id": "req-001"},
            )

        self.assertTrue(result["approved"])
        self.assertEqual(result["changed_fields"], ["mortgage_rate"])
        verify.assert_called_once()
        correct.assert_called_once()
        assess.assert_called_once()
        persist.assert_called_once_with(
            connection,
            model_execution_id="modelexec-001",
            assessment=assessment,
        )
        approval_actor = decide.call_args.kwargs["actor"]
        self.assertEqual(approval_actor["actor_type"], "system")
        self.assertEqual(approval_actor["ai_model_execution_id"], "modelexec-001")
        self.assertEqual(approval_actor["ai_auto_approval_assessment"], assessment)
        queue_refresh.assert_called_once()

    def test_ineligible_assessment_keeps_review_without_approval(self):
        assessment = {
            "eligible": False,
            "pass_rate": 0.6,
            "reason_codes": ["verification_pass_rate_below_threshold"],
        }
        execution = {
            "model_execution_id": "modelexec-001",
            "execution_status": "completed",
            "execution_metadata": {
                "approval_field_names": ["product_name"],
                "auto_approval_assessment": assessment,
            },
        }
        with (
            patch("api_service.collection_ai_autopilot.load_review_task_detail", return_value=_detail()),
            patch("api_service.collection_ai_autopilot._load_latest_verification_execution", return_value=execution),
            patch("api_service.collection_ai_autopilot.run_review_ai_verification") as verify,
            patch("api_service.collection_ai_autopilot.apply_review_decision") as decide,
        ):
            result = remediate_collection_review_task(
                object(),
                review_task_id="review-001",
                approval_threshold=0.8,
                request_context={"request_id": "req-001"},
            )

        self.assertFalse(result["approved"])
        self.assertEqual(result["status"], "review_retained")
        self.assertTrue(result["reused_verification"])
        verify.assert_not_called()
        decide.assert_not_called()

    def test_retains_review_when_correction_introduces_missing_conditional_field(self):
        first_execution = {
            "model_execution_id": "modelexec-001",
            "execution_status": "completed",
            "execution_metadata": {"verification_result": {}},
        }
        corrected_execution = {
            "model_execution_id": "modelexec-001",
            "execution_status": "completed",
            "execution_metadata": {"verification_result": {}},
        }
        assessment = {
            "eligible": True,
            "threshold": 1.0,
            "requested_field_count": 4,
            "passed_field_count": 4,
            "pass_rate": 1.0,
            "product_identity_verified": True,
            "reason_codes": [],
        }
        connection = object()
        with (
            patch(
                "api_service.collection_ai_autopilot.load_review_task_detail",
                side_effect=[
                    _us_savings_detail(monthly_fee=0),
                    _us_savings_detail(monthly_fee=12),
                ],
            ),
            patch("api_service.collection_ai_autopilot._load_latest_verification_execution", return_value=None),
            patch(
                "api_service.collection_ai_autopilot.run_review_ai_verification",
                return_value={
                    "ok": True,
                    "ai_verification": {"latest_attempt": {"model_execution_id": "modelexec-001"}},
                },
            ),
            patch(
                "api_service.collection_ai_autopilot._load_verification_execution",
                side_effect=[first_execution, corrected_execution],
            ),
            patch(
                "api_service.collection_ai_autopilot.apply_review_ai_corrections",
                return_value={"applied": True, "changed_fields": ["monthly_fee"]},
            ),
            patch(
                "api_service.collection_ai_autopilot.assess_review_ai_auto_approval",
                return_value=assessment,
            ),
            patch("api_service.collection_ai_autopilot.persist_review_ai_auto_approval_assessment") as persist,
            patch("api_service.collection_ai_autopilot.apply_review_decision") as decide,
        ):
            result = remediate_collection_review_task(
                connection,
                review_task_id="review-001",
                approval_threshold=1.0,
                request_context={"request_id": "req-001"},
            )

        self.assertFalse(result["approved"])
        self.assertEqual(result["status"], "review_retained")
        self.assertEqual(result["changed_fields"], ["monthly_fee"])
        self.assertEqual(
            result["assessment"]["reason_codes"],
            ["essential_comparison_fields_missing_after_correction"],
        )
        self.assertEqual(
            result["assessment"]["missing_comparison_fields"],
            ["fee_waiver_condition"],
        )
        self.assertEqual(persist.call_count, 2)
        decide.assert_not_called()
