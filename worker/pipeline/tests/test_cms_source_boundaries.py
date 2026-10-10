"""Official-byte source boundaries and definite property collateral evidence."""
import gzip,hashlib,json,re,unittest
from pathlib import Path
from worker.discovery.fpds_discovery.discovery import extract_links
from worker.source_content_validity import html_unavailable_reason
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_approval_policy import security_meaning
F=Path(__file__).parent/'fixtures/cms-source-boundaries'
def chunked_segments(raw, content_type):
 from types import SimpleNamespace
 from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
 artifact=parse_snapshot_bytes(body=raw,content_type=content_type)
 chunks=_build_evidence_chunks(parsed_document_id='parsed-fixture',source_language='en',artifact=artifact,max_chars=900,overlap_chars=120)
 for chunk in chunks:
  assert artifact.full_text[chunk.chunk_char_start:chunk.chunk_char_end]==chunk.evidence_excerpt
 return [SimpleNamespace(anchor_type=c.anchor_type,anchor_value=c.anchor_value,page_no=c.page_no,text=c.evidence_excerpt) for c in chunks]

class SourceBoundaryTests(unittest.TestCase):
 def raw(self,name):
  r=next(r for r in json.loads((F/'sources.json').read_text(encoding='utf8')) if r['fixture']==name+'.html.gz')
  raw=gzip.decompress((F/r['fixture']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256']);return r,raw
 def test_actual_content_item_urls_are_not_public_links(self):
  r,raw=self.raw('heloc');links=extract_links(raw.decode(),base_url=r['url'])
  self.assertFalse(any('/page-data/' in x.href.lower() for x in links))
  self.assertTrue(any(x.href == 'https://www.huntington.com/Personal/heloc-digital-application' for x in links))
 def test_cms_items_preserve_nested_actual_links_across_markets(self):
  payload={'id':'93fb0602-e36f-4b95-9667-80a9cad74681','url':'/data/savings-prices','name':'Rates','displayName':'Rates','fields':{'Content':{'value':'Rates are on the parent page.'},'Link':{'value':{'href':'/current-rates','text':'Current rates'}}}}
  html='<script type="application/json">'+json.dumps(payload)+'</script><a href="/savings">Savings</a>'
  links={x.href for x in extract_links(html,base_url='https://example.ca/accounts')}
  self.assertNotIn('/data/savings-prices',links);self.assertIn('/current-rates',links);self.assertIn('/savings',links)
  public='<script type="application/ld+json">'+json.dumps({'@type':'Product','url':'/named-cd','name':'Named CD'})+'</script>'
  self.assertTrue(any(x.href.endswith('/named-cd') for x in extract_links(public,base_url='https://example.com')))
 def test_actual_soft404_cannot_parse_as_success(self):
  _,raw=self.raw('soft404');self.assertEqual(html_unavailable_reason(raw),'soft_404')
  with self.assertRaises(ValueError):parse_snapshot_bytes(body=raw,content_type='text/html')
 def test_error_message_requires_prominent_error_identity(self):
  for html in ['<h1>Example Savings</h1><p>We cannot find that page is a sample error message.</p>','<h1>Example Loan</h1><p>Something went wrong with a payment? Contact us.</p>']:
   self.assertIsNone(html_unavailable_reason(html.encode()))
  self.assertEqual(html_unavailable_reason(b'<h1>Oops!</h1><p>We cannot find that page.</p>'),'soft_404')
 def test_actual_mandatory_property_security_keeps_all_fees(self):
  _,raw=self.raw('heloc');records=[s for s in parse_snapshot_bytes(body=raw,content_type='text/html').segments if s.anchor_type=='owned_lending_terms' and 'real property securing' in s.text]
  self.assertEqual(len(records),1);self.assertIn('$750,000',records[0].text);self.assertIn('$375',records[0].text);self.assertIs(security_meaning(records[0].text),True)
 def test_other_bank_property_security_uncertainty_and_conflict(self):
  own='Example Line of Credit\nInsurance must be carried on the real property securing the account.'
  self.assertIs(security_meaning(own),True)
  for bad in [own.replace('must be carried','may be carried'),own+' This account is unsecured.',own+' Collateral may be required.',own+' It could be unsecured.']:
   self.assertIsNone(security_meaning(bad))
 def test_current_account_price_component_survives_marketing_headings(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  r,raw=self.raw('savings');segments=chunked_segments(raw,'text/html')
  panels=[s for s in segments if s.anchor_type=='owned_account_apy'];self.assertEqual(len(panels),1);self.assertGreater(len(panels[0].text),900)
  item=input_from_segments(bank='GSBU',url=r['url'],product='savings',name='High Yield Online Savings Account',country='US',segments=segments)
  row,v,e=run_services([item]);p=row['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p)
  self.assertEqual(p['standard_rate'],3.5);self.assertEqual(p['monthly_fee'],0);self.assertEqual(p['minimum_deposit'],0)
  self.assertEqual(row['product_name'],'Online Savings Account');self.assertIn('October 09, 2026',p['interest_rate_summary']);self.assertIn('Maximum balance limits',p['interest_rate_summary'])
  self.assertNotIn('promotional_rate',p)
  from worker.pipeline.fpds_collection_accuracy import text
  self.assertEqual(text(p['interest_rate_summary']),text(panels[0].text))
 def test_generic_account_price_ownership_conditions_and_origins(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
  from dataclasses import replace
  html='<title>High Yield Example Savings Account | Example Bank</title><main><h1>Grow your future</h1><section><p>3.25% APY</p><p>Example Savings Account Annual Percentage Yield</p><p>No fees. No minimum deposit.</p><p>Annual percentage yield as of October 09, 2026. APY may change at any time before or after account is opened. Maximum balance limits apply.</p></section></main>'
  def parse(h):return parse_snapshot_bytes(body=h.encode(),content_type='text/html').segments
  segments=parse(html);item=input_from_segments(bank='OTHER',url='https://example.ca/savings/high-yield-savings',product='savings',name='Example Savings Account',country='CA',segments=segments)
  self.assertTrue(any(s.anchor_type=='owned_account_apy' for s in segments))
  for bad in [html.replace('3.25% APY','% APY'),html.replace('3.25% APY','3.25% APY for the first 3 months'),html.replace('No fees.','No fees if eligible.'),html.replace('<section>','<section data-product-name="Other Savings Account">'),html.replace('<section>','<section class="savings-calculator">'),html.replace('Maximum balance limits apply.','Maximum balance limits apply. Another APY is 4.5%.'),html.replace('High Yield Example Savings Account | Example Bank','Other Savings Account | Example Bank')]:
   self.assertFalse(any(s.anchor_type=='owned_account_apy' for s in parse(bad)),bad)
  self.assertFalse(_append_captured_decision_facts(context=item.context,candidates=[replace(c,source_snapshot_id='old') for c in item.candidates],fields=[],requested_fields=['standard_rate']))
 def test_actual_single_card_pdf_keeps_continuation_and_issuer_identity(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  raw=gzip.decompress((F/'single-card.pdf.gz').read_bytes());r=next(r for r in json.loads((F/'sources.json').read_text()) if r['fixture']=='single-card.pdf.gz');self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
  segments=chunked_segments(raw,'application/pdf')
  records=[s for s in segments if s.anchor_type=='single_card_purchase_terms'];self.assertEqual(len(records),1)
  self.assertIn('16.49% to 25.49%',records[0].text);self.assertIn('December 31, 2025',records[0].text);self.assertIn('60 days late',records[0].text);self.assertIn('CONDITIONS:',records[0].text)
  html=b'<title>Cash Rewards Credit Card | First Citizens</title><main><h1>Cash Rewards Credit Card</h1><p>Annual Fee</p><p>$0</p></main>'
  detail=input_from_segments(bank='FCB',url='https://www.firstcitizens.com/personal/credit-cards/cash-rewards',product='credit-card',name='Cash Rewards Credit Card',country='US',segments=parse_snapshot_bytes(body=html,content_type='text/html').segments)
  companion=input_from_segments(bank='FCB',url=r['url'],product='credit-card',name='Pricing',country='US',segments=segments,role='linked_pdf',ident='pdf')
  row,v,e=run_services([detail,companion]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload']);self.assertNotIn('purchase_interest_rate',row['candidate_payload']);self.assertIn('Prime Rate',row['candidate_payload']['purchase_interest_rate_summary'])
 def test_tooltip_copies_require_local_complete_agreement(self):
  from bs4 import BeautifulSoup
  from worker.native_dom_ownership import local_notes
  html='<main><section><a href="#price">1</a><div tooltip-data-id="price">Complete fee condition.</div></section><div tooltip-data-id="price">Complete fee condition.</div></main>'
  soup=BeautifulSoup(html,'html.parser');self.assertEqual(local_notes(soup,soup.section),['Complete fee condition.'])
  for bad in [html.replace('Complete fee condition.</div></main>','Different fee condition.</div></main>'),html.replace('<div tooltip-data-id="price">Complete fee condition.</div></section>','</section>'),html.replace('</section>','<div tooltip-data-id="price">Complete fee condition.</div></section>')]:
   soup=BeautifulSoup(bad,'html.parser');self.assertIsNone(local_notes(soup,soup.section))
 def test_single_pdf_missing_pages_other_names_and_issuer_reject(self):
  from worker.native_single_card_pdf import single_card_purchase_records,issuer_product_match,single_card_fee_value
  from pypdf import PdfReader
  from io import BytesIO
  pages=[p.extract_text() for p in PdfReader(BytesIO(gzip.decompress((F/'single-card.pdf.gz').read_bytes()))).pages]
  for bad in [pages[:1],[pages[0],''],[pages[0],pages[1].replace('CONDITIONS:','')],[pages[0],pages[1]+' Other Credit Card Pricing Information Disclosure']]:self.assertFalse(single_card_purchase_records(bad))
  self.assertIsNone(single_card_fee_value('Example Cash Rewards Credit Card\nAnnual Fee $95 (None)'))
  self.assertIsNone(single_card_fee_value('Example Cash Rewards Credit Card\nAnnual Fee $0 Intro fee for the first year. After that, $95.'))
  self.assertTrue(issuer_product_match('Example Bank Cash Rewards Credit Card','Cash Rewards Credit Card','https://examplebank.com/pricing.pdf'))
  self.assertFalse(issuer_product_match('Example Bank Cash Rewards Credit Card','Rewards Credit Card','https://examplebank.com/pricing.pdf'))
  self.assertFalse(issuer_product_match('Other Bank Cash Rewards Credit Card','Cash Rewards Credit Card','https://examplebank.com/pricing.pdf'))
  self.assertEqual(html_unavailable_reason(b"<h1>Oops, Something went wrong.</h1><p>The page you're trying to access doesn't appear to exist</p>"),'soft_404')
 def test_actual_seo_alias_requires_current_detail_link_and_native_pdf_name(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  from dataclasses import replace
  rows=json.loads((F/'sources.json').read_text(encoding='utf8'));inputs=[]
  for fixture,typ,role,ident in [('alias-card.html.gz','text/html','detail','alias'),('alias-card.pdf.gz','application/pdf','linked_pdf','pdf')]:
   r=next(r for r in rows if r['fixture']==fixture);raw=gzip.decompress((F/fixture).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
   inputs.append(input_from_segments(bank='FCB',url=r['url'],product='credit-card',name='Smart Option (Low Interest) Credit Card',country='US',segments=chunked_segments(raw,typ),role=role,ident=ident))
  row,v,_=run_services(inputs);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload']);self.assertEqual(row['product_name'],'Smart Option Credit Card');self.assertIn('13.49% to 22.49%',row['candidate_payload']['purchase_interest_rate_summary'])
  no_link=replace(inputs[0],candidates=[c for c in inputs[0].candidates if c.anchor_type not in {'captured_product_link','captured_disclosure_link'}])
  row,v,_=run_services([no_link,inputs[1]]);self.assertEqual(v.validation_action,'excluded')
if __name__=='__main__':unittest.main()
