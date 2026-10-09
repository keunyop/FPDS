"""Complete owned account costs; service and other-product context stay separate."""
import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes

class OwnedMaintenanceFeeTests(unittest.TestCase):
    def test_explicit_no_maintenance_fee_has_monthly_meaning(self):
        self.assertTrue(quote_supports_value('monthly_fee', 0, 'Example Savings Account\nNo monthly maintenance fees or minimum balance requirements.'))
        self.assertTrue(quote_supports_value('public_display_fee', 0, 'Example Savings Account\nNo monthly maintenance fees.'))

    def test_owned_fee_row_retains_its_notes_not_another_rows_condition(self):
        html = '<main><h1>Example Savings Account</h1><h2>Account fees</h2><table><tr><th>Service</th><th>Fee</th></tr><tr><td>Monthly maintenance fees</td><td>$0</td></tr><tr><td>Excess transactions if over the limit</td><td>$0</td></tr></table></main>'
        records = [s.text for s in parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments if s.anchor_type == 'owned_account_assertion']
        self.assertTrue(any('Monthly maintenance fees\n$0' in s for s in records))
        self.assertTrue(any(quote_supports_value('monthly_fee', 0, s) for s in records))
        self.assertFalse(any('Excess transactions' in s for s in records))

    def test_conditions_and_missing_or_duplicate_notes_still_exclude(self):
        for quote in ['No monthly maintenance fees if your balance is $5000', 'No monthly maintenance fees for the first six months', 'No monthly maintenance fees for eligible students']:
            self.assertFalse(quote_supports_value('monthly_fee', 0, quote))
        for note in ['', '<p id="price">First six months only</p><p id="price">No fees</p>']:
            html = '<main><h1>Example Savings Account</h1><table><tr><td>Monthly maintenance fees</td><td>$0<sup><a href="#price">1</a></sup></td></tr></table>' + note + '</main>'
            self.assertFalse(any(s.anchor_type == 'owned_account_assertion' for s in parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments))

    def test_named_competitor_panel_cannot_donate_a_fee(self):
        html = '<main><h1>Example Savings Account</h1><section data-product-name="Other Savings Account"><table><tr><td>Monthly maintenance fees</td><td>$0</td></tr></table></section></main>'
        self.assertFalse(any(s.anchor_type == 'owned_account_assertion' for s in parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments))

    def test_conditional_fee_note_is_retained_and_rejected(self):
        html = '<main><h1>Example Savings Account</h1><table><tr><td>Monthly maintenance fees</td><td>$0<sup><a href="#price">1</a></sup></td></tr></table><p id="price">Only for the first six months.</p></main>'
        records = [s.text for s in parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments if s.anchor_type == 'owned_account_assertion']
        self.assertTrue(any('Only for the first six months.' in s for s in records))
        self.assertFalse(any(quote_supports_value('monthly_fee', 0, s) for s in records))
    def test_empty_semantic_heading_cannot_crash_or_establish_identity(self):
        html = '<main><h1></h1><p>No monthly maintenance fees.</p></main>'
        records = parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments
        self.assertFalse(any(s.anchor_type == 'owned_account_assertion' for s in records))
        html = '<main><h1></h1><h1>Example Savings Account</h1><p>No monthly maintenance fees.</p></main>'
        records = parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments
        self.assertTrue(any(s.anchor_type == 'owned_account_assertion' for s in records))

    def test_bare_fee_footnotes_must_resolve_and_keep_conditions(self):
        for note in ['', '<li><sup>1</sup> Only for the first six months.</li>']:
            html='<main><h1>Example Savings Account</h1><p>No monthly maintenance fees<sup>1</sup></p>'+note+'</main>'
            records=[s.text for s in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if s.anchor_type=='owned_account_assertion']
            if note:self.assertTrue(any('first six months' in s for s in records))
            else:self.assertEqual(records,[])
            self.assertFalse(any(quote_supports_value('monthly_fee',0,s) for s in records))

    def test_heading_fee_condition_is_preserved(self):
        html='<main><h1>Example Savings Account</h1><h2>Only for the first six months</h2><p>No monthly maintenance fees.</p></main>'
        records=[s.text for s in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if s.anchor_type=='owned_account_assertion']
        self.assertFalse(any(quote_supports_value('monthly_fee',0,s) for s in records))

    def test_separate_cash_reward_header_cannot_condition_regular_fee(self):
        html='<main><h1>Example Savings Account</h1><h2>Earn $350 when you set up direct deposit</h2><p>No monthly maintenance fees.</p></main>'
        records=[s.text for s in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if s.anchor_type=='owned_account_assertion']
        self.assertTrue(any(quote_supports_value('monthly_fee',0,s) for s in records))

    def test_dagger_fee_note_is_complete_or_missing(self):
        for note in ['', '<li><sup>\u2020</sup> Only for eligible customers.</li>']:
            html='<main><h1>Example Savings Account</h1><p>No monthly fees<sup>\u2020</sup></p>'+note+'</main>'
            records=[s.text for s in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if s.anchor_type=='owned_account_assertion']
            if note:self.assertTrue(any('Only for eligible' in s for s in records))
            else:self.assertEqual(records,[])
            self.assertFalse(any(quote_supports_value('monthly_fee',0,s) for s in records))
