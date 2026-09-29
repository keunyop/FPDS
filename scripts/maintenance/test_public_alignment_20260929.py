import copy
import unittest
from unittest.mock import patch
from scripts.maintenance.public_alignment_20260929 import prepare_payload, digest, check_public
from scripts.maintenance.public_collection_gap_report import inspect_rows


class BoundedAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.cp = {"country_code":"CA", "bank_code":"VANCITY", "product_type":"savings", "current_version_no":1,
                   "current_snapshot_payload":{"standard_rate":4.6,"public_display_rate":4.6,"monthly_fee":0,"minimum_balance":0}}
        self.item = {"product_id":"prod_NH7Vb_SO1LC8Ll2c", "expected_version":1,
                     "expected_payload_sha256":digest(self.cp["current_snapshot_payload"]),
                     "changes":{"standard_rate":0.6,"public_display_rate":0.6},
                     "field_evidence":[{"fields":["standard_rate","public_display_rate"], "source_url":"https://www.vancity.com/rates/accounts", "fact":"Reviewed regular rate", "checked_at":"2026-09-29"}],
                     "expected_public":{"active":True}}

    def test_typed_evidenced_correction_and_original_preserved(self):
        original = copy.deepcopy(self.cp)
        after, quality = prepare_payload(self.cp,self.item)
        self.assertEqual(after["standard_rate"],0.6)
        self.assertTrue(quality.complete)
        self.assertEqual(self.cp,original)

    def test_stale_version_or_payload_fails(self):
        for key,value in (("current_version_no",2),("current_snapshot_payload",{})):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                prepare_payload({**self.cp,key:value},self.item)

    def test_missing_evidence_and_wrong_domain_fail(self):
        for key,value in (("fields",[]),("source_url","https://www.vancity.com.attacker.example/rates"),("source_url","https://user@www.vancity.com/rates"),("checked_at","2026-08-01")):
            item=copy.deepcopy(self.item);item["field_evidence"][0][key]=value
            with self.subTest(key=key,value=value), self.assertRaises(RuntimeError):
                prepare_payload(self.cp,item)

    def test_missing_essential_cannot_stay_public(self):
        item=copy.deepcopy(self.item);item["changes"]={"standard_rate":None,"public_display_rate":None}
        with self.assertRaises(RuntimeError):prepare_payload(self.cp,item)

    def test_gap_report_deduplicates_urls_and_never_infers_zero(self):
        row={"country_code":"US", "product_id":"one", "bank_code":"BANK", "product_type":"savings", "product_name":"Account", "product_url":"https://bank.example/account", "deposit_terms":{"reason":"basis_unknown"}, "minimum_balance":None, "minimum_deposit":0}
        with patch("scripts.maintenance.public_collection_gap_report._serialize_product_row", side_effect=lambda r,locale:r):
            result=inspect_rows([row,{**row,"product_id":"two"}],[])
        self.assertEqual(result["gap_counts"]["minimum_balance:undisclosed"],2)
        self.assertNotIn("minimum_deposit:undisclosed",result["gap_counts"])
        self.assertEqual(len(result["suggested_product_ids"]),1)
        self.assertEqual(row["minimum_balance"],None)

    def test_gap_report_handles_empty_country_without_paid_calls(self):
        result=inspect_rows([],[])
        self.assertEqual(result["published_count"],0)
        self.assertEqual(result["suggested_product_ids"],[])


if __name__ == "__main__":unittest.main()
