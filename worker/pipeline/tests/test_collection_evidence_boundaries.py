"""Generic regressions from retained official captures; no live provider calls."""
from dataclasses import replace
from pathlib import Path
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_collection_accuracy import quote_supports_value, _ANNUAL_RATE_BASIS
import unittest
from worker.discovery.fpds_discovery.url_utils import normalize_source_url, infer_source_type
from worker.pipeline.fpds_extraction.service import _deposit_interest_context_conflicts
from worker.pipeline.fpds_normalization.models import NormalizationExtractedField
from worker.pipeline.tests.test_optional_collection import context, extract
from worker.pipeline.tests.test_checking_optional_rates import normalized, facts

class CollectionEvidenceBoundaryTests(unittest.TestCase):
    def test_document_query_identities_are_not_collapsed(self):
        for key in ('doc', 'form', 'file', 'id'):
            with self.subTest(key=key):
                a=normalize_source_url(f'https://bank.example/forms/pdf/?{key}=21&utm_source=mail')
                b=normalize_source_url(f'https://bank.example/forms/pdf/?{key}=22')
                self.assertNotEqual(a,b)
                self.assertIn(key+'=21',a)
        self.assertEqual(normalize_source_url('https://bank.example/home?id=tracking'), 'https://bank.example/home')

    def test_extensionless_pdf_endpoint_is_typed(self):
        for path in ('/forms/pdf/?form=bb184', '/marketing-material/pdf?doc=21', '/document.pdf?doc=2'):
            self.assertEqual(infer_source_type('https://bank.example'+path), 'pdf')
        self.assertEqual(infer_source_type('https://bank.example/pdf-help'), 'html')

    def test_grounded_product_identity_survives_discovery_formatting(self):
        for name, heading in [('Short-Term Guaranteed Investment Certificates (GICs)', 'Short Term Guaranteed Investment Certificates (GICs)'),
                              ('Example Checking+', 'Example Checking')]:
            ctx=context('chequing')
            ctx=replace(ctx,source_metadata={**ctx.source_metadata,'discovery_metadata':{'primary_heading':heading,'page_title':heading}})
            (fields,_,_),_,chunks=extract(ctx,facts(name))
            clean,receipt=normalized(ctx,fields,chunks)
            self.assertEqual(clean['product_name'],name)
            self.assertTrue(receipt['accepted'],receipt)

    def test_separate_overdraft_clause_does_not_hide_deposit_payment(self):
        quote='Interest is calculated daily on the closing balance and paid monthly.'
        excerpt=quote+'\nOverdraft interest is calculated daily on the closing overdraft balance.'
        ctx=context('chequing')
        (fields,_,_),_,chunks=extract(ctx,{**facts(),'interest_calculation_method':(quote,excerpt)},
            overrides={'interest_calculation_method':{'evidence_quote':quote}})
        clean,receipt=normalized(ctx,fields,chunks)
        self.assertEqual(clean['candidate_payload'].get('interest_calculation_method'),quote,receipt)

    def test_borrowing_and_companion_payment_still_omit(self):
        for quote in ['Overdraft interest is calculated daily and paid monthly.',
                      'Savings account interest is calculated daily and paid monthly.',
                      'Interest is paid monthly on the overdraft balance.', 'Overdraft\nInterest is calculated daily and paid monthly.',
                      'Savings Account\nInterest is calculated daily and paid monthly.']:
            (fields,_,_),_,_=extract(context('chequing'),{'interest_calculation_method':(quote,quote)})
            self.assertEqual(fields,[])

