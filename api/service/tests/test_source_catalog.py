from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api_service.source_catalog import (
    AiParallelCandidateScore,
    AiParallelScoringResult,
    CatalogItemMaterializationResult,
    HomepageCandidate,
    HomepageSourceGenerationResult,
    PageEvidenceAssessment,
    _build_source_catalog_collection_plan,
    _generate_sources_from_homepage,
    _materialize_sources_for_catalog_item,
    _launch_source_catalog_collection_runner,
    _candidate_promotes_to_detail,
    _deactivate_rejected_generated_detail_sources,
    _generate_bank_code,
    _invoke_openai_parallel_scorer,
    _link_is_relevant_supporting_source,
    _ordered_detail_candidates,
    _promote_detail_candidates,
    _product_type_discovery_profile,
    _record_catalog_audit_event,
    _score_candidate_links_with_ai,
    _score_page_evidence,
    _score_product_link,
    _upsert_source_registry_rows,
    create_bank_profile,
    delete_bank_profile,
    create_source_catalog_item,
    load_bank_list,
    normalize_bank_filters,
    start_source_catalog_collection,
    update_bank_profile,
)
from api_service.errors import SourceRegistryError


class _QueuedCursor:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.rowcount = int(payload) if isinstance(payload, int) else 0

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

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _QueuedCursor:
        self.calls.append((sql, params or {}))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _QueuedCursor(self._responses.pop(0))


def _product_type_definition(product_type_code: str) -> dict[str, object]:
    label = product_type_code.replace("-", " ").title()
    product_family = "lending" if product_type_code in {"credit-card", "mortgage", "personal-loan", "line-of-credit"} else "deposit"
    return {
        "product_type_code": product_type_code,
        "product_family": product_family,
        "display_name": label,
        "description": f"{label} product type",
        "status": "active",
        "managed_flag": True,
        "discovery_keywords": [product_type_code, label.lower()],
        "expected_fields": ["product_name", "notes"],
        "fallback_policy": "generic_ai_review",
    }


