"""Read literal confirmation-dialog destinations without executing JavaScript."""
from html.parser import HTMLParser
import re

# Only a registered click on an existing confirmation button with one literal
# destination. Dynamic expressions, arbitrary script URLs and code are ignored.
_HANDLER = re.compile(
    r"\$\(\s*(['\"])#(?P<id>[A-Za-z0-9_-]+)\1\s*\)\.on\(\s*(['\"])click\3\s*,\s*"
    r"function\s*\(\s*\)\s*\{\s*window\.(?:"
    r"location\s*=\s*(['\"])(?P<location>https://[^'\"\s<>]+)\4"
    r"|open\(\s*(['\"])(?P<open>https://[^'\"\s<>]+)\6\s*\))"
    r"\s*;?\s*\}\s*\)\s*;?", re.I)
_INLINE = re.compile(r"^\s*window\.open\(\s*(['\"])(https://[^'\"\s<>]+)\1\s*(?:,\s*(['\"])_blank\3\s*)?\)\s*;?\s*$")
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_NON_CODE = re.compile(r"//[^\r\n]*|/\*[\s\S]*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`")


def _literal_handlers(script):
    excluded = [match.span() for match in _NON_CODE.finditer(script)]
    return (match for match in _HANDLER.finditer(script)
            if not any(start <= match.start() < end for start, end in excluded))

class _ModalLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.triggers = []
        self.buttons = {}
        self.dialogs = {}
        self.destinations = {}
        self.script = None
        self.scripts = 0
        self.nodes = 0
        self.capture = None

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 20000:
            return
        attributes = dict(attrs)
        dialog = attributes.get("id") if ("modal" in str(attributes.get("class", "")).split()
            or attributes.get("role") == "dialog" or attributes.get("aria-modal") == "true") else None
        if dialog:
            self.dialogs[dialog] = self.dialogs.get(dialog, 0) + 1
        if tag not in _VOID:
            self.stack.append((tag, dialog))
        if tag == "script" and not attributes.get("src") and self.scripts < 64:
            self.script = []
            self.scripts += 1
        target = attributes.get("data-target", "")
        if tag in {"a", "button"} and re.fullmatch(r"#[A-Za-z0-9_-]+", target) and attributes.get("data-toggle") == "modal":
            self.capture = {"target":target[1:], "label":attributes.get("title") or attributes.get("aria-label"), "parts":[], "depth":len(self.stack)}
        if tag == "button":
            parent = next((d for _,d in reversed(self.stack) if d), None)
            key = attributes.get("id")
            if key and parent:
                if key in self.buttons:
                    self.buttons[key] = None
                elif len(self.buttons) < 256:
                    self.buttons[key] = parent
                else:
                    return
                inline = _INLINE.fullmatch(attributes.get("onclick", ""))
                if inline:
                    self.destinations.setdefault(key, set()).add(inline[2])

    def handle_data(self, data):
        if self.script is not None:
            if sum(map(len, self.script)) + len(data) <= 100000:
                self.script.append(data)
            else:
                self.script = None
        if self.capture is not None:
            self.capture["parts"].append(data[:1000])

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            for match in _literal_handlers("".join(self.script)):
                self.destinations.setdefault(match["id"], set()).add(match["location"] or match["open"])
            self.script = None
        if self.capture and self.capture["depth"] == len(self.stack):
            self.triggers.append((self.capture["target"], self.capture["label"] or " ".join(self.capture["parts"])))
            self.capture = None
        index = next((i for i in range(len(self.stack)-1, -1, -1) if self.stack[i][0] == tag), None)
        if index is not None:
            del self.stack[index:]

    def links(self):
        result = []
        for target, label in self.triggers:
            if self.dialogs.get(target) != 1:
                continue
            urls = {url for key, dialog in self.buttons.items() if dialog == target
                    for url in self.destinations.get(key, set())}
            if len(urls) == 1 and label:
                result.append((urls.pop(), label.strip()))
        return result[:64]

def literal_modal_links(html):
    parser = _ModalLinks()
    parser.feed(html)
    return parser.links()
