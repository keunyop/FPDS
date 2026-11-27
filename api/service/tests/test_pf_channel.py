from decimal import Decimal
import unittest

from api_service.pf_channel import prepare_conditions


class ChannelConditionTests(unittest.TestCase):
    def test_official_sections_keep_open_and_closed_bounds_and_all_rate_evidence(self):
        product = {"institution_code": "KAGO", "template_code": "C03", "currency": "JPY"}
        definitions = {code: {"value_type": code[0], "unit": unit,
                              "minimum_value": 0, "maximum_value": high}
                       for code, unit, high in [("R09", "JPY", 10**10), ("R10", "JPY", 10**10),
                                                ("I02", "연 %", 100), ("L02", "통화", None)]}
        facts = {"currency": {"value": "JPY", "evidence_ids": ["c"]},
                 "credit_limit_text": {"value": "10 万円以上1,000 万円以内", "evidence_ids": ["l"]},
                 "interest_rate_summary": {"value": "お借入利率(年利)\nご利用限度額 金利\n50 万円以下 14.80%\n"
                                                    "50 万円超 0.90%\n8. 金利改定ルール 変動金利 上限金利",
                                           "evidence_ids": ["r"]}}
        def convert():
            return prepare_conditions(product, facts, definitions, {"JPY": "01"})
        values = convert()
        tiers = [v for v in values if v["condition_code"] == "I02"]
        self.assertEqual([(r["lower"], r["lower_inclusive"], r["upper"], r["value"]) for r in tiers],
                         [(100000, True, 500000, "14.80"), (500000, False, 10000000, "0.90")])
        self.assertTrue(all(r["evidence_ids"] == ["l", "r"] for r in tiers))
        facts["interest_rate_summary"]["value"] = facts["interest_rate_summary"]["value"].replace("50 万円超", "60 万円超")
        self.assertFalse(any(v["type"] == "I" for v in convert()))
        del facts["credit_limit_text"]
        self.assertEqual([v["condition_code"] for v in convert()], ["L02"])

    def test_zero_missing_and_template_scope(self):
        product = {"institution_code": "HIGO", "template_code": "D01", "currency": "JPY"}
        defs = {"R01": {"value_type": "R", "unit": "원금통화", "minimum_value": 0, "maximum_value": 1000}}
        facts = {"minimum_deposit": {"value": Decimal("0"), "evidence_ids": ["a"]}}
        self.assertEqual(prepare_conditions(product, facts, defs, {})[0]["value"], 0)
        self.assertEqual(prepare_conditions(product, facts, {}, {}), [])
        self.assertEqual(prepare_conditions(product, {}, defs, {}), [])

    def test_term_table_keeps_each_maturity_and_qualifier_together(self):
        product = {"institution_code": "HIGO", "template_code": "D03", "currency": "JPY"}
        definitions = {"I01": {"value_type": "I", "unit": "연 %", "minimum_value": -100, "maximum_value": 100}}
        rows = [{"term_label": "1年", "rate": Decimal("0.50"), "minimum_deposit": 10000},
                {"term_label": "2年", "rate": Decimal("0.65"), "notes": "店頭のみ"}]
        facts = {"term_rate_table": {"value": rows, "evidence_ids": ["term"]}}
        values = prepare_conditions(product, facts, definitions, {})
        self.assertEqual([(v["term_label"], v["value"]) for v in values], [("1年", Decimal("0.50")), ("2年", Decimal("0.65"))])
        self.assertEqual(values[0]["minimum_deposit"], 10000)
        self.assertEqual(values[1]["notes"], "店頭のみ")
        rows[0]["rate"] = None
        self.assertEqual(prepare_conditions(product, facts, definitions, {}), [])
