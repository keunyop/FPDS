from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from api_service.product_types import (
    canonicalize_product_type_code,
    create_product_type_definition,
    delete_product_type_definition,
    _merge_keywords,
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


def _product_type_row(*, status: str = "active") -> dict[str, object]:
    return {
        "product_type_code": "tfsa-savings",
        "product_family": "deposit",
        "display_name": "TFSA Savings",
        "description": "Tax-free savings deposit account for retail customers.",
        "status": status,
        "managed_flag": True,
        "discovery_keywords": ["tfsa", "tax free savings", "savings"],
        "expected_fields": ["product_name", "minimum_deposit", "eligibility_text"],
        "fallback_policy": "generic_ai_review",
        "created_at": None,
        "updated_at": None,
    }


class ProductTypeRegistryTests(unittest.TestCase):
    def test_load_product_type_list_serializes_operator_managed_fields(self) -> None:
        connection = _QueuedConnection(
            [
                [_product_type_row()],
            ]
        )

        result = load_product_type_list(connection, filters=normalize_product_type_filters(search="tfsa", status="active"))

        self.assertEqual(result["summary"]["total_items"], 1)
        self.assertEqual(result["items"][0]["product_type_code"], "tfsa-savings")
        self.assertNotIn("built_in_flag", result["items"][0])
        self.assertNotIn("dynamic_onboarding_enabled", result["items"][0])
        self.assertEqual(result["applied_filters"]["search"], "tfsa")
        self.assertEqual(result["applied_filters"]["status"], "active")

    def test_create_product_type_definition_inserts_registry_and_taxonomy_entries(self) -> None:
        connection = _QueuedConnection([None, None, None, None, None])

        with (
            patch("api_service.product_types.load_product_type_definition", return_value=_product_type_row()),
            patch("api_service.product_types.new_id", return_value="audit-001"),
            patch(
                "api_service.product_types._generate_ai_discovery_keywords",
                return_value=["tfsa", "tax free savings account", "registered savings", "interest rate"],
            ),
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
        discovery_keywords = json.loads(insert_calls[0][1]["discovery_keywords"])
        self.assertEqual(discovery_keywords[:3], ["tfsa", "tax free savings account", "registered savings"])
        self.assertTrue(any("INSERT INTO taxonomy_registry" in sql for sql, _ in connection.calls))
        audit_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql]
        self.assertEqual(len(audit_calls), 1)
        self.assertNotIn("actor_display", audit_calls[0][0])
        self.assertEqual(audit_calls[0][1]["actor_role_snapshot"], "admin")

    def test_create_canonical_chequing_syncs_all_supported_subtypes(self) -> None:
        connection = _QueuedConnection([None, None, None, None, None])
        chequing_row = {
            **_product_type_row(),
            "product_type_code": "chequing",
            "display_name": "Chequing",
            "description": "Everyday transaction account.",
        }

        with (
            patch("api_service.product_types.load_product_type_definition", return_value=chequing_row),
            patch("api_service.product_types.new_id", return_value="audit-chequing"),
            patch("api_service.product_types._generate_ai_discovery_keywords", return_value=["chequing", "everyday banking"]),
        ):
            create_product_type_definition(
                connection,
                payload={
                    "product_type_code": "chequing",
                    "display_name": "Chequing",
                    "description": "A bank account designed for everyday transactions.",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        taxonomy_params = next(params for sql, params in connection.calls if "INSERT INTO taxonomy_registry" in sql)
        subtype_codes = {item["subtype_code"] for item in json.loads(str(taxonomy_params["subtype_rows"]))}
        self.assertEqual(subtype_codes, {"standard", "package", "interest_bearing", "premium", "other"})
        self.assertTrue(taxonomy_params["active_flag"])

    def test_update_product_type_definition_updates_taxonomy_and_audit(self) -> None:
        connection = _QueuedConnection([None, None, None, None])
        existing = _product_type_row(status="active")
        updated = _product_type_row(status="inactive")

        with (
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

    def test_update_product_type_status_only_preserves_keywords(self) -> None:
        connection = _QueuedConnection([None, None, None, None])
        existing = _product_type_row(status="active")
        existing["discovery_keywords"] = ["existing keyword", "tfsa"]
        updated = dict(existing)
        updated["status"] = "inactive"

        with (
            patch("api_service.product_types.load_product_type_definition", side_effect=[existing, updated]),
            patch("api_service.product_types.new_id", return_value="audit-002"),
            patch("api_service.product_types._generate_ai_discovery_keywords") as ai_generator,
        ):
            update_product_type_definition(
                connection,
                product_type_code="tfsa-savings",
                payload={"status": "inactive"},
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        update_calls = [(sql, params) for sql, params in connection.calls if "UPDATE product_type_registry" in sql]
        self.assertEqual(json.loads(update_calls[0][1]["discovery_keywords"]), ["existing keyword", "tfsa"])
        ai_generator.assert_not_called()

    def test_update_product_type_definition_can_rename_code_and_cascade_references(self) -> None:
        existing = _product_type_row()
        existing["product_type_code"] = "saving"
        existing["display_name"] = "Saving"
        updated = dict(existing)
        updated["product_type_code"] = "savings"
        updated["display_name"] = "Savings"
        connection = _QueuedConnection([existing, *([None] * 11), updated, None])

        with (
            patch("api_service.product_types.new_id", return_value="audit-rename"),
            patch("api_service.product_types._generate_ai_discovery_keywords", return_value=["savings", "interest rate"]),
        ):
            result = update_product_type_definition(
                connection,
                product_type_code="saving",
                payload={
                    "product_type_code": "savings",
                    "display_name": "Savings",
                    "description": "Savings deposit account focused on interest, rates, balances, and withdrawals.",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["product_type_code"], "savings")
        registry_update = next(params for sql, params in connection.calls if "UPDATE product_type_registry" in sql)
        self.assertEqual(registry_update["existing_product_type_code"], "saving")
        self.assertEqual(registry_update["updated_product_type_code"], "savings")
        cascade_tables = {
            sql.split("UPDATE ", 1)[1].split()[0]
            for sql, _ in connection.calls
            if "SET product_type = %(updated_product_type_code)s" in sql
        }
        self.assertTrue({"source_registry_catalog_item", "source_registry_item", "normalized_candidate", "canonical_product", "public_product_projection"}.issubset(cascade_tables))

    def test_delete_product_type_definition_removes_registry_and_taxonomy_when_unused(self) -> None:
        connection = _QueuedConnection(
            [
                {"catalog_count": 0, "source_count": 0},
                None,
                None,
                None,
            ]
        )
        existing = _product_type_row(status="inactive")

        with (
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
            patch("api_service.product_types.load_product_type_definition", return_value=_product_type_row()),
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
        with patch("api_service.product_types.load_product_type_definition", return_value=_product_type_row(status="inactive")):
            with self.assertRaises(SourceRegistryError) as captured:
                require_product_type_definition(object(), product_type_code="tfsa-savings", active_only=True)

        self.assertEqual(captured.exception.code, "product_type_inactive")

    def test_require_product_type_definition_uses_registered_code_without_aliasing(self) -> None:
        connection = _QueuedConnection([None])

        with self.assertRaises(SourceRegistryError) as captured:
            require_product_type_definition(connection, product_type_code="saving", active_only=True)

        self.assertEqual(captured.exception.code, "product_type_not_found")
        self.assertEqual(connection.calls[0][1]["product_type_code"], "saving")
        self.assertEqual(canonicalize_product_type_code("saving accounts"), "saving-accounts")

    def test_require_product_type_definition_fails_when_registered_row_is_missing(self) -> None:
        connection = _QueuedConnection([None])

        with self.assertRaises(SourceRegistryError) as captured:
            require_product_type_definition(connection, product_type_code="savings", active_only=True)

        self.assertEqual(captured.exception.code, "product_type_not_found")

    def test_merge_keywords_uses_ai_result_when_available(self) -> None:
        with patch(
            "api_service.product_types._generate_ai_discovery_keywords",
            return_value=["chequing", "everyday banking", "debit card", "bill payments", "transfers"],
        ):
            keywords = _merge_keywords(
                display_name="Chequing",
                description="A bank account designed for everyday transactions.",
                provided=[],
                regenerate=True,
            )

        self.assertEqual(keywords[:5], ["chequing", "everyday banking", "debit card", "bill payments", "transfers"])

    def test_merge_keywords_fallback_filters_description_filler_words(self) -> None:
        with patch("api_service.product_types._generate_ai_discovery_keywords", return_value=[]):
            keywords = _merge_keywords(
                display_name="Chequing",
                description=(
                    "A bank account designed for everyday transactions such as deposits, withdrawals, "
                    "debit card payments, bill payments, and transfers. It usually offers easy access "
                    "to funds but little or no interest."
                ),
                provided=[],
                regenerate=True,
            )

        self.assertIn("chequing", keywords)
        self.assertIn("everyday banking", keywords)
        self.assertIn("debit card", keywords)
        self.assertIn("bill payments", keywords)
        self.assertNotIn("designed", keywords)
        self.assertNotIn("for", keywords)
        self.assertNotIn("such", keywords)
        self.assertNotIn("and", keywords)


if __name__ == "__main__":
    unittest.main()
