from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch

from api_service.candidate_auto_promotion import promote_auto_validated_candidates


class _Cursor:
    def __init__(self, payload: object = None) -> None:
        self.payload = payload

    def fetchone(self):
        if isinstance(self.payload, list):
            return self.payload[0] if self.payload else None
        return self.payload if isinstance(self.payload, dict) else None

    def fetchall(self):
        if isinstance(self.payload, list):
            return self.payload
        if isinstance(self.payload, dict):
            return [self.payload]
        return []


class _Connection:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _Cursor:
        self.calls.append((sql, params or {}))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _Cursor(self._responses.pop(0))


def _policy_rows() -> list[dict[str, object]]:
    return [
        {"policy_key": "AUTO_APPROVE_MIN_CONFIDENCE", "policy_value": {"value": 0.82}},
        {"policy_key": "FORCE_REVIEW_ISSUE_CODES", "policy_value": ["required_field_missing", "conflicting_evidence"]},
    ]


def _candidate_row(*, validation_issue_codes: list[str] | None = None) -> dict[str, object]:
    return {
        "candidate_id": "cand-001",
        "run_id": "run-001",
        "product_id": None,
        "country_code": "CA",
        "bank_code": "TD",
        "product_family": "deposit",
        "product_type": "savings",
        "subtype_code": "standard",
        "product_name": "TD Every Day Savings Account",
        "source_language": "en",
        "currency": "CAD",
        "candidate_state": "auto_validated",
        "validation_status": "pass",
        "validation_issue_codes": validation_issue_codes or [],
        "source_confidence": 0.94,
        "candidate_payload": {
            "product_name": "TD Every Day Savings Account",
            "monthly_fee": 0,
            "status": "active",
        },
        "discovery_role": "detail",
        "source_metadata": {},
    }


