from dataclasses import replace
import json
import unittest
from unittest.mock import Mock, patch
from worker.pipeline.fpds_extraction.grounding_cache import grounded_with_reuse, input_digest
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext, ExtractedFieldCandidate
from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
from worker.pipeline.fpds_extraction.storage import ExtractionStorageConfig
from worker.pipeline.fpds_extraction.persistence import ExtractionDatabaseConfig, PsqlExtractionRepository


class Store:
    def __init__(self): self.data = {}
    def get_object_bytes(self, *, object_key): return self.data[object_key]
    def put_object_bytes(self, *, object_key, data, content_type): self.data[object_key] = data


class GroundingReuseTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.context = ExtractionDocumentContext("pd", "sd", "ss", "BANK", "CA", "html", "en",
            {"discovery_role": "detail", "official_domain_allowlist": ["bank.example"]})
        self.chunk = EvidenceChunkCandidate("ec", "pd", 0, "heading", None, None, "en",
            "USD Chequing", {}, "sd", "ss", "BANK", "CA", "html")
        self.field = ExtractedFieldCandidate("product_name", "USD Chequing", "string", .9,
            "openai_official_grounding", "sd", "ss", "ec", "USD Chequing", "heading", None, None, 0, {})
        self.extract = Mock(return_value=([self.field], [], {"model_id": "test", "prompt_tokens": 100,
            "completion_tokens": 20, "web_search_sources": [{"url": "https://bank.example"}]}))
        self.args = dict(object_store=self.store, storage_config=ExtractionStorageConfig("filesystem", "dev", "extracted", "hot"),
            run_id="run-one", context=self.context, candidates=[self.chunk], requested_fields=["product_name"],
            collected_fields=[], extract=self.extract)

    def test_independent_evaluation_bypasses_both_read_and_write(self):
        grounded_with_reuse(**self.args)
        cached_before = dict(self.store.data)
        fields1, _, usage1 = grounded_with_reuse(**self.args, reuse_cache=False)
        fields2, _, usage2 = grounded_with_reuse(**self.args, reuse_cache=False)
        self.assertEqual(self.extract.call_count, 3)
        self.assertEqual(self.store.data, cached_before)
        self.assertEqual(fields1, fields2)
        self.assertFalse(usage1["reused"])
        self.assertEqual(usage1["cache_policy"], "independent_evaluation")
        self.assertEqual(usage1["evaluation_input_digest"], usage2["evaluation_input_digest"])
        grounded_with_reuse(**self.args)
        self.assertEqual(self.extract.call_count, 3)

    def test_reused_parse_does_not_overwrite_previous_run_artifacts(self):
        config = self.args["storage_config"]
        kwargs = dict(country_code="CA", bank_code="BANK", source_document_id="sd", parsed_document_id="pd")
        for method in (config.build_extracted_object_key, config.build_metadata_object_key):
            self.assertNotEqual(method(**kwargs, run_id="run-one"), method(**kwargs, run_id="run-two"))
            self.assertNotEqual(method(**kwargs), method(**kwargs, run_id="run-one"))

    def test_absent_currency_still_grounds_product_facts(self):
        fields, notes, usage = grounded_with_reuse(**{**self.args,
            "candidates": [replace(self.chunk, evidence_excerpt="Savings Account monthly fee $0")]})
        self.assertEqual(fields, [self.field])
        self.assertIsNotNone(usage)
        self.extract.assert_called_once()
        self.assertTrue(self.store.data)

    def test_same_input_reuses_original_provenance_without_new_tokens(self):
        grounded_with_reuse(**self.args)
        fields, _, usage = grounded_with_reuse(**{**self.args, "run_id": "run-two"})
        self.assertEqual(self.extract.call_count, 1)
        self.assertEqual(fields, [self.field])
        self.assertEqual(usage["origin_run_id"], "run-one")
        self.assertEqual((usage["prompt_tokens"], usage["completion_tokens"]), (0, 0))
        self.assertTrue(usage["reused"])

    def test_changed_evidence_conditions_and_scope_do_not_reuse(self):
        grounded_with_reuse(**self.args)
        for change in [dict(candidates=[replace(self.chunk, evidence_excerpt="USD Chequing if balance maintained")]),
                       dict(context=replace(self.context, country_code="US")),
                       dict(context=replace(self.context, snapshot_id="ss-new")),
                       dict(context=replace(self.context, source_metadata={"official_domain_allowlist": []})),
                       dict(requested_fields=["product_name", "currency"])]:
            before = self.extract.call_count
            grounded_with_reuse(**{**self.args, **change})
            self.assertEqual(self.extract.call_count, before + 1)

    def test_model_day_and_policy_fingerprint_invalidate_cache(self):
        args = (self.context, [self.chunk], ["product_name"], [])
        a = input_digest(*args, day="2026-09-30")
        self.assertNotEqual(a, input_digest(*args, day="2026-10-01"))
        with patch("worker.pipeline.fpds_extraction.grounding_cache.configured_model_id", return_value="different"):
            self.assertNotEqual(a, input_digest(*args, day="2026-09-30"))
        grounded_with_reuse(**self.args)
        with patch("worker.pipeline.fpds_extraction.grounding_cache.input_digest", return_value="new-policy"):
            grounded_with_reuse(**self.args)
        self.assertEqual(self.extract.call_count, 2)

    def test_completed_exclusion_reuses_but_provider_failure_retries(self):
        self.extract.return_value = ([], ["model_unverified"], {"model_id": "test"})
        grounded_with_reuse(**self.args)
        fields, _, usage = grounded_with_reuse(**self.args)
        self.assertEqual(fields, [])
        self.assertTrue(usage["reused"])
        self.assertEqual(self.extract.call_count, 1)
        self.store.data.clear()
        self.extract.return_value = ([], ["provider timeout"], None)
        grounded_with_reuse(**self.args)
        grounded_with_reuse(**self.args)
        self.assertEqual(self.extract.call_count, 3)

    def test_corrupt_or_foreign_evidence_fails_to_normal_extraction(self):
        grounded_with_reuse(**self.args)
        key = next(iter(self.store.data))
        data = json.loads(self.store.data[key]); data["fields"][0]["source_document_id"] = "other-product"
        self.store.data[key] = json.dumps(data).encode()
        grounded_with_reuse(**self.args)
        self.assertEqual(self.extract.call_count, 2)
        self.store.data[key] = b"broken"
        grounded_with_reuse(**self.args)
        self.assertEqual(self.extract.call_count, 3)

    def test_run_context_requires_current_selected_parsed_snapshot(self):
        repo = PsqlExtractionRepository(ExtractionDatabaseConfig("unused", "public"))
        repo._resolved_schema = "public"
        repo._execute = Mock(return_value="[]")
        repo.load_latest_document_contexts(source_document_ids=["sd"], run_id="new-run")
        sql = repo._execute.call_args.args[0]
        self.assertIn("rsi.selected_snapshot_id=ss.snapshot_id", sql)
        self.assertIn("rsi.stage_metadata->>'parsed_document_id'=pd.parsed_document_id", sql)
        self.assertEqual(repo._execute.call_args.kwargs["variables"]["run_id"], "new-run")

if __name__ == "__main__": unittest.main()
