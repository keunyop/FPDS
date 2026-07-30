from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch

from api_service.auth import (
    LoginError,
    create_signup_request,
    load_admin_login_countries,
    review_signup_request,
    switch_session_country,
    validate_admin_country,
    validate_login_id,
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


class AuthTests(unittest.TestCase):
    def test_validate_login_id_normalizes_case(self) -> None:
        self.assertEqual(validate_login_id(" Admin.User "), "admin.user")

    def test_load_admin_login_countries_returns_active_registry_order(self) -> None:
        connection = _QueuedConnection(
            [[
                {"country_code": "CA", "country_name": "Canada"},
                {"country_code": "US", "country_name": "United States"},
            ]]
        )

        result = load_admin_login_countries(connection)

        self.assertEqual(
            result,
            [
                {"country_code": "CA", "country_name": "Canada"},
                {"country_code": "US", "country_name": "United States"},
            ],
        )
        self.assertIn("WHERE status = 'active'", connection.calls[0][0])

    def test_validate_admin_country_normalizes_supported_code(self) -> None:
        connection = _QueuedConnection([{"country_code": "CA"}])

        self.assertEqual(validate_admin_country(connection, " ca "), "CA")
        self.assertEqual(connection.calls[0][1]["country_code"], "CA")

    def test_validate_admin_country_rejects_disabled_or_unknown_code(self) -> None:
        connection = _QueuedConnection([None])

        with self.assertRaises(LoginError) as captured:
            validate_admin_country(connection, "US")

        self.assertEqual(captured.exception.code, "unsupported_country")

    def test_switch_session_country_updates_only_current_session_and_audits(self) -> None:
        connection = _QueuedConnection(
            [
                {"country_code": "US"},
                {
                    "auth_session_id": "sess-001",
                    "user_id": "admin-001",
                    "country_code": "CA",
                    "session_status": "active",
                },
                None,
                None,
            ]
        )

        result = switch_session_country(
            connection,
            auth_session_id="sess-001",
            country_code="us",
            actor={"user_id": "admin-001", "login_id": "admin", "role": "admin"},
            request_id="req-001",
            ip_address="127.0.0.1",
            user_agent="test",
        )

        self.assertEqual(result, "US")
        update = next((sql, params) for sql, params in connection.calls if "UPDATE admin_auth_session" in sql)
        self.assertEqual(update[1]["auth_session_id"], "sess-001")
        self.assertEqual(update[1]["country_code"], "US")
        audit = next((sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql)
        self.assertEqual(audit[1]["event_type"], "auth_country_switched")
        self.assertEqual(audit[1]["target_id"], "sess-001")

    def test_switch_session_country_same_country_is_noop(self) -> None:
        connection = _QueuedConnection(
            [
                {"country_code": "CA"},
                {
                    "auth_session_id": "sess-001",
                    "user_id": "admin-001",
                    "country_code": "CA",
                    "session_status": "active",
                },
            ]
        )

        result = switch_session_country(
            connection,
            auth_session_id="sess-001",
            country_code="CA",
            actor={"user_id": "admin-001", "login_id": "admin", "role": "admin"},
            request_id="req-001",
            ip_address=None,
            user_agent=None,
        )

        self.assertEqual(result, "CA")
        self.assertFalse(any("UPDATE admin_auth_session" in sql for sql, _ in connection.calls))
        self.assertFalse(any("INSERT INTO audit_event" in sql for sql, _ in connection.calls))

    def test_create_signup_request_inserts_pending_request(self) -> None:
        now = datetime(2026, 4, 22, 9, 0, tzinfo=UTC)
        connection = _QueuedConnection([None, None, None, None])

        with patch("api_service.auth.utc_now", return_value=now), patch(
            "api_service.auth.new_id",
            side_effect=["signup-001", "audit-001"],
        ):
            result = create_signup_request(
                connection,
                login_id="New.Operator",
                display_name="New Operator",
                password="correct horse battery staple",
                request_id="req-001",
                ip_address="127.0.0.1",
                user_agent="test",
            )

        self.assertEqual(result["signup_request_id"], "signup-001")
        self.assertEqual(result["login_id"], "new.operator")
        self.assertEqual(result["request_status"], "pending")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO user_signup_request" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["login_id"], "new.operator")
        self.assertEqual(insert_calls[0][1]["display_name"], "New Operator")
        self.assertNotEqual(insert_calls[0][1]["password_hash"], "correct horse battery staple")
        audit_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO audit_event" in sql]
        self.assertEqual(len(audit_calls), 1)
        self.assertEqual(audit_calls[0][1]["target_id"], "signup-001")

    def test_review_signup_request_approve_creates_user_account(self) -> None:
        now = datetime(2026, 4, 22, 9, 30, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "signup_request_id": "signup-001",
                    "login_id": "new.operator",
                    "display_name": "New Operator",
                    "password_hash": "hashed-password",
                    "password_algorithm": "scrypt",
                    "request_status": "pending",
                    "requested_at": now,
                    "reviewed_at": None,
                    "reviewed_role": None,
                    "review_reason": None,
                    "reviewed_by_user_id": None,
                    "approved_user_id": None,
                },
                None,
                None,
                None,
                None,
            ]
        )

        with patch("api_service.auth.utc_now", return_value=now), patch(
            "api_service.auth.new_id",
            side_effect=["user-001", "audit-001"],
        ):
            result = review_signup_request(
                connection,
                signup_request_id="signup-001",
                action="approve",
                actor={"user_id": "admin-001", "role": "admin"},
                role="reviewer",
                reason_text="Approved for review work.",
                request_id="req-001",
                ip_address="127.0.0.1",
                user_agent="test",
            )

        self.assertEqual(result["request_status"], "approved")
        self.assertEqual(result["reviewed_role"], "reviewer")
        self.assertEqual(result["approved_user_id"], "user-001")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO user_account" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["login_id"], "new.operator")
        self.assertEqual(insert_calls[0][1]["display_name"], "New Operator")
        self.assertEqual(insert_calls[0][1]["role"], "reviewer")

    def test_review_signup_request_requires_valid_role_on_approve(self) -> None:
        now = datetime(2026, 4, 22, 9, 30, tzinfo=UTC)
        connection = _QueuedConnection(
            [
                {
                    "signup_request_id": "signup-001",
                    "login_id": "new.operator",
                    "display_name": "New Operator",
                    "password_hash": "hashed-password",
                    "password_algorithm": "scrypt",
                    "request_status": "pending",
                    "requested_at": now,
                    "reviewed_at": None,
                    "reviewed_role": None,
                    "review_reason": None,
                    "reviewed_by_user_id": None,
                    "approved_user_id": None,
                }
            ]
        )

        with self.assertRaises(LoginError) as captured:
            review_signup_request(
                connection,
                signup_request_id="signup-001",
                action="approve",
                actor={"user_id": "admin-001", "role": "admin"},
                role="operator",
                reason_text=None,
                request_id="req-001",
                ip_address="127.0.0.1",
                user_agent="test",
            )

        self.assertEqual(captured.exception.code, "invalid_role")


if __name__ == "__main__":
    unittest.main()
