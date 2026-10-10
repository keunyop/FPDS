"""Complete single-card PDF disclosures, including every continuation page."""
import re
from urllib.parse import urlsplit
from worker.native_information_records import names_match, name_key


def issuer_product_match(owner, identity, url):
    if names_match(owner, identity):
        return True
    left, right = name_key(owner).split(), name_key(identity).split()
    if len(right) < 3 or len(left) <= len(right) or left[-len(right):] != right:
        return False
    issuer = ''.join(left[:-len(right)])
    host = (urlsplit(url).hostname or '').removeprefix('www.').split('.')
    return bool(issuer and issuer in host[:-1])


def single_card_purchase_records(pages):
    if not 2 <= len(pages) <= 4 or any(not p.strip() for p in pages):
        return []
    first = ' '.join(pages[0].split())
    full = ' '.join(' '.join(pages).split())
    names = list(re.finditer(r'(.{4,150}?Credit Card) Pricing Information Disclosure Interest Rates and Interest Charges ', first))
    if len(names) != 1 or full.count('Pricing Information Disclosure') != 1:
        return []
    owner = names[0][1].strip()
    start = names[0].end()
    purchase = re.match(r'Purchase Annual Percentage Rate \(APR\) (.+?) Balance Transfer APR\b',first[start:])
    if not purchase or not re.fullmatch(r'\d+(?:\.\d+)?% to \d+(?:\.\d+)?%, based on your creditworthiness[.] These APRs will vary\s*with the market based on the Prime Rate[.]',purchase[1]):
        return []
    grace = re.search(r'Paying Interest (.+?) Minimum Interest Charge\b',first)
    continuation = '\n'.join(pages[1:])
    if (not grace or '(continued)' not in first
            or not all(x in continuation for x in ['How We Will Calculate Your Variable APRs:', 'Prime Rate:', 'CONDITIONS:'])
            or not re.search(r'current rate is \d+(?:\.\d+)?% as of [A-Za-z]+ \d{1,2}, \d{4}', ' '.join(continuation.split()))):
        return []
    quote='\n'.join([owner,'Purchase Annual Percentage Rate (APR)',purchase[1],'Paying Interest',grace[1],continuation])
    if len(quote)>6400:
        return []
    out=[('single_card_purchase_terms',owner,quote)]
    fee=re.search(r' Fees Annual Fee (.+?) Transaction Fees ',first)
    if fee and single_card_fee_value(owner+'\nAnnual Fee '+fee[1]) is not None:
        out.append(('single_card_annual_fee',owner,owner+'\nAnnual Fee '+fee[1]))
    return out


def single_card_fee_value(quote):
    from decimal import Decimal
    lines=str(quote).splitlines()
    if len(lines)!=2 or not re.fullmatch(r'.{4,150}Credit Card',lines[0]):
        return None
    match=re.fullmatch(r'Annual Fee \$(\d+(?:\.\d+)?)(?: \(None\))?',lines[1])
    if not match:
        return None
    amount=Decimal(match[1])
    if '(None)' in lines[1] and amount!=0:
        return None
    return amount
