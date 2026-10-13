"""Egress fixes preserve eligibility and isolate bounded snapshot reuse."""
from copy import deepcopy
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Barrier, Event, Lock
from types import SimpleNamespace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api_service.public_common import load_public_projection_rows
from api_service.public_projection_cache import PublicProjectionCache, connection_scope
from api_service.public_products import (
    load_public_products, load_public_filters, load_public_product_detail,
    load_available_public_countries, normalize_public_products_query,
)
from tests.test_public_products import (
    _PublicConnection, _FakeResult, _projection_rows,
    _latest_success_snapshot, _latest_success_snapshot_attempt,
)
from tests import test_public_proof_scope as proof_fixtures


class ReadConnection(_PublicConnection):
    def __init__(self, *, database="db", role="reader", options="", read_only=True):
        super().__init__(latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_snapshot_attempt(), rows=_projection_rows(),
            countries=[{"code": "CA", "snapshot_id": "agg-001"}])
        self.info = SimpleNamespace(host="pooler.example", port=6543, dbname=database,
                                    user=role, options=options)
        self.read_only = read_only

    def execute(self, sql, params):
        result = super().execute(sql, params)
        if "FROM public_product_projection AS p" in sql and "product_id" in params:
            return _FakeResult(many=[r for r in self.rows if r["product_id"] == params["product_id"]])
        return result

    @property
    def projection_calls(self):
        return [(sql, params) for sql, params in self.calls if "FROM public_product_projection AS p" in sql]


def query(**overrides):
    args = dict(locale="en", country_code="CA", bank_codes=None, product_types=None,
        subtype_codes=None, target_customer_tags=None, fee_bucket=None,
        minimum_balance_bucket=None, minimum_deposit_bucket=None, term_bucket=None,
        sort_by="default", sort_order="desc", page=1, page_size=1)
    args.update(overrides)
    return normalize_public_products_query(**args)


def without_evaluation_time(value):
    if isinstance(value, dict):
        return {k: without_evaluation_time(v) for k, v in value.items() if k != "evaluated_at"}
    if isinstance(value, list):
        return [without_evaluation_time(v) for v in value]
    return value


class PublicEgressTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.cache = PublicProjectionCache(clock=lambda: self.now, max_entries=3)
        self.patcher = patch("api_service.public_projection_cache.projection_cache", self.cache)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def rows(self, connection, **changes):
        args = dict(snapshot_id="agg-001", country_code="CA")
        args.update(changes)
        return load_public_projection_rows(connection, **args)

    def test_countries_filters_pages_and_detail_share_only_validated_rows(self):
        connection = ReadConnection()
        connection.rows.append(proof_fixtures.PublicProofScopeTests().row(
            "Unlimited transactions at 40,000+ fee-free ATMs nationwide"))
        # Make the bad row country-local; it must still fail the existing proof gate.
        connection.rows[-1]["country_code"] = "CA"
        baseline = load_public_products(ReadConnection(read_only=False), query=query())
        first = load_public_products(connection, query=query())
        self.assertEqual(without_evaluation_time(first), without_evaluation_time(baseline))
        self.assertEqual(first["total_items"], baseline["total_items"])
        second = load_public_products(connection, query=query(page=2, locale="ja"))
        self.assertEqual(first["total_items"], second["total_items"])
        self.assertNotEqual(first["items"][0]["product_id"], second["items"][0]["product_id"])
        filters = load_public_filters(connection, filters=query().filters)
        countries = load_available_public_countries(connection)
        self.assertEqual(countries, filters["countries"])
        self.assertEqual(countries[0]["count"], first["total_items"])
        detail = load_public_product_detail(connection,
            product_id=first["items"][0]["product_id"], filters=query().filters)
        self.assertEqual(without_evaluation_time(detail["product"]), without_evaluation_time(first["items"][0]))
        self.assertEqual(len(connection.projection_calls), 1)
        cached = self.rows(connection)
        self.assertNotIn("p", [r["product_id"] for r in cached])
        self.assertNotIn("approved_collection_payload", str(cached))
        self.assertNotIn("approved_field_mapping_metadata", str(cached))
        self.assertNotIn("official_evidence_quote", str(cached))

    def test_detail_cold_read_is_parameterized_and_missing_stays_missing(self):
        connection = ReadConnection()
        product = next(r for r in connection.rows if r["product_type"] == "savings")
        result = load_public_product_detail(connection,
            product_id=" " + product["product_id"] + " ", filters=query().filters)
        self.assertEqual(result["product"]["product_id"], product["product_id"])
        sql, params = connection.projection_calls[0]
        self.assertIn("AND p.product_id = %(product_id)s", sql)
        self.assertEqual(params["product_id"], product["product_id"])
        missing = "missing' OR true --"
        self.assertIsNone(load_public_product_detail(connection, product_id=missing, filters=query().filters))
        self.assertNotIn(missing, connection.projection_calls[-1][0])
        self.assertEqual(connection.projection_calls[-1][1]["product_id"], missing)
        self.assertIsNone(load_public_product_detail(connection, product_id=missing, filters=query().filters))
        self.assertEqual(len(connection.projection_calls), 2)

    def test_country_snapshot_database_role_options_and_policy_are_separate(self):
        connection = ReadConnection()
        self.rows(connection)
        self.rows(connection)
        self.rows(connection, country_code="US")
        self.rows(connection, snapshot_id="new-snapshot")
        self.assertEqual(len(connection.projection_calls), 3)
        for changes in ({"database": "other"}, {"role": "other"}, {"options": "-c search_path=other"}):
            other = ReadConnection(**changes)
            self.rows(other)
            self.assertEqual(len(other.projection_calls), 1)
        self.rows(connection)
        before = len(connection.projection_calls)
        with patch("worker.pipeline.fpds_market_profile.MARKET_PROFILE_VERSION", "next-policy"):
            self.rows(connection)
        self.assertEqual(len(connection.projection_calls), before + 1)

    def test_expiry_revalidates_and_read_write_connections_bypass_cache(self):
        connection = ReadConnection()
        first = self.rows(connection)
        connection.rows = []
        self.now = 59.99
        self.assertEqual(self.rows(connection), first)
        self.now = 60
        self.assertEqual(self.rows(connection), [])
        self.assertEqual(len(connection.projection_calls), 2)
        writer = ReadConnection(read_only=False)
        self.rows(writer)
        writer.rows = []
        self.assertEqual(self.rows(writer), [])
        self.assertEqual(len(writer.projection_calls), 2)
        self.assertIsNone(connection_scope(object()))
        self.assertIsNone(connection_scope(writer))

    def test_expiry_rechecks_tampered_financial_essentials(self):
        connection = ReadConnection()
        product = next(r for r in connection.rows if r["product_type"] == "chequing")
        product_id = product["product_id"]
        self.assertIn(product_id, [r["product_id"] for r in self.rows(connection)])
        product["approved_collection_payload"].pop("unlimited_transactions_flag")
        self.now = 60
        self.assertNotIn(product_id, [r["product_id"] for r in self.rows(connection)])
        self.assertEqual(len(connection.projection_calls), 2)

    def test_callers_cannot_mutate_shared_rows_or_optional_facts(self):
        connection = ReadConnection()
        original = deepcopy(self.rows(connection))
        changed = self.rows(connection)
        changed[0]["refresh_metadata"]["private"] = "mutation"
        changed.clear()
        self.assertEqual(self.rows(connection), original)
        self.assertEqual(len(connection.projection_calls), 1)

    def test_proof_sql_projects_only_the_complete_required_quote(self):
        connection = ReadConnection()
        self.rows(connection)
        sql = connection.projection_calls[0][0]
        self.assertNotIn("approved_candidate.field_mapping_metadata AS", sql)
        self.assertIn("-> 'unlimited_transactions_flag' -> 'official_evidence_quote'", sql)
        self.assertIn("approved_version.normalized_payload AS approved_collection_payload", sql)


