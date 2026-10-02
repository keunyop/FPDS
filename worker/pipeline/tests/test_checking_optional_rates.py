"""Checking rates are opportunistic facts, never publication prerequisites."""
import json
from pathlib import Path
from dataclasses import asdict
import unittest
from unittest.mock import patch
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate, acceptance_receipt_valid, quote_supports_value
from worker.pipeline.fpds_extraction.service import _resolve_field_names
from worker.pipeline.fpds_market_profile import country_product_profile
from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
from worker.pipeline.fpds_normalization.service import _normalize_candidate
from worker.pipeline.tests.test_optional_collection import context, extract, URL

RATE_FIELDS = {'standard_rate', 'public_display_rate', 'interest_rate_summary',
    'interest_calculation_method', 'interest_payment_frequency', 'tiered_rate_flag',
    'tier_definition_text', 'promotional_rate', 'promotional_period_text', 'introductory_rate_flag'}

def facts(name='Example Checking', currency='CAD'):
    return {'product_name': (name, name), 'currency': (currency, 'Currency: '+currency),
        'monthly_fee': (0, 'No monthly fee.'),
        'unlimited_transactions_flag': (True, 'Unlimited day-to-day transactions.')}

def normalized(ctx, fields, chunks):
    item = NormalizationInput('source', 'source', 'snapshot', 'parsed', 'extract', 'private/key', None,
        'EXAMPLE', ctx.country_code, 'html', 'en', ctx.source_metadata,
        {'product_type': 'chequing', 'product_family': 'deposit'},
        [NormalizationExtractedField(**asdict(f)) for f in fields],
        [NormalizationEvidenceLink(f.field_name, str(f.candidate_value), f.evidence_chunk_id,
            f.evidence_text_excerpt, 'source', 'snapshot', .99, 'extract', f.anchor_type,
            f.anchor_value, f.page_no, f.chunk_index) for f in fields], [], normalized_source_url=URL)
    with patch('worker.pipeline.fpds_normalization.service.llm_provider_configured', return_value=False):
        record, _, _, _ = _normalize_candidate(run_id='run', candidate_id='candidate',
            normalization_model_execution_id='normalize', item=item)
    evidence = [{'evidence_chunk_id': c.evidence_chunk_id, 'evidence_excerpt': c.evidence_excerpt,
                 'source_url': URL} for c in chunks]
    return sanitize_candidate(record, source_metadata=ctx.source_metadata, evidence=evidence)

