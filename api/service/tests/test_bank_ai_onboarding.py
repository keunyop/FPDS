from __future__ import annotations

from contextlib import contextmanager
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from api_service.bank_ai_onboarding import (
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
        self.calls: list[tuple[str, dict[str, object]]] = []
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
        return _Result()

    def transaction(self) -> _Transaction:
        return _Transaction(self)


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
                    "provider_request_id": "resp-001",
                    "prompt_tokens": 120,
                    "completion_tokens": 80,
                    "web_search_sources": _sources(),
                },
            )
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
        self.assertTrue(invoke_model.call_args.kwargs["require_web_search"])
        self.assertTrue(any("INSERT INTO model_execution" in sql for sql, _params in connection.calls))
        self.assertTrue(any("INSERT INTO llm_usage_record" in sql for sql, _params in connection.calls))
        completed_executions = [
            params
            for sql, params in connection.calls
            if "UPDATE model_execution" in sql and params.get("execution_status") == "completed"
        ]
        self.assertEqual(len(completed_executions), 1)
        execution_metadata = json.loads(str(completed_executions[0]["execution_metadata"]))
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
