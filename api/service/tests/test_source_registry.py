from __future__ import annotations

import unittest
from unittest.mock import patch

from api_service.source_registry import (
    build_source_collection_plan,
    create_source_registry_item,
    load_source_registry_list,
    normalize_source_registry_filters,
    start_source_collection,
    update_source_registry_item,
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


class SourceRegistryTests(unittest.TestCase):
    def test_filter_normalization_compacts_values(self) -> None:
        filters = normalize_source_registry_filters(
            bank_code=" td ",
            country_code=" ca ",
            product_type=" Savings ",
            status=" Active ",
            discovery_role=" Detail ",
            search=" TD  growth  ",
        )

        self.assertEqual(filters.bank_code, "TD")
        self.assertEqual(filters.country_code, "CA")
        self.assertEqual(filters.product_type, "savings")
        self.assertEqual(filters.status, "active")
        self.assertEqual(filters.discovery_role, "detail")
        self.assertEqual(filters.search, "td growth")

    def test_build_source_collection_plan_groups_targets_and_supporting_sources(self) -> None:
        selected_rows = [
            {
                "source_id": "TD-SAV-002",
                "bank_code": "TD",
                "country_code": "CA",
                "product_type": "savings",
                "source_name": "Every Day",
                "source_url": "https://www.td.com/a",
                "source_type": "html",
                "discovery_role": "detail",
                "priority": "P0",
                "source_language": "en",
                "purpose": "detail",
                "expected_fields": ["product_name"],
                "seed_source_flag": True,
            }
        ]
        included_rows = selected_rows + [
            {
                "source_id": "TD-SAV-005",
                "bank_code": "TD",
                "country_code": "CA",
                "product_type": "savings",
                "source_name": "Rates",
                "source_url": "https://www.td.com/rates",
                "source_type": "html",
                "discovery_role": "supporting_html",
                "priority": "P0",
                "source_language": "en",
                "purpose": "support",
                "expected_fields": ["standard_rate"],
                "seed_source_flag": True,
            }
        ]

        plan = build_source_collection_plan(
            selected_rows=selected_rows,
            included_rows=included_rows,
            collection_id="collection-001",
            correlation_id="corr-001",
            actor={"email": "admin@example.com"},
            request_id="req-001",
        )

        self.assertEqual(plan["selected_source_ids"], ["TD-SAV-002"])
        self.assertEqual(plan["target_source_ids"], ["TD-SAV-002"])
        self.assertEqual(plan["auto_included_source_ids"], ["TD-SAV-005"])
        self.assertEqual(len(plan["groups"]), 1)
        self.assertEqual(plan["groups"][0]["included_source_ids"], ["TD-SAV-002", "TD-SAV-005"])

    def test_load_source_registry_list_omits_null_filter_params(self) -> None:
        connection = _QueuedConnection(
            [
                [],
            ]
        )

        filters = normalize_source_registry_filters(
            bank_code=None,
            country_code=None,
            product_type=None,
            status=None,
            discovery_role=None,
            search=None,
        )

        result = load_source_registry_list(connection, filters=filters)

        self.assertEqual(result["items"], [])
        select_calls = [
            (sql, params)
            for sql, params in connection.calls
            if "FROM source_registry_item" in sql and "ORDER BY bank_code, product_type, source_id" in sql
        ]
        self.assertEqual(len(select_calls), 1)
        self.assertEqual(select_calls[0][1], {})

    def test_create_source_registry_item_inserts_row_and_audit_event(self) -> None:
        connection = _QueuedConnection(
            [
                {"item_count": 1},
                None,
                None,
                {
                    "source_id": "SRC-001",
                    "bank_code": "TD",
                    "country_code": "CA",
                    "product_type": "savings",
                    "product_key": None,
                    "source_name": "TD detail page",
                    "source_url": "https://www.td.com/detail",
                    "normalized_url": "https://www.td.com/detail",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P0",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name"],
                    "seed_source_flag": False,
                    "last_verified_at": None,
                    "last_seen_at": None,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "manual add",
                    "created_at": None,
                    "updated_at": None,
                },
                [],
            ]
        )

        result = create_source_registry_item(
            connection,
            payload={
                "source_id": "SRC-001",
                "bank_code": "td",
                "country_code": "ca",
                "product_type": "savings",
                "source_name": "TD detail page",
                "source_url": "https://www.td.com/detail",
                "source_type": "html",
                "discovery_role": "detail",
                "status": "active",
                "priority": "P0",
                "source_language": "en",
                "purpose": "detail",
                "expected_fields": ["product_name"],
                "change_reason": "manual add",
            },
            actor={"user_id": "usr-001", "role": "admin"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
        )

        self.assertEqual(result["source_id"], "SRC-001")
        self.assertTrue(any("INSERT INTO source_registry_item" in sql for sql, _ in connection.calls))
        self.assertTrue(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_update_source_registry_item_records_state_change(self) -> None:
        existing_row = {
            "source_id": "SRC-001",
            "bank_code": "TD",
            "country_code": "CA",
            "product_type": "savings",
            "product_key": None,
            "source_name": "TD detail page",
            "source_url": "https://www.td.com/detail",
            "normalized_url": "https://www.td.com/detail",
            "source_type": "html",
            "discovery_role": "detail",
            "status": "inactive",
            "priority": "P0",
            "source_language": "en",
            "purpose": "detail",
            "expected_fields": ["product_name"],
            "seed_source_flag": False,
            "last_verified_at": None,
            "last_seen_at": None,
            "redirect_target_url": None,
            "alias_urls": [],
            "change_reason": "manual add",
            "created_at": None,
            "updated_at": None,
        }
        connection = _QueuedConnection(
            [
                {"item_count": 1},
                existing_row,
                None,
                None,
                {**existing_row, "status": "active", "change_reason": "activate"},
                [],
            ]
        )

        result = update_source_registry_item(
            connection,
            source_id="SRC-001",
            payload={"status": "active", "change_reason": "activate"},
            actor={"user_id": "usr-001", "role": "admin"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
        )

        self.assertEqual(result["status"], "active")
        audit_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql]
        self.assertEqual(len(audit_calls), 1)
        self.assertEqual(audit_calls[0][1]["previous_state"], "inactive")
        self.assertEqual(audit_calls[0][1]["new_state"], "active")

    def test_start_source_collection_auto_includes_supporting_sources(self) -> None:
        detail_row = {
            "source_id": "TD-SAV-002",
            "bank_code": "TD",
            "country_code": "CA",
            "product_type": "savings",
            "product_key": None,
            "source_name": "TD detail page",
            "source_url": "https://www.td.com/detail",
            "normalized_url": "https://www.td.com/detail",
            "source_type": "html",
            "discovery_role": "detail",
            "status": "active",
            "priority": "P0",
            "source_language": "en",
            "purpose": "detail",
            "expected_fields": ["product_name"],
            "seed_source_flag": False,
            "last_verified_at": None,
            "last_seen_at": None,
            "redirect_target_url": None,
            "alias_urls": [],
            "change_reason": None,
            "created_at": None,
            "updated_at": None,
        }
        support_row = {
            **detail_row,
            "source_id": "TD-SAV-005",
            "source_name": "TD rates page",
            "source_url": "https://www.td.com/rates",
            "normalized_url": "https://www.td.com/rates",
            "discovery_role": "supporting_html",
        }
        connection = _QueuedConnection(
            [
                [detail_row],
                [support_row],
                None,
                None,
            ]
        )

        with patch("api_service.source_registry._launch_source_collection_runner") as launch_runner:
            result = start_source_collection(
                connection,
                source_ids=["TD-SAV-002"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["selected_source_ids"], ["TD-SAV-002"])
        self.assertEqual(result["auto_included_source_ids"], ["TD-SAV-005"])
        self.assertEqual(len(result["run_ids"]), 1)
        self.assertTrue(any("INSERT INTO ingestion_run" in sql for sql, _ in connection.calls))
        launch_runner.assert_called_once()


if __name__ == "__main__":
    unittest.main()