class OfficialRateStructureTests(unittest.TestCase):
    def test_saved_account_rows_keep_annual_basis_and_full_legal_conditions(self):
        body=(Path(__file__).parent/'fixtures/official_rate_table_alterna.html').read_bytes()
        artifact=parse_snapshot_bytes(body=body,content_type='text/html')
        chunks=_build_evidence_chunks(parsed_document_id='parsed',source_language='en',artifact=artifact,max_chars=900,overlap_chars=120)
        rows=[c for c in chunks if c.anchor_type=='rate_table_row']
        self.assertEqual(len(rows),4)
        savings=next(c for c in rows if 'High Interest eSavings Account' in c.evidence_excerpt)
        self.assertIn('Interest rate is annualized',savings.evidence_excerpt)
        self.assertIn('For accounts opened before May 1, 2017',savings.evidence_excerpt)
        self.assertNotIn('0.05%',savings.evidence_excerpt)
        self.assertTrue(quote_supports_value('standard_rate',1.05,savings.evidence_excerpt))
        self.assertEqual(artifact.full_text[savings.chunk_char_start:savings.chunk_char_end],savings.evidence_excerpt)

    def test_annualization_and_maturity_only_require_explicit_nonnegated_statements(self):
        for quote in ['Rate 1.05%. Interest rate is annualized.', 'Annual interest rate 1.05%.']:
            self.assertTrue(quote_supports_value('standard_rate',1.05,quote))
        for quote in ['Interest rate 1.05%.', 'Rate 1.05%. Interest rate is not annualized.', 'Rate 1.05%. Annual fee $10.']:
            self.assertFalse(_ANNUAL_RATE_BASIS.search(quote))
        for quote in ['Cashable upon maturity only.', 'Can only be redeemed at maturity.']:
            self.assertTrue(quote_supports_value('redeemable_flag',False,quote))
        for quote in ['May be cashable upon maturity only.', 'Cashable upon maturity only or before maturity.', 'Not cashable upon maturity only.']:
            self.assertFalse(quote_supports_value('redeemable_flag',False,quote))

    def test_two_rate_tables_do_not_borrow_global_annual_basis(self):
        body=b'<main><table><tr><th>Account</th><th>Rate</th></tr><tr><td>A Savings</td><td>2%</td></tr></table><table><tr><th>Account</th><th>Rate</th></tr><tr><td>B Savings</td><td>3%</td></tr></table><h2>Legal</h2><p>Interest rate is annualized.</p></main>'
        a=parse_snapshot_bytes(body=body,content_type='text/html')
        self.assertFalse(any(s.anchor_type=='rate_table_row' and 'annualized' in s.text for s in a.segments))

