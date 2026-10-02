import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture

class ComparisonRateTests(unittest.TestCase):
    def test_national_and_other_product_reference_rates_are_rejected(self):
        for q in ["The national average for this type of account is 0.37% APY, based on rates published in the FDIC Monthly National Rates and Rate Caps.", "Our APY is more than 5x the national average of 0.37% APY.", "Industry average savings rate: 0.37% APY.", "Competitor savings account interest rate: 0.37% APY."]:
            with self.subTest(q=q): self.assertFalse(quote_supports_value('standard_rate',0.37,q))
    def test_own_current_rate_and_example_boundaries(self):
        self.assertTrue(quote_supports_value('standard_rate',3.5,'Current savings account interest rate 3.5% APY.'))
        self.assertFalse(quote_supports_value('interest_rate',35.65,'Example on how to calculate payments. If you borrow $400, your annual percentage rate will be 35.65%.'))
    def test_tightly_quoted_reference_rate_cannot_bypass_full_context(self):
        row,metadata,evidence=candidate_fixture()
        row['product_type']='savings';row['candidate_payload']={'product_name':row['product_name'],'standard_rate':0.37,'monthly_fee':0}
        row['field_mapping_metadata']['standard_rate']={**row['field_mapping_metadata']['monthly_fee'],'normalized_value':0.37,'official_evidence_quote':'0.37% APY','evidence_chunk_id':'standard_rate'}
        evidence.append({'evidence_chunk_id':'standard_rate','source_url':evidence[0]['source_url'],'evidence_excerpt':'The national average for this type of account is 0.37% APY, based on FDIC rates.'})
        clean,receipt=sanitize_candidate(row,source_metadata=metadata,evidence=evidence)
        self.assertFalse(receipt['accepted']);self.assertNotIn('standard_rate',clean['candidate_payload'])
