"""Owned literal declarations retain price scope and complete referenced notes."""
import gzip,hashlib,json,unittest
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/owned-card-declarations'
class OwnedCardDeclarationTests(unittest.TestCase):
    def source(self,name):
        r=next(r for r in json.loads((FIX/'sources.json').read_text()) if r['fixture']==name+'.html.gz')
        raw=gzip.decompress((FIX/r['fixture']).read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
        return r,raw
    def item(self,name):
        r,raw=self.source(name)
        from bs4 import BeautifulSoup
        title=BeautifulSoup(raw,'html.parser').title.get_text(' ',strip=True)
        item=input_from_segments(bank='CONA',url=r['url'],product='credit-card',name=title,country='US',segments=parse_snapshot_bytes(body=raw,content_type='text/html').segments)
        return item
    def test_official_partner_owned_fee_and_full_referenced_purchase_apr(self):
        row,v,e=run_services([self.item('partner')]);p=row['candidate_payload']
        self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
        self.assertEqual(p['annual_fee'],0)
        self.assertIn('29.24%',p['purchase_interest_rate_summary'])
        self.assertIn('creditworthiness',p['purchase_interest_rate_summary'])
        self.assertIsNone(v.review_task_record)
    def test_official_intro_offer_never_becomes_scalar(self):
        row,v,e=run_services([self.item('intro')]);p=row['candidate_payload']
        self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
        self.assertEqual(p['annual_fee'],0)
        self.assertIn('12 months',p['purchase_interest_rate_summary'])
        self.assertIn('18.74%',p['purchase_interest_rate_summary'])
        self.assertIn('Balance transfer fee applies',p['purchase_interest_rate_summary'])
        self.assertNotIn('purchase_interest_rate',p)
    def test_official_marketing_h1_owned_label(self):
        row,v,e=run_services([self.item('label')]);p=row['candidate_payload']
        self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
        self.assertEqual(p['annual_fee'],95)
        self.assertIn('19.74% - 28.74%',p['purchase_interest_rate_summary'])
    def test_literal_audience_and_brand_name_retain_owned_prices(self):
        for fixture,part in [('student','Students'),('good-credit','Good Credit')]:
            row,v,_=run_services([self.item(fixture)])
            self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload'])
            self.assertIn(part,row['product_name'])
            self.assertEqual(row['candidate_payload']['annual_fee'],0)
            self.assertIn('variable APR',row['candidate_payload']['purchase_interest_rate_summary'])
    def test_all_source_hashes(self):
        for name in ['partner','intro','label','cashback','student','good-credit']:self.source(name)

class CardDeclarationBoundaries(unittest.TestCase):
    def records(self,html):
        return parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments
    def test_other_bank_and_product_use_literal_declarations(self):
        for bank in ['Example Financial','Otherbank']:
            html='<title>'+bank+' Travel Visa</title><main><h1>'+bank+' Travel Visa</h1><div><h3>$0 annual fee</h3><p>No foreign transaction fees.</p></div><div><h3>Purchase rate</h3><p>17.5% - 27.5% variable APR</p></div></main>'
            row,v,_=run_services([input_from_segments(bank='EXAMPLE',url='https://example.com/travel-visa',product='credit-card',name=bank+' Travel Visa',country='US',segments=self.records(html))])
            self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload'])
            self.assertEqual(row['candidate_payload']['annual_fee'],0)
            self.assertNotIn('purchase_interest_rate',row['candidate_payload'])
    def test_generic_savings_scroll_reference_retains_fee_qualification(self):
        html='<main><h1>Example Savings Account</h1><p>No monthly fees<a data-scroll-target="price" href="javascript:void(0)"><sup>1</sup></a></p><p id="price">Only for the first six months.</p></main>'
        records=[s.text for s in self.records(html) if s.anchor_type=='owned_account_assertion']
        self.assertTrue(records)
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        self.assertFalse(any(quote_supports_value('monthly_fee',0,q) for q in records))
    def test_missing_duplicate_and_invalid_reference_do_not_supply_card_prices(self):
        prefix='<title>Example Travel Visa</title><main><h1>Example Travel Visa</h1><div><h3>No annual fee</h3><p>That is $0<a data-scroll-target="price" href="javascript:void(0)"><sup>1</sup></a></p></div>'
        for notes in ['', '<p id="price">No annual fee.</p><p id="price">First year only.</p>']:
            self.assertFalse(any(s.anchor_type=='labelled_financial_record' for s in self.records(prefix+notes+'</main>')))
    def test_fee_conditions_and_conflicts_stay_blocking(self):
        from worker.native_card_declarations import declaration_fee_value
        for q in ['Example Visa\n$0 annual fee\nFirst year only.', 'Example Visa\nNo annual fee\nIf you keep a $5000 minimum balance.', 'Example Visa\nNo annual fee\nOnly for eligible students.']:
            self.assertIsNone(declaration_fee_value(q))
        test=OwnedCardDeclarationTests();item=test.item('partner')
        q=next(c.evidence_excerpt for c in item.candidates if c.anchor_type=='labelled_financial_record')
        self.assertEqual(declaration_fee_value(q),0)
        self.assertIsNone(declaration_fee_value(q.replace('Annual Fee: $0;', 'Annual Fee: $95;')))
        self.assertIsNone(declaration_fee_value(q+'\nFee waived for the first year.'))
        self.assertIsNone(declaration_fee_value(q.replace('Annual Fee: $0;', 'Annual Fee: $0 for eligible students;')))
    def test_foreign_panel_and_calculator_cannot_donate_prices(self):
        for extra in ['data-product-name="Other Visa"', '']:
            html='<title>Example Visa</title><main><h1>Example Visa</h1><div '+extra+'><h3>$0 annual fee</h3><p>Price</p>'+('' if extra else '<input value="0">')+'</div></main>'
            self.assertFalse(any(s.anchor_type=='labelled_financial_record' for s in self.records(html)))
    def test_marketing_label_requires_corroboration_and_single_identity(self):
        for prefix in ['<title>Other Rewards Card</title>', '<title>Example Travel Card</title>']:
            html=prefix+'<main><div><div class="eyebrow">Example Rewards</div><h1>Enjoy a bonus</h1></div><div><h3>Purchase rate</h3><p>17.5% variable APR</p></div></main>'
            self.assertFalse(any(s.anchor_type=='owned_product_label' for s in self.records(html)))
        html='<title>Example Travel Card</title><main><h1>Example Visa</h1><h1>Other Visa</h1><div><h3>$0 annual fee</h3></div></main>'
        self.assertFalse(any(s.anchor_type=='labelled_financial_record' for s in self.records(html)))
    def test_current_origin_mismatch_does_not_ground_price(self):
        from dataclasses import replace
        from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
        item=OwnedCardDeclarationTests().item('partner')
        chunks=[replace(c,source_snapshot_id='old') for c in item.candidates]
        fields=_append_captured_decision_facts(context=item.context,candidates=chunks,fields=[],requested_fields=['annual_fee','purchase_interest_rate_summary'])
        self.assertFalse(fields)

    def test_bare_purchase_percentage_cannot_replace_full_annual_terms(self):
        html='<title>Example Visa</title><main><h1>Example Visa</h1><div><h3>Purchase rate</h3><p>20.99%</p></div></main>'
        self.assertFalse(any(s.anchor_type=='owned_card_apr_offer' for s in self.records(html)))

    def test_audience_name_is_not_a_price_waiver_but_actual_qualifiers_block(self):
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        self.assertTrue(quote_supports_value('annual_fee',0,'Example Rewards for Students\nAnnual Fee\n$0'))
        for q in ['Example Rewards only for Students\nAnnual Fee\n$0','Example Rewards for eligible Students\nAnnual Fee\n$0','Example Rewards for Students\nAnnual Fee\n$0\nFirst year only']:
            self.assertFalse(quote_supports_value('annual_fee',0,q))

    def test_conflicting_reference_targets_fail_closed(self):
        html='<title>Example Visa</title><main><h1>Example Visa</h1><div><h3>No annual fee</h3><p>$0<a href="#one" data-scroll-target="two"><sup>1</sup></a></p></div><p id="one">No annual fee.</p><p id="two">First year only.</p></main>'
        self.assertFalse(any(s.anchor_type=='labelled_financial_record' for s in self.records(html)))

    def test_conflicting_fee_restatement_cannot_hide_behind_zero_heading(self):
        from worker.native_card_declarations import declaration_fee_value
        for q in ["Example Visa\nNo annual fee\nThat's $95.", "Example Visa\nNo annual fee\nThat\u2019s $95.", 'Example Visa\nNo annual fee\nAnnual Fee: $95;', 'Example Visa\n$95 annual fee\nNo annual fee.']:
            self.assertIsNone(declaration_fee_value(q))
