from __future__ import annotations

from datetime import date
from decimal import Decimal
import unittest

from worker.pipeline.fpds_rate_safety import (
    advertised_promotional_total_rate,
    canonical_deposit_rate_suppression_reason,
    contains_explicit_rate_percentage,
    contains_unresolved_financial_placeholder,
)


class CanonicalDepositRateSafetyTests(unittest.TestCase):
    def test_masked_financial_template_is_not_an_explicit_rate(self) -> None:
        value = "Down payment 5%. Rate X.XXX%; APR X.XXX%; Monthly Payment $XXXX."

        self.assertTrue(contains_unresolved_financial_placeholder(value))
        self.assertFalse(contains_explicit_rate_percentage(value))
        self.assertTrue(contains_explicit_rate_percentage("6.25% rate / 6.41% APR"))

    def test_prime_rate_is_not_a_canonical_deposit_rate(self) -> None:
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(
                value="4.45",
                context="Tangerine Prime Rate: 4.45% Effective February 23, 2026 Savings Accounts",
            ),
            "non_annual_return_context",
        )

    def test_foreign_purchase_markup_is_not_a_savings_rate(self) -> None:
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(
                value="3.5",
                context=(
                    "Purchases with TD Access Card outside Canada. For foreign purchases, we add 3.5% "
                    "to your total after converting to Canadian dollars at the rate set by Visa International."
                ),
            ),
            "non_annual_return_context",
        )

    def test_atm_assessment_percentage_is_not_a_deposit_rate(self) -> None:
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(
                value="3.0",
                context=(
                    "3% International Point of Sale & ATM assessment fee per transaction. "
                    "Non-Truist ATMs may charge additional fees."
                ),
            ),
            "non_annual_return_context",
        )

    def test_prime_rate_is_not_a_canonical_deposit_rate(self) -> None:
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(
                value="4.45",
                context="Tangerine Prime Rate: 4.45% Effective February 23, 2026 Savings Accounts",
            ),
            "non_annual_return_context",
        )

    def test_extracts_only_explicit_advertised_promotional_total(self) -> None:
        self.assertEqual(
            advertised_promotional_total_rate(
                "Special offer: You can earn up to 5.00% for the first 3 months."
            ),
            5,
        )
        self.assertIsNone(
            advertised_promotional_total_rate(
                "Earn an extra promotional rate of 2.80% on top of the regular tiered rate."
            )
        )
        self.assertEqual(
            advertised_promotional_total_rate(
                "Earn a 0.50% savings interest rate or a promotional rate of 4.75%."
            ),
            Decimal("4.75"),
        )
        self.assertEqual(
            advertised_promotional_total_rate(
                "Earn 4.50% for 5 months. New Client offer terms apply."
            ),
            Decimal("4.50"),
        )

    def test_rejects_mutual_fund_fee_and_historical_performance_as_deposit_rates(self) -> None:
        cases = (
            (
                "0.50",
                "Mutual funds are not guaranteed. The annual management fee is 0.50% of each Global ETF Portfolio.",
            ),
            (
                "8.43",
                "If you invested in our Balanced Growth Core Portfolio 10 years ago, the annual average compound return was 8.43% after fees.",
            ),
            (
                "0.55",
                "The fee is 0.55% of each Tangerine Socially Responsible Global Portfolio. "
                "The fixed administration fee is 0.15% of each Portfolio's value.",
            ),
        )
        for value, context in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    canonical_deposit_rate_suppression_reason(value=value, context=context),
                    "non_annual_return_context",
                )

    def test_overdraft_interest_is_not_a_savings_rate(self) -> None:
        context = (
            "Payment Coverage Fee: $5 fee plus 21% annual interest on overdraft balance "
            "if the bank approves a payment higher than the available balance."
        )

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="21", context=context),
            "non_annual_return_context",
        )

    def test_redemption_percentage_of_original_investment_is_not_a_rate(self) -> None:
        context = "Redemption is permitted up to 33% or 20% of the original investment amount on the anniversary date."

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="20", context=context),
            "non_annual_return_context",
        )

    def test_plausible_annual_rate_remains_allowed(self) -> None:
        for context in (
            "3 year annual interest rate 3.10%",
            "The annual interest rate is 3.10% and is based on a benchmark rate set by the bank.",
        ):
            with self.subTest(context=context):
                self.assertIsNone(
                    canonical_deposit_rate_suppression_reason(value="3.10", context=context),
                )

    def test_double_digit_deposit_rate_requires_review_without_direct_context(self) -> None:
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="10"),
            "implausible_annual_deposit_rate",
        )
        self.assertIsNone(canonical_deposit_rate_suppression_reason(value="9.99"))

    def test_corporate_ownership_percentage_is_not_a_deposit_rate(self) -> None:
        context = "List each person who owns or controls 25% or more of the voting shares of the corporation."

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="25", context=context),
            "non_annual_return_context",
        )

    def test_cashback_and_mortgage_prepayment_percentages_are_not_rates(self) -> None:
        for context in (
            "Earn 3% cash back on eligible purchases.",
            "Prepay up to 20% of the original mortgage amount each year.",
            "A minimum 20% home equity position is required.",
        ):
            with self.subTest(context=context):
                self.assertEqual(
                    canonical_deposit_rate_suppression_reason(value="20" if "20%" in context else "3", context=context),
                    "non_annual_return_context",
                )

    def test_fnbc_prepayment_option_and_allowance_percentages_are_not_rates(self) -> None:
        for context in (
            "Choose a 20% prepayment option on your FNBC mortgage.",
            "The mortgage includes a prepayment allowance of 15% each year.",
        ):
            with self.subTest(context=context):
                self.assertEqual(
                    canonical_deposit_rate_suppression_reason(
                        value="20" if "20%" in context else "15",
                        context=context,
                    ),
                    "non_annual_return_context",
                )

    def test_operational_percentages_and_multi_year_returns_are_not_deposit_rates(self) -> None:
        cases = (
            ("20", "Access to 20% of your principal annually without penalty."),
            ("2.5", "A 2.5% foreign currency conversion fee applies."),
            ("2.5", "A 2.5% ATM convenience fee applies outside Canada."),
            (
                "2.5",
                "Purchases are converted to Canadian dollars at an exchange rate 2.5% over the Interbank Spot Rate.",
            ),
            ("20", "The hypothetical total return over the five-year term is 20%."),
            (
                "20",
                "Scenario 1: Market is Up. If the index moves from 100 to 120 over the 5-year term, "
                "you receive your principal plus a 20% return on your investment.",
            ),
            ("0.70", "This calculator provides estimates only and should not be relied upon. Estimated rate 0.70%."),
            (
                "10",
                "The maximum percentage of a Fund's net asset value invested in Underlying Investments is 10%.",
            ),
        )
        for value, context in cases:
            with self.subTest(context=context):
                self.assertEqual(
                    canonical_deposit_rate_suppression_reason(value=value, context=context),
                    "non_annual_return_context",
                )

    def test_survey_percentages_are_not_deposit_rates(self) -> None:
        context = (
            "Which of the following Cyber Security issues do you struggle with the most? "
            "Remembering passwords (45.65%). Recognizing phishing attempts (8.62%). "
            "Keeping devices secure from hackers (20.02%)."
        )
        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="20.02", context=context),
            "non_annual_return_context",
        )

    def test_expired_promotional_offer_is_not_a_current_rate(self) -> None:
        context = (
            "Special rate 6.00% for a 1 Year GIC. "
            "Terms and conditions apply. Offer valid from Nov 1 to Nov 30, 2023."
        )

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(
                value="6.00",
                context=context,
                reference_date=date(2026, 7, 19),
            ),
            "expired_promotional_offer",
        )

    def test_offer_that_has_not_ended_remains_eligible(self) -> None:
        self.assertIsNone(
            canonical_deposit_rate_suppression_reason(
                value="4.25",
                context="Special interest rate 4.25%. Offer valid until December 31, 2026.",
                reference_date=date(2026, 7, 19),
            )
        )


if __name__ == "__main__":
    unittest.main()
