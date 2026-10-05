from pathlib import Path
import unittest
from worker.pipeline.fpds_parse_chunk.parser import parse_snapshot_bytes
from worker.discovery.fpds_discovery.discovery import extract_structured_text_sections

FIXTURES = Path(__file__).parent / "fixtures" / "native-product-sections"

class NativeProductSectionTests(unittest.TestCase):
    def test_native_cms_disclosure_is_not_lost_or_truncated(self):
        html = (FIXTURES / "structured-loan.html").read_text(encoding="utf8")
        self.assertTrue(any("minimum loan term of 6 months" in t for t in extract_structured_text_sections(html)))
        parsed = parse_snapshot_bytes(body=html.encode(), content_type="text/html")
        self.assertIn("Your actual Annual Percentage Rate (APR) will vary", parsed.full_text)
        self.assertIn("maximum term of 60 months", parsed.full_text)

    def test_named_account_sections_retain_only_their_own_costs(self):
        parsed = parse_snapshot_bytes(body=(FIXTURES / "named-accounts.html").read_bytes(), content_type="text/html")
        blocks = {s.anchor_value: s.text for s in parsed.segments if s.anchor_type == "named_product_section"}
        self.assertIn("Value Account", blocks)
        self.assertIn("$3.95", blocks["Value Account"])
        self.assertNotIn("$11.95", blocks["Value Account"])
        self.assertIn("calendar month", blocks["Value Account"])
        self.assertIn("$11.95", blocks["Value Plus Account"])
        self.assertIn("$1.25", blocks["Value Plus Account"])

    def test_price_and_general_transaction_records_preserve_conditions(self):
        parsed = parse_snapshot_bytes(body=(FIXTURES / "named-accounts.html").read_bytes(), content_type="text/html")
        records = [s.text for s in parsed.segments if s.anchor_type == "named_product_financial_record" and s.anchor_value == "Value Account"]
        self.assertTrue(any("Monthly fees" in t and "$3.95" in t and "calendar month" in t for t in records))
        self.assertTrue(any("Transactions Included" in t and "12 included" in t and "$1.25 each" in t and "ATM withdrawal" not in t for t in records))

    def _context_and_chunks(self, filename="named-accounts.html", product_type="chequing", bank="FNBC"):
        from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_parse_chunk.service import _build_evidence_chunks
        a = parse_snapshot_bytes(body=(FIXTURES / filename).read_bytes(), content_type="text/html")
        ctx = ExtractionDocumentContext(parsed_document_id="parsed", source_document_id="doc", snapshot_id="snap",
            bank_code=bank, country_code="CA", source_type="html", source_language="en",
            source_metadata={"product_type": product_type, "discovery_role": "detail", "official_domain_allowlist": ["fnbc.ca"],
                "normalized_source_url": "https://www.fnbc.ca/personal/banking/chequing-accounts"})
        chunks = [EvidenceChunkCandidate(evidence_chunk_id=x.evidence_chunk_id, parsed_document_id="parsed",
            chunk_index=x.chunk_index, anchor_type=x.anchor_type, anchor_value=x.anchor_value, page_no=x.page_no,
            source_language="en", evidence_excerpt=x.evidence_excerpt, retrieval_metadata={}, source_document_id="doc",
            source_snapshot_id="snap", bank_code=bank, country_code="CA", source_type="html")
            for x in _build_evidence_chunks(parsed_document_id="parsed", source_language="en", artifact=a, max_chars=180, overlap_chars=20)]
        return ctx, chunks

    def test_four_accounts_have_independent_exact_field_origins(self):
        from worker.pipeline.fpds_extraction.service import _extract_grounded_named_account_variants
        ctx, chunks = self._context_and_chunks()
        variants = _extract_grounded_named_account_variants(context=ctx, candidates=chunks)
        self.assertEqual([v["product_name"] for v in variants], ["Value Account", "Value Plus Account", "Infinity Account", "Select Account"])
        self.assertEqual(variants[0]["monthly_fee"], 3.95)
        self.assertEqual(variants[1]["included_transactions"], 25)
        self.assertTrue(variants[3]["unlimited_transactions_flag"])
        for variant in variants:
            for name, row in variant["field_records"].items():
                chunk = next(c for c in chunks if c.evidence_chunk_id == row["evidence_chunk_id"])
                self.assertEqual(row["evidence_text_excerpt"], chunk.evidence_excerpt)
                self.assertEqual(chunk.anchor_value, variant["product_name"])
        self.assertNotEqual(variants[0]["field_records"]["product_name"]["evidence_chunk_id"], variants[0]["field_records"]["monthly_fee"]["evidence_chunk_id"])

    def test_other_bank_uses_same_rules_and_wrong_type_does_not_expand(self):
        from worker.pipeline.fpds_extraction.service import _extract_grounded_named_account_variants
        ctx, chunks = self._context_and_chunks(bank="OTHER")
        self.assertEqual(len(_extract_grounded_named_account_variants(context=ctx, candidates=chunks)), 4)
        ctx, chunks = self._context_and_chunks(product_type="savings")
        self.assertEqual(_extract_grounded_named_account_variants(context=ctx, candidates=chunks), [])

    def test_wrong_snapshot_or_bank_cannot_establish_siblings(self):
        from dataclasses import replace
        from worker.pipeline.fpds_extraction.service import _extract_grounded_named_account_variants
        ctx, chunks = self._context_and_chunks()
        for changed in [replace(ctx, snapshot_id="other"), replace(ctx, bank_code="other")]:
            self.assertEqual(_extract_grounded_named_account_variants(context=changed, candidates=chunks), [])

    def test_missing_duplicate_or_external_note_stays_unresolved(self):
        from worker.native_product_sections import complete_named_account_sections
        html = (FIXTURES / "named-accounts.html").read_text(encoding="utf8")
        missing = html.replace("Minimum monthly balance must be maintained throughout the calendar month to qualify for fee waiver or rebate.", "Unknown conditions.")
        self.assertEqual(complete_named_account_sections(missing), [])
        external = html.replace("$3.95", '$3.95<a href="#other-condition">1</a>')
        self.assertNotIn("Value Account", [v.name for v in complete_named_account_sections(external)])

    def test_waiver_zero_transfer_count_and_channel_only_unlimited_rejected(self):
        from worker.pipeline.fpds_collection_accuracy import quote_supports_value
        from worker.native_product_sections import extract_named_product_sections
        variants = extract_named_product_sections((FIXTURES / "named-accounts.html").read_text(encoding="utf8"))
        price = variants[1].financial_records[0]
        self.assertFalse(quote_supports_value("monthly_fee", 0, price))
        finite = variants[2].financial_records[1]
        self.assertTrue(quote_supports_value("included_transactions", 25, finite))
        self.assertFalse(quote_supports_value("included_transactions", 2, finite))
        self.assertFalse(quote_supports_value("unlimited_transactions_flag", True, "Example Account\nTransactions Included\nUnlimited ATM withdrawals"))

    def test_complete_lending_range_is_percentage_summary_without_scalar_conversion(self):
        from worker.pipeline.fpds_rate_safety import contains_explicit_rate_percentage
        parsed = parse_snapshot_bytes(body=(FIXTURES / "structured-loan.html").read_bytes(), content_type="text/html")
        record = next(s for s in parsed.segments if s.anchor_type == "named_lending_range_declaration" and s.text.startswith("Interest Rates on unsecured"))
        self.assertTrue(contains_explicit_rate_percentage(record.text))
        self.assertIn("29.99%-34.99%", record.text)
        self.assertIn("province of residence", record.text)
        self.assertFalse(contains_explicit_rate_percentage("Creditworthiness determines your rate."))

    def test_literal_cms_links_are_discovered_without_executing_script(self):
        from worker.discovery.fpds_discovery.discovery import extract_links
        import html, json
        payload = {"title": "Example loan", "url": "/loans/example", "content": "<p>APR 10%</p>"}
        source = '<custom-component aem-data="' + html.escape(json.dumps(payload), quote=True) + '"></custom-component><script>alert("ignore")</script>'
        links = extract_links(source, base_url="https://example.ca")
        self.assertTrue(any(l.normalized_url == "https://example.ca/loans/example" for l in links))

    def test_independent_named_annual_basis_retains_currency_and_payment_conditions(self):
        from worker.pipeline.fpds_collection_accuracy import _captured_named_annual_basis
        a = parse_snapshot_bytes(body=(FIXTURES / "named-rate-basis.html").read_bytes(), content_type="text/html")
        basis = next(s for s in a.segments if s.anchor_type == "named_product_rate_basis")
        self.assertIn("Canadian dollar", basis.text)
        self.assertIn("rates per annum", basis.text)
        self.assertIn("last business day", basis.text)
        row = {"anchor_type": basis.anchor_type, "anchor_value": basis.anchor_value, "evidence_excerpt": basis.text, "source_url": "https://www.haventreebank.com/en-CA/legal"}
        mapping = {"annual_basis_evidence_chunk_id": "basis", "annual_basis_evidence_quote": basis.text, "annual_basis_product_name": "Everyday Growth Account"}
        record = {"product_name": "Everyday Growth Account", "product_type": "savings"}
        md = {"official_domain_allowlist": ["haventreebank.com"]}
        self.assertTrue(_captured_named_annual_basis(record, mapping, {"basis": row}, md))
        self.assertFalse(_captured_named_annual_basis(record, mapping, {}, md))
        self.assertFalse(_captured_named_annual_basis({"product_name": "Other Account"}, mapping, {"basis": row}, md))
        self.assertFalse(_captured_named_annual_basis(record, mapping, {"basis": {**row, "source_url": "https://otherbank.ca/legal"}}, md))
        self.assertFalse(_captured_named_annual_basis(record, mapping, {"basis": {**row, "evidence_excerpt": "annual rate 2.50%"}}, md))

    def test_sibling_expansion_omits_family_optional_facts_and_resolves_all_real_chunks(self):
        from worker.pipeline.fpds_extraction.service import _extract_grounded_named_account_variants
        from worker.pipeline.fpds_normalization.grounded_product_expansion import expand_grounded_product_inputs
        from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField
        from worker.pipeline.fpds_normalization.persistence import PsqlNormalizationRepository, NormalizationDatabaseConfig
        from unittest.mock import patch
        import json
        ctx, chunks = self._context_and_chunks()
        variants = _extract_grounded_named_account_variants(context=ctx, candidates=chunks)
        def field(name, value, metadata):
            return NormalizationExtractedField(field_name=name, candidate_value=value, value_type="string", confidence=1,
                extraction_method="test", source_document_id="doc", source_snapshot_id="snap", evidence_chunk_id=None,
                evidence_text_excerpt=None, anchor_type=None, anchor_value=None, page_no=None, chunk_index=None, field_metadata=metadata)
        item = NormalizationInput(source_id="source", source_document_id="doc", snapshot_id="snap", parsed_document_id="parsed",
            extraction_model_execution_id="model", extracted_storage_key="key", metadata_storage_key=None, bank_code="FNBC",
            country_code="CA", source_type="html", source_language="en", source_metadata=ctx.source_metadata,
            schema_context={"product_type": "chequing"}, extracted_fields=[field("product_name", "Family", {"grounded_product_variants": variants}),
                field("description_short", "Other product promotion", {}), field("currency", "USD", {})], evidence_links=[], runtime_notes=[])
        expanded = expand_grounded_product_inputs(item)
        self.assertEqual(len(expanded), 4)
        self.assertFalse(any(f.field_name in {"description_short", "currency"} for e in expanded for f in e.extracted_fields))
        self.assertEqual([e.source_metadata["product_name"] for e in expanded], [v["product_name"] for v in variants])
        repo = PsqlNormalizationRepository(NormalizationDatabaseConfig(database_url="postgresql://test.invalid/test", schema="public"))
        origins = [{"evidence_chunk_id": c.evidence_chunk_id, "evidence_excerpt": c.evidence_excerpt,
                    "anchor_type": c.anchor_type, "anchor_value": c.anchor_value} for c in chunks]
        with patch.object(repo, "_execute", return_value=json.dumps(origins)) as execute:
            resolved = repo.resolve_evidence_origins(run_id="run", inputs=[item])
        self.assertEqual(len(resolved), 1)
        queried = json.loads(execute.call_args.kwargs["variables"]["chunk_ids_json"])
        expected = {l.evidence_chunk_id for e in expanded for l in e.evidence_links}
        self.assertEqual(set(queried), expected)
        self.assertEqual(set(resolved[0].evidence_origins), expected)
        self.assertIn("ec.anchor_type", execute.call_args.args[0])
