from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from api_service.source_catalog import (
    AiParallelCandidateScore,
    CatalogItemMaterializationResult,
    HomepageSourceGenerationResult,
    _backfill_seeded_bank_profile_fields,
    _generate_sources_from_homepage,
    _materialize_sources_for_catalog_item,
    _launch_source_catalog_collection_runner,
    _record_catalog_audit_event,
    _score_product_link,
    _upsert_source_registry_rows,
    create_bank_profile,
    delete_bank_profile,
    create_source_catalog_item,
    load_bank_list,
    normalize_bank_filters,
    start_source_catalog_collection,
)
from api_service.errors import SourceRegistryError


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

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _QueuedCursor:
        self.calls.append((sql, params or {}))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _QueuedCursor(self._responses.pop(0))


def _product_type_definition(product_type_code: str) -> dict[str, object]:
    label = product_type_code.replace("-", " ").title()
    return {
        "product_type_code": product_type_code,
        "display_name": label,
        "description": f"{label} product type",
        "status": "active",
        "built_in_flag": product_type_code in {"chequing", "savings", "gic"},
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

    def test_create_bank_profile_auto_generates_bank_code(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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

        with patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"):
            result = load_bank_list(connection, filters=normalize_bank_filters(search=None, status=None))

        self.assertEqual(result["items"][0]["catalog_product_types"], ["gic", "savings"])
        self.assertEqual(
            [item["catalog_item_id"] for item in result["items"][0]["catalog_items"]],
            ["catalog-ca-atl-savings-1", "catalog-ca-atl-gic-1"],
        )

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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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

    def test_backfill_seeded_bank_profile_fields_updates_missing_homepage_data(self) -> None:
        connection = _QueuedConnection([None])

        with patch(
            "api_service.source_catalog.load_seed_bank_homepage_repairs",
            return_value=[
                {
                    "bank_code": "RBC",
                    "homepage_url": "https://www.rbcroyalbank.com/",
                    "normalized_homepage_url": "https://www.rbcroyalbank.com/",
                    "source_language": "en",
                    "legacy_homepage_urls": ["https://www.rbcroyalbank.com/bank-accounts/chequing-accounts/index.html"],
                }
            ],
        ):
            _backfill_seeded_bank_profile_fields(connection)

        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("UPDATE bank", sql)
        self.assertEqual(params["bank_code"], "RBC")
        self.assertIn("homepage_url", params)

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
        self.assertEqual(params["bank_code"], "BMO")
        self.assertEqual(params["product_type"], "chequing")

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
            patch("api_service.source_catalog._ensure_bank_and_catalog_seeded"),
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

    def test_launch_source_catalog_collection_runner_spawns_one_process_per_group(self) -> None:
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

        self.assertEqual(popen.call_count, 2)
        first_plan = json.loads((repo_root / "tmp" / "source-catalog-collections" / "run-001.json").read_text(encoding="utf-8"))
        second_plan = json.loads((repo_root / "tmp" / "source-catalog-collections" / "run-002.json").read_text(encoding="utf-8"))
        self.assertEqual([group["run_id"] for group in first_plan["groups"]], ["run-001"])
        self.assertEqual([group["run_id"] for group in second_plan["groups"]], ["run-002"])

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
                return_value=(
                    {
                        "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account": AiParallelCandidateScore(
                            candidate_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account",
                            predicted_role="detail",
                            relevance_score=8.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                            short_rationale="Likely official chequing detail page.",
                        )
                    },
                    ["AI parallel scorer evaluated 1 candidate link(s)."],
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


if __name__ == "__main__":
    unittest.main()
