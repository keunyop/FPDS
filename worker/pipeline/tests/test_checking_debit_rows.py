import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value

ROW = "6 Debits legal disclaimer 1 / Month\nlegal disclaimer\n$1.25 each thereafter"

class CheckingDebitRowTests(unittest.TestCase):
    def test_explicit_monthly_debit_allowance_and_adjacent_excess_cost(self):
        for quote in [ROW, ROW.replace("\n", "\r\n"), ROW.replace(" legal disclaimer 1", "")]:
            self.assertTrue(quote_supports_value("included_transactions", 6, quote))
            self.assertTrue(quote_supports_value("additional_transaction_fee", 1.25, quote))
            self.assertFalse(quote_supports_value("included_transactions", 1, quote))
            self.assertFalse(quote_supports_value("included_transactions", True, quote))
            self.assertFalse(quote_supports_value("additional_transaction_fee", 6, quote))
            self.assertFalse(quote_supports_value("unlimited_transactions_flag", True, quote))
            self.assertFalse(quote_supports_value("transaction_fee", 1.25, quote))

    def test_ambiguous_conditional_channel_and_nonmonthly_rows_fail(self):
        for quote in [ROW + "\n" + ROW, ROW + "\n$2.00 each thereafter", ROW.replace("6 Debits", "6 to 12 Debits"), ROW.replace("Month", "Year"), "ATM withdrawals\n" + ROW, "Public transit\n" + ROW, ROW + " if a balance is maintained", ROW.replace("each thereafter", "each initially"), ROW.replace("6 Debits", "Unlimited Debits")]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("additional_transaction_fee", 1.25, quote))
        self.assertTrue(quote_supports_value("included_transactions", 6, ROW.split("$1.25")[0]))
        self.assertFalse(quote_supports_value("additional_transaction_fee", 1.25, "$1.25 each thereafter"))


    def test_normal_candidate_receipt_requires_both_allowance_and_excess_cost(self):
        from worker.pipeline.tests.test_collection_accuracy import candidate_fixture
        from worker.pipeline.fpds_collection_accuracy import sanitize_candidate, acceptance_receipt_valid
        row, metadata, _ = candidate_fixture()
        payload = {"product_name": "Example US Personal Account", "monthly_fee": 3, "included_transactions": 6, "additional_transaction_fee": 1.25}
        quotes = {"product_name": "Example US Personal Account in USD", "monthly_fee": "Monthly Fee $3/month USD", "included_transactions": ROW, "additional_transaction_fee": ROW}
        row.update(product_type="chequing", currency="USD", product_name=payload["product_name"], candidate_payload=payload)
        url = "https://bank.example/savings"
        row["field_mapping_metadata"] = {field: {"normalized_value": value, "evidence_chunk_id": field, "official_grounding_contract_version": "collection-official-grounding-v2", "official_verification_status": "match", "official_evidence_quote": quotes[field], "official_web_sources": [{"url": url}]} for field,value in payload.items()}
        evidence = [{"evidence_chunk_id": field, "evidence_excerpt": quote, "source_url": url} for field,quote in quotes.items()]
        clean, receipt = sanitize_candidate(row, source_metadata=metadata, evidence=evidence)
        self.assertTrue(receipt["accepted"], receipt)
        self.assertTrue(acceptance_receipt_valid(clean))
        row["candidate_payload"].pop("additional_transaction_fee")
        _, receipt = sanitize_candidate(row, source_metadata=metadata, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertIn("additional_transaction_fee", receipt["missing_fields"])