class SourceCatalogTests(unittest.TestCase):
    def _workspace_temp_path(self, name: str) -> Path:
        path = Path.cwd() / "tmp" / "test-source-catalog" / name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_score_product_link_uses_product_type_description_terms(self) -> None:
        product_type_definition = _product_type_definition("tfsa")
        product_type_definition["display_name"] = "TFSA"
        product_type_definition["discovery_keywords"] = []
        product_type_definition["description"] = "Tax free savings account with contribution room and withdrawal rules."

        score = _score_product_link(
            product_type="tfsa",
            product_type_definition=product_type_definition,
            normalized_url="https://www.atlasbank.ca/accounts/contribution-room",
            anchor_text="Contribution room details",
        )

        self.assertGreater(score, 0)

    def test_lending_product_type_discovery_profiles_are_recognized(self) -> None:
        self.assertEqual(_product_type_discovery_profile("credit_card", _product_type_definition("credit-card")), "credit-card")
        self.assertEqual(_product_type_discovery_profile("mortgages", _product_type_definition("mortgage")), "mortgage")
        self.assertEqual(_product_type_discovery_profile("vehicle-loan", _product_type_definition("personal-loan")), "personal-loan")
        self.assertEqual(_product_type_discovery_profile("home-equity-loc", _product_type_definition("line-of-credit")), "line-of-credit")

    def test_credit_card_page_evidence_uses_lending_attribute_signals(self) -> None:
        detail_html = """
        <html>
          <head><title>Cash Back Credit Card</title></head>
          <body>
            <h1>Cash Back Credit Card</h1>
            <p>Earn cash back rewards with an annual fee and a purchase interest rate.</p>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/credit-cards/cash-back",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition={
                    **_product_type_definition("credit-card"),
                    "display_name": "Credit Card",
                    "description": "Credit cards with annual fee, rewards, cash back, and purchase interest details.",
                    "discovery_keywords": ["credit cards", "cash back", "annual fee"],
                },
            )

        self.assertGreaterEqual(result.page_evidence_score, 4)
        self.assertIn("pricing_or_feature_signal", result.page_evidence_reason_codes)

    def test_credit_card_page_evidence_rejects_mortgage_page(self) -> None:
        detail_html = """
        <html>
          <head><title>Mortgage Rates</title></head>
          <body>
            <h1>Mortgage Rates</h1>
            <p>Choose fixed rate or variable rate mortgage terms with amortization options.</p>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/mortgages/rates",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
            )

        self.assertIn("other_product_type", result.page_evidence_reason_codes)
        self.assertGreaterEqual(result.negative_signal_count, 2)

    def test_lending_supporting_sources_accept_rate_pages_with_product_context(self) -> None:
        self.assertTrue(
            _link_is_relevant_supporting_source(
                product_type="mortgage",
                product_type_definition={
                    **_product_type_definition("mortgage"),
                    "display_name": "Mortgage",
                    "description": "Mortgage rates, fixed rate, variable rate, term, and amortization details.",
                    "discovery_keywords": ["mortgage rates", "fixed rate mortgage"],
                },
                normalized_url="https://www.examplebank.ca/mortgages/rates",
                anchor_text="Mortgage rates",
            )
        )

    def test_create_bank_profile_auto_generates_bank_code(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "country_code": "ca",
                    "source_language": "en",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["bank_code"], "ATL")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO bank" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["bank_code"], "ATL")
        self.assertTrue(insert_calls[0][1]["managed_flag"])

    def test_create_bank_profile_can_create_initial_coverage(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
            patch("api_service.source_catalog.create_source_catalog_item") as create_catalog_item,
        ):
            create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "country_code": "ca",
                    "source_language": "en",
                    "status": "active",
                    "change_reason": "Initial operator setup",
                    "initial_coverage_product_types": ["savings", "gic"],
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(create_catalog_item.call_count, 2)
        self.assertEqual(create_catalog_item.call_args_list[0].kwargs["payload"]["product_type"], "savings")
        self.assertEqual(create_catalog_item.call_args_list[1].kwargs["payload"]["product_type"], "gic")
        self.assertEqual(create_catalog_item.call_args_list[0].kwargs["payload"]["bank_code"], "ATL")

    def test_create_bank_profile_accepts_homepage_without_scheme(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "www.atlasbank.ca",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO bank" in sql]
        self.assertEqual(insert_calls[0][1]["homepage_url"], "https://www.atlasbank.ca/")
        self.assertEqual(insert_calls[0][1]["normalized_homepage_url"], "https://www.atlasbank.ca/")

    def test_create_bank_profile_persists_logo_metadata(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                        "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                        "logo_alt_text": "Atlas Bank logo",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca/",
                    "logo_url": "www.atlasbank.ca/assets/logo.svg",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        insert_call = next(params for sql, params in connection.calls if "INSERT INTO bank" in sql)
        self.assertEqual(insert_call["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        self.assertEqual(insert_call["logo_alt_text"], "Atlas Bank logo")

    def test_update_bank_profile_updates_logo_metadata(self) -> None:
        existing_row = {
            "bank_code": "ATL",
            "country_code": "CA",
            "bank_name": "Atlas Bank",
            "status": "active",
            "homepage_url": "https://www.atlasbank.ca/",
            "normalized_homepage_url": "https://www.atlasbank.ca/",
            "logo_url": None,
            "logo_alt_text": None,
            "source_language": "en",
            "managed_flag": True,
            "change_reason": None,
            "created_at": None,
            "updated_at": None,
        }
        connection = _QueuedConnection([existing_row, None, None])

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                        "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                        "logo_alt_text": "Atlas primary mark",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = update_bank_profile(
                connection,
                bank_code="ATL",
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca/",
                    "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                    "logo_alt_text": "Atlas primary mark",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["logo_alt_text"], "Atlas primary mark")
        update_call = next(params for sql, params in connection.calls if "UPDATE bank" in sql)
        self.assertEqual(update_call["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        self.assertEqual(update_call["logo_alt_text"], "Atlas primary mark")

    def test_generate_bank_code_prefers_known_seed_bank_codes(self) -> None:
        td_connection = _QueuedConnection([None])
        scotia_connection = _QueuedConnection([None])
        rbc_connection = _QueuedConnection([None])

        self.assertEqual(_generate_bank_code(td_connection, bank_name="TD Bank", normalized_homepage_url="https://www.td.com/"), "TD")
        self.assertEqual(
            _generate_bank_code(scotia_connection, bank_name="Scotiabank", normalized_homepage_url="https://www.scotiabank.com/"),
            "SCOTIA",
        )
        self.assertEqual(
            _generate_bank_code(rbc_connection, bank_name="Royal Bank of Canada", normalized_homepage_url="https://www.rbcroyalbank.com/"),
            "RBC",
        )

    def test_create_source_catalog_item_uses_existing_bank_and_product_type(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "bank_code": "ATL",
                    "country_code": "CA",
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "normalized_homepage_url": "https://www.atlasbank.ca",
                    "source_language": "en",
                },
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("savings"),
            ),
            patch("api_service.source_catalog.new_id", return_value="abcdef123456"),
            patch(
                "api_service.source_catalog.load_source_catalog_detail",
                return_value={
                    "catalog_item": {
                        "catalog_item_id": "catalog-ca-atl-savings-abcdef12",
                        "bank_code": "ATL",
                        "product_type": "savings",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_source_catalog_item(
                connection,
                payload={
                    "bank_code": "atl",
                    "product_type": "savings",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["catalog_item_id"], "catalog-ca-atl-savings-abcdef12")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO source_registry_catalog_item" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["bank_code"], "ATL")
        self.assertEqual(insert_calls[0][1]["product_type"], "savings")

    def test_create_source_catalog_item_uses_registered_product_type_code_without_aliasing(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "bank_name": "BMO",
                    "homepage_url": "https://www.bmo.com/",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "source_language": "en",
                },
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("saving"),
            ) as require_definition,
            patch("api_service.source_catalog.new_id", return_value="abcdef123456"),
            patch(
                "api_service.source_catalog.load_source_catalog_detail",
                return_value={
                    "catalog_item": {
                        "catalog_item_id": "catalog-ca-bmo-saving-abcdef12",
                        "bank_code": "BMO",
                        "product_type": "saving",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_source_catalog_item(
                connection,
                payload={
                    "bank_code": "bmo",
                    "product_type": "saving",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["product_type"], "saving")
        require_definition.assert_called_once_with(connection, product_type_code="saving", active_only=True)
        conflict_call = next(params for sql, params in connection.calls if "FROM source_registry_catalog_item" in sql and "ANY" in sql)
        self.assertEqual(conflict_call["product_type_scope"], ["saving"])
        insert_call = next(params for sql, params in connection.calls if "INSERT INTO source_registry_catalog_item" in sql)
        self.assertEqual(insert_call["product_type"], "saving")

    def test_load_bank_list_includes_catalog_items_for_bulk_collect(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "bank_code": "ATL",
                        "country_code": "CA",
                        "bank_name": "Atlas Bank",
                        "status": "active",
                        "homepage_url": "https://www.atlasbank.ca",
                        "normalized_homepage_url": "https://www.atlasbank.ca",
                        "source_language": "en",
                        "managed_flag": True,
                        "change_reason": None,
                        "created_at": None,
                        "updated_at": None,
                        "catalog_item_count": 2,
                        "catalog_product_types": ["gic", "savings"],
                        "generated_source_count": 3,
                    }
                ],
                [
                    {
                        "catalog_item_id": "catalog-ca-atl-savings-1",
                        "bank_code": "ATL",
                        "product_type": "savings",
                        "status": "active",
                        "generated_source_count": 2,
                    },
                    {
                        "catalog_item_id": "catalog-ca-atl-gic-1",
                        "bank_code": "ATL",
                        "product_type": "gic",
                        "status": "inactive",
                        "generated_source_count": 1,
                    },
                ],
            ]
        )

        result = load_bank_list(connection, filters=normalize_bank_filters(search=None, status=None))

        self.assertEqual(result["items"][0]["catalog_product_types"], ["gic", "savings"])
        self.assertEqual(
            [item["catalog_item_id"] for item in result["items"][0]["catalog_items"]],
            ["catalog-ca-atl-savings-1", "catalog-ca-atl-gic-1"],
        )

    def test_collection_plan_uses_registered_product_type_code_without_aliasing(self) -> None:
        plan = _build_source_catalog_collection_plan(
            rows=[
                {
                    "catalog_item_id": "catalog-ca-bmo-saving-legacy",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "saving",
                    "homepage_url": "https://www.bmo.com/",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "source_language": "en",
                }
            ],
            actor={"user_id": "usr-001", "email": "admin@example.com", "display_name": "Admin", "role": "admin"},
            request_context={"request_id": "req-001"},
            collection_id="collection-001",
            correlation_id="corr-001",
        )

        group = plan["groups"][0]
        self.assertEqual(group["product_type"], "saving")
        self.assertEqual(group["source_catalog_product_type"], "saving")
        self.assertIn("_bmo_saving_collect_", group["run_id"])

    def test_delete_bank_profile_removes_catalog_and_generated_sources_when_unused_downstream(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "catalog_count": 2,
                    "source_registry_count": 3,
                    "source_document_count": 0,
                    "candidate_count": 0,
                    "canonical_product_count": 0,
                    "public_projection_count": 0,
                    "dashboard_ranking_count": 0,
                    "dashboard_scatter_count": 0,
                },
                None,
                None,
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    },
                    "catalog_items": [],
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = delete_bank_profile(
                connection,
                bank_code="atl",
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["bank_code"], "ATL")
        self.assertTrue(any("DELETE FROM source_registry_item" in sql for sql, _ in connection.calls))
        self.assertTrue(any("DELETE FROM source_registry_catalog_item" in sql for sql, _ in connection.calls))
        self.assertTrue(any("DELETE FROM bank" in sql for sql, _ in connection.calls))

    def test_delete_bank_profile_rejects_bank_with_downstream_runtime_data(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "catalog_count": 1,
                    "source_registry_count": 1,
                    "source_document_count": 1,
                    "candidate_count": 0,
                    "canonical_product_count": 0,
                    "public_projection_count": 0,
                    "dashboard_ranking_count": 0,
                    "dashboard_scatter_count": 0,
                },
            ]
        )

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    },
                    "catalog_items": [],
                },
            ),
        ):
            with self.assertRaises(SourceRegistryError) as captured:
                delete_bank_profile(
                    connection,
                    bank_code="ATL",
                    actor={"user_id": "usr-001", "role": "admin"},
                    request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
                )

        self.assertEqual(captured.exception.code, "bank_profile_in_use")

    def test_start_source_catalog_collection_materializes_and_launches_collection(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "catalog_item_id": "catalog-ca-atl-savings-12345678",
                        "bank_code": "ATL",
                        "country_code": "CA",
                        "product_type": "savings",
                        "status": "active",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                        "normalized_homepage_url": "https://www.atlasbank.ca",
                        "source_language": "en",
                    }
                ]
            ]
        )

        with (
            patch("api_service.source_catalog._build_source_catalog_collection_run_id", return_value="run-001"),
            patch("api_service.source_catalog.new_id", side_effect=["collection-001", "corr-001"]),
            patch("api_service.source_catalog._insert_collection_run_row") as queue_run,
            patch("api_service.source_catalog._launch_source_catalog_collection_runner") as launch_runner,
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-atl-savings-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["catalog_item_ids"], ["catalog-ca-atl-savings-12345678"])
        self.assertEqual(result["collection_id"], "collection-001")
        self.assertEqual(result["correlation_id"], "corr-001")
        self.assertEqual(result["run_ids"], ["run-001"])
        self.assertEqual(result["materialized_items"], [])
        self.assertEqual(result["workflow_state"], "queued")
        self.assertEqual(result["queued_catalog_item_count"], 1)
        queue_run.assert_called_once_with(
            connection,
            run_id="run-001",
            triggered_by="admin@example.com",
            request_id="req-001",
            correlation_id="corr-001",
            collection_id="collection-001",
            group={
                "run_id": "run-001",
                "catalog_item_id": "catalog-ca-atl-savings-12345678",
                "bank_code": "ATL",
                "bank_name": "Atlas Bank",
                "country_code": "CA",
                "product_type": "savings",
                "source_catalog_product_type": "savings",
                "source_language": "en",
                "homepage_url": "https://www.atlasbank.ca",
                "normalized_homepage_url": "https://www.atlasbank.ca",
                "selected_source_ids": [],
                "target_source_ids": [],
                "included_source_ids": [],
                "included_sources": [],
            },
            pipeline_stage="source_catalog_collection",
            retry_of_run_id=None,
        )
        launch_runner.assert_called_once()

    def test_record_catalog_audit_event_uses_current_audit_schema(self) -> None:
        connection = _QueuedConnection([None])

        with patch("api_service.source_catalog.new_id", return_value="audit-001"):
            _record_catalog_audit_event(
                connection,
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
                event_type="bank_profile_updated",
                target_id="BMO",
                target_type="bank",
                diff_summary="Updated bank profile `BMO`: Homepage URL.",
                metadata={"bank_code": "BMO"},
            )

        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("event_category", sql)
        self.assertIn("actor_role_snapshot", sql)
        self.assertIn("occurred_at", sql)
        self.assertEqual(params["audit_event_id"], "audit-001")
        self.assertEqual(params["event_category"], "config")
        self.assertEqual(params["actor_id"], "usr-001")
        self.assertEqual(params["actor_role_snapshot"], "admin")
        self.assertEqual(params["diff_summary"], "Updated bank profile `BMO`: Homepage URL.")

    def test_materialize_sources_for_catalog_item_regenerates_from_bank_homepage(self) -> None:
        connection = _QueuedConnection([None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[
                        {
                            "source_id": "AUTO-BMO-CHQ-001",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing catalog entry",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "entry",
                            "status": "active",
                            "priority": "P0",
                            "source_language": "en",
                            "purpose": "entry",
                            "expected_fields": ["product_name"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        }
                    ],
                    discovery_notes=["seeded entry only"],
                    detail_source_ids=["AUTO-BMO-CHQ-001"],
                ),
            ) as generate_sources,
            patch(
                "api_service.source_catalog._upsert_source_registry_rows",
                return_value=[
                    {
                        "source_id": "AUTO-BMO-CHQ-001",
                        "bank_code": "BMO",
                        "country_code": "CA",
                        "product_type": "chequing",
                        "source_name": "BMO chequing catalog entry",
                        "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                        "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                        "source_type": "html",
                        "discovery_role": "entry",
                        "status": "active",
                        "priority": "P0",
                        "source_language": "en",
                        "purpose": "entry",
                        "expected_fields": ["product_name"],
                        "seed_source_flag": False,
                        "redirect_target_url": None,
                        "alias_urls": [],
                        "change_reason": "generated_from_bank_homepage",
                    }
                ],
            ) as upsert_rows,
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual([item["source_id"] for item in result.generated_rows], ["AUTO-BMO-CHQ-001"])
        self.assertEqual(result.discovery_notes, ["seeded entry only"])
        generate_sources.assert_called_once()
        upsert_rows.assert_called_once()
        self.assertEqual(upsert_rows.call_args.args[1][0]["source_id"], "AUTO-BMO-CHQ-001")
        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("UPDATE source_registry_item", sql)
        self.assertIn("discovery_role <> 'detail'", sql)
        self.assertIn("status <> 'removed'", sql)
        self.assertEqual(params["bank_code"], "BMO")
        self.assertIn("chequing", params["product_type_scope"])

    def test_materialize_sources_persists_homepage_ai_usage_for_run_detail(self) -> None:
        connection = _QueuedConnection([None, None, None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[],
                    discovery_notes=["AI parallel scorer evaluated 1 candidate link(s)."],
                    detail_source_ids=["AUTO-BMO-CHQ-001"],
                    model_execution_records=(
                        {
                            "model_execution_id": "modelexec-ai-001",
                            "run_id": "run-001",
                            "source_document_id": None,
                            "stage_name": "source_catalog_collection",
                            "agent_name": "fpds-homepage-ai-parallel-scorer",
                            "model_id": "gpt-5.6-luna",
                            "execution_status": "completed",
                            "execution_metadata": {"candidate_link_count": 1},
                            "started_at": "2026-04-28T20:39:48+00:00",
                            "completed_at": "2026-04-28T20:39:49+00:00",
                        },
                    ),
                    usage_records=(
                        {
                            "llm_usage_id": "usage-ai-001",
                            "model_execution_id": "modelexec-ai-001",
                            "run_id": "run-001",
                            "candidate_id": None,
                            "provider_request_id": "resp-001",
                            "prompt_tokens": 120,
                            "completion_tokens": 30,
                            "estimated_cost": "0.000072",
                            "usage_metadata": {
                                "usage_mode": "openai-homepage-parallel-scoring",
                                "provider": "openai",
                                "model_id": "gpt-5.6-luna",
                            },
                            "recorded_at": "2026-04-28T20:39:49+00:00",
                        },
                    ),
                ),
            ),
            patch("api_service.source_catalog._upsert_source_registry_rows", return_value=[]),
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
                run_id="run-001",
                correlation_id="corr-001",
                request_id="req-001",
            )

        self.assertEqual(len(result.model_execution_records), 1)
        self.assertEqual(len(result.usage_records), 1)
        model_call = next(params for sql, params in connection.calls if "INSERT INTO model_execution" in sql)
        usage_call = next(params for sql, params in connection.calls if "INSERT INTO llm_usage_record" in sql)
        self.assertEqual(model_call["stage_name"], "source_catalog_collection")
        self.assertEqual(usage_call["prompt_tokens"], 120)
        self.assertEqual(usage_call["completion_tokens"], 30)
        self.assertIn("openai-homepage-parallel-scoring", usage_call["usage_metadata"])

    def test_materialize_sources_dedupes_same_scope_and_prefers_detail(self) -> None:
        connection = _QueuedConnection([None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[
                        {
                            "source_id": "AUTO-BMO-CHQ-entry",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing catalog entry",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "entry",
                            "status": "active",
                            "priority": "P0",
                            "source_language": "en",
                            "purpose": "entry",
                            "expected_fields": ["product_name"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        },
                        {
                            "source_id": "AUTO-BMO-CHQ-detail",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing detail",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "detail",
                            "status": "active",
                            "priority": "P1",
                            "source_language": "en",
                            "purpose": "detail",
                            "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        },
                    ],
                    discovery_notes=[],
                    detail_source_ids=["AUTO-BMO-CHQ-detail"],
                ),
            ),
            patch(
                "api_service.source_catalog._upsert_source_registry_rows",
                side_effect=lambda _connection, rows: rows,
            ) as upsert_rows,
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual(len(result.generated_rows), 1)
        self.assertEqual(result.generated_rows[0]["discovery_role"], "detail")
        upserted_rows = upsert_rows.call_args.args[1]
        self.assertEqual(len(upserted_rows), 1)
        self.assertEqual(upserted_rows[0]["source_id"], "AUTO-BMO-CHQ-detail")

    def test_materialize_sources_preserves_existing_detail_scope_when_no_detail_is_discovered(self) -> None:
        connection = _QueuedConnection([])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[],
                    discovery_notes=["Homepage fetch was unavailable: timed out"],
                    detail_source_ids=[],
                ),
            ),
            patch("api_service.source_catalog._upsert_source_registry_rows") as upsert_rows,
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual(result.generated_rows, [])
        self.assertIn(
            "Existing active detail sources were preserved because homepage discovery did not produce replacement detail sources.",
            result.discovery_notes,
        )
        upsert_rows.assert_not_called()
        self.assertEqual(connection.calls, [])

    def test_start_source_catalog_collection_queues_background_work_before_detail_outcome_is_known(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "catalog_item_id": "catalog-ca-bmo-chequing-12345678",
                        "bank_code": "BMO",
                        "country_code": "CA",
                        "product_type": "chequing",
                        "status": "active",
                        "bank_name": "Bank of Montreal",
                        "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                        "normalized_homepage_url": "https://www.bmo.com/en-ca/main/personal",
                        "source_language": "en",
                    }
                ]
            ]
        )

        with (
            patch("api_service.source_catalog._build_source_catalog_collection_run_id", return_value="run-001"),
            patch("api_service.source_catalog.new_id", side_effect=["collection-001", "corr-001"]),
            patch("api_service.source_catalog._insert_collection_run_row"),
            patch("api_service.source_catalog._launch_source_catalog_collection_runner") as launch_runner,
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-bmo-chequing-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["run_ids"], ["run-001"])
        self.assertEqual(result["selected_source_ids"], [])
        self.assertEqual(result["materialized_items"], [])
        self.assertEqual(result["workflow_state"], "queued")
        launch_runner.assert_called_once()

    def test_launch_source_catalog_collection_runner_spawns_one_process_for_full_plan(self) -> None:
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "trigger_type": "admin_source_catalog_collection",
            "triggered_by": "admin@example.com",
            "actor": {"user_id": "usr-001", "email": "admin@example.com", "role": "admin"},
            "groups": [
                {
                    "run_id": "run-001",
                    "catalog_item_id": "catalog-ca-bmo-chequing",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "source_language": "en",
                    "homepage_url": "https://www.bmo.com",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "selected_source_ids": [],
                    "target_source_ids": [],
                    "included_source_ids": [],
                    "included_sources": [],
                },
                {
                    "run_id": "run-002",
                    "catalog_item_id": "catalog-ca-bmo-savings",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "savings",
                    "source_language": "en",
                    "homepage_url": "https://www.bmo.com",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "selected_source_ids": [],
                    "target_source_ids": [],
                    "included_source_ids": [],
                    "included_sources": [],
                },
            ],
        }

        repo_root = self._workspace_temp_path("launch-runner")
        with (
            patch("api_service.source_catalog.REPO_ROOT", repo_root),
            patch("api_service.source_catalog.subprocess.Popen") as popen,
        ):
            _launch_source_catalog_collection_runner(plan)

        self.assertEqual(popen.call_count, 1)
        persisted_plan = json.loads((repo_root / "tmp" / "source-catalog-collections" / "collection-001.json").read_text(encoding="utf-8"))
        self.assertEqual([group["run_id"] for group in persisted_plan["groups"]], ["run-001", "run-002"])

    def test_generate_sources_from_homepage_can_use_ai_to_resolve_detail_rows(self) -> None:
        homepage_html = """
        <html>
          <body>
            <a href="/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account/">
              Everyday transaction account
            </a>
          </body>
        </html>
        """
        detail_html = """
        <html>
          <head><title>BMO Performance Chequing Account</title></head>
          <body>
            <h1>BMO Performance Chequing Account</h1>
            <p>Monthly fee details, debit usage, and included transactions for day-to-day banking.</p>
          </body>
        </html>
        """
        with (
            patch("api_service.source_catalog.fetch_text", side_effect=[homepage_html, detail_html, detail_html]),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account": AiParallelCandidateScore(
                            candidate_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account",
                            predicted_role="detail",
                            relevance_score=8.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                            short_rationale="Likely official chequing detail page.",
                        )
                    },
                    notes=["AI parallel scorer evaluated 1 candidate link(s)."],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="Bank of Montreal",
                country_code="CA",
                product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                homepage_url="https://www.bmo.com/en-ca/main/personal/",
                source_language="en",
            )

        self.assertEqual(len(result.detail_source_ids), 1)
        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertEqual(len(detail_rows), 1)
        self.assertEqual(detail_rows[0]["discovery_metadata"]["selection_path"], "heuristic_plus_ai_plus_page_evidence")
        self.assertGreaterEqual(detail_rows[0]["discovery_metadata"]["page_evidence_score"], 4)
        self.assertIn("AI parallel scorer evaluated 1 candidate link(s).", result.discovery_notes)

    def test_strong_page_evidence_override_applies_across_product_types(self) -> None:
        cases = [
            {
                "product_type": "chequing",
                "url": "https://www.examplebank.ca/personal/accounts/no-fee-echequing",
                "label": "No Fee eChequing",
                "title": "No Fee eChequing Account",
                "heading": "No Fee eChequing Account",
            },
            {
                "product_type": "credit-card",
                "url": "https://www.examplebank.ca/personal/credit-cards/cash-back-visa",
                "label": "Cash Back Visa Card",
                "title": "Cash Back Visa Card",
                "heading": "Cash Back Visa Card",
            },
            {
                "product_type": "mortgage",
                "url": "https://www.examplebank.ca/personal/mortgages/fixed-rate-mortgage",
                "label": "Fixed Rate Mortgage",
                "title": "Fixed Rate Mortgage",
                "heading": "Fixed Rate Mortgage",
            },
        ]

        for case in cases:
            with self.subTest(product_type=case["product_type"]):
                candidate = HomepageCandidate(
                    normalized_url=str(case["url"]),
                    raw_url=str(case["url"]),
                    anchor_text=str(case["label"]),
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=2,
                    supporting_signal=True,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=candidate.normalized_url,
                    predicted_role="supporting_html",
                    relevance_score=6.0,
                    confidence_band="medium",
                    reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
                    short_rationale="Useful product page, but scorer conservatively classified it as supporting.",
                )
                page_evidence = PageEvidenceAssessment(
                    page_evidence_score=9,
                    page_evidence_reason_codes=[
                        "product_identity_signal",
                        "title_semantic_match",
                        "detail_page_layout_signal",
                        "product_type_semantic_match",
                        "pricing_or_feature_signal",
                    ],
                    page_title=str(case["title"]),
                    primary_heading=str(case["heading"]),
                    heading_match=True,
                    attribute_signal_count=4,
                    negative_signal_count=0,
                )

                self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=page_evidence))

    def test_supporting_page_veto_blocks_detail_override_across_product_types(self) -> None:
        cases = [
            ("chequing", "https://www.examplebank.ca/wire-transfers", "not_product_detail"),
            ("savings", "https://www.examplebank.ca/savings-rates", "supporting_terms_or_rates_page"),
            ("credit-card", "https://www.examplebank.ca/credit-card-rates", "supporting_terms_or_rates_page"),
            ("mortgage", "https://www.examplebank.ca/mortgage-calculator", "not_product_detail"),
        ]

        for product_type, url, veto_reason in cases:
            with self.subTest(product_type=product_type):
                candidate = HomepageCandidate(
                    normalized_url=url,
                    raw_url=url,
                    anchor_text="Support page",
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=4,
                    supporting_signal=True,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=url,
                    predicted_role="supporting_html",
                    relevance_score=8.0,
                    confidence_band="high",
                    reason_codes=[veto_reason, "pricing_or_feature_signal"],
                    short_rationale="Relevant supporting material, not a named product detail page.",
                )
                page_evidence = PageEvidenceAssessment(
                    page_evidence_score=9,
                    page_evidence_reason_codes=[
                        "product_identity_signal",
                        "title_semantic_match",
                        "detail_page_layout_signal",
                        "pricing_or_feature_signal",
                    ],
                    page_title="Product rates and tools",
                    primary_heading="Product rates and tools",
                    heading_match=True,
                    attribute_signal_count=4,
                    negative_signal_count=0,
                    product_identity_match=True,
                )

                self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=page_evidence))

    def test_generate_sources_from_homepage_promotes_alterna_no_fee_echequing_detail(self) -> None:
        homepage_html = """
        <html>
          <body>
            <a href="/en/personal/accounts/no-fee-echequing">No Fee eChequing</a>
            <a href="/en/personal/rates/chequing-savings">Chequing & Savings rates</a>
          </body>
        </html>
        """
        detail_html = """
        <html>
          <head><title>Alterna Bank - No Fee eChequing</title></head>
          <body>
            <h1>No-Fee eChequing Account</h1>
            <p>Our chequing account offers day-to-day transactions with no monthly fee.</p>
            <p>FREE, unlimited day-to-day transactions and Interac e-Transfers.</p>
            <p>No minimum balance is required, and overdraft protection is available.</p>
          </body>
        </html>
        """

        candidate_url = "https://www.alternabank.ca/en/personal/accounts/no-fee-echequing"
        with (
            patch("api_service.source_catalog.fetch_text", side_effect=[homepage_html, detail_html, detail_html]),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch("api_service.source_catalog._load_seed_supporting_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        candidate_url: AiParallelCandidateScore(
                            candidate_url=candidate_url,
                            predicted_role="supporting_html",
                            relevance_score=6.0,
                            confidence_band="medium",
                            reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
                            short_rationale="The No Fee eChequing page is the strongest chequing match.",
                        )
                    },
                    notes=["Scored Alterna Bank homepage-discovered candidate links for chequing-product relevance."],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="ALTERNA",
                bank_name="Alterna Bank",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing account for everyday transactions, debit card payments, bill payments, transfers, fees, and overdraft.",
                    "discovery_keywords": ["chequing account", "chequing", "no monthly fee", "unlimited transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.alternabank.ca/en/personal",
                source_language="en",
            )

        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertEqual(len(detail_rows), 1)
        self.assertEqual(detail_rows[0]["normalized_url"], candidate_url)
        self.assertEqual(detail_rows[0]["discovery_metadata"]["ai_predicted_role"], "supporting_html")
        self.assertIn("strong_page_evidence_detail_override", detail_rows[0]["discovery_metadata"]["selection_reason_codes"])

    def test_chequing_support_pages_do_not_override_ai_supporting_role(self) -> None:
        cases = [
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/wire-transfers",
                "Wire Transfers",
                "Send and receive wire transfers through online banking for everyday transactions.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/external-account-transfers",
                "External Account Transfers",
                "Move money between an external account and online banking.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/debit-cards",
                "Debit Cards",
                "Use a debit card for everyday transactions and Interac purchases.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/rates/chequing-savings",
                "Chequing & Savings Rates",
                "Current rates for chequing and savings accounts.",
                ["supporting_terms_or_rates_page", "pricing_or_feature_signal"],
            ),
        ]
        definition = {
            **_product_type_definition("chequing"),
            "description": "A chequing account for everyday transactions, debit payments, transfers, fees, and overdraft.",
            "discovery_keywords": ["chequing account", "everyday banking", "debit card", "transfers"],
        }

        for url, heading, body, reason_codes in cases:
            with self.subTest(url=url), patch(
                "api_service.source_catalog.fetch_text",
                return_value=f"<html><head><title>{heading}</title></head><body><h1>{heading}</h1><p>{body}</p></body></html>",
            ):
                evidence = _score_page_evidence(
                    raw_url=url,
                    fetch_policy=SimpleNamespace(),
                    product_type="chequing",
                    product_type_definition=definition,
                )
                candidate = HomepageCandidate(
                    normalized_url=url,
                    raw_url=url,
                    anchor_text=heading,
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=4,
                    supporting_signal="rates" in url,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=url,
                    predicted_role="supporting_html",
                    relevance_score=7.0,
                    confidence_band="high",
                    reason_codes=reason_codes,
                    short_rationale="Relevant support page, not a named chequing product.",
                )

                self.assertFalse(evidence.product_identity_match)
                self.assertNotIn("product_identity_signal", evidence.page_evidence_reason_codes)
                self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_repeated_support_attribute_counts_once(self) -> None:
        definition = {
            **_product_type_definition("chequing"),
            "description": "A chequing account supporting transfers.",
            "discovery_keywords": ["chequing account"],
        }
        html = "<html><head><title>Wire Transfers</title></head><body><h1>Wire Transfers</h1><p>Transfers transfers transfers.</p></body></html>"
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url="https://www.examplebank.ca/ways-to-bank/wire-transfers",
                fetch_policy=SimpleNamespace(),
                product_type="chequing",
                product_type_definition=definition,
            )

        self.assertEqual(evidence.attribute_signal_count, 1)

    def test_deactivates_only_explicitly_rejected_generated_detail_sources(self) -> None:
        connection = _QueuedConnection([2])

        count = _deactivate_rejected_generated_detail_sources(
            connection,
            bank_code="ALTERNA",
            product_type="chequing",
            normalized_urls=[
                "https://www.alternabank.ca/en/personal/accounts/ways-to-bank/wire-transfers",
                "https://www.alternabank.ca/en/personal/rates/chequing-savings",
            ],
        )

        self.assertEqual(count, 2)
        sql, params = connection.calls[0]
        self.assertIn("seed_source_flag = false", sql)
        self.assertIn("source_id LIKE 'AUTO-%%'", sql)
        self.assertEqual(len(params["normalized_urls"]), 2)

    def test_page_evidence_does_not_treat_product_cta_copy_as_negative(self) -> None:
        detail_html = """
        <html>
          <head><title>High Interest Savings Account</title></head>
          <body>
            <h1>High Interest Savings Account</h1>
            <p>Earn interest on your balance with no monthly fee and flexible withdrawals.</p>
            <a href="/apply">Apply now</a>
            <a href="/open-account">Open account</a>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/savings/high-interest",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "display_name": "Savings",
                    "description": "Savings account with interest, fee, balance, and withdrawal details.",
                    "discovery_keywords": ["savings account", "interest", "withdrawal"],
                },
            )

        self.assertGreaterEqual(result.page_evidence_score, 4)
        self.assertEqual(result.negative_signal_count, 0)

    def test_seed_detail_source_is_promoted_when_page_evidence_fetch_is_unavailable(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical-chequing-account",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical-chequing-account/",
            anchor_text="BMO Practical Chequing Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=8,
            supporting_signal=False,
            seed_source_id="BMO-CHQ-002",
            source_name_hint="BMO Practical Chequing Account",
            priority_hint="P0",
            expected_fields_hint=["product_name", "monthly_fee", "included_transactions"],
        )

        with patch(
            "api_service.source_catalog._score_page_evidence",
            return_value=PageEvidenceAssessment(
                page_evidence_score=0,
                page_evidence_reason_codes=["page_fetch_unavailable"],
                page_title=None,
                primary_heading=None,
                heading_match=False,
                attribute_signal_count=0,
                negative_signal_count=0,
                fetch_error="timed out",
            ),
        ):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="chequing",
                discovery_product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[candidate],
                ai_scores={},
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "BMO-CHQ-002")
        self.assertEqual(rows[0]["discovery_role"], "detail")
        self.assertEqual(rows[0]["discovery_metadata"]["selection_path"], "seed_hint_fetch_unavailable")
        self.assertIn("seed-backed source", " ".join(notes))

    def test_seed_detail_low_page_evidence_with_negative_signal_is_not_promoted(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic/",
            anchor_text="BMO Progressive GIC",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-GIC-003",
            source_name_hint="BMO Progressive GIC detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "term_options", "minimum_deposit"],
        )
        ai_scores = {
            candidate.normalized_url: AiParallelCandidateScore(
                candidate_url=candidate.normalized_url,
                predicted_role="detail",
                relevance_score=0.98,
                confidence_band="high",
                reason_codes=["contains_gic_keyword", "product_specific_slug"],
                short_rationale="Likely an official product detail page, but page evidence is weak.",
            )
        }

        with patch(
            "api_service.source_catalog._score_page_evidence",
            return_value=PageEvidenceAssessment(
                page_evidence_score=3,
                page_evidence_reason_codes=[
                    "title_semantic_match",
                    "product_type_semantic_match",
                    "pricing_or_feature_signal",
                    "insufficient_evidence",
                ],
                page_title="Progressive GIC Search Tool - BMO",
                primary_heading=None,
                heading_match=False,
                attribute_signal_count=1,
                negative_signal_count=1,
            ),
        ):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                discovery_product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit.",
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[candidate],
                ai_scores=ai_scores,
            )

        self.assertEqual(rows, [])
        self.assertIn("rejected all tentative detail pages", " ".join(notes))

    def test_seed_detail_candidates_are_not_displaced_by_high_scoring_homepage_links(self) -> None:
        seed_candidates = [
            HomepageCandidate(
                normalized_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/seed-{index}",
                raw_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/seed-{index}/",
                anchor_text=f"Seed {index}",
                source_type="html",
                origin="seed_detail_hint",
                heuristic_score=0,
                supporting_signal=False,
                seed_source_id=f"BMO-CHQ-00{index}",
                source_name_hint=f"BMO seed {index}",
                priority_hint="P0",
                expected_fields_hint=["product_name"],
            )
            for index in range(1, 6)
        ]
        homepage_candidates = [
            HomepageCandidate(
                normalized_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/high-score-{index}",
                raw_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/high-score-{index}/",
                anchor_text=f"High score {index}",
                source_type="html",
                origin="homepage_or_hub_link",
                heuristic_score=20,
                supporting_signal=False,
                seed_source_id=None,
                source_name_hint=None,
                priority_hint=None,
                expected_fields_hint=[],
            )
            for index in range(1, 8)
        ]

        ordered = _ordered_detail_candidates(candidates=[*homepage_candidates, *seed_candidates], ai_scores={})

        self.assertEqual([item.seed_source_id for item in ordered[:5]], [f"BMO-CHQ-00{index}" for index in range(1, 6)])
        self.assertEqual(len([item for item in ordered if item.seed_source_id]), 5)
        self.assertGreater(len([item for item in ordered if not item.seed_source_id]), 0)

    def test_seed_detail_rejection_does_not_block_ai_scored_homepage_detail(self) -> None:
        seed_candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic/",
            anchor_text="BMO Progressive GIC",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-GIC-003",
            source_name_hint="BMO Progressive GIC detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "term_options", "minimum_deposit"],
        )
        homepage_candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/special-rate-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/special-rate-gic/",
            anchor_text="Special Rate GIC",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=4,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_scores = {
            homepage_candidate.normalized_url: AiParallelCandidateScore(
                candidate_url=homepage_candidate.normalized_url,
                predicted_role="detail",
                relevance_score=6.0,
                confidence_band="high",
                reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                short_rationale="Likely an official GIC detail page.",
            )
        }

        def fake_page_evidence(*, raw_url: str, **_: object) -> PageEvidenceAssessment:
            if "progressive-gic" in raw_url:
                return PageEvidenceAssessment(
                    page_evidence_score=3,
                    page_evidence_reason_codes=["insufficient_evidence"],
                    page_title="Progressive GIC Search Tool - BMO",
                    primary_heading=None,
                    heading_match=False,
                    attribute_signal_count=1,
                    negative_signal_count=1,
                )
            return PageEvidenceAssessment(
                page_evidence_score=8,
                page_evidence_reason_codes=["title_semantic_match", "detail_page_layout_signal", "pricing_or_feature_signal"],
                page_title="Special Rate GIC",
                primary_heading="Special Rate GIC",
                heading_match=True,
                attribute_signal_count=3,
                negative_signal_count=0,
            )

        with patch("api_service.source_catalog._score_page_evidence", side_effect=fake_page_evidence):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                discovery_product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit.",
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[seed_candidate, homepage_candidate],
                ai_scores=ai_scores,
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["normalized_url"], homepage_candidate.normalized_url)
        self.assertEqual(rows[0]["discovery_metadata"]["selection_path"], "heuristic_plus_ai_plus_page_evidence")
        self.assertIn("promoted 1 detail source", " ".join(notes))

    def test_seed_detail_candidate_can_promote_despite_page_negative_terms(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical/",
            anchor_text="BMO Practical Chequing Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=0,
            supporting_signal=False,
            seed_source_id="BMO-CHQ-002",
            source_name_hint="BMO Practical Chequing Account",
            priority_hint="P0",
            expected_fields_hint=["product_name"],
        )
        page_evidence = PageEvidenceAssessment(
            page_evidence_score=5,
            page_evidence_reason_codes=["title_semantic_match", "insufficient_evidence"],
            page_title="Low Fee Chequing Account: Practical Chequing Account - BMO Canada",
            primary_heading="Practical Chequing Account",
            heading_match=True,
            attribute_signal_count=2,
            negative_signal_count=3,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=None, page_evidence=page_evidence))

    def test_generate_sources_from_homepage_uses_exact_product_type_seed_details(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Savings Account",
            primary_heading="BMO Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004", "BMO-SAV-005"}.issubset(source_ids))
        self.assertIn("BMO-SAV-006", source_ids)
        self.assertIn("BMO-SAV-007", source_ids)
        self.assertTrue(all(str(item["product_type"]) == "savings" for item in result.rows))

    def test_generate_sources_from_homepage_uses_seed_hints_for_known_bank_code_aliases(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="TD ePremium Savings Account",
            primary_heading="TD ePremium Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="TB",
                bank_name="TD Bank",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.td.com/",
                source_language="en",
            )

        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertGreaterEqual(len(detail_rows), 1)
        self.assertTrue(all(item["bank_code"] == "TB" for item in detail_rows))
        self.assertTrue(all(str(item["source_id"]).startswith("AUTO-TB-") for item in detail_rows))
        self.assertTrue(any("td.com" in item["normalized_url"] for item in detail_rows))

    def test_generate_sources_from_homepage_promotes_cibc_seed_details_when_ai_is_unavailable(self) -> None:
        weak_but_official_seed_evidence = PageEvidenceAssessment(
            page_evidence_score=3,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal", "insufficient_evidence"],
            page_title="CIBC Smart Account",
            primary_heading="CIBC Smart Account",
            heading_match=True,
            attribute_signal_count=1,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={},
                    notes=[
                        "AI parallel scorer was unavailable: OpenAI Responses API request failed with status 429: insufficient_quota",
                        "Deterministic homepage discovery fallback will evaluate bounded candidates.",
                    ],
                    ai_unavailable=True,
                ),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_but_official_seed_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing accounts for everyday banking with monthly fees, debit transactions, Interac, and overdraft.",
                    "discovery_keywords": ["chequing", "chequing account", "monthly fee", "transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.cibc.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"CIBC-CHQ-002", "CIBC-CHQ-003"}.issubset(source_ids))
        detail_rows = [item for item in result.rows if item["source_id"] in {"CIBC-CHQ-002", "CIBC-CHQ-003"}]
        self.assertTrue(all(item["discovery_metadata"]["selection_path"] == "seed_hint_ai_unavailable_low_page_evidence" for item in detail_rows))
        self.assertTrue(all(item["discovery_metadata"]["ai_unavailable"] for item in detail_rows))
        self.assertTrue(any("Deterministic homepage discovery fallback" in note for note in result.discovery_notes))

    def test_generate_sources_from_homepage_keeps_cibc_seed_details_when_ai_scores_but_page_evidence_is_weak(self) -> None:
        weak_but_official_seed_evidence = PageEvidenceAssessment(
            page_evidence_score=3,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal", "insufficient_evidence"],
            page_title="CIBC Smart Account",
            primary_heading="CIBC Smart Account",
            heading_match=True,
            attribute_signal_count=1,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        "https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html": AiParallelCandidateScore(
                            candidate_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
                            predicted_role="supporting_html",
                            relevance_score=3.0,
                            confidence_band="medium",
                            reason_codes=["pricing_or_feature_signal"],
                            short_rationale="Useful chequing account page but scorer was uncertain.",
                        )
                    },
                    notes=["Scored CIBC candidate links for chequing-account homepage-first discovery."],
                ),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_but_official_seed_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing accounts for everyday banking with monthly fees, debit transactions, Interac, and overdraft.",
                    "discovery_keywords": ["chequing", "chequing account", "monthly fee", "transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.cibc.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"CIBC-CHQ-002", "CIBC-CHQ-003"}.issubset(source_ids))
        detail_row = next(item for item in result.rows if item["source_id"] == "CIBC-CHQ-002")
        self.assertEqual(detail_row["discovery_metadata"]["selection_path"], "seed_hint_low_page_evidence")
        self.assertEqual(detail_row["discovery_metadata"]["ai_predicted_role"], "supporting_html")

    def test_generate_sources_from_homepage_uses_definition_semantics_for_discovery_profile(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Savings Account",
            primary_heading="BMO Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="saving",
                product_type_definition={
                    **_product_type_definition("saving"),
                    "display_name": "Savings",
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004", "BMO-SAV-005"}.issubset(source_ids))
        self.assertTrue(all(str(item["product_type"]) == "saving" for item in result.rows))
        self.assertTrue(any("used `savings` discovery signals" in note for note in result.discovery_notes))

    def test_product_type_discovery_profile_uses_code_terms_for_gic_term_deposit(self) -> None:
        self.assertEqual(
            _product_type_discovery_profile(
                "gic-term-deposit",
                {
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "Term Deposit",
                    "description": "Deposit product.",
                    "discovery_keywords": [],
                },
            ),
            "gic",
        )

    def test_generate_sources_from_homepage_keeps_seed_detail_when_ai_marks_irrelevant(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Progressive GIC",
            primary_heading="BMO Progressive GIC",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )
        ai_scores = {
            "https://www.bmo.com/main/personal/investments/gic/progressive-gic": AiParallelCandidateScore(
                candidate_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
                predicted_role="irrelevant",
                relevance_score=0.1,
                confidence_band="low",
                reason_codes=["insufficient_evidence"],
                short_rationale="AI scorer was not confident.",
            )
        }

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores=ai_scores, notes=["AI marked seed as irrelevant"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit with rate, term, redeemability, and minimum deposit details.",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate", "maturity"],
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertIn("BMO-GIC-003", source_ids)
        detail_row = next(item for item in result.rows if item["source_id"] == "BMO-GIC-003")
        self.assertEqual(detail_row["product_type"], "gic-term-deposit")
        self.assertEqual(detail_row["discovery_metadata"]["ai_predicted_role"], "irrelevant")
        self.assertTrue(any("used `gic` discovery signals" in note for note in result.discovery_notes))

    def test_generate_sources_from_homepage_keeps_seed_detail_with_low_page_evidence(self) -> None:
        low_evidence = PageEvidenceAssessment(
            page_evidence_score=1,
            page_evidence_reason_codes=["insufficient_evidence"],
            page_title="BMO Progressive GIC Search Tool",
            primary_heading="Progressive GIC Search Tool",
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=low_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit with rate, term, redeemability, and minimum deposit details.",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate", "maturity"],
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        detail_row = next(item for item in result.rows if item["source_id"] == "BMO-GIC-003")
        self.assertEqual(detail_row["product_type"], "gic-term-deposit")
        self.assertEqual(detail_row["discovery_metadata"]["selection_path"], "seed_hint_low_page_evidence")
        self.assertTrue(any("low page evidence" in note for note in result.discovery_notes))

    def test_ai_candidate_scorer_accepts_discovery_product_type_profile(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier/",
            anchor_text="Savings Amplifier",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-SAV-002",
            source_name_hint="BMO Savings Amplifier Account",
            priority_hint="P0",
            expected_fields_hint=["product_name"],
        )

        with patch("api_service.source_catalog.os.getenv", side_effect=lambda key, default="": "openai" if key == "FPDS_LLM_PROVIDER" else ""):
            result = _score_candidate_links_with_ai(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="saving",
                discovery_product_type="savings",
                product_type_definition={
                    **_product_type_definition("saving"),
                    "display_name": "Savings",
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                },
                source_language="en",
                homepage_url="https://www.bmo.com/",
                normalized_homepage_url="https://www.bmo.com/",
                homepage_fetch_error=None,
                candidates=[candidate],
            )

        self.assertEqual(result.scores, {})
        self.assertTrue(any("provider or API key was not configured" in note for note in result.notes))
        self.assertTrue(result.ai_unavailable)

    def test_ai_candidate_scorer_records_failed_execution_when_openai_quota_is_exceeded(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
            raw_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
            anchor_text="CIBC Smart Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=8,
            supporting_signal=False,
            seed_source_id="CIBC-CHQ-002",
            source_name_hint="CIBC Smart Account detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "monthly_fee"],
        )

        def fake_getenv(key: str, default: str = "") -> str:
            values = {
                "FPDS_LLM_PROVIDER": "openai",
                "FPDS_LLM_API_KEY": "test-key",
                "FPDS_LLM_MODEL": "gpt-test",
            }
            return values.get(key, default)

        with (
            patch("api_service.source_catalog.os.getenv", side_effect=fake_getenv),
            patch(
                "api_service.source_catalog._invoke_openai_parallel_scorer",
                side_effect=RuntimeError("OpenAI Responses API request failed with status 429: insufficient_quota"),
            ),
        ):
            result = _score_candidate_links_with_ai(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                discovery_product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                source_language="en",
                homepage_url="https://www.cibc.com/",
                normalized_homepage_url="https://www.cibc.com/",
                homepage_fetch_error=None,
                candidates=[candidate],
                run_id="run-cibc-chequing",
                correlation_id="corr-001",
                request_id="req-001",
            )

        self.assertEqual(result.scores, {})
        self.assertTrue(result.ai_unavailable)
        self.assertIsNotNone(result.model_execution_record)
        assert result.model_execution_record is not None
        self.assertEqual(result.model_execution_record["execution_status"], "failed")
        self.assertEqual(result.model_execution_record["execution_metadata"]["fallback_mode"], "deterministic")
        self.assertIn("429", result.model_execution_record["execution_metadata"]["error_summary"])
        self.assertTrue(any("Deterministic homepage discovery fallback" in note for note in result.notes))

    def test_generate_sources_from_homepage_uses_bmo_seed_details_and_filters_unrelated_support(self) -> None:
        homepage_links = [
            SimpleNamespace(
                normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
                resolved_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier/",
                anchor_text="Savings Amplifier High interest rate",
                source_type="html",
            ),
            SimpleNamespace(
                normalized_url="https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
                resolved_url="https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
                anchor_text="Modern Slavery Act Statement",
                source_type="pdf",
            ),
            SimpleNamespace(
                normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/global-terms-and-conditions",
                resolved_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/global-terms-and-conditions#onehundredandsix",
                anchor_text="106",
                source_type="html",
            ),
        ]
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "detail_page_layout_signal", "pricing_or_feature_signal"],
            page_title="BMO Chequing Account",
            primary_heading="BMO Chequing Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=homepage_links),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="Bank of Montreal",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Daily transaction account with monthly fee, debit card usage, and banking-plan benefits.",
                    "discovery_keywords": ["chequing", "daily banking", "banking plan"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-CHQ-002", "BMO-CHQ-003", "BMO-CHQ-004", "BMO-CHQ-005", "BMO-CHQ-008"}.issubset(source_ids))
        self.assertIn("BMO-CHQ-006", source_ids)
        self.assertIn("BMO-CHQ-007", source_ids)
        self.assertNotIn(
            "https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
            {str(item["normalized_url"]) for item in result.rows},
        )
        self.assertNotIn(
            "https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
            {str(item["normalized_url"]) for item in result.rows},
        )
        terms_row = next(item for item in result.rows if item["source_id"] == "BMO-CHQ-007")
        self.assertEqual(terms_row["source_name"], "BMO bank account terms and conditions")

    def test_generate_sources_from_homepage_uses_seed_entry_url_for_known_bank_aliases(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="Scotiabank Savings Account",
            primary_heading="Scotiabank Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="SCOTIABANK",
                bank_name="Scotiabank",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.scotiabank.com/",
                source_language="en",
            )

        entry_row = next(item for item in result.rows if item["discovery_role"] == "entry")
        self.assertEqual(
            entry_row["normalized_url"],
            "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts.html",
        )
        self.assertEqual(entry_row["discovery_metadata"]["candidate_origin"], "seed_entry_hint")
        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertGreaterEqual(len(detail_rows), 1)
        self.assertTrue(all(str(item["source_id"]).startswith("AUTO-SCOTIABANK-SAV-") for item in detail_rows))

    def test_generate_sources_from_homepage_keeps_seed_entry_when_detail_validation_fails(self) -> None:
        weak_detail_evidence = PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["insufficient_evidence"],
            page_title="Search Tool",
            primary_heading="Search Tool",
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "description": "Guaranteed investment certificate and term deposit product type",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate"],
                    "expected_fields": ["product_name", "term_options", "interest_rate_summary"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        entry_rows = [item for item in result.rows if item["discovery_role"] == "entry"]
        self.assertEqual(len(entry_rows), 1)
        self.assertEqual(entry_rows[0]["normalized_url"], "https://www.bmo.com/en-ca/main/personal/investments/gic")
        self.assertIn("BMO-GIC-002", {str(item["source_id"]) for item in result.rows})
        self.assertNotIn("BMO-GIC-003", {str(item["source_id"]) for item in result.rows})

    def test_out_of_scope_product_urls_are_not_promoted_as_detail_sources(self) -> None:
        cases = [
            {
                "product_type": "gic",
                "candidate_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/air-miles",
                "title": "BMO AIR MILES Chequing Account",
                "heading": "BMO AIR MILES Chequing Account",
                "body": "Monthly fee and included transactions for a chequing account.",
                "reason_code": "other_product_type",
            },
            {
                "product_type": "gic",
                "candidate_url": "https://www.cibc.com/en/personal-banking/bank-accounts/savings-accounts.html",
                "title": "CIBC Savings Accounts",
                "heading": "Savings Accounts",
                "body": "Earn interest on your savings balance.",
                "reason_code": "other_product_type",
            },
            {
                "product_type": "savings",
                "candidate_url": "https://www.cibc.com/en/personal-banking/investments/tax-free-savings-accounts.html",
                "title": "Tax-Free Savings Account",
                "heading": "Tax-Free Savings Account",
                "body": "TFSA registered plan information and contribution details.",
                "reason_code": "registered_plan_wrapper",
            },
            {
                "product_type": "chequing",
                "candidate_url": "https://www.scotiabank.com/ca/en/about/investors-shareholders.html",
                "title": "Investors and Shareholders",
                "heading": "Investors and Shareholders",
                "body": "Investor relations and shareholder information.",
                "reason_code": "non_product_or_investor_page",
            },
        ]

        for case in cases:
            with self.subTest(case=case["candidate_url"]):
                candidate = HomepageCandidate(
                    normalized_url=case["candidate_url"],
                    raw_url=case["candidate_url"],
                    anchor_text=str(case["heading"]),
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=8,
                    supporting_signal=False,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_scores = {
                    case["candidate_url"]: AiParallelCandidateScore(
                        candidate_url=case["candidate_url"],
                        predicted_role="detail",
                        relevance_score=9.0,
                        confidence_band="high",
                        reason_codes=["product_type_semantic_match"],
                        short_rationale="The scorer thought this was a detail page.",
                    )
                }
                html = f"""
                <html>
                  <head><title>{case['title']}</title></head>
                  <body>
                    <h1>{case['heading']}</h1>
                    <p>{case['body']}</p>
                  </body>
                </html>
                """

                with patch("api_service.source_catalog.fetch_text", return_value=html):
                    rows, _rejected_urls, notes = _promote_detail_candidates(
                        bank_code="TEST",
                        bank_name="Test Bank",
                        country_code="CA",
                        product_type=str(case["product_type"]),
                        discovery_product_type=str(case["product_type"]),
                        product_type_definition={
                            **_product_type_definition(str(case["product_type"])),
                            "description": "Canadian personal deposit product with rates, fees, term, balance, or transaction details.",
                            "discovery_keywords": [str(case["product_type"])],
                        },
                        source_language="en",
                        fetch_policy=SimpleNamespace(),
                        candidates=[candidate],
                        ai_scores=ai_scores,
                    )

                self.assertEqual(rows, [])
                self.assertIn("rejected all tentative detail pages", " ".join(notes))

                with patch("api_service.source_catalog.fetch_text", return_value=html):
                    evidence = _score_page_evidence(
                        raw_url=case["candidate_url"],
                        fetch_policy=SimpleNamespace(),
                        product_type=str(case["product_type"]),
                        product_type_definition={
                            **_product_type_definition(str(case["product_type"])),
                            "description": "Canadian personal deposit product with rates, fees, term, balance, or transaction details.",
                            "discovery_keywords": [str(case["product_type"])],
                        },
                    )
                self.assertIn(case["reason_code"], evidence.page_evidence_reason_codes)

    def test_upsert_source_registry_rows_targets_unique_scope_and_returns_persisted_rows(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "source_id": "AUTO-BMO-CHQ-existing",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing catalog entry",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ]
        )

        result = _upsert_source_registry_rows(
            connection,
            [
                {
                    "source_id": "AUTO-BMO-CHQ-detail",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ],
        )

        self.assertEqual(result[0]["source_id"], "AUTO-BMO-CHQ-existing")
        sql, _params = connection.calls[0]
        self.assertIn("ON CONFLICT (bank_code, product_type, normalized_url, source_type) DO UPDATE", sql)
        self.assertIn("WHEN source_registry_item.status = 'removed'", sql)

    def test_upsert_source_registry_rows_preserves_removed_status_on_conflict(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "source_id": "AUTO-BMO-CHQ-removed",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "removed",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "removed_by_operator",
                }
            ]
        )

        result = _upsert_source_registry_rows(
            connection,
            [
                {
                    "source_id": "AUTO-BMO-CHQ-detail",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ],
        )

        self.assertEqual(result[0]["status"], "removed")
        self.assertEqual(result[0]["change_reason"], "removed_by_operator")

    def test_recognized_bank_migration_adds_logos_and_full_active_product_type_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0020_canada_recognized_banks_full_coverage.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN IF NOT EXISTS logo_url", migration_sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS logo_alt_text", migration_sql)
        self.assertIn("CROSS JOIN product_type_registry", migration_sql)
        self.assertIn("bank.status = 'active'", migration_sql)
        self.assertIn("product_type_registry.status = 'active'", migration_sql)
        self.assertIn("ON CONFLICT (bank_code, country_code, product_type) DO UPDATE", migration_sql)
        for bank_code in ("NATIONAL", "TANGERINE", "SIMPLII", "EQBANK", "MANULIFE", "ROGERSBANK"):
            self.assertIn(f"('{bank_code}'", migration_sql)

    def test_vancity_migration_adds_full_active_product_type_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0021_vancity_credit_union_full_coverage.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("'VANCITY'", migration_sql)
        self.assertIn("'https://www.vancity.com/'", migration_sql)
        self.assertIn("'https://www.vancity.com/favicon.ico'", migration_sql)
        self.assertIn("CROSS JOIN product_type_registry", migration_sql)
        self.assertIn("bank.bank_code = 'VANCITY'", migration_sql)
        self.assertIn("bank.status = 'active'", migration_sql)
        self.assertIn("product_type_registry.status = 'active'", migration_sql)
        self.assertIn("ON CONFLICT (bank_code, country_code, product_type) DO UPDATE", migration_sql)

    def test_bank_logo_refresh_uses_official_assets_without_overwriting_custom_urls(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0022_bank_logo_asset_refresh.sql"
        ).read_text(encoding="utf-8")
        public_logo_component = (
            repo_root / "app" / "public" / "src" / "components" / "fpds" / "public" / "bank-logo.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("official_logo_refresh", migration_sql)
        self.assertIn("bank.logo_url IS NULL OR bank.logo_url = official_logo_refresh.previous_logo_url", migration_sql)
        self.assertIn("0022_bank_logo_asset_refresh.sql", migration_sql)
        for bank_code in ("NATIONAL", "TANGERINE", "EQBANK", "MANULIFE", "ALTERNA", "FNBC", "SIMPLII", "VERSABANK"):
            self.assertIn(f"'{bank_code}'", migration_sql)
            self.assertIn(f"{bank_code}: {{ src:", public_logo_component)

        self.assertIn('onError={() => setFailed(true)}', public_logo_component)
        self.assertNotIn('rounded-md border border-border/70 bg-white', public_logo_component)

    def test_homepage_parallel_scorer_uses_default_medium_reasoning_effort_when_omitted(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-homepage-score-001",
                "model": "gpt-5.6-luna",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"ok","candidate_scores":[]}',
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode("utf-8")

        with patch("api_service.source_catalog.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            result, metadata = _invoke_openai_parallel_scorer(
                model_id="gpt-5.6-luna",
                api_key="test-key",
                payload={"product_type": "chequing", "candidates": []},
            )

        request_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(request_body["model"], "gpt-5.6-luna")
        self.assertNotIn("reasoning", request_body)
        self.assertEqual(result, {"summary": "ok", "candidate_scores": []})
        self.assertEqual(metadata["model_id"], "gpt-5.6-luna")

    def test_gpt_5_6_luna_reasoning_effort_is_stage_specific(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        default_medium_paths = (
            repo_root / "worker" / "pipeline" / "fpds_ai_runtime.py",
            repo_root / "api" / "service" / "api_service" / "source_catalog.py",
        )
        for source_path in default_medium_paths:
            source = source_path.read_text(encoding="utf-8")
            self.assertIn("gpt-5.6-luna", source)
            self.assertNotIn('"reasoning": {"effort": "none"}', source)

        keyword_generator_source = (repo_root / "api" / "service" / "api_service" / "product_types.py").read_text(encoding="utf-8")
        self.assertIn("gpt-5.6-luna", keyword_generator_source)
        self.assertIn('"reasoning": {"effort": "none"}', keyword_generator_source)


if __name__ == "__main__":
    unittest.main()
