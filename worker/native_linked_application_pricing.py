"""Complete linked application prices; preserve enumeration and all APR conditions."""
import re
from decimal import Decimal
from worker.native_dom_ownership import local_notes


def application_pricing_records(soup):
    root = soup.find('main') or soup.body or soup
    heads = root.find_all('h1')
    if len(heads) != 1:
        return []
    match = re.fullmatch(r'(.+?) Terms and Conditions', heads[0].get_text(' ', strip=True), re.I)
    if not match or not re.search(r"credit card|visa|mastercard",match[1],re.I):
        return []
    owner = match[1]
    tables = [t for t in root.find_all('table') if t.get_text(' ',strip=True).startswith('Interest Rates and Interest Charges')]
    if len(tables) != 1:
        return []
    table=tables[0]; scope=table.parent
    if scope is root or len(scope.find_all('h2')) != 1:
        return []
    # Corroborate the two captured native headings, including network descriptors.
    second=scope.find('h2').get_text(' ',strip=True)
    from worker.native_information_records import names_match
    if not application_names_match(re.sub(r' Terms and Conditions$','',second,flags=re.I),owner):
        return []
    labels=['Annual Percentage Rate (APR) for Purchases','Annual Percentage Rate (APR) for Balance Transfers','How to Avoid Paying Interest on Purchases','Minimum Interest Charge']
    literal=table.get_text(' ',strip=True)
    if any(literal.count(label)!=1 for label in labels):
        return []
    purchase=literal.split(labels[0],1)[1].split(labels[1],1)[0]
    if (not re.search(r'based on your creditworthiness',purchase,re.I)
            or not re.search(r'vary with the market based on the U.S. Prime Rate',purchase,re.I)):
        return []
    values=re.findall(r'(\d+(?:\.\d+)?)%',purchase)
    if not values or not all(0<=Decimal(v)<100 for v in values):
        return []
    parts=[];ended=False
    for node in [table,*table.next_siblings]:
        if not getattr(node,'name',None):continue
        text=' '.join(node.get_text(' ',strip=True).split())
        if node.name=='h3' and text=='Table of Contents':ended=True;break
        if node.name not in {'table','h4','p','ul'}:return []
        notes=local_notes(soup,node)
        if notes is None:return []
        parts.extend([text,*notes])
    if not ended or len([x for x in parts if x.startswith('Fees Annual Fee ')])!=1:
        return []
    if not any(x.lower()=='how we will calculate your balance' for x in parts):return []
    if not any('average daily balance (including new purchases)' in x for x in parts):return []
    # Pricing continuation and offer eligibility are independent owned sections,
    # not optional snippets. Their full list records are mandatory.
    continuation=[]
    for pattern in [r'^Will you qualify if .+(?:Credit Card|Mastercard) account\?$',r'^How do we calculate your variable APRs\?$']:
        headings=[h for h in scope.find_all('h5') if re.fullmatch(pattern,h.get_text(' ',strip=True),re.I)]
        if len(headings)!=1:return []
        block=headings[0].find_parent('li')
        if block is None or len(block.find_all('h5'))!=1:return []
        notes=local_notes(soup,block)
        if notes is None:return []
        continuation.extend([block.get_text(' ',strip=True),*notes])
    variable=continuation[-1]
    if not all(term in variable for term in ['How We Determine the U.S. Prime Rate','How We Calculate Your Variable APR','Maximum APR','reserve the right to change terms']):return []
    dates=[p.get_text(' ',strip=True) for p in scope.find_all('p',recursive=False) if re.match(r'Please note: Information about the (?:credit )?card Account',p.get_text(' ',strip=True),re.I)]
    if len(dates)!=1:return []
    quote='\n'.join(['Pricing Information','Named card: '+owner,*parts,*dates,*continuation])
    from worker.pipeline.fpds_rate_safety import contains_unresolved_financial_placeholder
    if len(quote)>8000 or '\ufffd' in quote or contains_unresolved_financial_placeholder(quote):return []
    return [('linked_card_pricing_terms','Pricing Information',quote)]


def application_owner_matches(quote,identity,url):
    owner=re.search(r'(?m)^Named card: (.+)$',str(quote))
    if not owner:return True
    from worker.native_information_records import name_key,names_match
    from urllib.parse import urlsplit
    if application_names_match(owner[1],identity):return True
    left=name_key(owner[1]).split();host=(urlsplit(url).hostname or '').removeprefix('www.').split('.')[:-1]
    for cut in range(1,len(left)):
        if ''.join(left[:cut]) in host and application_names_match(' '.join(left[cut:]),identity):return True
    return False


def application_fee_value(quote):
    if not str(quote).startswith('Pricing Information\nNamed card: ') or 'How do we calculate your variable APRs?' not in quote:return None
    fees=re.findall(r'(?m)^Fees Annual Fee (None|\$\d+(?:\.\d+)?)(?= Transaction Fees|$)',quote)
    if len(fees)!=1 or re.search(r'annual fee.{0,80}(?:waiv|first year|only if)|waiv\w*.{0,80}annual fee',quote,re.I):return None
    return Decimal(0) if fees[0]=='None' else Decimal(fees[0][1:])


def application_names_match(left,right):
    """Only explicit card-network descriptors; preserve Select/Plus/audiences."""
    from worker.native_information_records import names_match
    def clean(value):
        value=re.sub(r"\bworld(?: elite)? (?=mastercard\b)","",str(value),flags=re.I)
        value=re.sub(r"\bvisa signature(?: infinite)?\b","Visa",value,flags=re.I)
        value=re.sub(r"\b(?:TM|SM)\b","",value)
        return value
    return names_match(clean(left),clean(right))


def remove_duplicate_trademark_labels(soup):
    """Drop only a hidden spoken duplicate of its adjacent visible symbol."""
    for label in soup.select('h1 .visually-hidden, h2 .visually-hidden'):
        symbols = {'trademark': '™', 'registered mark': '®'}
        expected = symbols.get(label.get_text(' ',strip=True).casefold())
        sibling = label.find_next_sibling()
        if expected and sibling is not None and sibling.get('aria-hidden') == 'true' and sibling.get_text('',strip=True) == expected:
            label.decompose()
