from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api_service.source_catalog import (
    AiParallelCandidateScore,
    AiParallelScoringResult,
    CatalogItemMaterializationResult,
    HomepageCandidate,
    HomepageSourceGenerationResult,
    PageEvidenceAssessment,
    _build_source_catalog_collection_plan,
    _build_homepage_self_candidate,
    _generate_sources_from_homepage,
    _generate_existing_detail_companion_rows,
    _materialize_sources_for_catalog_item,
    _launch_source_catalog_collection_runner,
    _candidate_promotes_to_detail,
    _deactivate_case_alias_generated_detail_sources,
    _deactivate_hard_scope_excluded_generated_detail_sources,
    _deactivate_rejected_generated_detail_sources,
    _dedupe_detail_rows_by_product_identity,
    _dedupe_generated_source_rows,
    _discover_detail_companion_links,
    _supporting_source_is_bounded_to_selected_details,
    _extract_allowed_links,
    _generate_bank_code,
    _has_excluded_link_signal,
    _authoritative_catalog_detail_bonus,
    _ai_supporting_source_is_relevant,
    _invoke_openai_parallel_scorer,
    _is_product_type_rate_page,
    _link_is_relevant_supporting_source,
    _looks_like_credit_card_detail_path,
    _looks_like_secondary_catalog_hub,
    _looks_like_javascript_shell,
    _normalize_country_code,
    _normalize_coverage_source_url,
    _ordered_detail_candidates,
    _page_is_audience_offer_hub,
    _promote_detail_candidates,
    _product_type_discovery_profile,
    _record_catalog_audit_event,
    _source_scope_exclusion_reason,
    _supporting_html_page_is_fetchable,
    _score_candidate_links_with_ai,
    _score_page_evidence,
    _score_product_link,
    _seed_supporting_hint_is_relevant,
    _suppress_family_overviews_when_named_details_exist,
    _upsert_source_registry_rows,
    _url_country_scope_conflicts,
    _url_locale_conflicts_source_language,
    create_bank_profile,
    delete_bank_profile,
    create_source_catalog_item,
    load_bank_list,
    normalize_bank_filters,
    repair_catalog_coverage_route,
    start_source_catalog_collection,
    update_bank_profile,
)
from api_service.errors import SourceRegistryError
from api_service.product_type_localization import localize_product_type_definition
from worker.discovery.fpds_discovery.url_utils import normalize_source_url


class _QueuedCursor:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.rowcount = int(payload) if isinstance(payload, int) else 0

    def fetchone(self) -> dict[str, object] | None:
        if isinstance(self.payload, list):
            return self.payload[0] if self.payload else None
        return self.payload if isinstance(self.payload, dict) else None

    def fetchall(self) -> list[dict[str, object]]:
        if isinstance(self.payload, list):
            return self.payload
        if isinstance(self.payload, dict):
            return [self.payload]
        return []


class _QueuedConnection:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object] | None = None) -> _QueuedCursor:
        self.calls.append((sql, params or {}))
        if not self._responses:
            raise AssertionError(f"Unexpected SQL call with no queued response left: {sql}")
        return _QueuedCursor(self._responses.pop(0))


def _product_type_definition(product_type_code: str) -> dict[str, object]:
    label = product_type_code.replace("-", " ").title()
    product_family = "lending" if product_type_code in {"credit-card", "mortgage", "personal-loan", "line-of-credit"} else "deposit"
    return {
        "product_type_code": product_type_code,
        "product_family": product_family,
        "display_name": label,
        "description": f"{label} product type",
        "status": "active",
        "managed_flag": True,
        "discovery_keywords": [product_type_code, label.lower()],
        "expected_fields": ["product_name", "notes"],
        "fallback_policy": "generic_ai_review",
    }


