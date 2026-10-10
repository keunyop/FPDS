"""Literal numeric links into grouped disclosures retain precise and shared scope."""
import gzip,hashlib,json,unittest
from pathlib import Path
from bs4 import BeautifulSoup
from worker.native_dom_ownership import local_notes
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
F=Path(__file__).parent/'fixtures/grouped-disclosures'

class GroupedDisclosureTests(unittest.TestCase):
 def test_official_numeric_reference_does_not_import_rewards_eligibility(self):
  r=json.loads((F/'sources.json').read_text())[0];raw=gzip.decompress((F/r['fixture']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
  soup=BeautifulSoup(raw,'html.parser');label=soup.find(string=lambda s:s and s.strip()=='Annual Fee');notes=local_notes(soup,label.find_parent('tr'))
  self.assertEqual(len(notes),1);self.assertIn('The annual fee is $0.',notes[0]);self.assertIn('All credit products are subject to credit approval.',notes[0]);self.assertNotIn('To be eligible for 2%',notes[0]);self.assertNotIn('FICO',notes[0])
 def test_official_complete_annual_fee_passes_ordinary_services(self):
  from worker.pipeline.tests.test_cms_source_boundaries import chunked_segments
  from worker.pipeline.tests.test_evidence_research_parity import input_from_segments,run_services
  r=json.loads((F/'sources.json').read_text())[0];raw=gzip.decompress((F/r['fixture']).read_bytes())
  segments=chunked_segments(raw,'text/html')
  item=input_from_segments(bank='KEYBANK',url=r['url'],product='credit-card',name='Key Cashback Credit Card',country='US',segments=segments)
  row,v,_=run_services([item]);self.assertEqual(v.validation_action,'auto_validated',row['candidate_payload']);self.assertEqual(row['candidate_payload']['annual_fee'],0)
  self.assertIn('20.74% to 27.74%',row['candidate_payload']['purchase_interest_rate_summary']);self.assertNotIn('purchase_interest_rate',row['candidate_payload'])
 def test_fee_conditions_and_conflicting_application_language_remain_blocking(self):
  from worker.pipeline.fpds_collection_accuracy import quote_supports_value
  good='Example Credit Card\nAnnual Fee\n$0\nAll credit products are subject to credit approval.'
  self.assertTrue(quote_supports_value('annual_fee',0,good))
  for suffix in [' The annual fee is waived only for students.',' The annual fee is $95 after the first year.',' Annual fee subject to credit approval.',' Only if you maintain a balance.',' The annual fee is $95.',' $95 annual fee.']:
   self.assertFalse(quote_supports_value('annual_fee',0,good+suffix),suffix)
 def example(self,marker='2',common='All account fees are waived only for students.'):
  return BeautifulSoup('<main><h1>Example Savings</h1><p id="price">Monthly fee $5<sup><a href="#notes">'+marker+'</a></sup></p><section id="notes"><div><span class="footnote">1</span><p>Rewards are conditional on balances.</p></div><div><span class="footnote">2</span><p>The monthly fee is $5. The fee is waived if a $500 balance is maintained.</p></div><div><p>'+common+'</p></div></section></main>','html.parser')
 def test_cross_market_product_type_shared_and_own_conditions_are_preserved(self):
  for name in ['Example Savings','Example Credit Card','Compte Exemple']:
   soup=self.example();soup.h1.string=name;notes=local_notes(soup,soup.find(id='price'));self.assertEqual(len(notes),1);self.assertNotIn('Rewards',notes[0]);self.assertIn('$500',notes[0]);self.assertIn('only for students',notes[0])
 def test_missing_duplicate_or_empty_numeric_notes_fail_closed(self):
  for kind in ['missing','duplicate','empty']:
   soup=self.example();groups=soup.find(id='notes').find_all('div',recursive=False)
   if kind=='missing':groups[1].span.string='3'
   elif kind=='duplicate':groups[0].span.string='2'
   else:groups[1].p.decompose()
   self.assertIsNone(local_notes(soup,soup.find(id='price')),kind)
 def test_non_numeric_anchor_retains_whole_container(self):
  soup=self.example(marker='See disclosures');notes=local_notes(soup,soup.find(id='price'));self.assertIn('Rewards',notes[0]);self.assertIn('$500',notes[0])
 def test_single_note_and_ambiguous_container_never_lose_context(self):
  soup=BeautifulSoup('<p id="price">Fee<sup><a href="#note">2</a></sup></p><div id="note"><p>If eligible the fee is waived.</p></div>','html.parser');self.assertIn('If eligible',local_notes(soup,soup.find(id='price'))[0])

if __name__=='__main__':unittest.main()
