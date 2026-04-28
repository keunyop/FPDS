from __future__ import annotations

import unittest

from worker.discovery.fpds_discovery.catalog import (
    load_all_registries,
    load_catalog_source_index,
    load_registry_catalog,
    resolve_sources_by_id,
)


class RegistryCatalogTests(unittest.TestCase):
    def test_catalog_covers_canada_big5_matrix(self) -> None:
        entries = load_registry_catalog()
        self.assertEqual(len(entries), 15)
        matrix = {(entry.bank_code, entry.product_type) for entry in entries}
        expected = {
            ("RBC", "chequing"),
            ("RBC", "savings"),
            ("RBC", "gic"),
            ("TD", "chequing"),
            ("TD", "savings"),
            ("TD", "gic"),
            ("BMO", "chequing"),
            ("BMO", "savings"),
            ("BMO", "gic"),
            ("SCOTIA", "chequing"),
            ("SCOTIA", "savings"),
            ("SCOTIA", "gic"),
            ("CIBC", "chequing"),
            ("CIBC", "savings"),
            ("CIBC", "gic"),
        }
        self.assertEqual(matrix, expected)

    def test_all_registries_load_with_unique_registry_keys(self) -> None:
        registries = load_all_registries()
        self.assertEqual(len(registries), 15)
        registry_keys = {f"{registry.country_code}:{registry.bank_code}:{registry.product_type}" for registry in registries}
        self.assertEqual(len(registry_keys), 15)

    def test_each_registry_has_entry_source_and_non_empty_source_set(self) -> None:
        for registry in load_all_registries():
            self.assertTrue(registry.allowed_domains)
            self.assertTrue(registry.sources)
            self.assertEqual(registry.entry_source.source_id, registry.entry_source_id)

    def test_catalog_source_index_covers_unique_source_ids(self) -> None:
        source_index = load_catalog_source_index()
        self.assertIn("TD-CHQ-002", source_index)
        self.assertIn("RBC-CHQ-002", source_index)
        self.assertIn("CIBC-GIC-001", source_index)

    def test_resolve_sources_by_id_uses_catalog_when_registry_path_is_omitted(self) -> None:
        resolved = resolve_sources_by_id(["TD-CHQ-002", "RBC-CHQ-002"])
        self.assertEqual(resolved["TD-CHQ-002"].product_type, "chequing")
        self.assertEqual(resolved["RBC-CHQ-002"].bank_code, "RBC")

    def test_scotia_savings_seed_registry_uses_current_us_dollar_account_url(self) -> None:
        resolved = resolve_sources_by_id(["SCOTIA-SAV-005"])
        self.assertEqual(
            resolved["SCOTIA-SAV-005"].normalized_url,
            "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html",
        )

    def test_bmo_chequing_seed_registry_covers_current_public_lineup(self) -> None:
        resolved = resolve_sources_by_id(["BMO-CHQ-002", "BMO-CHQ-003", "BMO-CHQ-004", "BMO-CHQ-005", "BMO-CHQ-008"])
        self.assertEqual(
            {item.normalized_url for item in resolved.values()},
            {
                "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/practical",
                "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/plus",
                "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance",
                "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/premium",
                "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/air-miles",
            },
        )


if __name__ == "__main__":
    unittest.main()
