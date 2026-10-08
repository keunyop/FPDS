"""Current owned rows, annual disclosure and unchanged automatic gates."""
import gzip,hashlib,json,unittest
from pathlib import Path
from dataclasses import replace
from functools import lru_cache
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/named-annual-records'
SOURCES=json.loads((FIX/'sources.json').read_text(encoding='utf8'))
@lru_cache(maxsize=16)
def captured(slug):
 r=next(r for r in SOURCES if r['slug']==slug);md=r['source_metadata'];a=parse_snapshot_bytes(body=gzip.decompress((FIX/r['fixture']).read_bytes()),content_type='text/html')
 item=input_from_segments(bank=r['bank_code'],url=r['url'],product=md['product_type'],name=(md.get('discovery_metadata') or {}).get('primary_heading',''),role=md['discovery_role'],ident=slug,segments=[])
 chunks=_build_evidence_chunks(parsed_document_id=item.context.parsed_document_id,source_language='en',artifact=a,max_chars=900,overlap_chars=120)
 candidates=[EvidenceChunkCandidate(c.evidence_chunk_id,c.parsed_document_id,c.chunk_index,c.anchor_type,c.anchor_value,c.page_no,'en',c.evidence_excerpt,c.retrieval_metadata,item.context.source_document_id,item.context.snapshot_id,r['bank_code'],'CA','html') for c in chunks]
 return replace(item,context=replace(item.context,source_metadata={**item.context.source_metadata,**md}),candidates=candidates)
class NamedAnnualRecordsTests(unittest.TestCase):
 def test_original_full_capture_hashes(self):
  for r in SOURCES:self.assertEqual(hashlib.sha256(gzip.decompress((FIX/r['fixture']).read_bytes())).hexdigest(),r['sha256'])
 def test_current_named_savings_row_survives_actual_artifact_and_origin_loader(self):
  r,v,e=run_services([captured('savings'),captured('savings-rates')]);p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['standard_rate'],.60);self.assertEqual(p['monthly_fee'],0);self.assertEqual(r['currency'],'CAD');self.assertEqual(p['interest_payment_frequency'],'monthly');self.assertIn('paid monthly',p['interest_calculation_method'])
 def test_target_configuration_does_not_discard_proven_same_record_optional_facts(self):
  i=captured('savings');md={**i.context.source_metadata,'collection_field_policy':{'CA':{'required_fields':[],'optional_fields':[]}}}
  r,v,_=run_services([replace(i,context=replace(i.context,source_metadata=md)),captured('savings-rates')]);p=r['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated');self.assertEqual(p['interest_payment_frequency'],'monthly');self.assertIn('paid monthly',p['interest_calculation_method'])
 def test_dated_named_rows_keep_annual_units_conditions_and_product_boundaries(self):
  from bs4 import BeautifulSoup
  from worker.native_named_rate_records import dated_account_rate_records,balance_rate_value
  for bank in ['North Bank','Other Bank']:
   html='<main><h1>Account rates</h1><table><tr><th>Accounts</th><th>Rates as of 2026-10-08</th></tr><tr><td>'+bank+' Savings (all balances)</td><td>1.25 %</td></tr><tr><td>'+bank+' Premium Savings (all balances)</td><td>2.50 %</td></tr></table><p>Interest is calculated on the closing daily balance in an account and paid monthly. The interest is an annual interest rate. Interest is earned in the currency of the account.</p><p>Rates are subject to change without notice.</p></main>'
   records=dated_account_rate_records(BeautifulSoup(html,'html.parser'));self.assertEqual(len(records),2);self.assertEqual([float(balance_rate_value(r[2])) for r in records],[1.25,2.50]);self.assertEqual(records[0][1],bank+' Savings')
   for bad in [html.replace('annual interest rate','monthly interest rate'),html.replace('1.25 %','1.25').replace('2.50 %','2.50'),html.replace('(all balances)','(balances above $5000)'),html.replace('Accounts</th>','Mortgages</th>'),html.replace('without notice.','without notice. Only if you qualify.'),html.replace('1.25 %','RDS%rate').replace('2.50 %','RDS%rate'),html.replace('</main>','<p>Interest is an annual interest rate, with a promotional bonus.</p></main>'),html.replace('<p>Interest is calculated','<p data-account-name="Different Savings Account">Interest is calculated'),html.replace('The interest is an annual interest rate.','The interest is an annual interest rate.<a href="#absent"></a>')]:self.assertFalse(dated_account_rate_records(BeautifulSoup(bad,'html.parser')),bad)

class IndependentlyProvenIdentityTests(unittest.TestCase):
 def test_discovery_false_does_not_veto_current_native_identity(self):
  i=captured('savings');self.assertIs(i.context.source_metadata['discovery_metadata']['product_identity_match'],False)
  r,v,_=run_services([i,captured('savings-rates')]);self.assertEqual(v.validation_action,'auto_validated',r['candidate_payload']['_collection_accuracy'])
  for changed in [replace(i.context,snapshot_id='different'),replace(i.context,bank_code='OTHER'),replace(i.context,source_language='fr')]:
   r,v,_=run_services([replace(i,context=changed),captured('savings-rates')]);self.assertEqual(v.validation_action,'excluded')

