from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from api_service import source_catalog_collection_runner
from api_service.source_catalog import CatalogItemMaterializationResult


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
    def test_refresh_active_seed_scope_rows_rewrites_seeded_url_from_current_baseline(self) -> None:
        connection = _Connection([{"source_id": "SCOTIA-SAV-005"}])

        with patch(
            "api_service.source_catalog_collection_runner.load_seed_source_registry_rows",
            return_value=[
                {
                    "source_id": "SCOTIA-SAV-005",
                    "bank_code": "SCOTIA",
                    "country_code": "CA",
                    "product_type": "savings",
                    "product_key": None,
                    "source_name": "Scotiabank U.S. Dollar Interest Account detail source",
                    "source_url": "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html",
                    "normalized_url": "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "Scotiabank U.S. Dollar Interest Account detail source",
                    "expected_fields": ["product_name", "currency", "monthly_fee", "interest_rate_summary"],
                    "seed_source_flag": True,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "seeded_from_json_catalog",
                }
            ],
        ):
            refreshed_source_ids = source_catalog_collection_runner._refresh_active_seed_scope_rows(
                connection,
                bank_code="SCOTIA",
                product_type="savings",
            )

        self.assertEqual(refreshed_source_ids, ["SCOTIA-SAV-005"])
        sql, params = connection.calls[0]
        self.assertIn("UPDATE source_registry_item", sql)
        self.assertIn("status = 'active'", sql)
        self.assertEqual(
            params["source_url"],
            "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html",
        )
        self.assertEqual(
            params["normalized_url"],
            "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html",
        )
        self.assertEqual(
            json.loads(str(params["expected_fields"])),
            ["product_name", "currency", "monthly_fee", "interest_rate_summary"],
        )

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
            patch("api_service.source_catalog_collection_runner._refresh_active_seed_scope_rows") as refresh_scope,
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                return_value={"collection_source_ids": [], "target_source_ids": []},
            ),
            patch("api_service.source_catalog_collection_runner.prepare_source_collection") as prepare_collection,
            patch("api_service.source_catalog_collection_runner.source_collection_runner._run_group") as run_group,
        ):
            source_catalog_collection_runner._run_group(plan=plan, group=group)

        prepare_collection.assert_not_called()
        run_group.assert_not_called()
        refresh_scope.assert_called_once_with(connection, bank_code="BMO", product_type="chequing")
        self.assertFalse(connection.committed)
        update_call = next(params for sql, params in connection.calls if "UPDATE ingestion_run" in sql)
        self.assertEqual(update_call["run_id"], "run-001")
        self.assertEqual(update_call["run_state"], "completed")
        self.assertTrue(update_call["partial_completion_flag"])
        self.assertEqual(update_call["error_summary"], "Homepage discovery produced no detail sources eligible for collection.")

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
        refresh_scope_called = {"value": False}

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
                "api_service.source_catalog_collection_runner._refresh_active_seed_scope_rows",
                side_effect=lambda *_args, **_kwargs: refresh_scope_called.__setitem__("value", True) or ["TD-SAV-010"],
            ),
            patch(
                "api_service.source_catalog_collection_runner._load_active_collection_scope",
                side_effect=lambda *_args, **_kwargs: (
                    self.assertTrue(refresh_scope_called["value"]),
                    {
                        "collection_source_ids": ["TD-SAV-010", "TD-SAV-011"],
                        "target_source_ids": ["TD-SAV-010"],
                    },
                )[1],
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
        insert_run.assert_called_once()
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])
        self.assertFalse(any("run_state" in params for _sql, params in connection.calls))

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
        insert_run.assert_called_once()
        run_group.assert_called_once_with(plan=prepared_plan, group=prepared_plan["groups"][0])


if __name__ == "__main__":
    unittest.main()
