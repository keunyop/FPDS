from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest

from api_service.public_products import (
    load_public_filters,
    load_public_product_detail,
    load_public_products,
    normalize_public_products_query,
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
        self.assertEqual(payload["items"][0]["product_url"], "https://www.bmo.com/main/personal/investments/gic/")
        self.assertEqual(payload["items"][0]["product_type_label"], "GIC")
        self.assertEqual(payload["items"][1]["product_id"], "gic-td-short")
        self.assertEqual(payload["freshness"]["status"], "fresh")
        self.assertEqual(payload["applied_filters"]["bank_code"], ["TD", "BMO"])

    def test_load_public_products_visible_sort_options_are_stable(self) -> None:
        cases = [
            ("monthly_fee", "asc", ["chq-rbc-student", "chq-td-everyday"]),
            ("minimum_balance", "asc", ["chq-rbc-student", "sav-bmo-standard", "chq-td-everyday"]),
            ("minimum_deposit", "asc", ["gic-td-short", "gic-bmo-1y"]),
        ]

        for sort_by, sort_order, expected_prefix in cases:
            with self.subTest(sort_by=sort_by):
                connection = _PublicConnection(
                    latest_success=_latest_success_snapshot(),
                    latest_attempt=_latest_success_snapshot_attempt(),
                    rows=_projection_rows(),
                )
                query = normalize_public_products_query(
                    locale="en",
                    country_code="CA",
                    bank_codes=None,
                    product_types=None,
                    subtype_codes=None,
                    target_customer_tags=None,
                    fee_bucket=None,
                    minimum_balance_bucket=None,
                    minimum_deposit_bucket=None,
                    term_bucket=None,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=1,
                    page_size=20,
                )

                payload = load_public_products(connection, query=query)

                self.assertEqual([item["product_id"] for item in payload["items"][: len(expected_prefix)]], expected_prefix)
                self.assertEqual(payload["sort"], {"sort_by": sort_by, "sort_order": sort_order})

    def test_load_public_products_handles_bad_numeric_values_in_visible_sorts(self) -> None:
        bad_row = dict(_projection_rows()[0])
        bad_row.update(
            {
                "product_id": "bad-numeric-row",
                "bank_code": "BAD",
                "bank_name": "Bad Numeric Bank",
                "product_name": "Bad Numeric Deposit",
                "public_display_rate": "not-a-number",
                "effective_fee": "not-a-number",
                "minimum_balance": Decimal("NaN"),
                "minimum_deposit": "Infinity",
                "refresh_metadata": {
                    "standard_rate": "not-a-number",
                    "base_12_month_rate": "Infinity",
                    "term_rate_table": [
                        {
                            "term_label": "Bad rate row",
                            "term_length_days": "365",
                            "rate": "NaN",
                            "minimum_deposit": "not-a-number",
                        }
                    ],
                },
            }
        )

        for sort_by in ("display_rate", "monthly_fee", "minimum_balance", "minimum_deposit"):
            with self.subTest(sort_by=sort_by):
                connection = _PublicConnection(
                    latest_success=_latest_success_snapshot(),
                    latest_attempt=_latest_success_snapshot_attempt(),
                    rows=[*_projection_rows(), bad_row],
                )
                query = normalize_public_products_query(
                    locale="en",
                    country_code="CA",
                    bank_codes=None,
                    product_types=None,
                    subtype_codes=None,
                    target_customer_tags=None,
                    fee_bucket=None,
                    minimum_balance_bucket=None,
                    minimum_deposit_bucket=None,
                    term_bucket=None,
                    sort_by=sort_by,
                    sort_order="asc",
                    page=1,
                    page_size=20,
                )

                payload = load_public_products(connection, query=query)
                serialized_bad_row = next(item for item in payload["items"] if item["product_id"] == "bad-numeric-row")

                self.assertIsNone(serialized_bad_row["public_display_rate"])
                self.assertIsNone(serialized_bad_row["public_display_fee"])
                self.assertIsNone(serialized_bad_row["minimum_balance"])
                self.assertIsNone(serialized_bad_row["minimum_deposit"])
                self.assertIsNone(serialized_bad_row["standard_rate"])
                self.assertIsNone(serialized_bad_row["base_12_month_rate"])
                self.assertIsNone(serialized_bad_row["term_rate_table"][0]["rate"])
                self.assertIsNone(serialized_bad_row["term_rate_table"][0]["minimum_deposit"])

    def test_load_public_product_detail_returns_product_by_id(self) -> None:
        connection = _PublicConnection(
            latest_success=_latest_success_snapshot(),
            latest_attempt=_latest_success_snapshot_attempt(),
            rows=_projection_rows(),
        )
        filters = normalize_public_products_query(
            locale="en",
            country_code="CA",
            bank_codes=None,
            product_types=None,
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

        payload = load_public_product_detail(connection, product_id="sav-td-epremium", filters=filters)

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["product"]["bank_code"], "TD")
        self.assertEqual(payload["product"]["product_url"], "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account")
        self.assertEqual(payload["product"]["standard_rate"], 3.2)
        self.assertEqual(payload["product"]["base_12_month_rate"], 3.2)
        self.assertEqual(payload["product"]["eligibility_text"], "Canadian residents who meet TD account opening requirements.")
        self.assertEqual(payload["product"]["application_method"], "Apply online, in branch, or by phone.")
        self.assertEqual(payload["product"]["post_maturity_interest_rate"], "Not applicable for this savings account.")
        self.assertEqual(payload["product"]["tax_benefits"], "No registered-plan tax benefit is disclosed.")
        self.assertEqual(payload["product"]["deposit_insurance"], "Eligible deposits are protected by CDIC limits.")
        self.assertEqual(payload["product"]["term_rate_table"][0]["term_label"], "12 months")
        self.assertEqual(payload["freshness"]["snapshot_id"], "agg-001")

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
            "product_url": "https://www.rbcroyalbank.com/accounts/student-banking.html",
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
            "product_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/chequing-accounts/everyday-chequing-account",
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
            "refresh_metadata": {
                "standard_rate": 3.2,
                "base_12_month_rate": 3.2,
                "eligibility_text": "Canadian residents who meet TD account opening requirements.",
                "application_method": "Apply online, in branch, or by phone.",
                "post_maturity_interest_rate": "Not applicable for this savings account.",
                "tax_benefits": "No registered-plan tax benefit is disclosed.",
                "deposit_insurance": "Eligible deposits are protected by CDIC limits.",
                "term_rate_table": [
                    {
                        "term_label": "12 months",
                        "term_length_days": 365,
                        "rate": 3.2,
                        "minimum_deposit": None,
                        "notes": "Savings rate shown for comparison.",
                    }
                ],
            },
            "product_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account",
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
            "product_url": "https://www.bmo.com/main/personal/bank-accounts/savings-accounts/savings-builder/",
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
            "product_url": "https://www.bmo.com/main/personal/investments/gic/",
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
            "product_url": "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic/cashable-gic",
        },
    ]


if __name__ == "__main__":
    unittest.main()
