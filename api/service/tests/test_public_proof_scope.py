"""Snapshot-pinned financial proof filtering never exposes private mappings."""
import unittest
from api_service.public_common import load_public_projection_rows
from worker.pipeline.fpds_collection_accuracy import ACCURACY_VERSION, payload_digest

class Result:
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows

class Connection:
    def __init__(self, rows): self.rows = rows; self.calls = []
    def execute(self, sql, params):
        self.calls.append((sql, params))
        return Result(self.rows)

class PublicProofScopeTests(unittest.TestCase):
    def row(self, quote):
        row = dict(product_id='p', country_code='US', bank_code='EXAMPLE', product_type='chequing', product_name='Example Checking', currency='USD', refresh_metadata={'product_version_id':'snapshot-version'})
        payload = dict(product_name='Example Checking', monthly_fee=0, unlimited_transactions_flag=True)
        payload['_collection_accuracy'] = dict(version=ACCURACY_VERSION, accepted=True, digest=payload_digest(row, payload), verified_fields=list(payload))
        row['approved_collection_payload'] = payload
        row['approved_field_mapping_metadata'] = {'unlimited_transactions_flag':{'official_evidence_quote':quote}}
        return row

    def test_old_accepted_receipt_with_only_atm_coverage_is_excluded(self):
        connection = Connection([self.row('Unlimited transactions at 40,000+ fee-free ATMs nationwide')])
        self.assertEqual(load_public_projection_rows(connection,snapshot_id='snapshot',country_code='US'), [])
        sql, params = connection.calls[0]
        self.assertIn("approved_version.product_version_id = NULLIF(p.refresh_metadata ->> 'product_version_id', '')", sql)
        self.assertIn('approved_candidate.candidate_id = approved_version.approved_candidate_id', sql)
        self.assertIn('approved_candidate.country_code = p.country_code', sql)
        self.assertIn('approved_candidate.bank_code = p.bank_code', sql)
        self.assertEqual(params, {'snapshot_id':'snapshot','country_code':'US'})

    def test_ordinary_coverage_survives_without_private_mapping_or_payload(self):
        row = self.row('Unlimited transactions. Separate ATM fees apply.')
        result = load_public_projection_rows(Connection([row]), snapshot_id='snapshot', country_code='US')
        self.assertEqual(len(result),1)
        self.assertTrue(result[0]['refresh_metadata']['unlimited_transactions_flag'])
        self.assertNotIn('approved_field_mapping_metadata',result[0])
        self.assertNotIn('approved_collection_payload',result[0])
        self.assertNotIn('official_evidence_quote',str(result))
        self.assertIn('approved_field_mapping_metadata',row)
