from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from api_service.auth import _record_login_attempt
from api_service.models import LoginRequest, SignupRequestCreateRequest
from api_service.security import hash_password, verify_password


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


class LoginTransitionRegressionTests(unittest.TestCase):
    def test_login_request_accepts_four_character_dev_password(self) -> None:
        payload = LoginRequest(login_id="test", password="test")
        self.assertEqual(payload.login_id, "test")
        self.assertEqual(payload.password, "test")

    def test_signup_request_accepts_four_character_dev_password(self) -> None:
        payload = SignupRequestCreateRequest(login_id="test", display_name="Test", password="test")
        self.assertEqual(payload.login_id, "test")
        self.assertEqual(payload.display_name, "Test")
        self.assertEqual(payload.password, "test")

    def test_login_request_accepts_five_character_dev_password(self) -> None:
        payload = LoginRequest(login_id="admin", password="admin")
        self.assertEqual(payload.login_id, "admin")
        self.assertEqual(payload.password, "admin")

    def test_login_request_still_rejects_too_short_password(self) -> None:
        with self.assertRaises(ValidationError):
            LoginRequest(login_id="admin", password="abc")

    def test_signup_request_still_rejects_too_short_password(self) -> None:
        with self.assertRaises(ValidationError):
            SignupRequestCreateRequest(login_id="test", display_name="Test", password="abc")

    def test_generated_admin_password_hash_keeps_expected_scrypt_format(self) -> None:
        encoded_hash = hash_password("admin")
        self.assertTrue(encoded_hash.startswith("scrypt$"))
        self.assertEqual(encoded_hash.count("$"), 5)
        self.assertTrue(verify_password("admin", encoded_hash))

    def test_shell_mangled_password_hash_does_not_verify(self) -> None:
        corrupted_hash = "scrypt==-4VMVwchlVa4pXTNjgqRhlQspmZADfXS3No7xkVPofInFrW0JkoYd_maumd2fG3c_tLhWWCj51Z35Q=="
        self.assertFalse(verify_password("admin", corrupted_hash))

    def test_record_login_attempt_keeps_legacy_email_column_non_null(self) -> None:
        connection = _QueuedConnection([None])

        with patch("api_service.auth.new_id", return_value="login-001"), patch(
            "api_service.auth.utc_now",
            return_value=datetime(2026, 4, 22, 20, 10, tzinfo=UTC),
        ):
            _record_login_attempt(
                connection,
                login_id="admin",
                email=None,
                user_id="user-001",
                ip_address="127.0.0.1",
                attempt_outcome="failed",
                failure_reason_code="invalid_credentials",
            )

        insert_sql, insert_params = connection.calls[0]
        self.assertIn("INSERT INTO auth_login_attempt", insert_sql)
        self.assertEqual(insert_params["login_id"], "admin")
        self.assertEqual(insert_params["email"], "admin")

    def test_record_login_attempt_prefers_real_email_when_present(self) -> None:
        connection = _QueuedConnection([None])

        with patch("api_service.auth.new_id", return_value="login-001"), patch(
            "api_service.auth.utc_now",
            return_value=datetime(2026, 4, 22, 20, 10, tzinfo=UTC),
        ):
            _record_login_attempt(
                connection,
                login_id="admin",
                email="Kylee1112@Hotmail.com",
                user_id="user-001",
                ip_address="127.0.0.1",
                attempt_outcome="failed",
                failure_reason_code="invalid_credentials",
            )

        _insert_sql, insert_params = connection.calls[0]
        self.assertEqual(insert_params["email"], "kylee1112@hotmail.com")


if __name__ == "__main__":
    unittest.main()
