from __future__ import annotations

from pathlib import Path
import os
import uuid
import unittest

from api_service.config import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_loads_boolean_and_origin_values_from_env_file(self) -> None:
        env_path = Path.cwd() / f"test_config_env_{uuid.uuid4().hex}.tmp"
        env_path.write_text(
            "\n".join(
                [
                    "FPDS_DATABASE_URL=postgres://user:pass@localhost:5432/fpds",
                    "FPDS_ADMIN_WEB_ORIGIN=http://localhost:3001",
                    "FPDS_ADMIN_API_ORIGIN=http://localhost:4000",
                    "FPDS_ALLOWED_ADMIN_ORIGINS=http://localhost:3001,http://127.0.0.1:3001",
                    "FPDS_ADMIN_SESSION_SECRET=dev-secret",
                    "FPDS_ADMIN_CSRF_SECRET=csrf-secret",
                    "FPDS_COOKIE_SECURE=false",
                    "FPDS_COOKIE_SAMESITE=Lax",
                ]
            ),
            encoding="utf-8",
        )

        previous = os.environ.copy()
        try:
            settings = Settings.from_env(env_path)
        finally:
            if env_path.exists():
                env_path.unlink()
            os.environ.clear()
            os.environ.update(previous)

        self.assertEqual(settings.admin_web_origin, "http://localhost:3001")
        self.assertEqual(settings.allowed_admin_origins, ("http://localhost:3001", "http://127.0.0.1:3001"))
        self.assertFalse(settings.cookie_secure)
        self.assertEqual(settings.cookie_same_site, "lax")

    def test_settings_loads_repo_root_env_file_when_process_runs_under_api_service(self) -> None:
        previous = os.environ.copy()
        original_cwd = Path.cwd()
        service_dir = Path(__file__).resolve().parents[1]
        try:
            os.chdir(service_dir)
            settings = Settings.from_env(".env.dev")
        finally:
            os.chdir(original_cwd)
            os.environ.clear()
            os.environ.update(previous)

        self.assertEqual(settings.admin_web_origin, "http://localhost:3001")
        self.assertEqual(settings.admin_api_origin, "http://localhost:4000")