class CandidateAutoPromotionTests(unittest.TestCase):
    def test_pass_candidate_promotes_to_canonical_with_audit_and_refresh(self) -> None:
        decided_at = datetime(2026, 5, 13, 12, 0, tzinfo=UTC)
        connection = _Connection(
            [
                _policy_rows(),
                [_candidate_row()],
                None,
                None,
                [],
                None,
                None,
                None,
                None,
                None,
                [],
                None,
            ]
        )

        with patch("api_service.candidate_auto_promotion.utc_now", return_value=decided_at):
            result = promote_auto_validated_candidates(
                connection,
                run_id="run-001",
                request_context={"request_id": "req-auto-001"},
            )

        self.assertEqual(result["promoted_count"], 1)
        self.assertEqual(result["skipped_count"], 0)

        product_version_call = next(params for sql, params in connection.calls if "INSERT INTO product_version" in sql)
        self.assertEqual(product_version_call["approved_candidate_id"], "cand-001")

        change_event_call = next(params for sql, params in connection.calls if "INSERT INTO change_event" in sql)
        self.assertEqual(change_event_call["event_type"], "New")
        self.assertIsNone(change_event_call["review_task_id"])

        candidate_update_call = next(params for sql, params in connection.calls if "UPDATE normalized_candidate" in sql)
        self.assertEqual(candidate_update_call["candidate_id"], "cand-001")
        self.assertEqual(candidate_update_call["product_name"], "TD Every Day Savings Account")

        audit_call = next(params for sql, params in connection.calls if "candidate_auto_promoted" in sql)
        self.assertEqual(audit_call["target_id"], "cand-001")
        self.assertEqual(audit_call["product_id"], result["promoted_items"][0]["product_id"])
        self.assertIn('"auto_approve_min_confidence": 0.82', str(audit_call["event_payload"]))

        refresh_call = next(params for sql, params in connection.calls if "INSERT INTO aggregate_refresh_request" in sql)
        self.assertEqual(refresh_call["trigger_reason"], "auto_promotion")
        self.assertIn('"candidate_ids": ["cand-001"]', str(refresh_call["request_metadata"]))

    def test_approval_supersedes_older_same_source_review_with_audit(self) -> None:
        candidate = _candidate_row()
        candidate["source_document_id"] = "src-detail-001"
        connection = _Connection(
            [
                _policy_rows(),
                [candidate],
                None,
                None,
                None,
                [],
                None,
                None,
                None,
                [
                    {
                        "candidate_id": "cand-stale",
                        "run_id": "run-stale",
                        "previous_candidate_state": "in_review",
                        "review_task_id": "review-stale",
                        "previous_review_state": "queued",
                    }
                ],
                None,
                None,
                None,
            ]
        )

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_items"][0]["superseded_review_count"], 1)
        supersede_call = next(params for sql, params in connection.calls if "superseded_candidates AS" in sql)
        self.assertEqual(supersede_call["approved_candidate_id"], "cand-001")
        audit_call = next(params for sql, params in connection.calls if "stale_review_auto_superseded" in sql)
        self.assertEqual(audit_call["candidate_id"], "cand-stale")
        self.assertEqual(audit_call["review_task_id"], "review-stale")
        self.assertIn('"approved_candidate_id": "cand-001"', str(audit_call["event_payload"]))

    def test_force_review_issue_candidate_is_not_promoted(self) -> None:
        connection = _Connection(
            [
                _policy_rows(),
                [_candidate_row(validation_issue_codes=["conflicting_evidence"])],
                None,
                {"review_task_id": "review-auto-001"},
                None,
            ]
        )

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "force_review_issue_code")
        self.assertEqual(result["skipped_items"][0]["action"], "queued_for_review")
        self.assertFalse(any("INSERT INTO canonical_product" in sql for sql, _params in connection.calls))
        review_insert_call = next(params for sql, params in connection.calls if "INSERT INTO review_task" in sql)
        self.assertEqual(review_insert_call["candidate_id"], "cand-001")
        self.assertEqual(review_insert_call["queue_reason_code"], "force_review_issue_code")
        audit_call = next(params for sql, params in connection.calls if "candidate_auto_promotion_skipped" in sql)
        self.assertEqual(audit_call["new_state"], "in_review")
        self.assertEqual(audit_call["review_task_id"], "review-auto-001")

    def test_non_product_page_title_candidate_is_not_promoted(self) -> None:
        candidate = _candidate_row()
        candidate["product_name"] = "Save smarter with our savings calculator"
        connection = _Connection(
            [
                _policy_rows(),
                [candidate],
                None,
                None,
            ]
        )

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "non_product_page_title")
        self.assertEqual(result["skipped_items"][0]["action"], "rejected")
        self.assertFalse(any("INSERT INTO canonical_product" in sql for sql, _params in connection.calls))
        candidate_update_call = next(params for sql, params in connection.calls if "UPDATE normalized_candidate" in sql)
        self.assertEqual(candidate_update_call["candidate_id"], "cand-001")
        self.assertEqual(candidate_update_call["reason_code"], "non_product_page_title")
        audit_call = next(params for sql, params in connection.calls if "candidate_auto_promotion_skipped" in sql)
        self.assertEqual(audit_call["new_state"], "rejected")

    def test_multi_product_family_candidate_is_queued_before_canonical_promotion(self) -> None:
        candidate = _candidate_row()
        candidate["source_metadata"] = {
            "discovery_metadata": {"page_evidence_reason_codes": ["multi_product_family_overview"]}
        }
        connection = _Connection(
            [_policy_rows(), [candidate], None, {"review_task_id": "review-boundary"}, None]
        )

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "ambiguous_product_boundary")
        self.assertEqual(result["skipped_items"][0]["action"], "queued_for_review")
        self.assertFalse(any("INSERT INTO canonical_product" in sql for sql, _params in connection.calls))

    def test_non_product_service_source_is_rejected_before_canonical_promotion(self) -> None:
        candidate = _candidate_row()
        candidate["source_metadata"] = {
            "discovery_metadata": {"page_evidence_reason_codes": ["non_product_service_flow"]}
        }
        connection = _Connection([_policy_rows(), [candidate], None, None])

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "non_product_service_flow")
        self.assertEqual(result["skipped_items"][0]["action"], "rejected")

    def test_rate_cta_candidate_name_is_not_promoted(self) -> None:
        candidate = _candidate_row()
        candidate["product_name"] = "See today's GIC rates"
        connection = _Connection([_policy_rows(), [candidate], None, None])

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "non_product_page_title")

    def test_supporting_source_candidate_is_rejected_before_canonical_promotion(self) -> None:
        candidate = _candidate_row()
        candidate["discovery_role"] = "linked_pdf"
        connection = _Connection([_policy_rows(), [candidate], None, None])

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "non_detail_source_role")
        self.assertFalse(any("INSERT INTO canonical_product" in sql for sql, _params in connection.calls))
        audit_call = next(params for sql, params in connection.calls if "candidate_auto_promotion_skipped" in sql)
        self.assertEqual(audit_call["new_state"], "rejected")
        self.assertIn('"discovery_role": "linked_pdf"', str(audit_call["event_payload"]))

    def test_missing_source_role_is_queued_instead_of_published(self) -> None:
        candidate = _candidate_row()
        candidate["discovery_role"] = None
        connection = _Connection([_policy_rows(), [candidate], None, {"review_task_id": "review-role"}, None])

        result = promote_auto_validated_candidates(connection, run_id="run-001")

        self.assertEqual(result["promoted_count"], 0)
        self.assertEqual(result["skipped_items"][0]["skip_reason"], "source_role_missing")
        self.assertEqual(result["skipped_items"][0]["action"], "queued_for_review")


if __name__ == "__main__":
    unittest.main()
