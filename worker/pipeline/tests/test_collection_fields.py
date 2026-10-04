from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from worker.pipeline.fpds_collection_fields import (
    resolve_collection_fields, validate_collection_fields,
    missing_additional_required_fields,
)
from worker.pipeline.fpds_collection_accuracy import sanitize_candidate, acceptance_receipt_valid
from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
from worker.pipeline.fpds_extraction.service import _resolve_field_names, _extract_official_fields_with_ai
from worker.pipeline.tests.test_collection_accuracy import candidate_fixture


class CollectionFieldPolicyTests(unittest.TestCase):
    def configured(self, product_type="chequing", country="CA", extra=(), optional=()):
        baseline = resolve_collection_fields(product_type=product_type, country_code=country)
        value = {"required_fields": [*baseline["required_fields"], *extra], "optional_fields": list(optional)}
        validated = validate_collection_fields(value, resolved=baseline)
        return {country: validated}

    def test_defaults_preserve_grouped_conditional_financial_essentials_and_optional_rates(self):
        for country in ("CA", "US"):
            with self.subTest(country=country):
                result = resolve_collection_fields(product_type="chequing", country_code=country)
                self.assertIn("currency", result["required_fields"])
                self.assertIn("transaction_fee", result["required_fields"])
                self.assertIn("standard_rate", result["optional_fields"])
                excess = next(r for r in result["requirements"] if r["key"] == "excess_transaction_cost")
                self.assertEqual(excess["required_when"], "limited_transactions")
                self.assertEqual(excess["alternatives"], ["additional_transaction_fee", "transaction_fee"])

    def test_configured_empty_optional_and_country_isolation(self):
        policy = self.configured(extra=("minimum_balance",))
        ca = resolve_collection_fields(product_type="chequing", country_code="CA", collection_field_policy=policy)
        us = resolve_collection_fields(product_type="chequing", country_code="US", collection_field_policy=policy)
        self.assertEqual(ca["optional_fields"], [])
        self.assertIn("minimum_balance", ca["required_fields"])
        self.assertFalse(us["configured"])
        self.assertNotIn("minimum_balance", us["required_fields"])
        self.assertIn("standard_rate", us["optional_fields"])

    def test_reject_weakened_essentials_unknown_fields_duplicates_and_overlap(self):
        base = resolve_collection_fields(product_type="gic", country_code="CA")
        valid = {"required_fields": base["required_fields"], "optional_fields": []}
        cases = [None, {"required_fields": []}, {**valid, "required_fields": []},
                 {**valid, "optional_fields": ["invented_fact"]},
                 {**valid, "optional_fields": ["monthly_fee", "monthly_fee"]},
                 {**valid, "optional_fields": ["product_name"]},
                 {**valid, "optional_fields": "monthly_fee"},
                 {**valid, "optional_fields": ["notes"] * 101}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_collection_fields(value, resolved=base)
        for key in ("redeemable_flag", "non_redeemable_flag", "early_withdrawal_penalty"):
            with self.subTest(remove=key), self.assertRaises(ValueError):
                validate_collection_fields({**valid, "required_fields": [f for f in valid["required_fields"] if f != key]}, resolved=base)

    def test_only_registered_extensions_enter_catalog(self):
        result = resolve_collection_fields(product_type="chequing", country_code="CA",
                                           expected_fields=["special_transaction_fee", "invented_fact"])
        names = {f["field_key"] for f in result["field_catalog"]}
        self.assertIn("special_transaction_fee", names)
        self.assertNotIn("invented_fact", names)
        with self.assertRaises(ValueError):
            validate_collection_fields({"required_fields": result["required_fields"],
                                        "optional_fields": ["unregistered_special_fee"]}, resolved=result)

    def test_configured_target_limit_matches_single_grounding_pass_budget(self):
        base = resolve_collection_fields(product_type="chequing", country_code="CA")
        unlocked = [f["field_key"] for f in base["field_catalog"] if f["field_key"] not in base["required_fields"]]
        remaining = 60 - len(base["required_fields"])
        self.assertEqual(len(validate_collection_fields({"required_fields": base["required_fields"],
            "optional_fields": unlocked[:remaining]}, resolved=base)["optional_fields"]), remaining)
        with self.assertRaisesRegex(ValueError, "at most 60"):
            validate_collection_fields({"required_fields": base["required_fields"],
                "optional_fields": unlocked[:remaining + 1]}, resolved=base)

    def test_optional_missing_never_blocks_and_zero_false_are_valid(self):
        policy = self.configured(extra=("minimum_balance", "overdraft_available"), optional=("notes",))
        result = resolve_collection_fields(product_type="chequing", country_code="CA", collection_field_policy=policy)
        self.assertEqual(missing_additional_required_fields(result, {"minimum_balance": 0, "overdraft_available": False}), [])
        self.assertEqual(missing_additional_required_fields(result, {"minimum_balance": "0", "overdraft_available": False}), ["minimum_balance"])
        self.assertEqual(set(missing_additional_required_fields(result, {})), {"minimum_balance", "overdraft_available"})

    def test_real_sanitizer_requires_proven_added_fields_without_manual_review(self):
        row, meta, evidence = candidate_fixture()
        meta["collection_field_policy"] = self.configured(product_type="savings", extra=("minimum_balance",), optional=("notes",))
        normalized, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"])
        self.assertEqual(receipt["additional_required_fields"], ["minimum_balance"])
        self.assertTrue(acceptance_receipt_valid(normalized))
        row["field_mapping_metadata"].pop("minimum_balance")
        excluded, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertIn("required_collection_fields_missing", receipt["reasons"])
        self.assertIn("minimum_balance", receipt["missing_fields"])
        self.assertNotIn("notes", receipt["missing_fields"])
        self.assertFalse(acceptance_receipt_valid(excluded))

    def test_configured_targets_override_legacy_optional_and_cli_without_narrowing_core(self):
        metadata = {"product_type": "chequing", "expected_fields": ["notes", "promotional_rate"],
                    "collection_field_policy": self.configured(extra=("minimum_balance",), optional=("eligibility_text",))}
        context = ExtractionDocumentContext("parsed", "source", "snapshot", "EXAMPLE", "CA", "html", "en", metadata)
        fields = _resolve_field_names(context=context, override_field_names=["notes"], default_fields=("notes", "monthly_fee"))
        self.assertIn("monthly_fee", fields)
        self.assertIn("minimum_balance", fields)
        self.assertIn("eligibility_text", fields)
        self.assertNotIn("notes", fields)
        self.assertNotIn("promotional_rate", fields)

    def test_grounding_prompt_uses_configured_required_and_optional_groups(self):
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        url = "https://bank.example/account"
        metadata = {"product_type": "chequing", "discovery_role": "detail", "expected_fields": ["notes"],
                    "normalized_source_url": url, "official_domain_allowlist": ["bank.example"],
                    "collection_field_policy": self.configured(extra=("minimum_balance",), optional=("eligibility_text",))}
        context = ExtractionDocumentContext("parsed", "source", "snapshot", "EXAMPLE", "CA", "html", "en", metadata)
        chunk = EvidenceChunkCandidate("chunk", "parsed", 0, "section", "account", None, "en",
            "Example Account. Monthly fee $0 CAD. Unlimited transactions. Minimum balance $0 CAD.",
            {}, "source", "snapshot", "EXAMPLE", "CA", "html")
        fields = _resolve_field_names(context=context, override_field_names=None, default_fields=("notes",))
        with patch("worker.pipeline.fpds_extraction.service.invoke_openai_json_schema",
                   return_value=({"fields": [], "summary": "No additional evidence"}, {})) as invoke:
            _extract_official_fields_with_ai(context=context, candidates=[chunk], requested_fields=fields, collected_fields=[])
        payload = invoke.call_args.kwargs["payload"]
        self.assertIn("minimum_balance", payload["required_comparison_fields"])
        self.assertNotIn("minimum_balance", payload["supplemental_fields"])
        self.assertIn("eligibility_text", payload["supplemental_fields"])
        self.assertNotIn("notes", payload["requested_fields"])
        self.assertIn({"key": "minimum_balance", "alternatives": ["minimum_balance"], "required_when": "always"},
                      payload["comparison_requirements"])

    def test_normalization_uses_per_run_policy_snapshot_instead_of_mutable_source_metadata(self):
        from worker.pipeline.fpds_normalization.__main__ import _build_normalization_input
        from worker.pipeline.fpds_normalization.models import NormalizationArtifactLookup
        from worker.discovery.fpds_discovery.registry import RegistrySource
        original = self.configured(extra=("minimum_balance",), optional=("notes",))
        source = RegistrySource("source", "P1", True, "html", "detail", "Account",
            "https://bank.example/account", "https://bank.example/account", ("monthly_fee", "minimum_balance", "notes"),
            "en", "EXAMPLE", "CA", "chequing", {"collection_field_policy": original})
        lookup = NormalizationArtifactLookup("source", "snapshot", "parsed", "execution", "extracted", None,
            "EXAMPLE", "CA", "html", "en", {"collection_field_policy": self.configured(extra=("minimum_deposit",)),
                                              "expected_fields": ["minimum_deposit"]})
        result = _build_normalization_input(source_id="source", lookup=lookup, artifact={}, registry_source=source)
        self.assertEqual(result.source_metadata["collection_field_policy"], original)
        self.assertEqual(result.source_metadata["expected_fields"], list(source.expected_fields))
        legacy = _build_normalization_input(source_id="source", lookup=lookup, artifact={})
        self.assertEqual(legacy.source_metadata, lookup.source_metadata)

    def test_existing_no_configuration_keeps_opportunistic_optional_contract(self):
        result = resolve_collection_fields(product_type="chequing", country_code="CA", expected_fields=["regular_interest_rate"])
        self.assertIn("regular_interest_rate", result["optional_fields"])
        self.assertIn("standard_rate", result["optional_fields"])
        self.assertFalse(result["configured"])


if __name__ == "__main__":
    unittest.main()
