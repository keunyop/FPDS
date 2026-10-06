from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import MagicMock, patch

from api_service.collection_evidence_research import (
    CapturedPage, EvidenceResearchPlanner, assess_captured_essentials,
    load_research_inputs, MAX_ADDITIONAL_PER_DETAIL, MAX_ADDITIONAL_PER_RUN,
)
from api_service import source_collection_runner as runner
from worker.discovery.fpds_discovery.registry import RegistrySource, SourceRegistry
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractionInput
from worker.pipeline.fpds_extraction.service import _bind_grounding_evidence

ROOT = Path(__file__).resolve().parents[3]


def source(url='https://examplebank.com/ca/everyday', *, country='CA', role='detail', name='Everyday Chequing Account', source_id='detail', product='chequing', extra=None):
    metadata = {'normalized_source_url': url, 'official_domain_allowlist': ['examplebank.com'],
        'product_family': 'deposit', 'discovery_metadata': {'primary_heading': name, 'page_title': name,
            'product_identity_match': True, 'product_type_identity_match': True,
            'detail_identity_confirmed': True, 'page_scope': 'product_detail'}, **(extra or {})}
    return RegistrySource(source_id, 'P0', True, 'html', role, 'fixture', url, url,
                          (), 'en', 'EXAMPLE', country, product, metadata)


def evidence(s, texts=None, html=''):
    context = ExtractionDocumentContext('parsed-' + s.source_id, s.source_document_id, 'snap-' + s.source_id,
        s.bank_code, s.country_code, s.source_type, s.source_language,
        s.to_source_document_record()['source_metadata'], s.source_id)
    texts = texts or [(s.extra_metadata['discovery_metadata']['primary_heading'], 'section'),
                       ('Monthly fee $4.00', 'financial_declaration')]
    chunks = [EvidenceChunkCandidate('chunk-' + s.source_id + '-' + str(i), context.parsed_document_id,
        i, anchor, s.extra_metadata['discovery_metadata']['primary_heading'], None, 'en', text, {},
        context.source_document_id, context.snapshot_id, s.bank_code, s.country_code, 'html')
        for i, (text, anchor) in enumerate(texts)]
    page = CapturedPage(context.source_document_id, context.snapshot_id, context.parsed_document_id,
                        s.normalized_url, html, sha256(html.encode()).hexdigest())
    return ExtractionInput(context, chunks), page


def registry(sources):
    first = sources[0]
    return SourceRegistry('fixture', first.bank_code, first.country_code, first.product_type,
                         'en', ('examplebank.com',), first.source_id, tuple(sources))


