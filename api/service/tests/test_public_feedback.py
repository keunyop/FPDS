from __future__ import annotations

import asyncio
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from starlette.requests import Request

from api_service import main
from api_service.models import PublicFeedbackRequest
from api_service.public_feedback import (
    PublicFeedbackRateLimiter,
    create_public_feedback_submission,
    load_public_feedback_submissions,
    normalize_public_feedback_filters,
)


class _Result:
    def __init__(self, *, one=None, many=None) -> None:
        self._one = one
        self._many = many or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._many


class _Connection:
    def __init__(self, results: list[_Result]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> _Result:
        self.calls.append((sql, params))
        return self.results.pop(0)


def _request(*, method: str = "POST", secret: str | None = None) -> Request:
    headers = []
    if secret is not None:
        headers.append((b"x-fpds-public-app-secret", secret.encode("utf-8")))
    request = Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/public/feedback",
            "headers": headers,
            "query_string": b"",
            "app": main.app,
        }
    )
    request.state.request_id = "req-public-feedback"
    request.state.generated_at = "2026-08-31T00:00:00+00:00"
    return request


class PublicFeedbackServiceTests(unittest.TestCase):
    def test_product_error_uses_latest_active_projection_context(self) -> None:
        submitted_at = datetime(2026, 8, 31, 12, tzinfo=UTC)
        connection = _Connection(
            [
                _Result(
                    one={
                        "submission_id": "feedback-1",
                        "submitted_at": submitted_at,
                        "country_code": "CA",
                        "submission_type": "product_error",
                        "category": "incorrect_rate_or_fee",
                        "details": "Rate looks stale.",
                        "locale": "en",
                        "snapshot_id": "snapshot-1",
                        "product_id": "prod-1",
                        "bank_code": "BANK",
                        "bank_name": "Example Bank",
                        "product_name": "Everyday Savings",
                        "product_type": "savings",
                    }
                )
            ]
        )

        submission = create_public_feedback_submission(
            connection,
            country_code=" ca ",
            submission_type="product_error",
            category="incorrect_rate_or_fee",
            details="  Rate looks stale.  ",
            locale="en",
            product_id="prod-1",
        )

        self.assertEqual(submission["product"]["product_name"], "Everyday Savings")
        self.assertEqual(submission["snapshot_id"], "snapshot-1")
        sql, params = connection.calls[0]
        self.assertIn("projection.status = 'active'", sql)
        self.assertIn("refresh_status = 'completed'", sql)
        self.assertEqual(params["country_code"], "CA")
        self.assertEqual(params["details"], "Rate looks stale.")

    def test_site_feedback_requires_active_country_and_no_product(self) -> None:
        connection = _Connection(
            [
                _Result(
                    one={
                        "submission_id": "feedback-2",
                        "submitted_at": datetime(2026, 8, 31, tzinfo=UTC),
                        "country_code": "US",
                        "submission_type": "site_feedback",
                        "category": "feature_suggestion",
                        "details": None,
                        "locale": "ja",
                    }
                )
            ]
        )

        submission = create_public_feedback_submission(
            connection,
            country_code="US",
            submission_type="site_feedback",
            category="feature_suggestion",
            details=" ",
            locale="ja",
            product_id=None,
        )

        self.assertIsNone(submission["product"])
        self.assertIn("country_registry.status = 'active'", connection.calls[0][0])
        self.assertIsNone(connection.calls[0][1]["details"])

    def test_incompatible_category_is_rejected_without_query(self) -> None:
        connection = _Connection([])
        submission = create_public_feedback_submission(
            connection,
            country_code="CA",
            submission_type="site_feedback",
            category="incorrect_rate_or_fee",
            details=None,
            locale="en",
            product_id=None,
        )
        self.assertIsNone(submission)
        self.assertEqual(connection.calls, [])

    def test_public_admin_list_is_country_scoped_and_paginated(self) -> None:
        connection = _Connection(
            [
                _Result(one={"total_items": 51, "product_error_items": 40, "site_feedback_items": 11}),
                _Result(
                    many=[
                        {
                            "submission_id": "feedback-3",
                            "submitted_at": datetime(2026, 8, 31, tzinfo=UTC),
                            "country_code": "CA",
                            "submission_type": "site_feedback",
                            "category": "usability_issue",
                            "details": "Hard to scan on mobile.",
                            "locale": "ko",
                        }
                    ]
                ),
            ]
        )
        filters = normalize_public_feedback_filters(
            country_code="ca",
            submission_type="site_feedback",
            category=None,
            search="mobile",
            page=2,
            page_size=50,
        )

        payload = load_public_feedback_submissions(connection, filters=filters)

        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["total_pages"], 2)
        self.assertFalse(payload["has_next_page"])
        self.assertEqual(payload["applied_filters"]["country_code"], "CA")
        for sql, params in connection.calls:
            self.assertIn("%(country_code)s::text IS NULL OR country_code = %(country_code)s", sql)
            self.assertEqual(params["country_code"], "CA")
            self.assertEqual(params["search_pattern"], "%mobile%")

    def test_public_admin_list_can_span_all_countries(self) -> None:
        connection = _Connection(
            [
                _Result(one={"total_items": 2, "product_error_items": 1, "site_feedback_items": 1}),
                _Result(many=[]),
            ]
        )
        filters = normalize_public_feedback_filters(
            country_code=None,
            submission_type=None,
            category=None,
            search=None,
            page=1,
            page_size=50,
        )

        payload = load_public_feedback_submissions(connection, filters=filters)

        self.assertEqual(payload["total_items"], 2)
        self.assertIsNone(payload["applied_filters"]["country_code"])
        for sql, params in connection.calls:
            self.assertIn("%(country_code)s::text IS NULL OR country_code = %(country_code)s", sql)
            self.assertIsNone(params["country_code"])

    def test_rate_limiter_and_migration_are_bounded_without_identity(self) -> None:
        limiter = PublicFeedbackRateLimiter(limit=1, window_seconds=60)
        self.assertTrue(limiter.allow())
        self.assertFalse(limiter.allow())
        migration = (
            Path(__file__).resolve().parents[3]
            / "db"
            / "migrations"
            / "0046_public_feedback_submission.sql"
        ).read_text(encoding="utf-8")
        self.assertIn("interval '400 days'", migration)
        self.assertNotIn("ip_address", migration)
        self.assertNotIn("email", migration)
        self.assertNotIn("user_agent", migration)


class PublicFeedbackRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_settings = main.app.state.settings
        self.original_limiter = main.app.state.public_feedback_rate_limiter
        main.app.state.public_feedback_rate_limiter = PublicFeedbackRateLimiter()

    def tearDown(self) -> None:
        main.app.state.settings = self.original_settings
        main.app.state.public_feedback_rate_limiter = self.original_limiter

    def test_missing_public_app_secret_fails_closed(self) -> None:
        main.app.state.settings = replace(self.original_settings, public_app_api_secret=None)
        response = asyncio.run(
            main.public_feedback(
                _request(),
                PublicFeedbackRequest(
                    country_code="CA",
                    submission_type="site_feedback",
                    category="other",
                ),
            )
        )
        self.assertEqual(response.status_code, 503)

    def test_incompatible_category_does_not_open_database(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        with patch.object(main, "open_connection") as mocked_open:
            response = asyncio.run(
                main.public_feedback(
                    _request(secret="public-app-secret"),
                    PublicFeedbackRequest(
                        country_code="CA",
                        submission_type="site_feedback",
                        category="incorrect_rate_or_fee",
                    ),
                )
            )
        self.assertEqual(response.status_code, 400)
        mocked_open.assert_not_called()

    def test_valid_product_error_returns_created_submission(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        submission = {
            "submission_id": "feedback-4",
            "submitted_at": "2026-08-31T00:00:00+00:00",
            "country_code": "CA",
            "submission_type": "product_error",
            "category": "missing_information",
            "details": None,
            "locale": "en",
            "snapshot_id": "snapshot-1",
            "product": {"product_id": "prod-1"},
        }
        with (
            patch.object(main, "open_connection") as mocked_open,
            patch.object(
                main,
                "create_public_feedback_submission",
                return_value=submission,
            ) as mocked_create,
        ):
            mocked_open.return_value.__enter__.return_value = object()
            response = asyncio.run(
                main.public_feedback(
                    _request(secret="public-app-secret"),
                    PublicFeedbackRequest(
                        country_code="CA",
                        submission_type="product_error",
                        category="missing_information",
                        product_id="prod-1",
                    ),
                )
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.body)["data"]["submission"]["submission_id"], "feedback-4")
        mocked_create.assert_called_once()

    def test_public_admin_list_requires_public_app_credential(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        with patch.object(main, "open_connection") as mocked_open:
            response = asyncio.run(
                main.public_admin_feedback(
                    _request(method="GET"),
                    country_code=None,
                    submission_type=None,
                    category=None,
                    q=None,
                    page=1,
                    page_size=50,
                )
            )

        self.assertEqual(response.status_code, 401)
        mocked_open.assert_not_called()

    def test_public_admin_list_uses_optional_country_scope(self) -> None:
        payload = {
            "items": [],
            "summary": {"total_items": 0, "product_error_items": 0, "site_feedback_items": 0},
            "applied_filters": {"submission_type": None, "category": None, "search": None},
            "page": 1,
            "page_size": 50,
            "total_items": 0,
            "total_pages": 1,
            "has_next_page": False,
        }

        @contextmanager
        def fake_open_connection(_settings):
            yield object()

        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        with (
            patch.object(main, "open_connection", fake_open_connection),
            patch.object(
                main,
                "load_public_feedback_submissions",
                return_value=payload,
            ) as mocked_load,
        ):
            response = asyncio.run(
                main.public_admin_feedback(
                    _request(method="GET", secret="public-app-secret"),
                    country_code="US",
                    submission_type=None,
                    category=None,
                    q=None,
                    page=1,
                    page_size=50,
                )
            )

        self.assertEqual(response.status_code, 200)
        filters = mocked_load.call_args.kwargs["filters"]
        self.assertEqual(filters.country_code, "US")


if __name__ == "__main__":
    unittest.main()
