import gzip,hashlib,json,unittest
from pathlib import Path
from worker.dynamic_pricing import has_empty_dynamic_rate_slot
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/owned-pricing-disclosures'
class OwnedPricingTests(unittest.TestCase):
 def raw(self,name):
  r=next(r for r in json.loads((FIX/'sources.json').read_text()) if r['fixture']==name+'.html.gz')
  raw=gzip.decompress((FIX/r['fixture']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256']);return r,raw
 def test_current_static_card_requests_render(self):
  _,raw=self.raw('card-static');self.assertTrue(has_empty_dynamic_rate_slot(raw.decode()))
 def test_official_sibling_labels_and_ambiguous_cta_ownership(self):
  _,raw=self.raw('card-sibling-label');self.assertTrue(has_empty_dynamic_rate_slot(raw.decode()))
  # An independently named sticky CTA introduces an unresolved competing
  # label in this source. Detecting a blank price cannot waive ownership.
  _,raw=self.raw('card-markup-label');self.assertFalse(has_empty_dynamic_rate_slot(raw.decode()))
 def test_inline_markup_preserves_owned_name_without_accepting_other_names(self):
  html='<main><h1>Example Visa</h1><section data-cardname="Example&lt;sup&gt;®&lt;/sup&gt; Visa"><p>Purchase APR <span data-id="purchaseRate-123"></span>%</p></section></main>'
  self.assertTrue(has_empty_dynamic_rate_slot(html))
  self.assertFalse(has_empty_dynamic_rate_slot(html.replace('Example&lt;sup&gt;', 'Other&lt;sup&gt;')))
  self.assertFalse(has_empty_dynamic_rate_slot(html.replace('&lt;sup&gt;®&lt;/sup&gt;', '&lt;a&gt;®&lt;/a&gt;')))
 def test_completed_card_does_not_request_render(self):
  _,raw=self.raw('card-rendered');self.assertFalse(has_empty_dynamic_rate_slot(raw.decode()))
 def test_official_loan_retains_complete_owned_apr_disclosure(self):
  r,raw=self.raw('loan');segments=parse_snapshot_bytes(body=raw,content_type='text/html').segments
  records=[s for s in segments if s.anchor_type=='owned_lending_terms'];self.assertTrue(records)
  quote=next(s.text for s in records if 'as low as 10.24%' in s.text)
  for part in ['18.49%','36 or 48 months','automatic payments','12 and 60-month','15.99% APR','2.00%','Rates subject to change without notice.']:self.assertIn(part,quote)
  item=input_from_segments(bank='CN',url=r['url'],product='personal-loan',name='Citi® PERSONAL LOANS',country='US',segments=segments)
  row,v,e=run_services([item]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload']);self.assertNotIn('standard_rate',row['candidate_payload'])
 def test_official_rendered_card_retains_prices_and_all_qualifications(self):
  r,raw=self.raw('card-rendered');segments=parse_snapshot_bytes(body=raw,content_type='text/html').segments
  item=input_from_segments(bank='CN',url=r['url'],product='credit-card',name='Citi Double Cash® Credit Card',country='US',segments=segments)
  row,v,e=run_services([item]);p=row['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p)
  self.assertEqual(p['annual_fee'],0)
  for part in ['18.49','28.74','creditworthiness','Penalty APR','returned','18 months','4 months']:self.assertIn(part,p['purchase_interest_rate_summary'])
  self.assertNotIn('purchase_interest_rate',p)
 def test_official_purchase_clause_shapes_retain_complete_disclosure(self):
  for name in ['card-combined','card-intro','card-after-periods','card-colon']:
   _,raw=self.raw(name)
   seg=parse_snapshot_bytes(body=raw,content_type='text/html').segments
   offers=[s for s in seg if s.anchor_type=='owned_card_apr_offer']
   self.assertTrue(offers,name)
   self.assertTrue(any('creditworthiness' in s.text and 'Subject to credit approval' in s.text for s in offers),name)
 def test_card_name_suffix_mismatch_is_not_waived_by_pricing_clause(self):
  _,raw=self.raw('card-applies')
  seg=parse_snapshot_bytes(body=raw,content_type='text/html').segments
  self.assertFalse(any(s.anchor_type=='owned_card_apr_offer' for s in seg))
 def test_generic_empty_slots_are_acquisition_only(self):
  for label in ['minimumAnnualPercentageRate','interestRate','annualPercentageYield']:
   html='<main><h1>Other Savings</h1><p>Annual percentage yield <span data-id="'+label+'-123"></span>%</p></main>'
   self.assertTrue(has_empty_dynamic_rate_slot(html))
   for wrapper in ['nav','aside','footer','form']:
    self.assertFalse(has_empty_dynamic_rate_slot('<'+wrapper+'>'+html+'</'+wrapper+'>'))
   self.assertFalse(has_empty_dynamic_rate_slot(html.replace('</span>','3.5</span>')))
 def test_calculator_ancestor_cannot_request_price_render(self):
  html='<main><h1>Example Loan</h1><section class="loan-calculator"><p>Interest rate <span data-id="annualRate-123"></span>%</p></section></main>'
  self.assertFalse(has_empty_dynamic_rate_slot(html))
 def test_other_bank_loan_full_range_and_example(self):
  html='<title>Example Personal Loans</title><main><h1>Example Personal Loans</h1><p>Rates as of 9-29-2026. Your APR may be as low as 10.24% or as high as 18.49% for the term of your loan. The lowest rate requires automatic payments. Your APR will depend on your creditworthiness. Loans have 12 to 60 month terms. For example, a $10000 loan at 15.99% APR has monthly payments. If you are in default, your APR may increase by 2.00%. Rates subject to change without notice.</p></main>'
  seg=parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments
  self.assertTrue(any(s.anchor_type=='owned_lending_terms' and '2.00%' in s.text for s in seg))
  for bad in [html.replace('as high as 18.49%','as high as %'),html.replace('<p>','<aside><p>').replace('</p>','</p></aside>'),html.replace('<p>','<div data-product-name="Other Loan"><p>').replace('</p>','</p></div>')]:
   self.assertFalse(any(s.anchor_type=='owned_lending_terms' for s in parse_snapshot_bytes(body=bad.encode(),content_type='text/html').segments))
 def test_fee_qualification_conflicts_and_missing_prices_exclude(self):
  from worker.native_card_declarations import pricing_disclosure_fee
  q="Example Visa\nExample Visa Pricing Details\nThe variable APR for purchases is 18.5% - 28.5%, based on your creditworthiness. Annual Fee – None. Subject to credit approval."
  self.assertEqual(pricing_disclosure_fee(q),0)
  for extra in [' Annual Fee – $95.', ' Fee waived for the first year.', ' Only an annual fee discount applies.']:
   self.assertIsNone(pricing_disclosure_fee(q+extra))
  self.assertIsNone(pricing_disclosure_fee(q.replace('None.', 'None if you maintain a balance.')))
  self.assertIsNone(pricing_disclosure_fee(q.replace('Example Visa Pricing Details','Other Visa Pricing Details')))
 def test_reciprocal_return_requires_exact_callers_and_complete_note(self):
  from bs4 import BeautifulSoup
  from worker.native_dom_ownership import local_notes
  html='<a id="call" href="#note"><sup>1</sup></a><a id="call" href="#note">1</a><p id="note">Complete annual terms.<a href="#call">← Go back</a></p>'
  soup=BeautifulSoup(html,'html.parser');self.assertEqual(local_notes(soup,soup.find(id='note')),[])
  for bad in [html.replace('href="#note">1','href="#foreign">1'),html.replace('id="call"','id="missing"'),html.replace('← Go back','Read condition')]:
   soup=BeautifulSoup(bad,'html.parser');self.assertIsNone(local_notes(soup,soup.find(id='note')))
 def test_owned_pricing_does_not_accept_foreign_or_incomplete_block(self):
  html='<title>Example Visa</title><main><h1>Example Visa</h1><section><h3>Example Visa Pricing Details</h3><p>The variable APR for purchases is 18.5% - 28.5%, based on your creditworthiness. Annual Fee – None.</p><p>Subject to credit approval.</p></section></main>'
  def records(h):return [s for s in parse_snapshot_bytes(body=h.encode(),content_type='text/html').segments if s.anchor_type=='owned_card_apr_offer']
  self.assertTrue(records(html))
  for bad in [html.replace('Example Visa Pricing Details','Other Visa Pricing Details'),html.replace('18.5%', '<span data-id="purchaseRate"></span>%'),html.replace('<section>','<aside><section>').replace('</section>','</section></aside>'),html.replace('<section>','<section><input value="18.5">')]:self.assertFalse(records(bad))
 def test_partial_native_summary_and_wrong_origin_still_fail(self):
  from dataclasses import replace
  from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
  r,raw=self.raw('card-rendered');item=input_from_segments(bank='CN',url=r['url'],product='credit-card',name='Citi Double Cash® Credit Card',country='US',segments=parse_snapshot_bytes(body=raw,content_type='text/html').segments)
  self.assertFalse(_append_captured_decision_facts(context=item.context,candidates=[replace(c,source_snapshot_id='old') for c in item.candidates],fields=[],requested_fields=['annual_fee','purchase_interest_rate_summary']))
if __name__=='__main__':unittest.main()
