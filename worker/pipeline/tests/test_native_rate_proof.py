from pathlib import Path
import unittest
from worker.discovery.fpds_discovery.discovery import extract_links
from worker.discovery.fpds_discovery.fetch import FetchedResponse, NonRetryableFetchError
from worker.discovery.fpds_snapshot.capture import CaptureSource, _validate_fetched_payload
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.fpds_rate_safety import contains_explicit_rate_percentage

FIX=Path(__file__).parent/'fixtures/native-rate-tables'

class NativeRateProofTests(unittest.TestCase):
 def parse(self,html):return parse_snapshot_bytes(body=html.encode(),content_type='text/html')
 def test_current_gic_schedule_retains_header_numbers_and_complete_legal(self):
  a=self.parse((FIX/'fixed-gic.html').read_text(encoding='utf8'))
  records=[x for x in a.segments if x.anchor_type=='native_rate_table']
  self.assertTrue(records)
  q=records[0].text
  self.assertIn('Annual % rate',q);self.assertIn('outside of Quebec',q)
  self.assertTrue(quote_supports_value('term_rate_table',[{'term_label':'1 year','rate':3.5}],q))
  self.assertFalse(quote_supports_value('term_rate_table',[{'term_label':'1 year','rate':4.1}],q))
  self.assertFalse(quote_supports_value('term_rate_table',[{'term_label':'1 year','rate':3.5,'term_length_days':365}],q))
 def test_independent_bank_explicit_header_cell_binding(self):
  html='<main><h1>Fixed-rate Certificate of Deposit</h1><section><h2>Current terms</h2><table><thead><tr><th>Term</th><th>Annual rate (%)</th></tr></thead><tbody><tr><td>12 months</td><td>3.25</td></tr><tr><td>24 months</td><td>3.5</td></tr></tbody></table><p>Non-redeemable. USD accounts only.</p></section></main>'
  records=[x for x in self.parse(html).segments if x.anchor_type=='native_rate_table']
  self.assertTrue(records)
  self.assertTrue(quote_supports_value('term_rate_table',[{'term_label':'12 months','rate':3.25}],records[0].text))
  self.assertIn('USD accounts only',records[0].text)
 def test_current_mortgage_sections_do_not_import_other_scopes(self):
  records=[x for x in self.parse((FIX/'mortgage-rates.html').read_text(encoding='utf8')).segments if x.anchor_type=='native_rate_table']
  fixed=next(x for x in records if x.anchor_value=='Fixed-rate mortgage.')
  self.assertTrue(contains_explicit_rate_percentage(fixed.text));self.assertIn('5.640',fixed.text)
  self.assertIn('Promotional rate - 5 years',fixed.text)
  self.assertNotIn('4.69%',fixed.text);self.assertNotIn('Prime rate -0.25%',fixed.text)
 def test_real_gic_access_keeps_legal_and_optional_facts(self):
  records=[x for x in self.parse((FIX/'fixed-gic.html').read_text(encoding='utf8')).segments if x.anchor_type=='native_product_terms']
  self.assertTrue(records);q=records[0].text
  self.assertTrue(quote_supports_value('non_redeemable_flag',True,q))
  self.assertIn('$500',q);self.assertIn('outside of Quebec',q)
  self.assertTrue(quote_supports_value('minimum_deposit',500,q))
  self.assertFalse(quote_supports_value('minimum_deposit',500,'Minimum monthly balance: $500.'))
 def test_numbered_legal_notes_are_unique_and_attached_by_literal_reference(self):
  from bs4 import BeautifulSoup
  from worker.native_rate_tables import _local_notes
  html='<main><section><a href="#legal-1">1</a></section><div><button>Legal</button><article><ol><li>The annual rate is 4.45%.</li></ol></article></div></main>'
  soup=BeautifulSoup(html,'html.parser')
  self.assertEqual(_local_notes(soup,soup.section),['The annual rate is 4.45%.'])
  duplicate=BeautifulSoup(html.replace('</article>','<ol><li>Other conditions.</li></ol></article>'),'html.parser')
  self.assertIsNone(_local_notes(duplicate,duplicate.section))
 def test_current_variable_row_keeps_own_apr_note_and_excludes_conflicting_spread(self):
  records=[x for x in self.parse((FIX/'mortgage-rates.html').read_text(encoding='utf8')).segments if x.anchor_type=='native_rate_table' and x.anchor_value=='Variable-rate mortgage.']
  self.assertTrue(records);q=records[0].text
  self.assertIn('4.450',q);self.assertIn('3 years',q);self.assertIn('25 years',q)
  self.assertNotIn('4.200',q);self.assertNotIn('Prime rate -0.25%',q)
  self.assertTrue(contains_explicit_rate_percentage(q))
 def test_native_schedule_is_atomic_and_rejects_ambiguous_units_or_duplicates(self):
  from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
  from worker.native_rate_tables import rate_schedules
  a=self.parse((FIX/'fixed-gic.html').read_text(encoding='utf8'))
  chunks=_build_evidence_chunks(parsed_document_id='p',source_language='en',artifact=a,max_chars=180,overlap_chars=20)
  q=next(c.evidence_excerpt for c in chunks if c.anchor_type=='native_rate_table')
  self.assertIn('outside of Quebec',q);self.assertGreater(len(q),180)
  self.assertFalse(rate_schedules('Term\nAnnual rate\n1 year\n3.5',annual_only=True))
  self.assertFalse(rate_schedules('Term\nAnnual rate (%)\n1 year\n3.5\nBonus\n1.0',annual_only=True))
  self.assertFalse(rate_schedules('Term\nAnnual rate (%)\n1 year\n3.5\n1 year\n4.0',annual_only=True))
  self.assertFalse(quote_supports_value('term_rate_table',[{'term_label':'1 year','rate':3.5}],q.replace('1 year\nAnnual % rate\n3.50','1 year\nAnnual % rate\n4.50')))
 def test_explicit_access_no_cannot_hide_exception_or_conflict(self):
  for q in ['Cashable: No. Except after 90 days, when it may be cashed.', 'Cashable: No. Cashable: Yes.', 'Cashable: No. Redeemable after 90 days.', 'Cashable: No until 90 days.', 'GICs are not cashable until 90 days.']:
   self.assertFalse(quote_supports_value('non_redeemable_flag',True,q))
 def test_saved_soft404_cannot_reenter_parse(self):
  with self.assertRaisesRegex(ValueError,'soft_404'):
   self.parse('<title>Page introuvable</title><main><h1>Unavailable</h1></main>')
 def test_us_certificate_ordinary_extraction_normalization_preserves_native_rows(self):
  from dataclasses import asdict
  from unittest.mock import patch
  from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext,ExtractionInput
  from worker.pipeline.fpds_extraction.service import collect_captured_fields
  from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
  from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
  from worker.pipeline.fpds_normalization.models import NormalizationInput,NormalizationExtractedField
  from worker.pipeline.fpds_normalization.service import _normalize_candidate
  html='<main><h1>Fixed-rate Certificate of Deposit</h1><section><h2>Current terms</h2><table><thead><tr><th>Term</th><th>Annual rate (%)</th></tr></thead><tbody><tr><td>12 months</td><td>3.25</td></tr><tr><td>24 months</td><td>3.5</td></tr></tbody></table></section><section><h2>Features</h2><p>Cashable: No. Non-redeemable. Available terms range from 12 months to 24 months. USD accounts only.</p></section></main>'
  a=self.parse(html);chunks=[]
  for c in _build_evidence_chunks(parsed_document_id='p',source_language='en',artifact=a,max_chars=200,overlap_chars=20):
   r=c.to_record();chunks.append(EvidenceChunkCandidate(**{k:r[k] for k in ['evidence_chunk_id','parsed_document_id','chunk_index','anchor_type','anchor_value','page_no','source_language','retrieval_metadata']},evidence_excerpt=c.evidence_excerpt,source_document_id='d',source_snapshot_id='s',bank_code='EXAMPLE',country_code='US',source_type='html'))
  md={'product_type':'gic','product_family':'deposit','discovery_role':'detail','normalized_source_url':'https://bank.example/fixed-certificate','official_domain_allowlist':['bank.example'],'expected_fields':['product_name','currency','term_rate_table','term_length_text','redeemable_flag','non_redeemable_flag','eligibility_text'],'discovery_metadata':{'primary_heading':'Fixed-rate Certificate of Deposit','page_title':'Fixed-rate Certificate of Deposit','product_identity_match':True}}
  ctx=ExtractionDocumentContext(parsed_document_id='p',source_document_id='d',snapshot_id='s',bank_code='EXAMPLE',country_code='US',source_type='html',source_language='en',source_metadata=md)
  _,facts,_,_=collect_captured_fields(extraction_input=ExtractionInput(context=ctx,candidates=chunks),field_names=md['expected_fields'],run_id='run')
  table=next(f for f in facts if f.field_name=='term_rate_table');self.assertTrue(all('term_length_days' not in r for r in table.candidate_value))
  origins={c.evidence_chunk_id:{'run_id':'run','bank_code':'EXAMPLE','country_code':'US','source_document_id':'d','snapshot_id':'s','parsed_document_id':'p','evidence_excerpt':c.evidence_excerpt,'source_url':md['normalized_source_url']} for c in chunks}
  item=NormalizationInput(source_id='src',source_document_id='d',snapshot_id='s',parsed_document_id='p',extraction_model_execution_id='x',extracted_storage_key='x',metadata_storage_key=None,bank_code='EXAMPLE',country_code='US',source_type='html',source_language='en',source_metadata=md,schema_context={'product_type':'gic','country_code':'US'},extracted_fields=[NormalizationExtractedField(**asdict(f)) for f in facts],evidence_links=[],runtime_notes=[],normalized_source_url=md['normalized_source_url'],evidence_origins_resolved=True,evidence_origins=origins)
  with patch('worker.pipeline.fpds_normalization.service.llm_provider_configured',return_value=False):
   record,_,_,_=_normalize_candidate(run_id='run',candidate_id='candidate',normalization_model_execution_id='n',item=item)
  self.assertEqual(record['candidate_payload']['term_rate_table'],table.candidate_value)
  self.assertEqual(record['currency'],'USD')
  from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
  _,receipt=sanitize_candidate(record,source_metadata=md,evidence=[{'evidence_chunk_id':c.evidence_chunk_id,'evidence_excerpt':c.evidence_excerpt,'source_url':md['normalized_source_url'],'anchor_type':c.anchor_type,'anchor_value':c.anchor_value} for c in chunks])
  self.assertIn('term_rate_table',receipt['verified_fields'],receipt)
  import copy
  for shortened in (None,'12 months'):
   altered=copy.deepcopy(record)
   for row in altered['candidate_payload']['term_rate_table']:
    if shortened is None:row.pop('notes',None)
    else:row['notes']=shortened
   altered['field_mapping_metadata']['term_rate_table']['normalized_value']=copy.deepcopy(altered['candidate_payload']['term_rate_table'])
   with self.subTest(shortened=shortened):
    _,invalid=sanitize_candidate(altered,source_metadata=md,evidence=[{'evidence_chunk_id':c.evidence_chunk_id,'evidence_excerpt':c.evidence_excerpt,'source_url':md['normalized_source_url'],'anchor_type':c.anchor_type,'anchor_value':c.anchor_value} for c in chunks])
    self.assertEqual(invalid['omitted_fields'].get('term_rate_table'),'native_rate_conditions_incomplete')
 def test_current_targets_pass_actual_saved_json_origin_and_routing_services(self):
  from dataclasses import replace
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  rate_segments=self.parse((FIX/'mortgage-rates.html').read_text(encoding='utf8')).segments
  for product,file,name,url in [('gic','fixed-gic','FIXED-RATE GIC','https://www.laurentianbank.ca/en/personal/investments/gics/fixed-rate'),('mortgage','fixed-mortgage','FIXED-RATE MORTGAGE','https://www.laurentianbank.ca/en/personal/mortgages/fixed-rate'),('mortgage','variable-mortgage','VARIABLE-RATE MORTGAGE','https://www.laurentianbank.ca/en/personal/mortgages/variable-rate')]:
   with self.subTest(target=file):
    detail=input_from_segments(bank='LAURENTIAN',url=url,product=product,name=name,segments=self.parse((FIX/(file+'.html')).read_text(encoding='utf8')).segments)
    detail=replace(detail,context=replace(detail.context,source_metadata={**detail.context.source_metadata,'product_family':'lending' if product=='mortgage' else 'deposit'}))
    inputs=[detail]
    if product=='mortgage':inputs.append(input_from_segments(bank='LAURENTIAN',url='https://www.laurentianbank.ca/en/personal/rates/mortgages',product=product,name='Mortgage and equity lines of credit rates.',segments=rate_segments,role='supporting_html',parent=url,ident='rates'))
    rec,val,_=run_services(inputs)
    self.assertEqual(val.validation_action,'auto_validated',rec['candidate_payload']['_collection_accuracy'])
    self.assertIsNone(val.review_task_record)
    if product=='gic':
     self.assertEqual(rec['candidate_payload']['minimum_deposit'],500)
     self.assertTrue(rec['candidate_payload']['non_redeemable_flag'])
     self.assertTrue(all('term_length_days' not in r for r in rec['candidate_payload']['term_rate_table']))
    if file=='variable-mortgage':
     self.assertEqual(rec['candidate_payload']['term_length_text'],'3 years')
     self.assertNotIn('4.200',rec['candidate_payload']['interest_rate_summary'])
 def test_numeric_balance_is_not_a_rate_table(self):
  self.assertFalse(contains_explicit_rate_percentage('Balance\nAnnual fee ($)\n12 months\n3.25'))
 def test_structured_site_routes_follow_demonstrated_public_root_convention(self):
  html='<a href="/en/personal/rates/lending">Rates</a><script type="application/json">{"links":[{"url":"en/personal/rates/lending"},{"url":"en/personal/rates/investments"}]}</script>'
  urls={x.normalized_url for x in extract_links(html,base_url='https://bank.example/en/personal/gics/fixed')}
  self.assertIn('https://bank.example/en/personal/rates/investments',urls)
  self.assertFalse(any('/gics/en/' in x for x in urls))
 def test_genuine_relative_routes_and_absent_root_convention_are_preserved(self):
  html='<a href="rates.html">Rates</a><script type="application/json">{"url":"en/personal/rates/lending"}</script>'
  urls={x.normalized_url for x in extract_links(html,base_url='https://bank.example/products/fixed')}
  self.assertIn('https://bank.example/products/rates.html',urls)
  self.assertIn('https://bank.example/products/en/personal/rates/lending',urls)
 def test_soft404_is_terminal_but_body_mentions_are_not(self):
  source=CaptureSource('s','d','https://bank.example/rates','https://bank.example/rates','html','en','B','CA','high',False,{})
  def fetched(body):return FetchedResponse(body.encode(),'https://bank.example/rates','text/html',200,{},'2026-10-05T00:00:00Z',0)
  for text in ['<title>Page introuvable | Banque</title><main><h1>Unavailable</h1></main>','<main><h1>Page not found</h1></main>','<main><h1>\u30da\u30fc\u30b8\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093</h1></main>']:
   with self.subTest(text=text),self.assertRaises(NonRetryableFetchError):_validate_fetched_payload(source=source,fetched=fetched(text))
  _validate_fetched_payload(source=source,fetched=fetched('<title>Everyday account</title><main><h1>Everyday account</h1><p>Our old page not found message has changed. Annual interest rate 2.5%.</p></main>'))

if __name__=='__main__':unittest.main()