class CompanionEvidenceTests(unittest.TestCase):
    def test_captured_companion_reaches_one_grounding_call_with_its_actual_origin(self):
        from worker.pipeline.fpds_extraction.models import ExtractionInput
        from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence, _extract_official_fields_with_ai
        from worker.pipeline.tests.test_optional_collection import INVOKE, URL
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from unittest.mock import patch
        import json
        detail=context('savings')
        detail=replace(detail,source_metadata={**detail.source_metadata,'discovery_metadata':{'primary_heading':'Maple High Interest Savings'}})
        supporting=replace(detail,source_document_id='rates',snapshot_id='rates-snapshot',parsed_document_id='rates-parsed',
            source_metadata={**detail.source_metadata,'source_url':'https://bank.example/rates','discovery_role':'supporting_html'})
        excerpt='Maple High Interest Savings\nAnnual interest rate 2.20%.'
        chunk=EvidenceChunkCandidate('rate-row','rates-parsed',0,'rate_table_row','row',None,'en',excerpt,{},'rates','rates-snapshot','EXAMPLE','CA','html')
        inputs=_bind_grounding_evidence([ExtractionInput(detail,[]),ExtractionInput(supporting,[chunk])])
        self.assertEqual(len(inputs[0].grounding_candidates),1)
        entry={'field_name':'standard_rate','status':'match','has_verified_value':True,'verified_value_json':'2.2',
            'evidence_chunk_id':'rate-row','evidence_quote':excerpt,'confidence':.99,'sources':[{'url':'https://bank.example/rates'}]}
        with patch(INVOKE,return_value=({'fields':[entry]},{'web_search_sources':[{'url':'https://bank.example/rates'}]})) as call:
            fields,notes,_=_extract_official_fields_with_ai(context=detail,candidates=inputs[0].grounding_candidates,requested_fields=['standard_rate'],collected_fields=[])
        self.assertEqual(len(fields),1,notes)
        self.assertEqual(fields[0].source_document_id,'rates')
        self.assertEqual(fields[0].source_snapshot_id,'rates-snapshot')
        sent=call.call_args.kwargs['payload']['candidate_chunks'][0]
        self.assertEqual(sent['source_url'],'https://bank.example/rates')
        call.assert_called_once()
        entry['sources']=[{'url':URL}]
        with patch(INVOKE,return_value=({'fields':[entry]},{'web_search_sources':[{'url':URL}]})):
            fields,_,_=_extract_official_fields_with_ai(context=detail,candidates=inputs[0].grounding_candidates,requested_fields=['standard_rate'],collected_fields=[])
        self.assertEqual(fields,[])

    def test_companions_remain_bank_country_language_product_bounded(self):
        from worker.pipeline.fpds_extraction.models import ExtractionInput
        from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        detail=context('savings');detail=replace(detail,source_metadata={**detail.source_metadata,'discovery_metadata':{'primary_heading':'Maple High Interest Savings'}})
        support=replace(detail,source_document_id='support',snapshot_id='s',parsed_document_id='p',source_metadata={**detail.source_metadata,'source_url':'https://bank.example/rates','discovery_role':'supporting_html'})
        chunk=EvidenceChunkCandidate('row','p',0,'section','row',None,'en','Maple High Interest Savings annual rate 2%.',{},'support','s','EXAMPLE','CA','html')
        for bad in [replace(support,bank_code='OTHER'),replace(support,country_code='US'),replace(support,source_language='fr'),
                    replace(support,source_metadata={**support.source_metadata,'source_url':'https://evil.example/rates'}),
                    replace(support,source_metadata={**support.source_metadata,'discovery_role':'detail'})]:
            inputs=_bind_grounding_evidence([ExtractionInput(detail,[]),ExtractionInput(bad,[chunk])])
            self.assertEqual(inputs[0].grounding_candidates,[])
        unrelated=replace(chunk,evidence_excerpt='Example Companion Checking annual rate 2%.')
        self.assertEqual(_bind_grounding_evidence([ExtractionInput(detail,[]),ExtractionInput(support,[unrelated])])[0].grounding_candidates,[])

