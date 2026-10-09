"""Bounded native product ownership and literal local disclosure references."""
import re
from bs4 import Tag


def unique_heading(root):
    headings = root.find_all("h1")
    names = {" ".join(h.get_text(" ", strip=True).split()): h for h in headings if h.get_text(" ", strip=True).strip()}
    return next(iter(names.values())) if len(names) == 1 else None


def owns_label(node, root, owner):
    """A named sibling panel cannot donate its values to the page's H1."""
    from worker.native_information_records import names_match
    for ancestor in [node, *list(node.parents)[:8]]:
        if ancestor is root or not isinstance(ancestor, Tag):
            break
        if len(ancestor.get_text(" ", strip=True)) > 8000:
            break
        names = []
        for named in [ancestor, *ancestor.find_all(True)]:
            for key, value in named.attrs.items():
                if re.fullmatch(r"data-(?:card|product|account)[_-]name", key, re.I):
                    names.append(str(value))
            classes = " ".join(named.get("class", []))
            if re.search(r"(?:card|product|account)[_-](?:name|title)(?:\s|$)", classes, re.I):
                names.append(named.get_text(" ", strip=True))
        if any(n and not names_match(n, owner) for n in names):
            return False
    return True


def local_notes(soup, block):
    """Resolve only unique same-document literal references; never evaluate JS."""
    notes = []
    for ref in block.find_all(True):
        target = None
        href = str(ref.get("href", ""))
        if href.startswith("#") and len(href) > 1:
            target = href[1:]
        elif str(ref.get("data-target", "")).startswith("#"):
            target = str(ref["data-target"])[1:]
        elif ref.get("aria-describedby"):
            ids = str(ref["aria-describedby"]).split()
            if len(ids) != 1:
                return None
            target = ids[0]
        elif "footnote" in ref.name and ref.get("target"):
            target = str(ref["target"])
        if not target:
            if href == "#":
                return None
            continue
        targets = soup.find_all(id=target)
        if len(targets) != 1:
            return None
        note = targets[0].get_text(" ", strip=True)
        if not note or len(note) > 6000:
            return None
        notes.append(note)
    return list(dict.fromkeys(notes))


def without_reference_markers(block):
    from copy import deepcopy
    literal = deepcopy(block)
    for sup in literal.find_all("sup"):
        if sup.find("a") is not None:
            sup.decompose()
    return literal.get_text("\n", strip=True)
