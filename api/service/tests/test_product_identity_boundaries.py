"""Prominent non-product identities cannot consume product collection slots."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from api_service.collection_preflight import source_block_reason
from api_service.source_catalog import (
    AiParallelCandidateScore, HomepageCandidate, _candidate_promotes_to_detail, _score_page_evidence,
)
from tests.test_source_catalog import _product_type_definition
from worker.product_source_policy import non_product_identity_reason

# Identity strings copied from retained BMO discovery metadata, 2026-10-02.
SAVED_IDENTITIES = (
    ('credit-card', 'Credit Card Access Details'),
    ('credit-card', 'Credit Card Security Protection'),
    ('credit-card', 'BMO ® Mastercard ®* Travel Insurance'),
    ('credit-card', 'BMO Prepaid Mastercard ®*'),
    ('gic', 'BMO Progressive GIC G I C Series search tool'),
    ('mortgage', 'Mortgage Protection Insurance'),
)


class ProductIdentityBoundaryTests(unittest.TestCase):
    def test_saved_and_independent_service_pages_cannot_be_promoted(self):
        independent = (
            ('mortgage', 'Example Bank Mortgage Protection Insurance'),
            ('credit-card', 'Example Visa Travel Insurance'),
            ('gic', 'Certificate of Deposit Search Tool'),
            ('personal-loan', 'Personal Loan Calculator'),
        )
        for product_type, heading in (*SAVED_IDENTITIES, *independent):
            with self.subTest(heading=heading):
                url = 'https://bank.example/products/'+product_type
                html = '<html><title>'+heading+'</title><h1>'+heading+'</h1><p>Annual interest rate 3.5%. Monthly fee $0. Term 12 months.</p></html>'
                with patch('api_service.source_catalog.fetch_text', return_value=html):
                    evidence = _score_page_evidence(raw_url=url, fetch_policy=SimpleNamespace(),
                        product_type=product_type, product_type_definition=_product_type_definition(product_type))
                self.assertIn('non_product_service_flow', evidence.page_evidence_reason_codes)
                candidate = HomepageCandidate(normalized_url=url, raw_url=url, anchor_text=heading,
                    source_type='html', origin='homepage_or_hub_link', heuristic_score=10, supporting_signal=False,
                    seed_source_id=None, source_name_hint=None, priority_hint=None, expected_fields_hint=[])
                ai = AiParallelCandidateScore(candidate_url=url, predicted_role='detail', relevance_score=10,
                    confidence_band='high', reason_codes=['detail_page_layout_signal'], short_rationale='')
                self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai,
                    page_evidence=evidence, allow_family_overview=True, allow_verified_coverage_review_source=True,
                    allow_verified_lending_review_source=True))

    def test_insurance_benefits_do_not_exclude_named_financial_products(self):
        for heading in ('Example Travel Visa', 'BMO Support Our Troops Mastercard', 'Security Savings Account'):
            product_type = 'savings' if 'Savings' in heading else 'credit-card'
            with self.subTest(heading=heading), patch('api_service.source_catalog.fetch_text', return_value=(
                '<html><title>'+heading+'</title><h1>'+heading+'</h1><h2>Travel Insurance</h2>'
                '<p>Insurance and security protection benefits. Annual fee $120. Annual purchase interest rate 20.99%.</p></html>')):
                evidence = _score_page_evidence(raw_url='https://bank.example/products/named', fetch_policy=SimpleNamespace(),
                    product_type=product_type, product_type_definition=_product_type_definition(product_type))
            self.assertNotIn('non_product_service_flow', evidence.page_evidence_reason_codes)
            self.assertIsNone(non_product_identity_reason(product_type=product_type, primary_heading=heading,
                page_title='Credit Card Travel Insurance | Bank'))

    def test_reuse_preflight_blocks_details_but_preserves_supporting_evidence(self):
        for product_type, heading in SAVED_IDENTITIES:
            row = {'product_type': product_type, 'discovery_role': 'detail',
                'latest_candidate_state': 'approved', 'discovery_metadata': {'primary_heading': heading}}
            with self.subTest(heading=heading):
                self.assertEqual(source_block_reason(row), 'non_product_service_flow')
                self.assertIsNone(source_block_reason({**row, 'discovery_role': 'supporting_html'}))
                # Explicit precision rediscovery fetches the current page before reclassification.
                self.assertIsNone(source_block_reason(row, revalidate=True))

    def test_missing_identity_is_left_for_normal_evidence_gates(self):
        self.assertIsNone(non_product_identity_reason(product_type='mortgage'))
        self.assertIsNone(non_product_identity_reason(product_type='unregistered', primary_heading='Search tool'))
        self.assertIsNone(source_block_reason({'product_type': 'mortgage', 'discovery_role': 'detail'}))


if __name__ == '__main__':
    unittest.main()
