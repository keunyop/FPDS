"""Bounded native DOM product boundaries shared by discovery and parsing.

No bank, price or source-specific selector establishes product ownership.
A section has one primary heading, subordinate labelled financial facts and
its complete local notes. Sibling headings never donate their facts.
"""
from dataclasses import dataclass, field
from html.parser import HTMLParser
import re

@dataclass(eq=False)
class _Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    parent: object = None
    children: list = field(default_factory=list)

    def nodes(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.nodes()

    def text(self, sep="\n"):
        parts = []
        for child in self.children:
            value = child.text(sep) if isinstance(child, _Node) else child.strip()
            if value:
                parts.append(value)
        return sep.join(parts)

class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack = [self.root]
        self.skip = 0
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if self.skip or tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
            return
        self.count += 1
        if self.count > 40000:
            return
        node = _Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "area", "embed"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not self.skip and self.count <= 40000 and data.strip():
            self.stack[-1].children.append(data)

@dataclass(frozen=True)
class NamedProductSection:
    name: str
    text: str
    financial_records: tuple[str, ...]

_LABEL = re.compile(r"^(?:Monthly (?:account |plan )?fees?|Annual fees?|Transactions Included|Transactions per month|Additional transactions|Interest rates?|Rates and fees|Loan terms?)$", re.I)
_PRODUCT = re.compile(r"\b(?:account|card|plan|GIC|certificate|deposit|mortgage|loan|line of credit)\b", re.I)

def extract_named_product_sections(html: str) -> list[NamedProductSection]:
    if len(html) > 4000000:
        return []
    tree = _Tree()
    tree.feed(html)
    if tree.count > 40000:
        return []
    roots = [n for n in tree.root.nodes() if n.tag == "main" or n.attrs.get("id") in {"maincontent", "main-content"}]
    root = roots[0] if roots else tree.root
    sections = []
    seen = set()
    for heading in [n for n in root.nodes() if n.tag in {"h2", "h3", "h4"}][:128]:
        name = re.sub(r"\s+", " ", heading.text(" ")).strip()
        if not _PRODUCT.search(name) or _LABEL.fullmatch(name) or not 4 <= len(name) <= 120:
            continue
        level = int(heading.tag[1])
        block = heading
        parent = heading.parent
        while parent is not None and parent is not root and parent.tag not in {"body", "html", "root"}:
            primary = [n for n in parent.nodes() if re.fullmatch(r"h[1-4]", n.tag) and int(n.tag[1]) <= level]
            if len(primary) != 1 or primary[0] is not heading or len(parent.text()) > 12000:
                break
            block = parent
            parent = parent.parent
        text = block.text()
        labelled = [n for n in block.nodes() if re.fullmatch(r"h[2-6]", n.tag) and _LABEL.fullmatch(n.text(" ").strip())]
        if len(labelled) < 2 or not re.search(r"[$%]|\bunlimited\b", text, re.I):
            continue
        # Local numeric notes belong to this DOM product, never global notes.
        notes = {}
        for n in block.nodes():
            if n.tag != "p":
                continue
            for m in re.finditer(r"(?:^|\s)(\d+)\.\s*(.*?)(?=\s\d+\.\s|$)", n.text(" ")):
                notes.setdefault(m[1], set()).add(m[2].strip())
        records = []
        for label in labelled:
            following = []
            references = set()
            unresolved = False
            nodes = list(block.nodes())
            pos = nodes.index(label)
            consumed = set()
            for n in nodes[pos+1:]:
                if re.fullmatch(r"h[1-6]", n.tag):
                    break
                if n.tag in {"p", "table", "ul", "dl"} and not any(a in consumed for a in _ancestors(n)):
                    if n.tag == "table":
                        following.extend(row.text(" ") for row in n.nodes() if row.tag == "tr")
                    else:
                        following.append(n.text(" "))
                    references.update(ref.text(" ").strip() for ref in n.nodes() if ref.tag == "sup")
                    unresolved |= any(str(ref.attrs.get("href") or "").startswith("#") or ref.attrs.get("aria-describedby")
                                      for ref in n.nodes())
                    consumed.add(n)
            if following:
                if unresolved or any(len(notes.get(ref, set())) != 1 for ref in references):
                    continue  # An unresolved local reference cannot prove a price.
                record = "\n".join([name, label.text(" "), *following,
                                     *[ref + ". " + next(iter(notes[ref])) for ref in sorted(references)]])
                records.append(record)
        if name.casefold() not in seen and records:
            sections.append(NamedProductSection(name, text, tuple(records)))
            seen.add(name.casefold())
    return sections

def _ancestors(node):
    parent = node.parent
    while parent is not None:
        yield parent
        parent = parent.parent


def complete_named_account_sections(html: str) -> list[NamedProductSection]:
    from worker.pipeline.fpds_collection_accuracy import quote_supports_value
    result = []
    for section in extract_named_product_sections(html):
        facts = {}
        for record in section.financial_records:
            proposals = {}
            price = re.search(r"(?mi)^Monthly (?:account |plan )?fees?\n\$(\d+(?:\.\d+)?)", record)
            count = re.search(r"(?mi)^Transactions Included\n(\d+) included", record)
            excess = re.search(r"(?mi)^Additional transactions:?\s+\$(\d+(?:\.\d+)?) each", record)
            if price:
                proposals["monthly_fee"] = float(price[1])
            if count:
                proposals["included_transactions"] = int(count[1])
            if excess:
                proposals["additional_transaction_fee"] = float(excess[1])
            if re.search(r"(?mi)^Transactions Included\nUnlimited", record):
                proposals["unlimited_transactions_flag"] = True
            for name, value in proposals.items():
                if quote_supports_value(name, value, record):
                    facts.setdefault(name, set()).add(value)
        if any(len(values) != 1 for values in facts.values()):
            continue
        if ("monthly_fee" in facts and ("unlimited_transactions_flag" in facts or
                {"included_transactions", "additional_transaction_fee"} <= facts.keys())
                and not {"unlimited_transactions_flag", "included_transactions"} <= facts.keys()):
            result.append(section)
    return result
