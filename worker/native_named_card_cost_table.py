"""Complete named card-cost tables; monthly and annual units remain literal."""
import re
from decimal import Decimal
from worker.native_dom_ownership import owns_label, local_notes


_LABELS = {'Annual Membership Fee', 'Interest Charge', 'Cash Advance Service Fee and Interest Charge', 'Late Payment Charge', 'Over Credit Limit Fee'}


def table_parts(quote):
    lines = [x.strip() for x in str(quote).splitlines() if x.strip()]
    if len(lines) < 8 or lines[1] != 'Fees and Charges':
        return None
    rows = {}
    key = None
    for line in lines[2:]:
        if line in _LABELS:
            if line in rows:
                return None
            key = line
            rows[key] = []
        elif key:
            rows[key].append(line)
        else:
            return None
    if not {'Annual Membership Fee', 'Interest Charge', 'Cash Advance Service Fee and Interest Charge'} <= rows.keys():
        return None
    rows = {key: ' '.join(value) for key, value in rows.items()}
    interest = rows['Interest Charge']
    pair = re.fullmatch(r'(\d+(?:\.\d+)?)% per month or (\d+(?:\.\d+)?)% effective rate annually', interest, re.I)
    if not pair or not all(0 <= Decimal(n) < 100 for n in pair.groups()):
        return None
    if not rows['Cash Advance Service Fee and Interest Charge']:
        return None
    # Exact purchase denomination and full payment trigger make this the
    # regular card charge, distinct from its cash-advance or instalment price.
    if not re.search(r'All your purchases, .+? are billed in .+? to allow you to keep your foreign currenc(?:y|ies) intact[.]', ' '.join(lines), re.I):
        return None
    if not re.search(r'An Interest Charge will be billed if your payment on or before the Payment Due Date is less than your Total Statement Balance[.]', ' '.join(lines), re.I):
        return None
    return lines[0], rows


def annual_fee_value(quote):
    parts = table_parts(quote)
    if not parts:
        return None
    fee = parts[1]['Annual Membership Fee']
    # Different existing-customer principal prices are alternatives, not one fee.
    if len(re.findall(r'Principal Card:', fee, re.I)) != 1 or re.search(r'\bexisting\b', fee, re.I):
        return None
    principal = re.fullmatch(r'Principal Card:\s*(.+?)\s+Supplementary Card:\s*.+', fee, re.I)
    if not principal:
        return None
    price = principal[1]
    if price.casefold() == 'waived perpetually':
        return Decimal(0)
    from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
    amount = re.match(_MONEY_AMOUNT, price, re.I)
    if not amount or Decimal(amount[1].replace(',', '')) <= 0:
        return None
    suffix = price[amount.end():].strip()
    # Preserve only explicitly printed annual base costs. Monthly alternatives
    # are not multiplied, and neither first-year nor spend waivers become zero.
    if suffix and not (re.fullmatch(r'\(FREE on the 1st year\)', suffix, re.I)
        or re.fullmatch(r'\(Automatically waived upon reaching .+ accumulated spend for the past 12 months from card anniversary date\)', suffix, re.I)
        or re.fullmatch(r'\* or .+/month', suffix, re.I)):
        return None
    return Decimal(amount[1].replace(',', ''))


def named_card_cost_tables(soup):
    root = soup.find('main') or soup.body or soup
    headings = {' '.join(h.get_text(' ', strip=True).split()) for h in root.find_all('h1')}
    output = []
    for table in root.find_all('table')[:128]:
        if table.find_parent(['nav', 'aside', 'footer', 'form']):
            continue
        header = table.find('thead')
        cells = header.find_all('th') if header else []
        if len(cells) != 1:
            continue
        title = ' '.join(cells[0].get_text(' ', strip=True).split())
        match = re.fullmatch(r'(.{4,180}?) Fees and Charges', title)
        if not match:
            continue
        owner = match[1]
        # A second actual product H1 is ambiguous. An explicitly administrative
        # Note heading is retained in normal parsed text, never treated as a name.
        if owner not in headings or headings - {owner, 'Important Note:', 'Important Note'}:
            continue
        if not owns_label(table, root, owner):
            continue
        lines = [owner, 'Fees and Charges']
        valid = True
        for row in table.select('tbody > tr'):
            cells = row.find_all(['th', 'td'], recursive=False)
            if len(cells) != 2:
                valid = False
                break
            label, value = [' '.join(c.get_text(' ', strip=True).split()) for c in cells]
            if label not in _LABELS or not value:
                valid = False
                break
            lines.extend([label, value])
        notes = local_notes(soup, table)
        if not valid or notes is None:
            continue
        declarations = []
        for paragraph in root.find_all('p')[:2048]:
            text = ' '.join(paragraph.get_text(' ', strip=True).split())
            if not (text.startswith('All your purchases,') or 'An Interest Charge will be billed if' in text):
                continue
            if (len(text) > 1000 or paragraph.find_parent(['aside', 'nav', 'footer', 'form', 'table'])
                    or not owns_label(paragraph, root, owner)):
                continue
            paragraph_notes = local_notes(soup, paragraph)
            if paragraph_notes is None:
                continue
            declarations.extend([text, *paragraph_notes])
        quote = '\n'.join([*lines, *notes, *dict.fromkeys(declarations)])
        if len(quote) <= 6400 and table_parts(quote):
            output.append(('named_card_cost_table', owner, quote))
    return list(dict.fromkeys(output))
