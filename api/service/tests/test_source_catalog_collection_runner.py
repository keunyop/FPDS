from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from api_service import source_catalog_collection_runner, source_collection_runner
from api_service.source_catalog import CatalogItemMaterializationResult, CoverageRouteRepairResult


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
    def __init__(self, responses: list[object] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self._responses = list(responses or [])
        self.committed = False

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _Cursor:
        self.calls.append((sql, params or {}))
        payload = self._responses.pop(0) if self._responses else None
        return _Cursor(payload)

    def commit(self) -> None:
        self.committed = True


class _ConnectionContext:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    def __enter__(self) -> _Connection:
        return self.connection

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class SourceCatalogCollectionRunnerTests(unittest.TestCase):
    def test_failure_persistence_error_is_contained_for_next_group(self) -> None:
        with patch(
            "api_service.source_catalog_collection_runner._mark_run_finished",
            side_effect=RuntimeError("temporary database DNS failure"),
        ):
            source_catalog_collection_runner._mark_run_failure_best_effort(
                run_id="run-001",
                run_metadata={"discovery_status": "materialization_failed"},
                failure=RuntimeError("collection failed"),
            )

    def test_active_scope_excludes_other_country_and_language_routes(self) -> None:
        connection = _Connection(
            [
                [
                    {
                        "source_id": "AUTO-TBNA-US",
                        "discovery_role": "detail",
                        "source_name": "TD Beyond Checking",
                        "source_url": "https://www.td.com/us/en/personal-banking/checking-accounts/beyond",
                        "purpose": "detail",
                        "expected_fields": [],
                    },
                    {
                        "source_id": "AUTO-TBNA-CA",
                        "discovery_role": "detail",
                        "source_name": "TD Canadian Chequing",
                        "source_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/chequing-accounts/every-day-chequing-account",
                        "purpose": "detail",
                        "expected_fields": [],
                    },
                    {
                        "source_id": "AUTO-TBNA-ZH",
                        "discovery_role": "detail",
                        "source_name": "TD Chinese Chequing",
                        "source_url": "https://zh.td.com/ca/en/personal-banking/products/bank-accounts/chequing-accounts/every-day-chequing-account",
                        "purpose": "detail",
                        "expected_fields": [],
                    },
                ]
            ]
        )

        scope = source_catalog_collection_runner._load_active_collection_scope(
            connection,
            bank_code="TBNA",
            country_code="US",
            product_type="chequing",
            source_language="en",
        )

        self.assertEqual(scope["target_source_ids"], ["AUTO-TBNA-US"])
        self.assertEqual(scope["collection_source_ids"], ["AUTO-TBNA-US"])
        sql, params = connection.calls[0]
        self.assertIn("country_code = %(country_code)s", sql)
        self.assertEqual(params["country_code"], "US")

    def test_active_card_scope_excludes_legacy_auto_loan_supporting_sources(self) -> None:
        connection = _Connection(
            [
                [
                    {
                        "source_id": "CARD-DETAIL",
                        "discovery_role": "detail",
                        "source_name": "Travel Rewards Credit Card",
                        "source_url": "https://www.bank.example/credit-cards/travel-rewards",
                        "purpose": "detail",
                        "expected_fields": [],
                    },
                    {
                        "source_id": "CARD-PRICING",
                        "discovery_role": "supporting_html",
                        "source_name": "Pricing and terms",
                        "source_url": "https://www.bank.example/disclosures/card?offerId=42",
                        "purpose": "pricing companion",
                        "expected_fields": [],
                    },
                    {
                        "source_id": "AUTO-LOAN-RATES",
                        "discovery_role": "supporting_html",
                        "source_name": "Auto Loan Rates",
                        "source_url": "https://www.bank.example/auto-loans/auto-loan-rates",
                        "purpose": "legacy broad support",
                        "expected_fields": [],
                    },
                ]
            ]
        )

        scope = source_catalog_collection_runner._load_active_collection_scope(
            connection,
            bank_code="EX",
            country_code="US",
            product_type="credit-card",
            source_language="en",
        )

        self.assertEqual(scope["target_source_ids"], ["CARD-DETAIL"])
        self.assertEqual(scope["collection_source_ids"], ["CARD-DETAIL", "CARD-PRICING"])

    def test_catalog_failure_metadata_retains_exact_worker_stage(self) -> None:
        failure = source_collection_runner.WorkerStageError(
            stage_name="fpds_snapshot",
            failure_kind="nonzero_exit",
            return_code=1,
            diagnostic="psql command failed: country_code is required",
        )
        metadata = source_catalog_collection_runner._catalog_run_metadata(
            plan={
                "collection_id": "collection-001",
                "correlation_id": "corr-001",
                "request_id": "req-001",
            },
            group={
                "catalog_item_id": "catalog-us-boan-mortgage-001",
                "bank_code": "BOAN",
                "country_code": "US",
                "product_type": "mortgage",
                "product_family": "lending",
                "source_language": "en",
            },
            discovery_status="materialization_failed",
            discovery_notes=[str(failure)],
            generated_source_ids=[],
            collection_source_ids=[],
            target_source_ids=[],
            failure=failure,
        )

        self.assertEqual(metadata["pipeline_stage"], "source_catalog_collection")
        self.assertEqual(metadata["failed_stage"], "fpds_snapshot")
        self.assertEqual(metadata["stage_failure"]["failure_kind"], "nonzero_exit")
        self.assertEqual(metadata["stage_failure"]["return_code"], 1)

    def test_only_detail_sources_can_produce_standalone_candidates(self) -> None:
        detail = {"discovery_role": "detail", "product_type": "gic"}
        linked_terms = {
            "discovery_role": "linked_pdf",
            "product_type": "gic",
            "source_name": "Registered Term Deposit Terms",
            "purpose": "Auto-generated linked PDF source for GIC",
            "expected_fields": ["product_name", "standard_rate"],
        }

        self.assertTrue(source_catalog_collection_runner._is_candidate_producing_source(detail, product_type="gic"))
        self.assertFalse(source_catalog_collection_runner._is_candidate_producing_source(linked_terms, product_type="gic"))

    def test_run_group_marks_run_completed_when_no_detail_sources_are_found(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "groups": [],
        }
        group = {
            "run_id": "run-001",
            "catalog_item_id": "catalog-ca-bmo-chequing-12345678",
            "bank_code": "BMO",
            "bank_name": "Bank of Montreal",
            "country_code": "CA",
            "product_type": "chequing",
            "source_language": "en",
            "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
            "normalized_homepage_url": "https://www.bmo.com/en-ca/main/personal",
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[],
                    discovery_notes=["Homepage discovery completed but no candidate-producing detail sources were identified."],
                    detail_source_ids=[],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={"collection_source_ids": [], "target_source_ids": []},
            ),
            patch(
                "api_service.source_catalog_collection_runner.repair_catalog_coverage_route",
                return_value=CoverageRouteRepairResult(
                    status="uncertain",
                    coverage_source_url=None,
                    coverage_source_metadata={},
                    notes=["Coverage route remained uncertain."],
                ),
            ),
            patch("api_service.source_catalog_collection_runner.prepare_source_collection") as prepare_collection,
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        prepare_collection.assert_not_called()
        run_group.assert_not_called()
        self.assertFalse(connection.committed)
        update_call = next(params for sql, params in connection.calls if "UPDATE ingestion_run" in sql)
        self.assertEqual(update_call["run_id"], "run-001")
        self.assertEqual(update_call["run_state"], "completed")
        self.assertTrue(update_call["partial_completion_flag"])
        self.assertEqual(
            update_call["error_summary"],
            "Homepage discovery produced no detail sources eligible for collection. Homepage discovery completed but no candidate-producing detail sources were identified.",
        )

    def test_no_detail_summary_prioritizes_decisive_rejection_diagnostics(self) -> None:
        summary = source_catalog_collection_runner._no_detail_sources_summary(
            [
                "AI parallel scorer evaluated 32 candidate link(s).",
                "Page evidence was unavailable for https://example.com/article: HTTP 503.",
                "Homepage discovery candidate validation rejected all tentative detail pages.",
                "Detail rejection summary: page_evidence_below_threshold=1, page_fetch_unavailable=31.",
                "Rejected detail https://example.com/product: reason=page_evidence_below_threshold; ai=detail/9.0.",
            ]
        )

        self.assertIn("Detail rejection summary:", summary)
        self.assertIn("Rejected detail https://example.com/product", summary)
        self.assertNotIn("HTTP 503", summary)

    def test_run_group_closes_verified_retired_product_without_partial_failure(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-retired",
            "correlation_id": "corr-retired",
            "request_id": "req-retired",
            "actor": {"user_id": "usr-admin", "role": "admin"},
            "groups": [],
        }
        group = {
            "run_id": "run-retired",
            "catalog_item_id": "catalog-us-gsbu-personal-loan",
            "bank_code": "GSBU",
            "bank_name": "Goldman Sachs Bank USA",
            "country_code": "US",
            "product_type": "personal-loan",
            "product_family": "lending",
            "source_language": "en",
            "homepage_url": "https://www.goldmansachs.com/",
            "normalized_homepage_url": "https://www.goldmansachs.com/",
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[],
                    discovery_notes=["Homepage discovery found no detail sources."],
                    detail_source_ids=[],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={"collection_source_ids": [], "target_source_ids": []},
            ),
            patch(
                "api_service.source_catalog_collection_runner.repair_catalog_coverage_route",
                return_value=CoverageRouteRepairResult(
                    status="not_currently_offered",
                    coverage_source_url=None,
                    coverage_source_metadata={"verification_status": "verified_not_currently_offered"},
                    notes=["Official evidence verified that this Product Type is not currently offered."],
                ),
            ),
            patch("api_service.source_catalog_collection_runner.prepare_source_collection") as prepare_collection,
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        prepare_collection.assert_not_called()
        run_group.assert_not_called()
        update_call = next(params for sql, params in connection.calls if "UPDATE ingestion_run" in sql)
        self.assertEqual(update_call["run_state"], "completed")
        self.assertFalse(update_call["partial_completion_flag"])
        self.assertIsNone(update_call["error_summary"])
        run_metadata = json.loads(str(update_call["run_metadata"]))
        self.assertEqual(run_metadata["discovery_status"], "product_not_currently_offered")

    def test_run_group_metadata_infers_lending_product_family(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-cc-001",
            "correlation_id": "corr-cc-001",
            "request_id": "req-cc-001",
            "groups": [],
        }
        group = {
            "run_id": "run-cc-001",
            "catalog_item_id": "catalog-ca-rbc-credit-card-12345678",
            "bank_code": "RBC",
            "bank_name": "RBC",
            "country_code": "CA",
            "product_type": "credit_card",
            "source_language": "en",
            "homepage_url": "https://www.rbcroyalbank.com/personal.html",
            "normalized_homepage_url": "https://www.rbcroyalbank.com/personal",
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[],
                    discovery_notes=["Homepage discovery completed but no candidate-producing detail sources were identified."],
                    detail_source_ids=[],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={"collection_source_ids": [], "target_source_ids": []},
            ),
            patch(
                "api_service.source_catalog_collection_runner.repair_catalog_coverage_route",
                return_value=CoverageRouteRepairResult(
                    status="uncertain",
                    coverage_source_url=None,
                    coverage_source_metadata={},
                    notes=["Coverage route remained uncertain."],
                ),
            ),
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        update_call = next(params for sql, params in connection.calls if "UPDATE ingestion_run" in sql)
        run_metadata = json.loads(str(update_call["run_metadata"]))
        self.assertEqual(run_metadata["product_type"], "credit-card")
        self.assertEqual(run_metadata["product_family"], "lending")

    def test_run_group_uses_registered_product_type_code_without_aliasing(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "triggered_by": "admin@example.com",
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-001",
            "catalog_item_id": "catalog-ca-bmo-saving-legacy",
            "bank_code": "BMO",
            "bank_name": "BMO",
            "country_code": "CA",
            "product_type": "saving",
            "source_language": "en",
            "homepage_url": "https://www.bmo.com/",
            "normalized_homepage_url": "https://www.bmo.com/",
            "coverage_source_url": "https://www.bmo.com/main/personal/bank-accounts/savings/",
        }
        prepared_plan = {
            "triggered_by": "admin@example.com",
            "groups": [{"run_id": "run-001"}],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[
                        {
                            "source_id": "BMO-SAV-002",
                            "discovery_role": "detail",
                            "status": "active",
                        }
                    ],
                    discovery_notes=["Homepage discovery produced detail sources for registered product type `saving`."],
                    detail_source_ids=["BMO-SAV-002"],
                ),
            ) as materialize,
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={
                    "collection_id": "collection-001",
                    "correlation_id": "corr-001",
                    "plan": prepared_plan,
                },
            ) as prepare_collection,
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row"),
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        self.assertEqual(materialize.call_args.kwargs["row"]["product_type"], "saving")
        self.assertEqual(
            materialize.call_args.kwargs["row"]["coverage_source_url"],
            "https://www.bmo.com/main/personal/bank-accounts/savings/",
        )
        prepare_collection.assert_called_once()
        self.assertEqual(
            prepare_collection.call_args.kwargs["run_id_overrides"],
            {("CA", "BMO", "saving", "en"): "run-001"},
        )
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])

    def test_run_group_reuses_preserved_active_detail_scope_when_homepage_discovery_finds_no_replacement(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-001",
            "catalog_item_id": "catalog-ca-td-savings-12345678",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "country_code": "CA",
            "product_type": "savings",
            "source_language": "en",
            "homepage_url": "https://www.td.com/ca/en/personal-banking",
            "normalized_homepage_url": "https://www.td.com/ca/en/personal-banking",
        }
        prepared_plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "triggered_by": "admin@example.com",
            "groups": [
                {
                    "run_id": "run-001",
                    "bank_code": "TD",
                    "country_code": "CA",
                    "product_type": "savings",
                    "source_language": "en",
                    "selected_source_ids": ["TD-SAV-010", "TD-SAV-011"],
                    "target_source_ids": ["TD-SAV-010"],
                    "included_source_ids": ["TD-SAV-010", "TD-SAV-011"],
                    "included_sources": [],
                }
            ],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[],
                    discovery_notes=[
                        "Existing active detail sources were preserved because homepage discovery did not produce replacement detail sources."
                    ],
                    detail_source_ids=[],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={
                    "collection_source_ids": ["TD-SAV-010", "TD-SAV-011"],
                    "target_source_ids": ["TD-SAV-010"],
                },
            ),
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={
                    "collection_id": "collection-001",
                    "correlation_id": "corr-001",
                    "plan": prepared_plan,
                },
            ) as prepare_collection,
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row") as insert_run,
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        self.assertTrue(connection.committed)
        prepare_collection.assert_called_once_with(
            connection,
            source_ids=["TD-SAV-010", "TD-SAV-011"],
            actor=plan["actor"],
            request_id="req-001",
            collection_id="collection-001",
            correlation_id="corr-001",
            run_id_overrides={
                ("CA", "TD", "savings", "en"): "run-001",
            },
        )
        self.assertEqual(insert_run.call_count, 2)
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])
        self.assertFalse(any("run_state" in params for _sql, params in connection.calls))

    def test_completed_standard_collection_reuses_active_scope_without_rediscovery(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-standard",
            "correlation_id": "corr-standard",
            "request_id": "req-standard",
            "precision_rediscovery_requested": False,
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-standard",
            "catalog_item_id": "catalog-ca-td-savings",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "country_code": "CA",
            "product_type": "savings",
            "source_language": "en",
            "homepage_url": "https://www.td.com/ca/en/personal-banking",
            "normalized_homepage_url": "https://www.td.com/ca/en/personal-banking",
            "has_completed_collection": True,
            "source_coverage_mode": "standard",
        }
        prepared_plan = {
            "triggered_by": "admin@example.com",
            "groups": [{"run_id": "run-standard"}],
        }
        active_scope = {
            "collection_source_ids": ["TD-SAV-001", "TD-SAV-RATES"],
            "target_source_ids": ["TD-SAV-001"],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch("api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item") as materialize,
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value=active_scope,
            ),
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={"plan": prepared_plan},
            ) as prepare_collection,
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row"),
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        materialize.assert_not_called()
        self.assertEqual(
            prepare_collection.call_args.kwargs["source_ids"],
            ["TD-SAV-001", "TD-SAV-RATES"],
        )
        metadata_call = next(
            params
            for sql, params in connection.calls
            if "SET run_metadata = run_metadata ||" in sql
        )
        metadata = json.loads(str(metadata_call["run_metadata"]))
        self.assertEqual(metadata["source_coverage_mode"], "standard")
        self.assertEqual(metadata["discovery_status"], "reused_existing_detail_scope")
        self.assertEqual(metadata["source_coverage_metrics"]["reused_detail_source_count"], 1)
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])

    def test_standard_collection_forces_precision_fallback_when_active_details_are_missing(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-fallback",
            "correlation_id": "corr-fallback",
            "request_id": "req-fallback",
            "precision_rediscovery_requested": False,
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-fallback",
            "catalog_item_id": "catalog-ca-atl-chequing",
            "bank_code": "ATL",
            "bank_name": "Atlas Bank",
            "country_code": "CA",
            "product_type": "chequing",
            "source_language": "en",
            "homepage_url": "https://www.atlasbank.ca/",
            "normalized_homepage_url": "https://www.atlasbank.ca/",
            "has_completed_collection": True,
            "source_coverage_mode": "standard",
        }
        prepared_plan = {
            "triggered_by": "admin@example.com",
            "groups": [{"run_id": "run-fallback"}],
        }
        refreshed_scope = {
            "collection_source_ids": ["AUTO-ATL-CHQ-NEW"],
            "target_source_ids": ["AUTO-ATL-CHQ-NEW"],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[
                        {
                            "source_id": "AUTO-ATL-CHQ-NEW",
                            "discovery_role": "detail",
                            "status": "active",
                        }
                    ],
                    discovery_notes=["Precision discovery recovered a current detail source."],
                    detail_source_ids=["AUTO-ATL-CHQ-NEW"],
                    discovery_metrics={"mode": "precision", "promoted_detail_source_count": 1},
                ),
            ) as materialize,
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                side_effect=[
                    {"collection_source_ids": [], "target_source_ids": []},
                    refreshed_scope,
                    refreshed_scope,
                ],
            ),
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={"plan": prepared_plan},
            ),
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row"),
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group"),
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        materialize.assert_called_once()
        metadata_call = next(
            params
            for sql, params in connection.calls
            if "SET run_metadata = run_metadata ||" in sql
        )
        metadata = json.loads(str(metadata_call["run_metadata"]))
        self.assertEqual(metadata["source_coverage_mode"], "precision_fallback")
        self.assertEqual(metadata["source_coverage_metrics"]["promoted_detail_source_count"], 1)
        self.assertTrue(
            any("precision source rediscovery was forced" in note for note in metadata["discovery_notes"])
        )

    def test_run_group_reuses_precreated_run_id_for_background_source_collection(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-001",
            "catalog_item_id": "catalog-ca-bmo-chequing-12345678",
            "bank_code": "BMO",
            "bank_name": "Bank of Montreal",
            "country_code": "CA",
            "product_type": "chequing",
            "source_language": "en",
            "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
            "normalized_homepage_url": "https://www.bmo.com/en-ca/main/personal",
        }
        prepared_plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "triggered_by": "admin@example.com",
            "groups": [
                {
                    "run_id": "run-001",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "source_language": "en",
                    "selected_source_ids": ["AUTO-BMO-CHQ-001"],
                    "target_source_ids": ["AUTO-BMO-CHQ-001"],
                    "included_source_ids": ["AUTO-BMO-CHQ-001", "AUTO-BMO-CHQ-002"],
                    "included_sources": [],
                }
            ],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[
                        {"source_id": "AUTO-BMO-CHQ-001", "discovery_role": "detail", "status": "active"},
                        {"source_id": "AUTO-BMO-CHQ-002", "discovery_role": "supporting_html", "status": "active"},
                    ],
                    discovery_notes=[],
                    detail_source_ids=["AUTO-BMO-CHQ-001"],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={
                    "collection_id": "collection-001",
                    "correlation_id": "corr-001",
                    "plan": prepared_plan,
                },
            ) as prepare_collection,
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row") as insert_run,
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        self.assertTrue(connection.committed)
        prepare_collection.assert_called_once()
        self.assertEqual(insert_run.call_count, 2)
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])

    def test_run_group_merges_generated_rows_with_existing_active_detail_scope(self) -> None:
        connection = _Connection()
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "actor": {"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            "groups": [],
        }
        group = {
            "run_id": "run-001",
            "catalog_item_id": "catalog-ca-cibc-gic-term-deposit",
            "bank_code": "CIBC",
            "bank_name": "CIBC",
            "country_code": "CA",
            "product_type": "gic-term-deposit",
            "source_language": "en",
            "homepage_url": "https://www.cibc.com/",
            "normalized_homepage_url": "https://www.cibc.com/",
        }
        prepared_plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "triggered_by": "admin@example.com",
            "groups": [{"run_id": "run-001"}],
        }

        with (
            patch("api_service.source_catalog_collection_runner.Settings.from_env"),
            patch("api_service.source_catalog_collection_runner.open_connection", return_value=_ConnectionContext(connection)),
            patch(
                "api_service.source_catalog_collection_runner._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[
                        {"source_id": "AUTO-CIBC-GIC-new", "discovery_role": "detail", "status": "active"},
                        {"source_id": "AUTO-CIBC-GIC-support", "discovery_role": "supporting_html", "status": "active"},
                    ],
                    discovery_notes=[],
                    detail_source_ids=["AUTO-CIBC-GIC-new"],
                ),
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={
                    "collection_source_ids": ["CIBC-GIC-002", "CIBC-GIC-003", "CIBC-GIC-004"],
                    "target_source_ids": ["CIBC-GIC-002", "CIBC-GIC-003"],
                },
            ),
            patch(
                "api_service.source_catalog_collection_runner.prepare_source_collection",
                return_value={
                    "collection_id": "collection-001",
                    "correlation_id": "corr-001",
                    "plan": prepared_plan,
                },
            ) as prepare_collection,
            patch("api_service.source_catalog_collection_runner._insert_collection_run_row"),
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        prepare_collection.assert_called_once()
        self.assertEqual(
            prepare_collection.call_args.kwargs["source_ids"],
            ["AUTO-CIBC-GIC-new", "AUTO-CIBC-GIC-support", "CIBC-GIC-002", "CIBC-GIC-003", "CIBC-GIC-004"],
        )
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])


if __name__ == "__main__":
    unittest.main()
