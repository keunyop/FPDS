from __future__ import annotations

import unittest
from unittest.mock import patch

from api_service.source_catalog import (
    CatalogItemMaterializationResult,
    HomepageSourceGenerationResult,
    _backfill_seeded_bank_profile_fields,
    _generate_sources_from_homepage,
    _materialize_sources_for_catalog_item,
    _record_catalog_audit_event,
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
            patch(
                "api_service.source_catalog._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[
                        {
                            "source_id": "AUTO-ATL-SAV-001",
                            "discovery_role": "detail",
                            "status": "active",
                        },
                        {
                            "source_id": "AUTO-ATL-SAV-002",
                            "discovery_role": "supporting_html",
                            "status": "active",
                        },
                    ],
                    discovery_notes=[],
                    detail_source_ids=["AUTO-ATL-SAV-001"],
                ),
            ) as materialize_sources,
            patch(
                "api_service.source_catalog.start_source_collection",
                return_value={
                    "collection_id": "collection-001",
                    "run_ids": ["run-001"],
                    "selected_source_ids": ["AUTO-ATL-SAV-001"],
                    "target_source_ids": ["AUTO-ATL-SAV-001"],
                    "auto_included_source_ids": [],
                    "groups": [],
                },
            ) as launch_collection,
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-atl-savings-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["catalog_item_ids"], ["catalog-ca-atl-savings-12345678"])
        self.assertEqual(result["materialized_items"][0]["generated_source_ids"], ["AUTO-ATL-SAV-001", "AUTO-ATL-SAV-002"])
        self.assertEqual(result["materialized_items"][0]["collection_source_ids"], ["AUTO-ATL-SAV-001", "AUTO-ATL-SAV-002"])
        self.assertEqual(result["materialized_items"][0]["discovery_status"], "detail_sources_ready")
        materialize_sources.assert_called_once()
        launch_collection.assert_called_once_with(
            connection,
            source_ids=["AUTO-ATL-SAV-001", "AUTO-ATL-SAV-002"],
            actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
        )

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

    def test_start_source_catalog_collection_returns_no_detail_result_without_launching_collection(self) -> None:
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
            patch(
                "api_service.source_catalog._materialize_sources_for_catalog_item",
                return_value=CatalogItemMaterializationResult(
                    generated_rows=[],
                    discovery_notes=["Homepage discovery completed but no candidate-producing detail sources were identified."],
                    detail_source_ids=[],
                ),
            ),
            patch("api_service.source_catalog.start_source_collection") as launch_collection,
            patch("api_service.source_catalog.new_id", side_effect=["collection-001", "corr-001"]),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-bmo-chequing-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["run_ids"], [])
        self.assertEqual(result["selected_source_ids"], [])
        self.assertEqual(result["materialized_items"][0]["discovery_status"], "no_detail_sources_discovered")
        self.assertEqual(
            result["materialized_items"][0]["discovery_notes"],
            ["Homepage discovery completed but no candidate-producing detail sources were identified."],
        )
        launch_collection.assert_not_called()

    def test_generate_sources_from_homepage_can_use_ai_to_resolve_detail_rows(self) -> None:
        ai_detail_row = {
            "source_id": "BMO-CHQ-002",
            "bank_code": "BMO",
            "country_code": "CA",
            "product_type": "chequing",
            "product_key": "BMO:chequing",
            "source_name": "BMO Performance Chequing Account",
            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account/",
            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account",
            "source_type": "html",
            "discovery_role": "detail",
            "status": "active",
            "priority": "P1",
            "source_language": "en",
            "purpose": "AI-resolved chequing detail source from homepage context",
            "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
            "seed_source_flag": False,
            "redirect_target_url": None,
            "alias_urls": [],
            "change_reason": "generated_from_bank_homepage",
        }

        with (
            patch("api_service.source_catalog.fetch_text", side_effect=TimeoutError("timed out")),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch(
                "api_service.source_catalog._load_seed_detail_hints",
                return_value=[
                    {
                        "source_id": "BMO-CHQ-002",
                        "source_name": "BMO Performance Chequing Account",
                        "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account/",
                        "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account",
                        "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                        "purpose": "detail",
                        "priority": "P1",
                    }
                ],
            ),
            patch(
                "api_service.source_catalog._resolve_detail_rows_with_ai",
                return_value=([ai_detail_row], ["AI-assisted homepage discovery resolved 1 detail source(s)."]),
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

        self.assertEqual([item["source_id"] for item in result.rows], ["BMO-CHQ-002"])
        self.assertEqual(result.detail_source_ids, ["BMO-CHQ-002"])
        self.assertIn("AI-assisted homepage discovery resolved 1 detail source(s).", result.discovery_notes)

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
