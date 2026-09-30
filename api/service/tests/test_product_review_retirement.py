from __future__ import annotations

import asyncio
from dataclasses import replace
import json
import unittest
from unittest.mock import MagicMock, patch
from starlette.requests import Request
from api_service import main
from api_service.models import ReviewDecisionRequest
from api_service.review_detail import ReviewTaskError


class ProductReviewRetirementTests(unittest.TestCase):
    def setUp(self):
        self.settings = main.app.state.settings
        main.app.state.settings = replace(self.settings, csrf_enabled=True)
        self.actor = {"user_id": "test", "role": "admin"}
        self.session = {"country_code": "CA", "csrf_token": "csrf-test"}

    def tearDown(self):
        main.app.state.settings = self.settings

    def request(self, csrf="csrf-test"):
        request = Request({"type": "http", "method": "POST", "path": "/api/admin/review-tasks/legacy/approve",
            "headers": [(b"x-csrf-token", csrf.encode())], "query_string": b"", "app": main.app})
        request.state.request_id = "retirement-test"
        request.state.generated_at = "2026-09-30T00:00:00Z"
        return request

    def test_every_legacy_mutation_returns_gone_without_writes_or_model_calls(self):
        for action in ("approve", "reject", "edit_approve", "defer", "ai_verify"):
            connection = MagicMock()
            with self.subTest(action=action), patch.object(main, "_resolve_session", return_value=(self.actor, self.session)), patch.object(main, "open_connection") as opened, patch.object(main, "_require_review_task_country") as scope:
                opened.return_value.__enter__.return_value = connection
                handler = getattr(main, action + "_review_task")
                if action == "ai_verify":
                    response = handler(self.request(), "legacy")
                else:
                    response = asyncio.run(handler(self.request(), "legacy", ReviewDecisionRequest()))
                self.assertEqual(response.status_code, 410)
                self.assertEqual(json.loads(response.body)["error"]["code"], "product_review_retired")
                self.assertEqual(scope.call_args.kwargs["country_code"], "CA")
                connection.execute.assert_not_called()

    def test_csrf_and_role_are_checked_before_country_or_retirement(self):
        for role, csrf in (("admin", "wrong"), ("read_only", "csrf-test")):
            with patch.object(main, "_resolve_session", return_value=({**self.actor, "role":role}, self.session)), patch.object(main, "open_connection") as opened:
                with self.assertRaises(ReviewTaskError) as caught:
                    main.ai_verify_review_task(self.request(csrf), "legacy")
                self.assertEqual(caught.exception.status_code, 403)
                opened.assert_not_called()

    def test_cross_country_stays_hidden(self):
        with patch.object(main, "_resolve_session", return_value=(self.actor, self.session)), patch.object(main, "open_connection"), patch.object(main, "_require_review_task_country", side_effect=ReviewTaskError(status_code=404, code="review_task_not_found", message="Not found")):
            with self.assertRaises(ReviewTaskError) as caught:
                main.ai_verify_review_task(self.request(), "US-task")
            self.assertEqual(caught.exception.status_code, 404)
