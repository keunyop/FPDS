"""Official-byte and cross-issuer boundaries for complete named PDF pricing."""
import hashlib
import io
import json
import zlib
from pathlib import Path
import unittest
from pypdf import PdfReader
from worker.native_single_card_pdf import single_card_purchase_records, single_card_fee_value

FIXTURES = Path(__file__).parent / "fixtures/td-us-terms"

class OfficialTermsTests(unittest.TestCase):
    def test_current_official_extended_terms(self):
        for entry in json.loads((FIXTURES / "manifest.json").read_text()):
            raw = zlib.decompress((FIXTURES / entry["file"]).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
            pages = [p.extract_text() for p in PdfReader(io.BytesIO(raw)).pages]
            records = single_card_purchase_records(pages)
            purchase = next(q for k, _, q in records if k == "single_card_purchase_terms")
            assert "Prime Rate" in purchase and "December 11, 2025" in purchase
            assert "Minimum Payment Due" in purchase and "creditworthiness" in purchase
            assert "17.49%" in purchase if "tdflex" in entry["file"] else "28.49%" in purchase
            fee = next(q for k, _, q in records if k == "single_card_annual_fee")
            assert single_card_fee_value(fee) == 0


def sample():
    return ["""Acme Rewards Credit Card Important Credit Card Terms and Conditions
Additional fees and account terms are described in the Acme Rewards Credit Card Agreement.
The terms below and in the Acme Rewards Credit Card Agreement may change.
Interest Rates and Interest Charges Annual Percentage Rate (APR) for Purchases:
0% Introductory APR for the first 12 billing cycles after Account opening.
After that, your APR will be 18.49%, 21.49% or 28.49%, based on your creditworthiness.
All APRs will vary with the market based on the Prime Rate.
APR for Balance Transfers: 20% Paying Interest: Pay your entire balance by the due date.
Minimum Interest Charge: $1. Fees Annual Fee: None Transaction Fees: $5
How We Will Calculate Your Balance: Average Daily Balance.
Procedures for Opening a New Account: identification required.""",
"""How the Variable APRs on your Account are Determined: Add a margin.
Margins: For Purchases, 11.74%, 14.74% or 21.74% will be added to the Index.
Index: The Prime Rate (U.S.) as published in The Wall Street Journal.
As of December 11, 2025 the Prime Rate was 6.75%.
Card Eligibility: Minimum age and credit requirements.
Balance Transfers: Only eligible accounts.
Introductory or Promotional APRs on Balance transfers: Pay Minimum Payment Due plus purchases and fees.
Credit Reports: We obtain a report.""",
"CONSENT TO USE CREDIT BUREAUS: legal administrative consent."]


def test_other_issuer_preserves_all_purchase_and_grace_conditions():
    records = single_card_purchase_records(sample())
    quote = next(q for k, _, q in records if k == "single_card_purchase_terms")
    assert "21.49%" in quote and "Minimum Payment Due plus purchases and fees" in quote
    assert "Minimum age and credit requirements" in quote
    assert not any(k == "purchase_interest_rate" for k, _, _ in records)


def test_missing_conflicting_or_invalid_terms_exclude():
    for old, new in [
        ("Credit Reports:", "Reports:"),
        ("December 11, 2025", "unknown"),
        ("28.49%", "128.49%"),
        ("All APRs will vary with the market based on the Prime Rate.", ""),
        ("Acme Rewards Credit Card Agreement may", "Acme Other Credit Card Agreement may"),
    ]:
        pages = [s.replace(old, new) for s in sample()]
        assert not single_card_purchase_records(pages), (old, new)


def test_later_conflicting_purchase_table_excludes():
    assert not single_card_purchase_records(sample() + ["Annual Percentage Rate (APR) for Purchases: 45%"])


def test_conditional_fee_never_becomes_zero():
    pages = [s.replace("Annual Fee: None", "Annual Fee: $89 (waived for the first year)") for s in sample()]
    records = single_card_purchase_records(pages)
    assert any(k == "single_card_purchase_terms" for k, _, _ in records)
    assert not any(k == "single_card_annual_fee" for k, _, _ in records)

class BoundaryTests(unittest.TestCase):
    test_other_issuer_preserves_all_purchase_and_grace_conditions = staticmethod(test_other_issuer_preserves_all_purchase_and_grace_conditions)
    test_missing_conflicting_or_invalid_terms_exclude = staticmethod(test_missing_conflicting_or_invalid_terms_exclude)
    test_later_conflicting_purchase_table_excludes = staticmethod(test_later_conflicting_purchase_table_excludes)
    test_conditional_fee_never_becomes_zero = staticmethod(test_conditional_fee_never_becomes_zero)


class PipelineTermsTests(unittest.TestCase):
    def test_atomic_terms_reach_existing_automatic_gate(self):
        from types import SimpleNamespace
        from worker.pipeline.tests.test_evidence_research_parity import input_from_segments, run_services
        records = single_card_purchase_records(sample())
        segments = [SimpleNamespace(anchor_type=k, anchor_value=o, page_no=1, text=q) for k, o, q in records]
        from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
        html = b'<title>Acme Rewards Credit Card</title><main><h1>Acme Rewards Credit Card</h1><p>Annual Fee</p><p>$0</p></main>'
        detail = input_from_segments(bank='ACME', url='https://acme.com/credit-cards/acme-rewards', product='credit-card', name='Acme Rewards Credit Card', country='US', segments=parse_snapshot_bytes(body=html,content_type='text/html').segments)
        companion = input_from_segments(bank='ACME', url='https://acme.com/rewards-terms.pdf', product='credit-card', name='Pricing', country='US', segments=segments,role='linked_pdf',ident='pdf')
        row, validation, _ = run_services([detail, companion])
        self.assertEqual(validation.validation_action, 'auto_validated', row['candidate_payload'])
        self.assertNotIn('purchase_interest_rate', row['candidate_payload'])
        self.assertIn('21.49%', row['candidate_payload']['purchase_interest_rate_summary'])
        from dataclasses import replace
        foreign = replace(companion, context=replace(companion.context, bank_code='OTHER'))
        row, validation, _ = run_services([detail, foreign])
        self.assertEqual(validation.validation_action, 'excluded')


class ContinuationBoundaryTests(unittest.TestCase):
    def test_late_financial_qualifications_are_not_discarded(self):
        for note in ["Purchases bear interest after a missed payment.", "Your APR increases on default.", "The annual fee is $99."]:
            self.assertFalse(single_card_purchase_records(sample() + [note]))
            pages = sample()
            pages[1] += " " + note
            self.assertFalse(single_card_purchase_records(pages))


class AccountDeclarationTests(unittest.TestCase):
    def test_actual_amount_first_fee_preserves_waiver(self):
        import gzip
        from bs4 import BeautifulSoup
        from worker.native_owned_account_records import account_records
        raw = gzip.decompress((FIXTURES / 'checking.html.gz').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), json.loads((FIXTURES / 'checking-source.json').read_text())['sha256'])
        records = account_records(BeautifulSoup(raw, 'html.parser'))
        prices = [q for _, _, q in records if '$15 Monthly Maintenance Fee' in q]
        self.assertEqual(len(prices), 1)
        self.assertIn('waive', prices[0].lower())
        self.assertIn('$500', prices[0])

    def test_checking_and_savings_own_amount_first_prices(self):
        from bs4 import BeautifulSoup
        from worker.native_owned_account_records import account_records
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        for name in ['Acme Checking', 'Acme Savings']:
            html = '<main><h1>'+name+'</h1><p>$15 Monthly Maintenance Fee</p></main>'
            records = account_records(BeautifulSoup(html, 'html.parser'))
            self.assertEqual(len(records), 1)
            self.assertTrue(quote_supports_value('monthly_fee', 15, records[0][2]))
            from worker.pipeline.tests.test_evidence_research_parity import input_from_segments, run_services
            from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
            kind = 'chequing' if 'Checking' in name else 'savings'
            body = html.replace('</main>', '<p>Unlimited transactions</p></main>').encode()
            detail = input_from_segments(bank='ACME', url='https://acme.com/'+kind+'/acme-'+kind, product=kind, name=name, country='US', segments=parse_snapshot_bytes(body=body, content_type='text/html').segments)
            row, validation, _ = run_services([detail])
            self.assertEqual(row['candidate_payload'].get('monthly_fee'), 15)
            if kind == 'chequing':
                self.assertEqual(validation.validation_action, 'auto_validated', row['candidate_payload'])
            else:
                self.assertEqual(validation.validation_action, 'excluded')
                self.assertIn('standard_rate', row['candidate_payload']['_collection_accuracy']['missing_fields'])
            foreign = html.replace('<p>', '<section data-account-name="Other Savings"><p>').replace('</p>', '</p></section>')
            self.assertFalse(account_records(BeautifulSoup(foreign, 'html.parser')))
            unknown = html.replace('Fee</p>', 'Fee<a href="#missing">1</a></p>')
            self.assertFalse(account_records(BeautifulSoup(unknown, 'html.parser')))
