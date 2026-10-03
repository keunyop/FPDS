from dataclasses import replace
import json
from pathlib import Path
import unittest
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, country_currency_fallback
from worker.discovery.fpds_discovery.discovery import extract_links
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.service import _append_structural_account_facts, _select_official_grounding_chunks

FIXTURE = Path(__file__).parent / "fixtures/golden/bmo_chequing_evidence_2026_10_03.json"

class DirectChequingComparisonTests(unittest.TestCase):
    def setUp(self):
        self.products = json.loads(FIXTURE.read_text(encoding="utf8"))["products"]

    def test_saved_monthly_table_allowances_are_not_rejected(self):
        expected = {"Practical":12, "Plus":25, "Performance":True, "Premium":True}
        for prefix, value in expected.items():
            product = next(x for x in self.products if x["name"].startswith(prefix))
            cell = next(x for x in product["cells"] if "Transactions per month" in x["anchor"])
            field = "unlimited_transactions_flag" if value is True else "included_transactions"
            with self.subTest(product=prefix):
                self.assertTrue(quote_supports_value(field, value, cell["text"]))

    def test_separate_named_account_perks_do_not_redeclare_currency(self):
        text = "Additional accounts\nCanadian dollar and US dollar Savings Account at no cost *3"
        self.assertEqual(country_currency_fallback({"country_code":"CA", "product_name":"Plus Chequing Account"}, [{"evidence_excerpt":text}]), "CAD")
        for quote in ["Currency USD", "Monthly fee USD $4", "USD Account", "If you select a U.S. dollar account as the lead account, all fees will be charged in U.S. dollars."]:
            with self.subTest(quote=quote):
                self.assertIsNone(country_currency_fallback({"country_code":"CA"}, [{"evidence_excerpt":quote}]))

    def test_special_channels_do_not_hide_an_explicit_ordinary_unlimited_declaration(self):
        self.assertTrue(quote_supports_value("unlimited_transactions_flag", True, "Unlimited transactions and Interac e-transfer transactions."))
        for quote in ["Unlimited Interac e-transfer transactions", "Unlimited transactions only for public transit", "Unlimited transactions if you maintain a $5,000 balance", "Transactions per month\n25\nUnlimited"]:
            with self.subTest(quote=quote):
                self.assertFalse(quote_supports_value("unlimited_transactions_flag", True, quote))

    def test_main_disclosure_survives_repeated_navigation_with_existing_caps(self):
        nav = "<nav>" + "".join(f'<a href="/menu/{i}">Menu {i}</a>' for i in range(300)) + "</nav>"
        url = "https://www.bmo.com/pdf/Agreements_Bank_Plans_and_Fees_for_Everyday_Banking.pdf"
        html = nav + f'<main><a href="{url}" aria-label="Agreements, Bank Plans and Fees">More <span>details</span></a></main>'
        links = extract_links(html, base_url="https://www.bmo.com/en-ca/detail")
        self.assertLessEqual(len(links), 256)
        self.assertIn(url, [x.normalized_url for x in links])

    def context_and_cell(self, *, bank="EXAMPLE", country="CA", value="Unlimited"):
        title = "Everyday Chequing Account"
        ctx = ExtractionDocumentContext("parsed", "doc", "snap", bank, country, "html", "en", {
            "product_type":"chequing", "discovery_role":"detail",
            "normalized_source_url":"https://examplebank.com/account", "official_domain_allowlist":["examplebank.com"],
            "discovery_metadata":{"primary_heading":title, "page_title":title,
                "product_identity_match":True, "page_evidence_score":10, "negative_signal_count":0}})
        chunk = EvidenceChunkCandidate("chunk", "parsed", 0, "financial_table_cell", "Transactions per month", None,
            "en", "Everyday\n$12 per month\nTransactions per month\n"+value, {}, "doc", "snap", bank, country, "html")
        return ctx, chunk

    def structural(self, ctx, cells):
        return _append_structural_account_facts(context=ctx, candidates=cells, fields=[],
            requested_fields=["included_transactions", "unlimited_transactions_flag", "monthly_fee"])

    def test_named_column_proof_works_across_banks_and_countries(self):
        for bank, country, value in [("TD","CA","25"), ("EXAMPLE","US","Unlimited")]:
            with self.subTest(bank=bank):
                ctx, cell = self.context_and_cell(bank=bank, country=country, value=value)
                fields = self.structural(ctx, [cell])
                self.assertEqual(len(fields), 1)
                self.assertEqual(fields[0].candidate_value, 25 if value=="25" else True)
                self.assertEqual(fields[0].evidence_text_excerpt, cell.evidence_excerpt)

    def test_wrong_column_capture_identity_and_conditions_cannot_ground(self):
        ctx, cell = self.context_and_cell()
        mutations = [replace(cell, source_document_id="other"), replace(cell, source_snapshot_id="old"),
            replace(cell, parsed_document_id="other"), replace(cell, bank_code="OTHER"),
            replace(cell, country_code="US"), replace(cell, source_language="fr"),
            replace(cell, evidence_excerpt=cell.evidence_excerpt.replace("Everyday", "Premium")),
            replace(cell, evidence_excerpt=cell.evidence_excerpt+"\nif you maintain $5,000"),
            replace(cell, evidence_excerpt=cell.evidence_excerpt.replace("Unlimited", "Unlimited ATM transactions")),
            replace(cell, evidence_excerpt="Not unlimited transactions.\n"+cell.evidence_excerpt),
            replace(cell, evidence_excerpt="You get 25 transactions per month.\n"+cell.evidence_excerpt)]
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertEqual(self.structural(ctx,[changed]),[])
        for meta in [{"official_domain_allowlist":["otherbank.com"]},
                     {"discovery_metadata":{"product_identity_match":False}}, {"discovery_role":"index"}]:
            self.assertEqual(self.structural(replace(ctx,source_metadata={**ctx.source_metadata,**meta}),[cell]),[])

    def test_conflicting_allowances_do_not_become_two_proven_facts(self):
        ctx, cell = self.context_and_cell()
        finite = replace(cell,evidence_chunk_id="other",evidence_excerpt=cell.evidence_excerpt.replace("Unlimited","25"))
        self.assertEqual(self.structural(ctx,[cell,finite]),[])
        _, other = self.context_and_cell(value="12")
        self.assertEqual(self.structural(ctx,[finite,replace(other,evidence_chunk_id="third")]),[])

    def test_fee_card_keeps_reward_separate_without_waiver_inference(self):
        quote = "Fees\n$17.95\nmonthly fee\nBundle offer: Earn 500 Bonus Points when you have an eligible card."
        self.assertTrue(quote_supports_value("monthly_fee",17.95,quote))
        for bad in [quote+"\nFees\n$30.95\nmonthly fee", "Fees\n$17.95\nmonthly fee\nif you maintain $4,000", quote.replace("$17.95","$0")]:
            self.assertFalse(quote_supports_value("monthly_fee",17.95,bad))
        self.assertFalse(quote_supports_value("monthly_fee",0,quote))

    def test_transaction_definition_is_not_a_waiver_condition(self):
        quote = "With the Everyday Chequing Account, you get unlimited transactions per month. When you move money out of your account, like an ATM withdrawal, that counts as a transaction."
        self.assertTrue(quote_supports_value("unlimited_transactions_flag",True,quote))
        for restriction in ["if you maintain $4,000", "provided you qualify"]:
            self.assertFalse(quote_supports_value("unlimited_transactions_flag",True,quote.replace("like an ATM withdrawal",restriction)))
        for suffix in [" When you maintain $4,000.", " If you qualify.", " Unlimited ATM transactions only."]:
            self.assertFalse(quote_supports_value("unlimited_transactions_flag",True,quote+suffix))

    def test_companion_price_evidence_is_selected_with_existing_payload_budget(self):
        from types import SimpleNamespace
        _, cell = self.context_and_cell()
        ordinary = [replace(cell,evidence_chunk_id=f"legal-{i}",source_document_id="terms",anchor_type="section",evidence_excerpt="General legal boilerplate.") for i in range(20)]
        priced = replace(cell,evidence_chunk_id="price",source_document_id="fees",anchor_type="page",evidence_excerpt="Everyday Chequing Account: Additional transactions $1.25 each.")
        selected = _select_official_grounding_chunks(candidates=[cell,*ordinary,priced],
            collected_fields=[SimpleNamespace(evidence_chunk_id="chunk",source_document_id="doc")],product_name="Everyday Chequing Account")
        self.assertIn(priced,selected)
        self.assertLessEqual(len(selected),24)
        self.assertLessEqual(sum(len(c.evidence_excerpt) for c in selected),43200)

    def test_proven_columns_survive_real_normalization_without_a_model(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from worker.pipeline.fpds_extraction.models import ExtractedFieldCandidate
        from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
        from worker.pipeline.fpds_normalization.service import NormalizationService
        from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig, build_object_store
        ctx, allowance = self.context_and_cell()
        price = replace(allowance,evidence_chunk_id="price",evidence_excerpt="Everyday\nMonthly plan fee\n$12.00")
        name = replace(allowance,evidence_chunk_id="name",anchor_type="section",evidence_excerpt="Everyday Chequing Account")
        fields = self.structural(ctx,[allowance,price])
        fields.append(ExtractedFieldCandidate("product_name",name.evidence_excerpt,"string",.99,"captured_identity",
            "doc","snap","name",name.evidence_excerpt,"section",None,None,0,
            {"official_grounding_contract_version":"collection-official-grounding-v2","official_verification_status":"match",
             "evidence_quote":name.evidence_excerpt,"official_web_sources":[{"url":"https://examplebank.com/account","title":name.evidence_excerpt}]}))
        links = [NormalizationEvidenceLink(f.field_name,str(f.candidate_value),f.evidence_chunk_id,f.evidence_text_excerpt,
            f.source_document_id,f.source_snapshot_id,f.confidence,None,f.anchor_type,f.anchor_value,f.page_no,f.chunk_index) for f in fields]
        item = NormalizationInput(None,"doc","snap","parsed","extract","private",None,"EXAMPLE","CA","html","en",
            ctx.source_metadata,{"product_type":"chequing","product_family":"deposit","country_code":"CA"},
            [NormalizationExtractedField(**f.to_dict()) for f in fields],links,[],normalized_source_url="https://examplebank.com/account",
            evidence_origins_resolved=True,evidence_origins={c.evidence_chunk_id:{"run_id":"run","bank_code":"EXAMPLE",
                "country_code":"CA","source_document_id":"doc","snapshot_id":"snap","evidence_chunk_id":c.evidence_chunk_id,
                "evidence_excerpt":c.evidence_excerpt,"source_url":"https://examplebank.com/account"} for c in [allowance,price,name]})
        with TemporaryDirectory() as tmp, patch("worker.pipeline.fpds_normalization.service.llm_provider_configured",return_value=False):
            cfg=NormalizationStorageConfig("filesystem","test","normalized","hot",filesystem_root=tmp)
            result=NormalizationService(storage_config=cfg,object_store=build_object_store(cfg)).normalize_inputs(run_id="run",inputs=[item]).source_results[0]
        self.assertIsNone(result.error_summary)
        payload=result.normalized_candidate_record["candidate_payload"]
        self.assertTrue(payload["_collection_accuracy"]["accepted"],payload)
        self.assertIs(payload["unlimited_transactions_flag"],True)
        self.assertEqual(payload["monthly_fee"],12)
        self.assertNotIn("standard_rate",payload)
        self.assertNotIn("included_transactions",payload)

if __name__ == "__main__":
    unittest.main()
