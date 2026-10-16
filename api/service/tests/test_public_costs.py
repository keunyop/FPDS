"""Exercise public caching and concurrent reads through the actual ASGI app."""
import asyncio
from contextlib import contextmanager
import json
from threading import Barrier, get_ident
import unittest
from unittest.mock import patch

from api_service import main


async def request(path, query=b"", method="GET"):
    messages = []
    received = False
    async def receive():
        nonlocal received
        if not received:
            received = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()
    async def send(message):
        messages.append(message)
    scope = {"type": "http", "http_version": "1.1", "asgi": {"version": "3.0", "spec_version": "2.4"},
             "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
             "query_string": query, "headers": [], "client": ("127.0.0.1", 1234),
             "server": ("test", 80)}
    await main.app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    headers = {k.decode(): v.decode() for k, v in start["headers"]}
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], headers, body


class PublicCostTests(unittest.TestCase):
    def test_latest_snapshot_lookup_uses_one_roundtrip_and_preserves_attempt_state(self):
        from api_service.public_common import load_latest_public_snapshot
        from tests.test_public_products import _PublicConnection, _latest_success_snapshot, _latest_success_snapshot_attempt
        for status in ("completed", "failed", "started"):
            success = _latest_success_snapshot()
            attempt = {**_latest_success_snapshot_attempt(), "refresh_status": status, "snapshot_id": "newest-attempt"}
            connection = _PublicConnection(latest_success=success, latest_attempt=attempt, rows=[])
            result = load_latest_public_snapshot(connection, country_code="PH")
            self.assertEqual({k: v for k, v in result.items() if k != "latest_attempt"}, success)
            self.assertEqual(result["latest_attempt"], attempt)
            self.assertEqual(len(connection.calls), 1)
            self.assertEqual(connection.calls[0][1], {"country_code": "PH"})
            self.assertNotIn("latest_attempt", success)
        connection = _PublicConnection(latest_success=None, latest_attempt=attempt, rows=[])
        self.assertIsNone(load_latest_public_snapshot(connection, country_code="US"))
        self.assertEqual(len(connection.calls), 1)

    def test_anonymous_countries_are_cacheable_and_fresh_checks_are_not(self):
        with patch.object(main, "open_connection"), patch.object(main, "load_available_public_countries", return_value=[]):
            status, headers, body = asyncio.run(request("/api/public/countries"))
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["data"], {"countries": []})
            self.assertEqual(headers["vercel-cdn-cache-control"], "public, s-maxage=60")
            self.assertIn("max-age=0", headers["cache-control"])
            self.assertIn("x-request-id", headers)
            _, fresh, _ = asyncio.run(request("/api/public/countries", b"fresh=1"))
            self.assertEqual(fresh["cache-control"], "no-store")
            self.assertNotIn("vercel-cdn-cache-control", fresh)

    def test_head_checks_exact_country_and_id_without_shipping_product_body(self):
        for country in ("CA", "US", "PH"):
            with self.subTest(country=country), patch.object(main, "open_connection") as connection, patch.object(
                    main, "load_public_product_detail", return_value={"product": {"private_probe": "never in HEAD"}}) as load:
                status, headers, body = asyncio.run(request("/api/public/products/prod_One", f"country_code={country}&locale=fil".encode(), "HEAD"))
                self.assertEqual(status, 200)
                self.assertEqual(body, b"")
                self.assertIn("vercel-cdn-cache-control", headers)
                self.assertEqual(load.call_args.kwargs["product_id"], "prod_One")
                self.assertEqual(load.call_args.kwargs["filters"].country_code, country)
                self.assertEqual(load.call_args.kwargs["filters"].locale, "fil")
                connection.assert_called_once_with(main.app.state.settings, read_only=True)

    def test_removed_and_cross_country_products_and_validation_errors_are_uncached(self):
        with patch.object(main, "open_connection"), patch.object(main, "load_public_product_detail", return_value=None):
            for method in ("GET", "HEAD"):
                status, headers, body = asyncio.run(request("/api/public/products/missing", b"country_code=US", method))
                self.assertEqual(status, 404)
                self.assertEqual(headers["cache-control"], "no-store")
                self.assertNotIn("vercel-cdn-cache-control", headers)
                if method == "HEAD": self.assertEqual(body, b"")
        with patch.object(main, "open_connection") as connection:
            status, headers, _ = asyncio.run(request("/api/public/products", b"page=0"))
            self.assertEqual(status, 422)
            self.assertEqual(headers["cache-control"], "no-store")
            connection.assert_not_called()

    def test_credentials_admin_routes_and_errors_never_enter_public_cache(self):
        for path in ("/api/admin/countries", "/api/public/admin/feedback", "/api/public/admin/engagement-summary", "/unknown"):
            with self.subTest(path=path), patch.object(main, "open_connection") as connection:
                status, headers, _ = asyncio.run(request(path))
                self.assertIn(status, (401, 404, 503))
                self.assertEqual(headers["cache-control"], "no-store")
                self.assertNotIn("vercel-cdn-cache-control", headers)
                connection.assert_not_called()

    def test_public_database_requests_overlap_and_connections_stay_in_worker_threads(self):
        main_thread = get_ident()
        threads = []
        entered = Barrier(2)
        @contextmanager
        def connection(*args, **kwargs):
            owner = get_ident()
            self.assertNotEqual(owner, main_thread)
            self.assertEqual(kwargs, {"read_only": True})
            threads.append(owner)
            yield object()
            self.assertEqual(get_ident(), owner)
        def load(_connection):
            entered.wait(timeout=3)
            return []
        async def run():
            return await asyncio.wait_for(asyncio.gather(request("/api/public/countries"), request("/api/public/countries")), timeout=5)
        with patch.object(main, "open_connection", connection), patch.object(main, "load_available_public_countries", load):
            results = asyncio.run(run())
        self.assertEqual([r[0] for r in results], [200, 200])
        self.assertEqual(len(set(threads)), 2)

    def test_database_failures_are_uncached_and_connections_close(self):
        from api_service.errors import SourceRegistryError
        with patch.object(main, "open_connection") as connection, patch.object(main, "load_available_public_countries", side_effect=SourceRegistryError(status_code=503, code="test_unavailable", message="Unavailable")):
            status, headers, body = asyncio.run(request("/api/public/countries"))
        self.assertEqual(status, 503)
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertNotIn("vercel-cdn-cache-control", headers)
        self.assertEqual(json.loads(body)["error"]["code"], "test_unavailable")
        connection.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()