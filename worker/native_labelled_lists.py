"""Bounded literal financial list labels and their observed disclosure links."""
import re
from worker.native_dom_ownership import owns_label


def financial_label_text(value):
    # Used only to recognize a label; original source text stays in the record.
    return re.sub(r"(?:[\s*\u2020\u2021]|footnote (?:star|dagger|\d+))+$", "", str(value).strip(), flags=re.I).strip()


def linked_list_notes(soup, block, label, owner):
    row = block if block.name == 'li' else block.find_parent('li')
    if row is None:
        from worker.native_dom_ownership import local_notes
        if financial_label_text(label) != str(label).strip() and not local_notes(soup, block):
            return None
        return []
    literal = row.get_text(' ', strip=True)
    marked = bool(re.search(r"[*\u2020\u2021]|footnote (?:star|dagger)", literal, re.I))
    if not marked:
        return []
    # Existing same-document references must resolve through local_notes.
    if row.select('[href^="#"], [aria-describedby], [data-target^="#"]'):
        return []
    for scope in [row, *list(row.parents)[:4]]:
        if scope.name in {'main', 'body', 'html'} or len(scope.get_text()) > 8000:
            break
        if not owns_label(scope, soup.find('main') or soup.body or soup, owner):
            return None
        links = {}
        for a in scope.find_all('a', href=True):
            href = str(a['href'])
            description = a.get_text(' ', strip=True) + ' ' + str(a.get('aria-label', ''))
            if re.search(r"credit terms|terms and conditions|summary of credit terms", description, re.I) and re.match(r'https://|/', href) and not href.startswith('//'):
                links.setdefault(href, []).append(a.get_text(' ', strip=True))
        if links:
            if len(links) != 1:
                return None
            href, labels = next(iter(links.items()))
            return [*[x for x in dict.fromkeys(labels) if re.search(r'terms', x, re.I)], href]
    return None



def pdf_purchase_terms(layout, plain):
    """Read complete named purchase columns; never choose a range endpoint."""
    lines = str(layout).splitlines()
    headers = [i for i, line in enumerate(lines) if line.lstrip().startswith('Interest Rates and')]
    if len(headers) != 1:
        return []
    hi = headers[0]
    parts = list(re.finditer(r'(?<!\S)\S.*?(?=\s{2,}|$)', lines[hi]))
    columns = [m.start() for m in parts if m.start() > 20 and len(m[0].split()) >= 2]
    starts = [i for i in range(hi + 1, min(hi + 6, len(lines))) if lines[i].lstrip().startswith('Annual Percentage')]
    stops = [i for i in range(hi + 1, len(lines)) if lines[i].lstrip().startswith('APR for Balance')]
    if not 2 <= len(columns) <= 8 or len(starts) != 1 or len(stops) != 1 or stops[0] <= starts[0]:
        return []
    owners = []
    for ci, left in enumerate(columns):
        right = columns[ci + 1] if ci + 1 < len(columns) else None
        name = ' '.join(lines[i][left:right].strip() for i in range(hi, starts[0]) if lines[i][left:right].strip())
        name = ' '.join(name.split())
        if not re.search(r'\b(?:Credit Card|Visa|Mastercard)\b', name, re.I) or len(name) > 180:
            return []
        owners.append(name)
    if len(set(owners)) != len(owners):
        return []
    shared = []
    for start, end in [('Loss of Introductory APR:', 'Penalty Fees:'), ('Promotional/Introductory Rates and Your Grace Period:', 'NOTICE TO')]:
        matches = list(re.finditer(re.escape(start) + r'(.*?)' + re.escape(end), plain, re.S))
        if len(matches) != 1:
            return []
        shared.append(' '.join((start + matches[0][1]).split()))
    content_columns = []
    for column in columns:
        observed = [m.start() for line in lines[starts[0]:stops[0]]
                    for m in re.finditer(r"(?<!\S)\S.*?(?=\s{2,}|$)", line)
                    if abs(m.start() - column) <= 8]
        if not observed:
            return []
        content_columns.append(min(observed))
    records = []
    for ci, left in enumerate(content_columns):
        right = content_columns[ci + 1] if ci + 1 < len(content_columns) else None
        cell = ' '.join(lines[i][left:right].strip() for i in range(starts[0], stops[0]) if lines[i][left:right].strip())
        # PDF glyph spacing is formatting; all original bytes remain pinned.
        cell = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', cell)
        cell = re.sub(r'(\d)\s+%', r'\1%', cell)
        cell = ' '.join(cell.split())
        percentages = re.findall(r'(?<![\d.])\d+(?:\.\d+)?%', cell)
        if (len(percentages) not in {2, 3} or not re.search(r'creditworthiness', cell, re.I)
                or not re.search(r'Prime Rate', cell) or not cell.endswith('Prime Rate.')
                or (len(percentages) == 3 and not re.search(r'^0% introductory APR for \d+ months from account opening date[.]', cell))):
            return []
        quote = '\n'.join([owners[ci], 'Annual Percentage Rate (APR) for Purchases', cell, *shared])
        if len(quote) > 6400:
            return []
        records.append(('named_card_apr_terms', owners[ci], quote))
    return records
