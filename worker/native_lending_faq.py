"""Complete single-product lending FAQs with a literal named return link."""
import re
from urllib.parse import urlsplit
from worker.native_information_records import name_key
from worker.native_dom_ownership import local_notes

def purpose_repayment_terms(value):
 body=' '.join(str(value).split())
 if not re.fullmatch(r'Our .{2,100}? Loan term/s varies depending on purpose: Type - Loan Term\* .+?\*Final loan term is subject to approval of management[.]',body):return None
 terms=re.findall(r' - Up to (\d+) years',body)
 if not terms or not all(0<int(t)<=100 for t in terms) or len(body)>3000:return None
 return body

def faq_values(quote):
 body=' '.join(str(quote).split())
 fixing=re.search(r'To protect yourself from future rate increases, you can choose to have your interest rate fixed for .+? Please see the following interest rates:',body)
 rows=re.findall(r'(\d+) to (\d+) years\s*\|\s*(\d+(?:\.\d+)?)% p[.]a[.]',body)
 from decimal import Decimal
 if (not fixing or not rows or len(re.findall(r'\b\d+ to \d+ years\s*\|\s*\d+(?:\.\d+)?%',body)) != len(rows) or any(not 0<int(a)<=int(b) or not 0<=Decimal(r)<100 for a,b,r in rows)
     or 'Rate Fixing Period | Interest Rate per Annum (p.a)' not in body
     or 'Rates above are subject to change at any given time.' not in body
     or 'rates are subject to review and repricing after the agreed-upon fixing period expires.' not in body):return None
 term=re.search(r'Our .+? Loan term/s varies depending on purpose: Type - Loan Term\* .+?\*Final loan term is subject to approval of management[.]',body)
 if not term or purpose_repayment_terms(term[0]) is None:return None
 return fixing[0],term[0]

def lending_faq_records(soup):
 root=soup.find('main') or soup.body or soup
 blocks=root.select('.faq-answer')
 if not 1<len(blocks)<=16 or any(len(b.get_text())>6000 for b in blocks):return []
 literal='\n'.join(b.get_text('\n',strip=True) for b in blocks)
 names=set(re.findall(r'Our (.{2,100}? Loan) term/s varies depending on purpose:',literal))
 if len(names)!=1:return []
 body_name=next(iter(names));core=set(name_key(re.sub(r' Loan$','',body_name)).split())
 title=set(name_key(soup.title.get_text(' ',strip=True) if soup.title else '').split())
 if not core or not set(name_key(body_name).split())<=title:return []
 headers=[h.get_text(' ',strip=True) for h in root.find_all(['h1','h2','h3']) if core<=set(name_key(h.get_text()).split())]
 if len(set(headers))!=1:return []
 notes=[]
 for block in blocks:
  if block.find_parent(['nav','aside','footer','form']) or block.select('input,select,textarea'):return []
  refs=local_notes(soup,block)
  if refs is None:return []
  notes.extend(refs)
 links=set()
 for a in root.find_all('a',href=True):
  href=a['href'];label=' '.join(a.get_text(' ',strip=True).split())
  route=set(name_key(urlsplit(href).path).split())-{'loan','loans'}
  if route==core and core<=set(name_key(label).split()) and len(label)<=160 and href.startswith(('/', 'https://')) and not href.startswith('//'):
   links.add((label,href))
 if len(links)!=1:return []
 owner,href=next(iter(links));quote='\n'.join([owner,headers[0],literal,*dict.fromkeys(notes),href])
 if len(quote)>8000 or faq_values(quote) is None:return []
 return [('named_lending_faq_terms',owner,quote),('captured_product_link',owner,href)]

def primary_lending_headings(soup):
 if soup.find('h1') is not None:return []
 root=soup.find('main') or soup.body or soup
 seo=set(name_key(soup.title.get_text(' ',strip=True) if soup.title else '').split())
 output=[]
 for h in root.find_all(['h2','h3'])[:512]:
  literal=' '.join(h.get_text(' ',strip=True).split());words=set(name_key(literal).split())
  if (2<=len(words)<=12 and words<=seo and len(literal)<=160
      and not h.find_parent(['nav','aside','footer','form'])):
   output.append(('primary_lending_heading',literal,literal))
 return list(dict.fromkeys(output))


def corroborated_primary_lending_title(*,url,title,headings):
 seo=set(name_key(title).split());parsed=urlsplit(url)
 route=set(name_key(parsed.path.rstrip('/').split('/')[-1]).split())
 if route & {'compare','apply','login','calculator','faq','faqs'}:return None
 host=(parsed.hostname or '').removeprefix('www.').split('.')[:-1];names=set()
 for literal in headings:
  words=name_key(literal).split();brand=set()
  for count in range(1,min(4,len(words))+1):
   if ''.join(words[:count]) in host:brand=set(words[:count])
  core=set(words)-brand
  if brand and core and set(words)<=seo and core<=route and route-core<={'loan','loans','personal','lending','mortgage','mortgages'}:names.add(literal)
 return next(iter(names)) if len(names)==1 else None
