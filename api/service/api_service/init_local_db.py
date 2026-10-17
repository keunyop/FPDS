"""Initialize a fresh development database for local Admin/API use."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import urlsplit

import psycopg
from psycopg.rows import dict_row

from api_service.config import REPO_ROOT, Settings
from api_service.security import hash_password, new_id


MIGRATIONS = REPO_ROOT / "db" / "migrations"
_TRANSACTION_WRAPPER = re.compile(
    r"\A(?P<comments>(?:\s|--[^\n]*(?:\n|\Z))*)BEGIN;(?P<body>.*)COMMIT;\s*\Z",
    re.DOTALL | re.IGNORECASE,
)
_TRANSACTION_COMMAND = re.compile(r"^\s*(?:BEGIN|COMMIT|ROLLBACK)\s*;", re.MULTILINE | re.IGNORECASE)


def validate_local_settings(settings: Settings) -> None:
    origins = (
        settings.admin_web_origin, settings.public_web_origin,
        settings.admin_api_origin, settings.public_api_origin,
        *settings.allowed_admin_origins, *settings.allowed_public_origins,
    )
    if settings.env != "dev" or settings.cookie_secure:
        raise ValueError("Local initialization requires FPDS_ENV=dev and FPDS_COOKIE_SECURE=false.")
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme != "http" or parsed.hostname != "localhost"
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            raise ValueError("Local initialization requires http://localhost origins and allowlists.")


def migration_body(path: Path) -> str:
    """Keep migration SQL unchanged inside one initializer-owned transaction."""
    text = path.read_text(encoding="utf-8-sig")
    wrapped = _TRANSACTION_WRAPPER.fullmatch(text)
    body = wrapped.group("comments") + wrapped.group("body") if wrapped else text
    if _TRANSACTION_COMMAND.search(body):
        raise ValueError(f"Unsupported transaction command in {path.name}.")
    return body


def initialize(settings: Settings) -> None:
    validate_local_settings(settings)
    migrations = sorted(MIGRATIONS.glob("*.sql"))
    if not migrations:
        raise ValueError("No migrations found. Run this command from a complete source clone.")
    scripts = [(path.name, migration_body(path)) for path in migrations]
    password_hash = hash_password("admin")
    with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
        with connection.transaction():
            connection.execute("SELECT pg_advisory_xact_lock(716349580614)")
            existing = connection.execute(
                """
                SELECT n.nspname, c.relname
                FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname NOT LIKE 'pg\\_%' ESCAPE '\\'
                  AND n.nspname <> 'information_schema'
                  AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
                  AND NOT EXISTS (
                      SELECT 1 FROM pg_depend d
                      WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid
                        AND d.deptype = 'e'
                  )
                LIMIT 1
                """
            ).fetchone()
            if existing:
                raise ValueError("Database is not empty. Existing data and accounts were not changed.")
            connection.execute("SET LOCAL search_path TO public")
            for name, body in scripts:
                print(f"Applying {name}")
                connection.execute(body)

            # These are optional historical catalog seeds, in this fresh DB only.
            connection.execute("DELETE FROM source_registry_item")
            connection.execute("DELETE FROM source_registry_catalog_item")
            connection.execute("DELETE FROM bank")
            if connection.execute("SELECT count(*) AS count FROM user_account").fetchone()["count"]:
                raise ValueError("Unexpected seeded users; initialization rolled back.")
            connection.execute(
                """
                INSERT INTO user_account (
                    user_id, login_id, email, display_name, role, account_status,
                    password_hash, password_algorithm
                ) VALUES (%(user_id)s, 'admin', NULL, 'Admin', 'admin', 'active',
                          %(password_hash)s, 'scrypt')
                """,
                {"user_id": new_id("user"), "password_hash": password_hash},
            )
    print("Initialized local database. Login: admin / admin (local development only).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env.dev", help="Local development environment file.")
    args = parser.parse_args()
    try:
        initialize(Settings.from_env(args.env_file))
    except (ValueError, psycopg.Error) as exc:
        # Do not print a DSN or database/server diagnostics that might contain secrets.
        if isinstance(exc, ValueError):
            parser.exit(1, f"{exc}\n")
        parser.exit(1, "Database initialization failed; all changes rolled back. Check DB access and pgvector installation.\n")


if __name__ == "__main__":
    main()
