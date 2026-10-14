import gzip,json,unittest
from dataclasses import replace
from worker.pipeline.tests.test_current_account_features import FIX,MANIFEST,ordinary
from worker.pipeline.tests.test_admin_collection_parity import run_services
class CurrentLendingFaqTests(unittest.TestCase):
 def inputs(self,bank='CHINABANK',replace_text=None):
  result=[]
  for suffix,ident,role in [('loans-homeplus','detail','detail'),('loans-faqs-homeplus-application','faq','supporting_html')]:
   row=next(x for x in MANIFEST if x['url'].endswith('/'+suffix))
   raw=gzip.decompress((FIX/row['file']).read_bytes())
   url=row['url']
   if replace_text:
    raw=replace_text(raw.decode('utf8')).encode();url=url.replace('chinabank.ph','examplebank.com')
   item=ordinary(row,bank=bank,product='mortgage',raw=raw,url=url)
   # Keep actual independent source/snapshot/parse origins; no supplied parent.
   ctx=replace(item.context,source_id=ident,source_document_id='doc-'+ident,snapshot_id='snapshot-'+ident,parsed_document_id='parsed-'+ident,source_metadata={**item.context.source_metadata,'discovery_role':role,'product_family':'lending'})
   candidates=[replace(c,evidence_chunk_id=ident+'-'+str(i),source_document_id=ctx.source_document_id,source_snapshot_id=ctx.snapshot_id,parsed_document_id=ctx.parsed_document_id) for i,c in enumerate(item.candidates)]
   result.append(replace(item,context=ctx,candidates=candidates))
  return result
 def test_current_named_faq_keeps_annual_fixing_and_repayment_distinct(self):
  r,v,_=run_services(self.inputs());p=r['candidate_payload']
  self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
  self.assertEqual(r['product_name'],'Chinabank HomePlus');self.assertEqual(r['currency'],'PHP')
  for literal in ['7.50% p.a.','8.00% p.a.','repricing','1 to 3 years','4 to 5 years']:self.assertIn(literal,p['interest_rate_summary'])
  self.assertIn('fixed',p['rate_type'])
  self.assertIn('Acquisition of House and Lot',p['term_length_text']);self.assertIn('Up to 20 years',p['term_length_text'])
  self.assertIn('approval of management',p['term_length_text'])
  self.assertNotIn('mortgage_rate',p);self.assertNotIn('term_length_days',p)

 def test_same_contract_works_for_other_issuer_and_rejects_missing_proof(self):
  mutate=lambda t:t.replace('Chinabank','ExampleBank').replace('China Bank','ExampleBank').replace('chinabank.ph','examplebank.com')
  inputs=self.inputs(bank='EXAMPLE',replace_text=mutate)
  r,v,_=run_services(inputs);self.assertEqual(v.validation_action,'auto_validated')
  for index,item in enumerate(inputs):
   changed=replace(item,context=replace(item.context,country_code='US'))
   altered=[changed if i==index else x for i,x in enumerate(inputs)]
   _,v,_=run_services(altered);self.assertEqual(v.validation_action,'excluded')
  for old,new in [('subject to review and repricing after the agreed-upon fixing period expires.','unknown repricing'),('7.50% p.a.','7.50% per month'),('loans-homeplus','loans-homeplus-premium'),('HomePlus Loan','Other Loan')]:
   changed=self.inputs(bank='EXAMPLE',replace_text=lambda t:mutate(t).replace(old,new))
   _,v,_=run_services(changed);self.assertEqual(v.validation_action,'excluded',old)
 def test_faq_cannot_donate_a_scalar_or_shortened_conditions(self):
  from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
  r,v,_=run_services(self.inputs());self.assertEqual(v.validation_action,'auto_validated')
  from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence
  chunks=_bind_grounding_evidence(self.inputs())[0].grounding_candidates
  evidence=[{'evidence_chunk_id':c.evidence_chunk_id,'evidence_excerpt':c.evidence_excerpt,'anchor_type':c.anchor_type,'anchor_value':c.anchor_value,'source_document_id':c.source_document_id,'snapshot_id':c.source_snapshot_id,'parsed_document_id':c.parsed_document_id,'bank_code':c.bank_code,'country_code':c.country_code,'source_url':c.retrieval_metadata.get('source_url')} for c in chunks]
  record={**r,'candidate_payload':dict(r['candidate_payload']),'field_mapping_metadata':dict(r['field_mapping_metadata'])}
  original=record['field_mapping_metadata']['interest_rate_summary']
  record['candidate_payload']['interest_rate_summary']='Interest rate per annum 7.50% p.a.'
  record['field_mapping_metadata']['interest_rate_summary']={**original,'official_evidence_quote':record['candidate_payload']['interest_rate_summary']}
  _,receipt=sanitize_candidate(record,source_metadata=self.inputs()[0].context.source_metadata,evidence=evidence)
  self.assertFalse(receipt['accepted'])

 def test_actual_two_wave_faq_path_keeps_the_two_url_cap(self):
  from dataclasses import replace
  from hashlib import sha256
  from worker.pipeline.tests.test_current_lending_faq import CurrentLendingFaqTests
  from worker.pipeline.tests.test_current_account_features import ordinary
  from worker.discovery.fpds_discovery.registry import RegistrySource,SourceRegistry
  from api_service.collection_evidence_research import EvidenceResearchPlanner,CapturedPage
  detail,faq=CurrentLendingFaqTests().inputs()
  row=next(x for x in json.loads((FIX/'sources.json').read_text()) if x['url'].endswith('/loans-faqs'))
  hub=ordinary(row,bank='CHINABANK',product='mortgage')
  ctx=replace(hub.context,source_id='hub',source_document_id='doc-hub',snapshot_id='snapshot-hub',parsed_document_id='parsed-hub',source_metadata={**hub.context.source_metadata,'discovery_role':'supporting_html','discovery_metadata':{'parent_detail_url':detail.context.source_metadata['normalized_source_url']}})
  hub=replace(hub,context=ctx,candidates=[replace(c,evidence_chunk_id='hub-'+str(i),source_document_id=ctx.source_document_id,source_snapshot_id=ctx.snapshot_id,parsed_document_id=ctx.parsed_document_id) for i,c in enumerate(hub.candidates)])
  def registry(items):
   sources=tuple(RegistrySource(i.context.source_id,'P0',True,'html',i.context.source_metadata['discovery_role'],'fixture',i.context.source_metadata['normalized_source_url'],i.context.source_metadata['normalized_source_url'],(),'en','CHINABANK','PH','mortgage',i.context.source_metadata) for i in items)
   return SourceRegistry('fixture','CHINABANK','PH','mortgage','en',('chinabank.ph',),detail.context.source_id,sources)
  def capture(item):
   url=item.context.source_metadata['normalized_source_url'];row=next(x for x in json.loads((FIX/'sources.json').read_text()) if x['url']==url);raw=gzip.decompress((FIX/row['file']).read_bytes())
   return CapturedPage(item.context.source_document_id,item.context.snapshot_id,item.context.parsed_document_id,url,raw.decode(),sha256(raw).hexdigest())
  planner=EvidenceResearchPlanner();parent=detail.context.source_metadata['normalized_source_url']
  first=planner.plan(run_id='run',registry=registry([detail]),inputs=[detail],captures=[capture(detail)],attempted_urls={parent},parent_counts={})
  self.assertEqual([x['url'] for x in first['sources']],[row['url']])
  self.assertTrue(first['diagnostics'][0]['faq_followup_slot_reserved'])
  second=planner.plan(run_id='run',registry=registry([detail,hub]),inputs=[detail,hub],captures=[capture(detail),capture(hub)],attempted_urls={parent,row['url']},parent_counts={parent:1})
  self.assertEqual([x['url'] for x in second['sources']],[faq.context.source_metadata['normalized_source_url']])
  final=planner.plan(run_id='run',registry=registry([detail,hub,faq]),inputs=[detail,hub,faq],captures=[capture(x) for x in [detail,hub,faq]],attempted_urls={parent,row['url'],faq.context.source_metadata['normalized_source_url']},parent_counts={parent:2})
  self.assertEqual(final['sources'],[])
  self.assertEqual(final['diagnostics'][0]['stop_reason'],'no_essential_gap')
