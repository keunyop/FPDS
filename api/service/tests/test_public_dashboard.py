from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.public_dashboard import (
    load_public_dashboard_rankings,
    load_public_dashboard_scatter,
    load_public_dashboard_summary,
    normalize_public_dashboard_query,
)


class _FakeResult:
    def __init__(self, *, one=None, many=None) -> None:
        self._one = one
        self._many = many or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._many


class _PublicConnection:
    def __init__(self, *, latest_success: dict | None, latest_attempt: dict | None, rows: list[dict]) -> None:
        self.latest_success = latest_success
        self.latest_attempt = latest_attempt
        self.rows = rows

    def execute(self, sql: str, params: dict[str, object]) -> _FakeResult:
        if "AND refresh_status = 'completed'" in sql:
            return _FakeResult(one=self.latest_success)
        if "FROM aggregate_refresh_run" in sql:
            return _FakeResult(one=self.latest_attempt)
        return _FakeResult(many=self.rows)


class PublicDashboardTests(unittest.TestCase):
    def test_dashboard_summary_builds_metrics_from_filtered_projection_rows(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_failed_attempt(),
            rows=_projection_rows(),
        )
        query = normalize_public_dashboard_query(
            locale="en",
            country_code="CA",
            bank_codes=None,
            product_types=["gic"],
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            axis_preset=None,
        )

        payload = load_public_dashboard_summary(connection, query=query)

        self.assertEqual(payload["metrics"][0]["value"], 3)
        self.assertEqual(payload["metrics"][2]["value"], 4.5)
        self.assertEqual(payload["breakdowns"]["products_by_bank"][0]["bank_code"], "BMO")
        self.assertEqual(payload["freshness"]["status"], "stale")

    def test_dashboard_rankings_follow_gic_priority_order(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_attempt(),
            rows=_projection_rows(),
        )
        query = normalize_public_dashboard_query(
            locale="ko",
            country_code="CA",
            bank_codes=None,
            product_types=["gic"],
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            axis_preset=None,
        )

        payload = load_public_dashboard_rankings(connection, query=query)

        self.assertEqual([widget["ranking_key"] for widget in payload["widgets"]], ["highest_display_rate", "lowest_minimum_deposit", "recently_changed_30d"])
        self.assertEqual(payload["widgets"][0]["items"][0]["product_id"], "gic-bmo-1y")
        self.assertEqual(payload["widgets"][1]["items"][0]["product_id"], "gic-td-short")

    def test_dashboard_scatter_requires_single_product_type_without_explicit_axis(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_attempt(),
            rows=_projection_rows(),
        )
        mixed_query = normalize_public_dashboard_query(
            locale="ja",
            country_code="CA",
            bank_codes=None,
            product_types=None,
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            axis_preset=None,
        )
        scoped_query = normalize_public_dashboard_query(
            locale="ja",
            country_code="CA",
            bank_codes=None,
            product_types=["gic"],
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            axis_preset="gic_term_vs_rate",
        )

        mixed_payload = load_public_dashboard_scatter(connection, query=mixed_query)
        scoped_payload = load_public_dashboard_scatter(connection, query=scoped_query)

        self.assertEqual(mixed_payload["availability_status"], "scope_selection_required")
        self.assertEqual(scoped_payload["chart_key"], "gic_term_vs_rate")
        self.assertEqual(len(scoped_payload["points"]), 3)


def _latest_success_snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "agg-001",
        "refresh_scope": "phase1_public",
        "country_code": "CA",
        "refresh_status": "completed",
        "source_change_cutoff_at": datetime(2026, 4, 13, 11, 0, tzinfo=UTC),
        "attempted_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
        "refreshed_at": datetime(2026, 4, 13, 12, 1, tzinfo=UTC),
        "stale_flag": False,
        "error_summary": None,
        "refresh_metadata": {},
    }


def _latest_success_attempt() -> dict[str, object]:
    return {
        "snapshot_id": "agg-001",
        "refresh_status": "completed",
        "attempted_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
        "refreshed_at": datetime(2026, 4, 13, 12, 1, tzinfo=UTC),
        "error_summary": None,
    }