class CardAnnualLabelTests(unittest.TestCase):
 def test_owned_colon_purchase_labels_and_complete_annual_disclosure(self):
  for slug in ['rewards-card','cashback-card']:
   r,v,e=run_services([captured(slug)]);p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['purchase_interest_rate'],21.99);self.assertEqual(p['cash_advance_rate'],22.99);self.assertEqual(p['annual_fee'],0)

class NativeLabelBoundaries(unittest.TestCase):
 def test_colon_rate_labels_preserve_actual_annual_notes_and_ownership(self):
  from bs4 import BeautifulSoup
  from worker.pipeline.fpds_parse_chunk.parser import _labelled_disclosure_sections
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  for bank in ['North Bank', 'Other Financial']:
   name=bank+' Rewards Card'
   html='<main><h1>'+name+'</h1><ul><li><span>Interest: Purchases</span><span>18.25%</span></li><li><span>Interest: Cash Advances</span><span>22.50%</span></li></ul><p>Annual interest rates, fees and features are current as of October 1, 2026, unless otherwise indicated and subject to change.</p></main>'
   records=_labelled_disclosure_sections(BeautifulSoup(html,'html.parser'));self.assertEqual(len(records),2);self.assertTrue(quote_supports_value('purchase_interest_rate',18.25,records[0].text));self.assertIn('October 1, 2026',records[0].text)
   for bad in [html.replace('Annual interest rates','Monthly interest rates'),html.replace('<p>Annual interest rates','<p data-product-name="Different Card">Annual interest rates'),html.replace('unless otherwise indicated and subject to change.</p>','unless otherwise indicated and subject to change.<a href="#absent"></a></p>'),html.replace('<ul>','<ul data-product-name="Premium Rewards Card">'),html.replace('18.25%','RDS%rate'),html.replace('<li><span>Interest: Purchases</span>','<li><span>Interest: Purchases</span><p>Only if eligible.</p>')]:
    rows=_labelled_disclosure_sections(BeautifulSoup(bad,'html.parser'));self.assertFalse(any(quote_supports_value('purchase_interest_rate',18.25,r.text) and 'Annual interest rates,' in r.text for r in rows),bad)
 def test_regular_owner_whitespace_does_not_merge_plus_variants(self):
  from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence,collect_captured_fields
  i=captured('cashback-card');b=_bind_grounding_evidence([i])[0]
  fields=collect_captured_fields(extraction_input=b,field_names=['product_name','purchase_interest_rate'],run_id='run')[1]
  self.assertTrue(any(f.field_name=='purchase_interest_rate' and f.field_metadata.get('official_grounding_contract_version') for f in fields))
  other='Unrelated Cash Back Plus Card'
  changed=replace(i,candidates=[replace(c,anchor_value=other,evidence_excerpt=c.evidence_excerpt.replace(c.anchor_value,other)) if c.anchor_type=='labelled_financial_record' else c for c in i.candidates if c.anchor_type in {'document_title','document_heading','labelled_financial_record'}])
  b=_bind_grounding_evidence([changed])[0];fields=collect_captured_fields(extraction_input=b,field_names=['product_name','purchase_interest_rate'],run_id='run')[1]
  self.assertFalse(any(f.field_name=='purchase_interest_rate' and f.field_metadata.get('official_grounding_contract_version') for f in fields))

class ExplicitUsdAnnualBasisTests(unittest.TestCase):
 def test_same_annual_disclosure_without_optional_comma_preserves_usd(self):
  r,v,_=run_services([captured('usd-card')]);p=r['candidate_payload'];self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(r['currency'],'USD');self.assertEqual(p['annual_fee'],39);self.assertEqual(p['purchase_interest_rate'],21.99)

class ActualMissingDisclosureTests(unittest.TestCase):
 def test_missing_required_modal_is_acquired_once_but_never_assumed(self):
  from api_service.collection_evidence_research import _has_required_dynamic_lead
  row=next(r for r in SOURCES if r['slug']=='checking');html=gzip.decompress((FIX/row['fixture']).read_bytes()).decode('utf8')
  self.assertTrue(_has_required_dynamic_lead(html,['unlimited_transactions_flag']))
  r,v,_=run_services([captured('checking')]);self.assertEqual(v.validation_action,'excluded');self.assertIn('unlimited_transactions_flag',r['candidate_payload']['_collection_accuracy']['missing_fields']);self.assertNotIn('unlimited_transactions_flag',r['candidate_payload'])

class PaymentFrequencyUnitBoundaries(unittest.TestCase):
 def test_annual_rate_unit_is_not_a_payment_option(self):
  from worker.pipeline.fpds_normalization.service import _looks_like_wrong_frequency_context as wrong
  for bank in ['North Bank','Other Financial']:
   for field in ['interest_payment_frequency','compounding_frequency','payout_option']:
    self.assertFalse(wrong(field_name=field,value='monthly',context=bank+' Savings. Interest is calculated daily and paid monthly. The interest is an annual interest rate.'))
    self.assertTrue(wrong(field_name=field,value='monthly',context=bank+' offers monthly or annual interest payments.'))
    self.assertTrue(wrong(field_name=field,value='monthly',context=bank+' offers monthly interest or annual interest.'))
    self.assertFalse(wrong(field_name=field,value='monthly',context=bank+' interest is paid monthly. Annual interest rates apply.'))
    self.assertTrue(wrong(field_name=field,value='monthly',context=bank+' offers monthly or annually.'))
    self.assertTrue(wrong(field_name=field,value='monthly',context=bank+' loan repayment payment frequency is monthly.'))
