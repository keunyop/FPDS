"""Source-backed current link applicability and database-safe parsed text."""
import gzip,hashlib,json,unittest
from pathlib import Path
from dataclasses import replace
from bs4 import BeautifulSoup
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_cms_source_boundaries import chunked_segments
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
F=Path(__file__).parent/'fixtures/owned-apr-source'
class LinkedPricingTests(unittest.TestCase):
 def raw(self,name):
  r=next(x for x in json.loads((F/'sources.json').read_text()) if x['fixture']==name+'.html.gz');raw=gzip.decompress((F/r['fixture']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256']);return r,raw
 def inputs(self):
  r,raw=self.raw('freedom-unlimited');q,legal=self.raw('linked-pricing');name='Chase Freedom Unlimited Credit Card'
  detail=input_from_segments(bank='JCBN',url=r['url'],product='credit-card',name=name,country='US',segments=chunked_segments(raw,'text/html'))
  detail=replace(detail,context=replace(detail.context,source_metadata={**detail.context.source_metadata,'official_domain_allowlist':['chase.com']}))
  companion=input_from_segments(bank='JCBN',url=q['url'],product='credit-card',name='Pricing Information',country='US',role='supporting_html',ident='pricing',segments=chunked_segments(legal,'text/html'))
  return detail,companion
 def test_official_current_link_full_pricing_and_origin(self):
  detail,companion=self.inputs();row,v,_=run_services([detail,companion]);p=row['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p);self.assertEqual(p['annual_fee'],0);self.assertNotIn('purchase_interest_rate',p)
  summary=p['purchase_interest_rate_summary'];self.assertIn('18.49%',summary);self.assertIn('27.99%',summary);self.assertIn('60 days late',summary);self.assertIn('indefinitely',summary);self.assertIn('9/22/2026',summary)
  self.assertEqual(row['field_mapping_metadata']['purchase_interest_rate_summary']['official_web_sources'][0]['url'],companion.context.source_metadata['normalized_source_url'])
 def test_missing_foreign_conflicting_or_stale_link_never_binds(self):
  from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence
  detail,companion=self.inputs()
  for changed in [replace(detail,candidates=[c for c in detail.candidates if c.anchor_type!='captured_disclosure_link']),replace(detail,candidates=[replace(c,source_snapshot_id='old') if c.anchor_type=='captured_disclosure_link' else c for c in detail.candidates])]:
   bound=_bind_grounding_evidence([changed,companion])[0];self.assertFalse(any(c.anchor_type=='linked_card_pricing_terms' for c in bound.grounding_candidates))
  for changed in [replace(companion,context=replace(companion.context,bank_code='OTHER')),replace(companion,context=replace(companion.context,country_code='CA')),replace(companion,context=replace(companion.context,source_metadata={**companion.context.source_metadata,'normalized_source_url':'https://evil.example/prices'}))]:
   bound=_bind_grounding_evidence([detail,changed])[0];self.assertFalse(any(c.anchor_type=='linked_card_pricing_terms' for c in bound.grounding_candidates))
 def test_current_h1_and_linked_prices_keep_network_words_with_abbreviated_seo(self):
  _,legal=self.raw('linked-pricing');html='<title>Example Travel Credit Card | Example Bank</title><main><h1>Example Travel Visa Signature Credit Card</h1><div><p>$95 annual fee</p></div><a href="https://example.com/legal/pricing">Pricing and Terms</a></main>'
  def item(h):
   x=input_from_segments(bank='OTHER',url='https://example.com/cards/example-travel',product='credit-card',name='Example Travel Visa Signature Credit Card',country='US',segments=chunked_segments(h.encode(),'text/html'))
   return replace(x,context=replace(x.context,source_metadata={**x.context.source_metadata,'discovery_metadata':{**x.context.source_metadata['discovery_metadata'],'product_identity_match':False,'page_title':'Example Travel Credit Card | Example Bank'}}))
  c=input_from_segments(bank='OTHER',url='https://example.com/legal/pricing',product='credit-card',name='Pricing Information',country='US',role='supporting_html',ident='pricing',segments=chunked_segments(legal,'text/html'))
  row,v,_=run_services([item(html),c]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload']);self.assertEqual(row['product_name'],'Example Travel Visa Signature Credit Card')
  for bad in [html.replace('Visa Signature','Gold'),html.replace('https://example.com/legal/pricing','https://example.com/unmatched-pricing'),html.replace('<main>','<main><h1>Other Card</h1>')]:
   row,v,_=run_services([item(bad),c]);self.assertEqual(v.validation_action,'excluded')
 def test_other_named_card_panel_cannot_supply_detail_pricing_link(self):
  detail,companion=self.inputs();target=companion.context.source_metadata['normalized_source_url']
  html='<main><h1>Example Travel Credit Card</h1><div><p>$95 annual fee</p></div><section data-card-name="Other Rewards Credit Card"><a href="'+target+'">Pricing and Terms</a></section></main>'
  segments=chunked_segments(html.encode(),'text/html');self.assertFalse(any(x.anchor_type=='captured_disclosure_link' for x in segments))
 def test_actual_cms_nul_is_visible_replacement_with_exact_spans(self):
  _,raw=self.raw('affordable');artifact=parse_snapshot_bytes(body=raw,content_type='text/html');self.assertNotIn(chr(0),artifact.full_text);self.assertIn(chr(0xfffd),artifact.full_text)
  for s in artifact.segments:self.assertEqual(artifact.full_text[s.char_start:s.char_end],s.text)
 def test_cross_type_nul_cannot_fuse_financial_digits(self):
  a=parse_snapshot_bytes(body=b'<main><h1>Example Savings</h1><p>Annual APY 3\x00.25%</p></main>',content_type='text/html');self.assertNotIn(chr(0),a.full_text);self.assertNotIn('3.25%',a.full_text)
 def test_other_bank_market_and_native_fee_paragraph(self):
  _,legal=self.raw('linked-pricing')
  html=b'<title>Example Travel Credit Card | Example Bank</title><main><h1>Example Travel Credit Card</h1><div><p>$95 annual fee<sup><a href="https://example.com/legal/prices" title="Pricing and Terms">*</a></sup></p></div><p><a href="https://example.com/legal/prices">Pricing and Terms</a></p></main>'
  for country in ['US','CA']:
   detail=input_from_segments(bank='OTHER',url='https://example.com/cards/travel',product='credit-card',name='Example Travel Credit Card',country=country,segments=chunked_segments(html,'text/html'))
   companion=input_from_segments(bank='OTHER',url='https://example.com/legal/prices',product='credit-card',name='Pricing Information',country=country,role='supporting_html',ident='pricing',segments=chunked_segments(legal,'text/html'))
   row,v,_=run_services([detail,companion]);self.assertEqual(v.validation_action,'auto_validated' if country=='US' else 'excluded',row['candidate_payload']);self.assertEqual(row['candidate_payload']['annual_fee'],95);self.assertEqual(row['currency'],'USD' if country=='US' else 'CAD');self.assertIn('purchase_interest_rate_summary',row['candidate_payload']['_collection_accuracy']['verified_fields'])
 def test_complete_long_pricing_and_single_variable_apr_are_not_truncated(self):
  from worker.native_linked_card_pricing import pricing_records
  for name in ['long-pricing','single-apr']:
   _,raw=self.raw(name);records=pricing_records(BeautifulSoup(raw,'html.parser'));self.assertEqual(len(records),1)
   quote=records[0][2]
   if name=='long-pricing':self.assertGreater(len(quote),6400);self.assertIn('Promotional Financing Equal Pay',quote)
   else:self.assertIn('29.24%',quote)
   detail_html=b'<title>Example Travel Credit Card | Example Bank</title><main><h1>Example Travel Credit Card</h1><div><p>$95 annual fee</p></div><a href="https://example.com/legal/pricing">Pricing and Terms</a></main>'
   d=input_from_segments(bank='OTHER',url='https://example.com/cards/travel',product='credit-card',name='Example Travel Credit Card',country='US',segments=chunked_segments(detail_html,'text/html'))
   c=input_from_segments(bank='OTHER',url='https://example.com/legal/pricing',product='credit-card',name='Pricing Information',country='US',role='supporting_html',ident='pricing',segments=chunked_segments(raw,'text/html'))
   row,v,_=run_services([d,c]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload'])
   from worker.pipeline.fpds_collection_accuracy import text
   self.assertEqual(text(row['candidate_payload']['purchase_interest_rate_summary']),text(quote));self.assertNotIn('purchase_interest_rate',row['candidate_payload'])
 def test_ordinary_model_context_keeps_link_and_complete_financing_within_caps(self):
  from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence,_append_captured_decision_facts,_select_official_grounding_chunks
  detail,companion=self.inputs();_,raw=self.raw('long-pricing');companion=input_from_segments(bank='JCBN',url=companion.context.source_metadata['normalized_source_url'],product='credit-card',name='Pricing Information',country='US',role='supporting_html',ident='pricing',segments=chunked_segments(raw,'text/html'))
  bound=_bind_grounding_evidence([detail,companion])[0];fields=_append_captured_decision_facts(context=bound.context,candidates=bound.grounding_candidates,fields=[],requested_fields=['product_name','annual_fee','purchase_interest_rate_summary'])
  fact=next(f for f in fields if f.field_name=='purchase_interest_rate_summary');chosen=_select_official_grounding_chunks(candidates=bound.grounding_candidates,collected_fields=fields)
  self.assertIn(fact.evidence_chunk_id,{c.evidence_chunk_id for c in chosen});self.assertIn(fact.field_metadata['applicability_evidence_chunk_id'],{c.evidence_chunk_id for c in chosen});self.assertLessEqual(len(chosen),24);self.assertLessEqual(sum(len(c.evidence_excerpt) for c in chosen),43200)
 def test_pricing_missing_notes_duplicate_rows_and_invalid_ranges_exclude(self):
  from worker.native_linked_card_pricing import pricing_records
  _,raw=self.raw('linked-pricing');html=raw.decode('utf8');self.assertEqual(len(pricing_records(BeautifulSoup(html,'html.parser'))),1)
  changes=[html.replace('Loss of Intro APR:', 'Missing consequence:'),html.replace('Prime Rate:','Missing basis:'),html.replace('>a</sup>','>z</sup>',1),html.replace('TERMS &amp; CONDITIONS','No boundary'),html.replace('>18.49%</span>','>98.49%</span>')]
  from copy import deepcopy
  soup=BeautifulSoup(html,'html.parser');soup.html.append(deepcopy(soup.find('table')));changes.append(str(soup))
  for bad in changes:self.assertFalse(pricing_records(BeautifulSoup(bad,'html.parser')))
 def test_official_fee_reference_not_a_fee_condition(self):
  from worker.native_card_declarations import card_declarations,declaration_fee_value
  _,raw=self.raw('sapphire-preferred');records=card_declarations(BeautifulSoup(raw,'html.parser'));fees=[q for kind,owner,q in records if kind=='labelled_financial_record' and declaration_fee_value(q)==95];self.assertEqual(len(fees),1)
  for text in ['$0 annual fee for the first year, then $95','$0 annual fee if eligible','$95 annual fee. No annual fee.']:
   html='<main><h1>Example Credit Card</h1><div><p>'+text+'</p></div></main>'
   self.assertFalse(any(declaration_fee_value(q) is not None for k,o,q in card_declarations(BeautifulSoup(html,'html.parser')) if k=='labelled_financial_record'))
 def test_actual_security_eligibility_is_distinct_and_complete(self):
  from worker.pipeline.fpds_approval_policy import security_meaning
  _,raw=self.raw('heloc');segments=chunked_segments(raw,'text/html');records=[x for x in segments if x.anchor_type=='owned_lending_terms' and 'as collateral' in x.text];self.assertEqual(len(records),1);quote=records[0].text
  self.assertIs(security_meaning(quote),True);self.assertIn('680',quote);self.assertIn('except Texas',quote);self.assertIn('80%',quote)
  for bad in [quote.replace('allows you to use','may allow you to use'),quote+' This account is unsecured.',quote+' Collateral may be required.']:
   self.assertIsNone(security_meaning(bad))
 def test_actual_heloc_offer_passes_with_complete_scenario_and_collateral(self):
  r,raw=self.raw('heloc');name='Home equity line of credit (HELOC)';item=input_from_segments(bank='JCBN',url=r['url'],product='line-of-credit',name=name,country='US',segments=chunked_segments(raw,'text/html'))
  row,v,_=run_services([item]);p=row['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p);self.assertIs(p['secured_flag'],True);self.assertNotIn('interest_rate',p)
  for condition in ['8.37%','43240','30-year','$100,000','55%','Ohio','excellent credit','18%','7%']:self.assertIn(condition,p['interest_rate_summary'])
  self.assertIn('except Texas',p['security_requirement'])
 def test_generic_offer_ownership_and_scenario_requirements(self):
  from worker.native_owned_lending_records import lending_records
  html='<main><h1>Example Home Equity Line of Credit</h1><div><p>Variable rate of 8.37% in ZIP code 43240 as of September 18th, 2026</p><p>Sample variable APR assumes a new 30-year $100,000 HELOC with a combined loan-to-value ratio of up to 55%. The actual APR may vary and be higher or lower than the rate shown. APR is based on the Prime Rate with a fixed margin and will not exceed 18%. Prime Rate is 7%.</p></div></main>'
  self.assertEqual(len(lending_records(BeautifulSoup(html,'html.parser'))),1)
  for bad in [html.replace('<div>','<div data-product-name="Another Line of Credit">'),html.replace('<div>','<form>'),html.replace('<div>','<div class="rate-calculator">'),html.replace('Sample variable APR assumes','Missing assumption'),html.replace('APR is based on the Prime Rate','Unknown annual basis'),html.replace('Variable rate of 8.37%','Variable rate of X.XX%')]:
   self.assertFalse(lending_records(BeautifulSoup(bad,'html.parser')))
 def test_qualified_generic_security_is_never_inferred(self):
  from worker.pipeline.fpds_approval_policy import security_meaning
  for q in ['Example Line of Credit may require collateral.','Example Loan depending on your assets.','Example HELOC uses credit approval.']:
   self.assertIsNone(security_meaning(q))
 def test_nul_anchor_and_pdf_segments_preserve_separation(self):
  from worker.pipeline.fpds_parse_chunk.parser import _finalize_segments,_RawSegment
  text,segments=_finalize_segments([_RawSegment('page','page-1',1,'APR 3'+chr(0)+'.25%')]);self.assertEqual(text,'APR 3'+chr(0xfffd)+'.25%');self.assertEqual(text[segments[0].char_start:segments[0].char_end],segments[0].text)
  a=parse_snapshot_bytes(body=b'<main><h1>Example\x00Card</h1><p>Annual fee $25</p></main>',content_type='text/html')
  self.assertTrue(all(chr(0) not in str(x.anchor_value) for x in a.segments))
if __name__=='__main__':unittest.main()