class CheckingOptionalRateTests(unittest.TestCase):
    def test_profiles_request_rates_as_optional_in_both_markets(self):
        for country in ('CA', 'US'):
            with self.subTest(country=country):
                profile = country_product_profile(country_code=country, product_type='chequing')
                self.assertTrue(RATE_FIELDS <= set(profile.supplemental_fields))
                _, call, _ = extract(context('chequing', country), {})
                request = call.call_args.kwargs['payload']
                self.assertTrue(RATE_FIELDS <= set(request['supplemental_fields']))
                self.assertFalse(RATE_FIELDS & set(request['required_comparison_fields']))

    def test_retrieval_uses_current_profile_with_old_registry_fields(self):
        for country in ('CA', 'US'):
            for product_type in ('chequing', 'savings', 'gic', 'credit-card', 'mortgage', 'personal-loan', 'line-of-credit'):
                with self.subTest(country=country, product_type=product_type):
                    selected = _resolve_field_names(context=context(product_type, country),
                        override_field_names=None, default_fields=('product_name',))
                    profile = country_product_profile(country_code=country, product_type=product_type)
                    self.assertTrue(set(profile.collection_fields) <= set(selected))

    def test_explicit_override_remains_bounded(self):
        self.assertEqual(_resolve_field_names(context=context('chequing'),
            override_field_names=['monthly_fee'], default_fields=('product_name',)), ['monthly_fee'])

    def test_saved_alterna_rate_and_other_bank_apy_survive_normalization(self):
        # Exact public wording present in the 2026-10-02 saved Alterna detail.
        for country, name, currency, rate, quote in (
            ('CA', 'No-Fee eChequing Account', 'CAD', .05, '0.05%* Annual Interest Rate.'),
            ('US', 'Example Interest Checking', 'USD', 1.25, 'Annual percentage yield (APY): 1.25%.'),
            ('CA', 'Example Zero Interest Checking', 'CAD', 0, '0% Annual Interest Rate.'),
        ):
            with self.subTest(country=country):
                ctx = context('chequing', country, expected=list(facts(name, currency)))
                (fields, _, _), _, chunks = extract(ctx, {**facts(name, currency), 'standard_rate': (rate, quote),
                    'interest_payment_frequency': ('paid monthly', 'Interest is paid monthly.')})
                clean, receipt = normalized(ctx, fields, chunks)
                self.assertTrue(receipt['accepted'], receipt)
                self.assertEqual(clean['candidate_payload'].get('standard_rate'), rate, receipt)
                self.assertEqual(clean['candidate_payload'].get('interest_payment_frequency'), 'paid monthly')
                self.assertTrue(acceptance_receipt_valid(clean))

    def test_full_saved_alterna_rate_context_survives_without_cropping(self):
        saved = json.loads((Path(__file__).parent / 'fixtures/checking_optional_rate_alterna.json').read_text(encoding='utf8'))
        ctx = context('chequing')
        (fields, _, _), _, chunks = extract(ctx, {**facts('No-Fee eChequing Account'), 'standard_rate': (.05, saved['excerpt'])},
            overrides={'standard_rate': {'evidence_quote': saved['rate_quote']}})
        clean, receipt = normalized(ctx, fields, chunks)
        self.assertTrue(receipt['accepted'], receipt)
        self.assertEqual(clean['candidate_payload'].get('standard_rate'), .05, receipt)

    def test_separate_insurance_limits_do_not_qualify_plain_deposit_rate(self):
        for insurance in (
            'Safe and secure - eligible deposits are insured up to the maximum amount through the Canada Deposit Insurance Corporation (CDIC)',
            'Deposits are insured up to $250,000 by the Federal Deposit Insurance Corporation (FDIC).',
        ):
            with self.subTest(insurance=insurance):
                self.assertTrue(quote_supports_value('standard_rate', .05, insurance+'\n0.05% Annual Interest Rate.'))
                self.assertTrue(quote_supports_value('public_display_rate', .05, insurance+'\nAnnual Interest Rate: 0.05%.'))

    def test_insurance_exception_never_removes_actual_rate_conditions(self):
        insurance = 'Eligible deposits are insured up to the maximum amount through the Canada Deposit Insurance Corporation (CDIC)'
        for suffix in (
            'Up to 0.05% Annual Interest Rate.',
            '0.05% Annual Interest Rate if you maintain a balance of $5,000.',
            '0.05% Annual Interest Rate.\nBonus interest applies when you qualify.',
            '0.05% Annual Interest Rate.\n0.10% Annual Interest Rate.',
            'Introductory 0.05% Annual Interest Rate.',
            '0.05% Annual Interest Rate for eligible deposits insured up to the maximum amount through the Canada Deposit Insurance Corporation (CDIC)',
        ):
            with self.subTest(suffix=suffix):
                self.assertFalse(quote_supports_value('standard_rate', .05, insurance+'\n'+suffix))
        for misleading_insurance in (
            insurance+' if you qualify',
            'Interest-bearing deposits earn up to the maximum amount through the Canada Deposit Insurance Corporation (CDIC)',
            insurance+' and earn up to 0.05%',
        ):
            with self.subTest(insurance=misleading_insurance):
                self.assertFalse(quote_supports_value('standard_rate', .05, misleading_insurance+'\n0.05% Annual Interest Rate.'))
        self.assertFalse(quote_supports_value('purchase_interest_rate', .05, insurance+'\n0.05% Annual Interest Rate for purchases.'))

    def test_missing_rate_does_not_become_zero_or_block_publication(self):
        ctx = context('chequing')
        (fields, notes, _), _, chunks = extract(ctx, facts())
        clean, receipt = normalized(ctx, fields, chunks)
        self.assertTrue(receipt['accepted'], receipt)
        self.assertNotIn('standard_rate', clean['candidate_payload'])
        self.assertNotIn('"standard_rate": "model_field_missing"', ' '.join(notes))

    def test_unsupported_rates_are_omitted_without_penalizing_publication(self):
        for quote in ('Interest rate: 0.05%.',
            'Annual interest rate up to 0.05% depending on your balance.',
            'Introductory annual interest rate 0.05% for the first 3 months.',
            'Annual overdraft interest rate 0.05%.', 'Savings account annual interest rate 0.05%.',
            'Annual interest rate 0.05% USD.'):
            with self.subTest(quote=quote):
                ctx = context('chequing')
                (fields, _, _), _, chunks = extract(ctx, {**facts(), 'standard_rate': (.05, quote)})
                clean, receipt = normalized(ctx, fields, chunks)
                self.assertTrue(receipt['accepted'], receipt)
                self.assertNotIn('standard_rate', clean['candidate_payload'], receipt)
                self.assertEqual(clean['candidate_payload']['monthly_fee'], 0)

    def test_companion_savings_payment_info_does_not_become_checking_information(self):
        ctx = context('chequing')
        quote = 'Canadian and U.S. dollar Savings Account at no additional cost. Interest is calculated on savings balances and paid monthly.'
        (fields, _, _), _, chunks = extract(ctx, {**facts(),
            'interest_payment_frequency': ('monthly', quote),
            'interest_calculation_method': ('Interest is calculated on savings balances and paid monthly.', quote)})
        clean, receipt = normalized(ctx, fields, chunks)
        self.assertTrue(receipt['accepted'], receipt)
        self.assertNotIn('interest_payment_frequency', clean['candidate_payload'])
        self.assertNotIn('interest_calculation_method', clean['candidate_payload'])

    def test_invented_quote_unconsulted_url_and_string_rate_are_omitted(self):
        for override in ({'evidence_quote': 'Annual interest rate 1.25%.'},
            {'sources': [{'url': 'https://other.example/rates'}]}, {'verified_value_json': '"0.05"'}):
            with self.subTest(override=override):
                ctx = context('chequing')
                (fields, _, _), _, chunks = extract(ctx, {**facts(), 'standard_rate': (.05, 'Annual interest rate 0.05%.')},
                    overrides={'standard_rate': override})
                clean, receipt = normalized(ctx, fields, chunks)
                self.assertTrue(receipt['accepted'], receipt)
                self.assertNotIn('standard_rate', clean['candidate_payload'])

if __name__ == '__main__':
    unittest.main()
