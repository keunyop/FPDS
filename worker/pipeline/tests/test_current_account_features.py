import gzip,hashlib,json,unittest
from pathlib import Path
from dataclasses import replace,fields
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.tests.test_admin_collection_parity import input_from_segments,run_services
FIX=Path(__file__).parent/'fixtures/current-ph-companions'
MANIFEST=json.loads((FIX/'sources.json').read_text())
def ordinary(row,bank='LANDBANK',product='savings',raw=None,url=None):
 raw=raw or gzip.decompress((FIX/row['file']).read_bytes())
 parsed=parse_snapshot_bytes(body=raw,content_type='text/html')
 item=input_from_segments(bank=bank,url=url or row['url'],product=product,name='unverified discovery',segments=parsed.segments,country='PH')
 keys={f.name for f in fields(EvidenceChunkCandidate)}
 chunks=_build_evidence_chunks(parsed_document_id=item.context.parsed_document_id,source_language='en',artifact=parsed,max_chars=900,overlap_chars=120)
 candidates=[EvidenceChunkCandidate(**{k:v for k,v in c.to_record().items() if k in keys},source_document_id=item.context.source_document_id,source_snapshot_id=item.context.snapshot_id,bank_code=bank,country_code='PH',source_type='html') for c in chunks]
 return replace(item,candidates=candidates)
class CurrentAccountFeaturesTests(unittest.TestCase):
 def test_actual_owned_annual_rate_and_conditional_monthly_cost(self):
  for row in MANIFEST:
   if 'landbank.com' not in row['url'] or 'perang-inimpok' in row['url']:continue
   raw=gzip.decompress((FIX/row['file']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
   r,v,_=run_services([ordinary(row)])
   p=r['candidate_payload'];usd='us-dollar' in row['url']
   with self.subTest(url=row['url']):
    self.assertEqual(v.validation_action,'auto_validated',p['_collection_accuracy'])
    self.assertEqual(r['currency'],'USD' if usd else 'PHP')
    self.assertEqual(p['monthly_fee'],5 if usd else 200)
    self.assertEqual(p['standard_rate'],0.025 if usd else 0.05)
    self.assertIn('two (2) consecutive month-end',p['fee_waiver_condition'])
    self.assertIn('second month',p['fee_waiver_condition'])
    self.assertIn('Required Daily Balance To Earn Interest',p['interest_rate_summary'])
    self.assertEqual(p['minimum_deposit'],100 if usd else 10000 if 'passbook' in row['url'] else 500)
    self.assertEqual(p['minimum_balance'],100 if usd else 10000 if 'passbook' in row['url'] else 500)
 def test_unknown_monthly_unit_does_not_make_zero(self):
  row=next(x for x in MANIFEST if 'perang-inimpok' in x['url'])
  r,v,_=run_services([ordinary(row)])
  self.assertEqual(v.validation_action,'excluded')
  self.assertNotEqual(r['candidate_payload'].get('monthly_fee'),0)

 def test_unproven_truncated_heading_is_not_a_responsive_alias(self):
  row=next(x for x in MANIFEST if 'regular-passbook' in x['url'])
  raw=gzip.decompress((FIX/row['file']).read_bytes()).replace(b'lg:hidden',b'lg:visible')
  r,v,_=run_services([ordinary(row,raw=raw)])
  self.assertEqual(v.validation_action,'excluded')
  self.assertIn('product_name',r['candidate_payload']['_collection_accuracy']['missing_fields'])
 def test_other_issuer_and_missing_conditions_use_same_gates(self):
  from bs4 import BeautifulSoup
  row=next(x for x in MANIFEST if 'savings-account-with-atm' in x['url'])
  raw=gzip.decompress((FIX/row['file']).read_bytes()).decode('utf8')
  generic=raw.replace('LANDBANK','ExampleBank').replace('landbank.com','examplebank.com')
  r,v,_=run_services([ordinary(row,bank='EXAMPLE',raw=generic.encode(),url='https://www.examplebank.com/personal-savings-account-with-atm')])
  self.assertEqual(v.validation_action,'auto_validated')
  for old,new in [('Collection:','Missing cadence:'),('Required Daily Balance To Earn Interest','Unknown balance requirement'),('Interest Rate (per Annum)','Interest Rate (per Month)')]:
   _,v,_=run_services([ordinary(row,raw=raw.replace(old,new).encode())])
   self.assertEqual(v.validation_action,'excluded',old)
  soup=BeautifulSoup(raw,'html.parser')
  rate=next(h for h in soup.find_all('h3') if h.get_text(strip=True)=='Interest Rate (per Annum)')
  rate.parent.parent['data-account-name']='Other Savings'
  _,v,_=run_services([ordinary(row,raw=str(soup).encode())]);self.assertEqual(v.validation_action,'excluded')
 def test_original_fixture_hashes(self):
  for row in MANIFEST:self.assertEqual(hashlib.sha256(gzip.decompress((FIX/row['file']).read_bytes())).hexdigest(),row['sha256'])

 def test_interest_earning_balance_survives_as_noncomparable_qualified_rate(self):
  from api_service.public_rates import public_rate
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  row=next(x for x in MANIFEST if 'savings-account-with-atm' in x['url'])
  r,v,_=run_services([ordinary(row)]);p=r['candidate_payload']
  projected={'product_family':'deposit','product_type':'savings','public_display_rate':p['standard_rate'],'refresh_metadata':p}
  self.assertEqual(public_rate(projected)['kind'],'conditional')
  self.assertIsNone(public_rate(projected)['comparable_rate'])
  quote=r['field_mapping_metadata']['interest_rate_summary']['official_evidence_quote']
  self.assertIn('Required Daily Balance To Earn Interest',quote)
  self.assertTrue(quote_supports_value('interest_rate_summary',p['interest_rate_summary'],quote))
  self.assertFalse(quote_supports_value('interest_rate_summary',p['interest_rate_summary'].replace('₱2,000','₱500'),quote))
