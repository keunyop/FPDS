"""Bounded literal CMS values, tied to the selected snapshot and owned DOM.

No JavaScript evaluation, arithmetic, guessed units or generated URLs.
"""
import copy
import json
import re
from decimal import Decimal, InvalidOperation

_LITERAL = r'"(?:[^"\\]|\\.)*"'
_MAP = re.compile(r'Websites\.Product\.Core\.setProductMap\(\s*JSON\.parse\(\s*(' + _LITERAL + r')\s*\)', re.S)
_ALIAS = re.compile(r'capsuleAlias\s*:\s*"([A-Za-z0-9_-]{1,64})"')
_TOKEN = re.compile(r'\$\{\s*([A-Za-z0-9_.]+)\s*(?:\|\s*(amount|percent)\s*:\s*"true"\s*)?\}')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate literal key")
        result[key] = value
    return result


def _loads(value):
    return json.loads(value, object_pairs_hook=_unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite literal")))


def product_maps(html):
    maps = []
    for match in _MAP.finditer(html):
        if len(match[1]) > 1000000:
            return {}
        try:
            literal = re.sub(r'\\x([0-9a-fA-F]{2})', r'\\u00\1', match[1])
            value = _loads(_loads(literal))
            if not isinstance(value, dict) or len(value) > 64:
                return {}
            decoded = {}
            for alias, rows in value.items():
                rows = _loads(rows) if isinstance(rows, str) else rows
                if not isinstance(rows, list) or not 0 < len(rows) <= 64:
                    return {}
                if any(not isinstance(row, dict) or len(row) > 512
                       or len(json.dumps(row)) > 128000 for row in rows):
                    return {}
                decoded[alias] = rows
            maps.append(decoded)
        except (ValueError, TypeError, RecursionError):
            return {}
    return maps[0] if maps and all(m == maps[0] for m in maps) else {}


def _name(value):
    value = re.sub(r'guaranteed investment certificates?', 'gic', str(value), flags=re.I)
    return re.sub(r'[^a-z0-9]', '', value.casefold())


def resolve_component_values(soup, html):
    records = product_maps(html)
    count = 0
    for node in soup.find_all(attrs={"data-fpds-literal-owner": True}):
        del node["data-fpds-literal-owner"]
    # Explicit consent dialogs cannot identify a financial product.
    for dialog in list(soup.select('[role="dialog"], [aria-modal="true"]')):
        title = dialog.find(["h1", "h2", "h3"])
        label = str(dialog.get("aria-label", "")) + " " + (title.get_text(" ", strip=True) if title else "")
        if dialog.parent is not None and re.search(r"privacy|cookies?|consent", label, re.I):
            dialog.decompose()
    h1s = soup.find_all('h1')
    if not records or len(h1s) != 1:
        return 0
    identity = _name(h1s[0].get_text(' ', strip=True))
    for script in list(soup.find_all('script'))[:512]:
        aliases = _ALIAS.findall(script.get_text())
        if len(aliases) != 1 or script.parent is None:
            continue
        scope = script.parent
        if len([s for s in scope.find_all('script') if _ALIAS.search(s.get_text())]) != 1:
            continue
        rows = records.get(aliases[0], [])
        if not rows or any(_name(row.get('productName', '')) != identity for row in rows):
            continue
        scope["data-fpds-literal-owner"] = h1s[0].get_text(" ", strip=True)
        dynamic = 'new Websites.TableDynamic(' in script.get_text()
        if dynamic:
            tables = scope.find_all('table')
            if len(tables) != 1:
                continue
            templates = [tr for tr in tables[0].find_all('tr') if '${' in tr.get_text()]
            if len(templates) != 1:
                continue
            template = templates[0]
            if re.search(r"criteriaNumericValue\}\s*months?", template.get_text()):
                units = {str(r.get("productCriteria.TERMRANGE.unitOfMsrCd", "MONTH")).upper() for r in rows}
                if units != {"MONTH"}:
                    continue
            for row in rows:
                clone = copy.deepcopy(template)
                count += _replace_values(clone, row, indexed=False)
                template.insert_before(clone)
            template.decompose()
        elif len(rows) == 1:
            count += _replace_values(scope, rows[0], indexed=True)
    return count


def _replace_values(scope, row, *, indexed):
    count = 0
    for node in list(scope.find_all(string=True)):
        if node.find_parent('script') is not None:
            continue
        def replace(match):
            nonlocal count
            key, fmt = match.groups()
            if indexed:
                if not key.startswith('p1.'):
                    return match[0]
                key = key[3:]
            elif re.match(r'p\d+\.', key):
                return match[0]
            value = row.get(key)
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                return match[0]
            if fmt:
                try:
                    number = Decimal(str(value))
                    if not number.is_finite() or number < 0:
                        return match[0]
                except InvalidOperation:
                    return match[0]
                value = ('$' if fmt == 'amount' else '') + str(value) + ('%' if fmt == 'percent' else '')
            elif '<' in str(value) or '${' in str(value):
                return match[0]
            count += 1
            return str(value)
        updated = _TOKEN.sub(replace, str(node))
        if updated != str(node):
            node.replace_with(updated)
    return count
