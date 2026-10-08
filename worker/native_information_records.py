"""Literal, bounded financial records from native information boxes and grids."""
from __future__ import annotations
import re
from decimal import Decimal
from bs4 import BeautifulSoup, Tag

TERM = re.compile(r'^\d+\s*[- ]?\s*(?:months?|years?)\s+(?:open|closed)(?:\s*\([^\n]+\))?$', re.I)
RATE = re.compile(r'^\d+(?:\.\d+)?%$')


def name_key(value):
    return ' '.join(re.findall(r'[a-z0-9]+', str(value).casefold().replace('\u00ad', '').replace('+', ' plus ')))


def names_match(left, right):
    def key(value):
        return tuple(t for t in name_key(value).split() if t not in {'credit', 'card', 'cards', 'mastercard', 'visa', 'r', 'tm'})
    return bool(key(left)) and key(left) == key(right)


def _note(soup, target_id):
    targets = soup.find_all(id=target_id)
    if len(targets) != 1:
        return None
    target = targets[0]
    if target.find_parent('table') is not None:
        return None
    # A numeric return anchor owns the following prose only until the next
    # explicit note anchor. Copy literal strings; do not import sibling notes.
    if len(target.get_text(' ', strip=True)) <= 4:
        container = target.find_parent(['p', 'li'])
        if container is None:
            return None
        parts, started = [], False
        for node in container.descendants:
            if node is target:
                started = True
            elif started and isinstance(node, Tag) and node.get('id') and node.get('id') != target_id:
                break
            if started and isinstance(node, str) and node.strip():
                parts.append(node.strip())
        value = ' '.join(parts)
    else:
        value = target.get_text('\n', strip=True)
    return value if len(value) > 15 and len(value) <= 3000 else None


def record_notes(soup, scope):
    notes = []
    for link in scope.select('a[href^="#"]'):
        href = link.get('href', '')
        if href == '#' and link.get('data-toggle') == 'popover' and link.get('data-content'):
            note = BeautifulSoup(link['data-content'], 'html.parser').get_text(' ', strip=True)
        else:
            note = _note(soup, href[1:]) if len(href) > 1 else None
        if not note:
            return None
        if note not in notes:
            notes.append(note)
    return notes


def mortgage_terms(quote):
    lines = [line.strip() for line in str(quote).splitlines() if line.strip()]
    return [lines[i] for i in range(len(lines)-1) if TERM.fullmatch(lines[i]) and RATE.fullmatch(lines[i+1])]


