from pathlib import Path
import gzip
import hashlib
import json
import unittest

from worker.country_defaults import default_currency_for_country
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, sanitize_candidate
from worker.pipeline.fpds_market_profile import country_product_profile
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture


class ExplicitMarketCurrencyTests(unittest.TestCase):
    def test_current_official_peso_capture(self):
        root = Path(__file__).parent / 'fixtures/explicit-market-currency'
        raw = gzip.decompress((root / 'bpi-checking.html.gz').read_bytes())
        manifest = json.loads((root / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['sha256'])
        parsed = parse_snapshot_bytes(body=raw, content_type='text/html')
        self.assertIn('Php', parsed.full_text)
        self.assertTrue(quote_supports_value('currency', 'PHP', 'Required initial deposit Php 10,000'))

    def test_explicit_currencies_keep_native_money_and_conflicts(self):
        for code, declaration in [('PHP', 'Philippine pesos'), ('PHP', 'PHP'), ('PHP', 'Php'), ('PHP', '\u20b1'), ('JPY', 'JPY'), ('SGD', 'SGD')]:
            with self.subTest(declaration=declaration):
                self.assertTrue(quote_supports_value('currency', code, declaration))
                self.assertTrue(quote_supports_value('monthly_fee', 300, f'Monthly account fee {declaration}300'))
        for quote in ['P300', 'pesos', 'PHP300 or USD5', 'https://example.com/INDEX.PHP/rates', '/INDEX.PHP/rates', 'https://example.com/prices?currency=PHP']:
            self.assertFalse(quote_supports_value('currency', 'PHP', quote))
        self.assertFalse(quote_supports_value('monthly_fee', 0, 'Monthly account fee PHP300 waived if balance is PHP10,000'))
        self.assertFalse(quote_supports_value('monthly_fee', 10000, 'Minimum balance PHP10,000. Monthly fee PHP300'))

    def test_ph_profiles_keep_conditional_essentials_and_no_default(self):
        self.assertIsNone(default_currency_for_country('PH'))
        for product in ['chequing', 'savings', 'gic', 'credit-card', 'mortgage', 'personal-loan', 'line-of-credit']:
            profile = country_product_profile(country_code='PH', product_type=product)
            self.assertIsNotNone(profile, product)
            self.assertEqual(profile.country_code, 'PH')
        self.assertIsNone(country_product_profile(country_code='ZZ', product_type='savings'))
        self.assertIn('loan_amount_text', country_product_profile(country_code='PH', product_type='personal-loan').supplemental_fields)
        self.assertIn('minimum_deposit', country_product_profile(country_code='PH', product_type='gic').supplemental_fields)

        quality = lambda product, payload: comparison_quality(country_code='PH', product_type=product, expected_fields=[], candidate_payload=payload)
        self.assertFalse(quality('chequing', {'monthly_fee':0, 'included_transactions':10}).complete)
        self.assertTrue(quality('chequing', {'monthly_fee':0, 'unlimited_transactions_flag':True}).complete)
        self.assertFalse(quality('gic', {'standard_rate':3, 'term_length_text':'30 days', 'redeemable_flag':True}).complete)
        self.assertFalse(quality('line-of-credit', {'interest_rate':5}).complete)
        self.assertTrue(quality('line-of-credit', {'interest_rate':5, 'secured_flag':False}).complete)

    def test_missing_currency_is_an_explicit_acquisition_gap(self):
        row, meta, evidence = candidate_fixture()
        row['country_code'] = 'PH'
        row['currency'] = 'XXX'
        for name in ['standard_rate', 'monthly_fee', 'minimum_balance']:
            quote = row['field_mapping_metadata'][name]['official_evidence_quote'].replace(' CAD', '')
            row['field_mapping_metadata'][name]['official_evidence_quote'] = quote
            next(e for e in evidence if e['evidence_chunk_id'] == name)['evidence_excerpt'] = quote
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertIn('currency', receipt['missing_fields'])
        self.assertFalse(receipt['accepted'])

    def test_unregistered_market_is_a_contract_failure(self):
        row, meta, evidence = candidate_fixture()
        row['country_code'] = 'ZZ'
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertIn('market_profile_not_registered', receipt['reasons'])
        self.assertFalse(receipt['accepted'])

    def test_owned_currency_records_reject_siblings_calculators_and_conflicts(self):
        from bs4 import BeautifulSoup
        from worker.native_currency_records import currency_records
        for code in ['PHP', 'CAD', 'JPY']:
            markup = f'<main><h1>Example Savings</h1><div><h6>Required initial deposit</h6><div><sup>{code}</sup><span>10,000</span></div></div></main>'
            parsed = parse_snapshot_bytes(body=markup.encode(), content_type='text/html')
            self.assertIn(code, parsed.full_text)
            self.assertTrue(currency_records(BeautifulSoup(markup, 'html.parser')))
            for bad in [markup.replace('<div><h6>', '<div data-account-name="Other Savings"><h6>', 1),
                        markup.replace('<sup>', '<input><sup>'),
                        markup.replace('10,000', '10,000 USD5'),
                        markup.replace('Required initial deposit', 'Example loan amount')]:
                self.assertEqual(currency_records(BeautifulSoup(bad, 'html.parser')), [], bad)

    def test_fee_plausibility_limits_are_in_their_own_currency(self):
        from worker.pipeline.fpds_money_safety import fee_plausibility_limit
        for currency in ['CAD', 'USD', 'XXX', None]:
            self.assertEqual(fee_plausibility_limit('annual_fee', currency), 2000)
            self.assertEqual(fee_plausibility_limit('monthly_fee', currency), 500)
        for currency in ['PHP', 'JPY', 'SGD']:
            self.assertIsNone(fee_plausibility_limit('annual_fee', currency))
            self.assertIsNone(fee_plausibility_limit('monthly_fee', currency))
        quality = comparison_quality(country_code='PH', product_type='credit-card', expected_fields=[], candidate_payload={'annual_fee':0, 'purchase_interest_rate_summary':'Purchase interest rate 3% per month'})
        self.assertFalse(quality.complete)

    def test_public_account_fee_alignment_keeps_currency_and_integer_zeros(self):
        from worker.pipeline.fpds_normalization.service import _align_public_display_fee, _is_direct_recurring_monthly_fee
        from worker.pipeline.fpds_normalization.models import NormalizationEvidenceLink
        from decimal import Decimal
        self.assertTrue(_is_direct_recurring_monthly_fee(value=Decimal('1000'), context='Monthly account fee PHP1000.'))
        for currency, amount in [('PHP', 1000), ('JPY', 10000), ('USD', 4), ('CAD', 500)]:
            quote = f'Monthly account fee {currency}{amount}.'
            link = NormalizationEvidenceLink(field_name='monthly_fee', candidate_value=str(amount), evidence_chunk_id='fee', evidence_text_excerpt=quote, source_document_id='source', source_snapshot_id='snapshot', citation_confidence=1, model_execution_id=None, anchor_type='section', anchor_value='fees', page_no=None, chunk_index=0)
            payload = {'monthly_fee':amount, 'public_display_fee':1}
            links = [link]
            _align_public_display_fee(product_type_family='chequing', currency=currency, candidate_payload=payload, field_mapping_metadata={}, normalized_values_for_links={}, evidence_links_for_output=links, runtime_notes=[])
            self.assertEqual(payload['public_display_fee'], 1 if currency == 'CAD' else amount)
            if currency != 'CAD':
                self.assertEqual(links[-1].evidence_chunk_id, 'fee')
        from decimal import Decimal
        for prefix in ['PHP', 'JPY', '$']:
            self.assertTrue(_is_direct_recurring_monthly_fee(value=Decimal('1000'), context=f'Monthly account fee {prefix}1000.'))
            self.assertFalse(_is_direct_recurring_monthly_fee(value=Decimal('1000'), context=f'Monthly account fee {prefix}1.'))
        self.assertFalse(_is_direct_recurring_monthly_fee(value=Decimal(0), context='Monthly fee PHP1000 waived if balance is PHP10000'))
