"""Complete named HTML application disclosures, with explicit standard rates."""
import re
from decimal import Decimal
from bs4 import Tag
from worker.native_information_records import names_match

N = r'\d+(?:\.\d+)?'
PROMO = r'A Promotional Rate of '+N+r'% \(unless this promotional low interest rate is further reduced by us in any offer we make to you\) will apply to any and all Balance Transfers made within \d+ days of your Account opening, and will remain in effect for \d+ Statement Periods from the date the last such Balance Transfer is posted to your Account \(the "Promotional Rate Period"\). The exact promotional low interest rate that applies during the Promotional Rate Period will be disclosed to you at the time an offer is made. After the expiry of the Promotional Rate Period, the remainder of your Balance Transfer amount will become subject to the Cash Advances rate outlined below.'
DEFAULT = r'If we don[’\x27]t receive your Minimum Payment by the payment due date as shown on \d+ consecutive monthly statements, your interest rate will increase to '+N+r'% on Purchases, and '+N+r'% on Cash Advances and Balance Transfers, including Balance Transfers with Promotional Rates in effect. This increase will take effect immediately(?: after the second consecutive missed payment)?, and will be reflected on the following monthly statement. These rates will remain in effect until we receive your minimum payments by the payment due date for \d+ consecutive months.'
GRACE = r'You[’\x27]ll receive an interest-free Grace Period of at least [a-z-]+ \( \d+ \) days on new Purchases on your Card if you pay the outstanding balance owing on your Account in full by the due date shown on your monthly statement. There is no interest-free grace period for Cash Advances, Balance Transfers, Cash-Like Transactions and applicable Cash Advance fees.'
MINIMUM = [r'Minimum Payment', r'For Residents Outside of Québec:',
 r'Your required Minimum Payment is the sum of Interest \+ Fees \+ \$'+N+r' , in addition to any over-limit or past due amounts. If your outstanding New Balance is less than \$'+N+r' , the Minimum Payment will be the balance.',
 r'For Québec Residents Only :', r'Your required Minimum Payment is the greater of '+N+r'% of the outstanding New Balance on your statement or \$'+N+r' .',
 r'In addition, in all cases your Minimum Payment will include any over-limit or past due amounts. If your outstanding New Balance is less than \$'+N+r' , the Minimum Payment will equal the balance.']
DETERMINATION = [r'Determination of Interest',
 r'If interest is charged, it is calculated on your average daily Balance and charged monthly to your Account on the last day of your billing cycle.',
 r'If annual interest rates change during a billing cycle \(statement period\), we use the annual interest rate in effect at the end of that billing cycle to calculate your daily interest for the entire statement period.']


def disclosure_names(title):
    suffix = ' Application Disclosure Statement'
    if not title.endswith(suffix):return []
    names = re.split(r' and ', title[:-len(suffix)])
    if len(names)>3 or any(not re.search(r'credit card|mastercard|visa', n, re.I) for n in names):return []
    return names


def application_card_rates(quote):
    lines=[' '.join(x.split()) for x in str(quote).splitlines() if x.strip()]
    if len(lines)<15 or not any(names_match(lines[0],n) for n in disclosure_names(lines[1])):return None
    patterns=[r'Annual Interest Rate',PROMO,r'Standard Rates [–-] These rates are in effect when your Account is opened:',
        r'Purchases: ('+N+r')% Cash Advances: ('+N+r')% \(includes Balance Transfers after the Promotional Rate Period has ended\)',DEFAULT,r'Interest-free Grace Period',GRACE]
    end=2+len(patterns)
    if len(lines) not in {end+len(MINIMUM),end+len(DETERMINATION)+len(MINIMUM)}:return None
    if len(lines)==end+len(DETERMINATION)+len(MINIMUM):patterns+=DETERMINATION
    patterns+=MINIMUM
    if not all(re.fullmatch(p,l,re.I) for p,l in zip(patterns,lines[2:])):return None
    rates=re.fullmatch(patterns[3],lines[5],re.I)
    values=tuple(Decimal(x) for x in rates.groups())
    return values if all(0<=v<100 for v in values) else None


def _section(head):
    lines=[head.get_text(' ',strip=True)];seen=set()
    for node in head.next_elements:
        if not isinstance(node,Tag):continue
        if node.name in {'h1','h2','h3'}:break
        if node.name not in {'p','ul','ol','table'} or any(id(a) in seen for a in node.parents):continue
        lines.append(node.get_text(' ',strip=True));seen.add(id(node))
    return lines


def application_disclosure_records(soup):
    root=soup.find('main') or soup.body or soup;output=[]
    for head in root.find_all('h2'):
        title=head.get_text(' ',strip=True);names=disclosure_names(title)
        if not names:continue
        sections={};duplicate=False
        for node in head.find_all_next(['h1','h2','h3']):
            if node.name in {'h1','h2'}:break
            label=node.get_text(' ',strip=True)
            if label in sections:duplicate=True
            sections[label]=_section(node)
        if duplicate or not {'Annual Interest Rate','Minimum Payment'}<=sections.keys():continue
        for owner in names:
            record='\n'.join([owner,title,*sections['Annual Interest Rate'],*sections['Minimum Payment']])
            if len(record)<=6400 and application_card_rates(record) is not None:
                output.append(('named_card_regular_rates',owner,record))
    return list(dict.fromkeys(output))
