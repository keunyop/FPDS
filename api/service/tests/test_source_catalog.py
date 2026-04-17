from __future__ import annotations

import unittest
from unittest.mock import patch

from api_service.source_catalog import (
    _backfill_seeded_bank_profile_fields,
    _materialize_sources_for_catalog_item,
    _record_catalog_audit_event,
    create_bank_profile,
    create_source_catalog_item,
    start_source_catalog_collection,
)


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
                return_value=[
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
                "api_service.source_catalog._generate_sources_from_homepage",
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
            ) as generate_sources,
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

        self.assertEqual([item["source_id"] for item in result], ["AUTO-BMO-CHQ-001"])
        generate_sources.assert_called_once()
        upsert_rows.assert_called_once()
        self.assertEqual(upsert_rows.call_args.args[1][0]["source_id"], "AUTO-BMO-CHQ-001")
        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("UPDATE source_registry_item", sql)
        self.assertEqual(params["bank_code"], "BMO")
        self.assertEqual(params["product_type"], "chequing")


if __name__ == "__main__":
    unittest.main()
