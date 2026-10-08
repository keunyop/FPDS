"""Native disclosure parity using exact official captures and ordinary services."""
import hashlib,json,unittest
from pathlib import Path
from dataclasses import replace
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
FIX=Path(__file__).parent/'fixtures/native-disclosure-parity'
class NativeDisclosureParityTests(unittest.TestCase):
 def item(self,fixture,product,ident='detail'):
  receipt=next(r for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')) if r['fixture']==fixture)
  md=receipt['source_metadata'];artifact=parse_snapshot_bytes(body=(FIX/fixture).read_bytes(),content_type=receipt['content_type'])
  name=(md.get('discovery_metadata') or {}).get('primary_heading','')
  i=input_from_segments(bank='SIMPLII',url=receipt['url'],product=product,name=name,role=md['discovery_role'],ident=ident,segments=artifact.segments)
  chunks=_build_evidence_chunks(parsed_document_id=i.context.parsed_document_id,source_language='en',artifact=artifact,max_chars=900,overlap_chars=120)
  candidates=[EvidenceChunkCandidate(c.evidence_chunk_id,c.parsed_document_id,c.chunk_index,c.anchor_type,c.anchor_value,c.page_no,'en',c.evidence_excerpt,c.retrieval_metadata,i.context.source_document_id,i.context.snapshot_id,'SIMPLII','CA',i.context.source_type) for c in chunks]
  return replace(i,context=replace(i.context,source_metadata={**i.context.source_metadata,**md}),candidates=candidates)
 def test_exact_official_source_hashes(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):self.assertEqual(hashlib.sha256((FIX/r['fixture']).read_bytes()).hexdigest(),r['sha256'])
 def test_current_owned_single_row_annual_deposit_rate(self):
  row,v,_=run_services([self.item('savings.html.bin','savings')]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['standard_rate'],2.8);self.assertEqual(row['currency'],'USD');self.assertEqual(p['interest_payment_frequency'],'monthly');self.assertIn('daily closing balance',p['interest_calculation_method'])
 def test_display_fee_alias_retains_verified_monthly_fee_origin(self):
  for file,typ in [('savings.html.bin','savings'),('checking.html.bin','chequing')]:
   row,v,_=run_services([self.item(file,typ)]);mapping=row['field_mapping_metadata']
   self.assertEqual(mapping['public_display_fee']['evidence_chunk_id'],mapping['monthly_fee']['evidence_chunk_id'])
   self.assertEqual(mapping['public_display_fee']['official_evidence_quote'],mapping['monthly_fee']['official_evidence_quote'])
   self.assertEqual(mapping['public_display_fee']['normalized_value'],mapping['monthly_fee']['normalized_value'])
 def test_owned_ordinary_debit_purchase_bill_payment_withdrawal_allowance(self):
  row,v,e=run_services([self.item('checking.html.bin','chequing')]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertIs(p['unlimited_transactions_flag'],True);self.assertEqual(p['monthly_fee'],0)
 def test_owned_primary_and_additional_cardholder_fee_is_not_lost(self):
  row,v,e=run_services([self.item('card.html.bin','credit-card')]);self.assertEqual(row['candidate_payload'].get('annual_fee'),0)
 def test_named_annual_pdf_columns_and_complete_default_rules_survive_services(self):
  row,v,e=run_services([self.item('card.html.bin','credit-card'),self.item('card-summary.pdf.bin','credit-card','summary')]);p=row['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy']);self.assertEqual(p['purchase_interest_rate'],21.99);self.assertEqual(p['annual_fee'],0)
  self.assertIn('24.99%',p['purchase_interest_rate_summary']);self.assertIn('third statement period',p['purchase_interest_rate_summary'])


class DisclosureBoundaryTests(unittest.TestCase):
 def test_generic_owned_heading_allowances_and_card_fees(self):
  for bank in ['EXAMPLE','OTHER']:
   url='https://'+bank.lower()+'.ca/checking'
   name=bank+' Everyday Checking Account'
   html='<main><h1>'+name+'</h1><h3>No monthly fees</h3><h3>Enjoy unlimited debit purchases, bill payments and withdrawals.</h3></main>'
   detail=input_from_segments(bank=bank,url=url,product='chequing',name=name,segments=parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments)
   row,v,_=run_services([detail]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload'])
 def test_channel_conditional_and_recommendation_allowances_fail(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  from worker.native_owned_account_records import account_records
  from bs4 import BeautifulSoup
  for text in ['Unlimited ATM withdrawals','Unlimited debit purchases','Unlimited bill payments and withdrawals',
               'Unlimited debit purchases, bill payments and withdrawals if eligible',
               'No unlimited debit purchases, bill payments and withdrawals',
               'Unlimited debit purchases, bill payments and withdrawals. 10 transactions each month.']:
   self.assertFalse(quote_supports_value('unlimited_transactions_flag',True,text),text)
  records=account_records(BeautifulSoup('<main><h1>Example Account</h1><h3>Looking for unlimited debit purchases, bill payments and withdrawals?</h3></main>','html.parser'))
  self.assertFalse(records)
 def test_other_named_panels_cannot_donate_heading_allowances(self):
  from worker.native_owned_account_records import account_records
  from bs4 import BeautifulSoup
  html='<main><h1>Example Account</h1><section data-product-name="Premium Account"><h3>Unlimited debit purchases, bill payments and withdrawals.</h3></section></main>'
  self.assertFalse(account_records(BeautifulSoup(html,'html.parser')))
 def test_card_count_scope_does_not_waive_other_fee_conditions(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  good='Annual fee\n(for primary cardholder and up to 3 additional cards)\n$0'
  self.assertTrue(quote_supports_value('annual_fee',0,good))
  for bad in [good+'\nFirst year only',good+'\nIf eligible',good+'\nMaintain a minimum balance of $5000',good.replace('primary cardholder','eligible students')]:
   self.assertFalse(quote_supports_value('annual_fee',0,bad),bad)
 def test_generic_pdf_owner_and_complete_default_conditions(self):
  from pypdf import PdfReader
  from worker.native_information_records import pdf_summary_records,summary_card_rates
  from io import BytesIO
  layout=PdfReader(BytesIO((FIX/'card-summary.pdf.bin').read_bytes())).pages[0].extract_text(extraction_mode='layout')
  good=pdf_summary_records(layout);self.assertEqual(len(good),1)
  for brand in ['Example Financial','Otherbank Retail']:
   changed=layout.replace('Simplii Financial',brand)
   records=pdf_summary_records(changed);self.assertEqual(len(records),1)
   self.assertIn(brand,records[0][1]);self.assertEqual(tuple(map(float,summary_card_rates(records[0][2]))),(21.99,22.99))
  for changed in [layout.replace('Annual','Monthly'),layout.replace('Purchases                         Cash Advances','Cash Rates                        Cash Advances'),
                  layout.replace('21.99%','99.99% 21.99%'),layout.replace('third statement period','later'),
                  layout.replace('excluding the annual fee','including the annual fee'),layout.replace('Card Product','Products')]:
   self.assertFalse(pdf_summary_records(changed))
 def test_missing_default_and_extra_qualification_block_summary_values(self):
  from worker.native_information_records import pdf_summary_records,summary_card_rates
  from pypdf import PdfReader
  from io import BytesIO
  quote=pdf_summary_records(PdfReader(BytesIO((FIX/'card-summary.pdf.bin').read_bytes())).pages[0].extract_text(extraction_mode='layout'))[0][2]
  for bad in [quote.split('Required Payment means:')[0],quote+'\nOnly for the first year',quote.replace('at least 12 months','for a while')]:
   self.assertIsNone(summary_card_rates(bad))
 def test_unrelated_or_wrong_country_companion_cannot_supply_rate(self):
  x=NativeDisclosureParityTests();detail=x.item('card.html.bin','credit-card');pdf=x.item('card-summary.pdf.bin','credit-card','summary')
  for ctx in [replace(pdf.context,bank_code='OTHER'),replace(pdf.context,country_code='US')]:
   row,v,_=run_services([detail,replace(pdf,context=ctx)])
   self.assertEqual(v.validation_action,'excluded');self.assertNotIn('purchase_interest_rate',row['candidate_payload'])

 def test_generic_single_row_deposit_tables_require_owned_complete_annual_scope(self):
  from bs4 import BeautifulSoup
  from worker.native_named_rate_records import compact_annual_balance_records,balance_rate_value
  notes='Interest is calculated on the daily closing balance and is paid into your account monthly. Rates subject to change.'
  for brand in ['Example','Otherbank']:
   html='<main><h1>'+brand+' Savings Account</h1><h2>Interest rates</h2><section><table><tr><td>Annual rate</td><td>1.25%</td></tr></table><p>'+notes+'</p></section></main>'
   records=compact_annual_balance_records(BeautifulSoup(html,'html.parser'));self.assertEqual(len(records),1);self.assertEqual(float(balance_rate_value(records[0][2])),1.25)
   for bad in [html.replace('Annual rate','Monthly rate'),html.replace(brand+' Savings Account','Discontinued '+brand+' Savings Account'),html.replace('1.25%','RDS%rate'),html.replace(notes,notes+' Only if eligible.'),
               html.replace('<section>','<section data-product-name="Other Savings Account">'),html.replace('<td>1.25%</td>','<td>1.25%<a href="#missing">1</a></td>'),
               html.replace('</tr>','</tr><tr><td>Annual rate</td><td>2.5%</td></tr>'),html.replace('<h2>Interest rates</h2>','<h2>Premium Savings Account</h2>')]:
    self.assertFalse(compact_annual_balance_records(BeautifulSoup(bad,'html.parser')),bad)
