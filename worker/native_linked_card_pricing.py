"""Anonymous pricing tables require a captured current detail-to-terms link.

These records never supply product identity or a scalar purchase APR. Keep the
whole rate table, post-table disclosures and every referenced literal footnote.
"""
import re
from decimal import Decimal
from worker.native_dom_ownership import local_notes

TERMS_ANCHOR = 'linked_card_pricing_terms'
MAX_PRICING_RECORD_CHARS = 8000
LINK_KEYS = ('applicability_evidence_chunk_id', 'applicability_evidence_quote', 'applicability_product_name')


def pricing_records(soup):
    tables = [t for t in soup.find_all('table') if re.search(r'Purchase Annual Percentage Rate \(APR\)', t.get_text(' ', strip=True), re.I)]
    if len(tables) != 1:
        return []
    table = tables[0]
    rows = {}
    for tr in table.find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if len(cells) != 2:
            continue
        label = ' '.join(cells[0].get_text(' ', strip=True).split())
        if label in rows:
            return []
        rows[label] = cells[1]
    required = ['Purchase Annual Percentage Rate (APR)', 'Penalty APR and When It Applies', 'How to Avoid Paying Interest on Purchases']
    if not all(key in rows for key in required):
        return []
    purchase = rows[required[0]].get_text(' ', strip=True)
    intervals = re.findall(r'(\d+(?:\.\d+)?)%\s+to\s+(\d+(?:\.\d+)?)%', purchase)
    interval = (len(intervals) == 1 and 0 <= Decimal(intervals[0][0]) <= Decimal(intervals[0][1]) < 100
        and re.search(r'based on your creditworthiness', purchase, re.I))
    single = re.fullmatch(r'(\d+(?:\.\d+)?)%\s*[.] This APR will vary with the market based on the Prime Rate[.]\s*[a-z]', ' '.join(purchase.split()))
    if not interval and not (single and 0 <= Decimal(single[1]) < 100):
        return []
    if not re.search(r'vary with the market based on the Prime Rate', purchase, re.I):
        return []
    # Only an independently bounded pricing section may supply these facts.
    # Following terms are a separate section; don't clip a paragraph or a note.
    fee_tables = [t for t in table.find_next_siblings('table') if re.match(r'Fees\b', t.get_text(' ', strip=True))]
    if len(fee_tables) != 1:
        return []
    disclosures = []
    reached_terms = False
    for node in fee_tables[0].find_next_siblings():
        literal = ' '.join(node.get_text(' ', strip=True).split())
        if re.fullmatch(r'TERMS\s*&\s*CONDITIONS', literal, re.I):
            reached_terms = True
            break
        if literal:
            if node.name != 'p':
                return []
            disclosures.append(literal)
    if not reached_terms or not any(re.match(r'Prime Rate: Variable APRs are based on the \d+(?:\.\d+)?% Prime Rate as of \d{1,2}/\d{1,2}/\d{4}[.]', d) for d in disclosures):
        return []
    if re.search(r'Intro APR', purchase, re.I) and not any(re.match(r'Loss of Intro APR:', d) for d in disclosures):
        return []
    markers = {s.get_text('', strip=True) for s in table.find_all('sup') if s.get_text('', strip=True) not in {'SM', 'R', '®', '™'}}
    # Every letter marker resolves once in the captured pricing section.
    if any(not re.fullmatch(r'[a-z]', marker) or len([d for d in disclosures if d.startswith(marker+' ')]) != 1 for marker in markers):
        return []
    notes = local_notes(soup, table)
    if notes is None:
        return []
    quote = '\n'.join(['Pricing Information', table.get_text(' ', strip=True), *disclosures, *notes])
    if len(quote) > MAX_PRICING_RECORD_CHARS or '\x00' in quote or '\ufffd' in quote:
        return []
    return [(TERMS_ANCHOR, 'Pricing Information', quote)]


def detail_link(candidates, target_url, detail_url):
    from urllib.parse import urljoin
    from worker.pipeline.fpds_collection_accuracy import canonical_url
    matches = [c for c in candidates if c.anchor_type == 'captured_disclosure_link'
        and canonical_url(urljoin(detail_url, c.evidence_excerpt)) == canonical_url(target_url)]
    return min(matches, key=lambda c: c.chunk_index) if matches else None


def stored_link_belongs(record, mapping, evidence, source_metadata, origin):
    """Only DB-resolved same-run origins, never model-supplied URL metadata."""
    from urllib.parse import urljoin
    from worker.pipeline.fpds_collection_accuracy import canonical_url, exact_quote
    from worker.native_information_records import names_match
    link = next((e for e in evidence if e.get('evidence_chunk_id') == mapping.get(LINK_KEYS[0])), None)
    detail = canonical_url(source_metadata.get('normalized_source_url') or source_metadata.get('source_url'))
    if not link or not detail or not names_match(mapping.get(LINK_KEYS[2]), record.get('product_name')):
        return False
    return bool(link.get('anchor_type') == 'captured_disclosure_link'
        and canonical_url(link.get('source_url')) == detail
        and link.get('bank_code') == record.get('bank_code')
        and link.get('country_code') == record.get('country_code')
        and exact_quote(mapping.get(LINK_KEYS[1]), link.get('evidence_excerpt'))
        and exact_quote(link.get('evidence_excerpt'), mapping.get(LINK_KEYS[1]))
        and canonical_url(urljoin(detail, link['evidence_excerpt'])) == canonical_url(origin))
