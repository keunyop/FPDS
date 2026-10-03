from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.service import _extract_official_fields_with_ai
from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationEvidenceLink
from worker.pipeline.fpds_normalization.service import _accuracy_evidence
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate

FIXTURE = Path(__file__).parent/'fixtures/golden/bmo_scoped_evidence_origin.json'

class CapturedGroundingTests(unittest.TestCase):
    def context_and_chunk(self, bank='TD', country='CA', product='savings', url='https://www.td.com/ca/savings'):
        ctx=ExtractionDocumentContext('parsed','doc','snap',bank,country,'html','en',{
            'product_type':product,'discovery_role':'detail','normalized_source_url':url,
            'official_domain_allowlist':['td.com'] if bank=='TD' else ['examplebank.com']})
        chunk=EvidenceChunkCandidate('chunk','parsed',0,'section','Everyday Savings',None,'en',
            'Everyday Savings Account. No monthly fee. Currency CAD. Standard interest rate 2.50% per annum.',
            {'source_url':url},'doc','snap',bank,country,'html')
        return ctx,chunk

    def assert_capture_proves_sources_without_duplicate_search(self, *, bank='TD', country='CA', url='https://www.td.com/ca/savings'):
        ctx,chunk=self.context_and_chunk(bank=bank, country=country, url=url)
        currency = 'CAD' if country == 'CA' else 'USD'
        chunk = replace(chunk, evidence_excerpt=chunk.evidence_excerpt.replace('CAD', currency))
        values=[('currency',currency,'Currency '+currency),('product_name','Everyday Savings Account','Everyday Savings Account'),
                ('monthly_fee',0,'No monthly fee.'),
                ('standard_rate',2.5,'Standard interest rate 2.50% per annum')]
        response={'summary':'Captured official facts','fields':[{
            'field_name':name,'status':'match','has_verified_value':True,'verified_value_json':json.dumps(value),
            'evidence_chunk_id':'chunk','evidence_quote':quote,'confidence':.99,'rationale':'Exact capture',
            'sources':[{'url':ctx.source_metadata['normalized_source_url'],'title':'Everyday Savings'}]
        } for name,value,quote in values]}
        with patch('worker.pipeline.fpds_extraction.service.invoke_openai_json_schema',return_value=(response,{'prompt_tokens':10,'completion_tokens':10,'web_search_sources':[]})) as model:
            fields,notes,usage=_extract_official_fields_with_ai(context=ctx,candidates=[chunk],requested_fields=[x[0] for x in values],collected_fields=[])
        self.assertEqual({f.field_name for f in fields},{x[0] for x in values})
        self.assertFalse(model.call_args.kwargs.get('require_web_search',False))
        self.assertFalse(model.call_args.kwargs.get('web_search_allowed_domains'))
        self.assertTrue(all(f.field_metadata['official_grounding_method']=='captured_official_evidence' for f in fields))
        model.assert_called_once()
        record={'product_name':'Everyday Savings Account','country_code':country,'bank_code':bank,'product_type':'savings','currency':currency,
                'candidate_payload':{f.field_name:(float(f.candidate_value) if f.value_type=='decimal' else f.candidate_value) for f in fields},
                'field_mapping_metadata':{f.field_name:{'normalized_value':(float(f.candidate_value) if f.value_type=='decimal' else f.candidate_value),
                    **f.field_metadata,'official_evidence_quote':f.field_metadata['evidence_quote'],'evidence_chunk_id':f.evidence_chunk_id} for f in fields}}
        result,receipt=sanitize_candidate(record,source_metadata=ctx.source_metadata,
            evidence=[{'evidence_chunk_id':'chunk','evidence_excerpt':chunk.evidence_excerpt,'source_url':ctx.source_metadata['normalized_source_url']}])
        self.assertTrue(receipt['accepted'],receipt)

    def test_capture_proves_sources_without_duplicate_search(self):
        for bank, country, url in [('TD', 'CA', 'https://www.td.com/ca/savings'),
                                   ('EXAMPLE', 'US', 'https://examplebank.com/us/savings')]:
            with self.subTest(bank=bank, country=country):
                self.assert_capture_proves_sources_without_duplicate_search(bank=bank, country=country, url=url)

    def test_non_product_identity_skips_provider(self):
        ctx, chunk = self.context_and_chunk(product='mortgage')
        ctx = replace(ctx, source_metadata={**ctx.source_metadata,
            'discovery_metadata': {'primary_heading': 'Mortgage Protection Insurance'}})
        with patch('worker.pipeline.fpds_extraction.service.invoke_openai_json_schema') as model:
            fields, notes, usage = _extract_official_fields_with_ai(
                context=ctx, candidates=[chunk], requested_fields=['product_name'], collected_fields=[])
        self.assertEqual(fields, [])
        self.assertIsNone(usage)
        self.assertIn('non_product_service_flow', ' '.join(notes))
        model.assert_not_called()

    def test_external_search_cannot_substitute_unprovided_source_or_chunk(self):
        ctx,chunk=self.context_and_chunk()
        for changes in [{'evidence_chunk_id':'invented'},{'evidence_quote':'invented product name'},
                        {'sources':[{'url':'https://evil.test/ca/savings','title':'fake'}]},
                        {'sources':[{'url':'https://www.td.com/us/other-product','title':'neighbor'}]},
                        {'sources':[{'url':'https://www.td.com/ca/savings?documentId=other','title':'other document'}]}]:
            response={'summary':'','fields':[{'field_name':'product_name','status':'match','has_verified_value':True,
                'verified_value_json':'"Everyday Savings Account"','evidence_chunk_id':'chunk',
                'evidence_quote':'Everyday Savings Account','confidence':.9,'rationale':'',
                'sources':[{'url':ctx.source_metadata['normalized_source_url'],'title':'Everyday'}],**changes}]}
            with self.subTest(changes=changes),patch('worker.pipeline.fpds_extraction.service.invoke_openai_json_schema',return_value=(response,{'web_search_sources':changes.get('sources',[])})):
                fields,_,_=_extract_official_fields_with_ai(context=ctx,candidates=[chunk],requested_fields=['product_name'],collected_fields=[])
                self.assertEqual(fields,[])

    def test_foreign_document_candidates_are_rejected_before_model(self):
        ctx,chunk=self.context_and_chunk()
        for changes in [{'bank_code':'OTHER'},{'country_code':'US'},{'source_snapshot_id':'old'},{'parsed_document_id':'old'},
                        {'retrieval_metadata':{'source_url':'https://evil.test/not-official'}}]:
            with self.subTest(changes=changes),patch('worker.pipeline.fpds_extraction.service.invoke_openai_json_schema') as model:
                fields,_,_=_extract_official_fields_with_ai(context=ctx,candidates=[replace(chunk,**changes)],requested_fields=['product_name'],collected_fields=[])
                self.assertEqual(fields,[]);model.assert_not_called()

