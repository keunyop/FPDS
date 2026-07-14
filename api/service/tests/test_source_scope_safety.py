from __future__ import annotations

import unittest

from api_service.source_catalog import _source_scope_exclusion_reason


class SourceScopeSafetyTests(unittest.TestCase):
    def test_personal_collection_excludes_business_audience_pages(self) -> None:
        cases = (
            "https://bank.example/en/small-business/account small business echequing",
            "https://bank.example/business-banking/accounts business banking",
            "https://bank.example/commercial-banking commercial banking",
            "https://bank.example/corporate-banking corporate banking",
        )

        for fingerprint in cases:
            with self.subTest(fingerprint=fingerprint):
                self.assertEqual(
                    _source_scope_exclusion_reason(product_type="chequing", fingerprint=fingerprint),
                    "non_consumer_business_page",
                )

    def test_consumer_product_page_remains_in_scope(self) -> None:
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="chequing",
                fingerprint="https://bank.example/en/personal/accounts/no-fee-echequing no fee echequing",
            )
        )


if __name__ == "__main__":
    unittest.main()
