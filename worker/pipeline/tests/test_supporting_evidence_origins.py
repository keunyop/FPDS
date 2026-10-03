from __future__ import annotations
from dataclasses import replace
from tempfile import TemporaryDirectory
import unittest
from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
from worker.pipeline.fpds_normalization.service import NormalizationService
from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig, build_object_store
from worker.pipeline.fpds_field_contract import canonical_value_type

DETAIL='https://bank.example/accounts/package'
TERMS='https://bank.example/terms.pdf'

def fixture():
    specs=[('product_name','Example Package','Example Package','detail'),
           ('monthly_fee',10.0,'Monthly account fee $10','detail'),
           ('unlimited_transactions_flag',True,'Unlimited debit transactions.','detail'),
           ('currency','CAD','All dollar amounts are in Canadian dollars unless otherwise noted.','terms')]
    fields=[];links=[]
    for name,value,quote,doc in specs:
        fields.append(NormalizationExtractedField(name,value,canonical_value_type(name),1.0,'openai_official_grounding',doc,'snap-'+doc,name,quote,'section',None,None,0,
            {'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match','official_web_sources':[{'url':TERMS if doc=='terms' else DETAIL}],'evidence_quote':quote}))
        links.append(NormalizationEvidenceLink(name,str(value),name,quote,doc,'snap-'+doc,1.0,'extract','section',None,None,0))
    # Foreign companion-account text prevents an unsupported CAD default.
    links.append(NormalizationEvidenceLink('currency_context','','companion','Separate US dollar account benefit.','detail','snap-detail',1.0,'extract','section',None,None,1))
    item=NormalizationInput('source','detail','snap-detail','parsed-detail','extract','input',None,'BANK','CA','html','en',
        {'product_type':'chequing','discovery_role':'detail','official_domain_allowlist':['bank.example']},
        {'product_type':'chequing','product_family':'deposit','country_code':'CA'},fields,links,[],normalized_source_url=DETAIL)
    origin={'evidence_chunk_id':'currency','source_document_id':'terms','snapshot_id':'snap-terms','evidence_excerpt':specs[-1][2],
        'source_url':TERMS,'bank_code':'BANK','country_code':'CA','run_id':'run-current'}
    item=replace(item,evidence_origins={'currency':origin})
    return item,origin

