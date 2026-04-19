from __future__ import annotations

import unittest
from unittest.mock import patch

from api_service.product_types import (
    create_product_type_definition,
    delete_product_type_definition,
    load_product_type_list,
    normalize_product_type_filters,
    require_product_type_definition,
    update_product_type_definition,
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


def _dynamic_product_row(*, status: str = "active") -> dict[str, object]:
    return {
        "product_type_code": "tfsa-savings",
        "product_family": "deposit",
        "display_name": "TFSA Savings",
        "description": "Tax-free savings deposit account for retail customers.",
        "status": status,
        "built_in_flag": False,
        "managed_flag": True,
        "discovery_keywords": ["tfsa", "tax free savings", "savings"],
        "expected_fields": ["product_name", "minimum_deposit", "eligibility_text"],
        "fallback_policy": "generic_ai_review",
        "created_at": None,
        "updated_at": None,
    }


class ProductTypeRegistryTests(unittest.TestCase):
    def test_load_product_type_list_serializes_dynamic_flag(self) -> None:
        connection = _QueuedConnection(
            [
                {"item_count": 1},
                [_dynamic_product_row()],
            ]
        )

        result = load_product_type_list(connection, filters=normalize_product_type_filters(search="tfsa", status="active"))

        self.assertEqual(result["summary"]["total_items"], 1)
        self.assertEqual(result["items"][0]["product_type_code"], "tfsa-savings")
        self.assertTrue(result["items"][0]["dynamic_onboarding_enabled"])
        self.assertEqual(result["applied_filters"]["search"], "tfsa")
        self.assertEqual(result["applied_filters"]["status"], "active")

    def test_create_product_type_definition_inserts_registry_and_taxonomy_entries(self) -> None:
        connection = _QueuedConnection([None, None, None, None])

        with (
            patch("api_service.product_types.ensure_product_type_registry_seeded"),
            patch("api_service.product_types.load_product_type_definition", return_value=_dynamic_product_row()),
            patch("api_service.product_types.new_id", return_value="audit-001"),
        ):
            result = create_product_type_definition(
                connection,
                payload={
                    "display_name": "TFSA Savings",
                    "description": "Tax-free savings deposit account for retail customers.",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["product_type_code"], "tfsa-savings")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO product_type_registry" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["fallback_policy"], "generic_ai_review")
        self.assertIn("tfsa", insert_calls[0][1]["discovery_keywords"])
        self.assertTrue(any("INSERT INTO taxonomy_registry" in sql for sql, _ in connection.calls))
        audit_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql]
        self.assertEqual(len(audit_calls), 1)
        self.assertNotIn("actor_display", audit_calls[0][0])
        self.assertEqual(audit_calls[0][1]["actor_role_snapshot"], "admin")

    def test_update_product_type_definition_updates_taxonomy_and_audit(self) -> None:
        connection = _QueuedConnection([None, None, None])
        existing = _dynamic_product_row(status="active")
        updated = _dynamic_product_row(status="inactive")

        with (
            patch("api_service.product_types.ensure_product_type_registry_seeded"),
            patch("api_service.product_types.load_product_type_definition", side_effect=[existing, updated]),
            patch("api_service.product_types.new_id", return_value="audit-002"),
        ):
            result = update_product_type_definition(
                connection,
                product_type_code="tfsa-savings",
                payload={
                    "display_name": "TFSA Savings",
                    "description": "Tax-free savings deposit account for retail customers.",
                    "status": "inactive",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["status"], "inactive")
        update_calls = [(sql, params) for sql, params in connection.calls if "UPDATE product_type_registry" in sql]
        self.assertEqual(len(update_calls), 1)
        self.assertEqual(update_calls[0][1]["status"], "inactive")
        self.assertTrue(any("INSERT INTO taxonomy_registry" in sql for sql, _ in connection.calls))
        self.assertTrue(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_delete_product_type_definition_removes_registry_and_taxonomy_when_unused(self) -> None:
        connection = _QueuedConnection(
            [
                {"catalog_count": 0, "source_count": 0},
                None,
                None,
                None,
            ]
        )
        existing = _dynamic_product_row(status="inactive")

        with (
            patch("api_service.product_types.ensure_product_type_registry_seeded"),
            patch("api_service.product_types.load_product_type_definition", return_value=existing),
            patch("api_service.product_types.new_id", return_value="audit-003"),
        ):
            result = delete_product_type_definition(
                connection,
                product_type_code="tfsa-savings",
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["product_type_code"], "tfsa-savings")
        self.assertTrue(any("DELETE FROM taxonomy_registry" in sql for sql, _ in connection.calls))
        self.assertTrue(any("DELETE FROM product_type_registry" in sql for sql, _ in connection.calls))
        self.assertTrue(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_delete_product_type_definition_rejects_in_use_product_type(self) -> None:
        connection = _QueuedConnection(
            [
                {"catalog_count": 1, "source_count": 0},
            ]
        )
        with (
            patch("api_service.product_types.ensure_product_type_registry_seeded"),
            patch("api_service.product_types.load_product_type_definition", return_value=_dynamic_product_row()),
        ):
            with self.assertRaises(SourceRegistryError) as captured:
                delete_product_type_definition(
                    connection,
                    product_type_code="tfsa-savings",
                    actor={"user_id": "usr-001", "role": "admin"},
                    request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
                )

        self.assertEqual(captured.exception.code, "product_type_in_use")

    def test_require_product_type_definition_rejects_inactive_product_type(self) -> None:
        with patch("api_service.product_types.load_product_type_definition", return_value=_dynamic_product_row(status="inactive")):
            with self.assertRaises(SourceRegistryError) as captured:
                require_product_type_definition(object(), product_type_code="tfsa-savings", active_only=True)

        self.assertEqual(captured.exception.code, "product_type_inactive")


if __name__ == "__main__":
    unittest.main()
