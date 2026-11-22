import unittest
import gzip
import hashlib
from pathlib import Path

from worker.country_defaults import default_currency_for_country
from worker.pipeline.fpds_approval_policy import comparison_quality, security_meaning
from worker.pipeline.fpds_collection_accuracy import acceptance_receipt_valid, quote_supports_value, sanitize_candidate
from worker.pipeline.fpds_market_profile import country_product_profile


class JapanMarketTests(unittest.TestCase):
    def test_official_japanese_pdf_preserves_tiers_owner_and_conditions(self):
        from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
        from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractionInput
        from worker.pipeline.fpds_extraction.service import collect_captured_fields
        from worker.native_japanese_disclosure import annual_limit_schedule
        from worker.pipeline.tests.test_evidence_research_parity import run_services

        fixture = Path(__file__).resolve().parents[2] / "discovery/tests/fixtures/kagin-cardloan-s-huyo.pdf.gz"
        body = gzip.decompress(fixture.read_bytes())
        self.assertEqual(hashlib.sha256(body).hexdigest(), "7046319a66b95a7cb1ec3d591ae1644a39286fe75971090451e0cbc1548cfd08")
        parsed = parse_snapshot_bytes(body=body, content_type="application/pdf")
        url = "https://www.kagin.co.jp/library/kojin/loan/pdf/2026/cardloanS_huyo.pdf"
        meta = {"product_type": "line-of-credit", "discovery_role": "detail",
                "product_family": "lending", "normalized_source_url": url, "official_domain_allowlist": ["kagin.co.jp"]}
        context = ExtractionDocumentContext("p", "d", "s", "KAGOSHIMA", "JP", "pdf", "ja", meta)
        chunks = _build_evidence_chunks(parsed_document_id="p", source_language="ja", artifact=parsed, max_chars=200, overlap_chars=32)
        candidates = [EvidenceChunkCandidate(c.evidence_chunk_id, "p", c.chunk_index, c.anchor_type, c.anchor_value, c.page_no,
                      "ja", c.evidence_excerpt, c.retrieval_metadata, "d", "s", "KAGOSHIMA", "JP", "pdf") for c in chunks]
        profile = country_product_profile(country_code="JP", product_type="line-of-credit")
        _, fields, _, _ = collect_captured_fields(extraction_input=ExtractionInput(context, candidates),
                                                   field_names=list(profile.collection_fields), run_id="jp-replay")
        grounded = {f.field_name: f for f in fields
                    if f.field_metadata.get("official_grounding_method") == "deterministic_captured_financial_record"}
        self.assertTrue({"product_name", "currency", "interest_rate_summary", "credit_limit_text",
                         "security_requirement", "eligibility_text", "interest_calculation_method"} <= grounded.keys(), grounded.keys())
        schedule = grounded["interest_rate_summary"].candidate_value
        self.assertTrue(annual_limit_schedule(schedule))
        self.assertEqual(schedule.count("%"), 8)
        self.assertFalse(annual_limit_schedule(schedule.replace("500 万円超800 万円以下 4.55%", "")))
        self.assertIn("上限金利", schedule)
        evidence = [{"evidence_chunk_id": c.evidence_chunk_id, "source_url": url, "anchor_type": c.anchor_type,
                     "anchor_value": c.anchor_value, "evidence_excerpt": c.evidence_excerpt} for c in candidates]
        row, routed, _ = run_services([ExtractionInput(context, candidates)], taxonomy_registry={"line-of-credit": {"other"}})
        self.assertEqual(routed.validation_action, "auto_validated", (routed.validation_issue_codes, row["candidate_payload"]))
        accepted, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"], receipt)
        self.assertTrue(acceptance_receipt_valid(accepted))
        self.assertTrue({"eligibility_text", "interest_calculation_method", "security_requirement"} <= set(receipt["verified_fields"]))
        for changed in ({**row, "product_type": "business-line-of-credit"},
                        {**row, "product_name": row["product_name"].replace("不要型", "引落型")},
                        {**row, "candidate_payload": {k: v for k, v in row["candidate_payload"].items() if k != "interest_rate_summary"}}):
            self.assertFalse(sanitize_candidate(changed, source_metadata=meta, evidence=evidence)[1]["accepted"])
        sibling = url.replace("cardloanS_huyo", "cardloanS_hikiotoshi")
        other_rate = [{**e, "source_url": sibling} if e["anchor_type"] == "jp_disclosure_annual_rates" else e for e in evidence]
        mapping = dict(row["field_mapping_metadata"])
        mapping["interest_rate_summary"] = {**mapping["interest_rate_summary"], "official_web_sources": [{"url": sibling}]}
        rejected = sanitize_candidate({**row, "field_mapping_metadata": mapping}, source_metadata=meta, evidence=other_rate)[1]
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["omitted_fields"]["interest_rate_summary"], "japanese_product_scope_unverified")

    def test_local_contracts_require_cost_access_and_business_credit_limits(self):
        from worker.pipeline.fpds_normalization.service import _infer_subtype_code

        for kind in ("chequing", "savings", "gic"):
            code, _ = _infer_subtype_code(product_type=kind, country_code="JP", currency="JPY",
                                          candidate_payload={"product_name": "預金"})
            self.assertEqual(code, "other")
        self.assertIsNone(default_currency_for_country("JP"))
        for kind, payload in (
            ("chequing", {"monthly_fee": 0, "included_transactions": 3}),
            ("gic", {"standard_rate": 1, "term_length_text": "1年", "redeemable_flag": True}),
            ("business-line-of-credit", {"interest_rate": 3, "credit_limit_text": "100万円"}),
            ("business-loan", {"interest_rate": 3, "term_length_text": "1年"}),
        ):
            with self.subTest(kind=kind):
                quality = comparison_quality(country_code="JP", product_type=kind, expected_fields=[], candidate_payload=payload)
                self.assertTrue(quality.contract_defined)
                self.assertFalse(quality.complete)
        self.assertIsNone(country_product_profile(country_code="CA", product_type="business-loan"))
        self.assertIsNone(country_product_profile(country_code="JP", product_type="investment-fund"))

    def test_native_denomination_collateral_and_wrong_financial_meaning(self):
        # Kagoshima, cardloanS_huyo.pdf, and its foreign deposit alternatives.
        self.assertTrue(quote_supports_value("currency", "JPY", "ご利用限度額 10 万円以上1,000 万円以内（10 万円単位）"))
        self.assertTrue(quote_supports_value("currency", "USD", "自動継続外貨定期預金 (米ドル建)"))
        for text in ["手数料 500円", "手数料 ￥500", "手数料 JPY 500", "円換算額", "自動継続外貨定期預金 (豪ドル建・ユーロ建)", "米ドル建・円建"]:
            self.assertFalse(quote_supports_value("currency", "JPY", text))
        self.assertFalse(quote_supports_value("currency", "AUD", "自動継続外貨定期預金 (豪ドル建・ユーロ建)"))
        self.assertIs(security_meaning("１３．担保・保証人 必要ございません。"), False)
        self.assertIsNone(security_meaning("保証人 必要ございません。"))
        self.assertIsNone(security_meaning("担保・保証人 必要ございません。ただし担保が必要な場合があります。"))
        self.assertFalse(quote_supports_value("interest_rate", 0.5, "基準金利より最大で年０．５％金利を引下げます。"))