class EvidenceResearchTests(unittest.TestCase):
    def plan(self, s=None, *, html=None, inputs=None, pages=None, attempted=None, counts=None, model=None, **kwargs):
        s = s or source()
        html = html or '<main><a href="/ca/account-fee-schedule">Account fee schedule</a></main>'
        item, page = evidence(s, html=html)
        return EvidenceResearchPlanner(invoke_model=model).plan(run_id='run', registry=registry([s]),
            inputs=inputs or [item], captures=pages or [page], attempted_urls=attempted or {s.normalized_url},
            parent_counts=counts if counts is not None else {}, **kwargs)

    def test_required_rate_reserves_observed_current_rates_ahead_of_agreement(self):
        s = source(url='https://examplebank.com/ca/credit-line', product='line-of-credit', name='Example Credit Line')
        html = '<a href="/current-rates.html">Current rates</a><a href="/line-of-credit-agreement.pdf">Line of credit agreement</a>'
        def model(**kw):
            options = json.loads(kw['messages'][-1]['content'])['observed_links']
            choice = next(c['link_id'] for c in options if 'agreement' in c['url'])
            return {'stop': False, 'link_ids': [choice]}, {}
        result = self.plan(s, html=html, model=model)
        self.assertEqual(result['sources'][0]['url'], 'https://examplebank.com/current-rates.html')
        self.assertLessEqual(len(result['sources']), MAX_ADDITIONAL_PER_DETAIL)
        self.assertEqual(result['diagnostics'][0]['required_rate_lead_reserved'], result['sources'][0]['url'])

    def test_other_product_specific_pricing_cannot_displace_shared_current_rates(self):
        s = source(url='https://examplebank.com/ca/savings', product='savings', name='Example Savings')
        result = self.plan(s, html='<a href="/credit-cards/rates">Credit card rates</a><a href="/current-rates.html">Current rates</a>')
        self.assertEqual([r['url'] for r in result['sources']], ['https://examplebank.com/current-rates.html'])

    def test_video_transcript_and_rate_news_are_not_essential_pricing_leads(self):
        s = source(url='https://examplebank.com/ca/mortgage', product='mortgage', name='Example Mortgage')
        result = self.plan(s, html='<a href="/documents/video-transcripts/mortgage-rates.pdf">Mortgage rates</a><a href="/news/mortgage-rates">Mortgage rates</a>')
        self.assertEqual(result['sources'], [])

    def test_missing_ordinary_costs_select_observed_evidence_only_companion(self):
        result = self.plan()
        self.assertEqual(len(result['sources']), 1)
        companion = result['sources'][0]
        self.assertEqual(companion['url'], 'https://examplebank.com/ca/account-fee-schedule')
        self.assertEqual(companion['discovery_role'], 'supporting_html')
        self.assertNotIn('monthly_fee', companion)
        self.assertEqual(companion['discovery_metadata']['parent_detail_url'], source().url)
        self.assertTrue(result['diagnostics'][0]['missing_fields'])

    def test_optional_interest_and_balance_gaps_do_not_trigger_any_call(self):
        s = source()
        item, page = evidence(s, texts=[('Everyday Chequing Account', 'section'),
            ('Monthly fee $4.00', 'financial_declaration'),
            ('Unlimited transactions per month.', 'financial_declaration')],
            html='<a href="/ca/savings-interest-rates">Interest rates</a>')
        model = MagicMock()
        result = self.plan(s, inputs=[item], pages=[page], model=model)
        self.assertEqual(result['sources'], [], result['diagnostics'])
        self.assertEqual(result['diagnostics'][0]['stop_reason'], 'no_essential_gap')
        model.assert_not_called()

    def test_limited_transactions_need_excess_cost_but_unlimited_does_not(self):
        s = source()
        for text, needs in [('18 transactions per month.', True), ('Unlimited transactions per month.', False)]:
            item, _ = evidence(s, texts=[('Everyday Chequing Account', 'section'),
                ('Monthly fee $4.00', 'financial_declaration'), (text, 'financial_declaration')])
            assessment = assess_captured_essentials(_bind_grounding_evidence([item])[0], run_id='run')
            self.assertEqual(bool(assessment['missing_fields']), needs, assessment)

    def test_safe_domain_market_action_and_privacy_filters_precede_model(self):
        html = '''<main><a href="https://evil.test/fees">Pricing fees</a>
            <a href="/us/fees">Pricing fees</a><a href="/apply-now">Pricing fees</a>
            <a href="/privacy-policy">Privacy policy</a><a href="/calculator">Pricing fees</a>
            <a href="/ca/fees">Account fee schedule</a></main>'''
        result = self.plan(html=html)
        self.assertEqual([s['url'] for s in result['sources']], ['https://examplebank.com/ca/fees'])

    def test_country_currency_conflict_stays_an_exclusion(self):
        s = source(country='US', url='https://examplebank.com/us/everyday')
        item, _ = evidence(s, texts=[('Everyday Chequing Account', 'section'),
            ('Monthly fee CAD $4.00', 'financial_declaration'),
            ('Unlimited transactions per month.', 'financial_declaration')])
        assessment = assess_captured_essentials(_bind_grounding_evidence([item])[0], run_id='run')
        self.assertTrue(assessment['missing_fields'] or 'product_currency_unverified' in assessment['reasons'])

    def test_supplied_ids_only_and_no_financial_outputs_from_planner(self):
        def model(**kwargs):
            self.assertFalse(kwargs['require_web_search'])
            self.assertIn('missing_required_fields', kwargs['payload'])
            self.assertNotIn('optional_fields', kwargs['payload'])
            self.assertIn('untrusted', kwargs['instructions'])
            return {'stop': False, 'link_ids': [kwargs['payload']['links'][0]['link_id']]}, {'model_id': 'fixture', 'prompt_tokens': 7}
        result = self.plan(model=model)
        self.assertEqual(result['planner_call_count'], 1)
        self.assertEqual(result['diagnostics'][0]['planner_usage']['prompt_tokens'], 7)
        self.assertEqual(len(result['sources']), 1)

    def test_invalid_foreign_duplicate_and_over_budget_model_ids_cannot_widen_plan(self):
        for ids in [['https://evil.test/fees'], ['invented'], ['invented'] * 3, [[]]]:
            with self.subTest(ids=ids):
                result = self.plan(model=lambda **kw: ({'stop': False, 'link_ids': ids}, {}))
                self.assertEqual(result['diagnostics'][0]['planner_failure'], 'failed_or_invalid_plan')
                self.assertEqual([s['url'] for s in result['sources']], ['https://examplebank.com/ca/account-fee-schedule'])

    def test_model_refusal_stops_without_paid_retry_or_guessed_fact(self):
        model = MagicMock(side_effect=RuntimeError('refused'))
        result = self.plan(model=model)
        model.assert_called_once()
        self.assertEqual(result['planner_call_count'], 1)
        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(result['diagnostics'][0]['planner_failure'], 'failed_or_invalid_plan')

    def test_planner_can_stop_without_forcing_speculative_capture(self):
        result = self.plan(model=lambda **kw: ({'stop': True, 'link_ids': []}, {}))
        self.assertEqual(result['sources'], [])
        self.assertEqual(result['diagnostics'][0]['stop_reason'], 'planner_no_relevant_lead')

    def test_source_and_model_budgets_are_hard_limits(self):
        html = '<main>' + ''.join(f'<a href="/ca/fees-{i}">Account fee schedule</a>' for i in range(60)) + '</main>'
        model = MagicMock()
        result = self.plan(html=html, remaining_sources=1, remaining_model_calls=0, model=model)
        self.assertEqual(len(result['sources']), 1)
        model.assert_not_called()
        result = self.plan(html=html, counts={source().url: MAX_ADDITIONAL_PER_DETAIL})
        self.assertEqual(result['sources'], [])
        self.assertEqual(result['diagnostics'][0]['stop_reason'], 'research_budget_exhausted')

    def test_attempted_or_failed_url_is_not_requested_again(self):
        result = self.plan(attempted={source().url, 'https://examplebank.com/ca/account-fee-schedule'})
        self.assertEqual(result['sources'], [])
        self.assertEqual(result['diagnostics'][0]['stop_reason'], 'no_unvisited_official_lead')

    def test_foreign_or_old_capture_cannot_supply_links(self):
        s = source()
        item, page = evidence(s, html='<a href="/ca/fees">Account fee schedule</a>')
        for changed in [replace(page, snapshot_id='old'), replace(page, parsed_document_id='old'),
                        replace(page, source_document_id='foreign'),
                        replace(page, source_url='https://evil.test/fees')]:
            with self.subTest(page=changed):
                result = self.plan(s, inputs=[item], pages=[changed])
                self.assertEqual(result['sources'], [])

    def test_shared_companion_preserves_all_parent_relationships(self):
        a, b = source(), source(url='https://examplebank.com/ca/other', source_id='other', name='Other Chequing Account')
        inputs, pages = zip(*(evidence(s, html='<a href="/ca/fees">Account fee schedule</a>') for s in [a, b]))
        result = EvidenceResearchPlanner().plan(run_id='run', registry=registry([a, b]), inputs=list(inputs),
            captures=list(pages), attempted_urls={a.url, b.url}, parent_counts={})
        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(set(result['sources'][0]['discovery_metadata']['parent_detail_urls']), {a.url, b.url})

    def test_current_bound_companion_supplies_second_hop_essential_lead(self):
        s = source()
        terms = source(url='https://examplebank.com/ca/terms', role='supporting_html', source_id='terms',
            extra={'discovery_metadata': {'parent_detail_url': s.url, 'parent_detail_urls': [s.url], 'primary_heading': 'Terms'}})
        a, page_a = evidence(s)
        b, page_b = evidence(terms, texts=[('Terms apply to Everyday Chequing Account.', 'section')],
            html='<a href="/ca/fees">Account fee schedule</a>')
        result = EvidenceResearchPlanner().plan(run_id='run', registry=registry([s, terms]), inputs=[a, b],
            captures=[page_a, page_b], attempted_urls={s.url, terms.url}, parent_counts={})
        self.assertEqual(result['sources'][0]['url'], 'https://examplebank.com/ca/fees')
        self.assertEqual(result['sources'][0]['discovery_metadata']['observed_on_url'], terms.url)

    def test_configured_extra_required_field_can_request_terms(self):
        s = source(extra={'collection_field_policy': {'CA': {'required_fields': ['eligibility_text'], 'optional_fields': []}}})
        item, page = evidence(s, texts=[('Everyday Chequing Account', 'section'),
            ('Monthly fee $4.00', 'financial_declaration'), ('Unlimited transactions per month.', 'financial_declaration')],
            html='<a href="/ca/account-terms">Account terms</a>')
        result = self.plan(s, inputs=[item], pages=[page])
        self.assertIn('eligibility_text', result['diagnostics'][0]['missing_fields'])
        self.assertEqual(len(result['sources']), 1)

    def test_gic_with_prohibited_access_needs_no_invented_penalty(self):
        s = source(product='gic', name='Everyday GIC', url='https://examplebank.com/ca/gic')
        item, _ = evidence(s, texts=[('Everyday GIC', 'section'),
            ('1 year GIC pays 3.50% per annum.', 'section'),
            ('This GIC is non-redeemable.', 'financial_declaration')])
        assessment = assess_captured_essentials(_bind_grounding_evidence([item])[0], run_id='run')
        self.assertNotIn('early_withdrawal_penalty', assessment['missing_fields'])

    def test_actual_localized_legal_lead_is_available_for_missing_savings_basis(self):
        url = 'https://www.haventreebank.com/en-CA/accounts/everyday-growth-account'
        base = source(url=url, product='savings', name='Everyday Growth Account')
        s = replace(base, bank_code='HAVENTREE', extra_metadata={**base.extra_metadata,
            'official_domain_allowlist': ['haventreebank.com']})
        html = (ROOT/'worker/pipeline/tests/fixtures/collection-research/haventree_legal_lead.html').read_text(encoding='utf8')
        item, page = evidence(s, texts=[('Everyday Growth Account', 'section'),
            ('No monthly fee.', 'financial_declaration'), ('Interest rate 2.50%.', 'section')], html=html)
        reg = replace(registry([s]), allowed_domains=('haventreebank.com',))
        result = EvidenceResearchPlanner().plan(run_id='run', registry=reg, inputs=[item], captures=[page],
            attempted_urls={url}, parent_counts={})
        self.assertIn('standard_rate', result['diagnostics'][0]['missing_fields'])
        self.assertEqual(result['sources'][0]['url'], 'https://www.haventreebank.com/en-CA/legal')
        self.assertNotIn('standard_rate', result['sources'][0])

    def test_actual_cibc_pricing_link_survives_unrelated_navigation_and_selects_exact_pdf(self):
        url = 'https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/adapta-mastercard.html'
        s = replace(source(url=url, name='CIBC Adapta Mastercard'), bank_code='CIBC',
                    product_type='credit-card', extra_metadata={**source().extra_metadata,
                        'official_domain_allowlist': ['cibc.com'], 'normalized_source_url': url,
                        'discovery_metadata': {'primary_heading': 'CIBC Adapta Mastercard', 'product_identity_match': True}})
        html = (ROOT/'worker/pipeline/tests/fixtures/golden/cibc_card_pricing_companion_dom.html').read_text(encoding='utf8')
        item, page = evidence(s, texts=[('CIBC Adapta Mastercard', 'section')], html=html)
        reg = replace(registry([s]), allowed_domains=('cibc.com',))
        result = EvidenceResearchPlanner().plan(run_id='run', registry=reg, inputs=[item], captures=[page],
            attempted_urls={url}, parent_counts={})
        self.assertEqual(len(result['sources']), 1, result['diagnostics'])
        self.assertTrue(result['sources'][0]['url'].endswith('cibc-creditcard-annual-interest-rate-fees-11995-en.pdf'))
        self.assertEqual(result['sources'][0]['discovery_role'], 'linked_pdf')


