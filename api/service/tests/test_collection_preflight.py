from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from api_service.collection_preflight import source_block_reason, no_detail_result_is_structural
from api_service.source_catalog import (
    HomepageCandidate, AiParallelCandidateScore, PageEvidenceAssessment,
    _preflight_catalog_items, _source_scope_exclusion_reason, _score_page_evidence,
    _promote_detail_candidates, _link_is_relevant_supporting_source,
    start_source_catalog_collection,
)
from api_service.source_registry import prepare_source_collection, _is_candidate_producing_collection_source
from api_service.errors import SourceRegistryError
from tests.test_source_catalog import _product_type_definition, _QueuedConnection


def source(**changes):
    return {"source_id": "BANK-SAV-1", "bank_code": "BANK", "country_code": "CA",
            "product_type": "savings", "source_language": "en", "status": "active",
            "discovery_role": "detail", "source_type": "html", "discovery_metadata": {},
            "source_name": "Savings Account", "source_url": "https://bank.example/savings",
            "normalized_url": "https://bank.example/savings", "expected_fields": [], **changes}


def catalog(**changes):
    return {"catalog_item_id": "catalog-1", "bank_code": "BANK", "country_code": "CA",
            "product_type": "savings", "bank_name": "Bank", "homepage_url": "https://bank.example",
            "source_language": "en", "has_completed_collection": True, **changes}


