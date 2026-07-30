from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch

from api_service.countries import (
    activate_country,
    deactivate_country,
    load_country_registry,
    normalize_country_code,
)
from api_service.country_catalog import COUNTRY_BY_CODE, COUNTRY_CATALOG
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


def _country_row(code: str, name: str, *, status: str = "active") -> dict[str, object]:
    now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
    return {
        "country_code": code,
        "country_name": name,
        "status": status,
        "display_order": 10,
        "created_at": now,
        "updated_at": now,
    }


class CountryRegistryTests(unittest.TestCase):
    def test_catalog_contains_unique_iso_alpha_two_countries(self) -> None:
        self.assertEqual(len(COUNTRY_CATALOG), 249)
        self.assertEqual(len(COUNTRY_BY_CODE), 249)
        self.assertEqual(COUNTRY_BY_CODE["CA"], "Canada")
        self.assertEqual(COUNTRY_BY_CODE["US"], "United States")
        self.assertTrue(all(len(code) == 2 and code.isupper() for code in COUNTRY_BY_CODE))

    def test_normalize_country_code_rejects_free_form_values(self) -> None:
        with self.assertRaises(SourceRegistryError) as captured:
            normalize_country_code("Canada")

        self.assertEqual(captured.exception.code, "unsupported_country_code")

    def test_load_country_registry_merges_active_rows_into_prepared_catalog(self) -> None:
        connection = _QueuedConnection(
            [[
                _country_row("CA", "Canada"),
                _country_row("US", "United States", status="inactive"),
            ]]
        )

        result = load_country_registry(connection)

        canada = next(item for item in result["items"] if item["country_code"] == "CA")
        united_states = next(item for item in result["items"] if item["country_code"] == "US")
        self.assertEqual(result["summary"], {"total_items": 249, "active_items": 1, "available_items": 248})
        self.assertEqual(canada["status"], "active")
        self.assertEqual(united_states["status"], "inactive")

    def test_activate_country_upserts_and_records_audit_event(self) -> None:
        now = datetime(2026, 7, 29, 12, 30, tzinfo=UTC)
        activated = _country_row("US", "United States")
        connection = _QueuedConnection([None, activated, None])

        with patch("api_service.countries.utc_now", return_value=now), patch(
            "api_service.countries.new_id",
            return_value="audit-001",
        ):
            result = activate_country(
                connection,
                country_code="us",
                actor={"user_id": "admin-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["country_code"], "US")
        self.assertEqual(result["status"], "active")
        upsert = next((sql, params) for sql, params in connection.calls if "INSERT INTO country_registry" in sql)
        self.assertEqual(upsert[1]["country_name"], "United States")
        audit = next((sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit[1]["event_type"], "country_activated")
        self.assertEqual(audit[1]["country_code"], "US")

    def test_deactivate_country_rejects_current_session_country(self) -> None:
        connection = _QueuedConnection([])

        with self.assertRaises(SourceRegistryError) as captured:
            deactivate_country(
                connection,
                country_code="CA",
                current_country_code="ca",
                actor={"user_id": "admin-001", "role": "admin"},
                request_context={},
            )

        self.assertEqual(captured.exception.code, "current_country_cannot_be_deactivated")
        self.assertEqual(connection.calls, [])

    def test_deactivate_country_preserves_last_active_country(self) -> None:
        connection = _QueuedConnection([_country_row("CA", "Canada"), [{"country_code": "CA"}]])

        with self.assertRaises(SourceRegistryError) as captured:
            deactivate_country(
                connection,
                country_code="CA",
                current_country_code="US",
                actor={"user_id": "admin-001", "role": "admin"},
                request_context={},
            )

        self.assertEqual(captured.exception.code, "last_active_country")

    def test_deactivate_country_revokes_sessions_and_records_audit(self) -> None:
        inactive = _country_row("US", "United States", status="inactive")
        connection = _QueuedConnection(
            [
                _country_row("US", "United States"),
                [{"country_code": "CA"}, {"country_code": "US"}],
                inactive,
                None,
                None,
            ]
        )

        result = deactivate_country(
            connection,
            country_code="US",
            current_country_code="CA",
            actor={"user_id": "admin-001", "role": "admin"},
            request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
        )

        self.assertEqual(result["status"], "inactive")
        revoke = next((sql, params) for sql, params in connection.calls if "UPDATE admin_auth_session" in sql)
        self.assertEqual(revoke[1]["country_code"], "US")
        audit = next((sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit[1]["event_type"], "country_deactivated")


if __name__ == "__main__":
    unittest.main()
