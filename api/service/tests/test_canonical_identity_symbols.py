"""Execute the production identity queries against an isolated SQL fixture."""
import re
import sqlite3
import unittest

from api_service.review_detail import _find_current_product


class SqlFixture:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.create_function("regexp_replace", 4, self.replace)
        self.db.executescript("""
            CREATE TABLE canonical_product (product_id TEXT, status TEXT,
                current_version_no INTEGER, product_name TEXT, product_type TEXT,
                subtype_code TEXT, last_verified_at TEXT, last_changed_at TEXT,
                country_code TEXT, bank_code TEXT, product_family TEXT, updated_at TEXT);
            CREATE TABLE product_version (product_id TEXT, version_no INTEGER,
                product_version_id TEXT, normalized_payload TEXT);
            CREATE TABLE normalized_candidate (run_id TEXT, source_document_id TEXT, product_name TEXT);
            CREATE TABLE field_evidence_link (product_version_id TEXT, field_name TEXT, source_document_id TEXT);
        """)

    @staticmethod
    def replace(value, pattern, replacement, flags):
        pattern = pattern.replace("[:alnum:]", "a-zA-Z0-9").replace("[[:space:]]", r"\s")
        return re.sub(pattern, replacement, value, count=0 if "g" in flags else 1)

    def execute(self, sql, params):
        return self.db.execute(re.sub(r"%\((\w+)\)s", r":\1", sql), params)

    def product(self, name, *, bank="BANK", product_type="credit-card", source=None):
        self.db.execute("INSERT INTO canonical_product VALUES (?, 'active', 1, ?, ?, NULL, NULL, NULL, 'CA', ?, 'lending', '2026-10-07')", ("existing", name, product_type, bank))
        self.db.execute("INSERT INTO product_version VALUES ('existing', 1, 'version', '{}')")
        if source:
            self.db.execute("INSERT INTO field_evidence_link VALUES ('version', 'product_name', ?)", (source,))


class CanonicalIdentitySymbolTests(unittest.TestCase):
    def fixture(self):
        fixture = SqlFixture()
        self.addCleanup(fixture.db.close)
        return fixture

    def match(self, fixture, name, **extra):
        return _find_current_product(fixture, review_row={"country_code": "CA", "bank_code": "BANK", "product_family": "lending", "product_type": "credit-card", "product_name": name, **extra})

    def test_symbol_variant_does_not_merge_with_base_product(self):
        for base, variant in [("RBC ION Visa", "RBC ION+ Visa"), ("Other Bank Savings", "Other Bank Savings+")]:
            with self.subTest(variant=variant):
                fixture = self.fixture(); fixture.product(base)
                self.assertIsNone(self.match(fixture, variant))

    def test_symbol_and_spelled_plus_match_without_losing_punctuation_aliases(self):
        for existing, incoming in [("Bank Rewards+ Visa", "Bank Rewards Plus Visa"), ("Bank Rewards Plus Visa", "Bank Rewards+ Visa"), ("Bank Rewards® Visa", "Bank Rewards Visa")]:
            with self.subTest(incoming=incoming):
                fixture = self.fixture(); fixture.product(existing)
                self.assertEqual(self.match(fixture, incoming)["product_id"], "existing")

    def test_variant_names_on_same_source_are_not_one_identity(self):
        fixture = self.fixture(); fixture.product("Bank Prior Name", source="source")
        fixture.db.executemany("INSERT INTO normalized_candidate VALUES ('run', 'source', ?)", [("Bank Savings",), ("Bank Savings+",)])
        self.assertIsNone(self.match(fixture, "Bank Savings+", run_id="run", source_document_id="source"))

    def test_single_identity_source_still_preserves_renamed_product(self):
        fixture = self.fixture(); fixture.product("Bank Prior Name", source="source")
        fixture.db.execute("INSERT INTO normalized_candidate VALUES ('run', 'source', 'Bank New Name')")
        self.assertEqual(self.match(fixture, "Bank New Name", run_id="run", source_document_id="source")["product_id"], "existing")

    def test_bank_and_product_type_boundaries_remain(self):
        for extra in [{"bank_code": "OTHER"}, {"product_type": "savings"}, {"country_code": "US"}]:
            with self.subTest(extra=extra):
                fixture = self.fixture(); fixture.product("Bank Rewards+ Visa")
                self.assertIsNone(self.match(fixture, "Bank Rewards+ Visa", **extra))
