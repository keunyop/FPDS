"""Detect empty source-native pricing slots; rendering never supplies a fact."""
import re


def has_empty_dynamic_rate_slot(html: str) -> bool:
    if has_literal_financial_template(html) or has_empty_native_price_slot(html):
        return True
    # Literal rate-loader markup plus an empty slot is stronger than a stray
    # percentage in legal notes. No scripts are evaluated here.
    loaders = re.findall(r'<script\b[^>]*\bsrc\s*=\s*["\']([^"\']+)', html, re.I)
    if not any(re.search(r'rates?|pricing|interest|apr|apy', src, re.I) for src in loaders):
        return False
    if not re.search(r'interest\s+rate|annual\s+percentage|\b(?:APR|APY)\b', html, re.I):
        return False
    marker = r'\b(?:id|class|data-[\w-]+)\s*=\s*["\'][^"\']*(?:rates?[_-]|pricing[_-])[^"\']*["\']'
    for match in re.finditer(r'<(?:div|tbody)\b([^>]{0,1500})>\s*</(?:div|tbody)>', html, re.I):
        if re.search(marker, match[1], re.I):
            return True
    for match in re.finditer(r'<tr\b([^>]{0,1500})>(.{0,3000}?)</tr>', html, re.I | re.S):
        if (re.search(marker, match[1], re.I)
                and re.fullmatch(r'\s*<th\b[^>]*>.+?</th>\s*', match[2], re.I | re.S)
                and not re.search(r'<td\b', match[2], re.I)):
            return True
    return False

def has_literal_financial_template(html: str, *, kind: str = 'rate') -> bool:
    """Observe bounded JSON label/value placeholders; never execute or fill them."""
    import json
    from html.parser import HTMLParser
    class Observer(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.excluded=[]; self.found=False; self.seen=0
        def handle_starttag(self,tag,attrs):
            if tag in {'nav','header','footer','script','style','aside'}:
                self.excluded.append(tag)
            if self.excluded or self.found:
                return
            for name,value in attrs:
                if not name.startswith('data-') or not value or not value.lstrip().startswith(('{','[')) or len(value)>128000:
                    continue
                self.seen+=1
                if self.seen>256:
                    return
                def unique(pairs):
                    result={}
                    for key,item in pairs:
                        if key in result: raise ValueError('Duplicate JSON key')
                        result[key]=item
                    return result
                try:
                    data=json.loads(value,object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
                except (ValueError,TypeError,RecursionError):
                    continue
                pending=[(data,0)]; visited=0
                while pending and visited<4096:
                    item,depth=pending.pop();visited+=1
                    if depth>16:continue
                    if isinstance(item,dict):
                        for label_key,value_key in [('header','content'),('label','value')]:
                            label=item.get(label_key);slot=item.get(value_key)
                            meaning=r'\b(?:APR|APY|rate|interest|yield)\b' if kind=='rate' else r'\b(?:fee|fees|charge|charges)\b'
                            if (isinstance(label,str) and isinstance(slot,str) and len(label)<600 and len(slot)<4000
                                and re.search(meaning,label.replace('_',' '),re.I)
                                and re.search(r'\{\{[^}]{1,300}\}\}|\$\{[^}]{1,300}\}',slot)
                                and not re.search(r'\b(?:url|image|login|link)\b',slot.replace('_',' '),re.I)):
                                self.found=True;return
                        pending.extend((v,depth+1) for v in item.values() if isinstance(v,(dict,list)))
                    elif isinstance(item,list):pending.extend((v,depth+1) for v in item if isinstance(v,(dict,list)))
        def handle_endtag(self,tag):
            if tag in self.excluded:
                self.excluded.remove(tag)
    if not html or len(html)>16000000:
        return False
    observer=Observer()
    try:observer.feed(html)
    except (ValueError,RecursionError):return False
    return observer.found

def has_empty_native_price_slot(html: str, *, kind: str = "rate") -> bool:
    """Empty literal DOM price bindings are render leads, never financial facts."""
    from bs4 import BeautifulSoup
    from worker.native_dom_ownership import unique_heading, owns_label
    if not html or len(html) > 16000000:
        return False
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup.body or soup
    heading = unique_heading(root)
    if heading is None:
        return False
    owner = heading.get_text(" ", strip=True)
    meaning = r"rate|apr|apy|yield" if kind == "rate" else r"fee|charge"
    for node in root.find_all(["span", "div", "td"])[:8192]:
        if node.get_text(strip=True) or node.find_parent(["nav", "aside", "footer", "header", "form", "script"]):
            continue
        if any(re.search(r"calculator|graph", " ".join(a.get("class", [])), re.I) for a in list(node.parents)[:4]):
            continue
        bindings = [str(node.get(key, "")) for key in ("data-id", "data-field", "data-bind")]
        if not any(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{1,120}", value) and re.search(meaning, value, re.I) for value in bindings):
            continue
        label = r"\b(?:APR|APY|rate|yield|interest)\b" if kind == "rate" else r"\b(?:fee|charge)\b"
        for block in list(node.parents)[:4]:
            if block is root or len(block.get_text()) > 2400:
                break
            if (block.select('input:not([type="hidden"]), select, textarea, [role="slider"]')
                    or re.search(r"calculator|graph", " ".join(block.get("class", [])), re.I)
                    or not owns_label(block, root, owner)):
                break
            if re.search(label, block.get_text(" ", strip=True), re.I):
                return True
    return False
