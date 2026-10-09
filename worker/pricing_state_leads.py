"""Bounded literal hydration-state headers are render leads, never facts."""
import json
import re
from html.parser import HTMLParser
from itertools import islice

MAX_STATE_CHARS = 1_000_000


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(_):
    raise ValueError("Nonfinite JSON")


_DECODER = json.JSONDecoder(object_pairs_hook=_unique, parse_constant=_nonfinite)
_ASSIGNMENT = re.compile(r"(?:^|;)\s*(?:(?:var|let|const)\s+)?(?:[A-Za-z_$][\w$]*\.)*[A-Za-z_$][\w$]*\s*=\s*", re.M)
_SKIP_BRANCH = re.compile(r"calculator|graph|estimat|project|benchmark|national|navigation|footer|headerlinks", re.I)


def _pairs(node):
    if isinstance(node, dict):
        return list(node.items())
    if isinstance(node, list) and node:
        if node[0] == "~#iM" and len(node) == 2 and isinstance(node[1], list):
            values = node[1]
        elif node[0] == "^ ":
            values = node[1:]
        else:
            return None
        if len(values) % 2 or any(not isinstance(k, str) for k in values[::2]):
            return None
        if len(set(values[::2])) != len(values[::2]):
            return None
        return list(zip(values[::2], values[1::2]))
    return None


def _rate_template(value):
    if not isinstance(value, str) or len(value) > 4000:
        return False
    return bool(re.search(r"\{\{(?:[A-Za-z_]*?(?:apy|apr|rate|interest)[A-Za-z_]*)\}\}|\$\{(?:[A-Za-z_]*?(?:apy|apr|rate|interest)[A-Za-z_]*)\}", value, re.I)
        and re.search(r"%\s*(?:APY|APR)|annual (?:percentage|interest)|interest rate", value, re.I))


def _header_has_template(value):
    if _rate_template(value):
        return True
    pairs = _pairs(value)
    return bool(pairs and any(re.fullmatch(r"(?:apy|apr|interestRate|rate)(?:Text|Template|Display)?", key, re.I)
        and _rate_template(slot) for key, slot in pairs))


def _payload_has_header(payload):
    pending = [(payload, 0)]
    visited = 0
    while pending and visited < 20000:
        item, depth = pending.pop()
        visited += 1
        if depth > 32:
            continue
        if isinstance(item, str) and len(item) <= MAX_STATE_CHARS and item.lstrip().startswith(("[", "{")):
            try:
                item = _DECODER.decode(item)
            except (ValueError, RecursionError):
                continue
        pairs = _pairs(item)
        if pairs is not None:
            for key, value in pairs:
                if _SKIP_BRANCH.search(key):
                    continue
                if key.casefold() in {"headertext", "headingtext", "headline"} and _header_has_template(value):
                    return True
                if isinstance(value, (dict, list)) or (isinstance(value, str) and value.lstrip().startswith(("[", "{"))):
                    pending.append((value, depth + 1))
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item if isinstance(child, (dict, list)))
    return False


def _script_has_header(raw, *, json_only):
    raw = raw.strip()
    if not raw or len(raw) > MAX_STATE_CHARS:
        return False
    if json_only:
        try:
            return _payload_has_header(_DECODER.decode(raw))
        except (ValueError, RecursionError):
            return False
    for match in islice(_ASSIGNMENT.finditer(raw), 32):
        tail = raw[match.end():]
        if not tail.startswith(("{", "[", '"')):
            continue
        try:
            payload, end = _DECODER.raw_decode(tail)
        except (ValueError, RecursionError):
            continue
        if tail[end:].lstrip().startswith(";") and _payload_has_header(payload):
            return True
    return False


def has_literal_state_rate_template(html):
    if not html or len(html) > 16_000_000:
        return False
    class Observer(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.excluded = []
            self.parts = None
            self.size = 0
            self.count = 0
            self.json_only = False
            self.found = False
        def handle_starttag(self, tag, attrs):
            if tag in {"nav", "header", "footer", "aside", "style"}:
                self.excluded.append(tag)
            if tag != "script" or self.excluded or self.found:
                return
            attributes = dict(attrs)
            script_type = str(attributes.get("type") or "").lower()
            if attributes.get("src") or script_type not in {"", "text/javascript", "application/javascript", "application/json", "application/ld+json"} or self.count >= 8:
                return
            self.count += 1
            self.parts = []
            self.size = 0
            self.json_only = script_type in {"application/json", "application/ld+json"}
        def handle_data(self, data):
            if self.parts is None:
                return
            self.size += len(data)
            if self.size > MAX_STATE_CHARS:
                self.parts = None
                return
            self.parts.append(data)
        def handle_endtag(self, tag):
            if tag == "script" and self.parts is not None:
                self.found = _script_has_header("".join(self.parts), json_only=self.json_only)
                self.parts = None
            if tag in self.excluded:
                self.excluded.remove(tag)
    observer = Observer()
    try:
        observer.feed(html)
    except (ValueError, RecursionError):
        return False
    return observer.found