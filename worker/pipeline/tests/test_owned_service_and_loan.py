import gzip,hashlib,json,unittest
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/owned-service-and-loan'
def raw(name):return gzip.decompress((FIX/(name+'.html.gz')).read_bytes())
class OwnedServiceAndLoanTests(unittest.TestCase):
 def test_official_source_checksums(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):
   self.assertEqual(hashlib.sha256(gzip.decompress((FIX/r['fixture']).read_bytes())).hexdigest(),r['sha256'])
 def test_own_monthly_service_charge_keeps_base_and_waiver(self):
  a=parse_snapshot_bytes(body=raw('wab-checking'),content_type='text/html')
  item=input_from_segments(bank='WAB',url='https://www.westernalliancebancorporation.com/personal/checking/personal-checking',product='chequing',name='Personal Checking',segments=a.segments,country='US')
  record,val,_=run_services([item]);p=record['candidate_payload']
  self.assertEqual(p.get('monthly_fee'),5,p.get('_collection_accuracy'))
  self.assertTrue(p.get('unlimited_transactions_flag'))
  self.assertIn('direct deposit',p.get('fee_waiver_condition',''))
  self.assertNotIn('minimum_balance',p)
  self.assertEqual(val.validation_action,'auto_validated')
 def test_complete_dated_loan_range_and_customer_term_boundary(self):
  a=parse_snapshot_bytes(body=raw('us-personal-loan'),content_type='text/html')
  item=input_from_segments(bank='USBN',url='https://www.usbank.com/loans-credit-lines/personal-loans-and-lines-of-credit/personal-loan.html',product='personal-loan',name='Personal Loan',segments=a.segments,country='US')
  item.context.source_metadata['product_family']='lending'
  record,val,_=run_services([item]);p=record['candidate_payload']
  self.assertEqual(val.validation_action,'auto_validated',p.get('_collection_accuracy'))
  self.assertIn('9.24% APR to 24.99% APR',p['interest_rate_summary'])
  self.assertIn('Loan payment example:',p['interest_rate_summary'])
  self.assertIn('up to 60 months for non-clients',p['term_length_text'])
  self.assertNotIn('interest_rate',p);self.assertNotIn('term_length_days',p)
 def test_observed_important_credit_terms_is_an_essential_lead(self):
  from api_service.collection_evidence_research import _link_relevance
  for product,label,url in [('credit-card','Important credit terms','https://example.com/credit-cards/own-card/terms'),('personal-loan','Important credit terms','https://example.com/personal-loan/terms')]:
   self.assertGreater(_link_relevance(product_type=product,url=url,label=label,missing=['interest_rate_summary']),0)
  for url,label in [('https://example.com/privacy','Important credit terms'),('https://example.com/login','Important credit terms'),('https://example.com/credit-cards/own-card/terms','Apply now')]:
   self.assertEqual(_link_relevance(product_type='credit-card',url=url,label=label,missing=['purchase_interest_rate_summary']),0)

 def test_current_linked_application_prices_survive_ordinary_gates(self):
  url='https://creditcards.wellsfargo.com/active-cash-credit-card'
  a=parse_snapshot_bytes(body=raw('wf-card'),content_type='text/html')
  b=parse_snapshot_bytes(body=raw('wf-card-terms'),content_type='text/html')
  detail=input_from_segments(bank='WFBN',url=url,product='credit-card',name='Active Cash Credit Card',segments=a.segments,country='US')
  detail.context.source_metadata['official_domain_allowlist']=['wellsfargo.com']
  from worker.discovery.fpds_discovery.url_utils import normalize_source_url
  terms_url=normalize_source_url(next(c.evidence_excerpt for c in detail.candidates if c.anchor_type=='captured_disclosure_link'))
  terms=input_from_segments(bank='WFBN',url=terms_url,product='credit-card',name='Pricing Information',segments=b.segments,country='US',role='supporting_html',ident='terms')
  record,val,extraction=run_services([detail,terms]);p=record['candidate_payload']
  self.assertEqual(val.validation_action,'auto_validated',p.get('_collection_accuracy'))
  self.assertEqual(p['annual_fee'],0)
  for literal in ['18.74%, 24.74%, or 28.74%','120 days','Maximum APR','last 48 months','How We Determine the U.S. Prime Rate']:
   self.assertIn(literal,p['purchase_interest_rate_summary'])
  self.assertNotIn('purchase_interest_rate',p)
  for f in extraction.extracted_fields:
   if f.field_name in {'annual_fee','purchase_interest_rate_summary'}:
    self.assertEqual(f.source_document_id,terms.context.source_document_id)
    self.assertTrue(f.field_metadata.get('applicability_evidence_chunk_id'))
  missing=type(detail)(detail.context,[c for c in detail.candidates if c.anchor_type!='captured_disclosure_link'])
  _,rejected,_=run_services([missing,terms]);self.assertEqual(rejected.validation_action,'excluded')
 def test_whole_linked_price_and_generic_issuer_boundaries(self):
  from bs4 import BeautifulSoup
  from worker.native_linked_application_pricing import application_pricing_records,application_owner_matches
  html=raw('wf-card-terms').decode('utf8')
  generic=html.replace('Wells Fargo','Example Bank').replace('WellsFargo','ExampleBank').replace('wellsfargo','examplebank')
  self.assertTrue(application_pricing_records(BeautifulSoup(generic,'html.parser')))
  for label in ['Table of Contents','How do we calculate your variable APRs?','How We Determine the U.S. Prime Rate','Maximum APR']:
   self.assertFalse(application_pricing_records(BeautifulSoup(generic.replace(label,'Missing boundary'),'html.parser')),label)
  quote=application_pricing_records(BeautifulSoup(generic,'html.parser'))[0][2]
  self.assertTrue(application_owner_matches(quote,'Active Cash Credit Card','https://examplebank.com/terms'))
  self.assertFalse(application_owner_matches(quote,'Other Credit Card','https://examplebank.com/terms'))
  self.assertFalse(application_owner_matches(quote,'Active Cash Credit Card','https://foreignbank.com/terms'))
 def test_service_base_amount_never_becomes_waiver_balance_or_zero(self):
  from worker.native_owned_account_records import service_monthly_fee
  from worker.pipeline.fpds_normalization.service import _money_value_is_non_fee_context
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  q='Example Savings Account\nMonthly service charge of $7 waived with one monthly recurring direct deposit, or for maintaining a daily balance of $700.'
  self.assertEqual(service_monthly_fee(q),7)
  self.assertFalse(_money_value_is_non_fee_context(field_name='monthly_fee',value=7,context=q))
  self.assertTrue(quote_supports_value('monthly_fee',7,q));self.assertFalse(quote_supports_value('monthly_fee',0,q))
  self.assertFalse(quote_supports_value('monthly_fee',700,q))
  self.assertTrue(_money_value_is_non_fee_context(field_name='monthly_fee',value=700,context='Direct deposit $700 to get a welcome bonus.'))
  for bad in [q.replace('$7 waived','$0 waived'),q.replace('Monthly service','First year monthly service'),q+'\nMonthly service charge of $9.']:
   self.assertIsNone(service_monthly_fee(bad))
 def test_dated_loan_keeps_complete_range_and_rejects_broken_context(self):
  from worker.native_owned_lending_records import dated_loan_range
  from bs4 import BeautifulSoup
  soup=BeautifulSoup(raw('us-personal-loan'),'html.parser')
  q=next(p.get_text(' ',strip=True) for p in soup.find_all('p') if 'Annual Percentage Rate (APR) ranged from' in p.get_text())
  generic=q.replace('U.S. Bank','Example Bank');self.assertIn('non-clients',dated_loan_range(generic,'Personal Loan'))
  for bad in [generic.replace('9.24% APR','x.xx% APR'),generic.replace('loan terms range from','repayment example ranges from'),generic.replace('Interest rates and program terms are subject to change without notice.',''),generic.replace('Personal loan :','Other loan :')]:
   self.assertIsNone(dated_loan_range(bad,'Personal Loan'))

 def test_price_identity_queries_survive_and_tracking_does_not(self):
  from worker.discovery.fpds_discovery.url_utils import normalize_source_url
  from worker.native_linked_card_pricing import detail_link
  from dataclasses import replace
  u='https://example.com/credit-cards/terms?FPID=offerA&product_code=CC&subproduct_code=ABC&vendor_code=tracking'
  normalized=normalize_source_url(u)
  self.assertIn('fpid=offerA',normalized);self.assertIn('product_code=CC',normalized);self.assertNotIn('vendor_code',normalized)
  self.assertNotEqual(normalized,normalize_source_url(u.replace('offerA','offerB')))
  a=parse_snapshot_bytes(body=raw('wf-card'),content_type='text/html')
  item=input_from_segments(bank='EX',url='https://example.com/card',product='credit-card',name='Example Card',segments=a.segments,country='US')
  link=replace(item.candidates[0],anchor_type='captured_disclosure_link',evidence_excerpt=u)
  self.assertIsNotNone(detail_link([link],normalized,'https://example.com/card'))
  self.assertIsNone(detail_link([link],normalized.replace('offerA','offerB'),'https://example.com/card'))

 def test_all_current_named_application_price_shapes(self):
  from bs4 import BeautifulSoup
  from worker.native_linked_application_pricing import application_pricing_records,application_fee_value,application_names_match
  rows=[r for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')) if r['name'].startswith('wf-terms-')]
  self.assertEqual(len(rows),8)
  for r in rows:
   html=gzip.decompress((FIX/r['fixture']).read_bytes())
   records=application_pricing_records(BeautifulSoup(html,'html.parser'))
   self.assertEqual(len(records),1,r['url'])
   q=records[0][2]
   expected=99 if '/onekeyplus?' in r['url'] else 95 if any(x in r['url'] for x in ['/choice-select/','/autograph-journey-visa/']) else 0
   self.assertEqual(application_fee_value(q),expected,r['url'])
   self.assertIn('Maximum APR',q);self.assertIn('qualify',q)
   self.assertFalse(application_pricing_records(BeautifulSoup(html.decode('utf8').replace('based on your creditworthiness','Missing terms'),'html.parser')))
  self.assertTrue(application_names_match('Example World Elite Mastercard','Example Credit Card'))
  self.assertFalse(application_names_match('Example Select Mastercard','Example Mastercard'))
  self.assertFalse(application_names_match('Example Plus Mastercard','Example Mastercard'))
 def test_actual_card_planner_selects_its_current_price_link(self):
  from api_service.collection_evidence_research import CapturedPage,EvidenceResearchPlanner
  from worker.discovery.fpds_discovery.registry import RegistrySource,SourceRegistry
  url='https://creditcards.wellsfargo.com/active-cash-credit-card'
  html=raw('wf-card').decode('utf8');a=parse_snapshot_bytes(body=html.encode(),content_type='text/html')
  item=input_from_segments(bank='WFBN',url=url,product='credit-card',name='Active Cash Credit Card',segments=a.segments,country='US')
  item.context.source_metadata['official_domain_allowlist']=['wellsfargo.com']
  source=RegistrySource('detail','P0',True,'html','detail','official fixture',url,url,(),'en','WFBN','US','credit-card',item.context.source_metadata)
  registry=SourceRegistry('fixture','WFBN','US','credit-card','en',('wellsfargo.com',),'detail',(source,))
  page=CapturedPage(item.context.source_document_id,item.context.snapshot_id,item.context.parsed_document_id,url,html,hashlib.sha256(html.encode()).hexdigest())
  plan=EvidenceResearchPlanner().plan(run_id='run',registry=registry,inputs=[item],captures=[page],attempted_urls={url},parent_counts={})
  self.assertTrue(any('/active-cash/terms?' in r['url'] and 'fpid=' in r['url'] for r in plan['sources']),plan)
  self.assertLessEqual(len(plan['sources']),2)
 def test_invalid_and_foreign_pricing_links_fail_closed(self):
  from worker.native_linked_card_pricing import normalized_link_url
  for u in ['javascript:alert(1)','https://user:pass@example.com/terms','https://example.com:99/terms','/relative-only']:
   self.assertEqual(normalized_link_url(u),'')

 def test_all_eight_current_card_details_pass_with_exact_linked_offer(self):
  from worker.discovery.fpds_discovery.url_utils import normalize_source_url
  rows=json.loads((FIX/'sources.json').read_text(encoding='utf8'))
  for row in [r for r in rows if r['name'].startswith('wf-detail-')]:
   detail_artifact=parse_snapshot_bytes(body=raw(row['name']),content_type='text/html')
   detail=input_from_segments(bank='WFBN',url=normalize_source_url(row['url']),product='credit-card',name='Metadata cannot supply identity',segments=detail_artifact.segments,country='US')
   detail.context.source_metadata['official_domain_allowlist']=['wellsfargo.com']
   links=[normalize_source_url(c.evidence_excerpt) for c in detail.candidates if c.anchor_type=='captured_disclosure_link']
   term_row=next(r for r in rows if r['name'].startswith('wf-terms-') and normalize_source_url(r['url']) in links)
   artifact=parse_snapshot_bytes(body=raw(term_row['name']),content_type='text/html')
   terms=input_from_segments(bank='WFBN',url=normalize_source_url(term_row['url']),product='credit-card',name='Pricing Information',segments=artifact.segments,country='US',role='supporting_html',ident='terms')
   record,routing,_=run_services([detail,terms]);p=record['candidate_payload']
   self.assertEqual(routing.validation_action,'auto_validated',(row['url'],p.get('_collection_accuracy')))
   self.assertNotIn('trademark',record['product_name']);self.assertNotIn('registered mark',record['product_name'])
   self.assertEqual(record['currency'],'USD')
   self.assertIn('How We Calculate Your Variable APR',p['purchase_interest_rate_summary'])
   self.assertNotIn('purchase_interest_rate',p)

 def test_foreign_transaction_label_is_not_a_currency_and_conflicts_still_block(self):
  from worker.pipeline.fpds_collection_accuracy import country_currency_fallback
  row={'product_type':'credit-card','product_name':'Example Card','country_code':'US','currency':'XXX'}
  q='Pricing Information\nNamed card: Example Card\nFees Annual Fee None Transaction Fees Foreign Currency Conversion/Foreign Transaction None Penalty Fees Late Payment Up to $40'
  evidence=lambda value:[{'evidence_excerpt':value}]
  self.assertEqual(country_currency_fallback(row,evidence(q)),'USD')
  for bad in [q+' Account currency: EUR',q+' denominated in euros',q+' multi-currency account',q.replace('Foreign Transaction None','Foreign Transaction EUR 5'),q.replace('Pricing Information\nNamed card: Example Card\n','')]:
   self.assertIsNone(country_currency_fallback(row,evidence(bad)),bad)
  self.assertIsNone(country_currency_fallback({**row,'country_code':'GB'},evidence(q)))

 def test_accessible_trademark_cleanup_never_drops_other_hidden_information(self):
  from bs4 import BeautifulSoup
  from worker.native_linked_application_pricing import remove_duplicate_trademark_labels
  soup=BeautifulSoup('<h1>Example<span class="visually-hidden">trademark</span><span aria-hidden="true">™</span> Card</h1><h2>Plan<span class="visually-hidden">Plus</span><span aria-hidden="true">™</span></h2>','html.parser')
  remove_duplicate_trademark_labels(soup)
  self.assertEqual(soup.h1.get_text(' ',strip=True),'Example ™ Card')
  self.assertIn('Plus',soup.h2.get_text())
