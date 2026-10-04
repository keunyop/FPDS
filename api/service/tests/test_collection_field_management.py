from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from pydantic import ValidationError

from api_service.errors import SourceRegistryError
from api_service.models import ProductTypeWriteRequest
from api_service.product_types import load_product_type_list, normalize_product_type_filters, update_product_type_definition
from api_service.source_registry import _collection_source_record
from api_service.source_collection_runner import _build_registry_payload
from api_service.source_catalog import _product_type_expected_fields, _published_product_counts
from worker.pipeline.fpds_collection_fields import resolve_collection_fields
from tests.test_product_types import _QueuedConnection, _product_type_row


class CollectionFieldManagementTests(unittest.TestCase):
    def policy(self, country="CA", extra="minimum_balance"):
        resolved = resolve_collection_fields(product_type="chequing", country_code=country)
        return {"required_fields": [*resolved["required_fields"], extra], "optional_fields": []}

    def definition(self):
        row = _product_type_row(product_type_code="chequing", display_name="Chequing")
        row["collection_field_policy"] = {"CA": self.policy()}
        return row

    def test_list_resolves_session_country_without_cross_country_overwrite(self):
        row = self.definition()
        for country, configured in (("CA", True), ("US", False)):
            with self.subTest(country=country):
                result = load_product_type_list(_QueuedConnection([[row]]),
                    filters=normalize_product_type_filters(search=None, status=None), country_code=country)
                fields = result["items"][0]["collection_fields"]
                self.assertEqual(fields["country_code"], country)
                self.assertEqual(fields["configured"], configured)

    def test_save_merges_only_current_country_and_does_not_regenerate_keywords(self):
        existing = self.definition()
        updated = {**existing, "collection_field_policy": {**existing["collection_field_policy"], "US": self.policy("US")}}
        connection = _QueuedConnection([None])
        with patch("api_service.product_types.load_product_type_definition", side_effect=[existing, updated]), \
             patch("api_service.product_types._merge_keywords", return_value=existing["discovery_keywords"]) as keywords, \
             patch("api_service.product_types._sync_product_type_taxonomy_registry"), \
             patch("api_service.product_types._record_product_type_audit_event"):
            result = update_product_type_definition(connection, product_type_code="chequing",
                country_code="US", payload={"display_name": existing["display_name"],
                    "description": existing["description"], "collection_fields": self.policy("US")},
                actor={}, request_context={})
        self.assertFalse(keywords.call_args.kwargs["regenerate"])
        sql, params = connection.calls[0]
        self.assertIn("COALESCE(collection_field_policy, '{}'::jsonb) ||", sql)
        self.assertEqual(json.loads(params["collection_field_policy"]), {"US": self.policy("US")})
        self.assertEqual(result["collection_field_policy"]["CA"], existing["collection_field_policy"]["CA"])

    def test_save_rejects_removal_of_conditional_financial_essentials_before_write(self):
        existing = self.definition()
        value = self.policy()
        value["required_fields"].remove("transaction_fee")
        connection = _QueuedConnection([])
        with patch("api_service.product_types.load_product_type_definition", return_value=existing), \
             patch("api_service.product_types._merge_keywords", return_value=[]), \
             self.assertRaises(SourceRegistryError) as failure:
            update_product_type_definition(connection, product_type_code="chequing",
                payload={"collection_fields": value}, actor={}, request_context={})
        self.assertEqual(failure.exception.status_code, 422)
        self.assertEqual(failure.exception.code, "invalid_collection_fields")
        self.assertEqual(connection.calls, [])

    def test_structured_request_rejects_coercion_and_unrecognized_policy_keys(self):
        good = ProductTypeWriteRequest(collection_fields=self.policy())
        self.assertEqual(good.collection_fields.optional_fields, [])
        for value in ({"required_fields": [True], "optional_fields": []},
                      {"required_fields": "monthly_fee", "optional_fields": []},
                      {**self.policy(), "override_security": True},
                      {"required_fields": [], "optional_fields": ["notes"] * 101}):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ProductTypeWriteRequest(collection_fields=value)

    def test_collection_plan_and_registry_snapshot_use_current_targets_over_legacy_source(self):
        definition = self.definition()
        source = {"source_id": "source", "bank_code": "EXAMPLE", "country_code": "CA", "product_type": "chequing",
                  "source_name": "Example Account", "source_url": "https://bank.example/account", "source_type": "html",
                  "discovery_role": "detail", "expected_fields": ["notes", "promotional_rate"]}
        expected = _product_type_expected_fields(definition, country_code="CA")
        record = _collection_source_record(source, product_type_definition=definition)
        self.assertEqual(set(record["expected_fields"]), set(expected))
        self.assertNotIn("promotional_rate", expected)
        self.assertIn("minimum_balance", expected)
        group = {"bank_code": "EXAMPLE", "country_code": "CA", "product_type": "chequing", "source_language": "en",
                 "included_sources": [record]}
        snapshot = _build_registry_payload(group)["sources"][0]
        self.assertEqual(snapshot["collection_field_policy"], definition["collection_field_policy"])
        self.assertEqual(snapshot["expected_fields"], record["expected_fields"])

    def test_published_counts_deduplicate_current_eligible_membership(self):
        with patch("api_service.public_common.load_latest_public_snapshot", return_value={"snapshot_id": "current"}) as latest, \
             patch("api_service.public_common.load_public_projection_rows", return_value=[
                 {"bank_code": "A", "product_id": "one"}, {"bank_code": "A", "product_id": "one"},
                 {"bank_code": "A", "product_id": "two"}, {"bank_code": "B", "product_id": "three"}]) as rows:
            connection = object()
            self.assertEqual(_published_product_counts(connection, country_code="US"), {"A": 2, "B": 1})
            latest.assert_called_once_with(connection, country_code="US")
            rows.assert_called_once_with(connection, country_code="US", snapshot_id="current")

    def test_published_counts_without_snapshot_are_zero_without_projection_read(self):
        with patch("api_service.public_common.load_latest_public_snapshot", return_value=None), \
             patch("api_service.public_common.load_public_projection_rows") as rows:
            self.assertEqual(_published_product_counts(object(), country_code="CA"), {})
            rows.assert_not_called()


if __name__ == "__main__":
    unittest.main()
