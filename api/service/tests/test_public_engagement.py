from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
import unittest

from api_service.public_engagement import (
    PublicEngagementRateLimiter,
    load_public_product_engagement_summary,
    record_public_product_engagement,
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


class PublicEngagementTests(unittest.TestCase):
    def test_record_upserts_only_latest_active_public_product(self) -> None:
        connection = _Connection([_Result(one={"product_id": "prod-1"})])

        recorded = record_public_product_engagement(
            connection,
            country_code=" us ",
            product_id="prod-1",
            event_type="product_detail_click",
        )

        self.assertTrue(recorded)
        sql, params = connection.calls[0]
        self.assertIn("projection.status = 'active'", sql)
        self.assertIn("ON CONFLICT", sql)
        self.assertEqual(params["country_code"], "US")
        self.assertEqual(params["product_id"], "prod-1")

    def test_record_rejects_unknown_event_without_query(self) -> None:
        connection = _Connection([])

        recorded = record_public_product_engagement(
            connection,
            country_code="US",
            product_id="prod-1",
            event_type="search_query",
        )

        self.assertFalse(recorded)
        self.assertEqual(connection.calls, [])

    def test_summary_returns_product_bank_and_daily_aggregates(self) -> None:
        now = datetime(2026, 8, 30, 12, tzinfo=UTC)
        connection = _Connection(
            [
                _Result(
                    one={
                        "product_detail_clicks": 8,
                        "official_bank_clicks": 3,
                        "finder_product_selections": 5,
                        "first_event_date": date(2026, 8, 29),
                        "last_recorded_at": now,
                    }
                ),
                _Result(
                    many=[
                        {
                            "country_code": "US",
                            "product_id": "prod-1",
                            "bank_code": "BANK",
                            "bank_name": "Bank",
                            "product_name": "Everyday Savings",
                            "product_type": "savings",
                            "product_detail_clicks": 8,
                            "official_bank_clicks": 3,
                            "finder_product_selections": 5,
                            "last_recorded_at": now,
                        }
                    ]
                ),
                _Result(
                    many=[
                        {
                            "event_date": date(2026, 8, 30),
                            "product_detail_clicks": 8,
                            "official_bank_clicks": 3,
                            "finder_product_selections": 5,
                        }
                    ]
                ),
            ]
        )

        summary = load_public_product_engagement_summary(
            connection,
            country_code="us",
        )

        self.assertEqual(summary["country_code"], "US")
        self.assertEqual(summary["retention_days"], 400)
        self.assertEqual(summary["totals"]["published_products"], 1)
        self.assertEqual(summary["products"][0]["finder_product_selections"], 5)
        self.assertEqual(summary["banks"][0]["official_bank_clicks"], 3)
        self.assertEqual(summary["daily"][0]["event_date"], "2026-08-30")
        for sql, _params in connection.calls:
            self.assertIn("%(country_code)s::text IS NULL", sql)
        self.assertIn("event_date >= current_date - 399", connection.calls[0][0])
        self.assertIn("event_date >= current_date - 399", connection.calls[1][0])

    def test_rate_limiter_is_bounded_without_persistent_identity(self) -> None:
        limiter = PublicEngagementRateLimiter(limit=2, window_seconds=60)
        self.assertTrue(limiter.allow())
        self.assertTrue(limiter.allow())
        self.assertFalse(limiter.allow())

    def test_migration_keeps_only_daily_product_counters_for_400_days(self) -> None:
        migration = (
            Path(__file__).resolve().parents[3]
            / "db"
            / "migrations"
            / "0045_public_product_engagement.sql"
        ).read_text(encoding="utf-8")
        self.assertIn("public_product_engagement_daily", migration)
        self.assertIn("event_date < current_date - 399", migration)
        self.assertNotIn("ip_address", migration)
        self.assertNotIn("search_query", migration)


if __name__ == "__main__":
    unittest.main()
