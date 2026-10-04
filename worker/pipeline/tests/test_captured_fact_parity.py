"""Direct and ordinary collection must prove the same captured financial facts."""
from dataclasses import replace
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes, _pdf_purchase_rate_cells
from worker.pipeline.fpds_extraction.service import _append_captured_decision_facts

class CapturedFactParityTests(unittest.TestCase):
    def context(self):
        from worker.pipeline.tests.test_chequing_direct_comparison import DirectChequingComparisonTests
        return DirectChequingComparisonTests().context_and_cell()

    def test_labels_keep_adjacent_offer_and_other_fees_out(self):
        html = '<main><h1>Everyday Account</h1><h2>Offer</h2>First year free if you qualify.<h2>Rates and fees</h2><div>Annual fee<br>$0<br>Additional cardholders<br>$0<br>Purchase interest rate<br>21.99%<br>Cash interest rate<br>22.99%</div></main>'
        atoms = [s for s in parse_snapshot_bytes(body=html.encode(), content_type='text/html').segments if s.anchor_type == 'financial_declaration']
        self.assertEqual(next(s.text for s in atoms if s.text.startswith('Annual fee')), 'Annual fee\n$0')

    def test_attached_conditions_are_preserved(self):
        html = '<main><h2>Rates and fees</h2><div>Monthly fee<br>$0<br>Only for eligible students until age 25.<br>Transactions<br>Unlimited</div></main>'
        atoms = [s for s in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if s.anchor_type == 'financial_declaration']
        self.assertIn('until age 25',next(s.text for s in atoms if s.text.startswith('Monthly fee')))

    def test_owned_facts_need_no_model_or_discovery_score(self):
        ctx, base = self.context()
        ctx = replace(ctx,source_metadata={**ctx.source_metadata,'discovery_metadata':{**ctx.source_metadata['discovery_metadata'],'page_evidence_score':0}})
        chunks = [replace(base,evidence_chunk_id='fee',anchor_type='financial_declaration',evidence_excerpt='Monthly fee\n$4.00'),replace(base,evidence_chunk_id='transactions',anchor_type='financial_declaration',evidence_excerpt='18 transactions included each month. $1.25 for each additional transaction over 18.')]
        fields=['monthly_fee','included_transactions','additional_transaction_fee']
        facts=_append_captured_decision_facts(context=ctx,candidates=chunks,fields=[],requested_fields=fields)
        self.assertEqual({f.field_name:f.candidate_value for f in facts},{'monthly_fee':'4.0','included_transactions':18,'additional_transaction_fee':'1.25'})
        for bad in [replace(chunks[0],source_snapshot_id='old'),replace(chunks[0],bank_code='OTHER'),replace(chunks[0],evidence_excerpt='Monthly fee\n$0\nFirst year only.')]:
            self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[bad],fields=[],requested_fields=fields),[])

    def test_conflicts_do_not_select_a_winner(self):
        ctx,base=self.context()
        chunks=[replace(base,evidence_chunk_id=str(i),anchor_type='financial_declaration',evidence_excerpt=f'Monthly fee\n${v}') for i,v in enumerate([4,5])]
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=chunks,fields=[],requested_fields=['monthly_fee']),[])
        earlier = _append_captured_decision_facts(context=ctx,candidates=chunks[:1],fields=[],requested_fields=['monthly_fee'])
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=chunks,fields=earlier,requested_fields=['monthly_fee']),[])

    def test_pdf_columns_keep_purchase_separate_from_cash_and_default(self):
        from pathlib import Path
        layout=Path(__file__).parent.joinpath('fixtures/golden/cibc_annual_card_purchase_layout.txt').read_text(encoding='utf8')
        cells=_pdf_purchase_rate_cells(layout,page_no=1)
        self.assertEqual(len(cells),3)
        self.assertIn('21.99%',cells[0].text)
        self.assertNotIn('22.99%',cells[0].text)
        self.assertNotIn('25.99%',cells[0].text)
        self.assertIn('except',cells[0].text)
        self.assertIn('date your Credit Card Account is opened',cells[0].text)
        missing_note=layout.split('1 These interest rates')[0]
        self.assertEqual(_pdf_purchase_rate_cells(missing_note,page_no=1),[])
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        qualified=layout.replace('These interest rates are in effect on the date your Credit Card Account is opened.', 'These promotional interest rates apply only for the first year.')
        self.assertFalse(quote_supports_value('purchase_interest_rate',21.99,_pdf_purchase_rate_cells(qualified,page_no=1)[0].text))
        self.assertEqual(_pdf_purchase_rate_cells(layout.replace('Purchases1','Cash Advances1'),page_no=1),[])

    def test_preceding_introductory_condition_cannot_become_zero_fee(self):
        html='<main><h2>First year free if you qualify</h2><div>Annual fee<br>$0<br>Purchase interest rate<br>21.99%</div></main>'
        atoms=[a for a in parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments if a.anchor_type=='financial_declaration']
        self.assertTrue(all('if you qualify' in a.text for a in atoms))
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        self.assertFalse(quote_supports_value('annual_fee',0,atoms[0].text))

    def test_captured_identity_overrides_navigation_heuristic(self):
        ctx,base=self.context()
        name=ctx.source_metadata['discovery_metadata']['primary_heading']
        good=replace(base,anchor_type='section',evidence_excerpt=name+'\nRegular pricing and features.')
        facts=_append_captured_decision_facts(context=ctx,candidates=[good],fields=[],requested_fields=['product_name'])
        self.assertEqual(facts[0].candidate_value,name)
        bad=replace(good,evidence_excerpt='Travel rewards cards\n'+name)
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[bad],fields=[],requested_fields=['product_name']),[])

    def test_real_current_dom_survives_parser_and_fact_proof(self):
        from pathlib import Path
        ctx,base=self.context()
        path=Path(__file__).parent/'fixtures/golden/cibc_adapta_pricing_dom.html'
        atoms=[a for a in parse_snapshot_bytes(body=path.read_bytes(),content_type='text/html').segments if a.anchor_type=='financial_declaration']
        ctx=replace(ctx,source_metadata={**ctx.source_metadata,'product_type':'credit-card'})
        chunks=[replace(base,evidence_chunk_id=str(i),anchor_type=a.anchor_type,evidence_excerpt=a.text) for i,a in enumerate(atoms)]
        facts=_append_captured_decision_facts(context=ctx,candidates=chunks,fields=[],requested_fields=['annual_fee'])
        self.assertEqual(facts[0].candidate_value,'0.0')
        ctx,base=self.context()
        atoms=[a for a in parse_snapshot_bytes(body=Path(__file__).parent.joinpath('fixtures/golden/cibc_everyday_pricing_dom.html').read_bytes(),content_type='text/html').segments if a.anchor_type=='financial_declaration']
        chunks=[replace(base,evidence_chunk_id=str(i),anchor_type=a.anchor_type,evidence_excerpt=a.text) for i,a in enumerate(atoms)]
        facts=_append_captured_decision_facts(context=ctx,candidates=chunks,fields=[],requested_fields=['monthly_fee','included_transactions','additional_transaction_fee'])
        self.assertEqual({f.field_name:f.candidate_value for f in facts},{'monthly_fee':'4.0','included_transactions':18,'additional_transaction_fee':'1.25'})

    def test_real_pdf_disclosure_anchor_survives_navigation_budget(self):
        from pathlib import Path
        from worker.discovery.fpds_discovery.discovery import extract_links
        nav='<nav>'+''.join(f'<a href="/menu/{i}">Menu {i}</a>' for i in range(300))+'</nav>'
        dom=Path(__file__).parent.joinpath('fixtures/golden/cibc_card_pricing_companion_dom.html').read_text(encoding='utf8')
        links=extract_links(nav+dom,base_url='https://www.cibc.com/card')
        self.assertLessEqual(len(links),256)
        self.assertTrue(any('cibc-creditcard-annual-interest-rate-fees-11995-en.pdf' in x.normalized_url for x in links))

    def test_normal_collection_proves_facts_before_model_and_restores_exact_values(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from worker.pipeline.fpds_extraction.models import ExtractionInput
        from worker.pipeline.fpds_extraction.service import ExtractionService
        from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store
        ctx,base=self.context()
        chunks=[replace(base,evidence_chunk_id='fee',anchor_type='financial_declaration',evidence_excerpt='Monthly fee\n$4.00'),replace(base,evidence_chunk_id='transactions',anchor_type='financial_declaration',evidence_excerpt='18 transactions included each month. $1.25 for each additional transaction over 18.')]
        called=[]
        def grounding(**kwargs):
            proven={f.field_name:f for f in kwargs['collected_fields']}
            self.assertEqual(proven['monthly_fee'].candidate_value,'4.0')
            self.assertEqual(proven['included_transactions'].candidate_value,18)
            called.append(True)
            return [replace(proven['monthly_fee'],candidate_value='0.0')],[],None
        with TemporaryDirectory() as temp, patch('worker.pipeline.fpds_extraction.service.llm_provider_configured',return_value=True), patch('worker.pipeline.fpds_extraction.service.grounded_with_reuse',side_effect=grounding):
            cfg=ExtractionStorageConfig('filesystem','test','extracted','hot',filesystem_root=temp)
            service=ExtractionService(storage_config=cfg,object_store=build_object_store(cfg))
            out=service._extract_single_document(run_id='run',extraction_input=ExtractionInput(context=ctx,candidates=chunks),correlation_id='test',request_id='test',override_field_names=['monthly_fee','included_transactions','additional_transaction_fee'])
        self.assertEqual(out.extraction_action,'stored',out.error_summary)
        self.assertEqual(called,[True])
        self.assertEqual(next(f.candidate_value for f in out.extracted_fields if f.field_name=='monthly_fee'),'4.0')

    def test_normalizer_cannot_overwrite_earned_financial_proof(self):
        from unittest.mock import patch
        from worker.pipeline.tests.test_normalization import _build_input,_field
        from worker.pipeline.fpds_normalization.service import _normalize_candidate
        item=_build_input()
        original=replace(next(f for f in item.extracted_fields if f.field_name=='product_name'),candidate_value='TD Rewards Visa Card')
        field=replace(_field('annual_fee','139','decimal',1.0,evidence_chunk_id='fee'),evidence_text_excerpt='Annual fee\n$139',field_metadata={'official_grounding_contract_version':'collection-official-grounding-v2','official_verification_status':'match','official_web_sources':[{'url':'https://td.com/card'}],'evidence_quote':'Annual fee\n$139'})
        item=replace(item,source_metadata={**item.source_metadata,'product_type':'credit-card','fallback_policy':'generic_ai_review','expected_fields':['product_name','annual_fee','purchase_interest_rate']},schema_context={'product_type':'credit-card','product_family':'lending'},extracted_fields=[original,field])
        from worker.pipeline.fpds_normalization.models import NormalizationEvidenceLink
        item=replace(item,normalized_source_url='https://td.com/card',source_metadata={**item.source_metadata,'official_domain_allowlist':['td.com'],'discovery_role':'detail'},evidence_links=[NormalizationEvidenceLink(field_name='annual_fee',candidate_value='139',evidence_chunk_id='fee',evidence_text_excerpt='Annual fee\n$139',source_document_id=item.source_document_id,source_snapshot_id=item.snapshot_id,citation_confidence=1.0,model_execution_id='extract',anchor_type='financial_declaration',anchor_value='fees',page_no=None,chunk_index=0)],evidence_origins_resolved=True,evidence_origins={'fee':{'run_id':'run','bank_code':'TD','country_code':'CA','source_document_id':item.source_document_id,'snapshot_id':item.snapshot_id,'parsed_document_id':item.parsed_document_id,'evidence_excerpt':'Annual fee\n$139','source_url':'https://td.com/card'}})
        with patch('worker.pipeline.fpds_normalization.service._normalize_dynamic_fields_with_ai',return_value=({'candidate_payload':{'annual_fee':0}},[],None)):
            record,links,notes,meta=_normalize_candidate(run_id='run',candidate_id='candidate',normalization_model_execution_id='normalizer',item=item)
        self.assertEqual(record['field_mapping_metadata']['annual_fee']['normalized_value'],139)
        self.assertIn('Preserved captured `annual_fee`', ' '.join(notes))
        # Missing identity/rate proof still prevents publication.
        from worker.pipeline.fpds_collection_accuracy import sanitize_candidate
        record,receipt=sanitize_candidate(record,source_metadata=item.source_metadata,evidence=[{'evidence_chunk_id':'fee','evidence_excerpt':'Annual fee\n$139','source_url':'https://td.com/card'}])
        self.assertFalse(receipt['accepted'])
        self.assertEqual(record['candidate_payload']['annual_fee'],139)

    def test_dynamic_placeholder_recovery_is_official_and_bounded(self):
        from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy,FetchedResponse,_should_try_browser_rendered_rate_fallback
        response=FetchedResponse(body=b'<main>Interest rate RDS%rate[3].Savings%</main>',final_url='https://examplebank.com/savings',content_type='text/html',status_code=200,headers={},fetched_at='2026-10-03T00:00:00Z',redirect_count=0)
        self.assertTrue(_should_try_browser_rendered_rate_fallback(response,DiscoveryFetchPolicy(allowed_domains=('examplebank.com',))))
        self.assertFalse(_should_try_browser_rendered_rate_fallback(replace(response,final_url='https://other.com'),DiscoveryFetchPolicy(allowed_domains=('examplebank.com',))))
        self.assertFalse(_should_try_browser_rendered_rate_fallback(replace(response,body=b'<main>Interest rate 2.5%</main>'),DiscoveryFetchPolicy(allowed_domains=('examplebank.com',))))

    def test_card_family_exceptions_and_wrong_companion_are_rejected(self):
        ctx,base=self.context()
        identity='BANKA Rewards Visa Card'
        ctx=replace(ctx,bank_code='BANKA',source_metadata={**ctx.source_metadata,'product_type':'credit-card','normalized_source_url':'https://examplebank.com/card','official_domain_allowlist':['examplebank.com'],'discovery_metadata':{'product_identity_match':True,'primary_heading':identity,'page_title':identity}})
        quote='Annual\nInterest\nRates\nCard Product\nAll BANKA Personal Credit Cards (except BANKA Select Visa)\nPurchases1\n21.99%'
        cell=replace(base,bank_code='BANKA',source_document_id='rates-doc',source_snapshot_id='rates-snap',anchor_type='card_purchase_rate_cell',evidence_excerpt=quote,retrieval_metadata={'captured_companion':True,'source_url':'https://examplebank.com/rates.pdf'})
        facts=_append_captured_decision_facts(context=ctx,candidates=[cell],fields=[],requested_fields=['purchase_interest_rate'])
        self.assertEqual(facts[0].candidate_value,'21.99')
        excluded=replace(ctx,source_metadata={**ctx.source_metadata,'discovery_metadata':{'product_identity_match':True,'primary_heading':'BANKA Select Visa','page_title':'BANKA Select Visa'}})
        self.assertEqual(_append_captured_decision_facts(context=excluded,candidates=[cell],fields=[],requested_fields=['purchase_interest_rate']),[])
        named=replace(cell,evidence_excerpt=quote.replace('All BANKA Personal Credit Cards (except BANKA Select Visa)','BANKA Rewards Visa Infinite Card'))
        self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[named],fields=[],requested_fields=['purchase_interest_rate']),[])
        for bad in [replace(cell,bank_code='OTHER'),replace(cell,country_code='US'),replace(cell,retrieval_metadata={}),replace(cell,source_language='fr')]:
            self.assertEqual(_append_captured_decision_facts(context=ctx,candidates=[bad],fields=[],requested_fields=['purchase_interest_rate']),[])

if __name__=='__main__': unittest.main()