class CapturedOriginTests(unittest.TestCase):
    def setUp(self):
        self.saved=json.loads(FIXTURE.read_text(encoding='utf8'));e=self.saved['extraction'];raw=self.saved['raw_chunk'];source=self.saved['source']
        self.item=NormalizationInput(source_id=e['source_id'],source_document_id=e['source_document_id'],snapshot_id=e['snapshot_id'],
            parsed_document_id=e['parsed_document_id'],extraction_model_execution_id=e['model_execution_id'],extracted_storage_key=e['extracted_storage_key'],
            metadata_storage_key=e['metadata_storage_key'],bank_code='BMO',country_code='CA',source_type='html',source_language='en',
            source_metadata=source['source_metadata'],schema_context={},extracted_fields=[],runtime_notes=[],
            normalized_source_url=source['normalized_source_url'],evidence_origins_resolved=True,evidence_links=[NormalizationEvidenceLink(**x) for x in e['evidence_links']],
            evidence_origins={raw['evidence_chunk_id']:{'run_id':'run','bank_code':'BMO','country_code':'CA','source_document_id':e['source_document_id'],
                'snapshot_id':e['snapshot_id'],'evidence_chunk_id':raw['evidence_chunk_id'],'evidence_excerpt':raw['evidence_excerpt'],
                'source_url':source['normalized_source_url']}})

    def test_saved_bmo_normalization_preserves_identity_and_excludes_calculator_rate(self):
        from tempfile import TemporaryDirectory
        from worker.pipeline.fpds_normalization.models import NormalizationExtractedField
        from worker.pipeline.fpds_normalization.service import NormalizationService
        from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig, build_object_store
        item = replace(self.item, extracted_fields=[NormalizationExtractedField(**field)
            for field in self.saved['extraction']['extracted_fields']],
            schema_context={'product_family': 'lending', 'product_type': 'personal-loan', 'country_code': 'CA'})
        with TemporaryDirectory() as tmp, patch('worker.pipeline.fpds_normalization.service.llm_provider_configured', return_value=False):
            cfg = NormalizationStorageConfig(driver='filesystem', env_prefix='test', normalization_object_prefix='normalized',
                retention_class='hot', filesystem_root=tmp)
            result = NormalizationService(storage_config=cfg, object_store=build_object_store(cfg)).normalize_inputs(
                run_id='run', inputs=[item]).source_results[0]
        self.assertIsNone(result.error_summary)
        receipt = result.normalized_candidate_record['candidate_payload']['_collection_accuracy']
        self.assertIn('product_name', receipt['verified_fields'], receipt)
        self.assertNotIn('product_identity_unverified', receipt['reasons'], receipt)
        self.assertFalse(receipt['accepted'])
        self.assertNotIn('interest_rate', result.normalized_candidate_record['candidate_payload'])
        self.assertIn('interest_rate_summary', receipt['omitted_fields'])

    def test_resolved_missing_origin_cannot_fall_back_to_own_url(self):
        item = replace(self.item, evidence_origins={})
        self.assertTrue(item.evidence_origins_resolved)
        self.assertTrue(all(row['source_url'] is None for row in _accuracy_evidence(item=item, run_id='run')))

    def test_actual_scoped_links_do_not_overwrite_full_current_capture(self):
        raw=self.saved['raw_chunk'];links=[x for x in self.item.evidence_links if x.evidence_chunk_id==raw['evidence_chunk_id']]
        self.assertGreater(len({x.evidence_text_excerpt for x in links}),1)
        output=_accuracy_evidence(item=self.item,run_id='run')
        evidence=next(x for x in output if x['evidence_chunk_id']==raw['evidence_chunk_id'])
        self.assertEqual(evidence['source_url'],self.item.normalized_source_url)
        self.assertEqual(evidence['evidence_excerpt'],raw['evidence_excerpt'])
        self.assertEqual(sum(x['evidence_chunk_id']==raw['evidence_chunk_id'] for x in output),1)
        self.assertIn('Enter an interest rate.',evidence['evidence_excerpt'])

    def test_scoped_excerpt_cannot_hide_qualified_zero(self):
        raw=self.saved['raw_chunk'];link=next(x for x in self.item.evidence_links if x.evidence_chunk_id==raw['evidence_chunk_id'])
        full='Example Savings. Monthly fee CAD $0 when you maintain a CAD $5,000 balance.'
        origin={**self.item.evidence_origins[raw['evidence_chunk_id']],'evidence_excerpt':full}
        item=replace(self.item,evidence_links=[replace(link,evidence_text_excerpt='Monthly fee CAD $0')],evidence_origins={raw['evidence_chunk_id']:origin})
        result=_accuracy_evidence(item=item,run_id='run')[0]
        self.assertEqual(result['evidence_excerpt'],full)
        record={'country_code':'CA','bank_code':'BMO','product_type':'savings','product_name':'Example Savings','currency':'CAD',
            'candidate_payload':{'monthly_fee':0},'field_mapping_metadata':{'monthly_fee':{'normalized_value':0,'evidence_chunk_id':raw['evidence_chunk_id'],
                'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match',
                'official_web_sources':[{'url':origin['source_url']}],'official_evidence_quote':'Monthly fee CAD $0'}}}
        sanitized,receipt=sanitize_candidate(record,source_metadata={'discovery_role':'detail','official_domain_allowlist':['bmo.com']},evidence=[result])
        self.assertNotIn('monthly_fee',sanitized['candidate_payload'])

    def test_wrong_run_or_mutated_excerpt_does_not_resolve(self):
        raw=self.saved['raw_chunk'];link=next(x for x in self.item.evidence_links if x.evidence_chunk_id==raw['evidence_chunk_id'])
        for changes in [{'run_id':'old'},{'bank_code':'OTHER'},{'country_code':'US'},{'snapshot_id':'old'},{'source_document_id':'other'}]:
            item=replace(self.item,evidence_links=[link],evidence_origins={raw['evidence_chunk_id']:{**self.item.evidence_origins[raw['evidence_chunk_id']],**changes}})
            self.assertIsNone(_accuracy_evidence(item=item,run_id='run')[0]['source_url'])
        item=replace(self.item,evidence_links=[replace(link,evidence_text_excerpt='fabricated evidence')])
        self.assertIsNone(_accuracy_evidence(item=item,run_id='run')[0]['source_url'])

if __name__=='__main__':unittest.main()
