from __future__ import annotations

from argparse import Namespace
from contextlib import redirect_stdout
from dataclasses import replace
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from api_service import init_local_db, bootstrap_admin_user
from api_service.auth import authenticate_user, LoginError
from api_service.config import Settings, REPO_ROOT
from api_service.models import LoginRequest
from api_service.security import verify_password


def local_settings(dsn: str = 'postgresql://unused') -> Settings:
    with patch.dict(os.environ, {}, clear=True):
        return replace(Settings.from_env(REPO_ROOT / '.env.dev.example'), database_url=dsn)


class InitializerGuardTests(unittest.TestCase):
    def test_all_current_migrations_fit_one_transaction(self):
        paths = sorted(init_local_db.MIGRATIONS.glob('*.sql'))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(init_local_db.migration_body(path).strip())

    def test_production_and_nonlocal_settings_never_connect(self):
        settings = local_settings()
        invalid = [replace(settings, env='prod'), replace(settings, cookie_secure=True),
                   replace(settings, admin_web_origin='https://admin.example.com'),
                   replace(settings, allowed_admin_origins=('https://admin.example.com',)),
                   replace(settings, public_api_origin='http://localhost.attacker.test:4000'),
                   replace(settings, admin_api_origin='http://user:pass@localhost:4000')]
        for value in invalid:
            with self.subTest(settings=value), patch.object(init_local_db.psycopg, 'connect') as connect:
                with self.assertRaises(ValueError):
                    init_local_db.initialize(value)
                connect.assert_not_called()

    def test_unexpected_transaction_control_rejected_before_connect(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '0001_invalid.sql'
            path.write_text('BEGIN;\nCREATE TABLE unwanted(id int);\nCOMMIT;\nSELECT 1;', encoding='utf-8')
            with patch.object(init_local_db, 'MIGRATIONS', Path(folder)), patch.object(init_local_db.psycopg, 'connect') as connect:
                with self.assertRaisesRegex(ValueError, 'Unsupported transaction'):
                    init_local_db.initialize(local_settings())
                connect.assert_not_called()

    def test_missing_migrations_rejected_before_connect(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(init_local_db, 'MIGRATIONS', Path(folder)), patch.object(init_local_db.psycopg, 'connect') as connect:
            with self.assertRaisesRegex(ValueError, 'No migrations'):
                init_local_db.initialize(local_settings())
            connect.assert_not_called()


    def test_normal_bootstrap_keeps_minimum_password_rule(self):
        args = Namespace(env_file='.env.dev', login_id='admin', email=None, password='admin')
        with patch.object(bootstrap_admin_user, 'parse_args', return_value=args), patch.object(bootstrap_admin_user.Settings, 'from_env', return_value=local_settings()), patch.object(bootstrap_admin_user, 'open_connection') as connect:
            with self.assertRaisesRegex(SystemExit, 'at least 8'):
                bootstrap_admin_user.main()
            connect.assert_not_called()

@unittest.skipUnless(os.getenv('FPDS_INITIALIZER_TEST_DSN'), 'Requires a disposable local PostgreSQL server')
class InitializerPostgresTests(unittest.TestCase):
    def setUp(self):
        self.base_dsn = os.environ['FPDS_INITIALIZER_TEST_DSN']
        parts = conninfo_to_dict(self.base_dsn)
        if parts.get('host') != '127.0.0.1' or parts.get('port') != '55437' or parts.get('user') != 'fpds_setup_test' or parts.get('dbname') != 'postgres':
            self.fail('Use only the dedicated local initializer test server.')
        self.name = 'fpds_init_test_' + uuid4().hex
        with psycopg.connect(self.base_dsn, autocommit=True) as connection:
            connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(self.name)))
            self.has_vector = connection.execute("SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name='vector')").fetchone()[0]
        self.dsn = make_conninfo(self.base_dsn, dbname=self.name)
        self.settings = local_settings(self.dsn)
        self.folder = tempfile.TemporaryDirectory()
        for path in init_local_db.MIGRATIONS.glob('*.sql'):
            if self.has_vector or not path.name.startswith('0012_'):
                (Path(self.folder.name) / path.name).write_bytes(path.read_bytes())
        self.addCleanup(self.folder.cleanup)

    def tearDown(self):
        with psycopg.connect(self.base_dsn, autocommit=True) as connection:
            connection.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(self.name)))

    def initialize_available_migrations(self):
        with patch.object(init_local_db, 'MIGRATIONS', Path(self.folder.name)), redirect_stdout(io.StringIO()):
            init_local_db.initialize(self.settings)

    def test_minimal_seed_and_real_admin_login(self):
        self.initialize_available_migrations()
        with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
            users = connection.execute('SELECT * FROM user_account').fetchall()
            self.assertEqual(len(users), 1)
            self.assertEqual((users[0]['login_id'], users[0]['role'], users[0]['account_status']), ('admin', 'admin', 'active'))
            self.assertNotEqual(users[0]['password_hash'], 'admin')
            self.assertTrue(verify_password('admin', users[0]['password_hash']))
            for table in ('bank', 'source_registry_item', 'source_registry_catalog_item', 'source_document', 'ingestion_run', 'canonical_product', 'audit_event'):
                self.assertEqual(connection.execute(sql.SQL('SELECT count(*) AS count FROM {}').format(sql.Identifier(table))).fetchone()['count'], 0)
            self.assertGreater(connection.execute('SELECT count(*) AS count FROM country_registry').fetchone()['count'], 0)
            self.assertGreater(connection.execute('SELECT count(*) AS count FROM product_type_registry').fetchone()['count'], 0)
            self.assertGreater(connection.execute('SELECT count(*) AS count FROM processing_policy_config').fetchone()['count'], 0)
            country = connection.execute("SELECT country_code FROM country_registry WHERE status='active' LIMIT 1").fetchone()['country_code']
            payload = LoginRequest(login_id='admin', password='admin', country_code=country)
            actor, session, token = authenticate_user(connection, login_id=payload.login_id, password=payload.password, country_code=payload.country_code,
                ip_address=None, user_agent='initializer-test', request_id='setup-test', settings=self.settings)
            self.assertEqual(actor['role'], 'admin')
            self.assertEqual(session['country_code'], country)
            self.assertTrue(token)
            with self.assertRaises(LoginError):
                authenticate_user(connection, login_id='admin', password='wrong', country_code=country,
                    ip_address=None, user_agent='initializer-test', request_id='setup-wrong', settings=self.settings)

    def test_second_initialization_preserves_existing_account(self):
        self.initialize_available_migrations()
        with psycopg.connect(self.dsn) as connection:
            before = connection.execute('SELECT user_id, password_hash FROM user_account').fetchall()
        with self.assertRaisesRegex(ValueError, 'not empty'):
            self.initialize_available_migrations()
        with psycopg.connect(self.dsn) as connection:
            self.assertEqual(connection.execute('SELECT user_id, password_hash FROM user_account').fetchall(), before)

    def test_existing_custom_schema_data_is_preserved(self):
        with psycopg.connect(self.dsn) as connection:
            connection.execute('CREATE SCHEMA existing; CREATE TABLE existing.keep_me(value text);')
            connection.execute("INSERT INTO existing.keep_me VALUES ('preserve')")
        with self.assertRaisesRegex(ValueError, 'not empty'):
            self.initialize_available_migrations()
        with psycopg.connect(self.dsn) as connection:
            self.assertEqual(connection.execute('SELECT value FROM existing.keep_me').fetchone()[0], 'preserve')
            self.assertIsNone(connection.execute("SELECT to_regclass('public.user_account')").fetchone()[0])

    def test_failure_rolls_back_schema_seeds_and_accounts(self):
        (Path(self.folder.name) / '9999_failure.sql').write_text('BEGIN;\nSELECT 1/0;\nCOMMIT;', encoding='utf-8')
        with self.assertRaises(psycopg.errors.DivisionByZero):
            self.initialize_available_migrations()
        with psycopg.connect(self.dsn) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'").fetchone()[0], 0)

    def test_unexpected_seeded_user_aborts_and_rolls_back(self):
        (Path(self.folder.name) / '9998_seeded_user.sql').write_text(
            "INSERT INTO user_account(user_id, login_id, email, display_name, role, account_status, password_hash) "
            "VALUES ('seed-user', 'unexpected', NULL, 'Unexpected', 'read_only', 'active', 'not-a-password');",
            encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unexpected seeded users'):
            self.initialize_available_migrations()
        with psycopg.connect(self.dsn) as connection:
            self.assertIsNone(connection.execute("SELECT to_regclass('public.user_account')").fetchone()[0])
    def test_full_install_or_missing_vector_atomic_rollback(self):
        with redirect_stdout(io.StringIO()):
            if self.has_vector:
                init_local_db.initialize(self.settings)
            else:
                with self.assertRaises(psycopg.errors.FeatureNotSupported):
                    init_local_db.initialize(self.settings)
                with psycopg.connect(self.dsn) as connection:
                    self.assertEqual(connection.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'").fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
