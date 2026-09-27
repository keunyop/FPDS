"""Read-only, operator-invoked checks of approved Public bank destinations.

Run from the repository root. Writes only the requested local JSON/Markdown
report; never updates a URL, verification date, canonical record or snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, validate_fetch_url

PUBLIC_ORIGIN = "https://www.switchabank.com"
MAX_BODY = 524288
MAX_REDIRECTS = 5


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PageIdentity(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.headings = []
        self.refresh = None
        self.canonical = None
        self._title = False
        self._title_seen = False
        self._svg = 0
        self._h1 = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "svg":
            self._svg += 1
        if tag == "title" and not self._svg and not self._title_seen:
            self._title = True
            self._title_seen = True
        if tag == "h1":
            self._h1 = True
            self.headings.append("")
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.refresh = attrs.get("content", "")[:500]
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href", "")[:2048]

    def handle_endtag(self, tag):
        if tag == "svg":
            self._svg = max(0, self._svg - 1)
        if tag == "title":
            self._title = False
        if tag == "h1":
            self._h1 = False

    def handle_data(self, data):
        if self._title:
            self.title = (self.title + data)[:500]
        if self._h1 and self.headings:
            self.headings[-1] = (self.headings[-1] + data)[:500]


def normalized_identity(value):
    return " ".join(re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE))


def comparable_url(value):
    parsed = urlparse(value)
    host = (parsed.hostname or "").removeprefix("www.")
    return (host, parsed.path.rstrip("/") or "/", parsed.query)


def safe_destination(value, policy):
    parsed = urlparse(value)
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port not in (None, 443) or not parsed.hostname
            or any(char.isspace() for char in value) or "\\" in value):
        raise ValueError("Unsupported official URL")
    return validate_fetch_url(value, policy)


def probe(product, *, opener=None, validator=safe_destination):
    url = product.get("product_url")
    result = {
        "product_id": product["product_id"], "country_code": product["country_code"],
        "bank": product["bank_name"], "product": product["product_name"],
        "checked_at": datetime.now(UTC).isoformat(), "original_url": url,
        "final_url": None, "http_status": None, "redirects": [],
        "title": None, "headings": [], "canonical_url": None,
        "status": "missing_url",
    }
    if not url:
        return result
    # Approved Public URL supplies the initial bank host. Only its exact www/apex
    # counterpart is traversable; any other destination is recorded for review.
    try:
        hostname = urlparse(url).hostname or ""
    except ValueError:
        result["status"] = "blocked_or_unreachable"
        result["error_type"] = "ValueError"
        return result
    base = hostname.removeprefix("www.")
    policy = DiscoveryFetchPolicy(allowed_domains=(base, "www." + base), timeout_seconds=10, max_redirects=MAX_REDIRECTS)
    allowed_hosts = {base, "www." + base}
    opener = opener or urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}))
    current = url
    try:
        for hop in range(MAX_REDIRECTS + 1):
            if (urlparse(current).hostname or "") not in allowed_hosts:
                result["status"] = "external_redirect_review"
                return result
            current = validator(current, policy)
            result["final_url"] = current
            req = urllib.request.Request(current, headers={"User-Agent": "SwitchaBank/1.0 official-link-check", "Accept": "text/html,application/xhtml+xml"})
            try:
                response = opener.open(req, timeout=10)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                status = response.code
                result["http_status"] = status
                if status in (301, 302, 303, 307, 308):
                    target = urljoin(current, response.headers.get("Location", ""))
                    result["redirects"].append({"status": status, "from": current, "to": target})
                    if target == current or any(item["from"] == target for item in result["redirects"]):
                        result["status"] = "redirect_loop"
                        return result
                    current = target
                    continue
                if status >= 400:
                    result["status"] = "access_unverified" if status in (401, 403, 429) else "http_failure"
                    return result
                if not 200 <= status < 300:
                    result["status"] = "unexpected_status"
                    return result
                if response.headers.get_content_type() not in ("text/html", "application/xhtml+xml"):
                    result["status"] = "content_review"
                    return result
                body = response.read(MAX_BODY + 1)
                result["body_truncated"] = len(body) > MAX_BODY
                parser = PageIdentity()
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    decoded = body[:MAX_BODY].decode(charset, errors="replace")
                except LookupError:
                    decoded = body[:MAX_BODY].decode("utf-8", errors="replace")
                parser.feed(decoded)
                result.update(title=parser.title.strip(), headings=parser.headings[:8], canonical_url=parser.canonical)
                name = normalized_identity(product["product_name"])
                identity = normalized_identity(" ".join([parser.title, *parser.headings]))
                if re.search(r"access denied|just a moment|verify you are human|request rejected|page not found", identity):
                    result["status"] = "access_unverified"
                elif parser.refresh is not None:
                    result["status"] = "client_redirect_review"
                elif comparable_url(url) != comparable_url(current):
                    result["status"] = "redirect_review"
                elif parser.canonical and comparable_url(current) != comparable_url(urljoin(current, parser.canonical)):
                    result["status"] = "canonical_review"
                elif name and name in identity:
                    result["status"] = "reachable_identity_observed"
                else:
                    result["status"] = "identity_review"
                return result
        result["status"] = "redirect_limit"
    except (ValueError, OSError, urllib.error.URLError) as exc:
        result["status"] = "blocked_or_unreachable"
        result["error_type"] = type(exc).__name__
    return result


def load_products(country, *, read_json=None):
    def fetch(url):
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read(4_000_001)
            if len(data) > 4_000_000:
                raise ValueError("Public response exceeds limit")
            return json.loads(data)["data"]
    read_json = read_json or fetch
    items, seen, snapshot_id = [], set(), None
    for page in range(1, 101):
        response = read_json(f"{PUBLIC_ORIGIN}/api/public/products?country_code={country}&page={page}&page_size=100&locale=en")
        current = response["freshness"]["snapshot_id"]
        if not current or (page > 1 and current != snapshot_id) or response["page"] != page:
            raise ValueError("Public snapshot changed or unavailable; retry")
        snapshot_id = current
        for product in response["items"]:
            if product["country_code"] != country or product["status"] != "active" or product["product_id"] in seen:
                raise ValueError("Invalid or duplicate Public product")
            seen.add(product["product_id"])
            items.append(product)
        if not response["has_next_page"]:
            return snapshot_id, items
        if not response["items"]:
            raise ValueError("Empty intermediate Public page")
    raise ValueError("Public pagination exceeds limit")


def markdown_report(report):
    def cell(value):
        return str(value or "—").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("\r", " ").replace("\n", " ")
    lines = ["# Official bank link check", "", f"Checked: {report['checked_at']}",
             f"Country: {report['country_code']} · Snapshot: {report['snapshot_id']}", "",
             "Read-only network observations. Redirects and identity reviews require a human",
             "to compare the product page. Reachability does not verify current financial terms.",
             "403/429/challenges are inconclusive, not proof a product was withdrawn.", "",
             "| Product | Result | HTTP | Original URL | Final URL | Page title |",
             "|---|---|---|---|---|---|"]
    for item in report["items"]:
        lines.append("| " + " | ".join(cell(item.get(key)) for key in ("product", "status", "http_status", "original_url", "final_url", "title")) + " |")
    lines += ["", "## Redirects", ""]
    for item in report["items"]:
        for hop in item["redirects"]:
            lines.append(f"- {cell(item['product'])}: {hop['status']} · {cell(hop['from'])} → {cell(hop['to'])}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True, choices=("CA", "US"))
    parser.add_argument("--product-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--output", required=True, help="Local report prefix; creates .json and .md")
    args = parser.parse_args()
    if not 1 <= args.limit <= 50 or len(args.product_id) > 50:
        parser.error("A run is limited to 1–50 products")
    if len(set(args.product_id)) > args.limit:
        parser.error("Requested product count exceeds --limit; increase it up to 50")
    snapshot, products = load_products(args.country)
    if args.product_id:
        requested = set(args.product_id)
        products = [product for product in products if product["product_id"] in requested]
        if len(products) != len(requested):
            parser.error("Requested product is not in the current country snapshot")
    products = sorted(products, key=lambda item: (item["bank_name"], item["product_name"]))[:args.limit]
    report = {"checked_at": datetime.now(UTC).isoformat(), "country_code": args.country,
              "snapshot_id": snapshot, "items": [probe(product) for product in products]}
    report["counts"] = dict(Counter(item["status"] for item in report["items"]))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"checked": len(products), "counts": report["counts"], "report": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
