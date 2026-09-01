from __future__ import annotations

from contextlib import contextmanager
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import urllib.error

from api_service.bank_ai_onboarding import (
    _is_transient_provider_transport_error,
    _ranked_candidates_for_evidence,
    _retain_bank_ai_relevant_sources,
    build_bank_ai_onboarding_payload,
    run_bank_ai_onboarding,
    sanitize_bank_ai_onboarding_result,
)
from api_service.errors import SourceRegistryError
from api_service.models import BankAiOnboardingRequest
from api_service.review_detail import ReviewTaskError


class _Result:
    def __init__(self, *, one=None, many=None) -> None:  # type: ignore[no-untyped-def]
        self.one = one
        self.many = many or []

    def fetchone(self):  # type: ignore[no-untyped-def]
        return self.one

    def fetchall(self):  # type: ignore[no-untyped-def]
        return self.many


class _Transaction:
    def __init__(self, connection: "_Connection") -> None:
        self.connection = connection

    def __enter__(self) -> "_Transaction":
        self.connection.transaction_entered += 1
        return self

    def __exit__(self, exc_type, _exc, _tb) -> bool:  # type: ignore[no-untyped-def]
        self.connection.transaction_exit_types.append(exc_type)
        return False


class _Connection:
    def __init__(
        self,
        *,
        existing_banks: list[dict[str, object]] | None = None,
        product_types: list[dict[str, object]] | None = None,
        schema_ready: bool = True,
        fail_model_execution_update: bool = False,
    ) -> None:
        self.existing_banks = existing_banks or []
        self.product_types = product_types or [
            {
                "product_type_code": "savings",
                "product_family": "deposit",
                "display_name": "Savings",
                "description": "Retail savings accounts",
            },
            {
                "product_type_code": "mortgage",
                "product_family": "lending",
                "display_name": "Mortgage",
                "description": "Retail residential mortgages",
            },
        ]
        self.schema_ready = schema_ready
        self.fail_model_execution_update = fail_model_execution_update
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.transaction_entered = 0
        self.transaction_exit_types: list[object] = []

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _Result:
        normalized = " ".join(sql.split())
        self.calls.append((normalized, params or {}))
        if "FROM information_schema.columns" in normalized:
            return _Result(one={"nullable_run_columns": 2 if self.schema_ready else 0})
        if "FROM country_registry" in normalized:
            return _Result(one={"country_code": "CA", "country_name": "Canada"})
        if "FROM product_type_registry" in normalized:
            return _Result(many=self.product_types)
        if "FROM bank" in normalized and "normalized_homepage_url" in normalized:
            return _Result(many=self.existing_banks)
        if self.fail_model_execution_update and "UPDATE model_execution" in normalized:
            raise RuntimeError("database connection closed while recording failure")
        return _Result()

    def transaction(self) -> _Transaction:
        return _Transaction(self)

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def _sources() -> list[dict[str, str]]:
    return [
        {"url": "https://regulator.example/bank-ranking", "title": "Bank ranking"},
        {"url": "https://alpha.example/", "title": "Alpha Bank"},
        {"url": "https://alpha.example/savings", "title": "Alpha savings"},
        {"url": "https://alpha.example/mortgages", "title": "Alpha mortgages"},
        {"url": "https://beta.example/", "title": "Beta Bank"},
        {"url": "https://beta.example/savings", "title": "Beta savings"},
        {"url": "https://existing.example/", "title": "Existing Bank"},
    ]


def _candidate(
    *,
    rank: int,
    name: str,
    host: str,
    coverage: list[str],
    known_names: list[str] | None = None,
) -> dict[str, object]:
    return {
        "rank": rank,
        "bank_name": name,
        "legal_name": f"{name} Legal Entity",
        "legal_name_source_url": f"https://{host}/",
        "ranking_name": name.upper(),
        "known_names": known_names or [],
        "homepage_url": f"https://{host}/",
        "homepage_source_url": f"https://{host}/",
        "logo_url": None,
        "logo_source_url": None,
        "source_language": "en",
        "size_metric_label": "Total assets",
        "size_metric_value": f"CAD {1000 - rank * 100} billion",
        "size_metric_as_of": "2025-12-31",
        "ranking_source_url": "https://regulator.example/bank-ranking",
        "coverage": [
            {
                "product_type": product_type,
                "source_url": f"https://{host}/{'mortgages' if product_type == 'mortgage' else 'savings'}",
                "current_offering_quote": (
                    "Current mortgage products are available."
                    if product_type == "mortgage"
                    else "Current savings accounts are available."
                ),
                "relationship_source_url": f"https://{host}/",
                "relationship_quote": f"{name} provides these products.",
            }
            for product_type in coverage
        ],
    }


