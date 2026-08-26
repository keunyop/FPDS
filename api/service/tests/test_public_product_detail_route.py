from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import patch

from starlette.requests import Request

from api_service import main


class PublicProductDetailRouteTests(unittest.TestCase):
    def test_missing_public_product_returns_not_found_response(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/public/products/missing-product",
                "headers": [],
                "query_string": b"",
                "app": main.app,
            }
        )
        request.state.request_id = "req-public-product-not-found"
        request.state.generated_at = "2026-08-25T00:00:00+00:00"

        with (
            patch.object(main, "open_connection") as mocked_open_connection,
            patch.object(main, "load_public_product_detail", return_value=None),
        ):
            mocked_open_connection.return_value.__enter__.return_value = object()
            response = asyncio.run(
                main.public_product_detail(
                    request,
                    "missing-product",
                    locale="en",
                    country_code="CA",
                )
            )

        payload = json.loads(response.body)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(payload["error"]["code"], "not_found")
        self.assertEqual(payload["meta"]["request_id"], request.state.request_id)


if __name__ == "__main__":
    unittest.main()
