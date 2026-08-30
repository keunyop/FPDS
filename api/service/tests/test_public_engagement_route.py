from __future__ import annotations

import asyncio
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from starlette.requests import Request

from api_service import main
from api_service.models import PublicEngagementRequest


def _request(*, secret: str | None = None) -> Request:
    headers = []
    if secret is not None:
        headers.append((b"x-fpds-public-app-secret", secret.encode("utf-8")))
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/public/engagement",
            "headers": headers,
            "query_string": b"",
            "app": main.app,
        }
    )
    request.state.request_id = "req-public-engagement"
    request.state.generated_at = "2026-08-30T00:00:00+00:00"
    return request


class PublicEngagementRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_settings = main.app.state.settings

    def tearDown(self) -> None:
        main.app.state.settings = self.original_settings

    def test_missing_server_credential_fails_closed(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret=None,
        )

        response = asyncio.run(
            main.public_engagement(
                _request(),
                PublicEngagementRequest(
                    country_code="US",
                    product_id="prod-1",
                    event_type="product_detail_click",
                ),
            )
        )

        payload = json.loads(response.body)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(payload["error"]["code"], "public_app_credential_not_configured")

    def test_valid_credential_records_active_product(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        with (
            patch.object(main, "open_connection") as mocked_open_connection,
            patch.object(main, "record_public_product_engagement", return_value=True) as mocked_record,
        ):
            mocked_open_connection.return_value.__enter__.return_value = object()
            response = asyncio.run(
                main.public_engagement(
                    _request(secret="public-app-secret"),
                    PublicEngagementRequest(
                        country_code="US",
                        product_id="prod-1",
                        event_type="official_bank_click",
                    ),
                )
            )

        self.assertEqual(response.status_code, 202)
        mocked_record.assert_called_once()

    def test_invalid_credential_does_not_open_database(self) -> None:
        main.app.state.settings = replace(
            self.original_settings,
            public_app_api_secret="public-app-secret",
        )
        with patch.object(main, "open_connection") as mocked_open_connection:
            response = asyncio.run(
                main.public_engagement(
                    _request(secret="wrong-secret"),
                    PublicEngagementRequest(
                        country_code="US",
                        product_id="prod-1",
                        event_type="finder_product_selected",
                    ),
                )
            )

        self.assertEqual(response.status_code, 401)
        mocked_open_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
