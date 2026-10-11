"""Complete named HTML card disclosures; never infer identity from a URL."""
import re
from bs4 import Tag, Comment
from decimal import Decimal
from worker.native_dom_ownership import local_notes, owns_label

HEADING = re.compile(r'^(.{4,140} Credit Card) Disclosure$', re.I)

def named_html_pricing(soup):
    root = soup.find('main') or soup.body or soup
    out = []
    for head in root.find_all(['h2','h3'])[:256]:
        match = HEADING.fullmatch(' '.join(head.get_text(' ',strip=True).split()))
        if not match or head.find_parent(['aside','nav','footer','form','table']):
            continue
        owner = match[1]
        parts, blocks, seen = [], [], set()
        started = False
        for node in head.next_elements:
            if root not in node.parents:
                break
            if not isinstance(node,Tag):
                if (started and not isinstance(node, Comment) and str(node).strip() and not any(id(a) in seen for a in node.parents)
                        and not any(a.name in ['style','script','noscript'] for a in node.parents)):
                    parts.append(' '.join(str(node).split()))
                continue
            if node.name in ['h1','h2','h3'] or root not in node.parents:
                break
            if node.name not in ['p','table','ul','ol'] or any(id(a) in seen for a in node.parents):
                continue
            if node.find_parent(['aside','nav','footer','form']):
                continue
            if not started and node.name == 'table' and node.get_text(' ', strip=True).startswith('Interest Rates and Interest Charges'):
                started = True
            if not started:
                continue
            parts.append(' '.join(node.get_text(' ', strip=True).split()))
            blocks.append(node);seen.add(id(node))
        if not parts or sum(map(len,parts)) > 7800:
            continue
        body = '\n'.join(parts)
        if len(re.findall(r'(?m)^REV \d{6}$',body)) != 1:
            continue
        labels = ['Interest Rates and Interest Charges','Annual Percentage Rate (APR) for Purchases',
                  'APR for Balance Transfers','APR for Cash Advances','Penalty APR',
                  'How to Avoid Paying Interest on Purchases','Minimum Interest Charge',
                  'Fees Annual Fee','How We Calculate Your Balance:','Variable Rate Information:',
                  'Credit Approval:']
        if any(body.count(label) != 1 for label in labels):
            continue
        if not re.search(r'The Prime Rate is currently \d+(?:\.\d+)?% as of [A-Za-z]+ \d{1,2}, \d{4}',body):
            continue
        purchase = body.split(labels[1],1)[1].split(labels[2],1)[0]
        interval = re.search(r'Your APR will be between (\d+(?:\.\d+)?)% and (\d+(?:\.\d+)?)%',purchase,re.I)
        if (not interval or not 0 <= Decimal(interval[1]) <= Decimal(interval[2]) < 100
                or 'based on your creditworthiness' not in purchase
                or 'vary with the market based on the Prime Rate' not in purchase):
            continue
        if re.search(r'introductory',purchase,re.I) and not re.search(r'\d+ months[.] After that,',purchase):
            continue
        # Every symbolic reference must have its own literal definition. Keep
        # both the marker and all continuation text, including fee waivers.
        markers=set(re.findall(r'(?<!\*)(\*{1,4})(?!\*)',purchase))
        definitions=set(re.findall(r'(?<!\*)(\*{1,4})(?!\*)\s*(?:The rate|The minimum|We charge)',body))
        all_markers=set(re.findall(r'(?<!\*)(\*{1,4})(?!\*)',body))
        definition_list=re.findall(r'(?<!\*)(\*{1,4})(?!\*)\s*(?:The rate|The minimum|We charge)',body)
        if markers-definitions or all_markers-definitions or len(definition_list)!=len(definitions):
            continue
        notes=[];valid=True
        for block in blocks:
            resolved=local_notes(soup,block)
            if resolved is None or not owns_label(block,root,owner):
                valid=False;break
            notes.extend(resolved)
        quote='\n'.join([owner,*parts,*dict.fromkeys(notes)])
        if not valid or len(quote)>8000 or '\ufffd' in quote:
            continue
        # References are formatting once their unique literal definitions have
        # been resolved above. Keep every note's full text, as the other native
        # DOM parsers do, while original captures preserve all marker bytes.
        from worker.financial_symbol_notes import resolved_symbol_text
        quote = resolved_symbol_text(quote)
        out.append(('named_card_apr_terms',owner,quote))
        fees = [p for p in parts if re.fullmatch(r'Fees Annual Fee (?:None|\$\d+(?:\.\d+)?\**)',p)]
        if len(fees)==1:
            # Retain the entire financial context for a positive base annual
            # price and its explicit waiver. Conditional zero remains unknown.
            value=re.fullmatch(r'Fees Annual Fee (None|\$\d+(?:\.\d+)?)(\**)',fees[0])
            if value and value[1]!='None':
                out.append(('named_html_annual_fee',owner,quote))
            elif value and not re.search(r'annual fee.{0,80}(?:waiv|first|only|if)|(?:waiv\w*).{0,80}annual fee',body,re.I):
                out.append(('named_html_annual_fee',owner,quote))
    return list(dict.fromkeys(out))

def named_html_fee_value(quote):
    lines=str(quote).splitlines()
    if len(lines)<5 or not re.fullmatch(r'.{4,140} Credit Card',lines[0],re.I):
        return None
    prices=[re.fullmatch(r'Fees Annual Fee (None|\$\d+(?:\.\d+)?)(\**)',line) for line in lines]
    prices=[m for m in prices if m]
    if len(prices)!=1:
        return None
    if prices[0][1]=='None':
        return Decimal(0) if not re.search(r'waiv\w*|first year|annual fee discount|annual fee reduction|annual fee.{0,80}(?:only|if|eligible|unless|provided|introductory)',quote,re.I) else None
    return Decimal(prices[0][1][1:])