class ResearchCaptureLoadingTests(unittest.TestCase):
    def test_snapshot_parse_country_and_raw_checksum_are_pinned(self):
        s = source()
        html = b'<a href="/ca/fees">Account fee schedule</a>'
        row = {'source_document_id': s.source_document_id, 'bank_code': s.bank_code, 'country_code': s.country_code,
            'source_type': 'html', 'source_language': 'en', 'source_metadata': {'product_type': 'wrong', 'collection_field_policy': {}},
            'snapshot_id': 'snap', 'parsed_document_id': 'parsed', 'checksum': sha256(html).hexdigest(),
            'object_storage_key': 'private/raw', 'content_type': 'text/html'}
        connection = MagicMock()
        connection.execute.side_effect = [MagicMock(fetchall=lambda: [row]), MagicMock(fetchall=lambda: [])]
        store = MagicMock(get_object_bytes=lambda **kw: html)
        inputs, captures, errors = load_research_inputs(connection, run_id='run', registry=registry([s]), source_ids=[s.source_id], object_store=store)
        self.assertEqual(errors, [])
        self.assertEqual(inputs[0].context.source_metadata['product_type'], 'chequing')
        self.assertEqual(captures[0].checksum, row['checksum'])
        sql = connection.execute.call_args_list[0].args[0]
        self.assertIn('rsi.selected_snapshot_id', sql)
        self.assertIn("rsi.stage_metadata->>'parsed_document_id'", sql)
        self.assertIn('rsi.error_count = 0', sql)

    def test_checksum_mismatch_removes_raw_link_capture_without_stale_fallback(self):
        s = source()
        row = {'source_document_id': s.source_document_id, 'bank_code': s.bank_code, 'country_code': s.country_code,
            'source_type': 'html', 'source_language': 'en', 'source_metadata': {}, 'snapshot_id': 'snap',
            'parsed_document_id': 'parsed', 'checksum': 'wrong', 'object_storage_key': 'private/raw', 'content_type': 'text/html'}
        connection = MagicMock()
        connection.execute.side_effect = [MagicMock(fetchall=lambda: [row]), MagicMock(fetchall=lambda: [])]
        inputs, captures, errors = load_research_inputs(connection, run_id='run', registry=registry([s]), source_ids=[s.source_id],
            object_store=MagicMock(get_object_bytes=lambda **kw: b'current'))
        self.assertEqual(captures, [])
        self.assertEqual(errors[0]['reason'], 'capture_read_or_checksum_failure')