class CollectionPreflightTests(unittest.TestCase):
    def test_only_latest_human_hold_blocks_standard_collection(self):
        for state, action, reason in (("deferred", "defer", "review_deferred"), ("rejected", "reject", "review_rejected")):
            row = source(latest_review_state=state, latest_review_action=action, latest_review_actor="operator")
            self.assertEqual(source_block_reason(row), reason)
            self.assertIsNone(source_block_reason(row, revalidate=True))
            self.assertIsNone(source_block_reason({**row, "latest_review_state": "approved", "latest_review_action": "approve"}))
            self.assertIsNone(source_block_reason({**row, "latest_review_actor": None}))
            self.assertIsNone(source_block_reason({**row, "latest_candidate_count": 2}))
        self.assertIsNone(source_block_reason(source(latest_review_state="queued")))
        self.assertIsNone(source_block_reason(source(candidate_payload={"product_name": "Savings Account"})))

    def test_structural_failures_block_but_transient_and_later_success_do_not(self):
        for error in ("PDF source returned non-PDF content after bounded fetch recovery", "HTML access challenge remained after bounded browser fallback", "HTTP Error 404: Not Found", "status 410"):
            row = source(latest_stage_status="failed", latest_error_summary=error)
            self.assertIsNotNone(source_block_reason(row))
            self.assertIsNone(source_block_reason({**row, "latest_stage_status": "completed"}))
        for error in ("HTTP Error 429", "HTTP Error 503", "timed out", "connection reset", "browser fallback was unavailable"):
            self.assertIsNone(source_block_reason(source(latest_stage_status="failed", latest_error_summary=error)))

    def test_ambiguous_boundary_cannot_enter_direct_collection(self):
        for reason in ("verified_coverage_review_source", "multi_product_family_overview", "hub_page_not_detail"):
            row = source(discovery_metadata={"selection_reason_codes": [reason]})
            self.assertEqual(source_block_reason(row), "unresolved_product_boundary")
            self.assertIsNone(source_block_reason({**row, "latest_candidate_state": "approved"}))
            with (patch("api_service.source_registry.load_source_preflight_rows", return_value=[row]),
                  patch("api_service.source_registry.load_product_type_definitions_map", return_value={} )):
                with self.assertRaises(SourceRegistryError):
                    prepare_source_collection(_QueuedConnection([[row]]), source_ids=[row["source_id"]], actor={}, request_id=None)
        self.assertTrue(_is_candidate_producing_collection_source(source()))

    def test_non_html_and_denied_redirect_are_structural_not_product_absence(self):
        notes = ["Hub page fetch was unavailable: Text fetch expected HTML content but received application/pdf",
                 "Page evidence was unavailable: Host not in discovery fetch allowlist: login.other.example",
                 "Detail rejection summary: page_evidence_below_threshold=20"]
        self.assertTrue(no_detail_result_is_structural(notes))
        self.assertFalse(no_detail_result_is_structural(notes + ["Page evidence was unavailable: timed out"]))
        self.assertFalse(no_detail_result_is_structural(notes + ["Page evidence was unavailable: SSL CERTIFICATE_VERIFY_FAILED"]))
        self.assertFalse(no_detail_result_is_structural([
            "HTML access challenge remained after bounded browser fallback", "Other page fetch was unavailable: timeout"]))

    def test_all_held_launch_creates_no_run_and_no_background_job(self):
        connection = _QueuedConnection([[catalog()]])
        held = source(latest_review_state="deferred", latest_review_action="defer", latest_review_actor="operator")
        with (patch("api_service.source_catalog.load_source_preflight_rows", return_value=[held]),
              patch("api_service.source_catalog._insert_collection_run_row") as insert,
              patch("api_service.source_catalog._launch_source_catalog_collection_runner") as launch,
              patch("api_service.source_catalog._record_catalog_audit_event")):
            result = start_source_catalog_collection(connection, catalog_item_ids=["catalog-1"], actor={"user_id": "operator"}, request_context={})
        self.assertEqual(result["run_ids"], [])
        self.assertEqual(result["workflow_state"], "skipped")
        self.assertEqual(result["skipped_items"][0]["reason_codes"], ["review_deferred"])
        insert.assert_not_called()
        launch.assert_not_called()

    def test_mixed_scopes_keep_valid_collection_and_explicit_rediscovery_reopens(self):
        rows = [catalog(), catalog(catalog_item_id="catalog-2", bank_code="OTHER")]
        held = source(latest_review_state="rejected", latest_review_action="reject", latest_review_actor="operator")
        with patch("api_service.source_catalog.load_source_preflight_rows", side_effect=[[held], [source(bank_code="OTHER")]]):
            eligible, skipped = _preflight_catalog_items(_QueuedConnection([]), rows=rows, precision_rediscovery=False)
        self.assertEqual(eligible, [rows[1]])
        self.assertEqual(skipped[0]["bank_code"], "BANK")
        with patch("api_service.source_catalog.load_source_preflight_rows") as load:
            self.assertEqual(_preflight_catalog_items(_QueuedConnection([]), rows=rows, precision_rediscovery=True), (rows, []))
        load.assert_not_called()
        with patch("api_service.source_catalog.load_source_preflight_rows", return_value=[held, source(source_id="NEW-DETAIL")]):
            self.assertEqual(_preflight_catalog_items(_QueuedConnection([]), rows=[rows[0]], precision_rediscovery=False), ([rows[0]], []))

    def test_zero_detail_history_blocks_only_unchanged_structural_scope(self):
        now = datetime.now(UTC)
        previous = {"run_metadata": {"discovery_status": "no_detail_sources_discovered", "discovery_notes": ["Detail rejection summary: no detail sources"]}, "completed_at": now, "catalog_updated_at": now - timedelta(days=1)}
        with patch("api_service.source_catalog.load_source_preflight_rows", return_value=[]):
            eligible, skipped = _preflight_catalog_items(_QueuedConnection([previous]), rows=[catalog()], precision_rediscovery=False)
            self.assertFalse(eligible)
            self.assertEqual(skipped[0]["reason_codes"], ["structural_zero_detail_requires_rediscovery"])
            eligible, _ = _preflight_catalog_items(_QueuedConnection([{**previous, "catalog_updated_at": now + timedelta(seconds=1)}]), rows=[catalog()], precision_rediscovery=False)
            self.assertEqual(len(eligible), 1)

    def test_direct_retry_does_not_reenter_held_review(self):
        held = source(latest_review_state="rejected", latest_review_action="reject", latest_review_actor="operator")
        with (patch("api_service.source_registry.load_source_preflight_rows", return_value=[held]),
              patch("api_service.source_registry.load_product_type_definitions_map", return_value={"savings": _product_type_definition("savings")})):
            with self.assertRaises(SourceRegistryError) as raised:
                prepare_source_collection(_QueuedConnection([[source()]]), source_ids=["BANK-SAV-1"], actor={}, request_id=None)
        self.assertEqual(raised.exception.code, "collection_preflight_blocked")

    def test_mixed_direct_collection_removes_orphan_support_group_from_plan(self):
        held = source(latest_review_state="rejected", latest_review_action="reject", latest_review_actor="operator")
        support = source(source_id="BANK-SUPPORT", discovery_role="supporting_html")
        valid = source(source_id="OTHER-DETAIL", bank_code="OTHER")
        with (patch("api_service.source_registry.load_source_preflight_rows", return_value=[held, support, valid]),
              patch("api_service.source_registry.load_product_type_definitions_map", return_value={})):
            plan = prepare_source_collection(
                _QueuedConnection([[held, support, valid]]),
                source_ids=[held["source_id"], support["source_id"], valid["source_id"]],
                actor={}, request_id=None,
            )["plan"]
        self.assertEqual(plan["selected_source_ids"], ["OTHER-DETAIL"])
        self.assertEqual(plan["target_source_ids"], ["OTHER-DETAIL"])
        self.assertEqual(plan["auto_included_source_ids"], [])
        self.assertEqual(len(plan["groups"]), 1)
        self.assertEqual(plan["groups"][0]["bank_code"], "OTHER")

    def test_investor_customer_is_not_investor_relations(self):
        for host in ("schwab.com", "anotherbank.example"):
            self.assertIsNone(_source_scope_exclusion_reason(product_type="chequing", fingerprint=f"https://{host}/checking A checking account built for investors."))
            for path in ("/investor-relations", "/about/investors-shareholders.html", "/shareholders"):
                self.assertEqual(_source_scope_exclusion_reason(product_type="chequing", fingerprint=f"https://{host}{path} Investor relations"), "non_product_or_investor_page")

    def test_non_product_pages_and_workbooks_are_excluded_across_banks(self):
        for host in ("desjardins.com", "bank.example"):
            for path in ("/about-us/system-modernization.html", "/help/system-maintenance"):
                self.assertEqual(_source_scope_exclusion_reason(product_type="credit-card", fingerprint=f"https://{host}{path} Modernizing our credit card management system"), "non_product_service_flow")
            self.assertFalse(_link_is_relevant_supporting_source(product_type="chequing", product_type_definition=_product_type_definition("chequing"), normalized_url=f"https://{host}/documents/e35-budget-etudiant-e.pdf", anchor_text="Student budget worksheet"))
            self.assertTrue(_link_is_relevant_supporting_source(product_type="chequing", product_type_definition=_product_type_definition("chequing"), normalized_url=f"https://{host}/chequing/fees.pdf", anchor_text="Chequing account service fees"))

    def test_single_named_section_recovers_plural_heading_without_accepting_two_products(self):
        url = "https://bank.example/savings-accounts"
        candidate = HomepageCandidate(normalized_url=url, raw_url=url, anchor_text="Savings accounts", source_type="html", origin="verified_coverage_source", heuristic_score=5, supporting_signal=False, seed_source_id=None, source_name_hint=None, priority_hint=None, expected_fields_hint=[])
        ai = AiParallelCandidateScore(candidate_url=url, predicted_role="supporting_html", relevance_score=9, confidence_band="high", reason_codes=["hub_page_not_detail", "product_type_semantic_match"], short_rationale="Plural URL")
        html = '<title>Savings Accounts | Bank</title><nav><h2>Youth Savings Account</h2></nav><h1>Savings accounts</h1><h2>The High-Interest Savings Account</h2><p>No monthly fee. Interest rate 1.5%. Two free transactions. Minimum balance $0.</p>'
        for extra, expected in (("", 1), ("<h2>Youth Savings Account</h2><p>Another rate.</p>", 0)):
            with patch("api_service.source_catalog.fetch_text", return_value=html + extra):
                rows, rejected, notes = _promote_detail_candidates(bank_code="BANK", bank_name="Bank", country_code="CA", product_type="savings", discovery_product_type="savings", product_type_definition=_product_type_definition("savings"), source_language="en", fetch_policy=SimpleNamespace(), candidates=[candidate], ai_scores={url: ai})
            self.assertEqual(len(rows), expected, notes)
            if rows:
                self.assertEqual(rows[0]["discovery_metadata"]["primary_heading"], "The High-Interest Savings Account")
                self.assertNotIn("hub_page_not_detail", rows[0]["discovery_metadata"]["selection_reason_codes"])
                self.assertIn("hub_page_not_detail", rows[0]["discovery_metadata"]["raw_ai_reason_codes"])
            else:
                self.assertIn(url, rejected)

    def test_verified_coverage_exception_stops_before_candidate_generation(self):
        url = "https://bank.example/lines-of-credit"
        candidate = HomepageCandidate(normalized_url=url, raw_url=url, anchor_text="Lines of Credit", source_type="html", origin="verified_coverage_source", heuristic_score=5, supporting_signal=False, seed_source_id=None, source_name_hint=None, priority_hint=None, expected_fields_hint=[])
        ai = AiParallelCandidateScore(candidate_url=url, predicted_role="detail", relevance_score=9, confidence_band="high", reason_codes=["product_type_semantic_match"], short_rationale="Coverage page")
        evidence = PageEvidenceAssessment(page_evidence_score=3, page_evidence_reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"], page_title="Loans", primary_heading="Loans", heading_match=False, attribute_signal_count=2, negative_signal_count=0)
        with patch("api_service.source_catalog._score_page_evidence", return_value=evidence):
            rows, rejected, notes = _promote_detail_candidates(bank_code="BANK", bank_name="Bank", country_code="CA", product_type="line-of-credit", discovery_product_type="line-of-credit", product_type_definition=_product_type_definition("line-of-credit"), source_language="en", fetch_policy=SimpleNamespace(), candidates=[candidate], ai_scores={url: ai})
        self.assertFalse(rows)
        self.assertIn(url, rejected)
        self.assertTrue(any("unresolved_product_boundary_before_collection" in note for note in notes))
