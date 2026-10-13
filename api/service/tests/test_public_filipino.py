from __future__ import annotations
from dataclasses import replace
from datetime import UTC, datetime
import unittest
from pydantic import ValidationError
from api_service.models import PublicFeedbackRequest
from api_service.public_common import normalize_public_query_filters, localize_product_type, localize_bucket
from api_service.public_dashboard import load_public_dashboard_summary, load_public_dashboard_rankings, load_public_dashboard_scatter, PublicDashboardQuery
from api_service.public_feedback import create_public_feedback_submission
from test_public_dashboard import _PublicConnection, _latest_success_snapshot, _latest_success_attempt, _projection_rows
from test_public_feedback import _Connection, _Result


def filters(locale='fil', country='CA'):
    return normalize_public_query_filters(locale=locale, country_code=country, bank_codes=None, product_types=None,
        subtype_codes=None, target_customer_tags=None, fee_bucket=None, minimum_balance_bucket=None,
        minimum_deposit_bucket=None, term_bucket=None)


class FilipinoPublicTests(unittest.TestCase):
    def test_query_keeps_filipino_and_ph_without_changing_unknown_fallback(self):
        self.assertEqual(filters(' FIL ', ' ph ').locale, 'fil')
        self.assertEqual(filters('fil', 'PH').country_code, 'PH')
        self.assertEqual(filters('unknown').locale, 'en')
        self.assertEqual(localize_product_type('savings', locale='fil'), 'Savings account')
        self.assertEqual(localize_bucket('under_1y', locale='fil'), 'Wala pang 1 taon')

    def test_dashboard_full_empty_and_missing_snapshots_support_filipino(self):
        for rows, snapshot in [(_projection_rows(), _latest_success_snapshot()), ([], _latest_success_snapshot()), ([], None)]:
            def connection():
                return _PublicConnection(latest_success=snapshot, latest_attempt=_latest_success_attempt(), rows=rows)
            query = PublicDashboardQuery(filters=filters(), axis_preset=None)
            summary = load_public_dashboard_summary(connection(), query=query)
            english = load_public_dashboard_summary(connection(), query=replace(query, filters=filters('en')))
            self.assertEqual([m['value'] for m in summary['metrics']], [m['value'] for m in english['metrics']])
            self.assertTrue(any('produkto' in m['label'] for m in summary['metrics']))
            load_public_dashboard_rankings(connection(), query=query)
            load_public_dashboard_scatter(connection(), query=query)
            for product_type in ['chequing', 'savings', 'gic']:
                load_public_dashboard_scatter(connection(), query=replace(query, filters=replace(filters(), product_types=(product_type,))))

    def test_feedback_keeps_locale_country_and_original_details(self):
        connection = _Connection([_Result(one={'submission_id':'fil-feedback','submitted_at':datetime.now(UTC),
            'country_code':'PH','submission_type':'site_feedback','category':'usability_issue',
            'details':'Mas malinaw na menu','locale':'fil'})])
        result = create_public_feedback_submission(connection, country_code='PH', submission_type='site_feedback',
            category='usability_issue', details='Mas malinaw na menu', locale='fil', product_id=None)
        self.assertEqual(result['locale'], 'fil')
        self.assertEqual(connection.calls[0][1]['country_code'], 'PH')
        self.assertEqual(connection.calls[0][1]['details'], 'Mas malinaw na menu')
        self.assertIn("country_registry.status = 'active'", connection.calls[0][0])
        self.assertEqual(PublicFeedbackRequest(country_code='PH', submission_type='site_feedback', category='other', locale='fil').locale, 'fil')

    def test_feedback_missing_country_or_product_still_fails_closed(self):
        for submission_type, category, product_id in [('site_feedback','other',None), ('product_error','incorrect_rate_or_fee','other-country-product')]:
            connection = _Connection([_Result(one=None)])
            self.assertIsNone(create_public_feedback_submission(connection, country_code='PH', submission_type=submission_type,
                category=category, details=None, locale='fil', product_id=product_id))
            self.assertEqual(connection.calls[0][1]['country_code'], 'PH')

    def test_unknown_locale_and_invalid_category_do_not_write(self):
        for locale, category in [('tl','other'), ('fil','incorrect_rate_or_fee')]:
            connection = _Connection([])
            self.assertIsNone(create_public_feedback_submission(connection, country_code='PH', submission_type='site_feedback',
                category=category, details=None, locale=locale, product_id=None))
            self.assertEqual(connection.calls, [])
        with self.assertRaises(ValidationError):
            PublicFeedbackRequest(country_code='PH', submission_type='site_feedback', category='other', locale='tl')
