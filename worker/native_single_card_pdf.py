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
    extended = extended_card_purchase_records(pages)
    if extended:
        return extended
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
    if lines[1] == 'Annual Fee None':
        return Decimal(0)
    match=re.fullmatch(r'Annual Fee \$(\d+(?:\.\d+)?)(?: \(None\))?',lines[1])
    if not match:
        return None
    amount=Decimal(match[1])
    if '(None)' in lines[1] and amount!=0:
        return None
    return amount


def extended_card_purchase_records(pages):
    """Named application terms: complete pricing plus bounded continuation.

    The administrative Credit Reports section closes the financial disclosure;
    every purchase/grace/index/eligibility paragraph before it remains atomic.
    No issuer or URL exception supplies ownership, prices or missing conditions.
    """
    if not 2 <= len(pages) <= 12 or any(not p.strip() for p in pages):
        return []
    normalized = [' '.join(p.split()) for p in pages]
    first, continuation = normalized[:2]
    heading = 'Important Credit Card Terms and Conditions'
    if first.count(heading) != 1:
        return []
    intro, sep, pricing = first.partition('Interest Rates and Interest Charges')
    if not sep or heading not in intro:
        return []
    owners = re.findall(r'(?:in the|and the) ([A-Z][^.]{3,90}?Credit Card) (?:Agreement|reward program)', intro)
    owners = [o for o in owners if name_key(o) != 'personal credit card']
    if len(owners) < 2 or any(not names_match(owners[0], o) for o in owners):
        return []
    owner = owners[0]
    purchase = re.match(r' Annual Percentage Rate \(APR\) for Purchases: (.+?) APR for Balance Transfers:', pricing)
    if not purchase or not re.search(r'(?:All APRs|This APR) will vary with the market based on the Prime Rate[.]', purchase[1]):
        return []
    from decimal import Decimal
    rates = re.findall(r'(\d+(?:\.\d+)?)%', purchase[1])
    if not rates or any(not 0 <= Decimal(r) < 100 for r in rates):
        return []
    if len(rates) > 1 and 'based on your creditworthiness' not in purchase[1]:
        return []
    financial, end, administration = pricing.partition('Procedures for Opening a New Account')
    following, boundary, reports = continuation.partition('Credit Reports:')
    if not end or not boundary or not following.rstrip().endswith('.'):
        return []
    if not all(label in financial for label in ['Paying Interest:', 'Minimum Interest Charge:', 'Annual Fee:', 'Transaction Fees:', 'How We Will Calculate Your Balance:']):
        return []
    if not all(label in following for label in ['How the Variable APRs on your Account are Determined:', 'Margins:', 'Index:', 'Card Eligibility:', 'Balance Transfers:', 'Introductory or Promotional APRs on Balance transfers:']):
        return []
    if not re.search(r'As of [A-Za-z]+ \d{1,2}, \d{4} the Prime Rate was \d+(?:\.\d+)?%[.]', following):
        return []
    # A second price table or restated annual fee anywhere else is ambiguous.
    remainder = ' '.join([administration, reports, *normalized[2:]])
    if re.search(r'\bAPRs?\b|\bannual fees?\b|\binterest rates?\b|\b(?:pay|charge|bear|accrue|purchase|increased?|waived?)\s+(?:you\s+)?interest\b', remainder, re.I):
        return []
    quote = owner + '\nInterest Rates and Interest Charges' + financial + '\n' + following
    if len(quote) > 8000 or any(c in quote for c in ['\x00', '\ufffd']):
        return []
    result = [('single_card_purchase_terms', owner, quote)]
    fee = re.search(r'Annual Fee: (.+?) Transaction Fees:', financial)
    if fee:
        fee_quote = owner + '\nAnnual Fee ' + fee[1]
        if single_card_fee_value(fee_quote) is not None:
            result.append(('single_card_annual_fee', owner, fee_quote))
    return result
