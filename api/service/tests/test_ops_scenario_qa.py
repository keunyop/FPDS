from __future__ import annotations

from datetime import UTC, datetime
import unittest

from api_service.audit_log import load_audit_log_list, normalize_audit_log_filters
from api_service.change_history import load_change_history_list, normalize_change_history_filters
from api_service.review_detail import ReviewRequestContext, apply_review_decision
from api_service.run_status import load_run_status_detail


class _QueuedCursor:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def fetchone(self) -> dict[str, object] | None:
        if isinstance(self.payload, list):
            return self.payload[0] if self.payload else None
        return self.payload if isinstance(self.payload, dict) else None

    def fetchall(self) -> list[dict[str, object]]:
        if isinstance(self.payload, list):
            return self.payload
        if isinstance(self.payload, dict):
            return [self.payload]
        return []


class _QueuedConnection:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> _QueuedCursor:
        self.calls.append((sql, params))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _QueuedCursor(self._responses.pop(0))


class OpsScenarioQATests(unittest.TestCase):
    def test_review_edit_approve_emits_change_and_audit_side_effects(self) -> None:
        decided_at = datetime(2026, 4, 13, 23, 30, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "review_task_id": "rt-001",
                    "candidate_id": "cand-001",
                    "run_id": "run-001",
                    "product_id": "prod-001",
                    "review_state": "queued",
                    "queue_reason_code": "manual_sampling_review",
                    "country_code": "CA",
                    "bank_code": "TD",
                    "product_family": "deposit",
                    "product_type": "savings",
                    "subtype_code": "high_interest",
                    "product_name": "TD Every Day Savings Account",
                    "source_language": "en",
                    "currency": "CAD",
                    "candidate_payload": {
                        "product_name": "TD Every Day Savings Account",
                        "monthly_fee": 5,
                        "notes": None,
                        "status": "active",
                    },
                },
                {
                    "product_id": "prod-001",
                    "status": "active",
                    "current_version_no": 2,
                    "product_name": "TD Every Day Savings Account",
                    "product_type": "savings",
                    "subtype_code": "high_interest",
                    "last_verified_at": decided_at,
                    "last_changed_at": decided_at,
                    "normalized_payload": {
                        "product_name": "TD Every Day Savings Account",
                        "monthly_fee": 5,
                        "notes": None,
                        "status": "active",
                    },
                },
                None,
                None,
                [
                    {
                        "evidence_chunk_id": "chunk-name-001",
                        "source_document_id": "src-001",
                        "field_name": "product_name",
                        "candidate_value": "TD Every Day Savings Account",
                        "citation_confidence": 0.94,
                    }
                ],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )

        from unittest.mock import patch

        with patch("api_service.review_detail.utc_now", return_value=decided_at):
            result = apply_review_decision(
                connection,
                review_task_id="rt-001",
                action_type="edit_approve",
                actor={"user_id": "usr-001", "role": "admin"},
                reason_code="evidence_clarified",
                reason_text="Corrected the monthly fee after checking the trace.",
                override_payload={"monthly_fee": 0, "notes": "No monthly fee"},
                context=ReviewRequestContext(
                    request_id="req-001",
                    ip_address="127.0.0.1",
                    user_agent="ops-scenario-test",
                ),
            )

        self.assertEqual(result["review_task_id"], "rt-001")
        self.assertEqual(result["review_state"], "edited")
        self.assertEqual(result["product_id"], "prod-001")
        self.assertEqual(result["change_event_types"], ["Updated", "ManualOverride"])
        self.assertFalse(result["already_applied"])

        change_event_calls = [
            params
            for sql, params in connection.calls
            if "INSERT INTO change_event" in sql
        ]
        self.assertEqual([params["event_type"] for params in change_event_calls], ["Updated", "ManualOverride"])

        audit_calls = [
            (sql, params)
            for sql, params in connection.calls
            if "INSERT INTO audit_event" in sql
        ]
        self.assertEqual(
            [
                "manual_override_recorded" if "'manual_override_recorded'" in sql else str(params["event_type"])
                for sql, params in audit_calls
            ],
            ["manual_override_recorded", "review_task_edited"],
        )
        self.assertEqual(audit_calls[1][1]["review_task_id"], "rt-001")
        self.assertEqual(audit_calls[1][1]["run_id"], "run-001")

        review_decision_call = next(
            params
            for sql, params in connection.calls
            if "INSERT INTO review_decision" in sql
        )
        self.assertEqual(review_decision_call["action_type"], "edit_approve")
        self.assertIn("Monthly Fee: 5 -> 0", str(review_decision_call["diff_summary"]))
        self.assertIn("Notes: empty -> No monthly fee", str(review_decision_call["diff_summary"]))

    def test_review_edit_approve_updates_canonical_product_name_from_override(self) -> None:
        decided_at = datetime(2026, 4, 13, 23, 30, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "review_task_id": "rt-001",
                    "candidate_id": "cand-001",
                    "run_id": "run-001",
                    "product_id": "prod-001",
                    "review_state": "queued",
                    "queue_reason_code": "manual_sampling_review",
                    "country_code": "CA",
                    "bank_code": "TD",
                    "product_family": "deposit",
                    "product_type": "savings",
                    "subtype_code": "high_interest",
                    "product_name": "TD Every Day Savings Account",
                    "source_language": "en",
                    "currency": "CAD",
                    "candidate_payload": {
                        "product_name": "TD Every Day Savings Account",
                        "monthly_fee": 5,
                        "status": "active",
                    },
                },
                {
                    "product_id": "prod-001",
                    "status": "active",
                    "current_version_no": 2,
                    "product_name": "TD Every Day Savings Account",
                    "product_type": "savings",
                    "subtype_code": "high_interest",
                    "last_verified_at": decided_at,
                    "last_changed_at": decided_at,
                    "normalized_payload": {
                        "product_name": "TD Every Day Savings Account",
                        "monthly_fee": 5,
                        "status": "active",
                    },
                },
                None,
                None,
                [],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )

        from unittest.mock import patch

        with patch("api_service.review_detail.utc_now", return_value=decided_at):
            result = apply_review_decision(
                connection,
                review_task_id="rt-001",
                action_type="edit_approve",
                actor={"user_id": "usr-001", "role": "admin"},
                reason_code="manual_override",
                reason_text="Aligned the approved product name with reviewer guidance.",
                override_payload={"product_name": " TD Every Day Savings Plus "},
                context=ReviewRequestContext(
                    request_id="req-001",
                    ip_address="127.0.0.1",
                    user_agent="ops-scenario-test",
                ),
            )

        self.assertEqual(result["product_id"], "prod-001")
        candidate_update_call = next(
            params
            for sql, params in connection.calls
            if "UPDATE normalized_candidate" in sql
        )
        self.assertEqual(candidate_update_call["product_name"], "TD Every Day Savings Plus")
        self.assertIn('"product_name": "TD Every Day Savings Plus"', str(candidate_update_call["candidate_payload"]))

        canonical_update_call = next(
            params
            for sql, params in connection.calls
            if "UPDATE canonical_product" in sql
            and "product_name = %(product_name)s" in sql
        )
        self.assertEqual(canonical_update_call["product_name"], "TD Every Day Savings Plus")

        review_decision_call = next(
            params
            for sql, params in connection.calls
            if "INSERT INTO review_decision" in sql
        )
        self.assertIn("Product Name: TD Every Day Savings Account -> TD Every Day Savings Plus", str(review_decision_call["diff_summary"]))
        self.assertIn('"product_name": "TD Every Day Savings Plus"', str(review_decision_call["override_payload"]))

    def test_approved_review_can_be_reopened_with_edit_approve(self) -> None:
        decided_at = datetime(2026, 4, 20, 13, 5, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "review_task_id": "rt-002",
                    "candidate_id": "cand-002",
                    "run_id": "run-002",
                    "product_id": "prod-002",
                    "review_state": "approved",
                    "queue_reason_code": "manual_sampling_review",
                    "country_code": "CA",
                    "bank_code": "BMO",
                    "product_family": "deposit",
                    "product_type": "chequing",
                    "subtype_code": None,
                    "product_name": "Benefits",
                    "source_language": "en",
                    "currency": "CAD",
                    "candidate_payload": {
                        "product_name": "Benefits",
                        "monthly_fee": 16.95,
                        "status": "active",
                    },
                },
                {
                    "product_id": "prod-002",
                    "status": "active",
                    "current_version_no": 3,
                    "product_name": "Benefits",
                    "product_type": "chequing",
                    "subtype_code": None,
                    "last_verified_at": decided_at,
                    "last_changed_at": decided_at,
                    "normalized_payload": {
                        "product_name": "Benefits",
                        "monthly_fee": 16.95,
                        "status": "active",
                    },
                },
                None,
                None,
                [],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )

        from unittest.mock import patch

        with patch("api_service.review_detail.utc_now", return_value=decided_at):
            result = apply_review_decision(
                connection,
                review_task_id="rt-002",
                action_type="edit_approve",
                actor={"user_id": "usr-001", "role": "admin"},
                reason_code="manual_override",
                reason_text="Reopened approved task to correct the product name.",
                override_payload={"product_name": "Plus Chequing Account"},
                context=ReviewRequestContext(
                    request_id="req-002",
                    ip_address="127.0.0.1",
                    user_agent="ops-scenario-test",
                ),
            )

        self.assertEqual(result["review_task_id"], "rt-002")
        self.assertEqual(result["review_state"], "edited")
        review_task_update_call = next(
            params
            for sql, params in connection.calls
            if "UPDATE review_task" in sql
        )
        self.assertEqual(review_task_update_call["review_state"], "edited")
        product_version_insert_call = next(
            params
            for sql, params in connection.calls
            if "INSERT INTO product_version" in sql
        )
        self.assertIsNone(product_version_insert_call["approved_candidate_id"])

    def test_edited_review_can_be_reopened_with_edit_approve(self) -> None:
        decided_at = datetime(2026, 4, 20, 13, 20, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "review_task_id": "rt-003",
                    "candidate_id": "cand-003",
                    "run_id": "run-003",
                    "product_id": "prod-003",
                    "review_state": "edited",
                    "queue_reason_code": "manual_sampling_review",
                    "country_code": "CA",
                    "bank_code": "BMO",
                    "product_family": "deposit",
                    "product_type": "chequing",
                    "subtype_code": None,
                    "product_name": "Plus Chequing Account",
                    "source_language": "en",
                    "currency": "CAD",
                    "candidate_payload": {
                        "product_name": "Plus Chequing Account",
                        "monthly_fee": 16.95,
                        "status": "active",
                    },
                },
                {
                    "product_id": "prod-003",
                    "status": "active",
                    "current_version_no": 4,
                    "product_name": "Plus Chequing Account",
                    "product_type": "chequing",
                    "subtype_code": None,
                    "last_verified_at": decided_at,
                    "last_changed_at": decided_at,
                    "normalized_payload": {
                        "product_name": "Plus Chequing Account",
                        "monthly_fee": 16.95,
                        "status": "active",
                    },
                },
                None,
                None,
                [],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )

        from unittest.mock import patch

        with patch("api_service.review_detail.utc_now", return_value=decided_at):
            result = apply_review_decision(
                connection,
                review_task_id="rt-003",
                action_type="edit_approve",
                actor={"user_id": "usr-001", "role": "admin"},
                reason_code="manual_override",
                reason_text="Applied a second correction after approval.",
                override_payload={"monthly_fee": 14.95},
                context=ReviewRequestContext(
                    request_id="req-003",
                    ip_address="127.0.0.1",
                    user_agent="ops-scenario-test",
                ),
            )

        self.assertEqual(result["review_task_id"], "rt-003")
        self.assertEqual(result["review_state"], "edited")
        review_task_update_call = next(
            params
            for sql, params in connection.calls
            if "UPDATE review_task" in sql
        )
        self.assertEqual(review_task_update_call["review_state"], "edited")
        product_version_insert_call = next(
            params
            for sql, params in connection.calls
            if "INSERT INTO product_version" in sql
        )
        self.assertIsNone(product_version_insert_call["approved_candidate_id"])

    def test_change_history_links_review_decision_to_manual_override_audit(self) -> None:
        connection = _QueuedConnection(
            [
                {"total_items": 1, "affected_product_count": 1},
                [{"event_type": "ManualOverride", "item_count": 1}],
                [
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
                        "detected_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                        "bank_code": "TD",
                        "bank_name": "TD Bank",
                        "product_name": "TD Every Day Savings Account",
                        "product_type": "savings",
                        "subtype_code": "high_interest",
                        "review_state": "edited",
                        "review_action_type": "edit_approve",
                        "review_reason_code": "evidence_clarified",
                        "review_reason_text": "Corrected the monthly fee after checking the trace.",
                        "review_diff_summary": "Monthly Fee: 5 -> 0; Notes: empty -> No monthly fee",
                        "review_decided_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                        "decision_actor_user_id": "usr-001",
                        "actor_display_name": "Admin Operator",
                        "actor_email": "admin@example.com",
                        "actor_role": "admin",
                        "run_type": "validation_routing",
                        "run_state": "completed",
                        "correlation_id": "corr-001",
                        "audit_event_id": "audit-001",
                        "audit_diff_summary": "Manual override fields: monthly_fee, notes",
                        "audit_occurred_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                        "audit_actor_id": "usr-001",
                        "audit_actor_display_name": "Admin Operator",
                        "audit_actor_email": "admin@example.com",
                        "audit_actor_role": "admin",
                    }
                ],
            ]
        )
        filters = normalize_change_history_filters(
            product_id=None,
            bank_code="td",
            product_type="savings",
            change_type="ManualOverride",
            changed_from=None,
            changed_to=None,
            search="rt-001",
            sort_by="detected_at",
            sort_order="desc",
            page=1,
            page_size=20,
        )

        payload = load_change_history_list(connection, filters=filters)

        self.assertEqual(payload["summary"]["manual_override_items"], 1)
        self.assertEqual(payload["items"][0]["review_context"]["review_task_id"], "rt-001")
        self.assertEqual(payload["items"][0]["review_context"]["action_type"], "edit_approve")
        self.assertEqual(payload["items"][0]["audit_context"]["audit_event_id"], "audit-001")
        self.assertEqual(payload["items"][0]["run_context"]["run_id"], "run-001")

    def test_audit_log_and_run_detail_keep_operator_drilldown_context(self) -> None:
        audit_connection = _QueuedConnection(
            [
                {"total_items": 2},
                [{"event_category": "review", "item_count": 2}],
                [{"actor_type": "user", "item_count": 2}],
                [
                    {
                        "audit_event_id": "audit-002",
                        "event_category": "review",
                        "event_type": "review_task_edited",
                        "occurred_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                        "actor_type": "user",
                        "actor_id": "usr-001",
                        "actor_role_snapshot": "admin",
                        "target_type": "review_task",
                        "target_id": "rt-001",
                        "target_display_name": "TD Every Day Savings Account",
                        "previous_state": "queued",
                        "new_state": "edited",
                        "reason_code": "evidence_clarified",
                        "reason_text": "Corrected the monthly fee after checking the trace.",
                        "run_id": "run-001",
                        "candidate_id": "cand-001",
                        "review_task_id": "rt-001",
                        "product_id": "prod-001",
                        "publish_item_id": None,
                        "request_id": "req-001",
                        "diff_summary": "Monthly Fee: 5 -> 0; Notes: empty -> No monthly fee",
                        "source_ref": None,
                        "ip_address": "127.0.0.1",
                        "user_agent": "ops-scenario-test",
                        "retention_class": "standard",
                        "event_payload": {"changed_fields": ["monthly_fee", "notes"]},
                        "actor_display_name": "Admin Operator",
                        "actor_email": "admin@example.com",
                        "actor_current_role": "admin",
                        "bank_code": "TD",
                        "bank_name": "TD Bank",
                        "product_name": "TD Every Day Savings Account",
                        "run_type": "validation_routing",
                        "run_state": "completed",
                    },
                    {
                        "audit_event_id": "audit-001",
                        "event_category": "review",
                        "event_type": "manual_override_recorded",
                        "occurred_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                        "actor_type": "user",
                        "actor_id": "usr-001",
                        "actor_role_snapshot": "admin",
                        "target_type": "product",
                        "target_id": "prod-001",
                        "target_display_name": "TD Every Day Savings Account",
                        "previous_state": None,
                        "new_state": None,
                        "reason_code": "manual_override",
                        "reason_text": None,
                        "run_id": "run-001",
                        "candidate_id": "cand-001",
                        "review_task_id": "rt-001",
                        "product_id": "prod-001",
                        "publish_item_id": None,
                        "request_id": "req-001",
                        "diff_summary": "Manual override fields: monthly_fee, notes",
                        "source_ref": None,
                        "ip_address": None,
                        "user_agent": None,
                        "retention_class": "standard",
                        "event_payload": {"changed_fields": ["monthly_fee", "notes"]},
                        "actor_display_name": "Admin Operator",
                        "actor_email": "admin@example.com",
                        "actor_current_role": "admin",
                        "bank_code": "TD",
                        "bank_name": "TD Bank",
                        "product_name": "TD Every Day Savings Account",
                        "run_type": "validation_routing",
                        "run_state": "completed",
                    },
                ],
            ]
        )
        audit_filters = normalize_audit_log_filters(
            event_category="review",
            event_type=None,
            actor_type=None,
            target_type=None,
            actor_id=None,
            target_id=None,
            run_id="run-001",
            review_task_id="rt-001",
            product_id=None,
            publish_item_id=None,
            occurred_from=None,
            occurred_to=None,
            search=None,
            sort_by="occurred_at",
            sort_order="desc",
            page=1,
            page_size=20,
        )

        audit_payload = load_audit_log_list(audit_connection, filters=audit_filters)

        self.assertEqual(audit_payload["summary"]["category_counts"]["review"], 2)
        self.assertEqual(audit_payload["items"][0]["related_context"]["review_task_id"], "rt-001")
        self.assertEqual(audit_payload["items"][0]["related_context"]["run_id"], "run-001")
        self.assertEqual(audit_payload["items"][1]["event_type"], "manual_override_recorded")

        run_connection = _QueuedConnection(
            [
                {
                    "run_id": "run-001",
                    "run_type": "validation_routing",
                    "run_state": "completed",
                    "trigger_type": "manual",
                    "triggered_by": "admin@example.com",
                    "source_scope_count": 1,
                    "source_success_count": 1,
                    "source_failure_count": 0,
                    "candidate_count": 1,
                    "review_queued_count": 1,
                    "error_summary": None,
                    "partial_completion_flag": False,
                    "retry_of_run_id": None,
                    "retried_by_run_id": None,
                    "run_metadata": {
                        "pipeline_stage": "validation_routing",
                        "correlation_id": "corr-001",
                        "request_id": "req-001",
                        "source_ids": ["TD-SAV-001"],
                    },
                    "started_at": datetime(2026, 4, 13, 23, 20, tzinfo=UTC),
                    "completed_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                    "source_item_count": 1,
                },
                [
                    {
                        "source_document_id": "src-001",
                        "source_id": "TD-SAV-001",
                        "bank_code": "TD",
                        "bank_name": "TD Bank",
                        "country_code": "CA",
                        "normalized_source_url": "https://example.com/td-savings",
                        "source_type": "html",
                        "source_language": "en",
                        "selected_snapshot_id": "snap-001",
                        "fetched_at": datetime(2026, 4, 13, 23, 15, tzinfo=UTC),
                        "parsed_document_id": "pdoc-001",
                        "parse_quality_note": None,
                        "stage_status": "completed",
                        "warning_count": 0,
                        "error_count": 0,
                        "error_summary": None,
                        "stage_metadata": {
                            "review_task_id": "rt-001",
                            "request_id": "req-001",
                            "source_confidence": 0.94,
                        },
                        "runtime_notes": [],
                    }
                ],
                [
                    {
                        "stage_name": "validation_routing",
                        "execution_status": "completed",
                        "started_at": datetime(2026, 4, 13, 23, 20, tzinfo=UTC),
                        "completed_at": datetime(2026, 4, 13, 23, 30, tzinfo=UTC),
                    }
                ],
                [
                    {
                        "stage_name": "validation_routing",
                        "prompt_tokens": 1200,
                        "completion_tokens": 300,
                        "estimated_cost": 0.045,
                        "usage_metadata": {"provider": "openai"},
                    }
                ],
                [
                    {
                        "review_task_id": "rt-001",
                        "candidate_id": "cand-001",
                        "review_state": "edited",
                        "queue_reason_code": "manual_sampling_review",
                        "created_at": datetime(2026, 4, 13, 23, 25, tzinfo=UTC),
                        "product_name": "TD Every Day Savings Account",
                        "validation_status": "warning",
                        "bank_name": "TD Bank",
                    }
                ],
            ]
        )

        run_payload = load_run_status_detail(run_connection, run_id="run-001")

        self.assertIsNotNone(run_payload)
        self.assertEqual(run_payload["run"]["run_id"], "run-001")
        self.assertEqual(run_payload["usage_summary"]["usage_record_count"], 1)
        self.assertEqual(run_payload["usage_summary"]["total_tokens"], 1500)
        self.assertEqual(run_payload["related_review_tasks"][0]["review_task_id"], "rt-001")
        self.assertEqual(run_payload["related_review_tasks"][0]["review_state"], "edited")


if __name__ == "__main__":
    unittest.main()
