from __future__ import annotations

import asyncio
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from starlette.requests import Request
from api_service import main
from api_service.review_detail import ReviewTaskError


class AuthRouteTests(unittest.TestCase):
    def setUp(self):
        self.settings = main.app.state.settings
        main.app.state.settings = replace(self.settings, csrf_enabled=True, env="dev")
        self.actor = {"user_id": "user-test", "role": "admin"}
        self.session = {"auth_session_id": "session-test", "csrf_token": "csrf-test", "country_code": "CA"}

    def tearDown(self):
        main.app.state.settings = self.settings

    def request(self, csrf=None, cookie=True):
        headers = []
        if cookie:
            headers.append((b"cookie", (self.settings.session_cookie_name + "=session-test").encode()))
        if csrf is not None:
            headers.append((b"x-csrf-token", csrf.encode()))
        request = Request({"type": "http", "method": "POST", "path": "/api/admin/auth/logout",
                           "headers": headers, "query_string": b"", "app": main.app})
        request.state.request_id = "request-test"
        request.state.generated_at = "2026-09-06T00:00:00Z"
        return request

    def test_logout_rejects_missing_and_wrong_csrf_without_revoking_or_clearing(self):
        for csrf in (None, "wrong"):
            with self.subTest(csrf=csrf), patch.object(main, "open_connection"), patch.object(
                main, "get_session_by_token", return_value=(self.actor, self.session)
            ), patch.object(main, "revoke_session") as revoke, patch.object(main, "_clear_auth_cookies") as clear:
                with self.assertRaises(ReviewTaskError) as caught:
                    asyncio.run(main.logout(self.request(csrf)))
                self.assertEqual(caught.exception.status_code, 403)
                revoke.assert_not_called()
                clear.assert_not_called()

    def test_logout_revokes_current_session_and_clears_both_cookies(self):
        with patch.object(main, "open_connection"), patch.object(
            main, "get_session_by_token", return_value=(self.actor, self.session)
        ), patch.object(main, "revoke_session") as revoke:
            response = asyncio.run(main.logout(self.request("csrf-test")))
        self.assertTrue(json.loads(response.body)["data"]["logged_out"])
        self.assertEqual(revoke.call_args.kwargs["auth_session_id"], "session-test")
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 2)
        self.assertTrue(all("Max-Age=0" in value for value in cookies))

    def test_logout_without_session_is_idempotent(self):
        with patch.object(main, "open_connection") as connection:
            response = asyncio.run(main.logout(self.request(cookie=False)))
        self.assertEqual(response.status_code, 200)
        connection.assert_not_called()

    def test_logout_expired_session_clears_stale_cookie(self):
        with patch.object(main, "open_connection"), patch.object(
            main, "get_session_by_token", return_value=None
        ), patch.object(main, "revoke_session") as revoke:
            response = asyncio.run(main.logout(self.request()))
        self.assertEqual(response.status_code, 200)
        revoke.assert_not_called()

    def test_session_reports_api_environment(self):
        with patch.object(main, "_resolve_session", return_value=(self.actor, self.session)):
            response = asyncio.run(main.session(self.request()))
        self.assertEqual(json.loads(response.body)["data"]["environment"], "dev")
