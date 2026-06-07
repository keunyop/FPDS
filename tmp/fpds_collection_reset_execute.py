from __future__ import annotations

import argparse

from fpds_collection_reset_common import delete_s3_prefix, load_settings, print_json, reset_db_collection_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete FPDS product collection DB artifacts and S3 prefix contents.")
    parser.add_argument("--env-file", default=".env.dev")
    parser.add_argument("--skip-db", action="store_true")
    parser.add_argument("--skip-s3", action="store_true")
    args = parser.parse_args()

    settings = load_settings(args.env_file)
    result = {}
    if not args.skip_db:
        result["database"] = reset_db_collection_artifacts(settings)
    if not args.skip_s3:
        result["object_storage"] = delete_s3_prefix()
    print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
