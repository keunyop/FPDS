from __future__ import annotations

import argparse
from getpass import getpass

from api_service.auth import normalize_email, validate_login_id
from api_service.config import Settings
from api_service.db import open_connection
from api_service.security import hash_password, new_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the first FPDS admin operator account.")
    parser.add_argument("--env-file", default=None, help="Optional env file to load before connecting to Postgres.")
    parser.add_argument("--login-id", required=True, help="Operator login ID.")
    parser.add_argument("--email", default=None, help="Optional operator email address.")
    parser.add_argument("--display-name", required=True, help="Operator display name.")
    parser.add_argument("--role", choices=["admin", "reviewer", "read_only"], default="admin")
    parser.add_argument("--password", default=None, help="Password. If omitted, the command prompts securely.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)
    login_id = validate_login_id(args.login_id)
    email = normalize_email(args.email) if args.email else None
    password = args.password or getpass("New operator password: ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters long.")

    with open_connection(settings) as connection:
        existing = connection.execute(
            "SELECT user_id FROM user_account WHERE login_id = %(login_id)s",
            {"login_id": login_id},
        ).fetchone()
        if existing:
            raise SystemExit(f"An operator account already exists for {login_id}.")

        connection.execute(
            """
            INSERT INTO user_account (
                user_id,
                login_id,
                email,
                display_name,
                role,
                account_status,
                password_hash,
                password_algorithm
            )
            VALUES (
                %(user_id)s,
                %(login_id)s,
                %(email)s,
                %(display_name)s,
                %(role)s,
                'active',
                %(password_hash)s,
                'scrypt'
            )
            """,
            {
                "user_id": new_id("user"),
                "login_id": login_id,
                "email": email,
                "display_name": args.display_name,
                "role": args.role,
                "password_hash": hash_password(password),
            },
        )

    print(f"Created {args.role} operator account for {login_id}.")


if __name__ == "__main__":
    main()
