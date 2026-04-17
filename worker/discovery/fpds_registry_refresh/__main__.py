from __future__ import annotations

import argparse
import json
from pathlib import Path

from worker.discovery.env import load_env_file, resolve_default_env_file
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy
from worker.discovery.fpds_discovery.registry import load_registry

from .service import RegistryRefreshService


def main() -> int:
    parser = argparse.ArgumentParser(description="FPDS source registry refresh artifact generation")
    parser.add_argument("--run-id", required=True, help="Refresh run identifier.")
    parser.add_argument("--correlation-id", default=None, help="Optional correlation identifier.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional env file to load before execution.")
    parser.add_argument(
        "--no-default-env-file",
        action="store_true",
        help="Disable automatic loading of .env.dev or .env when --env-file is not provided.",
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Optional custom registry path.")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional JSON artifact path to write in addition to stdout.",
    )
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None and not args.no_default_env_file:
        env_file = resolve_default_env_file()
    loaded_env_keys: list[str] = []
    if env_file is not None:
        loaded_env_keys = sorted(load_env_file(env_file, override=True).keys())

    registry = load_registry(args.registry_path)
    service = RegistryRefreshService(
        registry=registry,
        fetch_policy=DiscoveryFetchPolicy.from_env(extra_allowed_domains=registry.allowed_domains),
    )
    result = service.refresh_live(
        run_id=args.run_id,
        correlation_id=args.correlation_id,
    )
    output = result.to_dict()
    output["runtime"] = {
        "env_file": str(env_file) if env_file is not None else None,
        "loaded_env_key_count": len(loaded_env_keys),
        "registry_path": str(args.registry_path) if args.registry_path is not None else None,
        "artifact_path": str(args.output_path) if args.output_path is not None else None,
    }

    encoded = json.dumps(output, indent=2, ensure_ascii=True)
    if args.output_path is not None:
        args.output_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
