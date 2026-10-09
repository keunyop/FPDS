"""Acquisition -> ordinary extraction/normalization/routing, using official captures.

No provider or database writes. Snapshot/parse origins are fixture-pinned rather
than a claim about fresh deployed Admin yield.
"""
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT/'api/service') not in sys.path:
    sys.path.insert(0, str(ROOT/'api/service'))
from api_service.collection_evidence_research import CapturedPage, EvidenceResearchPlanner
from worker.discovery.fpds_discovery.registry import RegistrySource, SourceRegistry
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractionInput
from worker.pipeline.fpds_extraction.service import ExtractionService, _bind_grounding_evidence
from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig, build_object_store
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes, _pdf_purchase_rate_cells
from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
from worker.pipeline.fpds_normalization.service import NormalizationService
from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig
from worker.pipeline.fpds_validation_routing.models import ValidationInput, ValidationEvidenceLink, ValidationRoutingConfig
from worker.pipeline.fpds_validation_routing.service import ValidationRoutingService
from worker.pipeline.fpds_validation_routing.storage import ValidationRoutingStorageConfig

FIXTURES = Path(__file__).parent/'fixtures/golden'


def input_from_segments(*, bank, url, product, name, segments, role='detail', parent=None, ident='detail', country='CA'):
    metadata = {'normalized_source_url': url, 'official_domain_allowlist': [url.split('/')[2].removeprefix('www.')],
        'product_type': product, 'product_family': 'card' if product == 'credit-card' else 'deposit',
        'discovery_role': role, 'expected_fields': [], 'discovery_metadata': {
            'primary_heading': name, 'page_title': name, 'product_identity_match': True,
            'parent_detail_url': parent, 'parent_detail_urls': [parent] if parent else []}}
    ctx = ExtractionDocumentContext('parsed-' + ident, 'doc-' + ident, 'snapshot-' + ident,
        bank, country, 'pdf' if url.endswith('.pdf') else 'html', 'en', metadata, ident)
    chunks = [EvidenceChunkCandidate(ident+'-'+str(i), ctx.parsed_document_id, i, segment.anchor_type,
        segment.anchor_value, segment.page_no, 'en', segment.text, {}, ctx.source_document_id,
        ctx.snapshot_id, bank, country, ctx.source_type) for i, segment in enumerate(segments)]
    return ExtractionInput(ctx, chunks)