class CapturedCompanionIntegrationTests(unittest.TestCase):
    def test_saved_alterna_row_and_other_bank_row_survive_real_normalization_gate(self):
        import json
        from dataclasses import asdict
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from worker.pipeline.fpds_extraction.models import ExtractionInput
        from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence,_extract_official_fields_with_ai
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_normalization.models import NormalizationInput,NormalizationExtractedField,NormalizationEvidenceLink
        from worker.pipeline.fpds_normalization.service import NormalizationService
        from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig,build_object_store
        from worker.pipeline.tests.test_optional_collection import INVOKE,URL
        body=(Path(__file__).parent/'fixtures/official_rate_table_alterna.html').read_bytes()
        artifact=parse_snapshot_bytes(body=body,content_type='text/html')
        saved=next(s for s in artifact.segments if s.anchor_type=='rate_table_row' and 'High Interest eSavings Account' in s.text)
        for country,name,rate,excerpt in [('CA','High Interest eSavings',1.05,saved.text),
            ('US','Maple High Yield Savings',2.20,'Maple High Yield Savings\nAnnual percentage yield (APY)\n2.20%\nInterest is calculated daily and paid monthly.')]:
            with self.subTest(country=country):
                ctx=context('savings',country)
                ctx=replace(ctx,source_metadata={**ctx.source_metadata,'discovery_metadata':{'primary_heading':name}})
                support=replace(ctx,source_document_id='rates',snapshot_id='rates-snapshot',parsed_document_id='rates-parsed',
                    source_metadata={**ctx.source_metadata,'source_url':'https://bank.example/rates','discovery_role':'supporting_html'})
                chunk=EvidenceChunkCandidate('rate-row','rates-parsed',0,'rate_table_row','row',None,'en',excerpt,{},'rates','rates-snapshot','EXAMPLE',country,'html')
                inputs=_bind_grounding_evidence([ExtractionInput(ctx,[]),ExtractionInput(support,[chunk])])
                (base,_,_),_,_=extract(ctx,{'product_name':(name,name),'monthly_fee':(0,'No monthly fee.')})
                entry={'field_name':'standard_rate','status':'match','has_verified_value':True,'verified_value_json':json.dumps(rate),
                    'evidence_chunk_id':'rate-row','evidence_quote':excerpt,'confidence':.99,'sources':[{'url':'https://bank.example/rates'}]}
                with patch(INVOKE,return_value=({'fields':[entry]},{'web_search_sources':[{'url':'https://bank.example/rates'}]})):
                    rate_fields,notes,_=_extract_official_fields_with_ai(context=ctx,candidates=inputs[0].grounding_candidates,requested_fields=['standard_rate'],collected_fields=[])
                self.assertEqual(len(rate_fields),1,notes)
                fields=base+rate_fields
                links=[NormalizationEvidenceLink(f.field_name,str(f.candidate_value),f.evidence_chunk_id,f.evidence_text_excerpt,
                    f.source_document_id,f.source_snapshot_id,.99,'extract',f.anchor_type,f.anchor_value,f.page_no,f.chunk_index) for f in fields]
                origin={'evidence_chunk_id':'rate-row','source_document_id':'rates','snapshot_id':'rates-snapshot','evidence_excerpt':excerpt,
                    'source_url':'https://bank.example/rates','bank_code':'EXAMPLE','country_code':country,'run_id':'run-current'}
                item=NormalizationInput('detail','source','snapshot','parsed','extract','private',None,'EXAMPLE',country,'html','en',ctx.source_metadata,
                    {'product_type':'savings','product_family':'deposit'},[NormalizationExtractedField(**asdict(f)) for f in fields],links,[],normalized_source_url=URL,evidence_origins={'rate-row':origin})
                with TemporaryDirectory() as temp:
                    cfg=NormalizationStorageConfig(driver='filesystem',env_prefix='test',normalization_object_prefix='normalized',retention_class='hot',filesystem_root=temp)
                    with patch('worker.pipeline.fpds_normalization.service.llm_provider_configured',return_value=False):
                        result=NormalizationService(storage_config=cfg,object_store=build_object_store(cfg)).normalize_inputs(run_id='run-current',inputs=[item]).source_results[0]
                self.assertIsNone(result.error_summary)
                record=result.normalized_candidate_record;receipt=record['candidate_payload']['_collection_accuracy']
                self.assertTrue(receipt['accepted'],receipt)
                self.assertEqual(record['candidate_payload']['standard_rate'],rate)
                self.assertTrue(any(l['source_document_id']=='rates' and l['field_name']=='standard_rate' for l in result.field_evidence_link_records))

