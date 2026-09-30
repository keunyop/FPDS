import unittest
from scripts.maintenance.collection_accuracy_recovery import classify
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

class RecoveryDiagnosisTests(unittest.TestCase):
    def setUp(self):
        row, meta, evidence = candidate_fixture()
        self.product = {**row, "product_id": "product", "status": "inactive", "current_version_no": 2}
        self.candidate = {**row, "candidate_id": "candidate", "run_id": "original", "source_document_id": "source",
            "source_metadata": {**meta, "source_id": "registered"}, "normalized_source_url": "https://bank.example/savings"}
        self.evidence = {"candidate": evidence}
    def test_valid_old_evidence_still_requires_current_source_check(self):
        result = classify(self.product, [self.candidate], self.evidence)
        self.assertEqual(result["category"], "current_source_check_required")
    def test_foreign_product_cannot_supply_missing_proof(self):
        result = classify(self.product, [{**self.candidate, "product_name": "other"}], self.evidence)
        self.assertEqual(result["category"], "excluded_no_resolved_source")
    def test_missing_currency_requires_recollection(self):
        self.candidate["currency"] = "USD"; self.product["currency"] = "USD"
        result = classify(self.product, [self.candidate], self.evidence)
        self.assertEqual(result["category"], "recollection_required")
        self.assertIn("product_currency_unverified", result["best"]["assessment"]["reasons"])
    def test_active_product_is_never_selected_for_reactivation(self):
        self.product["status"] = "active"
        self.assertEqual(classify(self.product, [], {})["category"], "already_active")

if __name__ == "__main__": unittest.main()
