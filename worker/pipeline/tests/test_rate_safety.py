from __future__ import annotations

import unittest

from worker.pipeline.fpds_rate_safety import canonical_deposit_rate_suppression_reason


class CanonicalDepositRateSafetyTests(unittest.TestCase):
    def test_redemption_percentage_of_original_investment_is_not_a_rate(self) -> None:
        context = "Redemption is permitted up to 33% or 20% of the original investment amount on the anniversary date."

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="20", context=context),
            "non_annual_return_context",
        )

    def test_plausible_annual_rate_remains_allowed(self) -> None:
        self.assertIsNone(
            canonical_deposit_rate_suppression_reason(value="3.10", context="3 year annual interest rate 3.10%"),
        )

    def test_corporate_ownership_percentage_is_not_a_deposit_rate(self) -> None:
        context = "List each person who owns or controls 25% or more of the voting shares of the corporation."

        self.assertEqual(
            canonical_deposit_rate_suppression_reason(value="25", context=context),
            "implausible_annual_deposit_rate",
        )


if __name__ == "__main__":
    unittest.main()