class SourceCatalogTests(unittest.TestCase):
    def test_homepage_generation_loads_browser_policy_without_widening_bank_domains(self) -> None:
        bounded_policy = SimpleNamespace(
            allowed_domains=("vancity.com",),
            browser_fallback_domains=("vancity.com", "www.vancity.com"),
        )
        with (
            patch(
                "api_service.source_catalog.DiscoveryFetchPolicy.from_env",
                return_value=bounded_policy,
            ) as policy_factory,
            patch("api_service.source_catalog.fetch_text", return_value="<html><body></body></html>") as fetch,
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch("api_service.source_catalog._load_seed_supporting_hints", return_value=[]),
        ):
            result = _generate_sources_from_homepage(
                bank_code="VANCITY",
                bank_name="Vancity",
                country_code="CA",
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
                homepage_url="https://www.vancity.com/",
                source_language="en",
            )

        policy_factory.assert_called_once_with(allowed_domains=("vancity.com",))
        self.assertIs(fetch.call_args.args[1], bounded_policy)
        self.assertEqual(result.detail_source_ids, [])

    def test_shared_bank_domain_rejects_explicit_other_country_route(self) -> None:
        self.assertTrue(
            _url_country_scope_conflicts(
                country_code="US",
                normalized_url="https://www.td.com/ca/en/personal-banking/products/checking",
            )
        )
        self.assertTrue(
            _url_country_scope_conflicts(
                country_code="CA",
                normalized_url="https://www.td.com/us/en/personal-banking/checking-accounts/beyond",
            )
        )
        self.assertFalse(
            _url_country_scope_conflicts(
                country_code="US",
                normalized_url="https://www.td.com/us/en/personal-banking/checking-accounts/beyond",
            )
        )
        self.assertFalse(
            _url_country_scope_conflicts(
                country_code="US",
                normalized_url="https://www.td.com/content/dam/tdb/document/pdf/personal-banking/dda-en.pdf",
            )
        )

    def test_us_discovery_localizes_checking_and_cd_without_mutating_canonical_codes(self) -> None:
        chequing = localize_product_type_definition(
            country_code="US",
            definition=_product_type_definition("chequing"),
        )
        gic = localize_product_type_definition(
            country_code="US",
            definition=_product_type_definition("gic"),
        )

        self.assertEqual(chequing["product_type_code"], "chequing")
        self.assertIn("checking account", chequing["discovery_keywords"])
        self.assertEqual(gic["product_type_code"], "gic")
        self.assertIn("certificate of deposit", gic["discovery_keywords"])

    def test_structured_deposit_shell_uses_route_identity_without_global_nav_penalty(self) -> None:
        definition = localize_product_type_definition(
            country_code="US",
            definition=_product_type_definition("savings"),
        )
        html = """
        <html><head><title>Example Bank Online</title></head><body>
          <nav>Sign in Compare Legal Terms and Conditions</nav>
          <script type="application/ld+json">
            {
              "name": "Savings Account",
              "description": "Earn interest on your balance with no monthly fee and flexible withdrawals."
            }
          </script>
        </body></html>
        """
        raw_url = "https://www.examplebank.com/banking/savings-account"
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url=raw_url,
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=definition,
            )

        candidate = HomepageCandidate(
            normalized_url=raw_url,
            raw_url=raw_url,
            anchor_text="Savings Accounts",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=raw_url,
            predicted_role="supporting_html",
            relevance_score=7.0,
            confidence_band="medium",
            reason_codes=["product_type_semantic_match", "hub_page_not_detail"],
            short_rationale="Official savings family route.",
        )

        self.assertEqual(evidence.negative_signal_count, 0)
        self.assertTrue(evidence.product_identity_match)
        self.assertIn("url_product_identity_signal", evidence.page_evidence_reason_codes)
        self.assertGreaterEqual(evidence.page_evidence_score, 4)
        self.assertTrue(
            _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            )
        )

    def test_us_localized_auto_loan_identity_promotes_other_bank_detail(self) -> None:
        definition = localize_product_type_definition(
            country_code="US",
            definition=_product_type_definition("personal-loan"),
        )
        html = """
        <html><head><title>Auto Loan Refinancing | Example Bank</title></head><body>
          <h1>Goodbye overpaying. Hello refinancing.</h1>
          <nav>Sign in Compare Legal Terms and Conditions</nav>
          <script type="application/json">
            {"description": "Refinance an auto loan with a fixed interest rate, monthly payment, term, and repayment details."}
          </script>
        </body></html>
        """
        raw_url = "https://www.examplebank.com/auto-financing/refinance"
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url=raw_url,
                fetch_policy=SimpleNamespace(),
                product_type="personal-loan",
                product_type_definition=definition,
            )

        candidate = HomepageCandidate(
            normalized_url=raw_url,
            raw_url=raw_url,
            anchor_text="Auto refinancing",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=4,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=raw_url,
            predicted_role="detail",
            relevance_score=8.5,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="Official auto-loan refinancing product page.",
        )

        self.assertTrue(evidence.product_identity_match)
        self.assertIn("title_semantic_match", evidence.page_evidence_reason_codes)
        self.assertEqual(evidence.negative_signal_count, 0)
        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_high_confidence_structured_product_route_can_survive_unrendered_body(self) -> None:
        html = """
        <html><head><title>Mortgage Loans | Example Bank</title></head><body>
          <script type="application/json">{"description": "official product content"}</script>
        </body></html>
        """
        raw_url = "https://www.examplebank.com/borrow/home"
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url=raw_url,
                fetch_policy=SimpleNamespace(),
                product_type="mortgage",
                product_type_definition=_product_type_definition("mortgage"),
            )

        candidate = HomepageCandidate(
            normalized_url=raw_url,
            raw_url=raw_url,
            anchor_text="Home mortgage",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=raw_url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="Official mortgage product route.",
        )

        self.assertEqual(evidence.page_evidence_score, 3)
        self.assertIn("structured_component_evidence", evidence.page_evidence_reason_codes)
        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_location_gate_can_use_structured_product_evidence_without_promoting_a_family_hub(self) -> None:
        structured_payload = json.dumps(
            {
                "title": "Advantage Savings",
                "content": "<p>$8 monthly fee. Earn interest compounded daily.</p>",
            }
        )
        html = (
            "<html><head><title>Advantage Savings | Example Bank</title></head><body>"
            "<h1>Please select your county</h1><p>Enter your ZIP code.</p>"
            f"<div data-product='{structured_payload}'></div></body></html>"
        )
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url="https://www.bank.example/deposits/savings/advantage-savings/",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )

        candidate = HomepageCandidate(
            normalized_url="https://www.bank.example/deposits/savings/advantage-savings",
            raw_url="https://www.bank.example/deposits/savings/advantage-savings/",
            anchor_text="Advantage Savings",
            source_type="html",
            origin="verified_coverage_source",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint="Advantage Savings",
            priority_hint="P1",
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=candidate.normalized_url,
            predicted_role="supporting_html",
            relevance_score=7.0,
            confidence_band="medium",
            reason_codes=["hub_page_not_detail", "not_product_detail"],
            short_rationale="The visible page is location gated.",
        )

        self.assertIn("location_access_gate", evidence.page_evidence_reason_codes)
        self.assertIn("structured_component_evidence", evidence.page_evidence_reason_codes)
        self.assertNotIn("multi_product_family_overview", evidence.page_evidence_reason_codes)
        self.assertTrue(
            _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            ),
            evidence,
        )

    def test_us_cd_location_gate_uses_localized_identity_terms(self) -> None:
        definition = localize_product_type_definition(
            country_code="US",
            definition=_product_type_definition("gic"),
        )
        structured_payload = json.dumps(
            {
                "title": "Bank of America Certificates of Deposit",
                "content": (
                    "<p>Open a CD with a $1,000 minimum opening deposit. "
                    "Choose a fixed term and view the annual percentage yield.</p>"
                ),
            }
        )
        html = (
            "<html><head><title>Certificate of Deposit - View CD Rates and Account Options</title></head><body>"
            "<h1>Please select your county</h1><p>Enter your ZIP code.</p>"
            f"<div data-product='{structured_payload}'></div></body></html>"
        )
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url="https://www.bank.example/deposits/bank-cds/cd-accounts/",
                fetch_policy=SimpleNamespace(),
                product_type="gic",
                product_type_definition=definition,
            )

        candidate = HomepageCandidate(
            normalized_url="https://www.bank.example/deposits/bank-cds/cd-accounts",
            raw_url="https://www.bank.example/deposits/bank-cds/cd-accounts/",
            anchor_text="Certificate of Deposit (CD)",
            source_type="html",
            origin="verified_coverage_source",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint="Certificate of Deposit (CD)",
            priority_hint="P1",
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=candidate.normalized_url,
            predicted_role="detail",
            relevance_score=10.0,
            confidence_band="high",
            reason_codes=["named_product_detail"],
            short_rationale="Official Certificate of Deposit product page.",
        )

        self.assertTrue(evidence.product_identity_match, evidence)
        self.assertIn("title_semantic_match", evidence.page_evidence_reason_codes)
        self.assertTrue(
            _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            ),
            evidence,
        )

    def test_only_verified_coverage_can_relax_location_gate_page_score(self) -> None:
        url = "https://www.bank.example/deposits/savings/savings-accounts"
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="supporting_html",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["hub_page_not_detail", "not_product_detail"],
            short_rationale="Official location-gated savings coverage page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=4,
            page_evidence_reason_codes=[
                "product_identity_signal",
                "structured_component_evidence",
                "location_access_gate",
                "title_semantic_match",
                "product_type_semantic_match",
                "pricing_or_feature_signal",
                "insufficient_evidence",
            ],
            page_title="Open a Bank of America Advantage Savings Account Online",
            primary_heading="Please select your county",
            heading_match=False,
            attribute_signal_count=2,
            negative_signal_count=1,
            product_identity_match=True,
        )

        def candidate(origin: str) -> HomepageCandidate:
            return HomepageCandidate(
                normalized_url=url,
                raw_url=f"{url}/",
                anchor_text="Savings account",
                source_type="html",
                origin=origin,
                heuristic_score=5,
                supporting_signal=False,
                seed_source_id=None,
                source_name_hint=None,
                priority_hint=None,
                expected_fields_hint=[],
            )

        self.assertTrue(
            _candidate_promotes_to_detail(
                candidate=candidate("verified_coverage_source"),
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            )
        )
        self.assertFalse(
            _candidate_promotes_to_detail(
                candidate=candidate("homepage_or_hub_link"),
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            )
        )

    def test_unreachable_supporting_html_is_excluded_before_collection(self) -> None:
        url = "https://www.bank.example/en/home-ownership/stale-article"
        unavailable = PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["page_fetch_unavailable"],
            page_title=None,
            primary_heading=None,
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=0,
            fetch_error="HTTP fetch failed with status 404",
        )
        cache = {url: unavailable}

        with patch("api_service.source_catalog._score_page_evidence") as scorer:
            self.assertFalse(
                _supporting_html_page_is_fetchable(
                    normalized_url=url,
                    raw_url=url,
                    fetch_policy=SimpleNamespace(),
                    product_type="mortgage",
                    product_type_definition=_product_type_definition("mortgage"),
                    page_evidence_by_url=cache,
                )
            )
            scorer.assert_not_called()

    def test_country_code_requires_iso_alpha_2_shape(self) -> None:
        self.assertEqual(_normalize_country_code(" us "), "US")
        with self.assertRaises(SourceRegistryError) as captured:
            _normalize_country_code("Canada")
        self.assertEqual(captured.exception.code, "invalid_country_code")

    def test_seed_supporting_hints_remain_subject_to_current_scope_policy(self) -> None:
        definition = _product_type_definition("gic")
        self.assertFalse(
            _seed_supporting_hint_is_relevant(
                product_type="gic",
                discovery_product_type=None,
                product_type_definition=definition,
                hint={
                    "source_url": "https://www.examplebank.ca/investments/gic-calculator/",
                    "source_name": "GIC calculator",
                    "purpose": "Estimate GIC growth",
                    "expected_fields": ["gic_rate_table"],
                },
            )
        )
        self.assertFalse(
            _seed_supporting_hint_is_relevant(
                product_type="gic",
                discovery_product_type=None,
                product_type_definition=definition,
                hint={
                    "source_url": "https://www.examplebank.ca/open-an-investment?productCode=gic",
                    "source_name": "Open an investment",
                    "purpose": "Application flow",
                },
            )
        )
        self.assertTrue(
            _seed_supporting_hint_is_relevant(
                product_type="gic",
                discovery_product_type=None,
                product_type_definition=definition,
                hint={
                    "source_url": "https://www.examplebank.ca/investments/gic-rates/",
                    "source_name": "GIC rates",
                    "purpose": "Official GIC rate table",
                    "expected_fields": ["gic_rate_table"],
                },
            )
        )

    def test_seed_supporting_hints_reject_branded_blog_paths(self) -> None:
        definition = _product_type_definition("gic")
        self.assertFalse(
            _seed_supporting_hint_is_relevant(
                product_type="gic",
                discovery_product_type=None,
                product_type_definition=definition,
                hint={
                    "source_url": "https://www.examplebank.ca/oaken-blog/why-invest-in-a-gic/",
                    "source_name": "Example Bank GIC article",
                    "purpose": "Supporting GIC information",
                    "expected_fields": ["gic_rate_table"],
                },
            )
        )

    def test_product_specific_personal_path_can_remain_supporting_evidence(self) -> None:
        definition = _product_type_definition("gic")
        self.assertTrue(
            _seed_supporting_hint_is_relevant(
                product_type="gic",
                discovery_product_type=None,
                product_type_definition=definition,
                hint={
                    "source_url": "https://www.examplebank.ca/en-ca/personal/",
                    "source_name": "Personal non-registered GICs",
                    "purpose": "Official personal GIC product information",
                    "expected_fields": ["gic_rate_table"],
                },
            )
        )

    def test_deposit_supporting_filter_rejects_mutual_fund_governance_pdf(self) -> None:
        definition = _product_type_definition("gic")
        self.assertFalse(
            _link_is_relevant_supporting_source(
                product_type="gic",
                product_type_definition=definition,
                normalized_url=(
                    "https://www.examplebank.ca/content/dam/investments/pdfs/mutual_funds/"
                    "reporting_and_governance/fund-amendment.pdf"
                ),
                anchor_text="Investment reporting and governance amendment",
            )
        )

    def test_link_exclusion_does_not_reject_product_copy_containing_offers(self) -> None:
        self.assertFalse(
            _has_excluded_link_signal(
                normalized_url="https://www.examplebank.ca/mortgages/fixed-rate",
                anchor_text="Fixed-rate mortgage offers stable payments through the term of your mortgage.",
            )
        )

    def test_link_exclusion_still_rejects_action_and_promotion_flows(self) -> None:
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://www.examplebank.ca/mortgages/apply",
                anchor_text="Start your mortgage application",
            )
        )

    def test_ai_supporting_source_rejects_low_relevance_general_advice(self) -> None:
        self.assertFalse(
            _ai_supporting_source_is_relevant(
                AiParallelCandidateScore(
                    candidate_url="https://www.examplebank.ca/advice",
                    predicted_role="supporting_html",
                    relevance_score=1.0,
                    confidence_band="medium",
                    reason_codes=["insufficient_evidence"],
                    short_rationale="General advice with no named product facts.",
                )
            )
        )
        self.assertTrue(
            _ai_supporting_source_is_relevant(
                AiParallelCandidateScore(
                    candidate_url="https://www.examplebank.ca/savings/rates",
                    predicted_role="supporting_html",
                    relevance_score=7.0,
                    confidence_band="high",
                    reason_codes=["supporting_terms_or_rates_page", "pricing_or_feature_signal"],
                    short_rationale="Official current savings rate table.",
                )
            )
        )

    def test_calculator_is_not_collected_as_product_supporting_evidence(self) -> None:
        self.assertFalse(
            _link_is_relevant_supporting_source(
                product_type="gic",
                product_type_definition=_product_type_definition("gic"),
                normalized_url="https://www.examplebank.ca/investments/calculators/gic-calculator.html",
                anchor_text="GIC calculator",
            )
        )

    def test_servicing_and_editorial_pages_are_not_supporting_product_evidence(self) -> None:
        definition = _product_type_definition("credit-card")
        for path, anchor_text in (
            ("credit-cards/activate-your-credit-card.html", "Activate your credit card"),
            ("credit-cards/manage-your-credit-card/welcome-kits.html", "Credit card welcome kits"),
            ("digital-banking-guide/credit-cards.html", "Digital banking guide - credit cards"),
            ("advice-plus/posts/student-credit-cards.html", "Student credit card advice"),
        ):
            with self.subTest(path=path):
                self.assertFalse(
                    _link_is_relevant_supporting_source(
                        product_type="credit-card",
                        product_type_definition=definition,
                        normalized_url=f"https://www.examplebank.ca/{path}",
                        anchor_text=anchor_text,
                    )
                )

    def test_onboarding_and_forms_repositories_are_not_product_evidence(self) -> None:
        definition = _product_type_definition("gic")
        for url, anchor_text in (
            (
                "https://www.examplebank.ca/banking/join-bank/international-student-gic.html",
                "International student GIC application",
            ),
            ("https://www.examplebank.ca/forms-downloads.html", "Investment forms and downloads"),
        ):
            with self.subTest(url=url):
                self.assertFalse(
                    _link_is_relevant_supporting_source(
                        product_type="gic",
                        product_type_definition=definition,
                        normalized_url=url,
                        anchor_text=anchor_text,
                    )
                )

    def test_gic_editorial_and_investment_fund_pages_are_not_supporting_evidence(self) -> None:
        definition = _product_type_definition("gic")
        for url, anchor_text in (
            (
                "https://www.examplebank.ca/en/thejuice/save/a-beginners-guide-to-gics",
                "A beginner's guide to GICs",
            ),
            (
                "https://www.examplebank.ca/en/personal/invest/non-registered-funds",
                "Non-registered investment funds and GIC options",
            ),
        ):
            with self.subTest(url=url):
                self.assertFalse(
                    _link_is_relevant_supporting_source(
                        product_type="gic",
                        product_type_definition=definition,
                        normalized_url=url,
                        anchor_text=anchor_text,
                    )
                )

    def test_audience_offer_landing_page_is_not_a_second_product_detail(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="savings",
                fingerprint=(
                    "https://www.examplebank.ca/en/young-adults/saving-accounts.html "
                    "Saving Account Offer for Young Adults Step into your saving era with 4.50% interest"
                ),
            ),
            "non_product_service_flow",
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="chequing",
                fingerprint=(
                    "https://www.examplebank.ca/en/young-adults/student-chequing.html "
                    "Student Chequing Account"
                ),
            )
        )
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://www.examplebank.ca/mortgages/fixed-rate",
                anchor_text="Apply now",
            )
        )
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://www.examplebank.ca/open-an-investment?productCode=gic-non-reg",
                anchor_text="Open an investment",
            )
        )
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://www.examplebank.ca/open-an-account",
                anchor_text="",
            )
        )
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://hello.examplebank.ca/lending/prequalification",
                anchor_text="Start your application for a personal line of credit",
            )
        )

    def test_editorial_resource_page_is_out_of_product_candidate_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="mortgage",
                fingerprint="https://www.examplebank.ca/mortgages/resource-centre/how-refinancing-works",
            ),
            "non_product_editorial_page",
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="mortgage",
                fingerprint="https://www.examplebank.ca/mortgages/refinance-mortgage",
            )
        )

    def test_climate_report_pdf_is_not_product_supporting_evidence(self) -> None:
        self.assertTrue(
            _has_excluded_link_signal(
                normalized_url="https://annualreport.examplebank.ca/_doc/Example-2024-Climate-Report.pdf",
                anchor_text="2024 Climate Report",
            )
        )

    def test_singular_article_route_is_out_of_product_candidate_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint=(
                    "https://www.examplebank.com/personal/investments/learning-and-insights/article/"
                    "strategic-moves-for-cd-maturities Certificate of deposit maturity strategies"
                ),
            ),
            "non_product_editorial_page",
        )

    def test_product_identity_terms_override_sibling_route_vocabulary(self) -> None:
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="line-of-credit",
                fingerprint=(
                    "https://www.examplebank.com/personal/mortgage/refinance/equity "
                    "We offer a home equity line of credit (HELOC)."
                ),
            )
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint=(
                    "https://www.examplebank.com/personal/savings/bank-cd "
                    "Open a certificate of deposit with a fixed term."
                ),
            )
        )
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="line-of-credit",
                fingerprint="https://www.examplebank.com/personal/mortgage/jumbo Jumbo mortgage",
            ),
            "other_product_type",
        )

    def test_us_cd_detail_slug_overrides_savings_parent_route(self) -> None:
        for slug in ("high-yield-cds", "no-penalty-cd", "cd-rates"):
            with self.subTest(slug=slug):
                self.assertIsNone(
                    _source_scope_exclusion_reason(
                        product_type="gic",
                        fingerprint=(
                            f"https://www.examplebank.com/us/en/savings/{slug} "
                            "Certificate of Deposit rates and terms"
                        ),
                    )
                )

        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint=(
                    "https://www.examplebank.com/us/en/savings/high-yield-savings "
                    "High-Yield Savings Account"
                ),
            ),
            "other_product_type",
        )

    def test_mortgage_scope_rejects_heloc_even_below_mortgage_route(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="mortgage",
                fingerprint=(
                    "https://www.examplebank.com/personal/mortgage/home-equity-line-of-credit "
                    "Home Equity Line of Credit (HELOC)"
                ),
            ),
            "other_product_type",
        )

    def test_educational_slug_patterns_are_out_of_product_scope(self) -> None:
        for path in (
            "savings-accounts/what-is-a-savings-account",
            "savings-accounts/what-are-the-different-types-of-savings-accounts",
            "savings-accounts/how-does-interest-work-on-a-savings-account",
            "savings-accounts/how-to-choose-the-best-savings-account-for-me",
            "bank-accounts/chequing-vs-savings-account",
            "savings-accounts/rules-of-savings",
            "bank-accounts/getting-started",
            "savings-accounts/emergency-fund",
            "bank-accounts/multiple-bank-accounts",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    _source_scope_exclusion_reason(
                        product_type="savings",
                        fingerprint=f"https://www.examplebank.ca/{path} savings account guide",
                    ),
                    "non_product_editorial_page",
                )

    def test_relationship_rewards_program_is_not_savings_or_gic_evidence(self) -> None:
        for product_type in ("savings", "gic"):
            with self.subTest(product_type=product_type):
                self.assertEqual(
                    _source_scope_exclusion_reason(
                        product_type=product_type,
                        fingerprint="https://www.examplebank.ca/bank-accounts/value-program.html rewards and fee rebates",
                    ),
                    "other_product_type",
                )

        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="chequing",
                fingerprint="https://www.examplebank.ca/bank-accounts/value-program.html monthly fee rebate",
            )
        )

    def test_explicit_deposit_product_slug_outranks_shared_navigation_copy(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="savings",
                fingerprint=(
                    "https://www.examplebank.ca/en/bank-accounts/no-fee-chequing.html "
                    "No Fee Chequing Account navigation High Interest Savings"
                ),
            ),
            "other_product_type",
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="savings",
                fingerprint=(
                    "https://www.examplebank.ca/en/bank-accounts/high-interest-savings.html "
                    "High Interest Savings Account navigation No Fee Chequing"
                ),
            )
        )

    def test_explicit_deposit_route_rejects_other_product_application(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="savings",
                fingerprint=(
                    "https://www.examplebank.com/personal-banking/checking-accounts/apply/essential "
                    "Example Savings APY is 3.25%."
                ),
            ),
            "other_product_type",
        )

    def test_savings_and_gic_exclude_generic_transfer_and_mutual_fund_support(self) -> None:
        for product_type, url, expected in (
            ("savings", "https://www.examplebank.ca/en/banking/e-transfer.html", "non_product_service_flow"),
            ("gic", "https://www.examplebank.ca/en/global-money-transfer.html", "non_product_service_flow"),
            ("savings", "https://www.examplebank.ca/en/overlays/mutual-funds-types.html", "other_product_type"),
        ):
            with self.subTest(product_type=product_type, url=url):
                self.assertEqual(
                    _source_scope_exclusion_reason(product_type=product_type, fingerprint=url),
                    expected,
                )

    def test_mortgage_management_flow_is_out_of_product_candidate_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="mortgage",
                fingerprint="https://www.examplebank.ca/mortgages/switch-mortgage.html",
            ),
            "non_product_service_flow",
        )

    def test_internal_shadow_site_is_out_of_public_product_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="savings",
                fingerprint=(
                    "https://www.examplebank.ca/content/internal/ca/en/shadow-site/"
                    "personal/bank-accounts/services.html"
                ),
            ),
            "non_product_service_flow",
        )

    def test_internal_cms_product_alias_is_out_of_public_product_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="chequing",
                fingerprint=(
                    "https://www.examplebank.ca/content/site/ca/en/personal/bank-accounts/"
                    "chequing-accounts/preferred-package.html"
                ),
            ),
            "non_product_service_flow",
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="chequing",
                fingerprint="https://www.examplebank.ca/content/dam/legal/chequing-terms.pdf",
            )
        )

    def test_commercial_product_page_is_out_of_retail_candidate_scope(self) -> None:
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint="https://www.examplebank.ca/en-ca/commercial/ Oaken Commercial GICs",
            ),
            "non_consumer_business_page",
        )
        for fingerprint in (
            "https://www.examplebank.ca/credit-cards/all-credit-cards/corporate-classic-plus-card.html Corporate Classic Plus Visa Card",
            "https://www.examplebank.ca/credit-cards/all-credit-cards/bizline-visa-card.html CIBC bizline Visa Card",
        ):
            with self.subTest(fingerprint=fingerprint):
                self.assertEqual(
                    _source_scope_exclusion_reason(
                        product_type="credit-card",
                        fingerprint=fingerprint,
                    ),
                    "non_consumer_business_page",
                )

    def test_authoritative_card_catalog_details_receive_budget_priority(self) -> None:
        detail_url = "https://www.examplebank.ca/credit-cards/all-credit-cards/dividend-visa-card.html"
        entry_url = "https://www.examplebank.ca/credit-cards/all-credit-cards.html"
        base_score = 8

        self.assertEqual(
            _authoritative_catalog_detail_bonus(
                product_type="credit-card",
                normalized_url=detail_url,
                base_score=base_score,
                parent_url=entry_url,
                seed_entry_url=entry_url,
            ),
            6,
        )
        self.assertEqual(
            _authoritative_catalog_detail_bonus(
                product_type="credit-card",
                normalized_url=detail_url,
                base_score=base_score,
                parent_url="https://www.examplebank.ca/credit-cards/cash-back-cards.html",
                seed_entry_url=entry_url,
            ),
            0,
        )
        self.assertEqual(
            _authoritative_catalog_detail_bonus(
                product_type="credit-card",
                normalized_url="https://www.examplebank.ca/credit-cards/cash-back-cards.html",
                base_score=base_score,
                parent_url=entry_url,
                seed_entry_url=entry_url,
            ),
            0,
        )

    def test_javascript_shell_detection_requires_explicit_rendering_marker(self) -> None:
        self.assertTrue(
            _looks_like_javascript_shell(
                "<html><body><noscript>Please enable JavaScript to continue.</noscript><div id='app'></div></body></html>"
            )
        )
        self.assertFalse(
            _looks_like_javascript_shell(
                "<html><body><script src='/app.js'></script><h1>Everyday banking</h1></body></html>"
            )
        )

    def test_product_identifying_homepage_can_be_a_bounded_detail_candidate(self) -> None:
        candidate = _build_homepage_self_candidate(
            product_type="personal-loan",
            product_type_definition={
                **_product_type_definition("personal-loan"),
                "discovery_keywords": ["personal loan", "secured loan", "unsecured loan"],
            },
            homepage_url="https://www.examplebank.ca/",
            normalized_homepage_url="https://www.examplebank.ca/",
            homepage_html=(
                "<html><head><title>Personal loans for Canadians</title></head>"
                "<body><h1>Secured and unsecured personal loans</h1></body></html>"
            ),
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.origin, "homepage_self_detail_candidate")
        self.assertEqual(candidate.normalized_url, "https://www.examplebank.ca/")

    def test_unrelated_homepage_is_not_a_detail_candidate(self) -> None:
        candidate = _build_homepage_self_candidate(
            product_type="mortgage",
            product_type_definition=_product_type_definition("mortgage"),
            homepage_url="https://www.examplebank.ca/",
            normalized_homepage_url="https://www.examplebank.ca/",
            homepage_html="<html><head><title>Welcome to Example Bank</title></head><body><h1>Banking made simple</h1></body></html>",
        )

        self.assertIsNone(candidate)

    def test_term_specific_gic_homepage_promo_is_not_a_detail_candidate(self) -> None:
        candidate = _build_homepage_self_candidate(
            product_type="gic",
            product_type_definition=_product_type_definition("gic"),
            homepage_url="https://www.examplebank.ca/",
            normalized_homepage_url="https://www.examplebank.ca/",
            homepage_html=(
                "<html><head><title>1 Year GIC | Example Bank</title></head>"
                "<body><h1>Earn more with our 1 Year GIC</h1></body></html>"
            ),
        )

        self.assertIsNone(candidate)

    def test_detail_identity_dedupe_collapses_locale_aliases(self) -> None:
        base = {
            "bank_code": "B2B",
            "product_type": "gic",
            "source_type": "html",
            "discovery_role": "detail",
            "priority": "P1",
            "seed_source_flag": False,
            "discovery_metadata": {
                "product_identity_match": True,
                "page_title": "B2B Bank | Short Term GICs",
                "primary_heading": "Short Term GICs",
            },
        }
        rows = [
            {
                **base,
                "source_id": "AUTO-B2B-GIC-A",
                "source_url": "https://b2bbank.com/en/deposits/short-term-gics",
                "normalized_url": "https://b2bbank.com/en/deposits/short-term-gics",
                "alias_urls": [],
            },
            {
                **base,
                "source_id": "AUTO-B2B-GIC-B",
                "source_url": "https://www.b2bbank.com/deposits/short-term-gics",
                "normalized_url": "https://www.b2bbank.com/deposits/short-term-gics",
                "alias_urls": [],
            },
        ]

        deduped, duplicate_urls = _dedupe_detail_rows_by_product_identity(rows)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(len(duplicate_urls), 1)
        self.assertIn(duplicate_urls[0], deduped[0]["alias_urls"])

    def test_detail_identity_dedupe_collapses_retired_url_returning_same_product(self) -> None:
        base = {
            "bank_code": "BANK",
            "product_type": "chequing",
            "source_type": "html",
            "discovery_role": "detail",
            "priority": "P1",
            "seed_source_flag": False,
            "discovery_metadata": {
                # A retired product URL can return the replacement product even
                # when the seed-name/type scorer no longer recognizes the URL.
                "product_identity_match": False,
                "page_title": "Smart Account | Example Bank",
                "primary_heading": "Smart Account",
                "attribute_signal_count": 4,
                "negative_signal_count": 0,
                "page_evidence_reason_codes": ["pricing_or_feature_signal"],
            },
        }
        rows = [
            {
                **base,
                "source_id": "AUTO-BANK-CHQ-A",
                "source_url": "https://example.test/accounts/smart-account",
                "normalized_url": "https://example.test/accounts/smart-account",
                "alias_urls": [],
            },
            {
                **base,
                "source_id": "AUTO-BANK-CHQ-B",
                "source_url": "https://example.test/accounts/retired-plus-account",
                "normalized_url": "https://example.test/accounts/retired-plus-account",
                "alias_urls": [],
            },
        ]

        deduped, duplicate_urls = _dedupe_detail_rows_by_product_identity(rows)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(duplicate_urls, ["https://example.test/accounts/retired-plus-account"])
        self.assertIn(duplicate_urls[0], deduped[0]["alias_urls"])

    def test_final_generated_row_dedupe_rechecks_identical_returned_detail_identity(self) -> None:
        base = {
            "bank_code": "BANK",
            "product_type": "chequing",
            "source_type": "html",
            "discovery_role": "detail",
            "priority": "P0",
            "discovery_metadata": {
                "product_identity_match": False,
                "page_title": "Smart Account | Example Bank",
                "primary_heading": "Smart Account",
                "attribute_signal_count": 4,
                "negative_signal_count": 0,
                "page_evidence_reason_codes": ["pricing_or_feature_signal"],
            },
        }
        rows = [
            {**base, "source_id": "SMART", "source_url": "https://example.test/smart", "normalized_url": "https://example.test/smart", "alias_urls": []},
            {**base, "source_id": "SMART-PLUS", "source_url": "https://example.test/smart-plus", "normalized_url": "https://example.test/smart-plus", "alias_urls": []},
        ]

        deduped = _dedupe_generated_source_rows(rows)

        self.assertEqual(len(deduped), 1)
        self.assertIn("https://example.test/smart-plus", deduped[0]["alias_urls"])

    def test_locale_and_audience_offer_hubs_do_not_become_detail_products(self) -> None:
        self.assertTrue(
            _url_locale_conflicts_source_language(
                normalized_url="https://example.test/fr/comptes/compte-intelli",
                source_language="en",
            )
        )
        self.assertFalse(
            _url_locale_conflicts_source_language(
                normalized_url="https://example.test/ca/en/accounts/smart",
                source_language="en-CA",
            )
        )
        self.assertTrue(
            _page_is_audience_offer_hub(
                PageEvidenceAssessment(
                    page_evidence_score=4,
                    page_evidence_reason_codes=["product_type_semantic_match"],
                    page_title="CIBC Smart Account for Apprentices | CIBC",
                    primary_heading="Apprentice Banking Offers",
                    heading_match=False,
                    attribute_signal_count=4,
                    negative_signal_count=0,
                    product_identity_match=False,
                )
            )
        )

    def test_detail_identity_dedupe_keeps_weak_unconfirmed_pages_separate(self) -> None:
        base = {
            "bank_code": "BANK",
            "product_type": "chequing",
            "source_type": "html",
            "discovery_role": "detail",
            "priority": "P1",
            "seed_source_flag": False,
            "discovery_metadata": {
                "product_identity_match": False,
                "page_title": "Banking offer | Example Bank",
                "primary_heading": "Banking offer",
                "attribute_signal_count": 1,
                "negative_signal_count": 0,
                "page_evidence_reason_codes": ["pricing_or_feature_signal"],
            },
            "alias_urls": [],
        }
        rows = [
            {**base, "source_id": "A", "source_url": "https://example.test/a", "normalized_url": "https://example.test/a"},
            {**base, "source_id": "B", "source_url": "https://example.test/b", "normalized_url": "https://example.test/b"},
        ]

        deduped, duplicate_urls = _dedupe_detail_rows_by_product_identity(rows)

        self.assertEqual(len(deduped), 2)
        self.assertEqual(duplicate_urls, [])

    def test_detail_identity_dedupe_keeps_generic_strong_pages_separate(self) -> None:
        base = {
            "bank_code": "BANK",
            "product_type": "chequing",
            "source_type": "html",
            "discovery_role": "detail",
            "priority": "P1",
            "seed_source_flag": False,
            "discovery_metadata": {
                "product_identity_match": False,
                "page_title": "Personal Chequing Account | Bank",
                "primary_heading": "Personal Chequing Account",
                "attribute_signal_count": 4,
                "negative_signal_count": 0,
                "page_evidence_reason_codes": ["pricing_or_feature_signal"],
            },
            "alias_urls": [],
        }
        rows = [
            {**base, "source_id": "A", "source_url": "https://example.test/a", "normalized_url": "https://example.test/a"},
            {**base, "source_id": "B", "source_url": "https://example.test/b", "normalized_url": "https://example.test/b"},
        ]

        deduped, duplicate_urls = _dedupe_detail_rows_by_product_identity(rows)

        self.assertEqual(len(deduped), 2)
        self.assertEqual(duplicate_urls, [])

    def test_family_overview_becomes_supporting_when_named_details_exist(self) -> None:
        family = {
            "normalized_url": "https://example.test/gics",
            "discovery_metadata": {
                "page_evidence_reason_codes": ["product_identity_signal"],
                "ai_predicted_role": "supporting_html",
                "ai_reason_codes": ["product_type_semantic_match", "hub_page_not_detail"],
            },
        }
        named = {
            "normalized_url": "https://example.test/gics/non-redeemable",
            "discovery_metadata": {"page_evidence_reason_codes": ["product_identity_signal"]},
        }

        retained, suppressed_urls = _suppress_family_overviews_when_named_details_exist([family, named])

        self.assertEqual(retained, [named])
        self.assertEqual(suppressed_urls, ["https://example.test/gics"])

    def test_family_overview_remains_fallback_without_named_details(self) -> None:
        family = {
            "normalized_url": "https://example.test/gics",
            "discovery_metadata": {"page_evidence_reason_codes": ["multi_product_family_overview"]},
        }

        retained, suppressed_urls = _suppress_family_overviews_when_named_details_exist([family])

        self.assertEqual(retained, [family])
        self.assertEqual(suppressed_urls, [])

    def test_verified_seed_detail_survives_cross_sell_family_overview_signal(self) -> None:
        named_seed = {
            "bank_code": "VANCITY",
            "product_type": "gic",
            "normalized_url": "https://www.vancity.com/invest/term-deposit-gic/escalating",
            "discovery_metadata": {
                "candidate_origin": "seed_detail_hint",
                "product_identity_match": True,
                "page_evidence_score": 10,
                "negative_signal_count": 0,
                "page_evidence_reason_codes": [
                    "product_identity_signal",
                    "multi_product_family_overview",
                ],
            },
        }
        other_named = {
            "normalized_url": "https://www.vancity.com/invest/term-deposit-gic/impact-term-deposit",
            "discovery_metadata": {"page_evidence_reason_codes": ["product_identity_signal"]},
        }

        retained, suppressed_urls = _suppress_family_overviews_when_named_details_exist(
            [named_seed, other_named]
        )

        self.assertEqual(
            retained[0]["discovery_metadata"]["page_evidence_reason_codes"],
            ["product_identity_signal"],
        )
        self.assertNotIn(
            "multi_product_family_overview",
            retained[0]["discovery_metadata"]["selection_reason_codes"],
        )
        self.assertEqual(retained[1], other_named)
        self.assertEqual(suppressed_urls, [])

    def test_verified_vancity_loc_keeps_real_multi_option_boundary_signal(self) -> None:
        loc_seed = {
            "bank_code": "VANCITY",
            "product_type": "line-of-credit",
            "normalized_url": "https://www.vancity.com/borrow/loans-lines-of-credit/line-of-credit",
            "discovery_metadata": {
                "candidate_origin": "seed_detail_hint",
                "product_identity_match": True,
                "page_evidence_score": 10,
                "negative_signal_count": 0,
                "selection_reason_codes": ["multi_product_family_overview"],
                "page_evidence_reason_codes": ["multi_product_family_overview"],
            },
        }

        retained, suppressed_urls = _suppress_family_overviews_when_named_details_exist([loc_seed])

        self.assertEqual(retained, [loc_seed])
        self.assertIn(
            "multi_product_family_overview",
            retained[0]["discovery_metadata"]["selection_reason_codes"],
        )
        self.assertEqual(suppressed_urls, [])

    def test_extract_allowed_links_accepts_www_and_apex_aliases_only(self) -> None:
        html = """
        <a href="https://bridgewaterbank.ca/personal/savings">Savings</a>
        <a href="https://www.bridgewaterbank.ca/personal/gic">GIC</a>
        <a href="https://bridgewaterbank.ca.evil.example/phish">Bad</a>
        """

        links = _extract_allowed_links(
            html_text=html,
            base_url="https://www.bridgewaterbank.ca/",
            hostname="www.bridgewaterbank.ca",
        )

        self.assertEqual(
            [item.normalized_url for item in links],
            [
                "https://bridgewaterbank.ca/personal/savings",
                "https://www.bridgewaterbank.ca/personal/gic",
            ],
        )

    def test_confirmed_product_identity_can_override_navigation_negative_terms(self) -> None:
        url = "https://www.examplebank.ca/en/personal/mortgages/refinance"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="Refinance your mortgage",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="detail",
            relevance_score=8.0,
            confidence_band="high",
            reason_codes=["named_product_detail"],
            short_rationale="A named consumer mortgage detail page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match"],
            page_title="Refinance your mortgage",
            primary_heading="Refinance your mortgage",
            heading_match=True,
            attribute_signal_count=2,
            negative_signal_count=3,
            product_identity_match=True,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_high_confidence_identity_can_override_low_whole_page_score(self) -> None:
        url = "https://www.examplebank.ca/personal-banking/investments/gics"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="Guaranteed Investment Certificates",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=4,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["named_product_detail"],
            short_rationale="Official GIC product page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=2,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match", "pricing_or_feature_signal"],
            page_title="Guaranteed Investment Certificates",
            primary_heading="Lock in your GIC rate",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=2,
            product_identity_match=True,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_high_confidence_named_card_survives_trademark_mojibake_and_nav_noise(self) -> None:
        url = "https://www.examplebank.ca/credit-cards/visa/student-no-fee-card.html"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="Student no-fee Visa card",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="detail",
            relevance_score=9.5,
            confidence_band="high",
            reason_codes=["named_product_detail"],
            short_rationale="Official named credit-card detail page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
            page_title="Scotia Momentum No-Fee Visa Card (for students)",
            primary_heading="Scotia Momentum㈢ No-Fee Visa* Card (for students)",
            heading_match=False,
            attribute_signal_count=1,
            negative_signal_count=2,
            product_identity_match=False,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_high_confidence_singular_card_shell_is_kept_for_downstream_rendering(self) -> None:
        url = "https://www.examplebank.ca/credit-cards/visa/student-value-card.html"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="Student Value Visa Card",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="detail",
            relevance_score=9.5,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "named_product_detail"],
            short_rationale="Official named credit-card detail page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match", "product_type_semantic_match"],
            page_title="Student Value Visa Card | Example Bank",
            primary_heading="Student Value Visa Card",
            heading_match=True,
            attribute_signal_count=0,
            negative_signal_count=0,
            product_identity_match=True,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_high_confidence_override_keeps_scope_veto(self) -> None:
        url = "https://www.examplebank.ca/business-banking/gics"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="Business GICs",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=4,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["named_product_detail"],
            short_rationale="Business GIC page.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=2,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match", "non_consumer_business_page"],
            page_title="Business GICs",
            primary_heading="Business GICs",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=2,
            product_identity_match=True,
        )

        self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_deposit_family_overview_can_be_candidate_producing_source(self) -> None:
        url = "https://www.examplebank.ca/personal-banking/gics"
        candidate = HomepageCandidate(
            normalized_url=url,
            raw_url=url,
            anchor_text="GICs and GIC rates",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=True,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=url,
            predicted_role="supporting_html",
            relevance_score=8.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "hub_page_not_detail", "seed_hint_alignment"],
            short_rationale="Official GIC family overview.",
        )
        evidence = PageEvidenceAssessment(
            page_evidence_score=4,
            page_evidence_reason_codes=[
                "product_identity_signal",
                "title_semantic_match",
                "structured_component_evidence",
                "product_type_semantic_match",
                "pricing_or_feature_signal",
            ],
            page_title="GICs | Example Bank",
            primary_heading=None,
            heading_match=False,
            attribute_signal_count=2,
            negative_signal_count=0,
            product_identity_match=True,
        )

        self.assertTrue(
            _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=evidence,
                allow_family_overview=True,
            )
        )
        self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def _workspace_temp_path(self, name: str) -> Path:
        path = Path.cwd() / "tmp" / "test-source-catalog" / name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_score_product_link_uses_product_type_description_terms(self) -> None:
        product_type_definition = _product_type_definition("tfsa")
        product_type_definition["display_name"] = "TFSA"
        product_type_definition["discovery_keywords"] = []
        product_type_definition["description"] = "Tax free savings account with contribution room and withdrawal rules."

        score = _score_product_link(
            product_type="tfsa",
            product_type_definition=product_type_definition,
            normalized_url="https://www.atlasbank.ca/accounts/contribution-room",
            anchor_text="Contribution room details",
        )

        self.assertGreater(score, 0)

    def test_singular_card_paths_outrank_category_and_no_fee_is_not_supporting_identity(self) -> None:
        definition = _product_type_definition("credit-card")
        detail_url = "https://www.examplebank.ca/credit-cards/american-express/no-fee-amex-card.html"
        category_url = "https://www.examplebank.ca/credit-cards/no-annual-fee.html"

        detail_score = _score_product_link(
            product_type="credit-card",
            product_type_definition=definition,
            normalized_url=detail_url,
            anchor_text="No-Fee American Express Card",
        )
        category_score = _score_product_link(
            product_type="credit-card",
            product_type_definition=definition,
            normalized_url=category_url,
            anchor_text="No annual fee credit cards",
        )

        self.assertTrue(_looks_like_credit_card_detail_path(product_type="credit-card", normalized_url=detail_url))
        self.assertFalse(_looks_like_credit_card_detail_path(product_type="credit-card", normalized_url=category_url))
        self.assertGreater(detail_score, category_score)

    def test_lending_product_type_discovery_profiles_are_recognized(self) -> None:
        self.assertEqual(_product_type_discovery_profile("credit_card", _product_type_definition("credit-card")), "credit-card")
        self.assertEqual(_product_type_discovery_profile("mortgages", _product_type_definition("mortgage")), "mortgage")
        self.assertEqual(_product_type_discovery_profile("vehicle-loan", _product_type_definition("personal-loan")), "personal-loan")
        self.assertEqual(_product_type_discovery_profile("home-equity-loc", _product_type_definition("line-of-credit")), "line-of-credit")

    def test_credit_card_page_evidence_uses_lending_attribute_signals(self) -> None:
        detail_html = """
        <html>
          <head><title>Cash Back Credit Card</title></head>
          <body>
            <h1>Cash Back Credit Card</h1>
            <p>Earn cash back rewards with an annual fee and a purchase interest rate.</p>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/credit-cards/cash-back",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition={
                    **_product_type_definition("credit-card"),
                    "display_name": "Credit Card",
                    "description": "Credit cards with annual fee, rewards, cash back, and purchase interest details.",
                    "discovery_keywords": ["credit cards", "cash back", "annual fee"],
                },
            )

        self.assertGreaterEqual(result.page_evidence_score, 4)
        self.assertIn("pricing_or_feature_signal", result.page_evidence_reason_codes)

    def test_credit_card_page_evidence_rejects_mortgage_page(self) -> None:
        detail_html = """
        <html>
          <head><title>Mortgage Rates</title></head>
          <body>
            <h1>Mortgage Rates</h1>
            <p>Choose fixed rate or variable rate mortgage terms with amortization options.</p>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/mortgages/rates",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
            )

        self.assertIn("other_product_type", result.page_evidence_reason_codes)
        self.assertGreaterEqual(result.negative_signal_count, 2)

    def test_page_evidence_keeps_first_h1_as_primary_identity(self) -> None:
        detail_html = """
        <html><head><title>Example Savings Account</title></head><body>
          <h1>Example Savings Account</h1>
          <h1>Open an account today</h1>
          <p>Earn interest with no monthly fee.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/accounts/example-savings",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )

        self.assertEqual(result.primary_heading, "Example Savings Account")

    def test_product_titled_cross_sell_application_step_cannot_become_detail(self) -> None:
        detail_html = """
        <html><head><title>Growth Savings Account | Example Bank</title></head><body>
          <h1>Consider adding a Chequing account by selecting one of the products below:</h1>
          <p>No thanks, continue with my current application.</p>
          <h2>Unlimited Chequing Account</h2>
          <p>Monthly fee and account benefits.</p>
        </body></html>
        """
        raw_url = "https://www.examplebank.ca/accounts/bundles/growth-savings-account"
        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            evidence = _score_page_evidence(
                raw_url=raw_url,
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )

        self.assertIn("non_product_service_flow", evidence.page_evidence_reason_codes)
        candidate = HomepageCandidate(
            normalized_url=raw_url,
            raw_url=raw_url,
            anchor_text="Growth Savings Account",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=raw_url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="Title names a savings product.",
        )
        self.assertFalse(
            _candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence)
        )

    def test_generic_term_deposit_page_marks_multi_product_boundary(self) -> None:
        detail_html = """
        <html><head><title>Term Deposits | Example Bank</title></head><body>
          <h1>Term Deposits</h1>
          <h2>Long-Term Non-Redeemable Term Deposit</h2>
          <p>One to five year terms with a minimum deposit.</p>
          <h2>Long-Term Redeemable Term Deposit</h2>
          <p>Redeemable terms and rates.</p>
          <h2>Short-Term Redeemable Term Deposit</h2>
          <p>Terms from 30 to 365 days.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/investing/term-deposits",
                fetch_policy=SimpleNamespace(),
                product_type="gic",
                product_type_definition=_product_type_definition("gic"),
            )

        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_plural_bank_account_benefits_page_marks_chequing_multi_product_boundary(self) -> None:
        detail_html = """
        <html><head><title>Senior Benefits on Bank Accounts | Example Bank</title></head><body>
          <h1>Senior Benefits on Bank Accounts</h1>
          <h2>Smart Account</h2>
          <p>No monthly fee and unlimited transactions for eligible seniors.</p>
          <h2>Everyday Chequing Account</h2>
          <p>18 included transactions and a lower monthly fee.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/bank-accounts/senior-benefits",
                fetch_policy=SimpleNamespace(),
                product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
            )

        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_gic_category_list_marks_multi_product_boundary_without_secondary_headings(self) -> None:
        detail_html = """
        <html><head><title>Guaranteed-Return GICs | Example Bank</title></head><body>
          <h1>Guaranteed-Return GICs</h1>
          <p>Select Category</p>
          <ul>
            <li>Non-Redeemable GIC</li>
            <li>Redeemable GIC</li>
            <li>One-Year Cashable GIC</li>
            <li>RateAdvantage GIC</li>
            <li>U.S. Dollar Term Deposit</li>
            <li>Income Builder GIC</li>
          </ul>
          <p>Choose a term and minimum investment.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/investments/guaranteed-return-gics",
                fetch_policy=SimpleNamespace(),
                product_type="gic",
                product_type_definition=_product_type_definition("gic"),
            )

        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_plural_credit_card_category_marks_multi_product_boundary(self) -> None:
        detail_html = """
        <html><head><title>No Annual Fee Mastercard Credit Cards | Example Bank</title></head><body>
          <h1>No annual fee Mastercard credit cards</h1>
          <h2>Cashback Mastercard</h2>
          <p>No annual fee with cash back rewards.</p>
          <h2>Rewards Mastercard</h2>
          <p>No annual fee with travel rewards.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/credit-cards/no-fee",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
            )

        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

        candidate = HomepageCandidate(
            normalized_url="https://www.examplebank.ca/credit-cards/no-fee",
            raw_url="https://www.examplebank.ca/credit-cards/no-fee",
            anchor_text="No annual fee credit cards",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=candidate.normalized_url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="A credit-card category page.",
        )
        self.assertFalse(
            _candidate_promotes_to_detail(
                candidate=candidate,
                ai_score=ai_score,
                page_evidence=result,
                allow_family_overview=False,
            )
        )

    def test_personal_loans_name_and_use_case_sections_remain_one_product(self) -> None:
        detail_html = """
        <html><head><title>No-fee Personal Loans up to $30,000 | Example Bank</title></head><body>
          <h1>Example Bank Personal Loans</h1>
          <h2>Choose how to use your personal loan</h2>
          <h2>Loans for debt consolidation</h2>
          <h2>Loans for home improvement</h2>
          <h2>Personal loan calculator</h2>
          <p>Choose a fixed interest rate, loan amount, term, and monthly payment.</p>
        </body></html>
        """
        raw_url = "https://www.examplebank.com/personal-loans"
        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            evidence = _score_page_evidence(
                raw_url=raw_url,
                fetch_policy=SimpleNamespace(),
                product_type="personal-loan",
                product_type_definition=_product_type_definition("personal-loan"),
            )

        candidate = HomepageCandidate(
            normalized_url=raw_url,
            raw_url=raw_url,
            anchor_text="Personal Loans",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=raw_url,
            predicted_role="detail",
            relevance_score=10.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
            short_rationale="One personal-loan offering with multiple use cases.",
        )

        self.assertNotIn("multi_product_family_overview", evidence.page_evidence_reason_codes)
        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_distinct_personal_loan_subtypes_still_mark_family_boundary(self) -> None:
        family_html = """
        <html><head><title>Personal Loans | Example Bank</title></head><body>
          <h1>Personal Loans</h1>
          <h2>Auto Loan</h2><p>Finance a vehicle.</p>
          <h2>Student Loan</h2><p>Finance education.</p>
        </body></html>
        """
        with patch("api_service.source_catalog.fetch_text", return_value=family_html):
            evidence = _score_page_evidence(
                raw_url="https://www.examplebank.com/loans",
                fetch_policy=SimpleNamespace(),
                product_type="personal-loan",
                product_type_definition=_product_type_definition("personal-loan"),
            )

        self.assertIn("multi_product_family_overview", evidence.page_evidence_reason_codes)

    def test_high_confidence_named_card_survives_plural_seo_title_and_cross_sell_headings(self) -> None:
        detail_html = """
        <html><head><title>Momentum Visa Infinite Card - Travel Credit Cards | Example Bank</title></head><body>
          <h1>Momentum Visa Infinite Card</h1>
          <p>Earn rewards with a $120 annual fee and a 20.99% purchase rate.</p>
          <h2>Cashback Mastercard</h2>
          <h2>Rewards Mastercard</h2>
        </body></html>
        """
        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            evidence = _score_page_evidence(
                raw_url="https://www.examplebank.ca/credit-cards/momentum-visa-infinite",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
            )
        self.assertIn("multi_product_family_overview", evidence.page_evidence_reason_codes)
        candidate = HomepageCandidate(
            normalized_url="https://www.examplebank.ca/credit-cards/momentum-visa-infinite",
            raw_url="https://www.examplebank.ca/credit-cards/momentum-visa-infinite",
            anchor_text="Momentum Visa Infinite Card",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=candidate.normalized_url,
            predicted_role="detail",
            relevance_score=9.0,
            confidence_band="high",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="A named card detail page.",
        )
        self.assertTrue(
            _candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence)
        )

    def test_confirmed_named_card_does_not_require_exceptionally_high_ai_score(self) -> None:
        detail_html = """
        <html><head><title>Momentum Visa Infinite Card - Cash Back Credit Cards | Example Bank</title></head><body>
          <h1>Momentum Visa Infinite Card</h1>
          <p>Annual fee $120. Purchase interest rate 20.99%. Cash advance rate 22.99%.</p>
          <h2>Other Visa credit cards</h2>
          <h3>Cashback Mastercard</h3>
          <h3>Rewards Mastercard</h3>
        </body></html>
        """
        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            evidence = _score_page_evidence(
                raw_url="https://www.examplebank.ca/credit-cards/visa/momentum-visa-infinite",
                fetch_policy=SimpleNamespace(),
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
            )
        self.assertIn("multi_product_family_overview", evidence.page_evidence_reason_codes)
        candidate = HomepageCandidate(
            normalized_url="https://www.examplebank.ca/credit-cards/visa/momentum-visa-infinite",
            raw_url="https://www.examplebank.ca/credit-cards/visa/momentum-visa-infinite",
            anchor_text="Momentum Visa Infinite Card",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=5,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_score = AiParallelCandidateScore(
            candidate_url=candidate.normalized_url,
            predicted_role="detail",
            relevance_score=5.5,
            confidence_band="medium",
            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
            short_rationale="A named card detail page with explicit fees and rates.",
        )

        self.assertTrue(
            _candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence)
        )

    def test_named_high_interest_savings_detail_is_not_a_family_overview(self) -> None:
        detail_html = """
        <html><head><title>High Interest Savings Account (HISA) | Example Bank</title></head><body>
          <h1>High Interest Savings Account</h1>
          <h2>Saving made easy</h2>
          <p>Earn 0.55% interest paid monthly.</p>
          <h2>Our other investment products</h2>
          <h3>Cash Advantage Solution</h3>
          <h3>Guaranteed investment certificates</h3>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/savings/high-interest",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )

        self.assertNotIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_educational_hisa_page_with_named_account_is_a_family_overview(self) -> None:
        family_html = """
        <html><head><title>High Interest Savings Account | Example Bank</title></head><body>
          <h1>High Interest Savings Account</h1>
          <h2>What is a high interest savings account?</h2>
          <p>A HISA is a type of savings account that offers higher rates than a traditional one.</p>
          <h2>Savings Amplifier Account</h2>
          <p>Open account. Earn a 4.75% promotional rate for 120 days.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=family_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/savings/high-interest-savings-account",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )

        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_marketing_titled_savings_catalog_marks_multi_product_boundary(self) -> None:
        family_html = """
        <html><head><title>Open a Savings Account Online | Example Bank</title></head><body>
          <h1>Save for tomorrow, starting today</h1>
          <h2>High Interest Savings Account</h2>
          <h2>Money Master Savings Account</h2>
          <h2>U.S. Dollar Savings Account</h2>
        </body></html>
        """
        with patch("api_service.source_catalog.fetch_text", return_value=family_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/accounts/savings",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition=_product_type_definition("savings"),
            )
        self.assertIn("multi_product_family_overview", result.page_evidence_reason_codes)

    def test_mortgage_refinance_advice_page_is_not_product_detail(self) -> None:
        detail_html = """
        <html><head><title>Thinking about refinancing?</title></head><body>
          <h1>Thinking about refinancing your mortgage?</h1>
          <h2>Reasons to refinance</h2>
          <p>Talk to an Account Manager to understand how refinancing works.</p>
        </body></html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/en-CA/mortgages/refinance",
                fetch_policy=SimpleNamespace(),
                product_type="mortgage",
                product_type_definition=_product_type_definition("mortgage"),
            )

        self.assertIn("non_product_service_flow", result.page_evidence_reason_codes)
        self.assertGreaterEqual(result.negative_signal_count, 2)

    def test_lending_supporting_sources_accept_rate_pages_with_product_context(self) -> None:
        self.assertTrue(
            _link_is_relevant_supporting_source(
                product_type="mortgage",
                product_type_definition={
                    **_product_type_definition("mortgage"),
                    "display_name": "Mortgage",
                    "description": "Mortgage rates, fixed rate, variable rate, term, and amortization details.",
                    "discovery_keywords": ["mortgage rates", "fixed rate mortgage"],
                },
                normalized_url="https://www.examplebank.ca/mortgages/rates",
                anchor_text="Mortgage rates",
            )
        )

    def test_lending_supporting_sources_reject_unrelated_bank_account_path(self) -> None:
        self.assertFalse(
            _link_is_relevant_supporting_source(
                product_type="mortgage",
                product_type_definition=_product_type_definition("mortgage"),
                normalized_url="https://www.examplebank.ca/accounts/everyday-growth-account",
                anchor_text="Everyday Growth Account Terms and Conditions",
            )
        )

    def test_deposit_supporting_sources_accept_official_generic_rate_page(self) -> None:
        self.assertTrue(
            _link_is_relevant_supporting_source(
                product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic"),
                    "display_name": "GIC",
                    "description": "Guaranteed investment certificate terms and rates.",
                    "discovery_keywords": ["gic", "term deposit"],
                },
                normalized_url="https://www.examplebank.ca/rates",
                anchor_text="Compare all accounts",
            )
        )

    def test_deposit_supporting_sources_stay_on_detail_routes_or_shared_rates(self) -> None:
        details = {
            "https://www.bank.example/savings/platinum",
            "https://www.bank.example/savings/way2save",
        }

        self.assertTrue(
            _supporting_source_is_bounded_to_selected_details(
                product_type="savings",
                normalized_url="https://www.bank.example/savings/platinum/fees",
                promoted_detail_urls=details,
            )
        )
        self.assertTrue(
            _supporting_source_is_bounded_to_selected_details(
                product_type="savings",
                normalized_url="https://www.bank.example/savings/rates",
                promoted_detail_urls=details,
            )
        )
        self.assertFalse(
            _supporting_source_is_bounded_to_selected_details(
                product_type="savings",
                normalized_url="https://www.bank.example/help/zelle-faqs",
                promoted_detail_urls=details,
            )
        )
        self.assertFalse(
            _supporting_source_is_bounded_to_selected_details(
                product_type="savings",
                normalized_url="https://www.bank.example/business/fee-information",
                promoted_detail_urls=details,
            )
        )

    def test_lending_supporting_sources_keep_rates_and_drop_education_pages(self) -> None:
        details = {"https://www.bank.example/personal/mortgage/fha-loan"}

        self.assertTrue(
            _supporting_source_is_bounded_to_selected_details(
                product_type="mortgage",
                normalized_url="https://www.bank.example/personal/mortgage/refinance-rates",
                promoted_detail_urls=details,
            )
        )
        self.assertFalse(
            _supporting_source_is_bounded_to_selected_details(
                product_type="mortgage",
                normalized_url="https://www.bank.example/personal/mortgage/education/credit-score-guide",
                anchor_text="What credit score is needed to buy a house?",
                promoted_detail_urls=details,
            )
        )

    def test_gic_supporting_sources_reject_general_bank_account_fee_changes(self) -> None:
        self.assertFalse(
            _link_is_relevant_supporting_source(
                product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic"),
                    "display_name": "GIC",
                    "description": "Guaranteed investment certificate terms and rates.",
                    "discovery_keywords": ["gic", "term deposit"],
                },
                normalized_url="https://www.examplebank.ca/bank-accounts/account-fees-changes.html",
                anchor_text="Changes to Bank Account Fees and Services",
            )
        )

    def test_gic_supporting_sources_accept_general_deposit_investment_terms(self) -> None:
        self.assertTrue(
            _link_is_relevant_supporting_source(
                product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic"),
                    "display_name": "GIC",
                    "description": "Guaranteed investment certificate terms and rates.",
                    "discovery_keywords": ["gic", "term deposit"],
                },
                normalized_url="https://www.examplebank.ca/legal/terms-for-deposit-investments.pdf",
                anchor_text="Terms and disclosure for deposit investments",
            )
        )

    def test_homepage_discovery_preserves_generic_deposit_rates_as_supporting_evidence(self) -> None:
        detail_url = "https://www.examplebank.ca/personal/investments/gics"
        rates_url = "https://www.examplebank.ca/rates"
        homepage_links = [
            SimpleNamespace(
                normalized_url=detail_url,
                resolved_url=detail_url,
                anchor_text="GICs",
                source_type="html",
            ),
            SimpleNamespace(
                normalized_url=rates_url,
                resolved_url=rates_url,
                anchor_text="Rates",
                source_type="html",
            ),
            *[
                SimpleNamespace(
                    normalized_url=f"https://www.examplebank.ca/help/service-{index}",
                    resolved_url=f"https://www.examplebank.ca/help/service-{index}",
                    anchor_text=f"Service help {index}",
                    source_type="html",
                )
                for index in range(9)
            ],
        ]
        ai_result = AiParallelScoringResult(
            scores={
                detail_url: AiParallelCandidateScore(
                    candidate_url=detail_url,
                    predicted_role="detail",
                    relevance_score=9.0,
                    confidence_band="high",
                    reason_codes=["product_type_semantic_match"],
                    short_rationale="Official GIC detail page.",
                ),
                rates_url: AiParallelCandidateScore(
                    candidate_url=rates_url,
                    predicted_role="irrelevant",
                    relevance_score=2.0,
                    confidence_band="medium",
                    reason_codes=["generic_rates_page"],
                    short_rationale="Generic rates page.",
                ),
            },
            notes=[],
        )
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=8,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match", "pricing_or_feature_signal"],
            page_title="GICs",
            primary_heading="GICs",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=homepage_links),
            patch("api_service.source_catalog._score_candidate_links_with_ai", return_value=ai_result),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="TEST",
                bank_name="Test Bank",
                country_code="CA",
                product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic"),
                    "description": "Guaranteed investment certificates with term rates.",
                    "discovery_keywords": ["gic", "term deposit"],
                },
                homepage_url="https://www.examplebank.ca/",
                source_language="en",
            )

        rates_row = next(item for item in result.rows if item["normalized_url"] == rates_url)
        self.assertEqual(rates_row["discovery_role"], "supporting_html")
        self.assertEqual(rates_row["discovery_metadata"]["selection_path"], "deterministic_supporting_fallback")

    def test_product_type_rate_page_recognizes_vancity_family_routes_without_cross_product_leakage(self) -> None:
        cases = (
            ("chequing", "https://www.vancity.com/rates/accounts"),
            ("savings", "https://www.vancity.com/rates/accounts"),
            ("gic", "https://www.vancity.com/rates/term-deposit-gic"),
            ("mortgage", "https://www.vancity.com/rates/mortgages"),
            ("personal-loan", "https://www.vancity.com/rates/loans-lines-of-credit"),
            ("line-of-credit", "https://www.vancity.com/rates/loans-lines-of-credit"),
        )
        for product_type, url in cases:
            with self.subTest(product_type=product_type):
                self.assertTrue(
                    _is_product_type_rate_page(
                        product_type=product_type,
                        normalized_url=url,
                        anchor_text="See all rates",
                    )
                )

        self.assertFalse(
            _is_product_type_rate_page(
                product_type="mortgage",
                normalized_url="https://www.vancity.com/rates/accounts",
                anchor_text="Account interest rates",
            )
        )

    def test_registered_plan_wrapper_rule_keeps_exact_underlying_gic_and_rrsp_loan_products(self) -> None:
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint=(
                    "https://www.vancity.com/invest/term-deposit-gic/rrsp-rrif-convertible "
                    "RRSP/RRIF convertible term deposit"
                ),
            )
        )
        self.assertIsNone(
            _source_scope_exclusion_reason(
                product_type="personal-loan",
                fingerprint="https://www.vancity.com/borrow/loans-lines-of-credit/rrsp-loan RRSP loan",
            )
        )
        self.assertEqual(
            _source_scope_exclusion_reason(
                product_type="gic",
                fingerprint="https://www.examplebank.ca/investing/rrsp Registered Retirement Savings Plan",
            ),
            "registered_plan_wrapper",
        )

    def test_homepage_discovery_promotes_json_script_routes_across_banks_and_product_types(self) -> None:
        cases = (
            {
                "bank_code": "ATLAS",
                "bank_name": "Atlas Bank",
                "product_type": "savings",
                "homepage_url": "https://www.atlas.example/",
                "detail_url": "https://www.atlas.example/banking/high-interest-savings",
                "product_name": "Atlas High Interest Savings",
            },
            {
                "bank_code": "HARBOR",
                "bank_name": "Harbor Bank",
                "product_type": "mortgage",
                "homepage_url": "https://www.harbor.example/",
                "detail_url": "https://www.harbor.example/mortgages/fixed-rate",
                "product_name": "Harbor Fixed Mortgage",
            },
        )
        for case in cases:
            with self.subTest(bank_code=case["bank_code"], product_type=case["product_type"]):
                homepage_html = (
                    '<script type="application/json" id="ssr-state">'
                    + json.dumps(
                        {
                            "cards": [
                                {
                                    "title": case["product_name"],
                                    "targetUrl": case["detail_url"],
                                }
                            ]
                        }
                    )
                    + "</script>"
                )
                ai_result = AiParallelScoringResult(
                    scores={
                        case["detail_url"]: AiParallelCandidateScore(
                            candidate_url=case["detail_url"],
                            predicted_role="detail",
                            relevance_score=9.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match"],
                            short_rationale="Official named product detail page.",
                        )
                    },
                    notes=[],
                )
                detail_evidence = PageEvidenceAssessment(
                    page_evidence_score=8,
                    page_evidence_reason_codes=[
                        "product_identity_signal",
                        "title_semantic_match",
                        "pricing_or_feature_signal",
                    ],
                    page_title=case["product_name"],
                    primary_heading=case["product_name"],
                    heading_match=True,
                    attribute_signal_count=3,
                    negative_signal_count=0,
                )

                with (
                    patch(
                        "api_service.source_catalog.fetch_text",
                        side_effect=lambda url, _policy: homepage_html if url == case["homepage_url"] else "<html></html>",
                    ),
                    patch("api_service.source_catalog._score_candidate_links_with_ai", return_value=ai_result),
                    patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
                ):
                    result = _generate_sources_from_homepage(
                        bank_code=case["bank_code"],
                        bank_name=case["bank_name"],
                        country_code="US",
                        product_type=case["product_type"],
                        product_type_definition=_product_type_definition(case["product_type"]),
                        homepage_url=case["homepage_url"],
                        source_language="en",
                    )

                detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
                self.assertEqual([item["normalized_url"] for item in detail_rows], [case["detail_url"]])
                self.assertEqual(len(result.detail_source_ids), 1)

    def test_product_faq_minimum_is_supporting_evidence_not_a_detail_candidate(self) -> None:
        detail_url = "https://www.examplebank.ca/investments/gic"
        faq_url = "https://www.examplebank.ca/en/faq/minimum-balance-needed-to-open-a-gic"
        entry_html = (
            f'<a href="{detail_url}">Guaranteed Investment</a>'
            f'<a href="{faq_url}">What is the minimum balance needed to open a GIC?</a>'
        )
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=8,
            page_evidence_reason_codes=["product_identity_signal", "title_semantic_match", "pricing_or_feature_signal"],
            page_title="Guaranteed Investment",
            primary_heading="Guaranteed Investment",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )
        ai_result = AiParallelScoringResult(
            scores={
                detail_url: AiParallelCandidateScore(
                    candidate_url=detail_url,
                    predicted_role="detail",
                    relevance_score=9.0,
                    confidence_band="high",
                    reason_codes=["product_type_semantic_match"],
                    short_rationale="Official GIC detail page.",
                )
            },
            notes=[],
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value=entry_html),
            patch("api_service.source_catalog._score_candidate_links_with_ai", return_value=ai_result),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="TEST",
                bank_name="Test Bank",
                country_code="CA",
                product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic"),
                    "description": "Guaranteed investment certificates with rates, terms, and minimum deposits.",
                    "discovery_keywords": ["gic", "guaranteed investment", "minimum balance"],
                },
                homepage_url="https://www.examplebank.ca/investments",
                source_language="en",
            )

        faq_rows = [item for item in result.rows if item["normalized_url"] == faq_url]
        self.assertEqual(len(faq_rows), 1)
        self.assertEqual(faq_rows[0]["discovery_role"], "supporting_html")
        self.assertNotIn(faq_url, {item["normalized_url"] for item in result.rows if item["discovery_role"] == "detail"})

    def test_create_bank_profile_auto_generates_bank_code(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "country_code": "ca",
                    "source_language": "en",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["bank_code"], "ATL")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO bank" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["bank_code"], "ATL")
        self.assertTrue(insert_calls[0][1]["managed_flag"])

    def test_create_bank_profile_can_create_initial_coverage(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
            patch("api_service.source_catalog.create_source_catalog_item") as create_catalog_item,
        ):
            create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "country_code": "ca",
                    "source_language": "en",
                    "status": "active",
                    "change_reason": "Initial operator setup",
                    "initial_coverage_product_types": ["savings", "gic"],
                    "initial_coverage_source_urls": {
                        "savings": "https://www.atlasbank.ca/accounts/savings/",
                        "gic": "https://www.atlasbank.ca/investments/cds/",
                    },
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(create_catalog_item.call_count, 2)
        self.assertEqual(create_catalog_item.call_args_list[0].kwargs["payload"]["product_type"], "savings")
        self.assertEqual(create_catalog_item.call_args_list[1].kwargs["payload"]["product_type"], "gic")
        self.assertEqual(create_catalog_item.call_args_list[0].kwargs["payload"]["bank_code"], "ATL")
        self.assertEqual(
            create_catalog_item.call_args_list[0].kwargs["payload"]["coverage_source_url"],
            "https://www.atlasbank.ca/accounts/savings/",
        )

    def test_coverage_source_url_must_be_https_and_on_the_bank_domain(self) -> None:
        self.assertEqual(
            _normalize_coverage_source_url(
                "https://products.atlasbank.ca/accounts/savings/",
                normalized_homepage_url="https://www.atlasbank.ca/",
            ),
            (
                "https://products.atlasbank.ca/accounts/savings/",
                "https://products.atlasbank.ca/accounts/savings",
            ),
        )
        with self.assertRaisesRegex(SourceRegistryError, "official homepage domain"):
            _normalize_coverage_source_url(
                "https://unrelated.example/savings/",
                normalized_homepage_url="https://www.atlasbank.ca/",
            )
        with self.assertRaisesRegex(SourceRegistryError, "public HTTPS"):
            _normalize_coverage_source_url(
                "http://www.atlasbank.ca/savings/",
                normalized_homepage_url="https://www.atlasbank.ca/",
            )

    def test_verified_brand_domain_coverage_route_is_allowed_without_broadening_unverified_urls(self) -> None:
        metadata = {
            "verification_status": "verified",
            "verification_method": "ai_web_search_exact_quote",
            "coverage_domain": "marcus.com",
            "relationship_source_url": "https://www.marcus.com/us/en/faqs",
            "relationship_quote": "Marcus by Goldman Sachs is a brand of Goldman Sachs Bank USA.",
        }

        self.assertEqual(
            _normalize_coverage_source_url(
                "https://www.marcus.com/us/en/savings",
                normalized_homepage_url="https://www.goldmansachs.com/",
                coverage_source_metadata=metadata,
            ),
            (
                "https://www.marcus.com/us/en/savings",
                "https://www.marcus.com/us/en/savings",
            ),
        )
        with self.assertRaisesRegex(SourceRegistryError, "verified official brand-domain"):
            _normalize_coverage_source_url(
                "https://unrelated.example/savings",
                normalized_homepage_url="https://www.goldmansachs.com/",
                coverage_source_metadata=metadata,
            )

    @patch("api_service.source_catalog._record_catalog_audit_event")
    @patch("api_service.source_catalog._require_exact_quote_on_page")
    @patch("api_service.source_catalog.llm_provider_configured", return_value=True)
    @patch(
        "api_service.source_catalog.require_product_type_definition",
        return_value={
            "product_type_code": "savings",
            "display_name": "Savings account",
            "description": "Retail savings accounts",
            "discovery_keywords": ["savings account"],
        },
    )
    def test_coverage_route_repair_persists_verified_cross_domain_evidence(
        self,
        _definition: MagicMock,
        _configured: MagicMock,
        _quote_check: MagicMock,
        audit: MagicMock,
    ) -> None:
        connection = _QueuedConnection([None, None, None])

        def invoke_model(**_kwargs):
            return (
                {
                    "status": "current_offering",
                    "summary": (
                        "Marcus currently offers savings accounts for Goldman Sachs Bank USA; "
                        "the prior Transaction Banking route was rejected."
                    ),
                    "coverage_source_url": "https://www.marcus.com/us/en/savings",
                    "current_offering_quote": "## Online Savings Account",
                    "relationship_source_url": "https://www.marcus.com/us/en/faqs",
                    "relationship_quote": "Marcus by Goldman Sachs is a brand of Goldman Sachs Bank USA.",
                    "not_offered_source_url": None,
                    "not_offered_quote": None,
                },
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-route-001",
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "web_search_sources": [
                        {"url": "https://www.marcus.com/us/en/savings", "title": "Savings"},
                        {"url": "https://www.marcus.com/us/en/faqs", "title": "FAQs"},
                    ],
                },
            )

        result = repair_catalog_coverage_route(
            connection,
            row={
                "catalog_item_id": "catalog-us-gsbu-savings",
                "bank_code": "GSBU",
                "bank_name": "Goldman Sachs Bank USA",
                "country_code": "US",
                "product_type": "savings",
                "homepage_url": "https://www.goldmansachs.com/",
                "coverage_source_url": None,
            },
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-route-001"},
            run_id="run-route-001",
            correlation_id="corr-route-001",
            invoke_model=invoke_model,
        )

        self.assertEqual(result.status, "current_offering")
        self.assertEqual(result.coverage_source_metadata["coverage_domain"], "marcus.com")
        route_update = next(
            params
            for sql, params in connection.calls
            if "ai_verified_current_coverage_route" in sql
        )
        self.assertEqual(route_update["coverage_source_url"], "https://www.marcus.com/us/en/savings")
        self.assertIn('"verification_status": "verified"', str(route_update["coverage_source_metadata"]))
        _quote_check.assert_any_call(
            url="https://www.marcus.com/us/en/savings",
            quote="Online Savings Account",
        )
        audit.assert_called_once()

    @patch("api_service.source_catalog._record_catalog_audit_event")
    @patch("api_service.source_catalog._require_exact_quote_on_page")
    @patch("api_service.source_catalog.llm_provider_configured", return_value=True)
    @patch(
        "api_service.source_catalog.require_product_type_definition",
        return_value={
            "product_type_code": "personal-loan",
            "display_name": "Personal loan",
            "description": "Retail unsecured personal loans",
            "discovery_keywords": ["personal loan"],
        },
    )
    def test_coverage_route_repair_deactivates_explicitly_retired_pdf_evidence(
        self,
        _definition: MagicMock,
        _configured: MagicMock,
        _quote_check: MagicMock,
        audit: MagicMock,
    ) -> None:
        connection = _QueuedConnection([None, None, None])
        evidence_url = "https://www.federalreserve.gov/consumerscommunities/files/goldman-sachs-strategic-plan.pdf"
        relationship_url = "https://www.marcus.com/us/en/faqs"

        def invoke_model(**_kwargs):
            return (
                {
                    "status": "not_currently_offered",
                    "summary": "The bank ceased originating consumer installment loans.",
                    "coverage_source_url": None,
                    "current_offering_quote": None,
                    "relationship_source_url": relationship_url,
                    "relationship_quote": "Marcus by Goldman Sachs is a brand of Goldman Sachs Bank USA.",
                    "not_offered_source_url": evidence_url,
                    "not_offered_quote": (
                        "Marcus is in the process of winding down its offering of online consumer personal loan products in 2023."
                    ),
                },
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-route-retired",
                    "prompt_tokens": 90,
                    "completion_tokens": 40,
                    "web_search_sources": [
                        {"url": evidence_url, "title": "Federal Reserve strategic plan"},
                        {"url": relationship_url, "title": "Marcus FAQs"},
                    ],
                },
            )

        result = repair_catalog_coverage_route(
            connection,
            row={
                "catalog_item_id": "catalog-us-gsbu-personal-loan",
                "bank_code": "GSBU",
                "bank_name": "Goldman Sachs Bank USA",
                "country_code": "US",
                "product_type": "personal-loan",
                "homepage_url": "https://www.goldmansachs.com/",
                "coverage_source_url": None,
            },
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-route-retired"},
            run_id="run-route-retired",
            correlation_id="corr-route-retired",
            invoke_model=invoke_model,
        )

        self.assertEqual(result.status, "not_currently_offered")
        retired_update = next(
            params
            for sql, params in connection.calls
            if "ai_verified_product_not_currently_offered" in sql
        )
        self.assertEqual(retired_update["catalog_item_id"], "catalog-us-gsbu-personal-loan")
        self.assertIn('"verification_status": "verified_not_currently_offered"', str(retired_update["coverage_source_metadata"]))
        audit.assert_called_once()

    @patch("api_service.source_catalog._record_catalog_audit_event")
    @patch("api_service.source_catalog._require_exact_quote_on_page")
    @patch("api_service.source_catalog.llm_provider_configured", return_value=True)
    @patch(
        "api_service.source_catalog.require_product_type_definition",
        return_value={
            "product_type_code": "gic",
            "display_name": "Certificate of Deposit (CD)",
            "description": "Retail consumer certificates of deposit",
            "discovery_keywords": ["certificate of deposit", "cd"],
        },
    )
    def test_coverage_route_repair_rejects_transaction_banking_term_deposit(
        self,
        _definition: MagicMock,
        _configured: MagicMock,
        _quote_check: MagicMock,
        audit: MagicMock,
    ) -> None:
        connection = _QueuedConnection([None, None])
        route_url = "https://www.goldmansachs.com/what-we-do/transaction-banking/"

        def invoke_model(**_kwargs):
            return (
                {
                    "status": "current_offering",
                    "summary": "Transaction Banking offers corporate term deposits.",
                    "coverage_source_url": route_url,
                    "current_offering_quote": "Deposit products include Term Deposits.",
                    "relationship_source_url": None,
                    "relationship_quote": None,
                    "not_offered_source_url": None,
                    "not_offered_quote": None,
                },
                {
                    "provider": "openai",
                    "model_id": "test-model",
                    "provider_request_id": "resp-route-corporate",
                    "prompt_tokens": 80,
                    "completion_tokens": 30,
                    "web_search_sources": [{"url": route_url, "title": "Transaction Banking"}],
                },
            )

        result = repair_catalog_coverage_route(
            connection,
            row={
                "catalog_item_id": "catalog-us-gsbu-gic",
                "bank_code": "GSBU",
                "bank_name": "Goldman Sachs Bank USA",
                "country_code": "US",
                "product_type": "gic",
                "homepage_url": "https://www.goldmansachs.com/",
                "coverage_source_url": None,
            },
            actor={"user_id": "usr-admin", "role": "admin"},
            request_context={"request_id": "req-route-corporate"},
            run_id="run-route-corporate",
            correlation_id="corr-route-corporate",
            invoke_model=invoke_model,
        )

        self.assertEqual(result.status, "uncertain")
        self.assertTrue(any("non_consumer_business_page" in note for note in result.notes))
        self.assertFalse(any("ai_verified_current_coverage_route" in sql for sql, _params in connection.calls))
        audit.assert_not_called()

    def test_coverage_route_metadata_migration_is_additive(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0031_catalog_coverage_route_evidence.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN IF NOT EXISTS coverage_source_metadata jsonb", migration_sql)
        self.assertIn("jsonb_typeof(coverage_source_metadata) = 'object'", migration_sql)
        self.assertIn("0031_catalog_coverage_route_evidence.sql", migration_sql)

    def test_create_bank_profile_accepts_homepage_without_scheme(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "www.atlasbank.ca",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO bank" in sql]
        self.assertEqual(insert_calls[0][1]["homepage_url"], "https://www.atlasbank.ca/")
        self.assertEqual(insert_calls[0][1]["normalized_homepage_url"], "https://www.atlasbank.ca/")

    def test_create_bank_profile_persists_logo_metadata(self) -> None:
        connection = _QueuedConnection([None, None])

        with (
            patch("api_service.source_catalog._generate_bank_code", return_value="ATL"),
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                        "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                        "logo_alt_text": "Atlas Bank logo",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_bank_profile(
                connection,
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca/",
                    "logo_url": "www.atlasbank.ca/assets/logo.svg",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        insert_call = next(params for sql, params in connection.calls if "INSERT INTO bank" in sql)
        self.assertEqual(insert_call["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        self.assertEqual(insert_call["logo_alt_text"], "Atlas Bank logo")

    def test_update_bank_profile_updates_logo_metadata(self) -> None:
        existing_row = {
            "bank_code": "ATL",
            "country_code": "CA",
            "bank_name": "Atlas Bank",
            "status": "active",
            "homepage_url": "https://www.atlasbank.ca/",
            "normalized_homepage_url": "https://www.atlasbank.ca/",
            "logo_url": None,
            "logo_alt_text": None,
            "source_language": "en",
            "managed_flag": True,
            "change_reason": None,
            "created_at": None,
            "updated_at": None,
        }
        connection = _QueuedConnection([existing_row, None, None])

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                        "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                        "logo_alt_text": "Atlas primary mark",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = update_bank_profile(
                connection,
                bank_code="ATL",
                payload={
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca/",
                    "logo_url": "https://www.atlasbank.ca/assets/logo.svg",
                    "logo_alt_text": "Atlas primary mark",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["logo_alt_text"], "Atlas primary mark")
        update_call = next(params for sql, params in connection.calls if "UPDATE bank" in sql)
        self.assertEqual(update_call["logo_url"], "https://www.atlasbank.ca/assets/logo.svg")
        self.assertEqual(update_call["logo_alt_text"], "Atlas primary mark")

    def test_generate_bank_code_prefers_known_seed_bank_codes(self) -> None:
        td_connection = _QueuedConnection([None])
        scotia_connection = _QueuedConnection([None])
        rbc_connection = _QueuedConnection([None])

        self.assertEqual(_generate_bank_code(td_connection, bank_name="TD Bank", normalized_homepage_url="https://www.td.com/"), "TD")
        self.assertEqual(
            _generate_bank_code(scotia_connection, bank_name="Scotiabank", normalized_homepage_url="https://www.scotiabank.com/"),
            "SCOTIA",
        )
        self.assertEqual(
            _generate_bank_code(rbc_connection, bank_name="Royal Bank of Canada", normalized_homepage_url="https://www.rbcroyalbank.com/"),
            "RBC",
        )

    def test_create_source_catalog_item_uses_existing_bank_and_product_type(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "bank_code": "ATL",
                    "country_code": "CA",
                    "bank_name": "Atlas Bank",
                    "homepage_url": "https://www.atlasbank.ca",
                    "normalized_homepage_url": "https://www.atlasbank.ca",
                    "source_language": "en",
                },
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("savings"),
            ),
            patch("api_service.source_catalog.new_id", return_value="abcdef123456"),
            patch(
                "api_service.source_catalog.load_source_catalog_detail",
                return_value={
                    "catalog_item": {
                        "catalog_item_id": "catalog-ca-atl-savings-abcdef12",
                        "bank_code": "ATL",
                        "product_type": "savings",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_source_catalog_item(
                connection,
                payload={
                    "bank_code": "atl",
                    "product_type": "savings",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["catalog_item_id"], "catalog-ca-atl-savings-abcdef12")
        insert_calls = [(sql, params) for sql, params in connection.calls if "INSERT INTO source_registry_catalog_item" in sql]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1]["bank_code"], "ATL")
        self.assertEqual(insert_calls[0][1]["product_type"], "savings")

    def test_create_source_catalog_item_uses_registered_product_type_code_without_aliasing(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "bank_name": "BMO",
                    "homepage_url": "https://www.bmo.com/",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "source_language": "en",
                },
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("saving"),
            ) as require_definition,
            patch("api_service.source_catalog.new_id", return_value="abcdef123456"),
            patch(
                "api_service.source_catalog.load_source_catalog_detail",
                return_value={
                    "catalog_item": {
                        "catalog_item_id": "catalog-ca-bmo-saving-abcdef12",
                        "bank_code": "BMO",
                        "product_type": "saving",
                    }
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = create_source_catalog_item(
                connection,
                payload={
                    "bank_code": "bmo",
                    "product_type": "saving",
                    "status": "active",
                },
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["product_type"], "saving")
        require_definition.assert_called_once_with(connection, product_type_code="saving", active_only=True)
        conflict_call = next(params for sql, params in connection.calls if "FROM source_registry_catalog_item" in sql and "ANY" in sql)
        self.assertEqual(conflict_call["product_type_scope"], ["saving"])
        insert_call = next(params for sql, params in connection.calls if "INSERT INTO source_registry_catalog_item" in sql)
        self.assertEqual(insert_call["product_type"], "saving")

    def test_load_bank_list_includes_catalog_items_for_bulk_collect(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "bank_code": "ATL",
                        "country_code": "CA",
                        "bank_name": "Atlas Bank",
                        "status": "active",
                        "product_family": "deposit",
                        "homepage_url": "https://www.atlasbank.ca",
                        "normalized_homepage_url": "https://www.atlasbank.ca",
                        "source_language": "en",
                        "managed_flag": True,
                        "change_reason": None,
                        "created_at": None,
                        "updated_at": None,
                        "catalog_item_count": 2,
                        "catalog_product_types": ["gic", "savings"],
                        "generated_source_count": 3,
                    }
                ],
                [
                    {
                        "catalog_item_id": "catalog-ca-atl-savings-1",
                        "bank_code": "ATL",
                        "product_type": "savings",
                        "status": "active",
                        "generated_source_count": 2,
                    },
                    {
                        "catalog_item_id": "catalog-ca-atl-gic-1",
                        "bank_code": "ATL",
                        "product_type": "gic",
                        "status": "inactive",
                        "generated_source_count": 1,
                    },
                ],
            ]
        )

        result = load_bank_list(
            connection,
            filters=normalize_bank_filters(country_code="CA", search=None, status=None),
        )

        self.assertEqual(result["items"][0]["catalog_product_types"], ["gic", "savings"])
        self.assertEqual(
            [item["catalog_item_id"] for item in result["items"][0]["catalog_items"]],
            ["catalog-ca-atl-savings-1", "catalog-ca-atl-gic-1"],
        )

    def test_collection_plan_uses_registered_product_type_code_without_aliasing(self) -> None:
        plan = _build_source_catalog_collection_plan(
            rows=[
                {
                    "catalog_item_id": "catalog-ca-bmo-saving-legacy",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "saving",
                    "homepage_url": "https://www.bmo.com/",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "source_language": "en",
                }
            ],
            actor={"user_id": "usr-001", "email": "admin@example.com", "display_name": "Admin", "role": "admin"},
            request_context={"request_id": "req-001"},
            collection_id="collection-001",
            correlation_id="corr-001",
        )

        group = plan["groups"][0]
        self.assertEqual(group["product_type"], "saving")
        self.assertEqual(group["source_catalog_product_type"], "saving")
        self.assertIn("_bmo_saving_collect_", group["run_id"])

    def test_delete_bank_profile_removes_catalog_and_generated_sources_when_unused_downstream(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "catalog_count": 2,
                    "source_registry_count": 3,
                    "source_document_count": 0,
                    "candidate_count": 0,
                    "canonical_product_count": 0,
                    "public_projection_count": 0,
                    "dashboard_ranking_count": 0,
                    "dashboard_scatter_count": 0,
                },
                None,
                None,
                None,
                None,
            ]
        )

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    },
                    "catalog_items": [],
                },
            ),
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = delete_bank_profile(
                connection,
                bank_code="atl",
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["bank_code"], "ATL")
        self.assertTrue(any("DELETE FROM source_registry_item" in sql for sql, _ in connection.calls))
        self.assertTrue(any("DELETE FROM source_registry_catalog_item" in sql for sql, _ in connection.calls))
        self.assertTrue(any("DELETE FROM bank" in sql for sql, _ in connection.calls))

    def test_delete_bank_profile_rejects_bank_with_downstream_runtime_data(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "catalog_count": 1,
                    "source_registry_count": 1,
                    "source_document_count": 1,
                    "candidate_count": 0,
                    "canonical_product_count": 0,
                    "public_projection_count": 0,
                    "dashboard_ranking_count": 0,
                    "dashboard_scatter_count": 0,
                },
            ]
        )

        with (
            patch(
                "api_service.source_catalog.load_bank_detail",
                return_value={
                    "bank": {
                        "bank_code": "ATL",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca/",
                    },
                    "catalog_items": [],
                },
            ),
        ):
            with self.assertRaises(SourceRegistryError) as captured:
                delete_bank_profile(
                    connection,
                    bank_code="ATL",
                    actor={"user_id": "usr-001", "role": "admin"},
                    request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
                )

        self.assertEqual(captured.exception.code, "bank_profile_in_use")

    def test_start_source_catalog_collection_materializes_and_launches_collection(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "catalog_item_id": "catalog-ca-atl-savings-12345678",
                        "bank_code": "ATL",
                        "country_code": "CA",
                        "product_type": "savings",
                        "status": "active",
                        "bank_name": "Atlas Bank",
                        "homepage_url": "https://www.atlasbank.ca",
                        "normalized_homepage_url": "https://www.atlasbank.ca",
                        "source_language": "en",
                    }
                ]
            ]
        )

        with (
            patch("api_service.source_catalog._build_source_catalog_collection_run_id", return_value="run-001"),
            patch("api_service.source_catalog.new_id", side_effect=["collection-001", "corr-001"]),
            patch("api_service.source_catalog._insert_collection_run_row") as queue_run,
            patch("api_service.source_catalog._launch_source_catalog_collection_runner") as launch_runner,
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-atl-savings-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["catalog_item_ids"], ["catalog-ca-atl-savings-12345678"])
        self.assertEqual(result["collection_id"], "collection-001")
        self.assertEqual(result["correlation_id"], "corr-001")
        self.assertEqual(result["run_ids"], ["run-001"])
        self.assertEqual(result["materialized_items"], [])
        self.assertEqual(result["workflow_state"], "queued")
        self.assertEqual(result["queued_catalog_item_count"], 1)
        queue_run.assert_called_once_with(
            connection,
            run_id="run-001",
            triggered_by="admin@example.com",
            request_id="req-001",
            correlation_id="corr-001",
            collection_id="collection-001",
            group={
                "run_id": "run-001",
                "catalog_item_id": "catalog-ca-atl-savings-12345678",
                "bank_code": "ATL",
                "bank_name": "Atlas Bank",
                "country_code": "CA",
                "product_type": "savings",
                "source_catalog_product_type": "savings",
                "product_family": "deposit",
                "source_language": "en",
                "homepage_url": "https://www.atlasbank.ca",
                "normalized_homepage_url": "https://www.atlasbank.ca",
                "coverage_source_url": None,
                "coverage_source_metadata": {},
                "selected_source_ids": [],
                "target_source_ids": [],
                "included_source_ids": [],
                "included_sources": [],
            },
            pipeline_stage="source_catalog_collection",
            trigger_type="admin_source_collection",
            retry_of_run_id=None,
        )
        launch_runner.assert_called_once()

    def test_record_catalog_audit_event_uses_current_audit_schema(self) -> None:
        connection = _QueuedConnection([None])

        with patch("api_service.source_catalog.new_id", return_value="audit-001"):
            _record_catalog_audit_event(
                connection,
                actor={"user_id": "usr-001", "role": "admin"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
                event_type="bank_profile_updated",
                target_id="BMO",
                target_type="bank",
                diff_summary="Updated bank profile `BMO`: Homepage URL.",
                metadata={"bank_code": "BMO"},
            )

        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("event_category", sql)
        self.assertIn("actor_role_snapshot", sql)
        self.assertIn("occurred_at", sql)
        self.assertEqual(params["audit_event_id"], "audit-001")
        self.assertEqual(params["event_category"], "config")
        self.assertEqual(params["actor_id"], "usr-001")
        self.assertEqual(params["actor_role_snapshot"], "admin")
        self.assertEqual(params["diff_summary"], "Updated bank profile `BMO`: Homepage URL.")

    def test_materialize_sources_for_catalog_item_regenerates_from_bank_homepage(self) -> None:
        connection = _QueuedConnection([None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[
                        {
                            "source_id": "AUTO-BMO-CHQ-001",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing catalog entry",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "entry",
                            "status": "active",
                            "priority": "P0",
                            "source_language": "en",
                            "purpose": "entry",
                            "expected_fields": ["product_name"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        }
                    ],
                    discovery_notes=["seeded entry only"],
                    detail_source_ids=["AUTO-BMO-CHQ-001"],
                ),
            ) as generate_sources,
            patch(
                "api_service.source_catalog._upsert_source_registry_rows",
                return_value=[
                    {
                        "source_id": "AUTO-BMO-CHQ-001",
                        "bank_code": "BMO",
                        "country_code": "CA",
                        "product_type": "chequing",
                        "source_name": "BMO chequing catalog entry",
                        "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                        "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                        "source_type": "html",
                        "discovery_role": "entry",
                        "status": "active",
                        "priority": "P0",
                        "source_language": "en",
                        "purpose": "entry",
                        "expected_fields": ["product_name"],
                        "seed_source_flag": False,
                        "redirect_target_url": None,
                        "alias_urls": [],
                        "change_reason": "generated_from_bank_homepage",
                    }
                ],
            ) as upsert_rows,
            patch(
                "api_service.source_catalog._deactivate_hard_scope_excluded_generated_detail_sources",
                return_value=0,
            ),
            patch(
                "api_service.source_catalog._deactivate_case_alias_generated_detail_sources",
                return_value=0,
            ),
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual([item["source_id"] for item in result.generated_rows], ["AUTO-BMO-CHQ-001"])
        self.assertEqual(result.discovery_notes, ["seeded entry only"])
        generate_sources.assert_called_once()
        upsert_rows.assert_called_once()
        self.assertEqual(upsert_rows.call_args.args[1][0]["source_id"], "AUTO-BMO-CHQ-001")
        self.assertEqual(len(connection.calls), 1)
        sql, params = connection.calls[0]
        self.assertIn("UPDATE source_registry_item", sql)
        self.assertIn("discovery_role <> 'detail'", sql)
        self.assertIn("status <> 'removed'", sql)
        self.assertEqual(params["bank_code"], "BMO")
        self.assertIn("chequing", params["product_type_scope"])

    def test_materialize_sources_persists_homepage_ai_usage_for_run_detail(self) -> None:
        connection = _QueuedConnection([None, None, None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[],
                    discovery_notes=["AI parallel scorer evaluated 1 candidate link(s)."],
                    detail_source_ids=["AUTO-BMO-CHQ-001"],
                    model_execution_records=(
                        {
                            "model_execution_id": "modelexec-ai-001",
                            "run_id": "run-001",
                            "source_document_id": None,
                            "stage_name": "source_catalog_collection",
                            "agent_name": "fpds-homepage-ai-parallel-scorer",
                            "model_id": "gpt-5.6-luna",
                            "execution_status": "completed",
                            "execution_metadata": {"candidate_link_count": 1},
                            "started_at": "2026-04-28T20:39:48+00:00",
                            "completed_at": "2026-04-28T20:39:49+00:00",
                        },
                    ),
                    usage_records=(
                        {
                            "llm_usage_id": "usage-ai-001",
                            "model_execution_id": "modelexec-ai-001",
                            "run_id": "run-001",
                            "candidate_id": None,
                            "provider_request_id": "resp-001",
                            "prompt_tokens": 120,
                            "completion_tokens": 30,
                            "estimated_cost": "0.000072",
                            "usage_metadata": {
                                "usage_mode": "openai-homepage-parallel-scoring",
                                "provider": "openai",
                                "model_id": "gpt-5.6-luna",
                            },
                            "recorded_at": "2026-04-28T20:39:49+00:00",
                        },
                    ),
                ),
            ),
            patch("api_service.source_catalog._upsert_source_registry_rows", return_value=[]),
            patch(
                "api_service.source_catalog._deactivate_hard_scope_excluded_generated_detail_sources",
                return_value=0,
            ),
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
                run_id="run-001",
                correlation_id="corr-001",
                request_id="req-001",
            )

        self.assertEqual(len(result.model_execution_records), 1)
        self.assertEqual(len(result.usage_records), 1)
        model_call = next(params for sql, params in connection.calls if "INSERT INTO model_execution" in sql)
        usage_call = next(params for sql, params in connection.calls if "INSERT INTO llm_usage_record" in sql)
        self.assertEqual(model_call["stage_name"], "source_catalog_collection")
        self.assertEqual(usage_call["prompt_tokens"], 120)
        self.assertEqual(usage_call["completion_tokens"], 30)
        self.assertIn("openai-homepage-parallel-scoring", usage_call["usage_metadata"])

    def test_materialize_sources_dedupes_same_scope_and_prefers_detail(self) -> None:
        connection = _QueuedConnection([None])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[
                        {
                            "source_id": "AUTO-BMO-CHQ-entry",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing catalog entry",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "entry",
                            "status": "active",
                            "priority": "P0",
                            "source_language": "en",
                            "purpose": "entry",
                            "expected_fields": ["product_name"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        },
                        {
                            "source_id": "AUTO-BMO-CHQ-detail",
                            "bank_code": "BMO",
                            "country_code": "CA",
                            "product_type": "chequing",
                            "source_name": "BMO chequing detail",
                            "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                            "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                            "source_type": "html",
                            "discovery_role": "detail",
                            "status": "active",
                            "priority": "P1",
                            "source_language": "en",
                            "purpose": "detail",
                            "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                            "seed_source_flag": False,
                            "redirect_target_url": None,
                            "alias_urls": [],
                            "change_reason": "generated_from_bank_homepage",
                        },
                    ],
                    discovery_notes=[],
                    detail_source_ids=["AUTO-BMO-CHQ-detail"],
                ),
            ),
            patch(
                "api_service.source_catalog._upsert_source_registry_rows",
                side_effect=lambda _connection, rows: rows,
            ) as upsert_rows,
            patch(
                "api_service.source_catalog._deactivate_hard_scope_excluded_generated_detail_sources",
                return_value=0,
            ),
            patch(
                "api_service.source_catalog._deactivate_case_alias_generated_detail_sources",
                return_value=0,
            ),
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual(len(result.generated_rows), 1)
        self.assertEqual(result.generated_rows[0]["discovery_role"], "detail")
        upserted_rows = upsert_rows.call_args.args[1]
        self.assertEqual(len(upserted_rows), 1)
        self.assertEqual(upserted_rows[0]["source_id"], "AUTO-BMO-CHQ-detail")

    def test_materialize_sources_preserves_existing_detail_scope_when_no_detail_is_discovered(self) -> None:
        connection = _QueuedConnection([])

        with (
            patch(
                "api_service.source_catalog.require_product_type_definition",
                return_value=_product_type_definition("chequing"),
            ),
            patch(
                "api_service.source_catalog._generate_sources_from_homepage",
                return_value=HomepageSourceGenerationResult(
                    rows=[],
                    discovery_notes=["Homepage fetch was unavailable: timed out"],
                    detail_source_ids=[],
                ),
            ),
            patch(
                "api_service.source_catalog._load_existing_detail_rows_for_companion_discovery",
                return_value=[],
            ),
            patch("api_service.source_catalog._upsert_source_registry_rows") as upsert_rows,
            patch(
                "api_service.source_catalog._deactivate_hard_scope_excluded_generated_detail_sources",
                return_value=0,
            ) as deactivate_hard_scope,
        ):
            result = _materialize_sources_for_catalog_item(
                connection,
                row={
                    "bank_code": "BMO",
                    "bank_name": "Bank of Montreal",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                    "source_language": "en",
                },
            )

        self.assertEqual(result.generated_rows, [])
        self.assertIn(
            "Existing active detail sources were preserved because homepage discovery did not produce replacement detail sources.",
            result.discovery_notes,
        )
        upsert_rows.assert_not_called()
        deactivate_hard_scope.assert_called_once_with(
            connection,
            bank_code="BMO",
            country_code="CA",
            product_type="chequing",
        )
        self.assertEqual(connection.calls, [])

    def test_start_source_catalog_collection_queues_background_work_before_detail_outcome_is_known(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "catalog_item_id": "catalog-ca-bmo-chequing-12345678",
                        "bank_code": "BMO",
                        "country_code": "CA",
                        "product_type": "chequing",
                        "status": "active",
                        "bank_name": "Bank of Montreal",
                        "homepage_url": "https://www.bmo.com/en-ca/main/personal/",
                        "normalized_homepage_url": "https://www.bmo.com/en-ca/main/personal",
                        "source_language": "en",
                    }
                ]
            ]
        )

        with (
            patch("api_service.source_catalog._build_source_catalog_collection_run_id", return_value="run-001"),
            patch("api_service.source_catalog.new_id", side_effect=["collection-001", "corr-001"]),
            patch("api_service.source_catalog._insert_collection_run_row"),
            patch("api_service.source_catalog._launch_source_catalog_collection_runner") as launch_runner,
            patch("api_service.source_catalog._record_catalog_audit_event"),
        ):
            result = start_source_catalog_collection(
                connection,
                catalog_item_ids=["catalog-ca-bmo-chequing-12345678"],
                actor={"user_id": "usr-001", "role": "admin", "email": "admin@example.com"},
                request_context={"request_id": "req-001", "ip_address": "127.0.0.1", "user_agent": "test"},
            )

        self.assertEqual(result["run_ids"], ["run-001"])
        self.assertEqual(result["selected_source_ids"], [])
        self.assertEqual(result["materialized_items"], [])
        self.assertEqual(result["workflow_state"], "queued")
        launch_runner.assert_called_once()

    def test_launch_source_catalog_collection_runner_spawns_one_process_for_full_plan(self) -> None:
        plan = {
            "collection_id": "collection-001",
            "correlation_id": "corr-001",
            "request_id": "req-001",
            "trigger_type": "admin_source_catalog_collection",
            "triggered_by": "admin@example.com",
            "actor": {"user_id": "usr-001", "email": "admin@example.com", "role": "admin"},
            "groups": [
                {
                    "run_id": "run-001",
                    "catalog_item_id": "catalog-ca-bmo-chequing",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "source_language": "en",
                    "homepage_url": "https://www.bmo.com",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "selected_source_ids": [],
                    "target_source_ids": [],
                    "included_source_ids": [],
                    "included_sources": [],
                },
                {
                    "run_id": "run-002",
                    "catalog_item_id": "catalog-ca-bmo-savings",
                    "bank_code": "BMO",
                    "bank_name": "BMO",
                    "country_code": "CA",
                    "product_type": "savings",
                    "source_language": "en",
                    "homepage_url": "https://www.bmo.com",
                    "normalized_homepage_url": "https://www.bmo.com/",
                    "selected_source_ids": [],
                    "target_source_ids": [],
                    "included_source_ids": [],
                    "included_sources": [],
                },
            ],
        }

        repo_root = self._workspace_temp_path("launch-runner")
        with (
            patch("api_service.source_catalog.REPO_ROOT", repo_root),
            patch("api_service.source_catalog.subprocess.Popen") as popen,
        ):
            _launch_source_catalog_collection_runner(plan)

        self.assertEqual(popen.call_count, 1)
        persisted_plan = json.loads((repo_root / "tmp" / "source-catalog-collections" / "collection-001.json").read_text(encoding="utf-8"))
        self.assertEqual([group["run_id"] for group in persisted_plan["groups"]], ["run-001", "run-002"])

    def test_generate_sources_from_homepage_can_use_ai_to_resolve_detail_rows(self) -> None:
        homepage_html = """
        <html>
          <body>
            <a href="/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account/">
              Everyday transaction account
            </a>
          </body>
        </html>
        """
        detail_html = """
        <html>
          <head><title>BMO Performance Chequing Account</title></head>
          <body>
            <h1>BMO Performance Chequing Account</h1>
            <p>Monthly fee details, debit usage, and included transactions for day-to-day banking.</p>
          </body>
        </html>
        """
        with (
            patch("api_service.source_catalog.fetch_text", side_effect=[homepage_html, detail_html, detail_html]),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account": AiParallelCandidateScore(
                            candidate_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance-chequing-account",
                            predicted_role="detail",
                            relevance_score=8.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                            short_rationale="Likely official chequing detail page.",
                        )
                    },
                    notes=["AI parallel scorer evaluated 1 candidate link(s)."],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="Bank of Montreal",
                country_code="CA",
                product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                homepage_url="https://www.bmo.com/en-ca/main/personal/",
                source_language="en",
            )

        self.assertEqual(len(result.detail_source_ids), 1)
        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertEqual(len(detail_rows), 1)
        self.assertEqual(detail_rows[0]["discovery_metadata"]["selection_path"], "heuristic_plus_ai_plus_page_evidence")
        self.assertGreaterEqual(detail_rows[0]["discovery_metadata"]["page_evidence_score"], 4)
        self.assertIn("AI parallel scorer evaluated 1 candidate link(s).", result.discovery_notes)

    def test_selected_card_details_preserve_query_identified_pricing_companions(self) -> None:
        first_detail = "https://www.bankofamerica.com/credit-cards/products/travel-card"
        second_detail = "https://www.bankofamerica.com/credit-cards/products/cash-card"
        first_disclosure = (
            "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline"
            "?cId=4076236&isMobile=true&locale=en_US&poCd=D7"
        )
        second_disclosure = (
            "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline"
            "?cId=4078153&isMobile=true&locale=en_US&poCd=5R"
        )
        companions, notes = _discover_detail_companion_links(
            detail_rows=[
                {"normalized_url": first_detail, "raw_url": first_detail},
                {"normalized_url": second_detail, "raw_url": second_detail},
            ],
            country_code="US",
            product_type="credit-card",
            fetch_policy=SimpleNamespace(),
            hostname="www.bankofamerica.com",
            allowed_domains=("bankofamerica.com",),
            page_html_by_url={
                first_detail: (
                    f'<a href="{first_disclosure}">Pricing &amp; Terms</a>'
                    '<a href="/privacy/online-privacy-notice">Privacy terms</a>'
                    '<a href="/online-banking/service-agreement.go">Online Banking Service Agreement</a>'
                ),
                second_detail: f'<a href="{second_disclosure}">Details of Rate, Fee and Other Cost Information</a>',
            },
        )

        self.assertEqual(len(companions), 2)
        self.assertEqual(
            {item.link.normalized_url for item in companions},
            {
                "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline?cid=4076236&pocd=D7",
                "https://www.bankofamerica.com/salesservices/getDisclosurePDFInline?cid=4078153&pocd=5R",
            },
        )
        self.assertEqual(
            {item.parent_detail_url for item in companions},
            {first_detail, second_detail},
        )
        self.assertIn("2 exact-product", " ".join(notes))

    def test_existing_active_detail_can_supply_new_pricing_companion(self) -> None:
        homepage_url = "https://www.bank.example/"
        detail_url = "https://www.bank.example/cards/existing-card"
        disclosure_url = "https://www.bank.example/disclosures/card?offerId=offer-42&locale=en_US"

        def fake_fetch(url: str, _policy: object) -> str:
            normalized = normalize_source_url(url)
            if normalized == normalize_source_url(homepage_url):
                return "<html><body>Consumer banking</body></html>"
            if normalized == detail_url:
                return f'<a href="{disclosure_url}">Pricing and terms</a>'
            raise AssertionError(f"Unexpected fetch: {url}")

        with patch("api_service.source_catalog.fetch_text", side_effect=fake_fetch):
            companions, notes = _generate_existing_detail_companion_rows(
                bank_code="EX",
                bank_name="Example Bank",
                country_code="US",
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
                homepage_url=homepage_url,
                source_language="en",
                existing_detail_rows=[
                    {"normalized_url": detail_url, "raw_url": detail_url},
                ],
            )

        companion_rows = [
            item
            for item in companions
            if item["discovery_metadata"].get("selection_path") == "selected_existing_detail_companion"
        ]
        self.assertEqual(len(companion_rows), 1)
        self.assertEqual(
            companion_rows[0]["normalized_url"],
            "https://www.bank.example/disclosures/card?offerid=offer-42",
        )
        self.assertEqual(companion_rows[0]["discovery_metadata"]["parent_detail_url"], detail_url)
        self.assertIn("1 exact-product", " ".join(notes))

    def test_generate_sources_starts_from_verified_coverage_url_and_embedded_json_links(self) -> None:
        homepage_url = "https://www.bank.example/"
        coverage_url = "https://www.bank.example/credit-cards/"
        detail_url = "https://www.bank.example/credit-cards/products/travel-rewards-credit-card"
        embedded_catalog = json.dumps(
            {
                "products": [
                    {
                        "name": "Travel Rewards Credit Card",
                        "learnMore": {"path": "products/travel-rewards-credit-card/"},
                    }
                ]
            }
        )
        pages = {
            normalize_source_url(homepage_url): "<html><body>Bank homepage without product navigation</body></html>",
            normalize_source_url(coverage_url): f"<div data-product-catalog='{embedded_catalog}'></div>",
            detail_url: (
                "<html><head><title>Travel Rewards Credit Card</title></head><body>"
                "<h1>Travel Rewards Credit Card</h1><p>No annual fee and rewards on purchases.</p>"
                "</body></html>"
            ),
        }

        def fake_fetch(url: str, _policy: object) -> str:
            return pages[normalize_source_url(url)]

        with (
            patch("api_service.source_catalog.fetch_text", side_effect=fake_fetch),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch("api_service.source_catalog._load_seed_supporting_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        detail_url: AiParallelCandidateScore(
                            candidate_url=detail_url,
                            predicted_role="detail",
                            relevance_score=9.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                            short_rationale="Named credit card detail page.",
                        )
                    },
                    notes=[],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BANK",
                bank_name="Example Bank",
                country_code="US",
                product_type="credit-card",
                product_type_definition=_product_type_definition("credit-card"),
                homepage_url=homepage_url,
                coverage_source_url=coverage_url,
                source_language="en",
            )

        detail_urls = {
            item["normalized_url"]
            for item in result.rows
            if item["discovery_role"] == "detail"
        }
        self.assertIn(detail_url, detail_urls, (result.discovery_notes, result.rows))
        self.assertTrue(any("verified official Product Type coverage URL" in note for note in result.discovery_notes))

    def test_generate_sources_from_homepage_expands_secondary_product_category_hub(self) -> None:
        homepage_url = "https://www.examplebank.ca/"
        entry_url = "https://www.examplebank.ca/personal/credit-cards"
        category_url = "https://www.examplebank.ca/personal/credit-cards/cash-back-cards.html"
        detail_url = "https://www.examplebank.ca/personal/credit-cards/all-credit-cards/dividend-visa-infinite-card.html"
        pages = {
            homepage_url: '<a href="/personal/credit-cards">Credit cards</a>',
            entry_url: '<a href="/personal/credit-cards/cash-back-cards.html">Cash back cards</a>',
            category_url: (
                '<a href="/personal/credit-cards/all-credit-cards/dividend-visa-infinite-card.html">'
                "Dividend Visa Infinite Card</a>"
            ),
            detail_url: (
                "<html><head><title>Dividend Visa Infinite Card</title></head><body>"
                "<h1>Dividend Visa Infinite Card</h1><p>$120 annual fee. Purchase interest rate 21.99%.</p>"
                "</body></html>"
            ),
        }

        def fake_fetch(url: str, _policy: object) -> str:
            return pages[url]

        with (
            patch("api_service.source_catalog.fetch_text", side_effect=fake_fetch),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=entry_url),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch("api_service.source_catalog._load_seed_supporting_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        detail_url: AiParallelCandidateScore(
                            candidate_url=detail_url,
                            predicted_role="detail",
                            relevance_score=9.0,
                            confidence_band="high",
                            reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                            short_rationale="Official individual credit-card detail page.",
                        )
                    },
                    notes=["AI parallel scorer evaluated secondary-hub candidates."],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="EXAMPLE",
                bank_name="Example Bank",
                country_code="CA",
                product_type="credit-card",
                product_type_definition={
                    **_product_type_definition("credit-card"),
                    "description": "Credit cards with annual fees, purchase rates, cash advance rates, and rewards.",
                    "discovery_keywords": ["credit card", "visa", "mastercard", "annual fee"],
                    "expected_fields": ["product_name", "annual_fee", "purchase_interest_rate"],
                },
                homepage_url=homepage_url,
                source_language="en",
            )

        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertIn(detail_url, {item["normalized_url"] for item in detail_rows})
        self.assertTrue(any("secondary product-category hub" in note for note in result.discovery_notes))

    def test_secondary_catalog_hub_detection_is_plural_and_excludes_operational_pages(self) -> None:
        self.assertTrue(
            _looks_like_secondary_catalog_hub(
                product_type="credit-card",
                normalized_url="https://www.examplebank.ca/credit-cards/travel-rewards-cards.html",
                anchor_text="Travel rewards cards",
            )
        )
        self.assertFalse(
            _looks_like_secondary_catalog_hub(
                product_type="credit-card",
                normalized_url="https://www.examplebank.ca/credit-cards/dividend-visa-infinite-card.html",
                anchor_text="Dividend Visa Infinite Card",
            )
        )
        self.assertFalse(
            _looks_like_secondary_catalog_hub(
                product_type="credit-card",
                normalized_url="https://www.examplebank.ca/credit-cards/compare-cards.html",
                anchor_text="Compare credit cards",
            )
        )

    def test_strong_page_evidence_override_applies_across_product_types(self) -> None:
        cases = [
            {
                "product_type": "chequing",
                "url": "https://www.examplebank.ca/personal/accounts/no-fee-echequing",
                "label": "No Fee eChequing",
                "title": "No Fee eChequing Account",
                "heading": "No Fee eChequing Account",
            },
            {
                "product_type": "credit-card",
                "url": "https://www.examplebank.ca/personal/credit-cards/cash-back-visa",
                "label": "Cash Back Visa Card",
                "title": "Cash Back Visa Card",
                "heading": "Cash Back Visa Card",
            },
            {
                "product_type": "mortgage",
                "url": "https://www.examplebank.ca/personal/mortgages/fixed-rate-mortgage",
                "label": "Fixed Rate Mortgage",
                "title": "Fixed Rate Mortgage",
                "heading": "Fixed Rate Mortgage",
            },
        ]

        for case in cases:
            with self.subTest(product_type=case["product_type"]):
                candidate = HomepageCandidate(
                    normalized_url=str(case["url"]),
                    raw_url=str(case["url"]),
                    anchor_text=str(case["label"]),
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=2,
                    supporting_signal=True,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=candidate.normalized_url,
                    predicted_role="supporting_html",
                    relevance_score=6.0,
                    confidence_band="medium",
                    reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
                    short_rationale="Useful product page, but scorer conservatively classified it as supporting.",
                )
                page_evidence = PageEvidenceAssessment(
                    page_evidence_score=9,
                    page_evidence_reason_codes=[
                        "product_identity_signal",
                        "title_semantic_match",
                        "detail_page_layout_signal",
                        "product_type_semantic_match",
                        "pricing_or_feature_signal",
                    ],
                    page_title=str(case["title"]),
                    primary_heading=str(case["heading"]),
                    heading_match=True,
                    attribute_signal_count=4,
                    negative_signal_count=0,
                )

                self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=page_evidence))

    def test_supporting_page_veto_blocks_detail_override_across_product_types(self) -> None:
        cases = [
            ("chequing", "https://www.examplebank.ca/wire-transfers", "not_product_detail"),
            ("savings", "https://www.examplebank.ca/savings-rates", "supporting_terms_or_rates_page"),
            ("credit-card", "https://www.examplebank.ca/credit-card-rates", "supporting_terms_or_rates_page"),
            ("mortgage", "https://www.examplebank.ca/mortgage-calculator", "not_product_detail"),
        ]

        for product_type, url, veto_reason in cases:
            with self.subTest(product_type=product_type):
                candidate = HomepageCandidate(
                    normalized_url=url,
                    raw_url=url,
                    anchor_text="Support page",
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=4,
                    supporting_signal=True,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=url,
                    predicted_role="supporting_html",
                    relevance_score=8.0,
                    confidence_band="high",
                    reason_codes=[veto_reason, "pricing_or_feature_signal"],
                    short_rationale="Relevant supporting material, not a named product detail page.",
                )
                page_evidence = PageEvidenceAssessment(
                    page_evidence_score=9,
                    page_evidence_reason_codes=[
                        "product_identity_signal",
                        "title_semantic_match",
                        "detail_page_layout_signal",
                        "pricing_or_feature_signal",
                    ],
                    page_title="Product rates and tools",
                    primary_heading="Product rates and tools",
                    heading_match=True,
                    attribute_signal_count=4,
                    negative_signal_count=0,
                    product_identity_match=True,
                )

                self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=page_evidence))

    def test_generate_sources_from_homepage_promotes_alterna_no_fee_echequing_detail(self) -> None:
        homepage_html = """
        <html>
          <body>
            <a href="/en/personal/accounts/no-fee-echequing">No Fee eChequing</a>
            <a href="/en/personal/rates/chequing-savings">Chequing & Savings rates</a>
          </body>
        </html>
        """
        detail_html = """
        <html>
          <head><title>Alterna Bank - No Fee eChequing</title></head>
          <body>
            <h1>No-Fee eChequing Account</h1>
            <p>Our chequing account offers day-to-day transactions with no monthly fee.</p>
            <p>FREE, unlimited day-to-day transactions and Interac e-Transfers.</p>
            <p>No minimum balance is required, and overdraft protection is available.</p>
          </body>
        </html>
        """

        candidate_url = "https://www.alternabank.ca/en/personal/accounts/no-fee-echequing"
        with (
            patch("api_service.source_catalog.fetch_text", side_effect=[homepage_html, detail_html, detail_html]),
            patch("api_service.source_catalog._load_seed_entry_url", return_value=None),
            patch("api_service.source_catalog._load_seed_detail_hints", return_value=[]),
            patch("api_service.source_catalog._load_seed_supporting_hints", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        candidate_url: AiParallelCandidateScore(
                            candidate_url=candidate_url,
                            predicted_role="supporting_html",
                            relevance_score=6.0,
                            confidence_band="medium",
                            reason_codes=["product_type_semantic_match", "pricing_or_feature_signal"],
                            short_rationale="The No Fee eChequing page is the strongest chequing match.",
                        )
                    },
                    notes=["Scored Alterna Bank homepage-discovered candidate links for chequing-product relevance."],
                ),
            ),
        ):
            result = _generate_sources_from_homepage(
                bank_code="ALTERNA",
                bank_name="Alterna Bank",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing account for everyday transactions, debit card payments, bill payments, transfers, fees, and overdraft.",
                    "discovery_keywords": ["chequing account", "chequing", "no monthly fee", "unlimited transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.alternabank.ca/en/personal",
                source_language="en",
            )

        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertEqual(len(detail_rows), 1)
        self.assertEqual(detail_rows[0]["normalized_url"], candidate_url)
        self.assertEqual(detail_rows[0]["discovery_metadata"]["ai_predicted_role"], "supporting_html")
        self.assertIn("strong_page_evidence_detail_override", detail_rows[0]["discovery_metadata"]["selection_reason_codes"])

    def test_chequing_support_pages_do_not_override_ai_supporting_role(self) -> None:
        cases = [
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/wire-transfers",
                "Wire Transfers",
                "Send and receive wire transfers through online banking for everyday transactions.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/external-account-transfers",
                "External Account Transfers",
                "Move money between an external account and online banking.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/accounts/ways-to-bank/debit-cards",
                "Debit Cards",
                "Use a debit card for everyday transactions and Interac purchases.",
                ["not_product_detail", "pricing_or_feature_signal"],
            ),
            (
                "https://www.examplebank.ca/personal/rates/chequing-savings",
                "Chequing & Savings Rates",
                "Current rates for chequing and savings accounts.",
                ["supporting_terms_or_rates_page", "pricing_or_feature_signal"],
            ),
        ]
        definition = {
            **_product_type_definition("chequing"),
            "description": "A chequing account for everyday transactions, debit payments, transfers, fees, and overdraft.",
            "discovery_keywords": ["chequing account", "everyday banking", "debit card", "transfers"],
        }

        for url, heading, body, reason_codes in cases:
            with self.subTest(url=url), patch(
                "api_service.source_catalog.fetch_text",
                return_value=f"<html><head><title>{heading}</title></head><body><h1>{heading}</h1><p>{body}</p></body></html>",
            ):
                evidence = _score_page_evidence(
                    raw_url=url,
                    fetch_policy=SimpleNamespace(),
                    product_type="chequing",
                    product_type_definition=definition,
                )
                candidate = HomepageCandidate(
                    normalized_url=url,
                    raw_url=url,
                    anchor_text=heading,
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=4,
                    supporting_signal="rates" in url,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_score = AiParallelCandidateScore(
                    candidate_url=url,
                    predicted_role="supporting_html",
                    relevance_score=7.0,
                    confidence_band="high",
                    reason_codes=reason_codes,
                    short_rationale="Relevant support page, not a named chequing product.",
                )

                self.assertFalse(evidence.product_identity_match)
                self.assertNotIn("product_identity_signal", evidence.page_evidence_reason_codes)
                self.assertFalse(_candidate_promotes_to_detail(candidate=candidate, ai_score=ai_score, page_evidence=evidence))

    def test_repeated_support_attribute_counts_once(self) -> None:
        definition = {
            **_product_type_definition("chequing"),
            "description": "A chequing account supporting transfers.",
            "discovery_keywords": ["chequing account"],
        }
        html = "<html><head><title>Wire Transfers</title></head><body><h1>Wire Transfers</h1><p>Transfers transfers transfers.</p></body></html>"
        with patch("api_service.source_catalog.fetch_text", return_value=html):
            evidence = _score_page_evidence(
                raw_url="https://www.examplebank.ca/ways-to-bank/wire-transfers",
                fetch_policy=SimpleNamespace(),
                product_type="chequing",
                product_type_definition=definition,
            )

        self.assertEqual(evidence.attribute_signal_count, 1)

    def test_deactivates_only_explicitly_rejected_generated_detail_sources(self) -> None:
        connection = _QueuedConnection([2])

        count = _deactivate_rejected_generated_detail_sources(
            connection,
            bank_code="ALTERNA",
            product_type="chequing",
            normalized_urls=[
                "https://www.alternabank.ca/en/personal/accounts/ways-to-bank/wire-transfers",
                "https://www.alternabank.ca/en/personal/rates/chequing-savings",
            ],
        )

        self.assertEqual(count, 2)
        sql, params = connection.calls[0]
        self.assertIn("seed_source_flag = false", sql)
        self.assertIn("source_id LIKE 'AUTO-%%'", sql)
        self.assertEqual(len(params["normalized_urls"]), 2)

    def test_deactivates_stale_generated_case_only_detail_alias(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "source_id": "AUTO-VANCITY-CRE-old",
                        "normalized_url": "https://www.vancity.com/Bank/Credit-cards/enviro-Infinite",
                    },
                    {
                        "source_id": "AUTO-VANCITY-CRE-other",
                        "normalized_url": "https://www.vancity.com/bank/credit-cards/enviro-gold",
                    },
                ],
                1,
            ]
        )

        count = _deactivate_case_alias_generated_detail_sources(
            connection,
            bank_code="VANCITY",
            product_type="credit-card",
            selected_normalized_urls=[
                "https://www.vancity.com/bank/credit-cards/enviro-infinite",
            ],
        )

        self.assertEqual(count, 1)
        update_sql, update_params = connection.calls[1]
        self.assertIn("superseded_case_only_url_alias", update_sql)
        self.assertEqual(update_params["source_ids"], ["AUTO-VANCITY-CRE-old"])

    def test_deactivates_existing_generated_detail_with_hard_retail_scope_exclusion(self) -> None:
        connection = _QueuedConnection(
            [
                [
                    {
                        "source_id": "AUTO-OAKEN-GIC-commercial",
                        "normalized_url": "https://oaken.com/en-ca/commercial",
                        "source_name": "Oaken Commercial GICs",
                        "discovery_metadata": {
                            "page_title": "Commercial GICs - Organization Savings",
                            "primary_heading": "Oaken Commercial GICs",
                        },
                    },
                    {
                        "source_id": "AUTO-OAKEN-GIC-personal",
                        "normalized_url": "https://oaken.com/en-ca/guaranteed-investment-certificate",
                        "source_name": "Oaken Personal GICs",
                        "discovery_metadata": {"primary_heading": "Guaranteed Investment Certificates"},
                    },
                ],
                1,
            ]
        )

        count = _deactivate_hard_scope_excluded_generated_detail_sources(
            connection,
            bank_code="OAKEN",
            country_code="CA",
            product_type="gic",
        )

        self.assertEqual(count, 1)
        update_sql, update_params = connection.calls[1]
        self.assertIn("status = 'inactive'", update_sql)
        self.assertEqual(update_params["source_ids"], ["AUTO-OAKEN-GIC-commercial"])
        self.assertIn("non_consumer_business_page", update_params["change_reason"])

    def test_page_evidence_does_not_treat_product_cta_copy_as_negative(self) -> None:
        detail_html = """
        <html>
          <head><title>High Interest Savings Account</title></head>
          <body>
            <h1>High Interest Savings Account</h1>
            <p>Earn interest on your balance with no monthly fee and flexible withdrawals.</p>
            <a href="/apply">Apply now</a>
            <a href="/open-account">Open account</a>
          </body>
        </html>
        """

        with patch("api_service.source_catalog.fetch_text", return_value=detail_html):
            result = _score_page_evidence(
                raw_url="https://www.examplebank.ca/savings/high-interest",
                fetch_policy=SimpleNamespace(),
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "display_name": "Savings",
                    "description": "Savings account with interest, fee, balance, and withdrawal details.",
                    "discovery_keywords": ["savings account", "interest", "withdrawal"],
                },
            )

        self.assertGreaterEqual(result.page_evidence_score, 4)
        self.assertEqual(result.negative_signal_count, 0)

    def test_seed_detail_source_is_promoted_when_page_evidence_fetch_is_unavailable(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical-chequing-account",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical-chequing-account/",
            anchor_text="BMO Practical Chequing Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=8,
            supporting_signal=False,
            seed_source_id="BMO-CHQ-002",
            source_name_hint="BMO Practical Chequing Account",
            priority_hint="P0",
            expected_fields_hint=["product_name", "monthly_fee", "included_transactions"],
        )

        with patch(
            "api_service.source_catalog._score_page_evidence",
            return_value=PageEvidenceAssessment(
                page_evidence_score=0,
                page_evidence_reason_codes=["page_fetch_unavailable"],
                page_title=None,
                primary_heading=None,
                heading_match=False,
                attribute_signal_count=0,
                negative_signal_count=0,
                fetch_error="timed out",
            ),
        ):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="chequing",
                discovery_product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[candidate],
                ai_scores={},
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "BMO-CHQ-002")
        self.assertEqual(rows[0]["discovery_role"], "detail")
        self.assertEqual(rows[0]["discovery_metadata"]["selection_path"], "seed_hint_fetch_unavailable")
        self.assertIn("seed-backed source", " ".join(notes))

    def test_seed_detail_low_page_evidence_with_negative_signal_is_not_promoted(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic/",
            anchor_text="BMO Progressive GIC",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-GIC-003",
            source_name_hint="BMO Progressive GIC detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "term_options", "minimum_deposit"],
        )
        ai_scores = {
            candidate.normalized_url: AiParallelCandidateScore(
                candidate_url=candidate.normalized_url,
                predicted_role="detail",
                relevance_score=0.98,
                confidence_band="high",
                reason_codes=["contains_gic_keyword", "product_specific_slug"],
                short_rationale="Likely an official product detail page, but page evidence is weak.",
            )
        }

        with patch(
            "api_service.source_catalog._score_page_evidence",
            return_value=PageEvidenceAssessment(
                page_evidence_score=3,
                page_evidence_reason_codes=[
                    "title_semantic_match",
                    "product_type_semantic_match",
                    "pricing_or_feature_signal",
                    "insufficient_evidence",
                ],
                page_title="Progressive GIC Search Tool - BMO",
                primary_heading=None,
                heading_match=False,
                attribute_signal_count=1,
                negative_signal_count=1,
            ),
        ):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                discovery_product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit.",
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[candidate],
                ai_scores=ai_scores,
            )

        self.assertEqual(rows, [])
        self.assertIn("rejected all tentative detail pages", " ".join(notes))

    def test_seed_detail_candidates_are_not_displaced_by_high_scoring_homepage_links(self) -> None:
        seed_candidates = [
            HomepageCandidate(
                normalized_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/seed-{index}",
                raw_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/seed-{index}/",
                anchor_text=f"Seed {index}",
                source_type="html",
                origin="seed_detail_hint",
                heuristic_score=0,
                supporting_signal=False,
                seed_source_id=f"BMO-CHQ-00{index}",
                source_name_hint=f"BMO seed {index}",
                priority_hint="P0",
                expected_fields_hint=["product_name"],
            )
            for index in range(1, 6)
        ]
        homepage_candidates = [
            HomepageCandidate(
                normalized_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/high-score-{index}",
                raw_url=f"https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/high-score-{index}/",
                anchor_text=f"High score {index}",
                source_type="html",
                origin="homepage_or_hub_link",
                heuristic_score=20,
                supporting_signal=False,
                seed_source_id=None,
                source_name_hint=None,
                priority_hint=None,
                expected_fields_hint=[],
            )
            for index in range(1, 8)
        ]

        ordered = _ordered_detail_candidates(candidates=[*homepage_candidates, *seed_candidates], ai_scores={})

        self.assertEqual([item.seed_source_id for item in ordered[:5]], [f"BMO-CHQ-00{index}" for index in range(1, 6)])
        self.assertEqual(len([item for item in ordered if item.seed_source_id]), 5)
        self.assertGreater(len([item for item in ordered if not item.seed_source_id]), 0)

    def test_seed_detail_rejection_does_not_block_ai_scored_homepage_detail(self) -> None:
        seed_candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic/",
            anchor_text="BMO Progressive GIC",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-GIC-003",
            source_name_hint="BMO Progressive GIC detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "term_options", "minimum_deposit"],
        )
        homepage_candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/main/personal/investments/gic/special-rate-gic",
            raw_url="https://www.bmo.com/main/personal/investments/gic/special-rate-gic/",
            anchor_text="Special Rate GIC",
            source_type="html",
            origin="homepage_or_hub_link",
            heuristic_score=4,
            supporting_signal=False,
            seed_source_id=None,
            source_name_hint=None,
            priority_hint=None,
            expected_fields_hint=[],
        )
        ai_scores = {
            homepage_candidate.normalized_url: AiParallelCandidateScore(
                candidate_url=homepage_candidate.normalized_url,
                predicted_role="detail",
                relevance_score=6.0,
                confidence_band="high",
                reason_codes=["product_type_semantic_match", "detail_page_layout_signal"],
                short_rationale="Likely an official GIC detail page.",
            )
        }

        def fake_page_evidence(*, raw_url: str, **_: object) -> PageEvidenceAssessment:
            if "progressive-gic" in raw_url:
                return PageEvidenceAssessment(
                    page_evidence_score=3,
                    page_evidence_reason_codes=["insufficient_evidence"],
                    page_title="Progressive GIC Search Tool - BMO",
                    primary_heading=None,
                    heading_match=False,
                    attribute_signal_count=1,
                    negative_signal_count=1,
                )
            return PageEvidenceAssessment(
                page_evidence_score=8,
                page_evidence_reason_codes=["title_semantic_match", "detail_page_layout_signal", "pricing_or_feature_signal"],
                page_title="Special Rate GIC",
                primary_heading="Special Rate GIC",
                heading_match=True,
                attribute_signal_count=3,
                negative_signal_count=0,
            )

        with patch("api_service.source_catalog._score_page_evidence", side_effect=fake_page_evidence):
            rows, _rejected_urls, notes = _promote_detail_candidates(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                discovery_product_type="gic",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit.",
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                source_language="en",
                fetch_policy=SimpleNamespace(),
                candidates=[seed_candidate, homepage_candidate],
                ai_scores=ai_scores,
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["normalized_url"], homepage_candidate.normalized_url)
        self.assertEqual(rows[0]["discovery_metadata"]["selection_path"], "heuristic_plus_ai_plus_page_evidence")
        self.assertIn("promoted 1 detail source", " ".join(notes))

    def test_seed_detail_candidate_can_promote_despite_page_negative_terms(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical/",
            anchor_text="BMO Practical Chequing Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=0,
            supporting_signal=False,
            seed_source_id="BMO-CHQ-002",
            source_name_hint="BMO Practical Chequing Account",
            priority_hint="P0",
            expected_fields_hint=["product_name"],
        )
        page_evidence = PageEvidenceAssessment(
            page_evidence_score=5,
            page_evidence_reason_codes=["title_semantic_match", "insufficient_evidence"],
            page_title="Low Fee Chequing Account: Practical Chequing Account - BMO Canada",
            primary_heading="Practical Chequing Account",
            heading_match=True,
            attribute_signal_count=2,
            negative_signal_count=3,
        )

        self.assertTrue(_candidate_promotes_to_detail(candidate=candidate, ai_score=None, page_evidence=page_evidence))

    def test_generate_sources_from_homepage_uses_exact_product_type_seed_details(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Savings Account",
            primary_heading="BMO Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004", "BMO-SAV-005"}.issubset(source_ids))
        self.assertIn("BMO-SAV-006", source_ids)
        self.assertIn("BMO-SAV-007", source_ids)
        self.assertTrue(all(str(item["product_type"]) == "savings" for item in result.rows))

    def test_generate_sources_from_homepage_uses_seed_hints_for_known_bank_code_aliases(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="TD ePremium Savings Account",
            primary_heading="TD ePremium Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="TB",
                bank_name="TD Bank",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.td.com/",
                source_language="en",
            )

        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertGreaterEqual(len(detail_rows), 1)
        self.assertTrue(all(item["bank_code"] == "TB" for item in detail_rows))
        self.assertTrue(all(str(item["source_id"]).startswith("AUTO-TB-") for item in detail_rows))
        self.assertTrue(any("td.com" in item["normalized_url"] for item in detail_rows))

    def test_generate_sources_from_homepage_promotes_cibc_seed_details_when_ai_is_unavailable(self) -> None:
        weak_but_official_seed_evidence = PageEvidenceAssessment(
            page_evidence_score=3,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal", "insufficient_evidence"],
            page_title="CIBC Smart Account",
            primary_heading="CIBC Smart Account",
            heading_match=True,
            attribute_signal_count=1,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={},
                    notes=[
                        "AI parallel scorer was unavailable: OpenAI Responses API request failed with status 429: insufficient_quota",
                        "Deterministic homepage discovery fallback will evaluate bounded candidates.",
                    ],
                    ai_unavailable=True,
                ),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_but_official_seed_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing accounts for everyday banking with monthly fees, debit transactions, Interac, and overdraft.",
                    "discovery_keywords": ["chequing", "chequing account", "monthly fee", "transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.cibc.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"CIBC-CHQ-002", "CIBC-CHQ-003"}.issubset(source_ids))
        detail_rows = [item for item in result.rows if item["source_id"] in {"CIBC-CHQ-002", "CIBC-CHQ-003"}]
        self.assertTrue(all(item["discovery_metadata"]["selection_path"] == "seed_hint_ai_unavailable_low_page_evidence" for item in detail_rows))
        self.assertTrue(all(item["discovery_metadata"]["ai_unavailable"] for item in detail_rows))
        self.assertTrue(all("fee_waiver_condition" not in item["expected_fields"] for item in detail_rows))
        self.assertTrue(all("included_transactions" in item["expected_fields"] for item in detail_rows))
        self.assertTrue(all("minimum_balance" in item["expected_fields"] for item in detail_rows))
        self.assertTrue(any("Deterministic homepage discovery fallback" in note for note in result.discovery_notes))

    def test_generate_sources_from_homepage_keeps_cibc_seed_details_when_ai_scores_but_page_evidence_is_weak(self) -> None:
        weak_but_official_seed_evidence = PageEvidenceAssessment(
            page_evidence_score=3,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal", "insufficient_evidence"],
            page_title="CIBC Smart Account",
            primary_heading="CIBC Smart Account",
            heading_match=True,
            attribute_signal_count=1,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(
                    scores={
                        "https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html": AiParallelCandidateScore(
                            candidate_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
                            predicted_role="supporting_html",
                            relevance_score=3.0,
                            confidence_band="medium",
                            reason_codes=["pricing_or_feature_signal"],
                            short_rationale="Useful chequing account page but scorer was uncertain.",
                        )
                    },
                    notes=["Scored CIBC candidate links for chequing-account homepage-first discovery."],
                ),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_but_official_seed_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Chequing accounts for everyday banking with monthly fees, debit transactions, Interac, and overdraft.",
                    "discovery_keywords": ["chequing", "chequing account", "monthly fee", "transactions"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.cibc.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"CIBC-CHQ-002", "CIBC-CHQ-003"}.issubset(source_ids))
        detail_row = next(item for item in result.rows if item["source_id"] == "CIBC-CHQ-002")
        self.assertEqual(detail_row["discovery_metadata"]["selection_path"], "seed_hint_low_page_evidence")
        self.assertEqual(detail_row["discovery_metadata"]["ai_predicted_role"], "supporting_html")

    def test_generate_sources_from_homepage_uses_definition_semantics_for_discovery_profile(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Savings Account",
            primary_heading="BMO Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="saving",
                product_type_definition={
                    **_product_type_definition("saving"),
                    "display_name": "Savings",
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004", "BMO-SAV-005"}.issubset(source_ids))
        self.assertTrue(all(str(item["product_type"]) == "saving" for item in result.rows))
        self.assertTrue(any("used `savings` discovery signals" in note for note in result.discovery_notes))

    def test_product_type_discovery_profile_uses_code_terms_for_gic_term_deposit(self) -> None:
        self.assertEqual(
            _product_type_discovery_profile(
                "gic-term-deposit",
                {
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "Term Deposit",
                    "description": "Deposit product.",
                    "discovery_keywords": [],
                },
            ),
            "gic",
        )

    def test_generate_sources_from_homepage_keeps_seed_detail_when_ai_marks_irrelevant(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="BMO Progressive GIC",
            primary_heading="BMO Progressive GIC",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )
        ai_scores = {
            "https://www.bmo.com/main/personal/investments/gic/progressive-gic": AiParallelCandidateScore(
                candidate_url="https://www.bmo.com/main/personal/investments/gic/progressive-gic",
                predicted_role="irrelevant",
                relevance_score=0.1,
                confidence_band="low",
                reason_codes=["insufficient_evidence"],
                short_rationale="AI scorer was not confident.",
            )
        }

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores=ai_scores, notes=["AI marked seed as irrelevant"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit with rate, term, redeemability, and minimum deposit details.",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate", "maturity"],
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertIn("BMO-GIC-003", source_ids)
        detail_row = next(item for item in result.rows if item["source_id"] == "BMO-GIC-003")
        self.assertEqual(detail_row["product_type"], "gic-term-deposit")
        self.assertEqual(detail_row["discovery_metadata"]["ai_predicted_role"], "irrelevant")
        self.assertTrue(any("used `gic` discovery signals" in note for note in result.discovery_notes))

    def test_generate_sources_from_homepage_keeps_seed_detail_with_low_page_evidence(self) -> None:
        low_evidence = PageEvidenceAssessment(
            page_evidence_score=1,
            page_evidence_reason_codes=["insufficient_evidence"],
            page_title="BMO Progressive GIC Search Tool",
            primary_heading="Progressive GIC Search Tool",
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=low_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "display_name": "GIC Term Deposit",
                    "description": "Guaranteed investment certificate or term deposit with rate, term, redeemability, and minimum deposit details.",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate", "maturity"],
                    "expected_fields": ["product_name", "term_options", "minimum_deposit"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        detail_row = next(item for item in result.rows if item["source_id"] == "BMO-GIC-003")
        self.assertEqual(detail_row["product_type"], "gic-term-deposit")
        self.assertEqual(detail_row["discovery_metadata"]["selection_path"], "seed_hint_low_page_evidence")
        self.assertTrue(any("low page evidence" in note for note in result.discovery_notes))

    def test_ai_candidate_scorer_accepts_discovery_product_type_profile(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
            raw_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier/",
            anchor_text="Savings Amplifier",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=3,
            supporting_signal=False,
            seed_source_id="BMO-SAV-002",
            source_name_hint="BMO Savings Amplifier Account",
            priority_hint="P0",
            expected_fields_hint=["product_name"],
        )

        with patch("api_service.source_catalog.os.getenv", side_effect=lambda key, default="": "openai" if key == "FPDS_LLM_PROVIDER" else ""):
            result = _score_candidate_links_with_ai(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="saving",
                discovery_product_type="savings",
                product_type_definition={
                    **_product_type_definition("saving"),
                    "display_name": "Savings",
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                },
                source_language="en",
                homepage_url="https://www.bmo.com/",
                normalized_homepage_url="https://www.bmo.com/",
                homepage_fetch_error=None,
                candidates=[candidate],
            )

        self.assertEqual(result.scores, {})
        self.assertTrue(any("provider or API key was not configured" in note for note in result.notes))
        self.assertTrue(result.ai_unavailable)

    def test_ai_candidate_scorer_records_failed_execution_when_openai_quota_is_exceeded(self) -> None:
        candidate = HomepageCandidate(
            normalized_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
            raw_url="https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html",
            anchor_text="CIBC Smart Account",
            source_type="html",
            origin="seed_detail_hint",
            heuristic_score=8,
            supporting_signal=False,
            seed_source_id="CIBC-CHQ-002",
            source_name_hint="CIBC Smart Account detail source",
            priority_hint="P0",
            expected_fields_hint=["product_name", "monthly_fee"],
        )

        def fake_getenv(key: str, default: str = "") -> str:
            values = {
                "FPDS_LLM_PROVIDER": "openai",
                "FPDS_LLM_API_KEY": "test-key",
                "FPDS_LLM_MODEL": "gpt-test",
            }
            return values.get(key, default)

        with (
            patch("api_service.source_catalog.os.getenv", side_effect=fake_getenv),
            patch(
                "api_service.source_catalog._invoke_openai_parallel_scorer",
                side_effect=RuntimeError("OpenAI Responses API request failed with status 429: insufficient_quota"),
            ),
        ):
            result = _score_candidate_links_with_ai(
                bank_code="CIBC",
                bank_name="CIBC",
                country_code="CA",
                product_type="chequing",
                discovery_product_type="chequing",
                product_type_definition=_product_type_definition("chequing"),
                source_language="en",
                homepage_url="https://www.cibc.com/",
                normalized_homepage_url="https://www.cibc.com/",
                homepage_fetch_error=None,
                candidates=[candidate],
                run_id="run-cibc-chequing",
                correlation_id="corr-001",
                request_id="req-001",
            )

        self.assertEqual(result.scores, {})
        self.assertTrue(result.ai_unavailable)
        self.assertIsNotNone(result.model_execution_record)
        assert result.model_execution_record is not None
        self.assertEqual(result.model_execution_record["execution_status"], "failed")
        self.assertEqual(result.model_execution_record["execution_metadata"]["fallback_mode"], "deterministic")
        self.assertIn("429", result.model_execution_record["execution_metadata"]["error_summary"])
        self.assertTrue(any("Deterministic homepage discovery fallback" in note for note in result.notes))

    def test_generate_sources_from_homepage_uses_bmo_seed_details_and_filters_unrelated_support(self) -> None:
        homepage_links = [
            SimpleNamespace(
                normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
                resolved_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier/",
                anchor_text="Savings Amplifier High interest rate",
                source_type="html",
            ),
            SimpleNamespace(
                normalized_url="https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
                resolved_url="https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
                anchor_text="Modern Slavery Act Statement",
                source_type="pdf",
            ),
            SimpleNamespace(
                normalized_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/global-terms-and-conditions",
                resolved_url="https://www.bmo.com/en-ca/main/personal/bank-accounts/global-terms-and-conditions#onehundredandsix",
                anchor_text="106",
                source_type="html",
            ),
        ]
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "detail_page_layout_signal", "pricing_or_feature_signal"],
            page_title="BMO Chequing Account",
            primary_heading="BMO Chequing Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=homepage_links),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="Bank of Montreal",
                country_code="CA",
                product_type="chequing",
                product_type_definition={
                    **_product_type_definition("chequing"),
                    "description": "Daily transaction account with monthly fee, debit card usage, and banking-plan benefits.",
                    "discovery_keywords": ["chequing", "daily banking", "banking plan"],
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        source_ids = {str(item["source_id"]) for item in result.rows}
        self.assertTrue({"BMO-CHQ-002", "BMO-CHQ-003", "BMO-CHQ-004", "BMO-CHQ-005", "BMO-CHQ-008"}.issubset(source_ids))
        self.assertIn("BMO-CHQ-006", source_ids)
        self.assertIn("BMO-CHQ-007", source_ids)
        self.assertNotIn(
            "https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts/savings-amplifier",
            {str(item["normalized_url"]) for item in result.rows},
        )
        self.assertNotIn(
            "https://www.bmo.com/pdfs/bmo_statement_against_modern_slavery_and_human_trafficking.pdf",
            {str(item["normalized_url"]) for item in result.rows},
        )
        terms_row = next(item for item in result.rows if item["source_id"] == "BMO-CHQ-007")
        self.assertEqual(terms_row["source_name"], "BMO bank account terms and conditions")

    def test_generate_sources_from_homepage_uses_seed_entry_url_for_known_bank_aliases(self) -> None:
        detail_evidence = PageEvidenceAssessment(
            page_evidence_score=7,
            page_evidence_reason_codes=["title_semantic_match", "pricing_or_feature_signal"],
            page_title="Scotiabank Savings Account",
            primary_heading="Scotiabank Savings Account",
            heading_match=True,
            attribute_signal_count=3,
            negative_signal_count=0,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="SCOTIABANK",
                bank_name="Scotiabank",
                country_code="CA",
                product_type="savings",
                product_type_definition={
                    **_product_type_definition("savings"),
                    "description": "Savings account with interest rates, balances, withdrawals, and tiering.",
                    "discovery_keywords": ["savings", "interest rate", "balance"],
                    "expected_fields": ["product_name", "interest_rate_summary", "monthly_fee"],
                },
                homepage_url="https://www.scotiabank.com/",
                source_language="en",
            )

        entry_row = next(item for item in result.rows if item["discovery_role"] == "entry")
        self.assertEqual(
            entry_row["normalized_url"],
            "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts.html",
        )
        self.assertEqual(entry_row["discovery_metadata"]["candidate_origin"], "seed_entry_hint")
        detail_rows = [item for item in result.rows if item["discovery_role"] == "detail"]
        self.assertGreaterEqual(len(detail_rows), 1)
        self.assertTrue(all(str(item["source_id"]).startswith("AUTO-SCOTIABANK-SAV-") for item in detail_rows))

    def test_generate_sources_from_homepage_keeps_seed_entry_when_detail_validation_fails(self) -> None:
        weak_detail_evidence = PageEvidenceAssessment(
            page_evidence_score=0,
            page_evidence_reason_codes=["insufficient_evidence"],
            page_title="Search Tool",
            primary_heading="Search Tool",
            heading_match=False,
            attribute_signal_count=0,
            negative_signal_count=1,
        )

        with (
            patch("api_service.source_catalog.fetch_text", return_value="<html></html>"),
            patch("api_service.source_catalog._extract_allowed_links", return_value=[]),
            patch(
                "api_service.source_catalog._score_candidate_links_with_ai",
                return_value=AiParallelScoringResult(scores={}, notes=["AI unavailable"]),
            ),
            patch("api_service.source_catalog._score_page_evidence", return_value=weak_detail_evidence),
        ):
            result = _generate_sources_from_homepage(
                bank_code="BMO",
                bank_name="BMO",
                country_code="CA",
                product_type="gic-term-deposit",
                product_type_definition={
                    **_product_type_definition("gic-term-deposit"),
                    "description": "Guaranteed investment certificate and term deposit product type",
                    "discovery_keywords": ["gic", "term deposit", "guaranteed investment certificate"],
                    "expected_fields": ["product_name", "term_options", "interest_rate_summary"],
                },
                homepage_url="https://www.bmo.com/",
                source_language="en",
            )

        entry_rows = [item for item in result.rows if item["discovery_role"] == "entry"]
        self.assertEqual(len(entry_rows), 1)
        self.assertEqual(entry_rows[0]["normalized_url"], "https://www.bmo.com/en-ca/main/personal/investments/gic")
        self.assertIn("BMO-GIC-002", {str(item["source_id"]) for item in result.rows})
        self.assertNotIn("BMO-GIC-003", {str(item["source_id"]) for item in result.rows})

    def test_out_of_scope_product_urls_are_not_promoted_as_detail_sources(self) -> None:
        cases = [
            {
                "product_type": "gic",
                "candidate_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/air-miles",
                "title": "BMO AIR MILES Chequing Account",
                "heading": "BMO AIR MILES Chequing Account",
                "body": "Monthly fee and included transactions for a chequing account.",
                "reason_code": "other_product_type",
            },
            {
                "product_type": "gic",
                "candidate_url": "https://www.cibc.com/en/personal-banking/bank-accounts/savings-accounts.html",
                "title": "CIBC Savings Accounts",
                "heading": "Savings Accounts",
                "body": "Earn interest on your savings balance.",
                "reason_code": "other_product_type",
            },
            {
                "product_type": "savings",
                "candidate_url": "https://www.cibc.com/en/personal-banking/investments/tax-free-savings-accounts.html",
                "title": "Tax-Free Savings Account",
                "heading": "Tax-Free Savings Account",
                "body": "TFSA registered plan information and contribution details.",
                "reason_code": "registered_plan_wrapper",
            },
            {
                "product_type": "chequing",
                "candidate_url": "https://www.scotiabank.com/ca/en/about/investors-shareholders.html",
                "title": "Investors and Shareholders",
                "heading": "Investors and Shareholders",
                "body": "Investor relations and shareholder information.",
                "reason_code": "non_product_or_investor_page",
            },
        ]

        for case in cases:
            with self.subTest(case=case["candidate_url"]):
                candidate = HomepageCandidate(
                    normalized_url=case["candidate_url"],
                    raw_url=case["candidate_url"],
                    anchor_text=str(case["heading"]),
                    source_type="html",
                    origin="homepage_or_hub_link",
                    heuristic_score=8,
                    supporting_signal=False,
                    seed_source_id=None,
                    source_name_hint=None,
                    priority_hint=None,
                    expected_fields_hint=[],
                )
                ai_scores = {
                    case["candidate_url"]: AiParallelCandidateScore(
                        candidate_url=case["candidate_url"],
                        predicted_role="detail",
                        relevance_score=9.0,
                        confidence_band="high",
                        reason_codes=["product_type_semantic_match"],
                        short_rationale="The scorer thought this was a detail page.",
                    )
                }
                html = f"""
                <html>
                  <head><title>{case['title']}</title></head>
                  <body>
                    <h1>{case['heading']}</h1>
                    <p>{case['body']}</p>
                  </body>
                </html>
                """

                with patch("api_service.source_catalog.fetch_text", return_value=html):
                    rows, _rejected_urls, notes = _promote_detail_candidates(
                        bank_code="TEST",
                        bank_name="Test Bank",
                        country_code="CA",
                        product_type=str(case["product_type"]),
                        discovery_product_type=str(case["product_type"]),
                        product_type_definition={
                            **_product_type_definition(str(case["product_type"])),
                            "description": "Canadian personal deposit product with rates, fees, term, balance, or transaction details.",
                            "discovery_keywords": [str(case["product_type"])],
                        },
                        source_language="en",
                        fetch_policy=SimpleNamespace(),
                        candidates=[candidate],
                        ai_scores=ai_scores,
                    )

                self.assertEqual(rows, [])
                self.assertIn("rejected all tentative detail pages", " ".join(notes))

                with patch("api_service.source_catalog.fetch_text", return_value=html):
                    evidence = _score_page_evidence(
                        raw_url=case["candidate_url"],
                        fetch_policy=SimpleNamespace(),
                        product_type=str(case["product_type"]),
                        product_type_definition={
                            **_product_type_definition(str(case["product_type"])),
                            "description": "Canadian personal deposit product with rates, fees, term, balance, or transaction details.",
                            "discovery_keywords": [str(case["product_type"])],
                        },
                    )
                self.assertIn(case["reason_code"], evidence.page_evidence_reason_codes)

    def test_upsert_source_registry_rows_targets_unique_scope_and_returns_persisted_rows(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "source_id": "AUTO-BMO-CHQ-existing",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing catalog entry",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ]
        )

        result = _upsert_source_registry_rows(
            connection,
            [
                {
                    "source_id": "AUTO-BMO-CHQ-detail",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ],
        )

        self.assertEqual(result[0]["source_id"], "AUTO-BMO-CHQ-existing")
        sql, _params = connection.calls[0]
        self.assertIn(
            "ON CONFLICT (country_code, bank_code, product_type, normalized_url, source_type) DO UPDATE",
            sql,
        )
        self.assertIn("WHEN source_registry_item.status = 'removed'", sql)

    def test_upsert_source_registry_rows_preserves_removed_status_on_conflict(self) -> None:
        connection = _QueuedConnection(
            [
                {
                    "source_id": "AUTO-BMO-CHQ-removed",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "removed",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "removed_by_operator",
                }
            ]
        )

        result = _upsert_source_registry_rows(
            connection,
            [
                {
                    "source_id": "AUTO-BMO-CHQ-detail",
                    "bank_code": "BMO",
                    "country_code": "CA",
                    "product_type": "chequing",
                    "product_key": "BMO:chequing",
                    "source_name": "BMO chequing detail",
                    "source_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/",
                    "normalized_url": "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
                    "source_type": "html",
                    "discovery_role": "detail",
                    "status": "active",
                    "priority": "P1",
                    "source_language": "en",
                    "purpose": "detail",
                    "expected_fields": ["product_name", "monthly_fee", "included_transactions"],
                    "seed_source_flag": False,
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "generated_from_bank_homepage",
                }
            ],
        )

        self.assertEqual(result[0]["status"], "removed")
        self.assertEqual(result[0]["change_reason"], "removed_by_operator")

    def test_recognized_bank_migration_adds_logos_and_full_active_product_type_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0020_canada_recognized_banks_full_coverage.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN IF NOT EXISTS logo_url", migration_sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS logo_alt_text", migration_sql)
        self.assertIn("CROSS JOIN product_type_registry", migration_sql)
        self.assertIn("bank.status = 'active'", migration_sql)
        self.assertIn("product_type_registry.status = 'active'", migration_sql)
        self.assertIn("ON CONFLICT (bank_code, country_code, product_type) DO UPDATE", migration_sql)
        for bank_code in ("NATIONAL", "TANGERINE", "SIMPLII", "EQBANK", "MANULIFE", "ROGERSBANK"):
            self.assertIn(f"('{bank_code}'", migration_sql)

    def test_vancity_migration_adds_full_active_product_type_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0021_vancity_credit_union_full_coverage.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("'VANCITY'", migration_sql)
        self.assertIn("'https://www.vancity.com/'", migration_sql)
        self.assertIn("'https://www.vancity.com/favicon.ico'", migration_sql)
        self.assertIn("CROSS JOIN product_type_registry", migration_sql)
        self.assertIn("bank.bank_code = 'VANCITY'", migration_sql)
        self.assertIn("bank.status = 'active'", migration_sql)
        self.assertIn("product_type_registry.status = 'active'", migration_sql)
        self.assertIn("ON CONFLICT (bank_code, country_code, product_type) DO UPDATE", migration_sql)

    def test_vancity_route_migration_pins_all_seven_official_product_hubs(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0041_vancity_official_product_routes.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("product_owner_directed_official_site_audit", migration_sql)
        self.assertIn("https://www.vancity.com/bank/accounts", migration_sql)
        self.assertIn("https://www.vancity.com/bank/credit-cards", migration_sql)
        self.assertIn("https://www.vancity.com/invest/term-deposit-gic", migration_sql)
        self.assertIn("https://www.vancity.com/borrow/mortgages", migration_sql)
        self.assertIn("https://www.vancity.com/borrow/loans-lines-of-credit", migration_sql)
        for product_type in (
            "chequing", "savings", "gic", "credit-card", "mortgage", "personal-loan", "line-of-credit"
        ):
            self.assertIn(f"('{product_type}',", migration_sql)

    def test_coverage_evidence_migration_is_additive_and_auditable(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0028_source_catalog_coverage_evidence.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN IF NOT EXISTS coverage_source_url text", migration_sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS normalized_coverage_source_url text", migration_sql)
        self.assertIn("source_registry_catalog_item_coverage_source_https_check", migration_sql)
        self.assertIn("0028_source_catalog_coverage_evidence.sql", migration_sql)

    def test_bank_logo_refresh_uses_official_assets_without_overwriting_custom_urls(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        migration_sql = (
            repo_root / "db" / "migrations" / "0022_bank_logo_asset_refresh.sql"
        ).read_text(encoding="utf-8")
        public_logo_component = (
            repo_root / "app" / "public" / "src" / "components" / "fpds" / "public" / "bank-logo.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("official_logo_refresh", migration_sql)
        self.assertIn("bank.logo_url IS NULL OR bank.logo_url = official_logo_refresh.previous_logo_url", migration_sql)
        self.assertIn("0022_bank_logo_asset_refresh.sql", migration_sql)
        for bank_code in ("NATIONAL", "TANGERINE", "EQBANK", "MANULIFE", "ALTERNA", "FNBC", "SIMPLII", "VERSABANK"):
            self.assertIn(f"'{bank_code}'", migration_sql)
            self.assertIn(f"{bank_code}: {{ src:", public_logo_component)

        self.assertIn('onError={() => setFailed(true)}', public_logo_component)
        self.assertNotIn('rounded-md border border-border/70 bg-white', public_logo_component)

    def test_homepage_parallel_scorer_uses_default_medium_reasoning_effort_when_omitted(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-homepage-score-001",
                "model": "gpt-5.6-luna",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"ok","candidate_scores":[]}',
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode("utf-8")

        with patch("api_service.source_catalog.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            result, metadata = _invoke_openai_parallel_scorer(
                model_id="gpt-5.6-luna",
                api_key="test-key",
                payload={"product_type": "chequing", "candidates": []},
            )

        request_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(request_body["model"], "gpt-5.6-luna")
        self.assertNotIn("reasoning", request_body)
        self.assertEqual(result, {"summary": "ok", "candidate_scores": []})
        self.assertEqual(metadata["model_id"], "gpt-5.6-luna")

    def test_gpt_5_6_luna_reasoning_effort_is_stage_specific(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        default_medium_paths = (
            repo_root / "worker" / "pipeline" / "fpds_ai_runtime.py",
            repo_root / "api" / "service" / "api_service" / "source_catalog.py",
        )
        for source_path in default_medium_paths:
            source = source_path.read_text(encoding="utf-8")
            self.assertIn("gpt-5.6-luna", source)
            self.assertNotIn('"reasoning": {"effort": "none"}', source)

        keyword_generator_source = (repo_root / "api" / "service" / "api_service" / "product_types.py").read_text(encoding="utf-8")
        self.assertIn("gpt-5.6-luna", keyword_generator_source)
        self.assertIn('"reasoning": {"effort": "none"}', keyword_generator_source)


if __name__ == "__main__":
    unittest.main()
