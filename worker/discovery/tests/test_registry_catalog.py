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

    def test_seed_detail_sources_cover_current_official_product_list_expansions(self) -> None:
        resolved = resolve_sources_by_id(
            [
                "CIBC-CHQ-006",
                "CIBC-CHQ-007",
                "CIBC-CHQ-008",
                "CIBC-CHQ-009",
                "CIBC-CHQ-010",
                "CIBC-CHQ-011",
                "RBC-CHQ-007",
                "RBC-SAV-007",
                "RBC-SAV-008",
                "RBC-SAV-009",
                "RBC-SAV-010",
                "RBC-SAV-011",
                "RBC-SAV-012",
                "SCOTIA-CHQ-007",
                "SCOTIA-SAV-007",
                "SCOTIA-SAV-008",
                "SCOTIA-GIC-005",
                "TD-CHQ-007",
                "TD-GIC-007",
                "TD-GIC-008",
            ]
        )

        self.assertEqual(
            {source_id: source.normalized_url for source_id, source in resolved.items()},
            {
                "CIBC-CHQ-006": "https://www.cibc.com/en/student/bank-accounts.html",
                "CIBC-CHQ-007": "https://www.cibc.com/en/personal-banking/bank-accounts/skilled-trades/smart-account-apprentices.html",
                "CIBC-CHQ-008": "https://www.cibc.com/en/journeys/banking-offers-for-newcomers/smart-account-for-newcomers.html",
                "CIBC-CHQ-009": "https://www.cibc.com/en/journeys/banking-offers-for-newcomers/banking-for-foreign-workers.html",
                "CIBC-CHQ-010": "https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-start.html",
                "CIBC-CHQ-011": "https://www.cibc.com/en/personal-banking/bank-accounts/senior-banking-offers.html",
                "RBC-CHQ-007": "https://www.rbcroyalbank.com/bank-accounts/us-personal-account.html",
                "RBC-SAV-007": "https://www.rbcroyalbank.com/bank-accounts/nomi-find-and-save.html",
                "RBC-SAV-008": "https://www.rbcroyalbank.com/bank-accounts/youth-student-banking/leo-young-savers-account.html",
                "RBC-SAV-009": "https://www.rbcroyalbank.com/bank-accounts/us-high-interest-savings-account.html",
                "RBC-SAV-010": "https://www.rbcroyalbank.com/bank-accounts/euro-savings-account.html",
                "RBC-SAV-011": "https://www.rbcroyalbank.com/bank-accounts/british-pound-savings-account.html",
                "RBC-SAV-012": "https://www.rbcroyalbank.com/bank-accounts/hong-kong-dollar-savings-account.html",
                "SCOTIA-CHQ-007": "https://www.scotiabank.com/ca/en/personal/bank-accounts/chequing-accounts/preferred-student-youth-bank-account.html",
                "SCOTIA-SAV-007": "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/savings-accelerator-account.html",
                "SCOTIA-SAV-008": "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/euro-savings-account.html",
                "SCOTIA-GIC-005": "https://www.scotiabank.com/ca/en/personal/investing/guaranteed-investment-certificates/personal-redeemable-gics.html",
                "TD-CHQ-007": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/chequing-accounts/student-chequing-account",
                "TD-GIC-007": "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic/cashable-gic",
                "TD-GIC-008": "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic/us-dollar-and-foreign-currency-term-deposits",
            },
        )

    def test_seed_entry_sources_use_official_product_list_urls(self) -> None:
        expected_entry_urls = {
            ("RBC", "chequing"): "https://www.rbcroyalbank.com/bank-accounts/chequing-accounts/index.html",
            ("RBC", "savings"): "https://www.rbcroyalbank.com/bank-accounts/savings-accounts",
            ("RBC", "gic"): "https://www.rbcroyalbank.com/investments/gics.html",
            ("TD", "chequing"): "https://www.td.com/ca/en/personal-banking/products/bank-accounts/chequing-accounts",
            ("TD", "savings"): "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts",
            ("TD", "gic"): "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic",
            ("BMO", "chequing"): "https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts",
            ("BMO", "savings"): "https://www.bmo.com/en-ca/main/personal/bank-accounts/savings-accounts",
            ("BMO", "gic"): "https://www.bmo.com/en-ca/main/personal/investments/gic",
            ("SCOTIA", "chequing"): "https://www.scotiabank.com/ca/en/personal/bank-accounts/chequing-accounts.html",
            ("SCOTIA", "savings"): "https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts.html",
            ("SCOTIA", "gic"): "https://www.scotiabank.com/ca/en/personal/investing/guaranteed-investment-certificates.html",
            ("CIBC", "chequing"): "https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts.html",
            ("CIBC", "savings"): "https://www.cibc.com/en/personal-banking/bank-accounts/savings-accounts.html",
            ("CIBC", "gic"): "https://www.cibc.com/en/personal-banking/investments/gics.html",
        }

        for registry in load_all_registries():
            with self.subTest(bank_code=registry.bank_code, product_type=registry.product_type):
                self.assertEqual(
                    registry.entry_source.normalized_url,
                    expected_entry_urls[(registry.bank_code, registry.product_type)],
                )

    def test_seed_detail_sources_do_not_point_to_other_product_type_or_excluded_wrappers(self) -> None:
        conflicting_tokens_by_type = {
            "chequing": ("savings-account", "savings-accounts", "gic", "guaranteed-investment"),
            "savings": ("chequing-account", "chequing-accounts", "gic", "guaranteed-investment", "tax-free-savings", "tfsa", "fhsa", "rrsp", "resp"),
            "gic": ("chequing-account", "chequing-accounts", "savings-account", "savings-accounts", "tax-free-savings", "tfsa", "fhsa", "rrsp", "resp"),
        }
        excluded_tokens = ("investor", "investors", "shareholder", "shareholders")

        for registry in load_all_registries():
            for source in registry.sources:
                if source.discovery_role != "detail":
                    continue
                fingerprint = source.normalized_url.lower()
                with self.subTest(source_id=source.source_id):
                    self.assertFalse(any(token in fingerprint for token in excluded_tokens))
                    self.assertFalse(any(token in fingerprint for token in conflicting_tokens_by_type[registry.product_type]))


if __name__ == "__main__":
    unittest.main()
