"""Exact official captures: owned annual declarations and complete terms."""
import gzip,hashlib,json,unittest
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/annual-disclosure-parity'
SOURCES=json.loads((FIX/'sources.json').read_text(encoding='utf8'))

@lru_cache(maxsize=32)
def captured(slug, product=None):
 r=next(r for r in SOURCES if r['url'].rsplit('/',1)[1]==slug)
 md=r['source_metadata'];product=product or md['product_type'];name=(md.get('discovery_metadata') or {}).get('primary_heading','')
 artifact=parse_snapshot_bytes(body=gzip.decompress((FIX/r['fixture']).read_bytes()),content_type=r['content_type'])
 item=input_from_segments(bank=r['bank_code'],url=r['url'],product=product,name=name,role=md['discovery_role'],ident=slug,segments=[])
 chunks=_build_evidence_chunks(parsed_document_id=item.context.parsed_document_id,source_language=r['source_language'],artifact=artifact,max_chars=900,overlap_chars=120)
 candidates=[EvidenceChunkCandidate(c.evidence_chunk_id,c.parsed_document_id,c.chunk_index,c.anchor_type,c.anchor_value,c.page_no,r['source_language'],c.evidence_excerpt,c.retrieval_metadata,item.context.source_document_id,item.context.snapshot_id,r['bank_code'],r['country_code'],item.context.source_type) for c in chunks]
 return replace(item,context=replace(item.context,source_metadata={**item.context.source_metadata,**md}),candidates=candidates)

def product_inputs(slug):
 i=captured(slug);typ=i.context.source_metadata['product_type'];companions={'savings':['savings-account-rates'],'gic':['gic-rates','account-terms'],'credit-card':['credit-card-cardholder-agreement']}.get(typ,[])
 return [i,*[captured(c,typ) for c in companions]]

class AnnualDisclosureParityTests(unittest.TestCase):
 def test_source_hashes(self):
  for r in SOURCES:self.assertEqual(hashlib.sha256(gzip.decompress((FIX/r['fixture']).read_bytes())).hexdigest(),r['sha256'])
 def test_owned_daily_transaction_allowance(self):
  r,v,_=run_services(product_inputs('chequing-account'));p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(r['currency'],'CAD');self.assertIs(p['unlimited_transactions_flag'],True);self.assertEqual(p['monthly_fee'],0)
 def test_named_annual_savings_and_original_currency(self):
  for slug,rate,currency in [('savings-account',.30,'CAD'),('rsp',.30,'CAD'),('rif',.35,'CAD'),('us-dollar-savings-account',.10,'USD'),('childrens-savings-account',.40,'CAD')]:
   with self.subTest(slug=slug):
    r,v,_=run_services(product_inputs(slug));p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['standard_rate'],rate);self.assertEqual(r['currency'],currency);self.assertEqual(p['monthly_fee'],0);self.assertEqual(p['interest_payment_frequency'],'monthly');self.assertIn('calculated daily',p['interest_calculation_method'])
 def test_named_card_standard_rates_retain_default_and_reset(self):
  for slug,fee in [('money-back-credit-card',0),('world-credit-card',0),('world-elite-mastercard',120)]:
   with self.subTest(slug=slug):
    r,v,_=run_services(product_inputs(slug));p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['purchase_interest_rate'],20.95);self.assertEqual(p['annual_fee'],fee)
    for required in ['25.95%','27.95%','12 consecutive months']:self.assertIn(required,p['purchase_interest_rate_summary'])
 def test_gic_calendar_schedule_survives_but_ambiguous_access_stays_excluded(self):
  # A discretionary exception and cancellation window do not prove an
  # unconditional redeemable/non-redeemable boolean. Preserve the verified
  # schedule, but never widen the existing access-essential contract.
  for slug,currency,rate in [('rsp-gic','CAD',3.60),('rif-gic','CAD',3.60),('tax-free-gic','CAD',3.60),('us-gic','USD',4.25)]:
   with self.subTest(slug=slug):
    r,v,_=run_services(product_inputs(slug));p=r['candidate_payload'];self.assertEqual(v.validation_action,'excluded');self.assertIsNone(v.review_task_record)
    self.assertEqual(r['currency'],currency);self.assertEqual(len(p['term_rate_table']),9)
    self.assertEqual(next(x['rate'] for x in p['term_rate_table'] if x['term_label']=='1 Year'),rate)
    for row in p['term_rate_table']:
     self.assertNotIn('term_length_days',row);self.assertIn('annual interest rates',row['notes'])
    self.assertIn('redeemable_flag',p['_collection_accuracy']['missing_fields']);self.assertNotIn('redeemable_flag',p);self.assertNotIn('non_redeemable_flag',p)

