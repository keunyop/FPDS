from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.public_products import load_public_filters, load_public_products, normalize_public_products_query


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
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> _FakeResult:
        self.calls.append((sql, params))
        if "AND refresh_status = 'completed'" in sql:
            return _FakeResult(one=self.latest_success)
        if "FROM aggregate_refresh_run" in sql:
            return _FakeResult(one=self.latest_attempt)
        return _FakeResult(many=self.rows)


class PublicProductsTests(unittest.TestCase):
    def test_load_public_products_sorts_and_paginates_snapshot_rows(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_snapshot_attempt(),
            rows=_projection_rows(),
        )
        query = normalize_public_products_query(
            locale="ko",
            country_code="CA",
            bank_codes=["TD", "BMO"],
            product_types=["gic", "savings"],
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            sort_by="display_rate",
            sort_order="desc",
            page=1,
            page_size=2,
        )

        payload = load_public_products(connection, query=query)

        self.assertEqual(payload["total_items"], 4)
        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["product_id"], "gic-bmo-1y")
        self.assertEqual(payload["items"][0]["product_type_label"], "GIC")
        self.assertEqual(payload["items"][1]["product_id"], "gic-td-short")
        self.assertEqual(payload["freshness"]["status"], "fresh")
        self.assertEqual(payload["applied_filters"]["bank_code"], ["TD", "BMO"])

    def test_load_public_filters_returns_localized_counts(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_snapshot_attempt(),
            rows=_projection_rows(),
        )
        filters = normalize_public_products_query(
            locale="ja",
            country_code="CA",
            bank_codes=None,
            product_types=["chequing"],
            subtype_codes=None,
            target_customer_tags=None,
            fee_bucket=None,
            minimum_balance_bucket=None,
            minimum_deposit_bucket=None,
            term_bucket=None,
            sort_by="default",
            sort_order="desc",
            page=1,
            page_size=20,
        ).filters

        payload = load_public_filters(connection, filters=filters)

        self.assertEqual(payload["product_types"][0]["code"], "chequing")
        self.assertEqual(payload["product_types"][0]["label"], "当座預金")
        self.assertEqual(payload["banks"][0]["code"], "RBC")
        self.assertEqual(payload["target_customer_tags"][0]["code"], "student")
        self.assertEqual(payload["fee_buckets"][0]["code"], "free")


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


def _latest_success_snapshot_attempt() -> dict[str, object]:
    return {
        "snapshot_id": "agg-001",
        "refresh_status": "completed",
        "attempted_at": datetime(2026, 4, 13, 12, 0, tzinfo=UTC),
        "refreshed_at": datetime(2026, 4, 13, 12, 1, tzinfo=UTC),
        "error_summary": None,
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
            "product_id": "chq-td-everyday",
            "bank_code": "TD",
            "bank_name": "TD Bank",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "chequing",
            "subtype_code": "standard",
            "product_name": "TD Everyday Chequing Account",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": None,
            "public_display_fee": None,
            "monthly_fee": Decimal("16.95"),
            "effective_fee": Decimal("16.95"),
            "minimum_balance": Decimal("5000.00"),
            "minimum_deposit": None,
            "term_length_days": None,
            "product_highlight_badge_code": None,
            "target_customer_tags": [],
            "fee_bucket": "high_fee",
            "minimum_balance_bucket": "5000_plus",
            "minimum_deposit_bucket": None,
            "term_bucket": None,
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 1, 0, 0, tzinfo=UTC),
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
            "product_id": "sav-bmo-standard",
            "bank_code": "BMO",
            "bank_name": "BMO",
            "country_code": "CA",
            "product_family": "deposit",
            "product_type": "savings",
            "subtype_code": "standard",
            "product_name": "BMO Savings Builder",
            "source_language": "en",
            "currency": "CAD",
            "status": "active",
            "public_display_rate": Decimal("1.5000"),
            "public_display_fee": None,
            "monthly_fee": None,
            "effective_fee": None,
            "minimum_balance": Decimal("100.00"),
            "minimum_deposit": None,
            "term_length_days": None,
            "product_highlight_badge_code": None,
            "target_customer_tags": [],
            "fee_bucket": None,
            "minimum_balance_bucket": "under_1000",
            "minimum_deposit_bucket": None,
            "term_bucket": None,
            "last_verified_at": datetime(2026, 4, 12, 0, 0, tzinfo=UTC),
            "last_changed_at": datetime(2026, 4, 8, 0, 0, tzinfo=UTC),
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
    ]


if __name__ == "__main__":
    unittest.main()