def _latest_failed_attempt() -> dict[str, object]:
    return {
        "snapshot_id": "agg-002",
        "refresh_status": "failed",
        "attempted_at": datetime(2026, 4, 13, 13, 0, tzinfo=UTC),
        "refreshed_at": datetime(2026, 4, 13, 13, 0, tzinfo=UTC),
        "error_summary": "Refresh failed after the last successful snapshot.",
    }


def _projection_rows() -> list[dict[str, object]]:
    return [
        {
            "product_id": "chq-rbc-student",
            "bank_code": "RBC",
            "bank_name": "Royal Bank of Canada",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "chequing",
            "subtype_code": "package",
            "product_name": "RBC Student Banking",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("1.0000"),
            "public_display_fee": None,
            "monthly_fee": Decimal("0.00"),
            "effective_fee": Decimal("0.00"),
            "minimum_balance": Decimal("0.00"),
            "minimum_deposit": None,
            "term_length_days": None,
            "product_highlight_badge_code": "no_monthly_fee",
            "target_customer_tags": ["student"],
            "fee_bucket": "free",
            "minimum_balance_bucket": "none",
            "minimum_deposit_bucket": None,
            "term_bucket": None,
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 10, 0, 0, tzinfo=UTC),
            "refresh_metadata": {},
        },
        {
            "product_id": "sav-td-epremium",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "savings",
            "subtype_code": "high_interest",
            "product_name": "TD ePremium Savings Account",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("3.2000"),
            "public_display_fee": None,
            "monthly_fee": None,
            "effective_fee": None,
            "minimum_balance": Decimal("5000.00"),
            "minimum_deposit": None,
            "term_length_days": None,
            "product_highlight_badge_code": "high_rate",
            "target_customer_tags": [],
            "fee_bucket": None,
            "minimum_balance_bucket": "5000_plus",
            "minimum_deposit_bucket": None,
            "term_bucket": None,
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 3, 25, 0, 0, tzinfo=UTC),
            "refresh_metadata": {},
        },
        {
            "product_id": "gic-bmo-1y",
            "bank_code": "BMO",
            "bank_name": "BMO",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "gic",
            "subtype_code": "non_redeemable",
            "product_name": "BMO 1 Year GIC",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("4.5000"),
            "public_display_fee": None,
            "monthly_fee": None,
            "effective_fee": None,
            "minimum_balance": None,
            "minimum_deposit": Decimal("500.00"),
            "term_length_days": 365,
            "product_highlight_badge_code": None,
            "target_customer_tags": [],
            "fee_bucket": None,
            "minimum_balance_bucket": None,
            "minimum_deposit_bucket": "from_500_to_4999",
            "term_bucket": "from_1y_to_3y",
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 7, 0, 0, tzinfo=UTC),
            "refresh_metadata": {},
        },
        {
            "product_id": "gic-td-short",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "gic",
            "subtype_code": "redeemable",
            "product_name": "TD 6 Month Cashable GIC",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("4.3000"),
            "public_display_fee": None,
            "monthly_fee": None,
            "effective_fee": None,
            "minimum_balance": None,
            "minimum_deposit": Decimal("250.00"),
            "term_length_days": 180,
            "product_highlight_badge_code": "low_minimum_deposit",
            "target_customer_tags": [],
            "fee_bucket": None,
            "minimum_balance_bucket": None,
            "minimum_deposit_bucket": "under_500",
            "term_bucket": "under_1y",
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 3, 0, 0, tzinfo=UTC),
            "refresh_metadata": {},
        },
        {
            "product_id": "gic-scotia-4y",
            "bank_code": "SCOTIA",
            "bank_name": "Scotiabank",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "gic",
            "subtype_code": "non_redeemable",
            "product_name": "Scotiabank 4 Year GIC",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("4.2000"),
            "public_display_fee": None,
            "monthly_fee": None,
            "effective_fee": None,
            "minimum_balance": None,
            "minimum_deposit": Decimal("5000.00"),
            "term_length_days": 1460,
            "product_highlight_badge_code": None,
            "target_customer_tags": [],
            "fee_bucket": None,
            "minimum_balance_bucket": None,
            "minimum_deposit_bucket": "5000_plus",
            "term_bucket": "over_3y",
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
            "refresh_metadata": {},
        },
    ]


if __name__ == "__main__":
    unittest.main()
