"""Current official tables through ordinary parse/artifact/automatic gates."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_collection_accuracy import quote_supports_value
from worker.pipeline.tests.test_evidence_research_parity import input_from_segments, run_services

FIXTURES = Path(__file__).parent / 'fixtures/owned-deposit-tables'
SOURCES = json.loads((FIXTURES/'sources.json').read_text(encoding='utf8'))

def captured(kind, role='detail', bank='OAKEN'):
    row=next(r for r in SOURCES if r['kind']==kind)
    artifact=parse_snapshot_bytes(body=(FIXTURES/row['file']).read_bytes(),content_type='text/html')
    item=input_from_segments(bank=bank,url=row['url'],product=row['type'],name=row['name'],
        segments=[],role=role,ident=kind)
    rows=_build_evidence_chunks(parsed_document_id=item.context.parsed_document_id,source_language='en',
        artifact=artifact,max_chars=900,overlap_chars=120)
    from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
    chunks=[EvidenceChunkCandidate(r.evidence_chunk_id,r.parsed_document_id,r.chunk_index,r.anchor_type,
        r.anchor_value,r.page_no,'en',r.evidence_excerpt,r.retrieval_metadata,item.context.source_document_id,
        item.context.snapshot_id,bank,'CA','html') for r in rows]
    return replace(item,candidates=chunks)

class OwnedDepositTableTests(unittest.TestCase):
    def test_current_official_fixture_hashes(self):
        for row in SOURCES:
            self.assertEqual(sha256((FIXTURES/row['file']).read_bytes()).hexdigest(),row['sha256'])

    def test_native_named_rows_and_complete_multi_column_schedules(self):
        item=captured('gic-rates','supporting_html')
        records=[c for c in item.candidates if c.anchor_type=='named_deposit_schedule']
        self.assertGreaterEqual(len(records),2)
        long=next(c for c in records if c.anchor_value=='Long Term GICs')
        self.assertIn('Semi Annual (%)',long.evidence_excerpt)
        self.assertIn('non-redeemable',long.evidence_excerpt)
        self.assertIn('per annum',long.evidence_excerpt)
        self.assertEqual(sum(c.anchor_type=='named_deposit_rate' for c in captured('savings-rates','supporting_html').candidates),4)

    def test_saved_shape_savings_passes_ordinary_services_without_provider(self):
        record,validation,_=run_services([captured('savings'),captured('savings-rates','supporting_html')])
        self.assertEqual(validation.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
        self.assertEqual(record['candidate_payload']['standard_rate'],2.8)
        self.assertEqual(record['candidate_payload']['monthly_fee'],0)
        self.assertEqual(record['candidate_payload'].get('interest_calculation_method'),'calculated daily')
        self.assertEqual(record['candidate_payload'].get('interest_payment_frequency'),'paid monthly')
        self.assertNotIn('promotional_rate',record['candidate_payload'])
        self.assertIsNone(validation.review_task_record)

    def test_gic_family_expands_owned_schedules_without_invented_days(self):
        record,validation,extracted=run_services([captured('gic'),captured('gic-rates','supporting_html')])
        self.assertEqual(validation.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
        self.assertEqual(record['product_name'],'Long Term GICs')
        rows=record['candidate_payload']['term_rate_table']
        self.assertEqual([(r['term_label'],r['rate']) for r in rows],
            [('1 Year',3.8),('18 Months',3.85),('2 Years',4.25),('3 Years',4.3),('4 Years',4.35),('5 Years',4.5)])
        self.assertTrue(all('term_length_days' not in r for r in rows))
        self.assertTrue(record['candidate_payload']['non_redeemable_flag'])
        self.assertEqual(record['candidate_payload']['minimum_deposit'],1000)
        name=next(f for f in extracted.extracted_fields if f.field_name=='product_name')
        self.assertEqual([v['product_name'] for v in name.field_metadata['grounded_product_variants']],
            ['Long Term GICs','Short Term GICs','Short Term GICs (RSP)'])

    def test_actual_latest_detail_metadata_preserves_named_gic_proof(self):
        metadata=json.loads((FIXTURES/'latest-detail-metadata.json').read_text(encoding='utf8'))
        detail=captured('gic')
        detail=replace(detail,context=replace(detail.context,source_metadata=metadata['gic']))
        record,validation,extracted=run_services([detail,captured('gic-rates','supporting_html')])
        self.assertEqual(validation.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
        self.assertEqual(record['product_name'],'Long Term GICs')
        name=next(f for f in extracted.extracted_fields if f.field_name=='product_name')
        self.assertEqual(len(name.field_metadata['grounded_product_variants']),3)

    def test_native_identity_keeps_qualifiers_and_rejects_two_named_headings(self):
        from worker.pipeline.fpds_extraction.service import _captured_native_product_title
        item=captured('gic')
        metadata=json.loads((FIXTURES/'latest-detail-metadata.json').read_text(encoding='utf8'))['gic']
        item=replace(item,context=replace(item.context,source_metadata=metadata))
        self.assertEqual(_captured_native_product_title(item.context,item.candidates),'Guaranteed Investment Certificates (GICs)')
        price=next(c for c in item.candidates if c.anchor_type=='document_heading' and c.evidence_excerpt=='4.25%')
        extra=replace(price,evidence_excerpt='Other Investment Certificates')
        self.assertIsNone(_captured_native_product_title(item.context,[extra if c is price else c for c in item.candidates]))
        heading=next(c for c in item.candidates if c.anchor_type=='document_heading' and c is not price)
        for qualifier in ['TFSA','XYZ','GICs Cashable']:
            changed=replace(heading,evidence_excerpt='Guaranteed Investment Certificates ('+qualifier+')')
            self.assertIsNone(_captured_native_product_title(item.context,[changed if c is heading else c for c in item.candidates]))

    def test_foreign_scope_and_missing_observed_detail_link_fail_closed(self):
        detail=captured('savings')
        companion=captured('savings-rates','supporting_html')
        for changed in [replace(companion,context=replace(companion.context,bank_code='OTHER')),
            replace(companion,candidates=[replace(c,source_snapshot_id='wrong') for c in companion.candidates]),
            replace(companion,candidates=[c for c in companion.candidates if c.anchor_type!='captured_product_link'])]:
            _,validation,_=run_services([detail,changed])
            self.assertEqual(validation.validation_action,'excluded')

    def test_blanket_account_fee_zero_is_attribute_scoped_and_unconditional(self):
        quote='With our non-registered savings account, you’ll enjoy no fees and no minimum balance requirements.'
        self.assertTrue(quote_supports_value('monthly_fee',0,quote))
        for q in ['No fees to open your savings account.','No transfer fees for your savings account.',
            'With our savings account, no fees if you maintain $1000.',
            'With our savings account, no fees for the first year.']:
            self.assertFalse(quote_supports_value('monthly_fee',0,q),q)
        self.assertFalse(quote_supports_value('minimum_deposit',0,quote))

    def test_blanket_fee_keeps_later_conditions_and_linked_notes(self):
        from bs4 import BeautifulSoup
        from worker.native_deposit_records import deposit_table_records
        declaration='With our savings account, no fees.'
        for tail in [' Monthly fees apply after the first year.',
            ' Conditions apply.', '<a href="#restriction"></a>']:
            html='<main><p>'+declaration+tail+'</p><p id="restriction">A balance condition applies.</p></main>'
            self.assertFalse(any(r[0]=='named_deposit_fee' for r in deposit_table_records(BeautifulSoup(html,'html.parser'))))
        html='<main><p>With our non-registered savings account, no fees. For our registered savings accounts, fees apply. Both types have an account charge.</p></main>'
        self.assertFalse(any(r[0]=='named_deposit_fee' for r in deposit_table_records(BeautifulSoup(html,'html.parser'))))

    def test_cross_bank_same_native_shape_and_payment_columns(self):
        from worker.native_rate_tables import rate_schedules
        q='Bond Certificate\nTerm\nAnnual (%)\nSemi Annual (%)\nMonthly (%)\n18 Months\n3.85\n3.80\n3.75\nInterest is calculated per annum.'
        self.assertEqual(rate_schedules(q,annual_only=True),[[{'term_label':'18 Months','rate':3.85}]])
        q2='Short Term Certificates\nTerm\nRate (%)\n30-59 Days\n1.00\nInterest is calculated per annum.'
        self.assertEqual(rate_schedules(q2,annual_only=True),[[{'term_label':'30-59 Days','rate':1.0}]])
        self.assertEqual(rate_schedules(q2.replace('Interest is calculated per annum.',''),annual_only=True),[])
        self.assertEqual(rate_schedules(q.replace('3.75','X.XXX'),annual_only=True),[])
        partial='Term\nAnnual rate (%)\n1 Year\n3.5\n2 Years\nUnavailable'
        self.assertEqual(rate_schedules(partial,annual_only=True),[])
        self.assertEqual(rate_schedules(partial.replace('\nUnavailable',''),annual_only=True),[])

    def test_oversized_terms_are_excluded_instead_of_truncated(self):
        from bs4 import BeautifulSoup
        from worker.native_deposit_records import deposit_table_records
        html='<main><div>Bond Certificates</div><table><tr><th>Term</th><th>Annual rate (%)</th></tr><tr><td>1 Year</td><td>3.5</td></tr></table><p>' + ('Annual terms. '*400) + '</p><p>Early withdrawal terms.</p></main>'
        self.assertEqual(deposit_table_records(BeautifulSoup(html,'html.parser')),[])


    def test_money_sentence_period_is_punctuation_not_a_decimal_fragment(self):
        self.assertTrue(quote_supports_value('monthly_fee',5,'Monthly fee $5.'))
        self.assertTrue(quote_supports_value('minimum_deposit',1000,'Minimum deposit of $1,000.'))
        self.assertFalse(quote_supports_value('monthly_fee',5,'Monthly fee $5.50.'))
        self.assertFalse(quote_supports_value('monthly_fee',5,'Monthly fee $5.5.1.'))

    def test_acquisition_diagnostics_use_complete_named_variants_before_research(self):
        from api_service.collection_evidence_research import assess_captured_essentials
        from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence
        item=_bind_grounding_evidence([captured('gic'),captured('gic-rates','supporting_html')])[0]
        result=assess_captured_essentials(item,run_id='run')
        self.assertEqual(result['missing_fields'],[])
        self.assertEqual(result['resolved_variant_count'],3)