def html_information_records(soup):
    result = []
    for table in soup.find_all('table')[:64]:
        rows = table.find_all('tr')
        if not rows:
            continue
        heads = rows[0].find_all(['th', 'td'], recursive=False)
        if len(heads) != 2:
            continue
        owner = heads[0].get_text(' ', strip=True)
        # An exact product-name header plus inner Fixed/Variable term/APR
        # subheaders binds the loan rows. Reference/positive-balance rows are
        # outside these subgroups and cannot become borrowing facts.
        if heads[1].get_text(' ', strip=True).casefold() == 'rate':
            records, mode, invalid = [], None, False
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'], recursive=False)
                if len(cells) != 2:
                    invalid = True; break
                label = cells[0].get_text(' ', strip=True)
                value = cells[1].get_text(' ', strip=True)
                if re.match(r'^(?:Fixed|Variable)[- ]rate (?:sub-account )?terms\b', label, re.I):
                    if not re.search(r'\bAPR\s*\(\s*%\s*\)', value, re.I):
                        invalid = True; break
                    notes = record_notes(soup, row)
                    if notes is None:
                        invalid = True; break
                    mode = [label, value, *notes]
                    records.extend(mode)
                elif TERM.fullmatch(label):
                    if mode is None or not RATE.fullmatch(value):
                        invalid = True; break
                    notes = record_notes(soup, row)
                    if notes is None:
                        invalid = True; break
                    records.extend([label, value, *notes])
                else:
                    mode = None
            quote = '\n'.join([owner, *records])
            terms = mortgage_terms(quote)
            if not invalid and terms and len(terms) == len(set(terms)) and len(quote) <= 6400:
                result.append(('named_mortgage_rate_schedule', owner, quote))
                # Literal term cells are a separate bounded field record. The
                # complete rate schedule above retains all APR conditions.
                result.append(('named_mortgage_term_schedule', owner, '\n'.join(terms)))
        if name_key(owner) == 'credit limit' and name_key(heads[1].get_text()) in {'interest', 'interest rate', 'annual interest rate'}:
            scope = table.find_parent('section') or table
            notes = record_notes(soup, scope)
            # Some tables refer to their annual-unit note in the adjacent owned
            # headline rate. Only an explicit link in the same rate component
            # establishes that relation, never a document-wide annual assertion.
            if notes == []:
                parent = scope.parent
                for _ in range(3):
                    if parent is None or len(parent.find_all('table')) != 1:
                        break
                    candidates = record_notes(soup, parent)
                    if candidates:
                        notes = candidates; break
                    parent = parent.parent
            if not notes and len(soup.find_all('h1')) == 1:
                for link in soup.select('a[href^="#"]'):
                    for block in list(link.parents)[:4]:
                        label = block.get_text(' ', strip=True)
                        if len(label) > 350:
                            break
                        if re.search(r'\bline of credit rate\b', label, re.I) and re.search(r'\d+(?:\.\d+)?\s*%',label):
                            candidates = record_notes(soup, block)
                            if candidates and any(re.search(r'all rates are annual rates',n,re.I) for n in candidates):
                                notes = candidates
                            break
                    if notes:
                        break
            grid = table.get_text('\n', strip=True)
            quote = '\n'.join([grid, *(notes or [])])
            if notes is not None and re.search(r'all rates are annual rates|annual interest rate', quote, re.I) and re.search(r'\d+(?:\.\d+)?%', grid) and len(quote) <= 6400:
                result.append(('credit_limit_rate_schedule', owner, quote))
    return result


def pdf_information_records(page_text, *, page_no):
    lines = str(page_text).splitlines()
    names = [line.strip() for line in lines if re.fullmatch(r'.+?\bCard Information Box', line.strip(), re.I)]
    if len(names) != 1:
        return _shared_pdf_records(page_text)
    owner = re.sub(r'\s+Information Box$', '', names[0], flags=re.I)
    start = re.search(r'(?mi)^Annual Interest\s*\nRates\s*\n', page_text)
    end = re.search(r'(?mi)^Interest-free\s*\nGrace Period\b', page_text)
    output = []
    if start and end and start.end() < end.start():
        quote = '\n'.join([owner, page_text[start.start():end.start()].strip()])
        if information_card_rates(quote) and len(quote) <= 6400:
            output.append(('card_information_rate', owner, quote))
    fee = re.search(r'(?mi)^Annual Fees\s+\$[^\n]+(?:\n(?!\d+\s*$|Installment Fee\b|Other Fees\b)[^\n]+)*', page_text)
    if fee and len(fee[0]) <= 1500:
        output.append(('card_information_fee', owner, '\n'.join([owner, fee[0]])))
    return output


def information_card_rates(quote):
    """Explicit ordinary labelled AIRs; preserve a separate complete default rule."""
    match = re.search(r'Annual Interest\s+Rates\s+These interest rates are in effect the day your account is opened \(whether or not your card is activated\)\.\s+Purchases, fees,? and other charges:\s*(\d+(?:\.\d+)?)%\s+Cash Advances and Balance Transfers:\s*(\d+(?:\.\d+)?)%', str(quote), re.I)
    if not match or len(re.findall(r'Purchases, fees,? and other charges:\s*\d',str(quote),re.I)) != 1:
        return None
    tail = str(quote)[match.end():].strip()
    if tail:
        if not re.fullmatch(r'If you do not make your minimum payment by the payment due date \d+ or more times in any \d+-month period,\s+your annual interest rates will increase to standard rates of \d+(?:\.\d+)?% on Purchases, fees,? and other charges\s+and \d+(?:\.\d+)?% for Cash Advances and Balance Transfers, including those done under any previous rate\.\s+This increase will take effect in the third statement period following the missed payment that caused the rate\s+to\s+increase\. The increased rates will remain in effect until you make your minimum payments by the due date for\s+\d+ consecutive months\.', tail, re.I):
            return None
    values = tuple(Decimal(v) for v in match.groups())
    return values if all(v.is_finite() and 0 <= v < 100 for v in values) else None


