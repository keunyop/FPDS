from pathlib import Path
import gzip
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_admin_collection_parity import input_from_segments, run_services

FIX = Path(__file__).parent / 'fixtures/explicit-market-currency'


class CompleteLoanCostRangeTests(unittest.TestCase):
    def test_current_complete_rate_range_survives_ordinary_pipeline(self):
        raw = gzip.decompress((FIX / 'metrobank-loan.html.gz').read_bytes())
        parsed = parse_snapshot_bytes(body=raw, content_type='text/html')
        item = input_from_segments(bank='METROBANK', url='https://www.metrobank.com.ph/personal/loans/personal-loan', product='personal-loan', name='Personal Loan', segments=parsed.segments, country='PH')
        item.context.source_metadata['product_family'] = 'lending'
        record, validation, _ = run_services([item])
        payload = record['candidate_payload']
        self.assertEqual(validation.validation_action, 'auto_validated', payload['_collection_accuracy'])
        self.assertEqual(record['currency'], 'PHP')
        for fact in ['30.516%', '33.317%', '1.25% monthly add-on', 'Disbursement Fee', 'Documentary Stamp Tax', 'Pre-termination Fee', 'subject to change']:
            self.assertIn(fact, payload['interest_rate_summary'])
        self.assertIn('12 months', payload['term_length_text'])
        self.assertIn('36 months', payload['term_length_text'])
        self.assertNotIn('interest_rate', payload)
        self.assertNotIn('term_length_days', payload)

    def test_complete_terms_are_generic_and_fail_closed_at_boundaries(self):
        from bs4 import BeautifulSoup
        from worker.native_owned_lending_records import lending_records, complete_loan_cost_range
        raw = gzip.decompress((FIX/'metrobank-loan.html.gz').read_bytes()).decode('utf8')
        html = raw.replace('Metrobank', 'ExampleBank').replace('metrobank', 'examplebank')
        records = lending_records(BeautifulSoup(html, 'html.parser'))
        quote = next(q for kind, _, q in records if kind == 'owned_lending_terms')
        self.assertIn('12 months', complete_loan_cost_range(quote))
        for old, new in [('Minimum APR is', 'Indicative APR is'), ('maximum APR is 33.317%', 'maximum APR is 20%'), ('maximum repayment period is 36 months', 'maximum repayment period is 6 months'), ('Rates and fees are subject to change.', ''), ('30.516%', 'XX.XXX%')]:
            self.assertIsNone(complete_loan_cost_range(quote.replace(old, new)))
        from worker.pipeline.fpds_rate_safety import contains_unresolved_financial_placeholder
        self.assertFalse(contains_unresolved_financial_placeholder(quote))
        self.assertTrue(contains_unresolved_financial_placeholder(quote.replace('**Minimum repayment', '**Missing repayment')))
        self.assertTrue(contains_unresolved_financial_placeholder(quote.replace('Php 1,500', 'Php ***')))
        for url in ['https://foreignbank.com/personal/loans/personal-loan', 'https://www.examplebank.com/personal/loans/other-loan']:
            parsed = parse_snapshot_bytes(body=html.encode(), content_type='text/html')
            item = input_from_segments(bank='EXAMPLE', url=url, product='personal-loan', name='unverified', segments=parsed.segments, country='PH')
            item.context.source_metadata['official_domain_allowlist'] = ['examplebank.com']
            _, validation, _ = run_services([item])
            self.assertEqual(validation.validation_action, 'excluded', url)

    def test_amortization_example_is_not_an_unconditional_lending_rate(self):
        from bs4 import BeautifulSoup
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        raw = gzip.decompress((FIX/'unionbank-loan.html.gz').read_bytes())
        soup = BeautifulSoup(raw, 'html.parser')
        table = next(t for t in soup.find_all('table') if 'Monthly Installment' in t.get_text() and '26.9%' in t.get_text())
        quote = table.get_text(' ', strip=True)
        self.assertFalse(quote_supports_value('interest_rate', 26.9, quote))
        self.assertFalse(quote_supports_value('interest_rate', 26.9, 'These are estimated amortizations based on average Annual Contractual Rate (ACR) of 26.9%.'))
        self.assertTrue(quote_supports_value('interest_rate', 26.9, 'Annual interest rate 26.9%'))
