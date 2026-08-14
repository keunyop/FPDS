from __future__ import annotations

import unittest

from worker.pipeline.fpds_approval_policy import (
    collection_fields_for_product_type,
    comparison_quality,
    dynamic_repair_fields,
)
from worker.pipeline.fpds_market_profile import market_profile_metadata


class ComparisonQualityPolicyTests(unittest.TestCase):
    def test_us_card_collection_prefers_range_summary_and_keeps_scalar_alternative(self) -> None:
        fields = collection_fields_for_product_type(
            product_type="credit-card",
            country_code="US",
            expected_fields=[],
        )

        self.assertIn("purchase_interest_rate", fields)
        self.assertIn("purchase_interest_rate_summary", fields)

        ranged = comparison_quality(
            product_type="credit-card",
            country_code="US",
            expected_fields=fields,
            candidate_payload={
                "annual_fee": 0,
                "purchase_interest_rate_summary": "Purchase APR 17.49%-27.49% variable",
            },
        )
        fixed = comparison_quality(
            product_type="credit-card",
            country_code="US",
            expected_fields=fields,
            candidate_payload={"annual_fee": 95, "purchase_interest_rate": 19.99},
        )

        self.assertTrue(ranged.complete)
        self.assertIn("purchase_interest_rate_summary", ranged.satisfied_fields)
        self.assertTrue(fixed.complete)
        self.assertIn("purchase_interest_rate", fixed.satisfied_fields)

    def test_personal_loan_accepts_evidence_preserving_apr_range(self) -> None:
        quality = comparison_quality(
            product_type="personal-loan",
            expected_fields=[],
            candidate_payload={
                "interest_rate_summary": "APR 9.99%-17.49%; 36 or 48 months with 0.5% autopay discount.",
                "loan_amount_text": "$2,000-$30,000",
                "term_length_text": "12-60 months",
            },
        )

        self.assertTrue(quality.complete)
        self.assertEqual(quality.satisfied_fields[0], "interest_rate_summary")

    def test_rate_marketing_copy_without_percentage_does_not_satisfy_contract(self) -> None:
        quality = comparison_quality(
            product_type="personal-loan",
            expected_fields=[],
            candidate_payload={
                "interest_rate_summary": "Competitive rates are available.",
                "loan_amount_text": "Up to $30,000",
                "term_length_text": "Up to 60 months",
            },
        )

        self.assertFalse(quality.complete)
        self.assertEqual(quality.missing_fields, ("interest_rate",))

    def test_new_dynamic_type_fails_closed_without_rate_plus_decision_contract(self) -> None:
        quality = comparison_quality(
            product_type="equipment-finance",
            expected_fields=["product_name", "eligibility_text"],
            candidate_payload={"eligibility_text": "Businesses only"},
        )

        self.assertFalse(quality.contract_defined)
        self.assertFalse(quality.complete)

    def test_new_dynamic_type_can_pass_with_registered_rate_plus_decision_contract(self) -> None:
        quality = comparison_quality(
            product_type="equipment-finance",
            expected_fields=["product_name", "annual_interest_rate", "maximum_amount_text"],
            candidate_payload={
                "annual_interest_rate": 8.25,
                "maximum_amount_text": "Up to $100,000",
            },
        )

        self.assertTrue(quality.contract_defined)
        self.assertTrue(quality.complete)

    def test_repair_fields_include_missing_core_fields_even_when_copy_is_populated(self) -> None:
        fields = dynamic_repair_fields(
            product_type="mortgage",
            expected_fields=["product_name", "mortgage_rate", "rate_type", "term_length_text", "payment_frequency"],
            candidate_payload={"payment_frequency": "Monthly"},
        )

        self.assertEqual(
            fields,
            ["mortgage_rate", "rate_type", "term_length_text"],
        )

    def test_known_collection_contract_drops_optional_legacy_fields(self) -> None:
        fields = collection_fields_for_product_type(
            product_type="savings",
            expected_fields=[
                "product_name",
                "standard_rate",
                "monthly_fee",
                "minimum_balance",
                "eligibility_text",
                "application_method",
            ],
        )

        self.assertEqual(
            fields,
            (
                "product_name",
                "standard_rate",
                "base_12_month_rate",
                "public_display_rate",
                "monthly_fee",
                "public_display_fee",
                "minimum_balance",
            ),
        )

    def test_deposit_contracts_require_their_comparison_essentials(self) -> None:
        chequing = comparison_quality(
            product_type="chequing",
            expected_fields=[],
            candidate_payload={"monthly_fee": 0, "minimum_balance": 0, "included_transactions": 25},
        )
        savings = comparison_quality(
            product_type="savings",
            expected_fields=[],
            candidate_payload={"standard_rate": 2.8, "monthly_fee": 0, "minimum_balance": 0},
        )
        gic = comparison_quality(
            product_type="gic",
            expected_fields=[],
            candidate_payload={
                "term_rate_table": [{"term_label": "1 year", "rate": 3.5}],
                "minimum_deposit": 500,
                "non_redeemable_flag": True,
            },
        )

        self.assertTrue(chequing.complete)
        self.assertTrue(savings.complete)
        self.assertTrue(gic.complete)

    def test_line_of_credit_requires_security_fact(self) -> None:
        quality = comparison_quality(
            product_type="line-of-credit",
            expected_fields=[],
            candidate_payload={"interest_rate_summary": "Prime + 2.0%", "credit_limit_text": "$5,000-$50,000"},
        )

        self.assertFalse(quality.complete)
        self.assertEqual(quality.missing_fields, ("secured_flag",))

    def test_us_checking_replaces_transaction_count_with_conditional_fee_waiver(self) -> None:
        no_fee = comparison_quality(
            country_code="US",
            product_type="chequing",
            expected_fields=[],
            candidate_payload={"monthly_fee": 0, "minimum_deposit": 25},
        )
        positive_fee_without_waiver = comparison_quality(
            country_code="US",
            product_type="chequing",
            expected_fields=[],
            candidate_payload={"monthly_fee": 12, "minimum_balance": 1500},
        )
        positive_fee_with_waiver = comparison_quality(
            country_code="US",
            product_type="chequing",
            expected_fields=[],
            candidate_payload={
                "monthly_fee": 12,
                "minimum_balance": 1500,
                "fee_waiver_condition": "Waived with $1,500 daily balance or qualifying direct deposit.",
            },
        )

        self.assertTrue(no_fee.complete)
        self.assertNotIn("included_transactions", no_fee.assessed_fields)
        self.assertFalse(positive_fee_without_waiver.complete)
        self.assertEqual(positive_fee_without_waiver.missing_fields, ("fee_waiver_condition",))
        self.assertTrue(positive_fee_with_waiver.complete)

    def test_us_savings_requires_positive_fee_waiver_and_collects_conditional_rate_summary(self) -> None:
        without_waiver = comparison_quality(
            country_code="US",
            product_type="savings",
            expected_fields=[],
            candidate_payload={"standard_rate": 3.2, "monthly_fee": 12, "minimum_balance": 25000},
        )
        with_waiver = comparison_quality(
            country_code="US",
            product_type="savings",
            expected_fields=[],
            candidate_payload={
                "standard_rate": 3.2,
                "monthly_fee": 12,
                "minimum_balance": 25000,
                "fee_waiver_condition": "Waived with a $3,500 minimum daily balance.",
            },
        )
        fields = collection_fields_for_product_type(country_code="US", product_type="savings")

        self.assertFalse(without_waiver.complete)
        self.assertEqual(without_waiver.missing_fields, ("fee_waiver_condition",))
        self.assertTrue(with_waiver.complete)
        self.assertIn("interest_rate_summary", fields)

    def test_us_cd_uses_early_withdrawal_penalty_not_redeemability(self) -> None:
        quality = comparison_quality(
            country_code="US",
            product_type="gic",
            expected_fields=[],
            candidate_payload={
                "term_rate_table": [{"term_label": "12 months", "rate": 4.1}],
                "minimum_deposit": 500,
                "early_withdrawal_penalty": "90 days of interest for terms of 12 months or less.",
            },
        )

        self.assertTrue(quality.complete)
        self.assertNotIn("redeemable_flag", quality.assessed_fields)

    def test_us_mortgage_requires_qualified_summary_not_bare_scalar(self) -> None:
        scalar_only = comparison_quality(
            country_code="US",
            product_type="mortgage",
            expected_fields=[],
            candidate_payload={"mortgage_rate": 6.25, "rate_type": "Fixed", "term_length_text": "30 years"},
        )
        qualified = comparison_quality(
            country_code="US",
            product_type="mortgage",
            expected_fields=[],
            candidate_payload={
                "interest_rate_summary": "6.25% rate / 6.41% APR for a 30-year fixed loan, 75% LTV, 1 point, ZIP 10001.",
                "rate_type": "Fixed",
                "term_length_text": "30 years",
            },
        )

        self.assertFalse(scalar_only.complete)
        self.assertEqual(scalar_only.missing_fields, ("interest_rate_summary",))
        self.assertTrue(qualified.complete)

    def test_us_mortgage_rejects_masked_rate_template_with_down_payment_percent(self) -> None:
        quality = comparison_quality(
            country_code="US",
            product_type="mortgage",
            expected_fields=[],
            candidate_payload={
                "interest_rate_summary": (
                    "Down payment 5% or more. Input ZIP code. Rate X.XXX%; APR X.XXX%; "
                    "monthly payment $XXXX."
                ),
                "rate_type": "Fixed rate",
                "term_length_text": "30 years",
            },
        )

        self.assertFalse(quality.complete)
        self.assertEqual(quality.missing_fields, ("interest_rate_summary",))

    def test_unconfigured_explicit_country_does_not_inherit_canada_contract(self) -> None:
        quality = comparison_quality(
            country_code="GB",
            product_type="chequing",
            expected_fields=["monthly_fee", "minimum_balance", "included_transactions"],
            candidate_payload={
                "monthly_fee": 0,
                "minimum_balance": 0,
                "included_transactions": 20,
            },
        )

        self.assertTrue(quality.applicable)
        self.assertFalse(quality.contract_defined)
        self.assertFalse(quality.complete)

    def test_us_collection_fields_are_profile_specific(self) -> None:
        checking_fields = collection_fields_for_product_type(
            country_code="US",
            product_type="chequing",
        )
        cd_fields = collection_fields_for_product_type(
            country_code="US",
            product_type="gic",
        )

        self.assertIn("fee_waiver_condition", checking_fields)
        self.assertNotIn("included_transactions", checking_fields)
        self.assertIn("early_withdrawal_penalty", cd_fields)
        self.assertNotIn("redeemable_flag", cd_fields)

    def test_unconfigured_market_metadata_keeps_requested_identity_and_fails_closed(self) -> None:
        metadata = market_profile_metadata(
            country_code="GB",
            product_type="credit-card",
        )

        self.assertEqual(metadata["market_profile_key"], "GB:credit-card")
        self.assertEqual(metadata["market_profile_resolution"], "dynamic_fail_closed")

    def test_us_cards_and_lines_of_credit_are_explicit_market_profiles(self) -> None:
        for product_type in ("credit-card", "line-of-credit"):
            metadata = market_profile_metadata(
                country_code="US",
                product_type=product_type,
            )

            self.assertEqual(metadata["market_profile_key"], f"US:{product_type}")
            self.assertEqual(metadata["market_profile_resolution"], "country_override")


if __name__ == "__main__":
    unittest.main()
