"""Explicit denomination in bounded owned monetary declarations; no defaults."""
import re
from worker.native_dom_ownership import unique_heading, owns_label, local_notes


_LABEL = re.compile(
    r"\b(?:currency|denominated in|(?:required )?(?:initial|opening|minimum) deposit|"
    r"opening balance|maintaining balance|loan (?:amount|starts|up to)|borrow up to)\b", re.I)


def currency_records(soup):
    from worker.pipeline.fpds_collection_accuracy import CURRENCY_PATTERNS, _MONEY_AMOUNT
    root = soup.find('main') or soup.body or soup
    heading = unique_heading(root)
    if heading is None:
        return []
    owner = heading.get_text(' ', strip=True)
    records = []
    for node in root.find_all(['p', 'li', 'div', 'tr'])[:4096]:
        quote = node.get_text(' ', strip=True)
        if len(quote) > 700 or not _LABEL.search(quote):
            continue
        if node.find_parent(['nav', 'aside', 'footer', 'form']) or node.select('input, select, textarea, [role="slider"]'):
            continue
        if not re.search(_MONEY_AMOUNT, quote, re.I):
            continue
        codes = [code for code, pattern in CURRENCY_PATTERNS.items() if re.search(pattern, quote, re.I)]
        if len(codes) != 1 or not owns_label(node, root, owner):
            continue
        if re.search(r'\b(?:similar|other products|related products|you might|exchange|conversion|calculator|example)\b', quote, re.I):
            continue
        previous = node.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if previous is not None and previous.name != 'h1':
            scope = previous.get_text(' ', strip=True)
            from worker.native_information_records import names_match
            if re.search(r'\b(?:account|card|loan|mortgage|deposit)\b', scope, re.I) and not _LABEL.search(scope) and not names_match(scope, owner):
                continue
        notes = local_notes(soup, node)
        if notes is None:
            continue
        literal = '\n'.join([owner, quote, *notes])
        if len(literal) <= 1500 and literal not in [q for _, q in records]:
            records.append((owner, literal))
    return records
