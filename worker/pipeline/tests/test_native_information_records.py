from pathlib import Path
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_collection_accuracy import quote_supports_value

FIX=Path(__file__).parent/'fixtures/native-information-records'

class NativeInformationRecordsTests(unittest.TestCase):
 def test_actual_pdf_information_box_retains_ordinary_and_default_rates(self):
  from worker.native_information_records import pdf_information_records
  records=pdf_information_records((FIX/'card-information-box.txt').read_text(),page_no=1)
  q=next(record for kind,owner,record in records if kind=='card_information_rate')
  self.assertIn('12 consecutive months',q)
  self.assertIn('25.99%',q)
  self.assertTrue(quote_supports_value('purchase_interest_rate',21.99,q))
  self.assertFalse(quote_supports_value('purchase_interest_rate',25.99,q))
  self.assertFalse(quote_supports_value('purchase_interest_rate',22.99,q))
 def test_actual_embedded_mortgage_grids_keep_own_terms_and_notes(self):
  a=parse_snapshot_bytes(body=(FIX/'mortgage-rates.html').read_bytes(),content_type='text/html')
  qs=[s for s in a.segments if s.anchor_type=='named_mortgage_rate_schedule']
  self.assertEqual(len(qs),2)
  one=next(s for s in qs if s.anchor_value=='Manulife One')
  self.assertIn('10-year closed',one.text)
  self.assertIn('APR (%)',one.text)
  self.assertIn('Fixed-rate sub-account interest is compounded semi-annually',one.text)
  self.assertNotIn('Interest rate for positive account balances',one.text)
  self.assertNotIn('Manulife Bank Select bank account',one.text)
 def test_actual_native_heading_normalizes_nonbreaking_space_for_identity(self):
  a=parse_snapshot_bytes(body=(FIX/'credit-card.html').read_bytes(),content_type='text/html')
  self.assertTrue(any(s.anchor_type=='document_heading' and s.text.replace('\xa0',' ')=='Manulife Bank Visa Infinite *' for s in a.segments))
 def test_actual_credit_limit_schedule_is_qualified_and_keeps_annual_note(self):
  a=parse_snapshot_bytes(body=(FIX/'line-of-credit.html').read_bytes(),content_type='text/html')
  q=next(s.text for s in a.segments if s.anchor_type=='credit_limit_rate_schedule')
  self.assertIn('ALOC+ Max',q);self.assertIn('Prime +1.50%',q)
  self.assertIn('All rates are annual rates',q)
  self.assertFalse(quote_supports_value('standard_rate',5.45,q))

 def test_information_box_rejects_truncated_default_or_duplicate_owner(self):
  from worker.native_information_records import pdf_information_records, information_card_rates
  raw=(FIX/'card-information-box.txt').read_text()
  q=next(q for k,o,q in pdf_information_records(raw,page_no=1) if k=='card_information_rate')
  self.assertIsNone(information_card_rates(q.split('The increased rates will remain')[0]))
  self.assertEqual(pdf_information_records(raw.replace('Interest-free', 'Unknown boundary'),page_no=1)[0][0], 'card_information_fee')
  self.assertEqual(pdf_information_records(raw+'\nAnother Card Information Box',page_no=1), [])

 def test_missing_or_duplicate_native_note_cannot_prove_mortgage_schedule(self):
  from bs4 import BeautifulSoup
  from worker.native_information_records import html_information_records
  soup=BeautifulSoup((FIX/'mortgage-rates.html').read_bytes(),'html.parser')
  note=soup.find(id='footnote1');self.assertIsNotNone(note)
  note.decompose()
  self.assertFalse(any(k=='named_mortgage_rate_schedule' for k,_,_ in html_information_records(soup)))

 def test_nested_navigation_is_not_denomination_but_actual_foreign_text_survives(self):
  html='<main><nav>US Dollar savings</nav><div role="navigation">EUR accounts</div><h1>Credit Line</h1><p>Annual interest rate 5%. USD borrowing is available.</p></main>'
  artifact=parse_snapshot_bytes(body=html.encode(),content_type='text/html')
  self.assertNotIn('US Dollar savings',artifact.full_text)
  self.assertNotIn('EUR accounts',artifact.full_text)
  self.assertIn('USD borrowing is available',artifact.full_text)

 def test_current_rates_link_survives_navigation_cap_without_main(self):
  from worker.discovery.fpds_discovery.discovery import extract_links
  html='<nav>'+''.join(f'<a href="/nav/{i}">Menu {i}</a>' for i in range(300))+'</nav><a href="/current-rates.html">Current rates</a>'
  links=extract_links(html,base_url='https://examplebank.com/card')
  self.assertLessEqual(len(links),256)
  self.assertTrue(any(l.normalized_url=='https://examplebank.com/current-rates.html' for l in links))

 def test_another_bank_information_box_passes_stored_artifact_and_origin_services(self):
  from types import SimpleNamespace
  from worker.native_information_records import pdf_information_records
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments, run_services
  name='Example Bank Visa Infinite *'
  html=f'<html><title>{name} | Example Bank</title><main><h1>{name}</h1><p>Credit card details.</p></main></html>'
  detail=input_from_segments(bank='EXAMPLE',url='https://examplebank.com/credit-cards/visa-infinite',product='credit-card',name=name,segments=parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments)
  raw=(FIX/'card-information-box.txt').read_text().replace('Manulife Bank','Example Bank')
  records=pdf_information_records(raw,page_no=1)
  companion=input_from_segments(bank='EXAMPLE',url='https://examplebank.com/infinite-rates.pdf',product='credit-card',name='Rates',role='linked_pdf',parent=detail.context.source_metadata['normalized_source_url'],ident='rates',segments=[SimpleNamespace(anchor_type=k,anchor_value=o,page_no=1,text=q) for k,o,q in records])
  row,validation,extraction=run_services([detail,companion])
  self.assertEqual(validation.validation_action,'auto_validated',row['candidate_payload']['_collection_accuracy'])
  p=row['candidate_payload'];self.assertEqual(p['purchase_interest_rate'],21.99);self.assertEqual(p['cash_advance_rate'],22.99)
  self.assertEqual(p['annual_fee'],139);self.assertIn('25.99%',p['purchase_interest_rate_summary'])
  from dataclasses import replace
  foreign=replace(companion,context=replace(companion.context,bank_code='OTHER'),candidates=[replace(c,bank_code='OTHER') for c in companion.candidates])
  _,validation,_=run_services([detail,foreign]);self.assertEqual(validation.validation_action,'excluded')

 def test_unnamed_shared_companion_fee_cannot_override_own_card_fee(self):
  from dataclasses import replace
  from worker.pipeline.tests.test_captured_fact_parity import CapturedFactParityTests
  from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
  ctx,base=CapturedFactParityTests().context()
  ctx=replace(ctx,source_metadata={**ctx.source_metadata,'product_type':'credit-card'})
  owned=replace(base,anchor_type='financial_declaration',evidence_excerpt='Annual fee\n$139')
  companion=replace(owned,evidence_chunk_id='other',source_document_id='other',source_snapshot_id='other',parsed_document_id='other',evidence_excerpt='Annual fee\n$0',retrieval_metadata={'captured_companion':True,'parent_detail_url':ctx.source_metadata['normalized_source_url'],'source_url':'https://www.cibc.com/current-rates.html'})
  rows=_append_captured_decision_facts(context=ctx,candidates=[owned,companion],fields=[],requested_fields=['annual_fee'])
  self.assertEqual([r.candidate_value for r in rows],['139.0'])

 def test_owned_explicit_collateral_proves_typed_flag_as_well_as_complete_sentence(self):
  from dataclasses import replace
  from worker.pipeline.tests.test_captured_fact_parity import CapturedFactParityTests
  from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts
  ctx,base=CapturedFactParityTests().context()
  ctx=replace(ctx,source_metadata={**ctx.source_metadata,'product_type':'line-of-credit'})
  sentence='Enjoy favorable interest rates by securing your line of credit with assets such as deposit accounts and GICs.'
  chunk=replace(base,anchor_type='section',evidence_excerpt=sentence)
  facts=_append_captured_decision_facts(context=ctx,candidates=[chunk],fields=[],requested_fields=['secured_flag','collateral_text'])
  self.assertEqual({f.field_name:f.candidate_value for f in facts},{'collateral_text':sentence,'secured_flag':True})
  bad=replace(chunk,evidence_excerpt='You may enjoy favorable interest rates by securing your line of credit with assets such as deposit accounts.')
  self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[bad],fields=[],requested_fields=['secured_flag','collateral_text']),[])

 def test_information_box_quote_cannot_drop_attached_default_condition(self):
  from worker.native_information_records import pdf_information_records
  from worker.pipeline.tests.test_collection_accuracy import candidate_fixture
  from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
  row,metadata,evidence=candidate_fixture()
  full=next(q for k,o,q in pdf_information_records((FIX/'card-information-box.txt').read_text(),page_no=1) if k=='card_information_rate')
  short=full.split('If you do not make')[0].strip()
  for name,value in [('purchase_interest_rate',21.99),('purchase_interest_rate_summary',short)]:
   row['candidate_payload'][name]=value
   row['field_mapping_metadata'][name]={**row['field_mapping_metadata']['standard_rate'],'normalized_value':value,'evidence_chunk_id':'information','official_evidence_quote':short}
  evidence.append({'evidence_chunk_id':'information','source_url':'https://bank.example/savings','evidence_excerpt':full,'anchor_type':'card_information_rate'})
  _,receipt=sanitize_candidate(row,source_metadata=metadata,evidence=evidence)
  for name in ['purchase_interest_rate','purchase_interest_rate_summary']:
   self.assertEqual(receipt['omitted_fields'][name],'native_rate_conditions_incomplete')
