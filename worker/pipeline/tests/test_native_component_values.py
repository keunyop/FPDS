from pathlib import Path
import json
import unittest
from bs4 import BeautifulSoup
from worker.native_component_values import product_maps, resolve_component_values

ROOT = Path(__file__).parent / "fixtures/admin-collection-parity"


class NativeComponentValuesTests(unittest.TestCase):
    def soup(self, filename="echo.html"):
        raw = (ROOT / filename).read_text(encoding="utf8")
        return BeautifulSoup(raw, "html.parser"), raw

    def test_real_literals_resolve_only_explicitly_owned_components(self):
        soup, raw = self.soup()
        other = BeautifulSoup('<div><p>${p1.productPricing.AF_CRD.productPricingValue|amount: "true"}</p><script>capsuleAlias: "c2-autres"</script></div>', 'html.parser').div
        soup.body.append(other)
        self.assertGreater(resolve_component_values(soup, raw), 0)
        scope = soup.find(attrs={"data-fpds-literal-owner": "ECHO Cashback Mastercard"})
        self.assertIsNotNone(scope)
        self.assertIn("${", other.get_text())

    def test_wrong_identity_and_absent_alias_are_not_resolved(self):
        for altered in ("identity", "alias"):
            soup, raw = self.soup()
            if altered == "identity":
                soup.h1.string = "Other Mastercard"
            else:
                for s in soup.find_all("script"):
                    s.string = s.get_text().replace('capsuleAlias: "c1"', 'capsuleAlias: "missing"')
            self.assertEqual(resolve_component_values(soup, raw), 0)

    def test_dynamic_records_keep_exact_months_and_interest_alternatives(self):
        soup, raw = self.soup("redeemable-plus.html")
        self.assertGreater(resolve_component_values(soup, raw), 0)
        table = soup.find(attrs={"data-fpds-literal-owner": "Redeemable Plus GIC"}).table
        rows = [tr.get_text(" ", strip=True) for tr in table.find_all("tr")[1:]]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all("36 months" in r and "0.300%" in r for r in rows))
        self.assertTrue(any("Simple" in r for r in rows))
        self.assertTrue(any("Compound" in r for r in rows))

    def test_conflicting_maps_duplicate_keys_and_executable_strings_are_rejected(self):
        _, raw = self.soup()
        self.assertEqual(product_maps(raw + 'Websites.Product.Core.setProductMap(JSON.parse("{}"))'), {})
        literal = json.dumps('{"c1":"[]","c1":"[]"}')
        self.assertEqual(product_maps('Websites.Product.Core.setProductMap(JSON.parse(' + literal + '))'), {})
        self.assertEqual(product_maps('Websites.Product.Core.setProductMap(JSON.parse(fetch("/data")))'), {})

    def test_source_scripts_are_never_evaluated_or_url_tokens_resolved(self):
        soup, raw = self.soup()
        resolve_component_values(soup, raw)
        self.assertIn('${p1.urlBoiteLogin|link:', str(soup))
        self.assertIn('setProductMap(JSON.parse(', str(soup))

    def test_consent_heading_is_removed_but_financial_dialog_is_preserved(self):
        soup = BeautifulSoup('<h1>Offer</h1><div role="dialog"><h1>Loan terms</h1></div><div role="dialog" aria-label="Cookie consent"><h1>Privacy</h1></div>', 'html.parser')
        resolve_component_values(soup, str(soup))
        self.assertIn("Loan terms", soup.get_text())
        self.assertNotIn("Privacy", soup.get_text())

    def test_explicit_conflicting_period_unit_keeps_template_unresolved(self):
        from worker.native_component_values import _MAP
        _, raw = self.soup("redeemable-plus.html")
        maps = product_maps(raw)
        for row in maps["c1"]:
            row["productCriteria.TERMRANGE.unitOfMsrCd"] = "YEAR"
        encoded = json.dumps(json.dumps({alias: json.dumps(rows) for alias, rows in maps.items()}))
        raw = _MAP.sub(lambda _: 'Websites.Product.Core.setProductMap(JSON.parse(' + encoded + ')', raw)
        soup = BeautifulSoup(raw, "html.parser")
        resolve_component_values(soup, raw)
        self.assertIn("${productCriteria.TERMRANGE.criteriaNumericValue}", soup.table.get_text())
