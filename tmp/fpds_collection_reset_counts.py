from __future__ import annotations

import argparse

from fpds_collection_reset_common import collect_db_counts, collect_s3_summary, load_settings, print_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Report FPDS collection artifact counts without mutating data.")
    parser.add_argument("--env-file", default=".env.dev")
    args = parser.parse_args()

    settings = load_settings(args.env_file)
    print_json(
        {
            "database": collect_db_counts(settings),
            "object_storage": collect_s3_summary(),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
