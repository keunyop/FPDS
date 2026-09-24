from copy import deepcopy
from decimal import Decimal
import unittest
from api_service.public_deposits import deposit_terms
from api_service.public_products import _serialize_product_row
from test_public_products import _projection_rows


def row(kind='savings', **metadata):
    return {'product_type': kind, 'product_family': 'deposit', 'currency': 'CAD',
            'product_name': 'Savings' if kind == 'savings' else 'Fixed GIC',
            'public_display_rate': 3, 'minimum_balance': 0, 'minimum_deposit': 500,
            'term_length_days': 365 if kind == 'gic' else None,
            'refresh_metadata': {'interest_calculation_method': 'Annual interest rate; simple daily calculation.',
                                 **({'term_length_text': '1 year', 'non_redeemable_flag': True} if kind == 'gic' else {}), **metadata}}


class DepositTermsTests(unittest.TestCase):
    def test_annual_savings_and_zero_rate_are_valid_without_mutation(self):
        value = row(); before = deepcopy(value)
        self.assertEqual(deposit_terms(value)['options'][0]['rate'], 3)
        self.assertEqual(value, before)
        value['public_display_rate'] = 0
        self.assertEqual(deposit_terms(value)['options'][0]['rate'], 0)

    def test_missing_basis_currency_and_legacy_values_fail_closed(self):
        for value, reason in ((row(interest_calculation_method=''), 'basis_unknown'),
                              ({**row(), 'currency': ''}, 'currency_unknown'),
                              ({**row(), 'public_display_rate': True}, 'rate_unclear'),
                              ({**row(), 'public_display_rate': Decimal('NaN')}, 'rate_unclear')):
            self.assertEqual(deposit_terms(value)['reason'], reason)
            self.assertEqual(deposit_terms(value)['options'], [])

    def test_market_linked_and_step_up_are_not_fixed_interest(self):
        for name in ('INDEXED GIC', 'Index-linked term deposit', 'Market-linked GIC', 'Step-up GIC'):
            value = row('gic'); value['product_name'] = name
            self.assertEqual(deposit_terms(value)['reason'], 'market_linked')

    def test_promotion_expiry_and_tier_qualifiers_block_even_scalar_rates(self):
        for metadata, reason in (({'promotional_rate': 3}, 'promotional'),
                                 ({'promotional_period_text': 'Ended 2025-01-01'}, 'promotional'),
                                 ({'introductory_rate_flag': True}, 'promotional'),
                                 ({'tiered_rate_flag': True}, 'tiered'),
                                 ({'tier_definition_text': '$0 to $1000'}, 'tiered')):
            value = row(); value['approved_deposit_conditions'] = metadata
            self.assertEqual(deposit_terms(value)['reason'], reason)

    def test_apy_and_compound_can_be_compared_but_not_simply_calculated(self):
        self.assertEqual(deposit_terms(row(interest_rate_summary='3% APY'))['calculation_reason'], 'apy')
        self.assertEqual(deposit_terms(row(compounding_frequency='monthly'))['calculation_reason'], 'compound')

    def test_exact_term_rows_use_their_own_rates(self):
        value = row('gic', term_rate_table=[{'term_label': '12 months', 'term_length_days': 360, 'rate': 3},
                                          {'term_label': '2 years', 'term_length_days': 730, 'rate': 4}])
        options = deposit_terms(value)['options']
        self.assertEqual([(x['key'], x['rate']) for x in options], [('m12', 3), ('m24', 4)])
        self.assertEqual(options[0]['minimum_deposit'], 500)

    def test_conflicting_terms_rates_and_row_notes_never_pick_a_winner(self):
        scenarios = [
            {'term_length_text': '18 months', 'term_rate_table': [{'term_label': '5 years', 'rate': 3}]},
            {'term_rate_table': [{'term_label': '1 year', 'term_length_days': 18, 'rate': 3}]},
            {'term_rate_table': [{'term_label': '1 year', 'rate': 3}, {'term_label': '12 months', 'rate': 4}]},
            {'term_rate_table': [{'term_label': '1 year', 'rate': 3, 'notes': 'New money only'}]},
            {'standard_rate': 2, 'term_rate_table': [{'term_label': '1 year', 'rate': 3}]},
        ]
        for metadata in scenarios:
            with self.subTest(metadata=metadata):
                self.assertEqual(deposit_terms(row('gic', **metadata))['options'], [])

    def test_table_cannot_bypass_product_qualification_or_invalid_duration(self):
        value = row('gic', description_short='Interest rate discount for eligible new clients.',
                    term_rate_table=[{'term_label': '1 year', 'rate': 3}, {'term_label': '2 years', 'rate': 4}])
        self.assertEqual(deposit_terms(value)['options'], [])
        for days in (-1, float('nan'), float('inf'), True):
            value = row('gic'); value['term_length_days'] = days
            self.assertEqual(deposit_terms(value)['options'], [])

    def test_term_missing_range_and_days_are_not_a_default_year(self):
        value = row('gic'); value['term_length_days'] = None
        value['refresh_metadata']['term_length_text'] = '1 to 5 years'
        self.assertEqual(deposit_terms(value)['reason'], 'term_unknown')
        value['refresh_metadata']['term_rate_table'] = [{'term_label': '29 days', 'rate': 3}]
        self.assertEqual(deposit_terms(value)['reason'], 'term_conflict')
        value['refresh_metadata']['term_rate_table'] = [{'term_label': '2 years', 'rate': 3}]
        self.assertEqual(deposit_terms(value)['options'][0]['key'], 'm24')
        value['refresh_metadata'] = {'interest_calculation_method': 'Annual rate', 'term_length_text': '360 days'}
        self.assertEqual(deposit_terms(value)['options'][0]['key'], 'd360')

    def test_reviewed_oaken_basis_is_bound_to_approved_version_and_values(self):
        value = row(interest_calculation_method='', standard_rate=2.8, product_version_id='pver_zq7rmli_JKGxZwKC')
        value.update(product_id='prod_mL9V64-_mjTai9Pb', bank_code='OAKEN', country_code='CA', public_display_rate=2.8)
        self.assertEqual(deposit_terms(value)['basis'], 'annual')
        for key, changed in (('product_id', 'other'), ('public_display_rate', 2.7), ('currency', 'USD')):
            self.assertEqual(deposit_terms({**value, key: changed})['reason'], 'basis_unknown')
        value['refresh_metadata']['product_version_id'] = 'new-version'
        self.assertEqual(deposit_terms(value)['reason'], 'basis_unknown')

    def test_qualified_deposit_contract_is_additive_and_private_fields_stay_private(self):
        value = next(deepcopy(item) for item in _projection_rows() if item['product_type'] == 'savings')
        original = _serialize_product_row(value, locale='en', evaluated_at='2026-09-24T00:00:00+00:00')
        value['approved_deposit_conditions'] = {'promotional_rate': 9, 'private_notes': 'SECRET'}
        updated = _serialize_product_row(value, locale='en', evaluated_at='2026-09-24T00:00:00+00:00')
        self.assertEqual(updated['deposit_terms']['reason'], 'promotional')
        self.assertEqual({k:v for k,v in original.items() if k != 'deposit_terms'}, {k:v for k,v in updated.items() if k != 'deposit_terms'})
        self.assertNotIn('SECRET', str(updated))
        self.assertIsNone(deposit_terms(row('credit-card')))
