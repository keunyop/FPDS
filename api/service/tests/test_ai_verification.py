from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from unittest import TestCase
from unittest.mock import patch

from api_service.ai_verification import (
    AiVerificationError,
    build_ai_verification_payload,
    load_registered_bank_domains,
    load_latest_ai_verification,
    normalize_official_domains,
    run_review_ai_verification,
    sanitize_ai_verification_result,
)


class _Cursor:
    def __init__(self, *, rows=None, row=None):
        self._rows = rows or []
        self._row = row

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._row


class _RecordingConnection:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.execution_status = "started"
        self.execution_metadata: dict = {}
        self.model_execution_id = "modelexec-test"
        self.model_id = "test-model"
        self.started_at = datetime(2026, 7, 28, tzinfo=UTC)
        self.completed_at = None
        self.usage: dict | None = None

    def execute(self, sql, params=None):
        params = params or {}
        normalized_sql = " ".join(str(sql).split())
        self.calls.append((normalized_sql, params))
        if "SELECT source_url FROM (" in normalized_sql:
            return _Cursor(
                rows=[
                    {"source_url": "https://www.bank.example/"},
                    {"source_url": "https://rates.bank.example/current"},
                ]
            )
        if "INSERT INTO model_execution" in normalized_sql:
            self.model_execution_id = params["model_execution_id"]
            self.model_id = params["model_id"]
            self.started_at = params["started_at"]
            self.execution_metadata = json.loads(params["execution_metadata"])
            return _Cursor()
        if "UPDATE model_execution" in normalized_sql:
            self.execution_status = params["execution_status"]
            self.execution_metadata = json.loads(params["execution_metadata"])
            self.completed_at = params["completed_at"]
            return _Cursor()
        if "INSERT INTO llm_usage_record" in normalized_sql:
            self.usage = params
            return _Cursor()
        if "FROM model_execution AS me" in normalized_sql:
            return _Cursor(
                row={
                    "model_execution_id": self.model_execution_id,
                    "model_id": self.model_id,
                    "execution_status": self.execution_status,
                    "execution_metadata": self.execution_metadata,
                    "started_at": self.started_at,
                    "completed_at": self.completed_at,
                    "llm_usage_id": self.usage["llm_usage_id"] if self.usage else None,
                    "prompt_tokens": self.usage["prompt_tokens"] if self.usage else None,
                    "completion_tokens": self.usage["completion_tokens"] if self.usage else None,
                    "estimated_cost": self.usage["estimated_cost"] if self.usage else None,
                    "recorded_at": self.usage["recorded_at"] if self.usage else None,
                }
            )
        return _Cursor()


def _detail():
    return {
        "review_task": {
            "review_task_id": "review-001",
            "candidate_id": "candidate-001",
            "run_id": "run-001",
            "product_id": None,
            "review_state": "queued",
            "queue_reason_code": "required_field_missing",
            "issue_summary": "Verify the current rate.",
        },
        "candidate": {
            "source_document_id": "source-document-001",
            "bank_code": "BANK",
            "bank_name": "Bank Example",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "savings",
            "product_name": "Example Savings",
            "currency": "CAD",
            "candidate_payload": {
                "standard_rate": 2.5,
                "monthly_fee": 0.0,
                "bank_code": "BANK",
            },
        },
        "source_context": {
            "source_url": "https://bank.example/example-savings",
        },
        "review_field_items": [
            {
                "field_name": "standard_rate",
                "label": "Standard Rate",
                "agent_value": 2.5,
                "effective_value": 2.5,
                "missing": False,
                "suspect": True,
                "issue_codes": ["conflicting_evidence"],
                "field_note": None,
            },
            {
                "field_name": "monthly_fee",
                "label": "Monthly Fee",
                "agent_value": 0.0,
                "effective_value": 0.0,
                "missing": False,
                "suspect": False,
                "issue_codes": [],
                "field_note": None,
            },
            {
                "field_name": "bank_code",
                "label": "Bank Code",
                "effective_value": "BANK",
                "missing": False,
                "suspect": False,
                "issue_codes": [],
                "field_note": None,
            },
            {
                "field_name": "currency",
                "label": "Currency",
                "effective_value": "CAD",
                "missing": False,
                "suspect": False,
                "issue_codes": [],
                "field_note": None,
            },
        ],
    }


