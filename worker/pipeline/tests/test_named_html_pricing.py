import gzip,hashlib,json,unittest
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
FIX=Path(__file__).parent/'fixtures/named-html-pricing'
class NamedHtmlPricingTests(unittest.TestCase):
 def test_official_complete_pricing_records(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):
   raw=gzip.decompress((FIX/r['fixture']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
   a=parse_snapshot_bytes(body=raw,content_type='text/html')
   records=[s for s in a.segments if s.anchor_type=='named_card_apr_terms']
   self.assertEqual(len(records),1,r['url'])
   self.assertIn('Variable Rate Information:',records[0].text)
   self.assertIn('Prime Rate',records[0].text)
   self.assertIn('How We Calculate Your Balance:',records[0].text)
   self.assertIn('How to Avoid Paying Interest on Purchases',records[0].text)
   self.assertLessEqual(len(records[0].text),8000)
   if 'future' in r['url']:
    self.assertIn('15 months',records[0].text);self.assertIn('within 90 days',records[0].text)
   else:self.assertIn('we will waive the Annual Fee',records[0].text)

 def test_real_sources_through_ordinary_services(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  for slug,name,fee in [('future','Truist Future credit card',0),('enjoy-beyond','Truist Enjoy Beyond credit card',95)]:
   raw=gzip.decompress((FIX/(slug+'.html.gz')).read_bytes())
   a=parse_snapshot_bytes(body=raw,content_type='text/html')
   item=input_from_segments(bank='TB',url='https://www.truist.com/credit-cards/'+slug,product='credit-card',name='Marketing credit card',segments=a.segments,country='US')
   item.context.source_metadata['expected_fields']=['product_name','annual_fee','purchase_interest_rate_summary']
   record,routing,_=run_services([item]);self.assertEqual(record['product_name'],name)
   payload=record['candidate_payload'];self.assertEqual(payload['annual_fee'],fee)
   self.assertIn('Variable Rate Information:',payload['purchase_interest_rate_summary'])
   self.assertEqual(routing.validation_action,'auto_validated')
   self.assertNotIn('purchase_interest_rate',payload)
   if slug=='enjoy-beyond':self.assertIn('Wealth Client',payload['fee_waiver_condition'])

 def test_generic_issuer_and_failure_boundaries(self):
  from bs4 import BeautifulSoup
  from worker.native_named_html_pricing import named_html_pricing
  raw=gzip.decompress((FIX/'future-disclosure.html.gz').read_bytes()).decode('utf8')
  generic=raw.replace('Truist','Example').replace('truist','example')
  self.assertTrue(named_html_pricing(BeautifulSoup(generic,'html.parser')))
  for changed in [generic.replace('Variable Rate Information:','Missing Information:'),
                  generic.replace('How We Calculate Your Balance:','Missing Calculation:'),
                  generic.replace('REV 070126',''),
                  generic.replace('Annual Percentage Rate (APR) for Purchases','Annual Percentage Rate (APR) for Cash'),
                  generic.replace('The rate for Purchases and Balance Transfers','Missing definition'),
                  generic.replace('6.75% as of July 1, 2026','X.XX% as of July 1, 2026')]:
   self.assertFalse(named_html_pricing(BeautifulSoup(changed,'html.parser')))

 def test_whole_price_record_is_atomic_and_comments_are_not_facts(self):
  from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
  raw=gzip.decompress((FIX/'future-disclosure.html.gz').read_bytes())
  a=parse_snapshot_bytes(body=raw,content_type='text/html')
  chunks=_build_evidence_chunks(parsed_document_id='parsed',source_language='en',artifact=a,max_chars=900,overlap_chars=120)
  terms=[c for c in chunks if c.anchor_type=='named_card_apr_terms'];self.assertEqual(len(terms),1)
  self.assertIn('REV 070126',terms[0].evidence_excerpt)
  self.assertNotIn('offerDisclosuresMap',terms[0].evidence_excerpt)

 def test_same_shared_account_and_conditional_zero_contracts(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  self.assertTrue(quote_supports_value('monthly_fee',5,'Example Savings Account\nMonthly maintenance fee\n$5'))
  self.assertFalse(quote_supports_value('monthly_fee',0,'No monthly maintenance fee if you maintain $5000.'))
  self.assertFalse(quote_supports_value('unlimited_transactions_flag',True,'Unlimited ATM transactions.'))

 def test_unresolved_masks_and_symbol_definitions(self):
  from worker.pipeline.fpds_rate_safety import contains_unresolved_financial_placeholder
  from worker.pipeline.fpds_normalization.service import _looks_like_unresolved_placeholder
  raw=gzip.decompress((FIX/'future-disclosure.html.gz').read_bytes())
  terms=next(s.text for s in parse_snapshot_bytes(body=raw,content_type='text/html').segments if s.anchor_type=='named_card_apr_terms')
  for check in [contains_unresolved_financial_placeholder,_looks_like_unresolved_placeholder]:
   self.assertFalse(check(terms))
   for bad in ['$***','X.XX%','{{rate}}',terms+' Annual Fee $***',terms.replace('16.74%','X.XX%')]:self.assertTrue(check(bad))

 def test_primary_identity_cannot_come_from_metadata_or_another_origin(self):
  from dataclasses import replace
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments
  from worker.pipeline.fpds_extraction.service import _captured_native_product_title
  raw=gzip.decompress((FIX/'future.html.gz').read_bytes());a=parse_snapshot_bytes(body=raw,content_type='text/html')
  item=input_from_segments(bank='TB',url='https://www.truist.com/credit-cards/future',product='credit-card',name='Marketing',segments=a.segments,country='US')
  self.assertEqual(_captured_native_product_title(item.context,item.candidates),'Truist Future credit card')
  for altered in [[c for c in item.candidates if c.anchor_type!='named_card_apr_terms'],
                  [replace(c,source_snapshot_id='foreign') if c.anchor_type=='named_card_apr_terms' else c for c in item.candidates],
                  [replace(c,evidence_excerpt='Other credit card | Example') if c.anchor_type=='document_title' else c for c in item.candidates]]:
   self.assertNotEqual(_captured_native_product_title(item.context,altered),'Truist Future credit card')

 def test_conditional_zero_and_main_boundary(self):
  from worker.native_named_html_pricing import named_html_fee_value,named_html_pricing
  from bs4 import BeautifulSoup
  raw=gzip.decompress((FIX/'future-disclosure.html.gz').read_bytes())
  soup=BeautifulSoup(raw,'html.parser');records=named_html_pricing(soup)
  quote=next(q for k,o,q in records if k=='named_html_annual_fee')
  self.assertEqual(named_html_fee_value(quote),0)
  for condition in ['Annual Fee is None only if eligible.', 'Annual fee discount applies.', 'Annual Fee applies unless provided otherwise.']:
   self.assertIsNone(named_html_fee_value(quote+'\n'+condition))
  # A boundary outside main cannot supply a missing final revision marker.
  head=soup.find('main')
  if head is not None:
   for text in head.find_all(string=True):
    if 'REV 070126' in text:text.replace_with(str(text).replace('REV 070126',''))
   soup.body.append(BeautifulSoup('<p>REV 070126</p>','html.parser'))
   self.assertFalse(named_html_pricing(soup))

 def test_verified_price_qualifier_survives_public_minimum_fields(self):
  from worker.pipeline.fpds_aggregate_refresh.service import _build_product_refresh_metadata
  value='The annual fee is waived if the account holder meets the disclosed wealth conditions.'
  for product in ['credit-card','savings','personal-loan']:
   for verified in [[],['fee_waiver_condition']]:
    metadata=_build_product_refresh_metadata(payload={'fee_waiver_condition':value,'notes':'private internal notes','_collection_accuracy':{'verified_fields':verified}},product_version_id='v',product_url=None,allowed_field_names={'product_name'},product_type=product)
    self.assertEqual(metadata.get('fee_waiver_condition'),value if verified else None)
    self.assertNotIn('notes',metadata)
    self.assertNotIn('_collection_accuracy',metadata)
