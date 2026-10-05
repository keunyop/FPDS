"""Native label/reference regressions shared by banks and product types."""
from dataclasses import replace
from pathlib import Path
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts

class LabelledDisclosureTests(unittest.TestCase):
    def records(self, html):
        return [s for s in parse_snapshot_bytes(body=html, content_type='text/html').segments if s.anchor_type == 'labelled_financial_record']

    def test_official_card_dom_preserves_regular_rate_and_default_consequence(self):
        records = self.records(Path(__file__).parent.joinpath('fixtures/golden/desjardins_labelled_pricing_dom.html').read_bytes())
        self.assertEqual(len(records), 3)
        purchase = next(r.text for r in records if 'Interest rate on purchases\n' in r.text)
        self.assertIn('fixed annual interest rates', purchase)
        self.assertIn('increase to 19.9%', purchase)
        self.assertTrue(quote_supports_value('purchase_interest_rate', 10.9, purchase))
        self.assertFalse(quote_supports_value('purchase_interest_rate', 19.9, purchase))
        self.assertFalse(quote_supports_value('cash_advance_rate', 10.9, purchase))
        fee = next(r.text for r in records if 'Annual fee\n' in r.text)
        self.assertTrue(quote_supports_value('annual_fee', 0, fee))

    def test_missing_or_ambiguous_reference_cannot_prove_rate(self):
        html = b'<main><h1>Everyday Visa</h1><div>Interest rate on purchases<br>12.5%<a href="#missing">1</a></div></main>'
        self.assertEqual(self.records(html), [])
        html = html.replace(b'</main>', b'<p id="missing">Annual interest rate.</p><p id="missing">First year only.</p></main>')
        self.assertEqual(self.records(html), [])

    def test_annual_default_note_alone_does_not_prove_regular_annual_basis(self):
        q = "Everyday Visa\nInterest rate on purchases\n12.5%\nIf you don't make the minimum payment by the due date, the annual interest rates on purchases and cash advances will increase to 19.9% until we receive your payment."
        self.assertFalse(quote_supports_value('purchase_interest_rate', 12.5, q))

    def test_other_bank_and_financial_conditions_fail_closed(self):
        q = 'Everyday Visa\nPurchase interest rate\n12.5%\nAnnual interest rates apply.'
        self.assertTrue(quote_supports_value('purchase_interest_rate', 12.5, q))
        for tail in ['\nFirst year only.', '\nIf you qualify.', '\nFrom 12.5% to 15.5%.', '\nPromotional rate.', '\nAnother purchase rate is 14%.']:
            with self.subTest(tail=tail):
                self.assertFalse(quote_supports_value('purchase_interest_rate', 12.5, q + tail))
        self.assertFalse(quote_supports_value('annual_fee', 0, 'Annual fee\nNone\nFirst year only.'))

    def test_rate_value_line_cannot_hide_conditions_or_competing_percentages(self):
        for value_line in ["12.5% first year only", "12.5% if eligible", "12.5% to 15.5%",
                           "12.5% promotional rate", "12.5% for new customers", "12.5% from 12.5%"]:
            with self.subTest(value_line=value_line):
                quote = "Everyday Visa\nPurchase interest rate\n" + value_line + "\nAnnual interest rates apply."
                self.assertFalse(quote_supports_value("purchase_interest_rate", 12.5, quote))
        quote = "Everyday Visa\nPurchase interest rate\n12.5% 1\nAnnual interest rates apply."
        self.assertTrue(quote_supports_value("purchase_interest_rate", 12.5, quote))

    def test_new_native_records_use_existing_exact_origin_gate(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx, base = DirectChequingComparisonTests().context_and_cell()
        ctx = replace(ctx, source_metadata={**ctx.source_metadata, 'product_type':'credit-card'})
        identity = ctx.source_metadata['discovery_metadata']['primary_heading']
        chunk = replace(base, anchor_type='labelled_financial_record', anchor_value=identity,
            evidence_excerpt=identity+'\nPurchase interest rate\n12.5%\nAnnual interest rates apply.')
        fields = lambda c: _append_captured_decision_facts(context=ctx, candidates=[c], fields=[], requested_fields=['purchase_interest_rate'])
        self.assertEqual(fields(chunk)[0].candidate_value, '12.5')
        for bad in [replace(chunk, source_snapshot_id='old'),replace(chunk, parsed_document_id='other'),replace(chunk, bank_code='OTHER'),replace(chunk,country_code='US'),replace(chunk,source_language='fr'),replace(chunk,anchor_value='Other product')]:
            self.assertEqual(fields(bad), [])

    def test_plural_absent_balance_does_not_hide_real_fee_conditions(self):
        for q in ["No monthly fees, no minimum balances.", "No monthly fee; no minimum balance required."]:
            self.assertTrue(quote_supports_value("monthly_fee", 0, q))
        for q in ["No monthly fees if you maintain $100.", "No monthly fees, not no minimum balances.", "No monthly fees for the first year."]:
            self.assertFalse(quote_supports_value("monthly_fee", 0, q))

    def test_actual_named_companion_cells_keep_product_currency_and_fee(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx, base = DirectChequingComparisonTests().context_and_cell()
        identity = "US Dollar Account"
        ctx = replace(ctx, source_metadata={**ctx.source_metadata, "product_type":"savings",
            "normalized_source_url":"https://www.eqbank.ca/personal-banking/savings/usd",
            "official_domain_allowlist":["eqbank.ca"],
            "discovery_metadata":{"primary_heading":identity, "page_title":identity, "product_identity_match":True}})
        dom = Path(__file__).parent.joinpath("fixtures/golden/eqbank_account_comparison_dom.html").read_bytes()
        atoms = [s for s in parse_snapshot_bytes(body=dom, content_type="text/html").segments if s.anchor_type == "financial_table_cell"]
        cells = [replace(base, evidence_chunk_id=str(i), source_document_id="companion", parsed_document_id="companion-pd",
            source_snapshot_id="companion-snap", anchor_type=a.anchor_type, anchor_value=a.anchor_value, evidence_excerpt=a.text,
            retrieval_metadata={"captured_companion":True,"source_url":"https://www.eqbank.ca/rates"}) for i,a in enumerate(atoms)]
        fields = _append_captured_decision_facts(context=ctx, candidates=cells, fields=[], requested_fields=["monthly_fee"])
        self.assertEqual({f.field_name:f.candidate_value for f in fields}, {"monthly_fee":"0.0","currency":"USD"})
        self.assertTrue(all("US Dollar Account" in f.evidence_text_excerpt for f in fields))
        # Neither other columns nor specific-channel unlimited means general transactions.
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=cells,fields=[],requested_fields=["unlimited_transactions_flag"]), [next(f for f in fields if f.field_name=="currency")])
        bad = [replace(c, bank_code="OTHER") for c in cells]
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=bad,fields=[],requested_fields=["monthly_fee"]), [])

    def test_marketing_h1_requires_owned_native_title_and_body(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx, base = DirectChequingComparisonTests().context_and_cell()
        ctx = replace(ctx, source_metadata={**ctx.source_metadata, "product_type":"savings",
            "normalized_source_url":"https://examplebank.com/savings/usd",
            "discovery_metadata":{"primary_heading":"Earn 2.50% on every US dollar",
                "page_title":"US Dollar Account | Example Bank", "product_identity_match":False}})
        title = replace(base, evidence_chunk_id="title", anchor_type="document_title", evidence_excerpt="US Dollar Account | Example Bank")
        body = replace(base, evidence_chunk_id="body", anchor_type="section", evidence_excerpt="US Dollar Account\nCurrent account features.")
        extract = lambda cs: _append_captured_decision_facts(context=ctx,candidates=cs,fields=[],requested_fields=["product_name"])
        good = extract([title,body])
        self.assertEqual(next(f for f in good if f.field_name=="product_name").candidate_value, "US Dollar Account")
        self.assertEqual(extract([body]), [])
        self.assertEqual(extract([replace(title,source_snapshot_id="old"),body]), [])
        self.assertEqual(extract([title,replace(body,bank_code="OTHER")]), [])

    def test_attached_fee_condition_cannot_be_bypassed_by_shorter_copy(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx, base = DirectChequingComparisonTests().context_and_cell()
        name = ctx.source_metadata["discovery_metadata"]["primary_heading"]
        short = replace(base, anchor_type="financial_declaration", evidence_excerpt="Annual fee\n$0")
        linked = replace(base,evidence_chunk_id="linked",anchor_type="labelled_financial_record",anchor_value=name,
            evidence_excerpt=name+"\nAnnual fee\n$0\nOnly for eligible customers until age 25.")
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[short,linked],fields=[],requested_fields=["annual_fee"]), [])
        html = b'<main><h1>Everyday Visa</h1><div>Annual fee<br>None<a href="#condition">1</a></div><p id="condition">Until age 25.</p></main>'
        record = self.records(html)[0]
        self.assertIn("Until age 25.", record.text)
        self.assertFalse(quote_supports_value("annual_fee",0,record.text))

    def test_linked_rate_records_keep_annual_basis_and_reject_sibling_offer(self):
        html = b'<main><h1>Deposit Account</h1><p>2.50%<sup><a href="#note">*</a></sup> interest</p><p id="note">Rates are per annum and subject to change without notice.</p><h2>Other Savings Account</h2><p>4.50%<a href="#note">*</a> interest</p></main>'
        atoms = [a for a in parse_snapshot_bytes(body=html,content_type="text/html").segments if a.anchor_type=="linked_rate_record"]
        self.assertEqual(len(atoms),1)
        self.assertTrue(quote_supports_value("standard_rate",2.5,atoms[0].text))
        self.assertIn("per annum",atoms[0].text)
        html=html.replace(b'id="note"',b'id="unresolved"')
        self.assertFalse(any(a.anchor_type=="linked_rate_record" for a in parse_snapshot_bytes(body=html,content_type="text/html").segments))

    def test_fee_payment_note_is_preserved_and_actual_fee_language_blocks(self):
        dom=Path(__file__).parent.joinpath("fixtures/golden/desjardins_labelled_pricing_dom.html").read_bytes()
        fee=next(a.text for a in self.records(dom) if "Annual fee\n" in a.text)
        self.assertIn("minimum payment",fee)
        self.assertTrue(quote_supports_value("annual_fee",0,fee))
        self.assertFalse(quote_supports_value("annual_fee",0,fee+"\nAnnual fee is waived for eligible customers."))

    def test_preceding_qualification_and_unresolved_note_block_shorter_fee(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx,base=DirectChequingComparisonTests().context_and_cell()
        name=ctx.source_metadata["discovery_metadata"]["primary_heading"]
        for tail in ['<h2>First year free if you qualify</h2><div>Annual fee<br>None</div>',
                     '<div>Annual fee<br>None<a href="#missing">1</a></div>']:
            html=("<main><h1>"+name+"</h1>"+tail+"</main>").encode()
            atoms=parse_snapshot_bytes(body=html,content_type="text/html").segments
            chunks=[replace(base,evidence_chunk_id=str(i),anchor_type=a.anchor_type,anchor_value=a.anchor_value,evidence_excerpt=a.text) for i,a in enumerate(atoms)]
            facts=_append_captured_decision_facts(context=ctx,candidates=chunks,fields=[],requested_fields=["annual_fee"])
            self.assertEqual(facts,[])

    def test_monthly_price_label_cannot_consume_later_transaction_fee_label(self):
        q = "Basic plan\nMonthly fee\n$3.95\n1\nTransaction fees apply if you exceed the number of transactions included in your monthly plan or if you don't have a plan. For more information, see the Service fees page."
        self.assertTrue(quote_supports_value("monthly_fee",3.95,q))
        self.assertFalse(quote_supports_value("additional_transaction_fee",3.95,q))

    def test_family_plan_heading_with_soft_hyphen_cannot_supply_composite_price(self):
        html='<main><h1>Everyday Chequing Account</h1><h2>Inter\u00admediate plan</h2><div>Monthly fee<br>$10.95<a href="#note">1</a></div><p id="note">Rates subject to change.</p></main>'
        self.assertEqual(self.records(html.encode()), [])
        atoms=parse_snapshot_bytes(body=html.encode(),content_type="text/html").segments
        self.assertTrue(any(a.anchor_type=="unresolved_financial_reference" for a in atoms))

    def test_same_owned_price_retains_complete_optional_waiver_without_extra_search(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        ctx,base=DirectChequingComparisonTests().context_and_cell()
        name=ctx.source_metadata["discovery_metadata"]["primary_heading"]
        price=replace(base,evidence_chunk_id="price",anchor_type="labelled_financial_record",anchor_value=name,evidence_excerpt=name+"\nMonthly fee\n$4.00")
        declaration='"Free if you maintain a balance of at least" means you don\'t pay a monthly fee for your plan if you maintain at least the minimum balance for that account for the entire month.\n$4,000'
        note=replace(base,evidence_chunk_id="waiver",anchor_type="section",evidence_excerpt="Account conditions\n"+declaration+"\nMonthly fee\n$4.00")
        collect=lambda cs: _append_captured_decision_facts(context=ctx,candidates=cs,fields=[],requested_fields=["fee_waiver_condition"])
        found=collect([price,note])
        self.assertEqual(found[0].candidate_value,declaration.replace("\n"," "))
        self.assertEqual(found[0].field_metadata["evidence_quote"],declaration)
        for bad in [replace(note,bank_code="OTHER"),replace(note,source_snapshot_id="old"),replace(note,evidence_excerpt=note.evidence_excerpt.replace("entire month","first month only")),replace(note,evidence_excerpt=note.evidence_excerpt+"\nOnly for eligible students.")]:
            self.assertEqual(collect([price,bad]),[])
        self.assertEqual(collect([note]),[])

if __name__ == '__main__':
    unittest.main()
