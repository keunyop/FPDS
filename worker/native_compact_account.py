"""Owned compact account definitions/features and explicitly linked category costs."""
import re
from decimal import Decimal
from urllib.parse import urlsplit
from worker.native_information_records import name_key
from worker.native_dom_ownership import owns_label, local_notes

LABELS=['Opening balance','Maintaining balance','Balance to earn interest','Interest rate (p.a.)']

def compact_feature_parts(quote):
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 if len(lines)!=9 or [lines[i].casefold() for i in [1,3,5,7]]!=[x.casefold() for x in LABELS]:return None
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 money=[re.fullmatch(_MONEY_AMOUNT,lines[i],re.I) for i in [2,4,6]]
 rate=re.fullmatch(r'(\d+(?:\.\d+)?)%',lines[8])
 if not all(money) or not rate or not 0<=Decimal(rate[1])<100:return None
 # Every amount must explicitly use the same denomination. A bare dollar or P
 # cannot gain a currency from a sibling field or the bank's country.
 from worker.pipeline.fpds_collection_accuracy import CURRENCY_PATTERNS
 currencies=[{c for c,p in CURRENCY_PATTERNS.items() if re.search(p,lines[i],re.I)} for i in [2,4,6]]
 if len(currencies[0])!=1 or not all(c==currencies[0] for c in currencies):return None
 return {'minimum_deposit':Decimal(money[0][1].replace(',','')),'minimum_balance':Decimal(money[1][1].replace(',','')),'earning_balance':Decimal(money[2][1].replace(',','')),'standard_rate':Decimal(rate[1]),'currency':next(iter(currencies[0]))}

def compact_rate_summary(quote):
 parts=compact_feature_parts(quote)
 if parts is None:return None
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 return str(quote)+('\nMinimum balance to earn interest: '+lines[6] if parts['earning_balance']>0 else '')

def compact_account_records(soup):
 root=soup.find('main') or soup.body or soup
 if root.find('h1') is not None:return []
 definitions=[]
 for p in root.find_all('p')[:2048]:
  literal=' '.join(p.get_text(' ',strip=True).split())
  m=re.match(r'(?:An? )?([A-Za-z0-9][A-Za-z0-9 \x27-]{1,100}? Savings Account) is a savings account\b',literal)
  if m and len(literal)<=700 and not p.find_parent(['nav','footer','aside','form','table']):definitions.append((p,m[1],literal))
 if len(definitions)!=1:return []
 definition,owner,literal=definitions[0];output=[]
 for table in root.find_all('table')[:1024]:
  rows=table.find_all('tr')
  if len(rows)!=4 or any(r.find(['th']) or r.select('[colspan],[rowspan]') for r in rows):continue
  cells=[r.find_all('td',recursive=False) for r in rows]
  if any(len(c)!=2 for c in cells):continue
  pairs=[[c.get_text(' ',strip=True) for c in row] for row in cells]
  if [r[0].casefold() for r in pairs]!=[x.casefold() for x in LABELS]:continue
  scope=next((a for a in list(table.parents)[:6] if any(a is b for b in list(definition.parents)[:6])),None)
  if scope is None or scope is root or len(scope.get_text())>4000 or len(scope.find_all('table'))!=1 or scope.select('input,select,textarea,form') or not owns_label(scope,root,owner):continue
  if local_notes(soup,table) != []:continue
  quote='\n'.join([owner,*[v for pair in pairs for v in pair]])
  if compact_feature_parts(quote) is not None:output.extend([('compact_account_definition',owner,owner+'\n'+literal),('owned_compact_account_features',owner,quote)])
 return list(dict.fromkeys(output))

def compact_primary_title(*,url,title,definitions):
 owners=set(definitions)
 if len(owners)!=1:return None
 owner=next(iter(owners));words=set(name_key(owner).split());route=set(name_key(urlsplit(url).path.rstrip('/').split('/')[-1]).split())
 generic={'account','accounts','savings','checking','chequing'}
 if words<=set(name_key(title).split()) and words-generic and words-generic==route-generic:return owner
 return None

def category_fee_value(quote):
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 if len(lines)!=9 or lines[1]!='Named account pricing row' or lines[2]!='Maintaining Balance':return None
 row=lines[3].split(' | ')
 if len(row)!=2 or name_key(row[0])!=name_key(lines[0]).removesuffix(' account') or not re.fullmatch(r'PHP\d[\d,]*(?:\.\d+)?(?: \(Effective [A-Za-z]+ \d{1,2}, \d{4}\))?',row[1]):return None
 try:i=lines.index('Account fee category')
 except ValueError:return None
 if i+4!=len(lines)-1 or lines[i+1]!='PESO SAVINGS ACCOUNT':return None
 if not lines[i+2].startswith('Minimum Balance Charges are to be collected only if the account falls below the minimum balance for two (2) consecutive months'):return None
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 m=re.fullmatch(_MONEY_AMOUNT+r' per month',lines[i+3],re.I)
 if not m or Decimal(m[1].replace(',',''))<=0 or not re.match(r'PHP',lines[i+3],re.I):return None
 if not lines[-1].startswith(('/', 'https://')) or lines[-1].startswith('//'):return None
 return Decimal(m[1].replace(',',''))

def category_fee_records(soup):
 root=soup.find('main') or soup.body or soup;output=[]
 links=[(a.get_text(' ',strip=True),a['href']) for a in soup.find_all('a',href=True) if a.get_text(' ',strip=True).endswith('Savings Account') and not a.find_parent('form')]
 cost=[]
 for table in root.find_all('table')[:1024]:
  rows=table.find_all('tr')
  if not rows:continue
  headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['th','td'],recursive=False)]
  if not headers or headers[0]!='FEES AND CHARGES' or headers.count('PESO SAVINGS ACCOUNT')!=1:continue
  index=headers.index('PESO SAVINGS ACCOUNT')
  for row in rows[1:]:
   cells=row.find_all(['th','td'],recursive=False)
   if len(cells)!=len(headers) or row.select('[rowspan],[colspan]'):continue
   condition=cells[0].get_text(' ',strip=True)
   if condition.startswith('Minimum Balance Charges are to be collected only if') and local_notes(soup,row)==[]:
    cost.append((headers[index],condition,cells[index].get_text(' ',strip=True)))
 if len(cost)!=1:return []
 for table in root.find_all('table')[:1024]:
  rows=table.find_all('tr')
  if not rows:continue
  headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['th','td'],recursive=False)]
  if not {'Opening Balance','Maintaining Balance','Interest Rate (% p.a)'}<=set(headers):continue
  for row in rows[1:]:
   cells=row.find_all(['th','td'],recursive=False)
   if len(cells)!=len(headers) or row.select('[rowspan],[colspan]'):continue
   values=[c.get_text(' ',strip=True) for c in cells];named=values[0]
   if not named.endswith('Savings') or not re.match(r'PHP\d',values[headers.index('Maintaining Balance')]):continue
   matches=set((label,href) for label,href in links if name_key(label).removesuffix(' account')==name_key(named))
   if len(matches)!=1 or local_notes(soup,row)!=[]:continue
   owner,href=next(iter(matches));quote='\n'.join([owner,'Named account pricing row','Maintaining Balance',named+' | '+values[headers.index('Maintaining Balance')],'Account fee category',*cost[0],href])
   if len(quote)<=6400 and category_fee_value(quote) is not None:output.append(('named_account_category_fee',owner,quote))
 return list(dict.fromkeys(output))