class SupportingEvidenceOriginTests(unittest.TestCase):
    def normalize(self,item):
        with TemporaryDirectory() as tmp:
            cfg=NormalizationStorageConfig(driver='filesystem',env_prefix='test',normalization_object_prefix='normalized',retention_class='hot',filesystem_root=tmp)
            result=NormalizationService(storage_config=cfg,object_store=build_object_store(cfg)).normalize_inputs(run_id='run-current',inputs=[item]).source_results[0]
            self.assertIsNone(result.error_summary)
            return result

    def test_linked_current_terms_prove_currency_without_a_default(self):
        item,_=fixture();result=self.normalize(item)
        receipt=result.normalized_candidate_record['candidate_payload']['_collection_accuracy']
        self.assertTrue(receipt['accepted'],receipt)
        self.assertEqual(receipt['currency_basis'],'official_evidence')
        currency=next(link for link in result.field_evidence_link_records if link['field_name']=='currency')
        self.assertEqual(currency['source_document_id'],'terms')
        self.assertEqual(currency['evidence_chunk_id'],'currency')

    def test_missing_origin_does_not_trust_model_sources(self):
        item,_=fixture();item=replace(item,evidence_origins={})
        receipt=self.normalize(item).normalized_candidate_record['candidate_payload']['_collection_accuracy']
        self.assertFalse(receipt['accepted'])
        self.assertIn('product_currency_unverified',receipt['reasons'])

    def test_wrong_document_snapshot_run_bank_country_or_excerpt_is_excluded(self):
        for key,bad in [('source_document_id','other'),('snapshot_id','old-snapshot'),('run_id','old-run'),('bank_code','OTHER'),('country_code','US'),('evidence_excerpt','Different captured text.'),('source_url','https://unapproved.example/terms.pdf')]:
            with self.subTest(key=key):
                item,origin=fixture();item=replace(item,evidence_origins={'currency':{**origin,key:bad}})
                self.assertFalse(self.normalize(item).normalized_candidate_record['candidate_payload']['_collection_accuracy']['accepted'])

    def test_model_consulted_url_must_match_captured_origin(self):
        item,_=fixture();fields=[replace(f,field_metadata={**f.field_metadata,'official_web_sources':[{'url':DETAIL}]}) if f.field_name=='currency' else f for f in item.extracted_fields]
        item=replace(item,extracted_fields=fields)
        self.assertFalse(self.normalize(item).normalized_candidate_record['candidate_payload']['_collection_accuracy']['accepted'])

    def test_repository_replaces_untrusted_origins_and_loads_only_referenced_chunks(self):
        import json
        from unittest.mock import patch
        from worker.pipeline.fpds_normalization.persistence import PsqlNormalizationRepository, NormalizationDatabaseConfig
        item,origin=fixture()
        repo=PsqlNormalizationRepository(NormalizationDatabaseConfig('postgres://unused','public'))
        repo._resolved_schema='public'
        origins = [origin, *[
            {'evidence_chunk_id': link.evidence_chunk_id, 'source_document_id': link.source_document_id,
             'snapshot_id': link.source_snapshot_id, 'evidence_excerpt': link.evidence_text_excerpt,
             'source_url': DETAIL, 'bank_code': 'BANK', 'country_code': 'CA', 'run_id': 'run-current'}
            for link in item.evidence_links if link.evidence_chunk_id != 'currency']]
        with patch.object(repo,'_execute',return_value=json.dumps(origins)) as query:
            resolved=repo.resolve_evidence_origins(run_id='run-current',inputs=[replace(item,evidence_origins={'invented':{'source_url':DETAIL}})])[0]
        self.assertEqual(resolved.evidence_origins, {row['evidence_chunk_id']: row for row in origins})
        self.assertTrue(resolved.evidence_origins_resolved)
        self.assertTrue(self.normalize(resolved).normalized_candidate_record['candidate_payload']['_collection_accuracy']['accepted'])
        sql=query.call_args.args[0]
        self.assertIn("rsi.selected_snapshot_id = ss.snapshot_id",sql)
        self.assertIn("rsi.stage_metadata ->> 'parsed_document_id' = pd.parsed_document_id",sql)
        self.assertIn("rsi.error_count = 0",sql)
        self.assertEqual(query.call_args.kwargs['variables']['run_id'],'run-current')
        self.assertEqual(set(json.loads(query.call_args.kwargs['variables']['chunk_ids_json'])),{link.evidence_chunk_id for link in item.evidence_links})
        with patch.object(repo,'_execute',return_value='[]'):
            missing=repo.resolve_evidence_origins(run_id='run-current',inputs=[item])[0]
        self.assertEqual(missing.evidence_origins,{})
        self.assertFalse(self.normalize(missing).normalized_candidate_record['candidate_payload']['_collection_accuracy']['accepted'])

    def test_artifact_cannot_supply_an_origin(self):
        from dataclasses import asdict
        from worker.pipeline.fpds_normalization.__main__ import _build_normalization_input
        from worker.pipeline.fpds_normalization.models import NormalizationArtifactLookup
        item,origin=fixture()
        lookup=NormalizationArtifactLookup('detail','snap-detail','parsed-detail','extract','input',None,'BANK','CA','html','en',item.source_metadata,DETAIL)
        artifact={'extracted_fields':[asdict(f) for f in item.extracted_fields],
                  'evidence_links':[asdict(link) for link in item.evidence_links],
                  'schema_context':item.schema_context,'evidence_origins':{'currency':origin}}
        loaded=_build_normalization_input(source_id='source',lookup=lookup,artifact=artifact)
        self.assertEqual(loaded.evidence_origins,{})
        self.assertFalse(self.normalize(loaded).normalized_candidate_record['candidate_payload']['_collection_accuracy']['accepted'])

    def test_validation_accepts_supported_currency_and_preserves_exclusion(self):
        from worker.pipeline.fpds_validation_routing.models import ValidationInput, ValidationEvidenceLink, ValidationRoutingConfig
        from worker.pipeline.fpds_validation_routing.service import ValidationRoutingService
        from worker.pipeline.fpds_validation_routing.storage import ValidationRoutingStorageConfig
        item,_=fixture()
        for valid in (True,False):
            result=self.normalize(item if valid else replace(item,evidence_origins={}))
            row=result.normalized_candidate_record
            v=ValidationInput(source_id='source',source_document_id='detail',snapshot_id='snap-detail',parsed_document_id='parsed-detail',candidate_id=row['candidate_id'],candidate_run_id='run-current',normalization_model_execution_id=result.normalization_model_execution_id,normalized_storage_key='normalized',metadata_storage_key=None,bank_code='BANK',country_code='CA',source_type='html',source_language='en',source_metadata=item.source_metadata,normalized_candidate_record=row,field_evidence_links=[ValidationEvidenceLink(**link) for link in result.field_evidence_link_records],runtime_notes=result.runtime_notes)
            with TemporaryDirectory() as tmp:
                cfg=NormalizationStorageConfig(driver='filesystem',env_prefix='test',normalization_object_prefix='normalized',retention_class='hot',filesystem_root=tmp)
                validator=ValidationRoutingService(storage_config=ValidationRoutingStorageConfig(driver='filesystem',env_prefix='test',validation_object_prefix='validated',retention_class='hot',filesystem_root=tmp),object_store=build_object_store(cfg))
                out=validator.validate_and_route_inputs(run_id='run-current',inputs=[v],taxonomy_registry={'chequing':{'standard','other','package','premium'}},routing_config=ValidationRoutingConfig(routing_mode='phase1',auto_approve_min_confidence=0,review_warning_confidence_floor=0,force_review_issue_codes=set())).source_results[0]
            self.assertEqual(out.validation_action,'auto_validated' if valid else 'excluded')
            self.assertIsNone(out.review_task_record)
            self.assertNotIn('evidence_origins',row['candidate_payload'])

if __name__=='__main__':unittest.main()
