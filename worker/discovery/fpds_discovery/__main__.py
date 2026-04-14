from __future__ import annotations

import argparse
import json
from pathlib import Path

from .discovery import SourceDiscoveryService
from .fetch import DiscoveryFetchPolicy, fetch_text
from .registry import load_registry
from .url_utils import normalize_source_url


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS source discovery runner")
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry JSON path.")
    parser.add_argument("--entry-html-path", type=Path, default=None, help="Offline entry page HTML fixture path.")
    parser.add_argument(
        "--page-html",
        action="append",
        default=[],
        help="Offline HTML mapping in the form URL=PATH. Repeat as needed.",
    )
    parser.add_argument("--run-id", default=None, help="Optional run identifier for result payloads.")
    parser.add_argument("--correlation-id", default=None, help="Optional correlation identifier for result payloads.")
    parser.add_argument(
        "--discovery-mode",
        default="manual",
        choices=("scheduled", "manual", "retry"),
        help="Discovery mode label used in the result payload.",
    )
    args = parser.parse_args()

    registry = load_registry(args.registry_path)
    service = SourceDiscoveryService(registry)

    if args.entry_html_path is not None:
        entry_html = args.entry_html_path.read_text(encoding="utf-8")
        html_overrides = _load_html_overrides(args.page_html)
        result = service.discover(
            entry_html=entry_html,
            html_overrides=html_overrides,
            run_id=args.run_id,
            correlation_id=args.correlation_id,
            discovery_mode=args.discovery_mode,
        )
    else:
        policy = DiscoveryFetchPolicy.from_env()
        result = service.discover_live(
            html_loader=lambda url: fetch_text(url, policy),
            run_id=args.run_id,
            correlation_id=args.correlation_id,
            discovery_mode=args.discovery_mode,
        )

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True))
    return 0


def _load_html_overrides(entries: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Invalid --page-html value: {entry}")
        raw_url, raw_path = entry.split("=", 1)
        normalized_url = normalize_source_url(raw_url)
        overrides[normalized_url] = Path(raw_path).read_text(encoding="utf-8")
    return overrides


if __name__ == "__main__":
    raise SystemExit(main())
