from copy import deepcopy
from datetime import UTC, datetime, timedelta
import unittest
from unittest.mock import patch

from api_service.public_common import build_freshness_payload
from api_service.public_verification import product_verification, overdue_products, verification_summary, VERIFICATION_POLICY
from api_service.public_verification_report import build_report
from api_service.public_products import load_public_products, load_public_product_detail, normalize_public_products_query
from tests.test_public_products import _PublicConnection, _latest_success_snapshot, _latest_success_snapshot_attempt, _projection_rows

NOW = datetime(2026, 9, 21, tzinfo=UTC)
POLICY = {"savings": (7, 30), "chequing": (30, 90)}


class PublicVerificationTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("api_service.public_verification.VERIFICATION_POLICY", POLICY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exact_boundaries_for_each_policy(self):
        for kind, (due, expiry) in POLICY.items():
            for age, status in ((0, "within_window"), (due * 86400 - 1, "within_window"), (due * 86400, "review_due"), (expiry * 86400 - 1, "review_due"), (expiry * 86400, "expired")):
                with self.subTest(kind=kind, age=age):
                    row = {"product_type": kind, "last_verified_at": NOW - timedelta(seconds=age)}
                    self.assertEqual(product_verification(row, now=NOW)["status"], status)

    def test_missing_malformed_future_and_unknown_type_fail_closed(self):
        for value in (None, "", "bad", 123, NOW + timedelta(seconds=1)):
            result = product_verification({"product_type": "savings", "last_verified_at": value}, now=NOW)
            self.assertEqual(result["status"], "unknown")
            self.assertIsNone(result["last_verified_at"])
        self.assertEqual(product_verification({"product_type": "other", "last_verified_at": NOW}, now=NOW)["status"], "unknown")
        self.assertEqual(product_verification({"product_type": "savings", "last_verified_at": "2026-09-21T01:00:00+01:00"}, now=NOW)["status"], "within_window")

    def test_snapshot_regeneration_never_resets_product_age(self):
        rows = [{"product_type": "savings", "last_verified_at": NOW - timedelta(days=40)}]
        before = deepcopy(rows)
        snapshot = {"snapshot_id": "new", "refreshed_at": NOW, "stale_flag": False}
        payload = build_freshness_payload(snapshot, cache_ttl_sec=300, rows=rows, now=NOW)
        self.assertEqual(payload["snapshot_status"], "completed")
        self.assertEqual(payload["status"], "stale")
        self.assertEqual(payload["verification"]["counts"]["expired"], 1)
        self.assertEqual(rows, before)
        self.assertEqual(build_freshness_payload(snapshot, cache_ttl_sec=300, now=NOW)["status"], "stale")

    def test_fresh_products_do_not_hide_failed_refresh(self):
        rows = [{"product_type": "savings", "last_verified_at": NOW}]
        snapshot = {"refreshed_at": NOW - timedelta(hours=1), "latest_attempt": {"refresh_status": "failed", "attempted_at": NOW}}
        result = build_freshness_payload(snapshot, cache_ttl_sec=300, rows=rows, now=NOW)
        self.assertEqual(result["snapshot_status"], "stale")
        self.assertEqual(result["status"], "stale")
        snapshot.pop("latest_attempt")
        self.assertEqual(build_freshness_payload(snapshot, cache_ttl_sec=300, rows=rows, now=NOW)["status"], "fresh")
        self.assertEqual(build_freshness_payload(None, cache_ttl_sec=300, now=NOW)["status"], "unavailable")

    def test_product_expiry_does_not_revive_an_old_snapshot_error(self):
        snapshot = {"refreshed_at": NOW, "latest_attempt": {"refresh_status": "failed", "attempted_at": NOW - timedelta(days=1), "error_summary": "old error"}}
        rows = [{"product_type": "savings", "last_verified_at": NOW - timedelta(days=40)}]
        result = build_freshness_payload(snapshot, cache_ttl_sec=300, rows=rows, now=NOW)
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["snapshot_status"], "completed")
        self.assertIsNone(result["latest_error_summary"])

    def test_report_is_safe_sorted_and_does_not_include_private_metadata(self):
        rows = [{"product_id": str(age), "product_type": "savings", "last_verified_at": NOW - timedelta(days=age), "refresh_metadata": {"private": "secret"}} for age in (1, 8, 50)]
        rows.append({"product_id": "unknown", "product_type": "savings"})
        self.assertEqual([r["product_id"] for r in overdue_products(rows, now=NOW)], ["50", "unknown", "8"])
        self.assertNotIn("secret", str(overdue_products(rows, now=NOW)))
        self.assertEqual(verification_summary(rows, now=NOW)["counts"], dict(within_window=1, review_due=1, expired=1, unknown=1))
        connection = _PublicConnection(latest_success=_latest_success_snapshot(), latest_attempt=None, rows=rows)
        report = build_report(connection, country_code="US", now=NOW)
        self.assertEqual(report["country_code"], "US")
        self.assertTrue(all(params["country_code"] == "US" for sql, params in connection.calls))
        with self.assertRaises(ValueError):
            build_report(connection, country_code="bad", now=NOW)

    def test_list_summary_precedes_pagination_and_detail_is_product_scoped(self):
        connection = _PublicConnection(latest_success=_latest_success_snapshot(), latest_attempt=_latest_success_snapshot_attempt(), rows=_projection_rows())
        query = normalize_public_products_query(locale="en", country_code="CA", bank_codes=None, product_types=None, subtype_codes=None, target_customer_tags=None, fee_bucket=None, minimum_balance_bucket=None, minimum_deposit_bucket=None, term_bucket=None, sort_by="default", sort_order="desc", page=1, page_size=1)
        payload = load_public_products(connection, query=query)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["freshness"]["verification"]["total_products"], payload["total_items"])
        product = payload["items"][0]
        detail = load_public_product_detail(connection, product_id=product["product_id"], filters=query.filters)
        self.assertEqual(detail["freshness"]["verification"]["total_products"], 1)
        self.assertEqual(detail["product"]["verification"]["last_verified_at"], product["last_verified_at"])


class InitialPolicyTests(unittest.TestCase):
    def test_every_governed_type_has_the_documented_warning_window(self):
        self.assertEqual(VERIFICATION_POLICY, {
            "savings": (7, 30), "gic": (7, 30), "mortgage": (7, 30),
            "personal-loan": (7, 30), "line-of-credit": (7, 30),
            "chequing": (30, 90), "credit-card": (30, 90),
        })
        for kind, (due, expiry) in VERIFICATION_POLICY.items():
            for age, expected in ((due - 1, "within_window"), (due, "review_due"), (expiry, "expired")):
                with self.subTest(kind=kind, age=age):
                    result = product_verification({"product_type": kind, "last_verified_at": NOW - timedelta(days=age)}, now=NOW)
                    self.assertEqual(result["status"], expected)

    def test_no_snapshot_report_and_invalid_datetime_extremes(self):
        connection = _PublicConnection(latest_success=None, latest_attempt=None, rows=[])
        self.assertEqual(build_report(connection, country_code="CA", now=NOW)["availability"], "unavailable")
        for value in ("0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"):
            self.assertEqual(product_verification({"product_type": "savings", "last_verified_at": value}, now=NOW)["status"], "unknown")
