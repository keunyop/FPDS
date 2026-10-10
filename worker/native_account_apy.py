"""Literal owned account APY panels, independent of marketing headings."""
import re
from decimal import Decimal
from worker.native_dom_ownership import owns_label
from worker.native_owned_account_records import _account_notes

LABEL = re.compile(r"^(.{4,100} (?:Savings|Checking|Chequing) Account) Annual Percentage Yield$", re.I)

def account_apy_value(quote):
    lines = [" ".join(s.split()) for s in str(quote).splitlines() if s.strip()]
    if not lines or not re.fullmatch(r".{4,100} (?:Savings|Checking|Chequing) Account", lines[0], re.I):
        return None
    q = " ".join(lines)
    declarations = list(re.finditer(r"(\d+(?:\.\d+)?)%\s*APY\s+" + re.escape(lines[0]) + r"\s+Annual Percentage Yield\b", q, re.I))
    rates = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", q)
    if len(declarations) != 1 or len(rates) != 1 or re.search(r"\{\{|\b(?:introductory|promotional|bonus|boost|tier|eligible|eligibility|qualifying|qualified|if|first \d+ months?|for \d+ months?)\b",q,re.I):
        return None
    if not re.search(r"Annual percentage yield as of [A-Za-z]+ \d{1,2}, \d{4}[.] APY may change at any time before or after account is opened[.]",q,re.I):
        return None
    return Decimal(declarations[0][1])

def account_wide_fee_value(quote):
    lines = [" ".join(s.split()) for s in str(quote).splitlines() if s.strip()]
    if len(lines) == 2 and re.fullmatch(r".{4,100} (?:Savings|Checking|Chequing) Account",lines[0],re.I) and re.fullmatch(r"No fees[.] No minimum deposit[.]",lines[1],re.I):
        return Decimal(0)
    return None

def account_apy_records(soup):
    root=soup.find('main') or soup.body or soup
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    out=[]
    panels={}
    conflicts=set()
    for label in root.find_all('p')[:2048]:
        name=LABEL.fullmatch(' '.join(label.get_text(' ',strip=True).split()))
        if not name or label.find_parent(['nav','aside','footer','header','form']):
            continue
        owner=name[1]
        if " ".join(re.findall(r"[a-z0-9]+",owner.casefold())) not in " ".join(re.findall(r"[a-z0-9]+",title.casefold())):
            continue
        for scope in list(label.parents)[:6]:
            if scope is root or len(scope.get_text())>6400:
                break
            if any(re.search(r'calculator|simulation|projection|graph',str(p.get('class',''))+' '+str(p.get('id','')),re.I) for p in [scope,*list(scope.parents)[:8]]):
                break
            if sum(bool(LABEL.fullmatch(' '.join(p.get_text(' ',strip=True).split()))) for p in scope.find_all('p'))!=1:
                break
            literal=scope.get_text('\n',strip=True)
            quote='\n'.join([owner,literal])
            if account_apy_value(quote) is None:
                continue
            notes=_account_notes(soup,scope)
            if notes is None or not owns_label(scope,root,owner):
                break
            quote='\n'.join([quote,*notes])
            if len(quote)>6400 or account_apy_value(quote) is None:
                break
            signature=(account_apy_value(quote),tuple(notes))
            if owner in panels and panels[owner][0]!=signature:
                conflicts.add(owner)
            panels.setdefault(owner,(signature,quote))
            for p in scope.find_all(['p','li']):
                statement=' '.join(p.get_text(' ',strip=True).split())
                fee_quote=owner+'\n'+statement
                if account_wide_fee_value(fee_quote) is not None and _account_notes(soup,p)==[]:
                    out.append(('owned_account_assertion',owner,fee_quote))
            break
    for owner,(_,quote) in panels.items():
        if owner not in conflicts:
            out.extend([('owned_product_label',owner,owner),('owned_account_apy',owner,quote)])
    return list(dict.fromkeys(x for x in out if x[1] not in conflicts))
