"""Owned account feature rows; annual-rate and monthly-cost qualifiers stay literal."""
import re
from decimal import Decimal
from worker.native_dom_ownership import unique_heading,owns_label,local_notes

LABELS={'Minimum Initial Deposit','Required Minimum Average Daily Balance (ADB)',
        'Interest Rate (per Annum)','Required Daily Balance To Earn Interest',
        'Service Charge Below Minimum ADB'}

def feature_fee_value(quote):
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 try:
  minimum=lines.index('Required Minimum Average Daily Balance (ADB)')
  charge=lines.index('Service Charge Below Minimum ADB')
 except ValueError:return None
 if minimum!=1 or charge!=3 or len(lines)<6:return None
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 if not re.fullmatch(_MONEY_AMOUNT,lines[2],re.I):return None
 price=re.fullmatch(_MONEY_AMOUNT,lines[4],re.I)
 if not price or Decimal(price[1].replace(',',''))<=0:return None
 conditions=' '.join(lines[5:])
 # A specific below-balance service charge must retain both its full trigger
 # and explicit collection cadence. Dormancy/closure charges cannot substitute.
 if not re.fullmatch(r'Coverage: Accounts falling below ADB requirement for two \(2\) consecutive month-end and every month-end thereafter[.] Collection: Monthly, to start at the end of the second month[.]?',conditions,re.I):return None
 return Decimal(price[1].replace(',',''))

def feature_minimum_balance(quote):
 if feature_fee_value(quote) is None:return None
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 line=[x.strip() for x in str(quote).splitlines() if x.strip()][2]
 amount=re.fullmatch(_MONEY_AMOUNT,line,re.I)
 return Decimal(amount[1].replace(',','')) if amount else None

def feature_rate_value(quote):
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 if len(lines)!=5 or lines[1]!='Interest Rate (per Annum)' or lines[3]!='Required Daily Balance To Earn Interest':return None
 m=re.fullmatch(r'(\d+(?:\.\d+)?)%',lines[2])
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 if not m or not re.fullmatch(_MONEY_AMOUNT,lines[4],re.I):return None
 value=Decimal(m[1]);return value if 0<=value<100 else None

def feature_rate_summary(quote):
 if feature_rate_value(quote) is None:return None
 lines=[x.strip() for x in str(quote).splitlines() if x.strip()]
 from worker.pipeline.fpds_collection_accuracy import _MONEY_AMOUNT
 amount=re.fullmatch(_MONEY_AMOUNT,lines[4],re.I)
 if Decimal(amount[1].replace(',',''))==0:return str(quote)
 # Lossless canonical labelling: keep the entire original declaration, then
 # repeat only its explicitly printed daily earning threshold under the shared
 # minimum-balance label. No amount, currency or financial meaning is inferred.
 return str(quote)+'\nMinimum balance to earn interest (daily): '+lines[4]

def feature_records(soup):
 root=soup.find('main') or soup.body or soup
 heading=unique_heading(root)
 if heading is None:return []
 owner=' '.join(heading.get_text(' ',strip=True).split())
 if not re.search(r'\b(?:account|savings|chequing|checking)\b',owner,re.I):return []
 rows={};conflict=False
 for h in root.find_all(['h2','h3','h4','h5','h6'])[:2048]:
  label=' '.join(h.get_text(' ',strip=True).split())
  if label not in LABELS:continue
  for block in list(h.parents)[:4]:
   if block is root or len(block.get_text())>1800:break
   if len(block.find_all(['h1','h2','h3','h4','h5','h6']))!=1:break
   if not block.find('p'):continue
   if block.find_parent(['nav','aside','footer','form']) or block.select('input,select,textarea') or not owns_label(block,root,owner):break
   notes=local_notes(soup,block)
   if notes is None:break
   literal='\n'.join([label,*[p.get_text(' ',strip=True) for p in block.find_all('p')],*notes])
   if label in rows and rows[label]!=literal:conflict=True
   rows[label]=literal;break
 if conflict:return []
 output=[]
 if {'Interest Rate (per Annum)','Required Daily Balance To Earn Interest'}<=rows.keys():
  quote='\n'.join([owner,rows['Interest Rate (per Annum)'],rows['Required Daily Balance To Earn Interest']])
  if feature_rate_value(quote) is not None:output.append(('owned_account_feature_rate',owner,quote))
 if {'Required Minimum Average Daily Balance (ADB)','Service Charge Below Minimum ADB'}<=rows.keys():
  quote='\n'.join([owner,rows['Required Minimum Average Daily Balance (ADB)'],rows['Service Charge Below Minimum ADB']])
  if feature_fee_value(quote) is not None:output.append(('owned_account_feature_fee',owner,quote))
 if 'Minimum Initial Deposit' in rows:
  quote='\n'.join([owner,rows['Minimum Initial Deposit']])
  output.append(('owned_account_feature_deposit',owner,quote))
 return output
