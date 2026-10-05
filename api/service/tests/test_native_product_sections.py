from pathlib import Path
import unittest
from unittest.mock import patch
from api_service.source_catalog import _score_page_evidence, _discover_detail_companion_links
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "worker/pipeline/tests/fixtures/native-product-sections"

class NativeProductDiscoveryTests(unittest.TestCase):
    def test_complete_native_sections_resolve_family_boundary_without_identity_score_override(self):
        html = (FIX / "named-accounts.html").read_text(encoding="utf8")
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            result = _score_page_evidence(raw_url="https://www.fnbc.ca/personal/banking/chequing-accounts",
                fetch_policy=DiscoveryFetchPolicy(allowed_domains=("fnbc.ca",)), product_type="chequing",
                product_type_definition={"discovery_keywords": ["chequing", "account"], "expected_fields": ["monthly_fee", "included_transactions"]})
        self.assertIn("native_named_product_sections_resolved", result.page_evidence_reason_codes)
        self.assertNotIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_incomplete_sections_keep_family_boundary_exclusion(self):
        html = (FIX / "named-accounts.html").read_text(encoding="utf8").replace("Minimum monthly balance must be maintained throughout the calendar month to qualify for fee waiver or rebate.", "Unknown terms.")
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            result = _score_page_evidence(raw_url="https://www.fnbc.ca/personal/banking/chequing-accounts",
                fetch_policy=DiscoveryFetchPolicy(allowed_domains=("fnbc.ca",)), product_type="chequing",
                product_type_definition={"discovery_keywords": ["chequing", "account"], "expected_fields": ["monthly_fee", "included_transactions"]})
        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_legal_companion_only_selected_for_missing_essential_annual_basis(self):
        url = "https://example.ca/savings/example"
        def discover(html):
            return _discover_detail_companion_links(detail_rows=[{"normalized_url": url, "raw_url": url}], country_code="CA",
                product_type="savings", fetch_policy=DiscoveryFetchPolicy(allowed_domains=("example.ca",)), hostname="example.ca",
                allowed_domains=("example.ca",), page_html_by_url={url: html})[0]
        self.assertEqual(len(discover('<h1>Example Account earns 2.50% interest</h1><a href="/legal">Legal</a>')), 1)
        self.assertEqual(discover('<h1>Example Account earns an annual interest rate of 2.50%</h1><a href="/legal">Legal</a>'), [])
        self.assertEqual(discover('<h1>Example Account</h1><a href="/legal">Legal</a>'), [])

    def test_native_proof_survives_ai_hub_label_through_final_source_selection(self):
        from api_service.source_catalog import HomepageCandidate, AiParallelCandidateScore, _promote_detail_candidates
        from dataclasses import replace
        url = "https://www.fnbc.ca/personal/banking/chequing-accounts"
        html = (FIX / "named-accounts.html").read_text(encoding="utf8")
        definition = {"discovery_keywords": ["chequing", "account"], "expected_fields": ["monthly_fee", "included_transactions"]}
        policy = DiscoveryFetchPolicy(allowed_domains=("fnbc.ca",))
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(raw_url=url, fetch_policy=policy, product_type="chequing", product_type_definition=definition)
        candidate = HomepageCandidate(normalized_url=url, raw_url=url, anchor_text="Chequing accounts", source_type="html", origin="homepage_or_hub_link", heuristic_score=3,
            supporting_signal=False, seed_source_id=None, source_name_hint=None, priority_hint=None, expected_fields_hint=[])
        ai = AiParallelCandidateScore(candidate_url=url, predicted_role="entry", relevance_score=7, confidence_band="high", reason_codes=["hub_page_not_detail", "multi_product_family_overview"], short_rationale="Family page.")
        rows, _, _ = _promote_detail_candidates(bank_code="FNBC", bank_name="First Nations Bank of Canada", country_code="CA", product_type="chequing", discovery_product_type="chequing",
            product_type_definition=definition, source_language="en", fetch_policy=policy, candidates=[candidate], ai_scores={url: ai}, page_evidence_by_url={url: evidence}, page_html_by_url={url: html})
        self.assertEqual(len(rows), 1)
        self.assertIn("native_named_product_sections_resolved", rows[0]["discovery_metadata"]["selection_reason_codes"])
        self.assertNotIn("hub_page_not_detail", rows[0]["discovery_metadata"]["selection_reason_codes"])
        self.assertIn("hub_page_not_detail", rows[0]["discovery_metadata"]["raw_ai_reason_codes"])

class NativeProductPromotionTests(unittest.TestCase):
    def _row(self):
        from worker.native_product_sections import extract_named_product_sections
        section = next(x for x in extract_named_product_sections((FIX / "named-accounts.html").read_text(encoding="utf8")) if x.name == "Value Account")
        price = next(x for x in section.financial_records if "Monthly fees" in x)
        transactions = next(x for x in section.financial_records if "Transactions Included" in x)
        facts = {"product_name": (section.name, section.name), "monthly_fee": (3.95, price),
            "included_transactions": (12, transactions), "additional_transaction_fee": (1.25, transactions)}
        return {"product_type": "chequing", "product_name": section.name,
            "candidate_payload": {name: value for name, (value, quote) in facts.items()},
            "field_mapping_metadata": {name: {"official_grounding_contract_version": "collection-official-grounding-v2",
                "official_grounding_method": "deterministic_named_product_section", "official_verification_status": "match",
                "official_web_sources": [{"url": "https://otherbank.ca/accounts"}], "evidence_chunk_id": "chunk-"+name,
                "official_evidence_quote": quote, "normalized_value": value}
                for name, (value, quote) in facts.items()},
            "source_metadata": {"discovery_metadata": {"selection_reason_codes": ["multi_product_family_overview"]}}}

    def test_complete_independent_account_proof_survives_original_family_metadata_at_promotion(self):
        from api_service.candidate_auto_promotion import _has_ambiguous_product_boundary
        self.assertFalse(_has_ambiguous_product_boundary(self._row()))

    def test_missing_foreign_or_conditional_account_proof_keeps_promotion_boundary(self):
        from api_service.candidate_auto_promotion import _has_ambiguous_product_boundary
        for field in ["monthly_fee", "additional_transaction_fee", "product_name"]:
            row = self._row();row["field_mapping_metadata"].pop(field)
            self.assertTrue(_has_ambiguous_product_boundary(row))
        row = self._row();row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = "Other Account Monthly fees $3.95"
        self.assertTrue(_has_ambiguous_product_boundary(row))
        row = self._row();row["candidate_payload"]["monthly_fee"] = 0
        self.assertTrue(_has_ambiguous_product_boundary(row))
        row = self._row();row["source_metadata"]["discovery_metadata"]["selection_reason_codes"].append("verified_coverage_review_source")
        self.assertTrue(_has_ambiguous_product_boundary(row))