class ReferencedDisclosureBoundaries(unittest.TestCase):
 def records(self,html):
  from bs4 import BeautifulSoup
  from worker.native_referenced_disclosures import referenced_annual_records
  return referenced_annual_records(BeautifulSoup(html,'html.parser'))
 def test_different_banks_and_unique_literal_annual_notes(self):
  for bank in ['Northbank','Another Bank']:
   html='<main><h1>'+bank+' Savings Account</h1><div><p>1.25%<sup>†</sup></p><p>Interest rate</p></div><p><sup>†</sup> Savings Account interest rates expressed on this website are annual interest rates. Interest is calculated daily and paid monthly.</p></main>'
   records=[r for r in self.records(html) if r[0]=="linked_rate_record"];self.assertEqual(len(records),1)
   from worker.pipeline.fpds_collection_accuracy import quote_supports_value
   self.assertTrue(quote_supports_value('standard_rate',1.25,records[0][2]))
   for bad in [html.replace('annual interest rates','monthly interest rates'),html.replace('Savings Account interest','Mortgage interest'),html.replace('1.25%','RDS%rate'),html.replace('<div>','<div data-product-name="Premium Savings Account">'),html.replace('</main>','<p><sup>†</sup> This different disclosure is another possible note.</p></main>'),html.replace('1.25%','1.25% 2.50%')]:self.assertFalse(self.records(bad),bad)
   qualified=html.replace('paid monthly.','paid monthly. Only if you qualify for the promotion.')
   self.assertFalse(quote_supports_value('standard_rate',1.25,self.records(qualified)[0][2]))
   self.assertFalse(any(r[0]=='named_product_interest_terms' for r in self.records(qualified)))
 def test_named_application_disclosure_rejects_missing_reset_or_unknown_conditions(self):
  from worker.native_application_disclosures import application_card_rates
  records=[c for c in captured('credit-card-cardholder-agreement').candidates if c.anchor_type=='named_card_regular_rates']
  self.assertEqual(len(records),3)
  quote=records[0].evidence_excerpt
  for brand in ['Example Bank','Another Financial']:
   renamed=quote.replace('Tangerine',brand);self.assertEqual(tuple(map(float,application_card_rates(renamed))),(20.95,22.95))
  for bad in [quote.replace('Annual Interest Rate','Monthly Interest Rate'),quote.replace('12 consecutive months','some time'),quote.split('Minimum Payment\n')[0],quote+'\nOnly if eligible.',quote.replace('Purchases: 20.95%','Purchases: 20.95% to 22.95%'),quote.replace('Standard Rates','Promotional Rates')]:self.assertIsNone(application_card_rates(bad))
 def test_wrong_bank_country_language_snapshot_and_named_owner_cannot_donate_card_rates(self):
  from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence,collect_captured_fields
  detail,companion=product_inputs('money-back-credit-card')
  def purchase(other):
   bound=_bind_grounding_evidence([detail,other])[0]
   return [f for f in collect_captured_fields(extraction_input=bound,field_names=['product_name','annual_fee','purchase_interest_rate'],run_id='boundary')[1] if f.field_name=='purchase_interest_rate' and f.field_metadata.get('official_grounding_contract_version')]
  self.assertTrue(purchase(companion))
  for ctx in [replace(companion.context,bank_code='OTHER'),replace(companion.context,country_code='US'),replace(companion.context,source_language='fr'),replace(companion.context,snapshot_id='stale')]:self.assertFalse(purchase(replace(companion,context=ctx)))
  changed=[replace(c,anchor_value='Unrelated Premium Card',evidence_excerpt=c.evidence_excerpt.replace('Money-Back Credit Card','Unrelated Premium Card')) if c.anchor_type=='named_card_regular_rates' else c for c in companion.candidates]
  self.assertFalse(purchase(replace(companion,candidates=changed)))
 def test_calculator_label_cannot_suppress_owned_account_fee(self):
  from bs4 import BeautifulSoup
  from worker.pipeline.fpds_parse_chunk.parser import _labelled_disclosure_sections
  for bank in ['Example','Otherbank']:
   html='<main><h1>'+bank+' Checking Account</h1><p>No monthly fees.</p><h2>Estimate your savings</h2><div><label>Monthly fee</label><input type="range" value="13"><p>$13 at your current bank</p></div></main>'
   self.assertFalse(_labelled_disclosure_sections(BeautifulSoup(html,'html.parser')))
 def test_literal_daily_allowance_is_not_a_channel_or_conditional_allowance(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  self.assertTrue(quote_supports_value('unlimited_transactions_flag',True,'Unlimited number of daily transactions'))
  for bad in ['Unlimited number of daily transactions only at ATMs','Unlimited number of daily transactions if eligible','No unlimited number of daily transactions','Unlimited number of daily transactions. 10 transactions each month.']:
   self.assertFalse(quote_supports_value('unlimited_transactions_flag',True,bad),bad)

class AdjacentAllowanceConditions(unittest.TestCase):
 def test_following_condition_cannot_be_separated_from_unlimited_heading(self):
  from bs4 import BeautifulSoup
  from worker.native_owned_account_records import account_records
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  html='<main><h1>Northbank Chequing Account</h1><section><h3>Unlimited number of daily transactions</h3><p>Only if you maintain a qualifying balance.</p></section></main>'
  rows=account_records(BeautifulSoup(html,'html.parser'))
  self.assertFalse(any(quote_supports_value('unlimited_transactions_flag',True,r[2]) for r in rows))
