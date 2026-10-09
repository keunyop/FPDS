"""Immutable official DOMs and independent product/rate expectations."""
from pathlib import Path
import hashlib,json,unittest,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"api/service"))
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
FIX=Path(__file__).parent/'fixtures/us-account-proof'
class USOfficialProofTests(unittest.TestCase):
 def parse(self,name):return parse_snapshot_bytes(body=(FIX/(name+'.html.bin')).read_bytes(),content_type='text/html').segments
 def test_source_bytes_are_immutable(self):
  for r in json.loads((FIX/'sources.json').read_text(encoding='utf8')):self.assertEqual(hashlib.sha256((FIX/r['fixture']).read_bytes()).hexdigest(),r['sha256'])
 def test_actual_svg_accessible_hysa_and_cd_headings_survive(self):
  for fixture,expected in [('amex-hysa','American Express High Yield Savings'),('amex-cd','American Express Certificate of Deposit')]:
   self.assertTrue(any(s.anchor_type=='document_heading' and s.text==expected for s in self.parse(fixture)))
 def test_actual_owned_monthly_maintenance_row_is_complete(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  records=[s for s in self.parse('ally-savings') if s.anchor_type=='owned_account_assertion']
  self.assertTrue(any(s.anchor_value=='Ally Bank Savings Account' and 'Monthly maintenance fees\n$0' in s.text and quote_supports_value('monthly_fee',0,s.text) for s in records))
 def test_actual_named_apy_component_retains_literal_detail_link_and_disclosure(self):
  records=[s for s in self.parse('ally-rates') if s.anchor_type=='named_deposit_apy']
  self.assertTrue(any(s.anchor_value=='Savings' and '3.1%' in s.text and '/bank/online-savings-account/' in s.text and 'No minimum balance required to open an account or earn APY.' in s.text for s in records))
 def test_actual_us_savings_passes_same_artifact_origin_services(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  detail=input_from_segments(bank='AB',country='US',url='https://www.ally.com/bank/online-savings-account',product='savings',name='Ally Bank Savings Account',segments=self.parse('ally-savings'))
  rates=input_from_segments(bank='AB',country='US',url='https://www.ally.com/bank/savings-account-rates',product='savings',name='Compare Savings',segments=self.parse('ally-rates'),role='supporting_html',parent=detail.context.source_metadata['normalized_source_url'],ident='rates')
  record,validated,extracted=run_services([detail,rates])
  self.assertEqual(validated.validation_action,'auto_validated',record['candidate_payload']['_collection_accuracy'])
  self.assertEqual(record['currency'],'USD')
  self.assertEqual(record['candidate_payload']['standard_rate'],3.1)
  self.assertEqual(record['candidate_payload']['monthly_fee'],0)
  self.assertIn('Annual Percentage Yield',record['candidate_payload']['interest_rate_summary'])
  self.assertTrue(any(f.field_name=='standard_rate' and f.source_document_id==rates.context.source_document_id for f in extracted.extracted_fields))

class FinancialTemplateAcquisitionTests(unittest.TestCase):
 def test_actual_card_attribute_template_requests_required_render(self):
  from api_service.collection_evidence_research import _has_required_dynamic_lead
  html=(FIX/'bofa-card.html.bin').read_text(encoding='utf8')
  self.assertTrue(_has_required_dynamic_lead(html,['purchase_interest_rate_summary']))
  self.assertFalse(_has_required_dynamic_lead(html,[]))
class RenderedOfficialProofTests(unittest.TestCase):
 parse=USOfficialProofTests.parse
 def test_actual_heading_annual_fee_is_a_label_not_another_product(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  self.assertTrue(any(s.anchor_type=='labelled_financial_record' and quote_supports_value('annual_fee',0,s.text) for s in self.parse('bofa-card-rendered')))
 def test_actual_referenced_hero_apy_has_complete_literal_note(self):
  records=[s for s in self.parse('amex-hysa-rendered') if s.anchor_type=='owned_referenced_apy']
  self.assertTrue(any('3.10% APY²' in s.text and 'before and after a High Yield Savings Account is opened' in s.text for s in records))
 def test_actual_card_summary_keeps_intro_and_current_range_without_scalar(self):
  records=[s for s in self.parse('bofa-card-rendered') if s.anchor_type=='owned_card_apr_offer']
  self.assertTrue(any('15 billing cycles' in s.text and '17.74%' in s.text and '27.74%' in s.text and '60 days' in s.text for s in records))
class GenericProofBoundaryTests(unittest.TestCase):
 def segments(self,html):return parse_snapshot_bytes(body=html.encode(),content_type='text/html').segments
 def test_discovery_and_parser_share_accessible_identity_without_svg_title_pollution(self):
  from api_service.source_catalog import _PageSignalParser
  for name in ['Example High Yield Savings','Example Certificate of Deposit']:
   html=f'<head><title>Official product</title></head><main><h1></h1><h1><svg role="img"><title>{name}</title><path/></svg></h1></main>'
   parser=_PageSignalParser();parser.feed(html)
   self.assertEqual(parser.title_text,'Official product')
   self.assertEqual(parser.primary_heading,name)
   self.assertTrue(any(x.anchor_type=='document_heading' and x.text==name for x in self.segments(html)))
 def test_hidden_ambiguous_or_conflicting_svg_never_establishes_product(self):
  from api_service.source_catalog import _PageSignalParser
  for graphic in ['<svg aria-hidden="true"><title>Other Savings</title></svg>', '<svg role="presentation"><title>Other Savings</title></svg>', '<svg aria-label="Other"><title>Other Savings</title></svg>', '<svg><title>First Savings</title><title>Second Savings</title></svg>']:
   html='<title>Official</title><main><h1>'+graphic+'</h1><p>No monthly fees.</p></main>'
   parser=_PageSignalParser();parser.feed(html)
   self.assertEqual(parser.title_text,'Official')
   self.assertEqual(parser.primary_heading,'')
   self.assertFalse(any(x.anchor_type=='owned_account_assertion' for x in self.segments(html)))
 def test_audience_is_product_name_but_fee_conditions_still_fail(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  for name in ['Example Credit Card for Students','Example Visa for Seniors']:
   self.assertTrue(quote_supports_value('annual_fee',0,name+'\nAnnual Fee\n$0'))
   for condition in ['Only for eligible students.','For the first six months.','If you maintain a $5000 balance.']:
    self.assertFalse(quote_supports_value('annual_fee',0,name+'\nAnnual Fee\n$0\n'+condition))
  self.assertFalse(quote_supports_value('annual_fee',0,'Example Credit Card\nAnnual fee\n$0 for students'))
 def test_financial_heading_remains_label_and_foreign_product_is_rejected(self):
  for label,accepted in [('Annual fee',True),('Other Rewards Credit Card',False)]:
   html=f'<main><h1>Example Rewards Credit Card</h1><section><h3>{label}</h3>'+(('<p>$0</p>') if accepted else '<p>Annual fee</p><p>$0</p>')+'</section></main>'
   self.assertEqual(any(x.anchor_type=='labelled_financial_record' for x in self.segments(html)),accepted)
 def test_json_placeholders_are_bounded_acquisition_leads_only(self):
  import html,json
  from worker.dynamic_pricing import has_literal_financial_template
  def attr(value):return '<div data-template="'+html.escape(value,quote=True)+'"></div>'
  rate=attr(json.dumps({'header':'Purchase APR','content':'{{currentAPR}}'}))
  self.assertTrue(has_literal_financial_template(rate))
  self.assertFalse(has_literal_financial_template(rate,kind='fee'))
  self.assertTrue(has_literal_financial_template(attr(json.dumps({'label':'Annual fee','value':'${price}'})),kind='fee'))
  for value in [attr('{"label":"Purchase APR","label":"other","value":"{{rate}}"}'),attr(json.dumps({'label':'Purchase APR','value':'{{image_url}}'})),attr(json.dumps({'label':'Reward points','value':'{{points}}'})),attr(json.dumps({'label':'Purchase APR','value':'17.74%'})),attr(json.dumps({'label':'Purchase APR','value':'{{'+('x'*301)+'}}'}))]:
   self.assertFalse(has_literal_financial_template(value))
  for wrapper in ['nav','header','footer','aside','script']:
   self.assertFalse(has_literal_financial_template(f'<{wrapper}>'+rate+f'</{wrapper}>'))
 def test_referenced_apy_requires_unique_owned_complete_note(self):
  for fixture in ['amex-hysa-rendered']:
   from bs4 import BeautifulSoup
   from worker.native_offer_records import owned_offer_records
   raw=(FIX/(fixture+'.html.bin')).read_text(encoding='utf8')
   from worker.native_apy_records import preserve_accessible_headings
   for mode in ['duplicate','conditional','different_product']:
    soup=BeautifulSoup(raw,'html.parser');preserve_accessible_headings(soup)
    note=next(p for p in soup.find_all(['p','li']) if ' '.join(p.get_text(' ',strip=True).split()).startswith('2 The Annual Percentage Yield'))
    if mode=='duplicate':
     from copy import deepcopy
     other=deepcopy(note);other.append(' Different disclosure.');note.insert_after(other)
    elif mode=='conditional':note.append(' Only for eligible customers.')
    else:
     text=note.get_text(' ',strip=True).replace('High Yield Savings Account','Other Savings Account');note.clear();note.append(text)
    self.assertFalse(any(x[0]=='owned_referenced_apy' for x in owned_offer_records(soup)),mode)
 def test_same_named_apy_cannot_cross_bank_country_or_wrong_detail_link(self):
  from dataclasses import replace
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  parse=USOfficialProofTests.parse
  detail=input_from_segments(bank='AB',country='US',url='https://www.ally.com/bank/online-savings-account',product='savings',name='Ally Bank Savings Account',segments=parse(self,'ally-savings'))
  rates=input_from_segments(bank='AB',country='US',url='https://www.ally.com/bank/savings-account-rates',product='savings',name='Compare Savings',segments=parse(self,'ally-rates'),role='supporting_html',ident='rates')
  for mode in ['bank','country','link']:
   from copy import deepcopy
   other=deepcopy(rates)
   if mode=='bank':other=replace(other,context=replace(other.context,bank_code='OTHER'),candidates=[replace(c,bank_code='OTHER') for c in other.candidates])
   elif mode=='country':other=replace(other,context=replace(other.context,country_code='CA'),candidates=[replace(c,country_code='CA') for c in other.candidates])
   else:other=replace(other,candidates=[replace(c,evidence_excerpt=c.evidence_excerpt.replace('/bank/online-savings-account/','/bank/other-savings-account/')) for c in other.candidates])
   record,result,_=run_services([detail,other])
   self.assertEqual(result.validation_action,'excluded',mode)
   self.assertNotIn('standard_rate',record['candidate_payload'],mode)
 def test_actual_amex_and_both_cards_pass_ordinary_artifacts_with_exact_qualified_prices(self):
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  parse=USOfficialProofTests.parse
  for fixture,bank,url,typ,name in [('amex-hysa-rendered','AE','https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account','savings','American Express High Yield Savings'),('bofa-card-rendered','BOAN','https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card','credit-card','Bank of America® Travel Rewards Credit Card'),('bofa-student-rendered','BOAN','https://www.bankofamerica.com/credit-cards/products/student-rewards-credit-card','credit-card','Bank of America® Travel Rewards Credit Card for Students')]:
   item=input_from_segments(bank=bank,country='US',url=url,product=typ,name=name,segments=parse(self,fixture))
   if typ=='savings':
    from dataclasses import replace
    metadata={**item.context.source_metadata,'discovery_metadata':{**item.context.source_metadata['discovery_metadata'],'page_title':'High Yield Savings Account with No Fees to Open | Amex US'}}
    item=replace(item,context=replace(item.context,source_metadata=metadata))
   record,result,_=run_services([item]);facts=record['candidate_payload']
   self.assertEqual(result.validation_action,'auto_validated',facts['_collection_accuracy'])
   self.assertEqual(record['currency'],'USD')
   if typ=='savings':self.assertEqual((facts['standard_rate'],facts['monthly_fee']),(3.1,0))
   else:
    self.assertEqual(facts['annual_fee'],0)
    self.assertNotIn('purchase_interest_rate',facts)
    self.assertIn('15 billing cycles',facts['purchase_interest_rate_summary'])
    self.assertIn('17.74%',facts['purchase_interest_rate_summary']);self.assertIn('27.74%',facts['purchase_interest_rate_summary'])

 def test_adjacent_or_heading_qualified_apy_cannot_become_standard_scalar(self):
  from worker.native_offer_records import owned_offer_records
  from bs4 import BeautifulSoup
  note='<li><sup>2</sup> The Annual Percentage Yield (APY) as advertised is accurate as of 10/8/2026. Interest rate and APY are subject to change at any time without notice before and after a High Yield Savings Account is opened.</li>'
  positive='<main><h1>Example High Yield Savings</h1><section><h2>3.10% APY\u00b2</h2></section>'+note+'</main>'
  self.assertTrue(any(x[0]=='owned_referenced_apy' for x in owned_offer_records(BeautifulSoup(positive,'html.parser'))))
  for context in ['<p>Only for eligible new customers.</p>','<p>Rate applies when your balance is at least $5000.</p>']:
   html='<main><h1>Example High Yield Savings</h1><section><h2>3.10% APY\u00b2</h2>'+context+'</section>'+note+'</main>'
   self.assertFalse(any(x[0]=='owned_referenced_apy' for x in owned_offer_records(BeautifulSoup(html,'html.parser'))))

 def test_named_apy_component_reference_cannot_lose_its_qualification(self):
  from worker.native_apy_records import apy_records
  from bs4 import BeautifulSoup
  html='<main><section><h2>Savings</h2><div><p>Annual Percentage Yield<a href="#price-note"></a></p><span>3.10%</span></div><a href="/bank/savings/">View Details</a></section><p>Our Annual Percentage Yields (APYs) are accurate as of 10/08/2026. No minimum balance required to open an account or earn APY.</p><p id="price-note">Only for eligible customers.</p></main>'
  self.assertEqual(apy_records(BeautifulSoup(html,'html.parser')),[])

class LiteralStateAcquisitionTests(unittest.TestCase):
 def test_actual_amex_header_template_requests_essential_render(self):
  from api_service.collection_evidence_research import _has_required_dynamic_lead
  raw=(FIX/'amex-hysa.html.bin').read_text(encoding='utf8')
  self.assertTrue(_has_required_dynamic_lead(raw,['standard_rate']))
  self.assertFalse(_has_required_dynamic_lead(raw,[]))
  self.assertFalse(_has_required_dynamic_lead(raw,['minimum_deposit']))

 def test_literal_json_and_transit_headers_are_bounded_generic_leads_only(self):
  import json
  from worker.pricing_state_leads import has_literal_state_rate_template
  def script(value):return '<script>window.otherBankState = '+json.dumps(value)+';</script>'
  obj={'headerText':{'apyText':'{{apy}}% APY'}}
  self.assertTrue(has_literal_state_rate_template(script(obj)))
  transit=['~#iM',['product',['^ ','headerText',['^ ','apyText','{{apy}}% APY']]]]
  self.assertTrue(has_literal_state_rate_template(script(json.dumps(transit))))
  self.assertTrue(has_literal_state_rate_template('<script type="application/json">'+json.dumps(obj)+'</script>'))
  for value in [{'calculator':obj},{'graph':obj},{'headerText':{'apyText':'3.10% APY'}},{'headerText':{'apyText':'{{date}}% APY'}},{'headerText':{'apyText':'{{apy}}% points'}}]:
   self.assertFalse(has_literal_state_rate_template(script(value)))
  for raw in ['<script>window.state = JSON.parse('+json.dumps(json.dumps(obj))+');</script>', '<script>window.state = {"headerText":{"apyText":"{{apy}}% APY","apyText":"other"}};</script>', '<script>window.state = {"headerText":{"apyText":"{{apy}}% APY"}} + getValue();</script>', '<script src="/pricing.js">window.state = '+json.dumps(obj)+';</script>']:
   self.assertFalse(has_literal_state_rate_template(raw))
  for wrapper in ['nav','header','footer','aside']:
   self.assertFalse(has_literal_state_rate_template('<'+wrapper+'>'+script(obj)+'</'+wrapper+'>'))
  self.assertFalse(has_literal_state_rate_template(script({'other':'x'*1_000_001,**obj})))
 def test_actual_amex_static_to_rendered_uses_ordinary_planner_and_artifacts(self):
  from dataclasses import replace
  from hashlib import sha256
  from unittest.mock import patch
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  from api_service.collection_evidence_research import CapturedPage,EvidenceResearchPlanner
  from worker.discovery.fpds_discovery.registry import RegistrySource,SourceRegistry
  from worker.pipeline.fpds_parse_chunk.version import PARSER_VERSION
  url='https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account'
  raw=(FIX/'amex-hysa.html.bin').read_bytes();parse=USOfficialProofTests.parse
  item=input_from_segments(bank='AE',country='US',url=url,product='savings',name='American Express High Yield Savings',segments=parse(self,'amex-hysa'))
  source=RegistrySource('detail','P0',True,'html','detail','official source',url,url,(),'en','AE','US','savings',item.context.source_metadata)
  registry=SourceRegistry('fixture','AE','US','savings','en',('americanexpress.com',),'detail',(source,))
  capture=CapturedPage(item.context.source_document_id,item.context.snapshot_id,item.context.parsed_document_id,url,raw.decode('utf8'),sha256(raw).hexdigest(),parser_version=PARSER_VERSION)
  planner=EvidenceResearchPlanner()
  with patch('api_service.collection_evidence_research.llm_provider_configured',return_value=False):
   before,excluded,_=run_services([item]);self.assertEqual(excluded.validation_action,'excluded')
   plan=planner.plan(run_id='run',registry=registry,inputs=[item],captures=[capture],attempted_urls={url},parent_counts={})
   self.assertEqual([a['kind'] for a in plan['actions']],['render_html'])
   for kwargs in [{'attempted_actions':['render:'+item.context.source_document_id]},{'remaining_renders':0}]:
    limited=planner.plan(run_id='run',registry=registry,inputs=[item],captures=[capture],attempted_urls={url},parent_counts={},**kwargs)
    self.assertEqual(limited['actions'],[])
   rendered=input_from_segments(bank='AE',country='US',url=url,product='savings',name='American Express High Yield Savings',segments=parse(self,'amex-hysa-rendered'))
   after,approved,_=run_services([rendered]);self.assertEqual(approved.validation_action,'auto_validated',after['candidate_payload']['_collection_accuracy'])
   self.assertEqual(after['candidate_payload']['standard_rate'],3.1)
   rendered_capture=replace(capture,html=(FIX/'amex-hysa-rendered.html.bin').read_text(encoding='utf8'),response_metadata={'fetch_method':'browser'})
   done=planner.plan(run_id='run',registry=registry,inputs=[rendered],captures=[rendered_capture],attempted_urls={url},parent_counts={})
   self.assertEqual(done['actions'],[])
   self.assertEqual(done['sources'],[])
