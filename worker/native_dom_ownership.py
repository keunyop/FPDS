"""Bounded native product ownership and literal local disclosure references."""
import re
from functools import lru_cache
from bs4 import BeautifulSoup, Tag


@lru_cache(maxsize=1024)
def _literal_attribute_name(value):
    if len(value) > 1000:
        return None
    if "<" not in value:
        return value
    label = BeautifulSoup(value, "html.parser")
    if any(tag.name not in {"sup", "span", "b", "strong"} for tag in label.find_all(True)):
        return None
    return label.get_text(" ", strip=True)


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
                if re.fullmatch(r"data-(?:card|product|account)[_-]?name", key, re.I):
                    literal = _literal_attribute_name(str(value))
                    if literal is None:
                        return False
                    names.append(literal)
            classes = " ".join(named.get("class", []))
            if re.search(r"(?:card|product|account)[_-](?:name|title)(?:\s|$)", classes, re.I):
                names.append(named.get_text(" ", strip=True))
        if any(n and not names_match(n, owner) for n in names):
            return False
    return True


def _numbered_container_note(target, ref):
    """A numeric superscript can select one explicitly numbered sibling note.

    Preserve all unnumbered shared copy. Missing/duplicate/empty numbered blocks
    are unresolved; a generic link or ordinary single note keeps full context.
    """
    whole = target.get_text(" ", strip=True)
    symbol = ref.get_text("", strip=True)
    if not re.fullmatch(r"[0-9]{1,3}", symbol) or ref.find_parent("sup") is None:
        return whole
    markers = target.find_all(["span", "sup"], class_="footnote")
    if len(markers) < 2:
        return whole
    if len(markers) > 128 or len(whole) > 24000:
        return None
    labels = [m.get_text("", strip=True) for m in markers]
    if (any(not re.fullmatch(r"[0-9]{1,3}", value) for value in labels)
            or len(set(labels)) != len(labels) or symbol not in labels):
        return None
    groups = [m.parent for m in markers]
    parent = groups[0].parent
    if (any(group is target or group.parent is not parent for group in groups)
            or len({id(group) for group in groups}) != len(groups)
            or any(next(iter(group.stripped_strings), "") != label
                or not group.find(["p", "li"])
                or not any(p.get_text(strip=True) for p in group.find_all(["p", "li"]))
                for group, label in zip(groups, labels))):
        return None
    excluded = {id(group) for group, label in zip(groups, labels) if label != symbol}
    return " ".join(str(t).strip() for t in target.find_all(string=True)
        if str(t).strip() and not any(id(a) in excluded for a in t.parents))


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
        elif ref.get("data-scroll-target"):
            target = str(ref["data-scroll-target"]).removeprefix("#")
            if not re.fullmatch(r"[A-Za-z][\w:.-]{0,199}", target):
                return None
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
        hints = []
        for key in ("href", "data-target"):
            value = str(ref.get(key, ""))
            if value.startswith("#") and len(value) > 1:
                hints.append(value[1:])
        for key in ("data-scroll-target", "aria-describedby"):
            if ref.get(key):
                hints.append(str(ref[key]).removeprefix("#"))
        if any(hint != target for hint in hints):
            return None
        targets = soup.find_all(id=target)
        if not targets:
            # CMS tooltip keys are literal references, scoped to the owned
            # block. Responsive copies must agree before one can support facts.
            components = soup.find_all(attrs={"tooltip-data-id": target})
            local = block.find_all(attrs={"tooltip-data-id": target})
            literals = {c.get_text(" ", strip=True) for c in components}
            if len(local) == 1 and len(literals) == 1 and components:
                targets = local
        # A reciprocal note return is navigation, not another disclosure.
        # Responsive copies may repeat the same numeric caller. Every caller
        # must point back to this uniquely identified complete note.
        note_id = block.get("id")
        if (note_id and len(soup.find_all(id=note_id)) == 1
                and re.fullmatch(r"[\s←]*Go back", ref.get_text(" ", strip=True), re.I)
                and targets and all(t.name == "a" and t.get("href") == "#" + note_id
                    and re.fullmatch(r"\d+", t.get_text("", strip=True)) for t in targets)):
            continue
        if len(targets) != 1:
            return None
        note = _numbered_container_note(targets[0], ref)
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
