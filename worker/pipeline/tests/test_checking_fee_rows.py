import unittest
from copy import deepcopy

from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate, acceptance_receipt_valid
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

EVERY_DAY = """Account Fees
Monthly Fee
$11.95
Monthly Fee for Seniors (60 or older)
$8.20
Minimum monthly balance for fee rebate 1
$3,000
Transactions included per month 2
25
Additional transaction fee
$1.25 each
Interac e-Transfer®
Free
Non-TD ATM Fee (in Canada) 4
$2.00 each
Foreign ATM Fee (in U.S., Mexico) 4
$3.00 each
Foreign ATM Fee (in any other foreign country ) 4
$5.00 each
Paper Statement
$2.00 per month"""
MINIMUM = """Account Fees
Monthly Fee 1
$3.95
Transactions included per month 2 , 3
12
Additional transaction Fee
$1.25 each
Interac e-Transfer® Send Money Fee: 5
No Fee
Interac e-Transfer® Request Money Fee (Up to $100) 5
$0.50 each
Interac e-Transfer® Request Money Fee (Over $100) 5
$1.00 each
Non-TD ATM Fees (in Canada) 6
$2.00 each
Foreign ATM Fee (in U.S., Mexico) 6
$3.00 each
Foreign ATM Fee (in any other foreign country) 6
$5.00 each"""

class CheckingFeeRowTests(unittest.TestCase):
    def test_complete_official_fee_tables(self):
        for quote, count in [(EVERY_DAY, 25), (MINIMUM, 12), (MINIMUM.replace("\n", "\r\n"), 12)]:
            with self.subTest(count=count):
                self.assertTrue(quote_supports_value("included_transactions", count, quote))
                self.assertTrue(quote_supports_value("additional_transaction_fee", 1.25, quote))
                self.assertFalse(quote_supports_value("included_transactions", 2, quote))
                self.assertFalse(quote_supports_value("additional_transaction_fee", 2, quote))
                self.assertFalse(quote_supports_value("transaction_fee", 1.25, quote))

    def test_transit_and_special_channels_never_prove_ordinary_unlimited(self):
        for quote in ["Unlimited public transit transactions", "Public transit: Unlimited transactions",
                      "Unlimited transactions for public transit", "Unlimited transactions at ATMs",
                      "Transactions included per month 2\r\n12\r\nUnlimited transactions", "Unlimited ATM transactions",
                      "Unlimited wire transactions", "Unlimited e-transfer transactions", "Not unlimited transactions",
                      "25 included transactions plus unlimited public transit transactions",
                      "12 transactions including up to 2 full-serve transactions plus unlimited public transit transactions"]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("unlimited_transactions_flag", True, quote))
        for quote in ["Unlimited transactions", "Unlimited debit transactions", "Unlimited everyday banking transactions"]:
            self.assertTrue(quote_supports_value("unlimited_transactions_flag", True, quote))

    def test_count_rows_fail_closed(self):
        for quote in ["Transactions included per month 2\nUp to 12", "Transactions included per month\n12 if you qualify",
                      "ATM Transactions included per month\n12", "Transactions included per month\n12 to 25",
                      "Transactions included per month\n12.5", "Transactions included per month\n-12",
                      "Transactions included per month\n12\nTransactions included per month\n25",
                      "Transactions included per month\n12\n25 included transactions",
                      "Transactions included per month\n12\nUnlimited transactions",
                      "Transactions included per month if you maintain $1000\n12"]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("included_transactions", 12, quote))

    def test_excess_rows_fail_closed(self):
        for quote in ["ATM additional transaction fee\n$1.25 each", "Additional transaction fee\n$1.25 each if you qualify",
                      "Additional transaction fee\n$1.25 to $2 each", "Additional transaction fee\n$2 each\nMonthly fee\n$1.25",
                      "Additional transaction fee\n$1.25 each\nAdditional transaction fee\n$2 each",
                      "Additional transaction fee\n$1.25 each\nUnlimited ordinary transactions"]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("additional_transaction_fee", 1.25, quote))

    def test_complete_rows_pass_receipt_and_missing_cost_does_not(self):
        row, meta, _ = candidate_fixture()
        url = "https://bank.example/checking"
        payload = {"product_name": "Example Checking", "monthly_fee": 3.95,
                   "included_transactions": 12, "additional_transaction_fee": 1.25}
        quotes = {"product_name": "Example Checking in CAD", "monthly_fee": "Monthly Fee 1\n$3.95",
                  "included_transactions": "Transactions included per month 2 , 3\n12",
                  "additional_transaction_fee": "Additional transaction Fee\n$1.25 each"}
        row.update(product_type="chequing", product_name=payload["product_name"], candidate_payload=payload)
        row["field_mapping_metadata"] = {name: {"normalized_value": value, "evidence_chunk_id": name,
            "official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match",
            "official_evidence_quote": quotes[name], "official_web_sources": [{"url": url}]}
            for name, value in payload.items()}
        evidence = [{"evidence_chunk_id": name, "source_url": url,
                     "evidence_excerpt": quotes[name] if name == "product_name" else MINIMUM} for name in payload]
        meta.update(normalized_source_url=url, expected_fields=list(payload))
        cleaned, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"], receipt)
        self.assertTrue(acceptance_receipt_valid(cleaned))
        changed = deepcopy(evidence)
        changed[-1]["evidence_excerpt"] = MINIMUM.replace("$1.25 each", "$2 each")
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=changed)
        self.assertFalse(receipt["accepted"], receipt)
