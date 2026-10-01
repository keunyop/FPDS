import json
import unittest
from api_service.public_products import _serialize_product_row
from tests.test_public_products import _projection_rows


class OptionalPublicFactsTests(unittest.TestCase):
    def test_only_approved_deposit_wording_is_public_with_native_types(self):
        row = next(row for row in _projection_rows() if row["product_type"] == "savings")
        row["refresh_metadata"]["deposit_conditions"] = {
            "interest_payment_frequency": "Interest is paid monthly.",
            "compounding_frequency": False, "payout_option": {"internal": "private"},
            "tier_definition_text": " ", "source_url": "private evidence", "notes": "operator note",
            "_collection_accuracy": {"accepted": True},
        }
        result = _serialize_product_row(row, locale="en")
        self.assertEqual(result["deposit_conditions"], {"interest_payment_frequency": "Interest is paid monthly."})
        self.assertNotIn("private", json.dumps(result["deposit_conditions"]))
        row["refresh_metadata"]["deposit_conditions"] = None
        self.assertEqual(_serialize_product_row(row, locale="en")["deposit_conditions"], {})
        row["product_type"] = "credit-card"
        row["refresh_metadata"]["deposit_conditions"] = {"payout_option": "Annual"}
        self.assertEqual(_serialize_product_row(row, locale="en")["deposit_conditions"], {})
