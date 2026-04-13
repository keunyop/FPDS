from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


SESSION_COOKIE_NAME = "fpds_admin_session"
CSRF_COOKIE_NAME = "fpds_admin_csrf"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILES = (REPO_ROOT / ".env.dev", REPO_ROOT / ".env.dev.example")


def _resolve_env_path(path: str | os.PathLike[str]) -> Path:
    env_path = Path(path)
    if env_path.is_absolute():
        return env_path

    candidates = (
        Path.cwd() / env_path,
        REPO_ROOT / env_path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path.cwd() / env_path


def _load_env_file(path: str | os.PathLike[str] | None) -> None:
    if not path:
        return

    env_path = _resolve_env_path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _read_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str
    admin_web_origin: str
    admin_api_origin: str
    allowed_admin_origins: tuple[str, ...]
    request_id_header: str
    session_cookie_name: str
    csrf_cookie_name: str
    session_secret: str
    csrf_secret: str
    cookie_secure: bool
    cookie_same_site: str
    security_headers_enabled: bool
    csrf_enabled: bool
    session_idle_timeout_minutes: int
    session_absolute_timeout_hours: int
    login_lock_window_minutes: int
    login_lock_threshold: int
    login_attempt_window_minutes: int
    login_attempt_ip_threshold: int

    @classmethod
    def from_env(cls, env_file: str | os.PathLike[str] | None = None) -> "Settings":
        selected_env_file = env_file or os.getenv("FPDS_ENV_FILE")
        if selected_env_file:
            _load_env_file(selected_env_file)
        else:
            for candidate in DEFAULT_ENV_FILES:
                _load_env_file(candidate)
        allowed_admin_origins = tuple(
            origin.strip()
            for origin in os.getenv("FPDS_ALLOWED_ADMIN_ORIGINS", "").split(",")
            if origin.strip()
        )
        if not allowed_admin_origins:
            allowed_admin_origins = (_read_required("FPDS_ADMIN_WEB_ORIGIN"),)

        cookie_same_site = os.getenv("FPDS_COOKIE_SAMESITE", "Lax").strip().lower()
        if cookie_same_site not in {"lax", "strict", "none"}:
            raise RuntimeError("FPDS_COOKIE_SAMESITE must be one of: Lax, Strict, None")

        return cls(
            env=os.getenv("FPDS_ENV", "dev"),
            database_url=_read_required("FPDS_DATABASE_URL"),
            admin_web_origin=_read_required("FPDS_ADMIN_WEB_ORIGIN"),
            admin_api_origin=_read_required("FPDS_ADMIN_API_ORIGIN"),
            allowed_admin_origins=allowed_admin_origins,
            request_id_header=os.getenv("FPDS_REQUEST_ID_HEADER", "x-request-id"),
            session_cookie_name=SESSION_COOKIE_NAME,
            csrf_cookie_name=CSRF_COOKIE_NAME,
            session_secret=_read_required("FPDS_ADMIN_SESSION_SECRET"),
            csrf_secret=_read_required("FPDS_ADMIN_CSRF_SECRET"),
            cookie_secure=_read_bool("FPDS_COOKIE_SECURE", False),
            cookie_same_site=cookie_same_site,
            security_headers_enabled=_read_bool("FPDS_SECURITY_HEADERS_ENABLED", True),
            csrf_enabled=_read_bool("FPDS_CSRF_PROTECTION_ENABLED", True),
            session_idle_timeout_minutes=60,
            session_absolute_timeout_hours=12,
            login_lock_window_minutes=15,
            login_lock_threshold=5,
            login_attempt_window_minutes=15,
            login_attempt_ip_threshold=10,
        )