def shared_card_rates(quote):
    from worker.native_application_disclosures import application_card_rates
    application = application_card_rates(quote)
    if application is not None:
        return application
    summary = summary_card_rates(quote)
    if summary is not None:
        return summary
    match = re.search(r'Annual\s+interest rates\s+Regular interest rates:\s+Cards Purchases Cash advances and balance\s+transfers\s+(.+?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%', str(quote), re.I | re.S)
    if not match or len(match[1]) > 1000 or '%' in match[1]:
        return None
    return tuple(Decimal(x) for x in match.groups()[1:])


def shared_card_fee(quote):
    match = re.fullmatch(r'Annual fees\s+Cards Main card Additional card\s+([^$\n]+)\s+\$(\d+(?:\.\d+)?)\s+\$(\d+(?:\.\d+)?)', str(quote).strip(), re.I)
    if not match or re.search(r'\b(?:if|first|eligible|students?|privilege|until|waiv|reduced interest rate)\b', match[1], re.I):
        return None
    return Decimal(match[2])


def _shared_pdf_records(page_text):
    output = []
    regular = re.search(r'Annual\s+interest rates\s+Regular interest rates:\s+Cards Purchases Cash advances and balance\s+transfers\s+(.+?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%', page_text, re.I | re.S)
    if regular and len(regular[1]) <= 1000:
        # The selected literal row keeps its unit/header and every applicable
        # default/payment rule. Other product rates are not its scalar proof.
        scope = re.search(r'Transactions charged.+?(?=Interest-free)', page_text, re.I | re.S)
        quote = regular[0] + ('\n' + scope[0].strip() if scope else '')
        if shared_card_rates(quote) and len(quote) <= 6400:
            names = re.split(r',|\band\b', re.sub(r'\s+', ' ', regular[1]), flags=re.I)
            output.extend(('named_card_regular_rates', n.strip(), quote) for n in names if n.strip())
    fee_start = re.search(r'Annual fees\s+Cards Main card Additional card\s+', page_text, re.I)
    if fee_start:
        for line in page_text[fee_start.end():].splitlines():
            quote = 'Annual fees\nCards Main card Additional card\n' + line.strip()
            if shared_card_fee(quote) is not None:
                label = line.split('$', 1)[0].strip()
                # Only literal names without qualifier suffixes are owners.
                for name in re.split(r',|\band\b', label, flags=re.I):
                    if name.strip():
                        output.append(('named_card_fee_row', name.strip(), quote))
    # Named GIC disclosures establish annual units without donating a rate.
    title = re.search(r'^(.+?Guaranteed\s+Investment\s+Certificate\s*\(GIC\))', page_text, re.I | re.S)
    annual = re.search(r'Annual interest rate\s+.+?(?=Type of interest)', page_text, re.I | re.S)
    if title and annual and len(title[1]) <= 200 and len(annual[0]) <= 1800:
        owner = re.sub(r'Guaranteed\s+Investment\s+Certificate\s*\(GIC\)', 'GIC', title[1], flags=re.I)
        owner = re.sub(r'\s+', ' ', owner).strip()
        output.append(('named_product_rate_basis', owner, owner + '\n' + annual[0].strip()))
        terms = re.search(r'Type of interest\s+.+?(?=Fees\s)', page_text, re.I | re.S)
        if terms and len(terms[0]) <= 3000:
            output.append(('named_product_interest_terms', owner, owner + '\n' + terms[0].strip()))
    return output


_SUMMARY_DEFAULT = re.compile(
    r'If you do not make your Required Payment by the payment due date \d+ times in any \d+ month '
    r'period, your interest rate may increase to \d+(?:\.\d+)?% on Purchases and \d+(?:\.\d+)?% on Cash Advances, '
    r'Balance Transfers and Convenience Cheques for at least \d+ months\. This increase will take effect in '
    r'the third statement period following the missed payment that caused the rate to increase\. '
    r'Required Payment means: a\) any interest; plus b\) fees \(excluding the annual fee\); plus '
    r'c\) any past due amount; plus d\) the lesser of either \$\d+(?:\.\d+)?, or your Balance minus a\) to c\)\. '
    r'If your Balance is under \$\d+(?:\.\d+)?, that lesser amount is your Minimum Payment\.', re.I)