class ReadOnlyConnectionTests(unittest.TestCase):
    def test_public_connection_sets_read_only_before_yielding(self):
        from api_service.db import open_connection
        settings = SimpleNamespace(database_url="postgresql://example.invalid/test")
        with patch("psycopg.connect") as connect:
            connected = connect.return_value.__enter__.return_value
            connected.read_only = None
            with open_connection(settings, read_only=True) as connection:
                self.assertIs(connection, connected)
                self.assertIs(connection.read_only, True)
        with patch("psycopg.connect") as connect:
            connected = connect.return_value.__enter__.return_value
            connected.read_only = None
            with open_connection(settings) as connection:
                self.assertIsNone(connection.read_only)


class ProjectionCacheBoundaryTests(unittest.TestCase):
    def test_expired_failure_is_not_cached_or_served_stale(self):
        now = [0]
        cache = PublicProjectionCache(clock=lambda: now[0])
        cache.load(("key",), lambda: [{"product_id": "old"}])
        now[0] = 60
        def fail():
            raise RuntimeError("database unavailable")
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            cache.load(("key",), fail)
        self.assertIsNone(cache.get(("key",)))
        self.assertEqual(cache.load(("key",), lambda: []), [])

    def test_lru_is_bounded_and_empty_results_are_cached(self):
        cache = PublicProjectionCache(max_entries=2)
        cache.load((1,), lambda: [])
        cache.load((2,), lambda: [{"product_id": "two"}])
        self.assertEqual(cache.get((1,)), [])
        cache.load((3,), lambda: [])
        self.assertIsNone(cache.get((2,)))
        self.assertEqual(cache.load((1,), lambda: self.fail("unexpected reload")), [])

    def test_concurrent_misses_share_result_or_failure_without_blocking_other_keys(self):
        for failure in (False, True):
            with self.subTest(failure=failure):
                cache = PublicProjectionCache()
                cache.load(("other-country",), lambda: [])
                entered, waiting, release = Event(), Event(), Event()
                waiters, calls = [], []
                waiters_lock = Lock()

                class ObservedFuture(Future):
                    def result(self, timeout=None):
                        with waiters_lock:
                            waiters.append(1)
                            if len(waiters) == 5:
                                waiting.set()
                        return super().result(timeout=3)

                barrier = Barrier(6)
                def request():
                    barrier.wait(timeout=3)
                    def load():
                        calls.append(1)
                        entered.set()
                        if not release.wait(timeout=3):
                            raise TimeoutError("test loader release")
                        if failure:
                            raise RuntimeError("upstream unavailable")
                        return [{"product_id": "one", "nested": []}]
                    return cache.load(("same",), load)

                with patch("api_service.public_projection_cache.Future", ObservedFuture), \
                     ThreadPoolExecutor(max_workers=6) as pool:
                    futures = [pool.submit(request) for _ in range(6)]
                    try:
                        self.assertTrue(entered.wait(timeout=3))
                        self.assertTrue(waiting.wait(timeout=3))
                        self.assertEqual(cache.get(("other-country",)), [])
                        self.assertEqual(cache.load(("new-country",), lambda: []), [])
                    finally:
                        release.set()
                    if failure:
                        for future in futures:
                            with self.assertRaisesRegex(RuntimeError, "upstream unavailable"):
                                future.result(timeout=3)
                        self.assertIsNone(cache.get(("same",)))
                        self.assertEqual(cache.load(("same",), lambda: []), [])
                    else:
                        results = [future.result(timeout=3) for future in futures]
                        results[0][0]["nested"].append("changed")
                        self.assertEqual(results[1][0]["nested"], [])
                self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
