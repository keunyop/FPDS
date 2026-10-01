import unittest
from copy import deepcopy
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate, acceptance_receipt_valid, RECEIPT_KEY, country_currency_fallback
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_market_profile import country_product_profile

class CountryCurrencyPolicyTests(unittest.TestCase):
    def undisclosed(self, country):
        row, meta, evidence = candidate_fixture()
        row['country_code'] = country
        row['currency'] = 'XXX'
        for m in row['field_mapping_metadata'].values():
            m['official_evidence_quote'] = m['official_evidence_quote'].replace(' in Canadian dollars','').replace(' in CAD','').replace(' CAD','')
        for e in evidence:
            e['evidence_excerpt'] = e['evidence_excerpt'].replace(' in Canadian dollars','').replace(' in CAD','').replace(' CAD','')
        return row,meta,evidence

    def test_country_defaults_and_private_provenance(self):
        for country,currency in [('CA','CAD'),('US','USD')]:
            with self.subTest(country=country):
                row,meta,evidence=self.undisclosed(country)
                cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
                self.assertTrue(r['accepted'], r)
                self.assertEqual(cleaned['currency'],currency)
                self.assertEqual(r['currency_basis'],'country_default')
                self.assertEqual(cleaned['field_mapping_metadata']['currency']['extraction_method'],'country_default')
                self.assertNotIn('official_evidence_quote',cleaned['field_mapping_metadata']['currency'])
                self.assertTrue(acceptance_receipt_valid(cleaned))
                self.assertEqual(row['currency'],'XXX')

    def test_foreign_currency_and_conflicts_never_become_defaults(self):
        for marker in ['USD','US$','CAD and USD','EUR','GBP','HKD','JPY','AUD','NZD','CNY','CHF','SGD','foreign currency','multi-currency','currency: MXN']:
            with self.subTest(marker=marker):
                row,meta,evidence=self.undisclosed('CA')
                evidence.append({'evidence_chunk_id':'foreign','source_url':'https://bank.example/savings','evidence_excerpt':marker})
                cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
                self.assertFalse(r['accepted'])
                self.assertEqual(cleaned['currency'],'XXX')
                self.assertEqual(r['currency_basis'],'unverified')
        self.assertIsNone(country_currency_fallback({'country_code':'CA','product_name':'USD Account'},[]))

    def test_explicit_currency_preserved_even_outside_country(self):
        row,meta,evidence=candidate_fixture()
        row['country_code']='US'
        cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertTrue(r['accepted'],r)
        self.assertEqual(cleaned['currency'],'CAD')
        self.assertEqual(r['currency_basis'],'official_evidence')

    def test_default_does_not_prove_missing_fields_or_unsupported_market(self):
        for country in ['CA','US','XX']:
            row,meta,evidence=self.undisclosed(country)
            row['field_mapping_metadata'].pop('standard_rate')
            cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
            self.assertFalse(r['accepted'])
            self.assertNotIn('standard_rate',cleaned['candidate_payload'])
        self.assertIsNone(country_currency_fallback({'country_code':'XX'},[]))

    def test_previous_strict_receipts_and_tampering(self):
        row,meta,evidence=candidate_fixture()
        cleaned,r=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        cleaned['candidate_payload'][RECEIPT_KEY]['version']='collection-accuracy-2026-09-30'
        self.assertTrue(acceptance_receipt_valid(cleaned))
        cleaned['currency']='USD'
        self.assertFalse(acceptance_receipt_valid(cleaned))

    def test_core_requirements_and_optional_collection(self):
        fixtures={
            'chequing':({'monthly_fee':0},'minimum_balance'),
            'savings':({'standard_rate':2.5,'monthly_fee':0},'minimum_balance'),
            'gic':({'standard_rate':3.5,'term_length_text':'1 year'},'minimum_deposit'),
            'credit-card':({'annual_fee':29,'purchase_interest_rate':13.99},None),
            'mortgage':({'interest_rate_summary':'Annual rate 4.5%','rate_type':'fixed','term_length_text':'5 years'},None),
            'personal-loan':({'interest_rate_summary':'Annual rate 8%','term_length_text':'2 years'},'loan_amount_text'),
            'line-of-credit':({'interest_rate_summary':'Annual rate 8%'},'credit_limit_text'),
        }
        for country in ['CA','US']:
            for kind,(payload,optional) in fixtures.items():
                with self.subTest(country=country,kind=kind):
                    q=comparison_quality(country_code=country,product_type=kind,expected_fields=[],candidate_payload=payload)
                    self.assertTrue(q.complete,q)
                    self.assertFalse(comparison_quality(country_code=country,product_type=kind,expected_fields=[],candidate_payload={}).complete)
                    if optional:
                        profile=country_product_profile(country_code=country,product_type=kind)
                        self.assertIn(optional,profile.collection_fields)
                        self.assertNotIn(optional,q.assessed_fields)

    def test_normalization_gic_does_not_reintroduce_optional_deposit_gate(self):
        from worker.pipeline.fpds_normalization.service import _compute_validation_issue_codes
        args=dict(product_type='gic',product_type_family='gic',subtype_code='other',product_name='Example GIC',country_code='CA',bank_code='EXAMPLE',product_family='deposit',source_language='en',currency='CAD',evidence_links=[])
        payload={'standard_rate':3.0,'term_length_text':'1 year','minimum_balance':100}
        issues=_compute_validation_issue_codes(**args,candidate_payload=payload)
        self.assertNotIn('required_field_missing',issues)
        self.assertNotIn('inconsistent_cross_field_logic',issues)
        for missing in ['standard_rate','term_length_text']:
            incomplete=dict(payload);incomplete.pop(missing)
            self.assertIn('required_field_missing',_compute_validation_issue_codes(**args,candidate_payload=incomplete))