class ResearchRunnerTests(unittest.TestCase):
    def test_normal_admin_run_researches_before_single_extraction_and_preserves_targets(self):
        s = source()
        planned = {'source_id': 'proof', 'url': 'https://examplebank.com/ca/fees', 'discovery_role': 'supporting_html'}
        group = {'run_id': 'run', 'bank_code': 'EXAMPLE', 'country_code': 'CA',
            'product_type': 'chequing', 'source_language': 'en', 'included_source_ids': ['detail'],
            'target_source_ids': ['detail'], 'included_sources': [{'source_id': 'detail', 'priority': 'P0',
                'seed_source_flag': True, 'source_type': 'html', 'discovery_role': 'detail', 'purpose': 'fixture',
                'source_url': s.url, 'expected_fields': [], 'source_language': 'en'}]}
        plans = [{'sources': [planned], 'planner_call_count': 0, 'diagnostics': []},
                 {'sources': [], 'planner_call_count': 0, 'diagnostics': []}]
        calls = []
        def stage(module, args):
            calls.append((module, list(args)))
            ids = [args[i + 1] for i, x in enumerate(args) if x == '--source-id']
            field, action = ('snapshot_action', 'stored') if 'snapshot' in module else ('parse_action', 'stored')
            if 'fpds_extraction' in module:
                field = 'extraction_action'
            elif 'fpds_normalization' in module:
                field = 'normalization_action'
            elif 'fpds_validation' in module:
                field, action = 'validation_action', 'auto_validated'
            return {'source_results': [{'source_id': sid, field: action} for sid in ids]}
        with TemporaryDirectory() as tmp, patch.object(runner, 'args_temp_dir', return_value=Path(tmp)), \
             patch.object(runner, '_resolve_env_file', return_value=None), patch.object(runner, 'open_connection'), \
             patch.object(runner.Settings, 'from_env'), patch.object(runner, 'plan_collection_evidence_research', side_effect=plans), \
             patch.object(runner, '_persist_evidence_research_receipt'), patch.object(runner, '_run_stage', side_effect=stage), \
             patch.object(runner, '_persist_end_to_end_source_summary') as summary, \
             patch.object(runner, '_supersede_stale_logical_reviews_for_run', return_value=0), \
             patch.object(runner, '_supersede_reviews_covered_by_approved_candidates_for_run', return_value=0), \
             patch.object(runner, '_promote_auto_validated_candidates_for_run', return_value={'promoted_count': 0}):
            runner._run_group(plan={}, group=group)
        self.assertEqual([module.rsplit('.', 1)[-1] for module, _ in calls],
            ['fpds_snapshot', 'fpds_parse_chunk', 'fpds_snapshot', 'fpds_parse_chunk',
             'fpds_extraction', 'fpds_normalization', 'fpds_validation_routing'])
        self.assertIn('proof', calls[4][1])
        self.assertNotIn('proof', calls[5][1])
        self.assertNotIn('proof', calls[6][1])
        self.assertEqual(summary.call_args.kwargs['summary']['source_scope_count'], 2)
        self.assertEqual(summary.call_args.kwargs['summary']['source_failure_count'], 0)

    def test_two_capture_parse_waves_feed_final_extraction_without_target_expansion(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/'registry.json'
            base = {'sources': [{'source_id': 'detail', 'url': 'https://examplebank.com/ca/everyday'}]}
            path.write_text(json.dumps(base), encoding='utf8')
            plans = [{'sources': [{'source_id': f'proof-{i}', 'url': f'https://examplebank.com/ca/fees-{i}'}],
                      'planner_call_count': 1, 'diagnostics': []} for i in range(2)]
            plans.append({'sources': [], 'planner_call_count': 0, 'diagnostics': []})
            def stage(module, args):
                sid = args[args.index('--source-id') + 1]
                if 'snapshot' in module:
                    return {'source_results': [{'source_id': sid, 'snapshot_action': 'stored'}]}
                return {'source_results': [{'source_id': sid, 'parse_action': 'stored'}]}
            manager = MagicMock()
            with patch.object(runner, 'open_connection', return_value=manager), patch.object(runner.Settings, 'from_env'), \
                 patch.object(runner, 'plan_collection_evidence_research', side_effect=plans) as planner, \
                 patch.object(runner, '_persist_evidence_research_receipt') as receipt, patch.object(runner, '_run_stage', side_effect=stage) as stages:
                successful, added = runner._research_essential_evidence(run_id='run', registry_path=path,
                    base_args=['--run-id', 'run'], parsed_source_ids=['detail'])
            self.assertEqual(successful, ['detail', 'proof-0', 'proof-1'])
            self.assertEqual(added, ['proof-0', 'proof-1'])
            self.assertEqual(stages.call_count, 4)
            self.assertEqual(planner.call_args.kwargs['remaining_sources'], 0)
            self.assertEqual(receipt.call_args.kwargs['model_calls'], 2)
            self.assertEqual(len(json.loads(path.read_text())['sources']), 3)

    def test_failed_research_capture_retains_original_success_and_diagnostic(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/'registry.json'
            path.write_text(json.dumps({'sources': [{'source_id': 'detail', 'url': 'https://examplebank.com/ca/everyday'}]}), encoding='utf8')
            plans = [{'sources': [{'source_id': 'proof', 'url': 'https://examplebank.com/ca/fees'}], 'planner_call_count': 0},
                     {'sources': [], 'planner_call_count': 0}]
            with patch.object(runner, 'open_connection'), patch.object(runner.Settings, 'from_env'), \
                 patch.object(runner, 'plan_collection_evidence_research', side_effect=plans), \
                 patch.object(runner, '_persist_evidence_research_receipt') as persist, \
                 patch.object(runner, '_run_stage', side_effect=runner.WorkerStageError(stage_name='snapshot', failure_kind='timeout', timeout_seconds=90)):
                successful, added = runner._research_essential_evidence(run_id='run', registry_path=path, base_args=[], parsed_source_ids=['detail'])
            self.assertEqual(successful, ['detail'])
            self.assertEqual(added, ['proof'])
            self.assertIn('capture_stage_failure', persist.call_args.kwargs['rounds'][0])


if __name__ == '__main__':
    unittest.main()