def summary_card_rates(quote):
    """One explicit annual purchase/cash row with its complete default disclosure."""
    lines = [' '.join(line.split()) for line in str(quote).splitlines() if line.strip()]
    # Normalization prefixes the real anchor owner to the complete excerpt.
    # Accept only that exact same owner; never discard arbitrary preceding copy.
    if len(lines) >= 10 and lines[0] == lines[4] + ' Annual':
        lines[0] = 'Annual'
    if (len(lines) < 10 or lines[:4] != ['Annual', 'Interest', 'Rates', 'Card Product']
            or lines[5] != 'Purchases' or lines[7:9] != ['Cash Advances, Balance Transfers', 'and Convenience Cheques']
            or not re.fullmatch(r'\d+(?:\.\d+)?%', lines[6])
            or not re.fullmatch(r'\d+(?:\.\d+)?%', lines[9])
            or re.search(r'\b(?:if|except|eligible|introductory|promotional|retired|no longer)\b', lines[4], re.I)):
        return None
    tail = ' '.join(lines[10:])
    # Truncated, changed or additional qualifications never become ordinary AIRs.
    if not _SUMMARY_DEFAULT.fullmatch(tail):
        return None
    values = tuple(Decimal(lines[i][:-1]) for i in [6, 9])
    return values if all(0 <= v < 100 for v in values) else None


def pdf_summary_records(layout):
    """Retain literal PDF column ownership, wrapped identity and full conditions.

    This bounded layout has one product/rate pair. Multi-product rows, missing
    columns/units, extra percentages and unresolved notes fail closed.
    """
    lines = str(layout).splitlines()
    headers = [(i, re.search(r'Card Product', line), re.search(r'(?<!\S)Purchases(?!\S)', line),
                re.search(r'Cash Advances, Balance Transfers', line))
               for i, line in enumerate(lines) if 'Card Product' in line]
    if len(headers) != 1:
        return []
    hi, product, purchase, cash = headers[0]
    if not all([product, purchase, cash]) or not product.end() < purchase.start() < cash.start():
        return []
    left = (product.end() + purchase.start()) // 2
    right = (purchase.end() + cash.start()) // 2
    annual = [line[:product.start()].strip() for line in lines[hi:hi+3] if line[:product.start()].strip()]
    if annual != ['Annual', 'Interest', 'Rates']:
        return []
    stops = [i for i in range(hi+3, len(lines)) if re.match(r'\s*Interest-\s+', lines[i])]
    if len(stops) != 1:
        return []
    body = lines[hi+3:stops[0]]
    pairs = [(i, line[left:right].strip(), line[right:].strip()) for i, line in enumerate(body)
             if re.fullmatch(r'\d+(?:\.\d+)?%', line[left:right].strip())
             and re.fullmatch(r'\d+(?:\.\d+)?%', line[right:].strip())]
    if len(pairs) != 1:
        return []
    ri, buy, advance = pairs[0]
    names = []
    ni = ri
    while ni > 0 and body[ni-1].strip():
        ni -= 1
    end = ri + 1
    while end < len(body) and body[end].strip():
        end += 1
    for line in body[ni:end]:
        name = line[:left].strip()
        if name:
            names.append(name)
        if line != body[ri] and (line[left:right].strip() or line[right:].strip()):
            return []
    owner = ' '.join(names)
    if not owner or len(owner) > 200 or not re.search(r'\b(?:Visa|Mastercard|Card)\b',owner,re.I):
        return []
    # The complete rest of the annual-rate cell belongs to this single named row.
    notes = '\n'.join(' '.join(line.split()) for line in body[end:] if line.strip())
    cash_continuation = lines[hi+1][right:].strip()
    quote = '\n'.join([*annual, product[0], owner, purchase[0], buy, cash[0], cash_continuation, advance, notes])
    return [('named_card_regular_rates', owner, quote)] if summary_card_rates(quote) and len(quote) <= 6400 else []