def _raw_result(candidates: list[dict[str, object]]) -> dict[str, object]:
    return {
        "country_code": "CA",
        "ranking_basis": {
            "metric": "Consolidated total assets",
            "as_of_date": "2025-12-31",
            "summary": "Latest comparable regulator-reported total assets.",
        },
        "candidates": candidates,
    }


def _created_bank(name: str, code: str, host: str) -> dict[str, object]:
    return {
        "bank_code": code,
        "country_code": "CA",
        "bank_name": name,
        "status": "active",
        "homepage_url": f"https://{host}/",
        "normalized_homepage_url": f"https://{host}/",
        "logo_url": f"https://{host}/favicon.ico",
        "logo_alt_text": f"{name} logo",
        "source_language": "en",
        "managed_flag": True,
        "change_reason": "AI bank onboarding",
        "created_at": None,
        "updated_at": None,
        "catalog_item_count": 1,
        "catalog_product_types": ["savings"],
        "catalog_items": [],
        "generated_source_count": 0,
    }


class BankAiOnboardingTests(unittest.TestCase):
    def test_provider_retry_classifies_only_transient_gateway_http_errors(self) -> None:
        transient_http_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses",
            503,
            "Service Unavailable",
            hdrs=None,
            fp=None,
        )
        wrapped_transient = RuntimeError("OpenAI request failed with status 503")
        wrapped_transient.__cause__ = transient_http_error
        client_http_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses",
            400,
            "Bad Request",
            hdrs=None,
            fp=None,
        )

        try:
            self.assertTrue(_is_transient_provider_transport_error(wrapped_transient))
            self.assertFalse(_is_transient_provider_transport_error(client_http_error))
        finally:
            wrapped_transient.__cause__ = None
            transient_http_error.close()
            client_http_error.close()

    def test_us_onboarding_uses_us_product_vocabulary_without_changing_codes(self) -> None:
        payload = build_bank_ai_onboarding_payload(
            country={"country_code": "US", "country_name": "United States"},
            requested_count=1,
            existing_banks=[],
            product_types=[
                {
                    "product_type_code": "chequing",
                    "product_family": "deposit",
                    "display_name": "Chequing",
                    "description": "Canadian chequing account.",
                    "discovery_keywords": ["chequing"],
                },
                {
                    "product_type_code": "gic",
                    "product_family": "deposit",
                    "display_name": "GIC",
                    "description": "Canadian guaranteed investment certificate.",
                    "discovery_keywords": ["gic"],
                },
            ],
        )

        allowed = {item["product_type_code"]: item for item in payload["allowed_product_types"]}
        self.assertEqual(set(allowed), {"chequing", "gic"})
        self.assertEqual(allowed["chequing"]["display_name"], "Checking account")
        self.assertIn("checking account", allowed["chequing"]["discovery_keywords"])
        self.assertEqual(allowed["gic"]["display_name"], "Certificate of Deposit (CD)")
        self.assertIn("certificate of deposit", allowed["gic"]["discovery_keywords"])
        self.assertEqual(payload["candidate_limit"], 2)

    def test_payload_bounds_extra_candidates_to_preserve_source_research_budget(self) -> None:
        payload = build_bank_ai_onboarding_payload(
            country={"country_code": "US", "country_name": "United States"},
            requested_count=5,
            existing_banks=[],
            product_types=[],
        )

        self.assertEqual(payload["candidate_limit"], 10)

    def test_relevant_source_filter_keeps_late_official_evidence_without_noise(self) -> None:
        candidate = _candidate(
            rank=1,
            name="Alpha Bank",
            host="alpha.example",
            coverage=["savings"],
        )
        candidate["legal_name_source_url"] = "https://alpha.example/about"
        candidate["coverage"][0]["relationship_source_url"] = "https://alpha.example/about"  # type: ignore[index]
        metadata = {
            "provider": "openai",
            "model_id": "test-model",
            "provider_request_id": "resp-source-filter",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "web_search_sources": [
                *[
                    {
                        "url": f"https://noise-{index}.example/report",
                        "title": f"Noise {index}",
                    }
                    for index in range(120)
                ],
                {"url": "https://alpha.example/about", "title": "About Alpha"},
                {"url": "https://alpha.example/savings", "title": "Alpha savings"},
            ],
        }

        filtered = _retain_bank_ai_relevant_sources(
            result=_raw_result([candidate]),
            provider_metadata=metadata,
        )

        self.assertEqual(filtered["web_search_source_total_count"], 122)
        self.assertEqual(
            [item["url"] for item in filtered["web_search_sources"]],
            ["https://alpha.example/about", "https://alpha.example/savings"],
        )

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    def test_run_requires_standalone_ai_migration_before_provider_call(
        self,
        _provider_configured: Mock,
    ) -> None:
        invoke_model = Mock()

        with self.assertRaises(SourceRegistryError) as captured:
            run_bank_ai_onboarding(
                _Connection(schema_ready=False),
                country_code="CA",
                requested_count=1,
                actor={"user_id": "usr-admin", "role": "admin"},
                request_context={"request_id": "req-schema"},
                invoke_model=invoke_model,
            )

        self.assertEqual(captured.exception.code, "bank_ai_schema_not_ready")
        invoke_model.assert_not_called()

    def test_sanitizer_excludes_existing_bank_and_keeps_largest_verified_missing_banks(self) -> None:
        raw = _raw_result(
            [
                _candidate(
                    rank=1,
                    name="Existing Financial",
                    host="existing.example",
                    coverage=["savings"],
                    known_names=["Existing Bank"],
                ),
                _candidate(
                    rank=2,
                    name="Alpha Bank",
                    host="alpha.example",
                    coverage=["savings", "mortgage"],
                ),
                _candidate(
                    rank=3,
                    name="Beta Bank",
                    host="beta.example",
                    coverage=["savings"],
                ),
            ]
        )

        result = sanitize_bank_ai_onboarding_result(
            raw_result=raw,
            country_code="CA",
            requested_count=2,
            active_product_types={"savings", "mortgage"},
            existing_banks=[
                {
                    "bank_name": "Existing Bank",
                    "homepage_url": "https://existing.example/",
                }
            ],
            sources=_sources(),
        )

        self.assertEqual([item["bank_name"] for item in result["candidates"]], ["Alpha Bank", "Beta Bank"])
        self.assertEqual(result["candidates"][0]["coverage_product_types"], ["savings", "mortgage"])
        self.assertEqual(result["candidates"][0]["logo_url"], "https://alpha.example/favicon.ico")

    def test_sanitizer_rejects_batch_when_requested_count_is_not_fully_sourced(self) -> None:
        raw = _raw_result(
            [
                _candidate(
                    rank=1,
                    name="Alpha Bank",
                    host="alpha.example",
                    coverage=["savings"],
                ),
                _candidate(
                    rank=2,
                    name="Off-domain Coverage Bank",
                    host="beta.example",
                    coverage=["mortgage"],
                ),
            ]
        )
        raw["candidates"][1]["coverage"][0]["source_url"] = "https://unrelated.example/mortgages"  # type: ignore[index]

        with self.assertRaises(SourceRegistryError) as captured:
            sanitize_bank_ai_onboarding_result(
                raw_result=raw,
                country_code="CA",
                requested_count=2,
                active_product_types={"savings", "mortgage"},
                existing_banks=[],
                sources=[*_sources(), {"url": "https://unrelated.example/mortgages", "title": "Unrelated"}],
            )

        self.assertEqual(captured.exception.code, "bank_ai_results_insufficient")
        diagnostics = getattr(captured.exception, "diagnostics", {})
        self.assertEqual(diagnostics["raw_candidate_count"], 2)
        self.assertEqual(diagnostics["accepted_candidate_count"], 1)
        self.assertEqual(diagnostics["candidates_with_consulted_homepage_source"], 2)
        self.assertEqual(diagnostics["candidates_with_consulted_coverage_source"], 2)

    def test_sanitizer_uses_consulted_same_host_page_as_homepage_evidence(self) -> None:
        candidate = _candidate(
            rank=1,
            name="Alpha Bank",
            host="alpha.example",
            coverage=["savings"],
        )
        candidate["legal_name_source_url"] = "https://alpha.example/about"
        candidate["coverage"][0]["relationship_source_url"] = "https://alpha.example/about"  # type: ignore[index]

        result = sanitize_bank_ai_onboarding_result(
            raw_result=_raw_result([candidate]),
            country_code="CA",
            requested_count=1,
            active_product_types={"savings"},
            existing_banks=[],
            sources=[
                {"url": "https://regulator.example/bank-ranking", "title": "Bank ranking"},
                {"url": "https://alpha.example/about", "title": "About Alpha"},
                {"url": "https://alpha.example/savings", "title": "Alpha savings"},
            ],
        )

        self.assertEqual(
            result["candidates"][0]["homepage_source_url"],
            "https://alpha.example/about",
        )

    def test_ranking_preparation_rejects_report_title_as_institution_name(self) -> None:
        report_candidate = _candidate(
            rank=1,
            name="Alpha Bank",
            host="alpha.example",
            coverage=["savings"],
        )
        report_candidate["ranking_name"] = (
            "U.S. Domestically Chartered Commercial Banks, Ranked by Consolidated Assets"
        )
        report_candidate["known_names"] = ["Alpha Bank"]
        valid_candidate = _candidate(
            rank=2,
            name="Beta Bank",
            host="beta.example",
            coverage=["savings"],
        )

        ranked = _ranked_candidates_for_evidence(
            ranking_result=_raw_result([report_candidate, valid_candidate]),
            existing_banks=[],
            candidate_limit=2,
        )

        self.assertEqual([item["ranking_name"] for item in ranked], ["BETA BANK"])

    def test_sanitizer_accepts_verified_official_consumer_brand_domain(self) -> None:
        candidate = _candidate(
            rank=1,
            name="Goldman Sachs Bank USA",
            host="goldmansachs.com",
            coverage=["savings"],
        )
        candidate["legal_name"] = "Goldman Sachs Bank USA"
        candidate["coverage"] = [
            {
                "product_type": "savings",
                "source_url": "https://www.marcus.com/us/en/savings",
                "current_offering_quote": "Online Savings Account",
                "relationship_source_url": "https://www.marcus.com/us/en/faqs",
                "relationship_quote": "Marcus by Goldman Sachs is a brand of Goldman Sachs Bank USA.",
            }
        ]
        raw = _raw_result([candidate])
        raw["country_code"] = "US"

        result = sanitize_bank_ai_onboarding_result(
            raw_result=raw,
            country_code="US",
            requested_count=1,
            active_product_types={"savings"},
            existing_banks=[],
            sources=[
                *_sources(),
                {"url": "https://goldmansachs.com/", "title": "Goldman Sachs"},
                {"url": "https://www.marcus.com/us/en/savings", "title": "Marcus Savings"},
                {"url": "https://www.marcus.com/us/en/faqs", "title": "Marcus FAQs"},
            ],
        )

        coverage = result["candidates"][0]["coverage"][0]
        self.assertEqual(coverage["source_url"], "https://www.marcus.com/us/en/savings")
        self.assertEqual(coverage["source_metadata"]["coverage_domain"], "marcus.com")
        self.assertEqual(
            coverage["source_metadata"]["verification_method"],
            "ai_bank_onboarding_web_search",
        )

    def test_sanitizer_rejects_us_regulatory_abbreviation_as_display_name(self) -> None:
        raw = _raw_result(
            [
                _candidate(
                    rank=1,
                    name="JPMORGAN CHASE BK NA",
                    host="chase.example",
                    coverage=["savings"],
                ),
                _candidate(
                    rank=2,
                    name="Readable Bank",
                    host="alpha.example",
                    coverage=["savings"],
                ),
            ]
        )
        raw["country_code"] = "US"

        result = sanitize_bank_ai_onboarding_result(
            raw_result=raw,
            country_code="US",
            requested_count=1,
            active_product_types={"savings"},
            existing_banks=[],
            sources=[
                *_sources(),
                {"url": "https://chase.example/", "title": "Chase"},
                {"url": "https://chase.example/savings", "title": "Chase savings"},
            ],
        )

        self.assertEqual(result["candidates"][0]["bank_name"], "Readable Bank")
        self.assertEqual(result["candidates"][0]["ranking_name"], "READABLE BANK")

    def test_sanitizer_preserves_legal_and_ranking_names_as_evidence(self) -> None:
        raw = _raw_result(
            [
                _candidate(
                    rank=1,
                    name="Bank of America",
                    host="alpha.example",
                    coverage=["savings"],
                )
            ]
        )
        raw["country_code"] = "US"
        raw_candidate = raw["candidates"][0]  # type: ignore[index]
        raw_candidate["legal_name"] = "Bank of America, National Association"
        raw_candidate["ranking_name"] = "BANK OF AMER NA"

        result = sanitize_bank_ai_onboarding_result(
            raw_result=raw,
            country_code="US",
            requested_count=1,
            active_product_types={"savings"},
            existing_banks=[],
            sources=_sources(),
        )

        self.assertEqual(result["candidates"][0]["bank_name"], "Bank of America")
        self.assertEqual(
            result["candidates"][0]["legal_name"],
            "Bank of America, National Association",
        )
        self.assertEqual(result["candidates"][0]["ranking_name"], "BANK OF AMER NA")

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    @patch("api_service.bank_ai_onboarding.create_bank_profile")
    def test_success_persists_usage_audit_and_atomic_bank_batch(
        self,
        create_bank_profile: Mock,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection()
        create_bank_profile.side_effect = [
            _created_bank("Alpha Bank", "ALPHA", "alpha.example"),
            _created_bank("Beta Bank", "BETA", "beta.example"),
        ]
        model_result = _raw_result(
            [
                _candidate(rank=1, name="Alpha Bank", host="alpha.example", coverage=["savings"]),
                _candidate(rank=2, name="Beta Bank", host="beta.example", coverage=["savings"]),
            ]
        )
        invoke_model = Mock(
            side_effect=[
                (
                    model_result,
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-ranking-001",
                        "prompt_tokens": 40,
                        "completion_tokens": 20,
                        "web_search_sources": [_sources()[0]],
                    },
                ),
                (
                    _raw_result(
                        [_candidate(rank=1, name="Alpha Bank", host="alpha.example", coverage=["savings"])]
                    ),
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-evidence-alpha",
                        "prompt_tokens": 40,
                        "completion_tokens": 30,
                        "web_search_sources": _sources()[1:3],
                    },
                ),
                (
                    _raw_result(
                        [_candidate(rank=2, name="Beta Bank", host="beta.example", coverage=["savings"])]
                    ),
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-evidence-beta",
                        "prompt_tokens": 40,
                        "completion_tokens": 30,
                        "web_search_sources": _sources()[4:6],
                    },
                ),
            ]
        )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=2,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1"},
            invoke_model=invoke_model,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["added_count"], 2)
        self.assertEqual(connection.commit_count, 1)
        self.assertEqual(connection.transaction_entered, 1)
        self.assertEqual(connection.transaction_exit_types, [None])
        self.assertEqual(create_bank_profile.call_count, 2)
        self.assertEqual(
            create_bank_profile.call_args_list[0].kwargs["payload"]["initial_coverage_source_urls"],
            {"savings": "https://alpha.example/savings"},
        )
        self.assertEqual(
            create_bank_profile.call_args_list[0].kwargs["payload"]["initial_coverage_source_metadata"]["savings"]["coverage_domain"],
            "alpha.example",
        )
        self.assertEqual(invoke_model.call_count, 3)
        ranking_call = invoke_model.call_args_list[0].kwargs
        alpha_evidence_call = invoke_model.call_args_list[1].kwargs
        beta_evidence_call = invoke_model.call_args_list[2].kwargs
        self.assertTrue(ranking_call["require_web_search"])
        self.assertEqual(ranking_call["schema_name"], "fpds_bank_registry_ranking_v1")
        self.assertEqual(ranking_call["max_web_search_tool_calls"], 4)
        self.assertEqual(ranking_call["schema"]["properties"]["candidates"]["minItems"], 4)
        self.assertEqual(ranking_call["schema"]["properties"]["candidates"]["maxItems"], 4)
        self.assertIn("ranking discovery agent", ranking_call["instructions"])
        self.assertTrue(alpha_evidence_call["require_web_search"])
        self.assertEqual(
            alpha_evidence_call["schema_name"],
            "fpds_bank_registry_onboarding_v8",
        )
        self.assertEqual(alpha_evidence_call["max_web_search_tool_calls"], 4)
        self.assertEqual(alpha_evidence_call["payload"]["candidate_limit"], 1)
        self.assertEqual(
            alpha_evidence_call["payload"]["ranking_research_result"]["candidates"][0]["ranking_name"],
            "ALPHA BANK",
        )
        self.assertEqual(
            beta_evidence_call["payload"]["ranking_research_result"]["candidates"][0]["ranking_name"],
            "BETA BANK",
        )
        self.assertIn(
            "Do not search for another ranking",
            alpha_evidence_call["instructions"],
        )
        self.assertTrue(any("INSERT INTO model_execution" in sql for sql, _params in connection.calls))
        self.assertTrue(any("INSERT INTO llm_usage_record" in sql for sql, _params in connection.calls))
        completed_executions = [
            params
            for sql, params in connection.calls
            if "UPDATE model_execution" in sql and params.get("execution_status") == "completed"
        ]
        self.assertEqual(len(completed_executions), 1)
        execution_metadata = json.loads(str(completed_executions[0]["execution_metadata"]))
        self.assertEqual(execution_metadata["candidate_limit"], 4)
        self.assertEqual(execution_metadata["ranking_search_tool_call_limit"], 4)
        self.assertEqual(execution_metadata["official_evidence_search_tool_call_limit"], 4)
        self.assertEqual(execution_metadata["official_evidence_candidate_limit"], 4)
        self.assertEqual(execution_metadata["web_search_tool_call_limit"], 20)
        self.assertEqual(
            execution_metadata["onboarding_contract_version"],
            "bank-registry-onboarding-v8",
        )
        self.assertEqual(
            execution_metadata["provider_request_ids"],
            ["resp-ranking-001", "resp-evidence-alpha", "resp-evidence-beta"],
        )
        self.assertEqual(
            execution_metadata["bank_name_evidence"][0]["ranking_name"],
            "ALPHA BANK",
        )
        completed_audits = [
            params
            for sql, params in connection.calls
            if "INSERT INTO audit_event" in sql and params.get("event_type") == "bank_ai_onboarding_completed"
        ]
        self.assertEqual(len(completed_audits), 1)
        audit_payload = json.loads(str(completed_audits[0]["event_payload"]))
        self.assertEqual(audit_payload["bank_codes"], ["ALPHA", "BETA"])
        self.assertEqual(
            audit_payload["bank_name_evidence"][0]["legal_name"],
            "Alpha Bank Legal Entity",
        )

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    @patch("api_service.bank_ai_onboarding.create_bank_profile")
    def test_empty_official_evidence_advances_to_next_ranked_candidate(
        self,
        create_bank_profile: Mock,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection()
        create_bank_profile.return_value = _created_bank(
            "Beta Bank",
            "BETA",
            "beta.example",
        )
        ranking_result = _raw_result(
            [
                _candidate(rank=1, name="Alpha Bank", host="alpha.example", coverage=["savings"]),
                _candidate(rank=2, name="Beta Bank", host="beta.example", coverage=["savings"]),
            ]
        )
        invoke_model = Mock(
            side_effect=[
                (
                    ranking_result,
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-ranking-fallback",
                        "prompt_tokens": 40,
                        "completion_tokens": 20,
                        "web_search_sources": [_sources()[0]],
                    },
                ),
                (
                    _raw_result([]),
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-alpha-empty",
                        "prompt_tokens": 30,
                        "completion_tokens": 10,
                        "web_search_sources": [],
                    },
                ),
                (
                    _raw_result(
                        [_candidate(rank=2, name="Beta Bank", host="beta.example", coverage=["savings"])]
                    ),
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-beta-sourced",
                        "prompt_tokens": 30,
                        "completion_tokens": 20,
                        "web_search_sources": _sources()[4:6],
                    },
                ),
            ]
        )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=1,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-ranked-fallback"},
            invoke_model=invoke_model,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["banks"][0]["bank"]["bank_name"], "Beta Bank")
        self.assertEqual(invoke_model.call_count, 3)
        self.assertEqual(
            invoke_model.call_args_list[1].kwargs["payload"]["ranking_research_result"]["candidates"][0]["rank"],
            1,
        )
        self.assertEqual(
            invoke_model.call_args_list[2].kwargs["payload"]["ranking_research_result"]["candidates"][0]["rank"],
            2,
        )

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    @patch("api_service.bank_ai_onboarding.create_bank_profile")
    def test_transient_provider_reset_is_retried_after_started_execution_commit(
        self,
        create_bank_profile: Mock,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection()
        create_bank_profile.return_value = _created_bank(
            "Alpha Bank",
            "ALPHA",
            "alpha.example",
        )
        committed_before_attempt: list[int] = []

        def invoke_model(**_kwargs):  # type: ignore[no-untyped-def]
            committed_before_attempt.append(connection.commit_count)
            if len(committed_before_attempt) == 1:
                raise ConnectionResetError(
                    10054,
                    "An existing connection was forcibly closed by the remote host",
                )
            return (
                _raw_result(
                    [
                        _candidate(
                            rank=1,
                            name="Alpha Bank",
                            host="alpha.example",
                            coverage=["savings"],
                        )
                    ]
                ),
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-retry-001",
                    "prompt_tokens": 120,
                    "completion_tokens": 80,
                    "web_search_sources": _sources(),
                },
            )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=1,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-retry"},
            invoke_model=invoke_model,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["added_count"], 1)
        self.assertEqual(committed_before_attempt, [1, 1, 1])
        self.assertEqual(create_bank_profile.call_count, 1)

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    def test_provider_and_failure_persistence_disconnect_returns_bounded_error(
        self,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection(fail_model_execution_update=True)
        invoke_model = Mock(
            side_effect=ConnectionResetError(
                10054,
                "An existing connection was forcibly closed by the remote host",
            )
        )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=1,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-provider-db-reset"},
            invoke_model=invoke_model,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status_code"], 502)
        self.assertEqual(result["error"]["code"], "bank_ai_onboarding_failed")
        self.assertEqual(invoke_model.call_count, 2)
        self.assertEqual(connection.commit_count, 1)
        self.assertEqual(connection.rollback_count, 1)
        self.assertEqual(connection.transaction_entered, 0)

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    def test_official_evidence_failure_retains_completed_ranking_usage(
        self,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection()
        ranking_result = _raw_result(
            [_candidate(rank=1, name="Alpha Bank", host="alpha.example", coverage=["savings"])]
        )
        invoke_model = Mock(
            side_effect=[
                (
                    ranking_result,
                    {
                        "provider": "openai",
                        "model_id": "test-model",
                        "provider_request_id": "resp-ranking-partial",
                        "prompt_tokens": 40,
                        "completion_tokens": 20,
                        "web_search_sources": [_sources()[0]],
                    },
                ),
                ConnectionResetError(10054, "official evidence reset"),
                ConnectionResetError(10054, "official evidence reset"),
            ]
        )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=1,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-evidence-reset"},
            invoke_model=invoke_model,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status_code"], 502)
        self.assertEqual(invoke_model.call_count, 3)
        usage_rows = [
            params
            for sql, params in connection.calls
            if "INSERT INTO llm_usage_record" in sql
        ]
        self.assertEqual(len(usage_rows), 1)
        self.assertEqual(usage_rows[0]["prompt_tokens"], 40)
        failed_executions = [
            json.loads(str(params["execution_metadata"]))
            for sql, params in connection.calls
            if "UPDATE model_execution" in sql and params.get("execution_status") == "failed"
        ]
        self.assertEqual(failed_executions[0]["failed_model_stage"], "official_evidence_rank_1")
        self.assertEqual(
            failed_executions[0]["provider_request_ids"],
            ["resp-ranking-partial"],
        )

    @patch("api_service.bank_ai_onboarding.llm_provider_configured", return_value=True)
    @patch("api_service.bank_ai_onboarding.create_bank_profile")
    def test_second_bank_failure_rolls_back_batch_and_reports_no_partial_success(
        self,
        create_bank_profile: Mock,
        _provider_configured: Mock,
    ) -> None:
        connection = _Connection()
        create_bank_profile.side_effect = [
            _created_bank("Alpha Bank", "ALPHA", "alpha.example"),
            SourceRegistryError(
                status_code=409,
                code="bank_homepage_exists",
                message="A bank with this homepage URL already exists.",
            ),
        ]
        invoke_model = Mock(
            return_value=(
                _raw_result(
                    [
                        _candidate(rank=1, name="Alpha Bank", host="alpha.example", coverage=["savings"]),
                        _candidate(rank=2, name="Beta Bank", host="beta.example", coverage=["savings"]),
                    ]
                ),
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-002",
                    "prompt_tokens": 100,
                    "completion_tokens": 60,
                    "web_search_sources": _sources(),
                },
            )
        )

        result = run_bank_ai_onboarding(
            connection,
            country_code="CA",
            requested_count=2,
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-002"},
            invoke_model=invoke_model,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "bank_homepage_exists")
        self.assertEqual(connection.transaction_exit_types, [SourceRegistryError])
        self.assertNotIn("banks", result)
        failed_audits = [
            params
            for sql, params in connection.calls
            if "INSERT INTO audit_event" in sql and params.get("event_type") == "bank_ai_onboarding_failed"
        ]
        self.assertEqual(len(failed_audits), 1)


class BankAiOnboardingRouteTests(unittest.TestCase):
    def _request(self, *, csrf_header: str | None = "csrf-001") -> SimpleNamespace:
        from api_service.main import settings

        return SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(settings=settings)),
            state=SimpleNamespace(request_id="req-route", generated_at="2026-07-30T00:00:00+00:00"),
            headers={
                **({"x-csrf-token": csrf_header} if csrf_header is not None else {}),
                "user-agent": "unit-test",
            },
            client=SimpleNamespace(host="127.0.0.1"),
        )

    def test_route_requires_admin_role(self) -> None:
        from api_service.main import ai_onboard_banks

        with patch(
            "api_service.main._resolve_session",
            return_value=(
                {"user_id": "usr-reviewer", "role": "reviewer"},
                {"country_code": "CA", "csrf_token": "csrf-001"},
            ),
        ):
            with self.assertRaises(SourceRegistryError) as captured:
                ai_onboard_banks(self._request(), BankAiOnboardingRequest(count=1))  # type: ignore[arg-type]

        self.assertEqual(captured.exception.code, "admin_role_required")

    def test_route_requires_matching_csrf_token(self) -> None:
        from api_service.main import ai_onboard_banks

        with patch(
            "api_service.main._resolve_session",
            return_value=(
                {"user_id": "usr-admin", "role": "admin"},
                {"country_code": "CA", "csrf_token": "csrf-001"},
            ),
        ):
            with self.assertRaises(ReviewTaskError) as captured:
                ai_onboard_banks(
                    self._request(csrf_header="wrong"),
                    BankAiOnboardingRequest(count=1),
                )  # type: ignore[arg-type]

        self.assertEqual(captured.exception.code, "invalid_csrf_token")

    def test_route_uses_server_session_country(self) -> None:
        from api_service.main import ai_onboard_banks

        connection = object()

        @contextmanager
        def fake_open_connection(_settings):  # type: ignore[no-untyped-def]
            yield connection

        with (
            patch(
                "api_service.main._resolve_session",
                return_value=(
                    {"user_id": "usr-admin", "role": "admin"},
                    {"country_code": "JP", "csrf_token": "csrf-001"},
                ),
            ),
            patch("api_service.main.open_connection", fake_open_connection),
            patch(
                "api_service.main.run_bank_ai_onboarding",
                return_value={
                    "ok": True,
                    "status_code": 201,
                    "operation_id": "bankonboard-001",
                    "country_code": "JP",
                    "country_name": "Japan",
                    "requested_count": 1,
                    "added_count": 1,
                    "coverage_item_count": 1,
                    "ranking_basis": {"metric": "Assets", "as_of_date": "2025", "summary": "Current"},
                    "banks": [],
                    "sources": [],
                },
            ) as run_onboarding,
        ):
            response = ai_onboard_banks(
                self._request(),
                BankAiOnboardingRequest(count=1),
            )  # type: ignore[arg-type]

        self.assertEqual(response.status_code, 201)
        self.assertEqual(run_onboarding.call_args.kwargs["country_code"], "JP")


if __name__ == "__main__":
    unittest.main()
