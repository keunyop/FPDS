from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.maintenance.collection_accuracy_cutover import prepare_product, load_manifest, digest
from worker.pipeline.fpds_collection_accuracy import RECEIPT_KEY, ACCURACY_VERSION, acceptance_receipt_valid


class AccuracyCutoverTests(unittest.TestCase):
    def setUp(self):
        self.cp = {"product_id":"prod-one", "status":"active", "current_version_no":3,
            "country_code":"CA", "bank_code":"BANK", "product_type":"savings", "product_name":"Savings",
            "currency":"CAD", "current_snapshot_payload":{"product_name":"Savings", "standard_rate":9}}
        self.previous = {"product_version_id":"version-three", "version_status":"approved", "normalized_payload":deepcopy(self.cp["current_snapshot_payload"])}
        self.item = {**{k:self.cp[k] for k in ("product_id", "country_code", "bank_code", "product_type", "product_name")},
            "version_no":3, "product_version_id":"version-three", "before_sha256":digest(self.cp["current_snapshot_payload"]),
            "assessment":{"accepted":False, "reasons":["product_currency_unverified"]},
            "after":{"product_name":"Savings", RECEIPT_KEY:{"version":ACCURACY_VERSION, "accepted":False}}}

    def test_retraction_preserves_original_and_cannot_approve_facts(self):
        before = deepcopy(self.cp)
        patch = prepare_product(self.cp, self.previous, self.item)
        self.assertEqual(self.cp, before)
        self.assertEqual(patch["version_no"], 4)
        self.assertEqual(patch["after"]["status"], "inactive")
        self.assertNotIn("standard_rate", patch["after"])
        self.assertFalse(acceptance_receipt_valid(self.cp, patch["after"]))
        self.assertEqual(patch["previous_version_id"], "version-three")

    def test_changed_scope_identity_version_or_payload_fails_before_write(self):
        for field, value in (("status","inactive"),("country_code","US"),("current_version_no",4),("current_snapshot_payload",{})):
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                prepare_product({**self.cp, field:value}, self.previous, self.item)

    def test_current_version_disagreement_fails(self):
        for field, value in (("product_version_id","different"),("version_status","superseded"),("normalized_payload",{})):
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                prepare_product(self.cp, {**self.previous, field:value}, self.item)

    def test_unapproved_manifest_cannot_select_arbitrary_records(self):
        with TemporaryDirectory() as root:
            manifest = Path(root) / "manifest.json"
            manifest.write_text('{"items":[]}', encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,"approved manifest changed"):
                load_manifest(manifest)
