from __future__ import annotations

import unittest
from decimal import Decimal

from api_service.public_rates import comparable_rate, interpret_rate_text, public_rate
from api_service.public_products import _explicit_rate_candidates, _serialize_product_row, _sort_numeric_rows
from api_service.public_dashboard import _build_ranking_widget, _build_scatter_chart
from test_public_products import _lending_projection


class PublicRateTests(unittest.TestCase):
    def test_reference_formulas_never_become_full_rates(self):
        for text in (
            'Variable low-interest rate based on BMO’s Prime Rate plus 0.5% while you’re in school.',
            'Variable interest rate is Prime Rate + 2.00%.',
            'BMO prime minus 0.25%', 'Prime − 0.25%', 'Prime – 0.25%',
            'Prime + .5%', 'Prime plus 1% to 3%', 'Prime Rate plus a margin of 2.00%',
            'SOFR + 2.25%', 'Base lending rate minus 1.5%',
            'Interest rate margin of 2%', 'Interest rate spread of 0.5%',
            'Variable interest rate equals Prime.',
            'Interest rate: Prime Rate was 6.75% as of July 1; plus 2%.',
            'Variable APR based on Prime Rate plus 1.50% to 3.00%.',
        ):
            with self.subTest(text=text):
                self.assertEqual(interpret_rate_text(text)['kind'], 'reference')
                self.assertEqual(_explicit_rate_candidates(text), [])

    def test_ranges_promotions_and_conditions_are_distinct(self):
        fixtures = {
            'Fixed rates from 5.15% to 18.00% APR': 'range',
            'APR between 16.74% and 25.74%': 'range',
            '5–7% APR': 'range',
            '18.24%–27.74% variable APR; Prime + 11.49% to 20.99%.': 'range',
            '0% introductory APR for 18 months, then 19.49% to 27.49%.': 'promotional',
            'Special offer interest rate of 4.5%.': 'promotional',
            '0% APR for 12 months then 18.99% APR.': 'promotional',
            'Discounted interest rate of 5%.': 'conditional',
            'Interest rate 9.99% with a 0.5% autopay discount.': 'conditional',
            '.25% interest rate discount for clients.': 'conditional',
            'Representative mortgage: 6.625% interest rate and 6.794% APR, 25% down payment.': 'conditional',
            'To pass the stress test, qualify at the contractual mortgage rate plus 2% or 5.25%.': 'conditional',
            'Interest rate from 6.74% APR, based on creditworthiness.': 'conditional',
            'Rates: 1 year 4.05%; 5 years 4.44%.': 'conditional',
        }
        for text, kind in fixtures.items():
            with self.subTest(text=text):
                parsed = interpret_rate_text(text)
                self.assertEqual(parsed['kind'], kind)
                self.assertIsNone(parsed['comparable_rate'])
                self.assertEqual(parsed['source_text'], text)

    def test_single_full_rates_and_zero_remain_usable(self):
        for value, expected in ((0, 0), (Decimal('5.25'), 5.25), ('0%', 0),
                                ('Fixed interest rate: 5.25%.', 5.25), ('0.050% per annum for all listed balance tiers', .05)):
            with self.subTest(value=value):
                self.assertEqual(_explicit_rate_candidates(value), [expected])
        for value in (True, False, 'NaN', Decimal('NaN'), 'Infinity', float('inf'), -1, 101, '101%', None,
                      '25% down payment', 'Earn 3% cashback', 'rate X.XX%', 'prime rate plus 0.5%'):
            with self.subTest(value=value):
                self.assertEqual(_explicit_rate_candidates(value), [])

    def test_summary_overrides_contaminated_scalar_in_list_and_detail(self):
        row = _lending_projection('reference', product_type='line-of-credit', rate_summary='Prime plus 0.5%')
        row['public_display_rate'] = Decimal('.5')
        row['refresh_metadata']['interest_rate'] = '.5'
        for locale in ('en', 'ko', 'ja'):
            item = _serialize_product_row(row, locale=locale)
            self.assertIsNone(item['card_display_rate'])
            self.assertIsNone(item['public_display_rate'])
            self.assertEqual(item['rate']['source_text'], 'Prime plus 0.5%')
            self.assertEqual(item['interest_rate_summary'], 'Prime plus 0.5%')
        self.assertEqual(row['public_display_rate'], Decimal('.5'))

    def test_numeric_conflict_and_deposit_conditions_fail_closed(self):
        self.assertIsNone(comparable_rate({'public_display_rate': 5, 'refresh_metadata': {'interest_rate_summary': 'Interest rate 4%'}}))
        for metadata in (
            {'description_short': 'Earn a boosted interest rate when you have an eligible account.'},
            {'interest_rate_summary': '5% promotional APY for new clients.'},
            {'term_rate_table': [{'term_label': '1 year', 'rate': 3}, {'term_label': '5 years', 'rate': 5}]},
        ):
            self.assertIsNone(comparable_rate({'product_family': 'deposit', 'public_display_rate': 5, 'refresh_metadata': metadata}))
        self.assertEqual(comparable_rate({'public_display_rate': 0, 'refresh_metadata': {}}), 0)
        self.assertIsNone(comparable_rate({'product_family': 'deposit', 'public_display_rate': 5, 'refresh_metadata': {'standard_rate': .5}}))
        for description in (
            'Great daily interest rates; deposits insured up to applicable limits.',
            'Earn up to 10x more interest on your USD compared to other banks.',
            '*rates subject to change. See all rates and account conditions.',
        ):
            self.assertEqual(comparable_rate({'public_display_rate': 2.5, 'refresh_metadata': {'description_short': description}}), 2.5)
        self.assertIsNone(comparable_rate({'public_display_rate': 4.5, 'refresh_metadata': {'description_short': 'Earn an interest rate of 0.30% on every dollar.'}}))


    def test_rate_sort_keeps_qualified_rows_after_full_rates_both_directions(self):
        rows = [self.row('spread', .5, 'Prime plus .5%'), self.row('full', 5), self.row('zero', 0)]
        for descending, expected in ((False, ['zero','full','spread']), (True, ['full','zero','spread'])):
            sorted_rows = _sort_numeric_rows(rows, field_name='public_display_rate', descending=descending, value_builder=comparable_rate)
            self.assertEqual([row['product_id'] for row in sorted_rows], expected)

    def test_dashboard_rank_and_scatter_exclude_non_comparable_rates(self):
        rows = [self.row('spread', 99, 'Prime plus 99%')] + [self.row(str(i), i) for i in (0, 2, 3)]
        widget = _build_ranking_widget(filtered_rows=rows, ranking_key='highest_display_rate', locale='en', refreshed_at=None)
        self.assertEqual([item['metric_value'] for item in widget['items']], [3, 2, 0])
        chart = _build_scatter_chart(filtered_rows=rows, axis_preset='savings_rate_vs_minimum_balance', locale='en')
        self.assertEqual([p['y_value'] for p in chart['points']], [0, 2, 3])
        self.assertIsNone(_build_ranking_widget(filtered_rows=rows[:3], ranking_key='highest_display_rate', locale='en', refreshed_at=None))

    @staticmethod
    def row(identifier, rate, summary=None):
        return {'product_id': identifier, 'product_type': 'savings', 'product_family': 'deposit',
                'product_name': identifier, 'bank_name': 'Bank', 'bank_code': 'B', 'minimum_balance': 0,
                'public_display_rate': rate, 'refresh_metadata': {'interest_rate_summary': summary}}