class AiVerificationTests(TestCase):
    def test_normalize_official_domains_keeps_registered_hosts_only(self):
        self.assertEqual(
            normalize_official_domains(
                [
                    "https://www.bank.example/product",
                    "https://bank.example/rates",
                    "https://rates.bank.example/table",
                    "http://127.0.0.1/private",
                    "localhost",
                    "not-a-host",
                ]
            ),
            ["bank.example", "rates.bank.example"],
        )

    def test_registered_bank_domains_do_not_admit_unregistered_preferred_host(self):
        connection = _RecordingConnection()
        self.assertEqual(
            load_registered_bank_domains(
                connection,
                bank_code="BANK",
                country_code="CA",
                preferred_urls=[
                    "https://unregistered.example/product",
                    "https://bank.example/example-savings",
                ],
            ),
            ["bank.example", "rates.bank.example"],
        )
        domain_query = next(params for sql, params in connection.calls if "SELECT source_url FROM (" in sql)
        self.assertEqual(domain_query["country_code"], "CA")

    def test_build_payload_excludes_read_only_fields(self):
        payload = build_ai_verification_payload(
            detail=_detail(),
            allowed_domains=["bank.example"],
        )
        self.assertEqual(
            [item["field_name"] for item in payload["fields_to_verify"]],
            ["product_name", "standard_rate", "monthly_fee", "currency"],
        )
        self.assertEqual(payload["official_domain_allowlist"], ["bank.example"])

    def test_run_rejects_read_only_actor_before_provider_or_database_work(self):
        connection = _RecordingConnection()
        with self.assertRaises(AiVerificationError) as raised:
            run_review_ai_verification(
                connection,
                detail=_detail(),
                actor={"user_id": "user-001", "role": "read_only"},
                request_context={"request_id": "request-001"},
            )
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(connection.calls, [])

    def test_rejected_task_cannot_run_and_is_disabled_in_latest_state(self):
        detail = _detail()
        detail["review_task"]["review_state"] = "rejected"
        connection = _RecordingConnection()
        with self.assertRaises(AiVerificationError) as raised:
            run_review_ai_verification(
                connection,
                detail=detail,
                actor={"user_id": "user-001", "role": "reviewer"},
                request_context={"request_id": "request-001"},
            )
        self.assertEqual(raised.exception.status_code, 409)

        with patch.dict(
            os.environ,
            {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"},
            clear=False,
        ):
            latest = load_latest_ai_verification(
                connection,
                review_task_id="review-001",
                actor_role="reviewer",
                review_state="rejected",
            )
        self.assertFalse(latest["can_run"])

    def test_sanitize_result_keeps_only_grounded_contract_safe_corrections(self):
        source = {"url": "https://bank.example/rates", "title": "Official rates"}
        result = sanitize_ai_verification_result(
            raw_result={
                "overall_status": "differences_found",
                "summary": "The current rate differs.",
                "fields": [
                    {
                        "field_name": "standard_rate",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": "3.25",
                        "confidence": 0.96,
                        "rationale": "The official product rate is 3.25%.",
                        "sources": [source],
                    },
                    {
                        "field_name": "monthly_fee",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": "999",
                        "confidence": 0.9,
                        "rationale": "Unsafe value.",
                        "sources": [source],
                    },
                    {
                        "field_name": "bank_code",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": '"OTHER"',
                        "confidence": 1,
                        "rationale": "Identity mutation must be ignored.",
                        "sources": [source],
                    },
                    {
                        "field_name": "invented_field",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": '"unsupported"',
                        "confidence": 1,
                        "rationale": "Unknown fields must be ignored.",
                        "sources": [source],
                    },
                ],
            },
            detail=_detail(),
            sources=[source],
            allowed_domains=["bank.example"],
        )
        self.assertEqual(result["overall_status"], "differences_found")
        self.assertEqual(result["proposed_corrections"], {"standard_rate": 3.25})
        self.assertEqual([item["field_name"] for item in result["fields"]], ["standard_rate", "monthly_fee"])
        monthly_fee = next(item for item in result["fields"] if item["field_name"] == "monthly_fee")
        self.assertFalse(monthly_fee["can_apply"])
        self.assertIn("safe range", monthly_fee["validation_note"])

    def test_sanitize_result_downgrades_claim_without_consulted_source(self):
        result = sanitize_ai_verification_result(
            raw_result={
                "summary": "No consulted source.",
                "fields": [
                    {
                        "field_name": "standard_rate",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": "3.25",
                        "confidence": 0.9,
                        "rationale": "Unsupported.",
                        "sources": [{"url": "https://other.example/rates", "title": "Other"}],
                    }
                ],
            },
            detail=_detail(),
            sources=[{"url": "https://bank.example/rates", "title": "Official"}],
            allowed_domains=["bank.example"],
        )
        self.assertEqual(result["fields"][0]["status"], "unverified")
        self.assertEqual(result["proposed_corrections"], {})

    def test_sanitize_result_derives_match_status_from_contract_normalized_values(self):
        source = {"url": "https://bank.example/rates", "title": "Official rates"}
        result = sanitize_ai_verification_result(
            raw_result={
                "summary": "Server should derive comparison status.",
                "fields": [
                    {
                        "field_name": "standard_rate",
                        "status": "match",
                        "has_verified_value": True,
                        "verified_value_json": "3.25",
                        "confidence": 0.95,
                        "rationale": "The model mislabeled a difference.",
                        "sources": [source],
                    },
                    {
                        "field_name": "monthly_fee",
                        "status": "mismatch",
                        "has_verified_value": True,
                        "verified_value_json": "0",
                        "confidence": 0.95,
                        "rationale": "The model mislabeled an equal value.",
                        "sources": [source],
                    },
                ],
            },
            detail=_detail(),
            sources=[source],
            allowed_domains=["bank.example"],
        )
        statuses = {item["field_name"]: item["status"] for item in result["fields"]}
        self.assertEqual(statuses, {"standard_rate": "mismatch", "monthly_fee": "match"})
        self.assertEqual(result["proposed_corrections"], {"standard_rate": 3.25})

    def test_run_persists_model_usage_result_and_audit(self):
        connection = _RecordingConnection()
        source = {"url": "https://bank.example/rates", "title": "Official rates"}

        def invoke_model(**kwargs):
            self.assertTrue(kwargs["require_web_search"])
            self.assertEqual(kwargs["web_search_allowed_domains"], ["bank.example", "rates.bank.example"])
            return (
                {
                    "overall_status": "differences_found",
                    "summary": "The current rate differs.",
                    "fields": [
                        {
                            "field_name": "standard_rate",
                            "status": "mismatch",
                            "has_verified_value": True,
                            "verified_value_json": "3.25",
                            "confidence": 0.98,
                            "rationale": "Official current rate.",
                            "sources": [source],
                        }
                    ],
                },
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-test",
                    "prompt_tokens": 120,
                    "completion_tokens": 40,
                    "web_search_sources": [source],
                },
            )

        with patch.dict(
            os.environ,
            {
                "FPDS_LLM_PROVIDER": "openai",
                "FPDS_LLM_API_KEY": "test-key",
                "FPDS_LLM_MODEL": "test-model",
            },
            clear=False,
        ):
            result = run_review_ai_verification(
                connection,
                detail=_detail(),
                actor={"user_id": "user-001", "role": "reviewer"},
                request_context={"request_id": "request-001"},
                invoke_model=invoke_model,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(connection.execution_status, "completed")
        self.assertEqual(connection.usage["prompt_tokens"], 120)
        self.assertEqual(
            connection.execution_metadata["verification_result"]["proposed_corrections"],
            {"standard_rate": 3.25},
        )
        audit = next(params for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit["event_type"], "review_ai_verification_completed")
        self.assertEqual(audit["diff_summary"], "standard_rate")
        audit_payload = json.loads(audit["event_payload"])
        self.assertEqual(audit_payload["allowed_domains"], ["bank.example", "rates.bank.example"])
        self.assertEqual(audit_payload["sources"], [source])

    def test_system_actor_is_preserved_in_verification_audit(self):
        connection = _RecordingConnection()
        source = {"url": "https://bank.example/rates", "title": "Official rates"}

        def invoke_model(**_kwargs):
            return (
                {"overall_status": "verified", "summary": "Verified.", "fields": []},
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "web_search_sources": [source],
                },
            )

        with patch.dict(
            os.environ,
            {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"},
            clear=False,
        ):
            run_review_ai_verification(
                connection,
                detail=_detail(),
                actor={"actor_type": "system", "role": "admin"},
                request_context={"request_id": "batch-001"},
                invoke_model=invoke_model,
            )

        audit = next(params for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit["actor_type"], "system")

    def test_run_failure_is_persisted_without_mutating_candidate(self):
        connection = _RecordingConnection()

        def invoke_model(**_kwargs):
            raise RuntimeError("OpenAI Responses API request timed out")

        with patch.dict(
            os.environ,
            {
                "FPDS_LLM_PROVIDER": "openai",
                "FPDS_LLM_API_KEY": "test-key",
            },
            clear=False,
        ):
            result = run_review_ai_verification(
                connection,
                detail=_detail(),
                actor={"user_id": "user-001", "role": "reviewer"},
                request_context={"request_id": "request-001"},
                invoke_model=invoke_model,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(connection.execution_status, "failed")
        self.assertIsNone(connection.usage)
        audit = next(params for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit["event_type"], "review_ai_verification_failed")
        self.assertIn("timed out", result["error"]["message"])