def run_services(inputs, *, provider=False):
    """Use ordinary services and the actual captured full-context origin map."""
    detail = inputs[0]
    ctx = detail.context
    with TemporaryDirectory() as tmp, \
         patch('worker.pipeline.fpds_extraction.service.llm_provider_configured', return_value=provider), \
         patch('worker.pipeline.fpds_normalization.service.llm_provider_configured', return_value=False):
        ecfg = ExtractionStorageConfig('filesystem', 'test', 'extracted', 'hot', filesystem_root=tmp)
        extraction = ExtractionService(storage_config=ecfg, object_store=build_object_store(ecfg)).extract_documents(
            run_id='run', inputs=inputs).source_results[0]
        if extraction.extraction_action != 'stored':
            raise AssertionError(extraction.error_summary)
        bound = _bind_grounding_evidence(inputs)[0]
        origins = {c.evidence_chunk_id: {'run_id': 'run', 'bank_code': c.bank_code, 'country_code': c.country_code,
            'source_document_id': c.source_document_id, 'snapshot_id': c.source_snapshot_id,
            'parsed_document_id': c.parsed_document_id, 'evidence_chunk_id': c.evidence_chunk_id,
            'evidence_excerpt': c.evidence_excerpt, 'source_url': c.retrieval_metadata['source_url'],
            'anchor_type': c.anchor_type, 'anchor_value': c.anchor_value}
            for c in bound.grounding_candidates}
        from worker.pipeline.fpds_normalization.__main__ import _build_normalization_input
        from worker.pipeline.fpds_normalization.models import NormalizationArtifactLookup
        from worker.pipeline.fpds_normalization.persistence import PsqlNormalizationRepository, NormalizationDatabaseConfig
        artifact = json.loads(build_object_store(ecfg).get_object_bytes(object_key=extraction.extracted_storage_key))
        lookup = NormalizationArtifactLookup(ctx.source_document_id, ctx.snapshot_id, ctx.parsed_document_id,
            extraction.model_execution_id, extraction.extracted_storage_key, None, ctx.bank_code, ctx.country_code,
            ctx.source_type, 'en', ctx.source_metadata, ctx.source_metadata['normalized_source_url'])
        item = _build_normalization_input(source_id=ctx.source_id, lookup=lookup, artifact=artifact)
        repo = PsqlNormalizationRepository(NormalizationDatabaseConfig('postgresql://fixture', 'public'))
        repo._resolved_schema = 'public'
        def query_origins(sql, variables):
            assert variables['run_id'] == 'run'
            assert "rsi.error_count = 0" in sql and "rsi.selected_snapshot_id = ss.snapshot_id" in sql
            ids = json.loads(variables['chunk_ids_json'])
            return json.dumps([origins[i] for i in ids if i in origins])
        with patch.object(repo, '_execute', side_effect=query_origins):
            item = repo.resolve_evidence_origins(run_id='run', inputs=[item])[0]
        links = item.evidence_links
        ncfg = NormalizationStorageConfig('filesystem', 'test', 'normalized', 'hot', filesystem_root=tmp)
        normalization_result = NormalizationService(storage_config=ncfg, object_store=build_object_store(ncfg)).normalize_inputs(
            run_id='run', inputs=[item])
        normalization = normalization_result.source_results[0]
        from worker.pipeline.fpds_normalization.models import normalization_field_flow
        assert normalization_result.to_dict()['source_results'][0]['field_flow'] == normalization_field_flow(normalization.normalized_candidate_record)
        if normalization.normalization_action != 'stored':
            raise AssertionError(normalization.error_summary)
        record = normalization.normalized_candidate_record
        evidence_links = [ValidationEvidenceLink(**row) for row in normalization.field_evidence_link_records]
        vi = ValidationInput(ctx.source_id, ctx.source_document_id, ctx.snapshot_id, ctx.parsed_document_id,
            record['candidate_id'], 'run', normalization.normalization_model_execution_id,
            normalization.normalized_storage_key, None, ctx.bank_code, ctx.country_code, ctx.source_type, 'en',
            ctx.source_metadata, record, evidence_links, [])
        vcfg = ValidationRoutingStorageConfig('filesystem', 'test', 'validated', 'hot', filesystem_root=tmp)
        validation = ValidationRoutingService(storage_config=vcfg, object_store=build_object_store(vcfg)).validate_and_route_inputs(
            run_id='run', inputs=[vi], taxonomy_registry={str(record['product_type']): {str(record['subtype_code'])}},
            routing_config=ValidationRoutingConfig('phase1', .85, .6, set())).source_results[0]
        return record, validation, extraction