class SavedFinancialContextTests(unittest.TestCase):
    def test_actual_saved_deposit_sentence_survives_compound_overdraft_chunk(self):
        import json
        saved=json.loads((Path(__file__).parent/'fixtures/official_deposit_overdraft_context.json').read_text(encoding='utf-8'))
        ctx=context('chequing')
        (fields,_,_),_,chunks=extract(ctx,{**facts('No-Fee eChequing Account'),
            'interest_calculation_method':(saved['quote'],saved['excerpt'])},overrides={'interest_calculation_method':{'evidence_quote':saved['quote']}})
        clean,receipt=normalized(ctx,fields,chunks)
        self.assertTrue(receipt['accepted'],receipt)
        self.assertEqual(clean['candidate_payload']['interest_calculation_method'],saved['quote'])
        self.assertEqual(next(f for f in fields if f.field_name=='interest_calculation_method').evidence_text_excerpt,saved['excerpt'])

    def test_actual_term_schedule_remains_atomic_with_promotion_and_access_conditions(self):
        from worker.pipeline.fpds_collection_accuracy import _ANNUAL_RATE_BASIS
        body=(Path(__file__).parent/'fixtures/official_term_schedule_alterna.html').read_bytes()
        artifact=parse_snapshot_bytes(body=body,content_type='text/html')
        chunks=_build_evidence_chunks(parsed_document_id='parsed',source_language='en',artifact=artifact,max_chars=900,overlap_chars=120)
        schedule=next(c for c in chunks if c.anchor_type=='rate_table_schedule')
        self.assertGreater(len(schedule.evidence_excerpt),900)
        self.assertIn('Special promotional rate may be changed or withdrawn',schedule.evidence_excerpt)
        self.assertIn('Cashable upon maturity only.',schedule.evidence_excerpt)
        self.assertIn('Maximum investment $500,000',schedule.evidence_excerpt)
        self.assertTrue(_ANNUAL_RATE_BASIS.search(schedule.evidence_excerpt))
        rows=[{'term_label':f'{i} Year','rate':r} for i,r in enumerate([2.65,2.85,3.10,3.25,3.30],1)]
        self.assertTrue(quote_supports_value('term_rate_table',rows,schedule.evidence_excerpt))
        self.assertFalse(quote_supports_value('standard_rate',2.65,schedule.evidence_excerpt))
        self.assertTrue(quote_supports_value('redeemable_flag',False,schedule.evidence_excerpt))
        # The year schedule is not a literal-day term or an unconditional rate.
        self.assertFalse(quote_supports_value('term_length_days',365,schedule.evidence_excerpt))

class GroundingBudgetTests(unittest.TestCase):
    def test_atomic_evidence_keeps_character_and_chunk_budget(self):
        from worker.pipeline.fpds_extraction.service import _select_official_grounding_chunks
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        chunks=[EvidenceChunkCandidate(str(i),'p',i,'rate_table_row','row',None,'en','A'*6000,{},'d','s','BANK','CA','html') for i in range(24)]
        selected=_select_official_grounding_chunks(candidates=chunks,collected_fields=[])
        self.assertLessEqual(len(selected),24)
        self.assertLessEqual(sum(len(c.evidence_excerpt) for c in selected),43200)
        self.assertTrue(all(len(c.evidence_excerpt)==6000 for c in selected))

    def test_maturity_only_does_not_discard_exception(self):
        self.assertFalse(quote_supports_value('redeemable_flag',False,'Cashable upon maturity only. However hardship withdrawal before maturity is possible.'))

class TableLabelBoundaryTests(unittest.TestCase):
    def test_row_header_product_labels_do_not_become_other_rows_headers(self):
        body=b'<main><table><thead><tr><th scope="col">Account</th><th scope="col">Annual interest rate</th></tr></thead><tbody><tr><th scope="row">Maple Savings</th><td>2.20%</td></tr><tr><th scope="row">Oak Savings</th><td>3.30%</td></tr></tbody></table></main>'
        artifact=parse_snapshot_bytes(body=body,content_type='text/html')
        rows=[s for s in artifact.segments if s.anchor_type=='rate_table_row']
        self.assertEqual(len(rows),2)
        self.assertIn('Maple Savings',rows[0].text)
        self.assertNotIn('Oak Savings',rows[0].text)
        self.assertTrue(quote_supports_value('standard_rate',2.20,rows[0].text))
        self.assertFalse(quote_supports_value('standard_rate',3.30,rows[0].text))