class OrdinaryEvidenceParityTests(unittest.TestCase):
    def cibc(self):
        url = 'https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/adapta-mastercard.html'
        name = 'CIBC Adapta™ Mastercard®'
        # Exact native title and prices from the original official capture.
        body = (FIXTURES/'cibc_adapta_pricing_dom.html').read_bytes()
        segments = parse_snapshot_bytes(body=body, content_type='text/html').segments
        item = input_from_segments(bank='CIBC', url=url, product='credit-card', name=name, segments=segments)
        link_html = (FIXTURES/'cibc_card_pricing_companion_dom.html').read_text(encoding='utf8')
        page = CapturedPage(item.context.source_document_id, item.context.snapshot_id, item.context.parsed_document_id,
                            url, link_html, sha256(link_html.encode()).hexdigest())
        s = RegistrySource('detail', 'P0', True, 'html', 'detail', 'source-backed test', url, url, (), 'en', 'CIBC', 'CA',
                           'credit-card', item.context.source_metadata)
        reg = SourceRegistry('fixture', 'CIBC', 'CA', 'credit-card', 'en', ('cibc.com',), 'detail', (s,))
        plan = EvidenceResearchPlanner().plan(run_id='run', registry=reg, inputs=[item], captures=[page],
            attempted_urls={url}, parent_counts={})
        return item, plan

    def test_actual_card_disclosure_is_acquired_and_passes_ordinary_services(self):
        item, plan = self.cibc()
        before, rejected, _ = run_services([item])
        self.assertEqual(rejected.validation_action, 'excluded')
        self.assertNotIn('purchase_interest_rate', before['candidate_payload'])
        self.assertEqual(len(plan['sources']), 1)
        pdf = plan['sources'][0]['url']
        layout = (FIXTURES/'cibc_annual_card_purchase_layout.txt').read_text(encoding='utf8')
        companion = input_from_segments(bank='CIBC', url=pdf, product='credit-card', name='Annual rates and fees',
            segments=_pdf_purchase_rate_cells(layout, page_no=1), role='linked_pdf', parent=item.context.source_metadata['normalized_source_url'], ident='rates')
        after, approved, extraction = run_services([item, companion])
        self.assertEqual(approved.validation_action, 'auto_validated', approved.validation_issue_codes)
        self.assertIsNone(approved.review_task_record)
        self.assertEqual(after['candidate_payload']['annual_fee'], 0)
        self.assertEqual(after['candidate_payload']['purchase_interest_rate'], 21.99)
        fact = next(f for f in extraction.extracted_fields if f.field_name == 'purchase_interest_rate')
        self.assertEqual(fact.source_document_id, companion.context.source_document_id)
        self.assertIn('Purchases', fact.evidence_text_excerpt)
        self.assertNotIn('22.99%', fact.evidence_text_excerpt)

    def test_real_action_seo_title_cannot_erase_owned_product_price_and_pdf_proof(self):
        item, plan = self.cibc()
        metadata = {**item.context.source_metadata, 'discovery_metadata': {
            **item.context.source_metadata['discovery_metadata'],
            'page_title': 'Apply for the CIBC Adapta Mastercard | CIBC'}}
        item = replace(item, context=replace(item.context, source_metadata=metadata))
        layout = (FIXTURES/'cibc_annual_card_purchase_layout.txt').read_text(encoding='utf8')
        companion = input_from_segments(bank='CIBC', url=plan['sources'][0]['url'], product='credit-card', name='Annual rates and fees',
            segments=_pdf_purchase_rate_cells(layout, page_no=1), role='linked_pdf',
            parent=item.context.source_metadata['normalized_source_url'], ident='rates')
        record, validation, _ = run_services([item, companion])
        self.assertEqual(validation.validation_action, 'auto_validated', record['candidate_payload']['_collection_accuracy'])
        self.assertEqual(record['candidate_payload']['purchase_interest_rate'], 21.99)

    def test_native_h1_proof_requires_owned_price_main_section_and_non_action_route(self):
        from worker.pipeline.fpds_extraction.service import _captured_native_product_title
        item, _ = self.cibc()
        meta = {**item.context.source_metadata, 'discovery_metadata': {
            **item.context.source_metadata['discovery_metadata'], 'page_title': 'Apply for the CIBC Adapta Mastercard | CIBC'}}
        ctx = replace(item.context, source_metadata=meta)
        self.assertEqual(_captured_native_product_title(ctx, item.candidates), meta['discovery_metadata']['primary_heading'])
        bad_sets = [
            [replace(c, bank_code='OTHER') for c in item.candidates],
            [replace(c, source_snapshot_id='old') for c in item.candidates],
            [replace(c, source_language='fr') for c in item.candidates],
            [c for c in item.candidates if c.anchor_type != 'section'],
            [c for c in item.candidates if c.anchor_type != 'labelled_financial_record'],
        ]
        for chunks in bad_sets:
            self.assertIsNone(_captured_native_product_title(ctx, chunks))
        for changes in [{'normalized_source_url': 'https://www.cibc.com/application/adapta-mastercard'},
                        {'normalized_source_url': 'https://www.cibc.com/credit-cards/another-card'},
                        {'discovery_metadata': {**meta['discovery_metadata'], 'multi_product_family_overview': True}}]:
            self.assertIsNone(_captured_native_product_title(replace(ctx, source_metadata={**meta, **changes}), item.candidates))

    def test_missing_annual_note_or_wrong_bank_companion_retains_exclusion(self):
        item, plan = self.cibc()
        layout = (FIXTURES/'cibc_annual_card_purchase_layout.txt').read_text(encoding='utf8')
        for bank, text in [('CIBC', layout.split('1 These interest rates')[0]), ('OTHER', layout)]:
            with self.subTest(bank=bank):
                companion = input_from_segments(bank=bank, url=plan['sources'][0]['url'], product='credit-card', name='Rates',
                    segments=_pdf_purchase_rate_cells(text, page_no=1), role='linked_pdf',
                    parent=item.context.source_metadata['normalized_source_url'], ident='rates')
                _, validation, _ = run_services([item, companion])
                self.assertEqual(validation.validation_action, 'excluded')
                self.assertIsNone(validation.review_task_record)

    def test_independent_annual_basis_survives_actual_extraction_artifact_and_origin_resolution(self):
        from types import SimpleNamespace
        saved = json.loads((Path(__file__).parent/'fixtures/collection-research/haventree_rate_capture.json').read_text(encoding='utf8'))
        detail = input_from_segments(bank='HAVENTREE', url=saved['official_url'], product='savings',
            name='Everyday Growth Account', segments=[SimpleNamespace(**c) for c in saved['chunks']])
        detail = replace(detail, context=replace(detail.context, source_metadata={**detail.context.source_metadata,
            'discovery_metadata': {**detail.context.source_metadata['discovery_metadata'],
                'primary_heading': 'Grow your money with 2.50%* interest'}}))
        basis = input_from_segments(bank='HAVENTREE', url='https://www.haventreebank.com/en-CA/legal', product='savings',
            name='Legal', role='supporting_html', parent=saved['official_url'], ident='basis',
            segments=parse_snapshot_bytes(body=(Path(__file__).parent/'fixtures/native-product-sections/named-rate-basis.html').read_bytes(),
                content_type='text/html').segments)
        _, missing, _ = run_services([detail])
        self.assertEqual(missing.validation_action, 'excluded')
        record, validated, extracted = run_services([detail, basis])
        self.assertEqual(validated.validation_action, 'auto_validated', record['candidate_payload']['_collection_accuracy'])
        self.assertEqual(record['candidate_payload']['standard_rate'], 2.5)
        source = RegistrySource('detail', 'P0', True, 'html', 'detail', 'source-backed', saved['official_url'],
            saved['official_url'], (), 'en', 'HAVENTREE', 'CA', 'savings', detail.context.source_metadata)
        reg = SourceRegistry('fixture', 'HAVENTREE', 'CA', 'savings', 'en', ('haventreebank.com',), 'detail', (source,))
        model = unittest.mock.MagicMock()
        plan = EvidenceResearchPlanner(invoke_model=model).plan(run_id='run', registry=reg,
            inputs=[detail, basis], captures=[], attempted_urls={saved['official_url']}, parent_counts={})
        self.assertEqual(plan['diagnostics'][0]['stop_reason'], 'no_essential_gap')
        model.assert_not_called()
        rate = next(f for f in extracted.extracted_fields if f.field_name == 'standard_rate')
        basis_id = rate.field_metadata['annual_basis_evidence_chunk_id']
        link = next(x for x in extracted.evidence_links if x.evidence_chunk_id == basis_id and x.field_name == 'standard_rate')
        self.assertEqual(link.source_document_id, basis.context.source_document_id)
        self.assertEqual(link.source_snapshot_id, basis.context.snapshot_id)
        self.assertIn('rates per annum', link.evidence_text_excerpt)
        self.assertIn('last business day', link.evidence_text_excerpt)
        # Origin lookup is driven by artifact links, as in the production CLI.
        self.assertTrue(basis_id)
        bad = replace(basis, candidates=[replace(c, anchor_value='Other Account') if c.anchor_type == 'named_product_rate_basis' else c for c in basis.candidates])
        _, excluded, _ = run_services([detail, bad])
        self.assertEqual(excluded.validation_action, 'excluded')

    def test_actual_other_bank_account_stays_complete_without_optional_research(self):
        saved = json.loads((FIXTURES/'coast_collection_evidence_2026_10_03.json').read_text(encoding='utf8'))['products'][0]
        ctx = ExtractionDocumentContext('parsed-detail', 'doc-detail', 'snapshot-detail', 'CCS', 'CA', 'html', 'en',
            {**saved['metadata'], 'normalized_source_url': saved['url']}, 'detail')
        chunks = [EvidenceChunkCandidate(**c, parsed_document_id=ctx.parsed_document_id,
            source_document_id=ctx.source_document_id, source_snapshot_id=ctx.snapshot_id,
            bank_code='CCS', country_code='CA', source_type='html') for c in saved['chunks']]
        item = ExtractionInput(ctx, chunks)
        record, validation, _ = run_services([item])
        self.assertEqual(validation.validation_action, 'auto_validated', validation.validation_issue_codes)
        self.assertEqual(record['candidate_payload']['monthly_fee'], 0)
        self.assertEqual(record['candidate_payload']['unlimited_transactions_flag'], True)
        s = RegistrySource('detail', 'P0', True, 'html', 'detail', 'source-backed', saved['url'], saved['url'], (), 'en', 'CCS', 'CA', 'chequing', ctx.source_metadata)
        reg = SourceRegistry('fixture', 'CCS', 'CA', 'chequing', 'en', ('coastcapitalsavings.com',), 'detail', (s,))
        plan = EvidenceResearchPlanner().plan(run_id='run', registry=reg, inputs=[item], captures=[],
            attempted_urls={saved['url']}, parent_counts={})
        self.assertEqual(plan['sources'], [])
        self.assertEqual(plan['diagnostics'][0]['stop_reason'], 'no_essential_gap')


if __name__ == '__main__':
    unittest.main()
