from __future__ import annotations

from datetime import timedelta
import json
from typing import Any

from psycopg import Connection

from api_service.config import Settings
from api_service.security import (
    absolute_expiry,
    hash_session_token,
    idle_expiry,
    new_csrf_token,
    new_id,
    new_session_token,
    utc_now,
    verify_password,
)


class LoginError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _record_audit_event(
    connection: Connection,
    *,
    event_type: str,
    actor_type: str,
    actor_id: str | None,
    actor_role_snapshot: str | None,
    target_type: str,
    target_id: str,
    reason_code: str | None,
    reason_text: str | None,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO audit_event (
            audit_event_id,
            event_category,
            event_type,
            actor_type,
            actor_id,
            actor_role_snapshot,
            target_type,
            target_id,
            reason_code,
            reason_text,
            request_id,
            ip_address,
            user_agent,
            event_payload,
            occurred_at
        )
        VALUES (
            %(audit_event_id)s,
            'auth',
            %(event_type)s,
            %(actor_type)s,
            %(actor_id)s,
            %(actor_role_snapshot)s,
            %(target_type)s,
            %(target_id)s,
            %(reason_code)s,
            %(reason_text)s,
            %(request_id)s,
            %(ip_address)s,
            %(user_agent)s,
            %(event_payload)s::jsonb,
            %(occurred_at)s
        )
        """,
        {
            "audit_event_id": new_id("audit"),
            "event_type": event_type,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "actor_role_snapshot": actor_role_snapshot,
            "target_type": target_type,
            "target_id": target_id,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "request_id": request_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "event_payload": json.dumps(payload or {}),
            "occurred_at": utc_now(),
        },
    )


def _record_login_attempt(
    connection: Connection,
    *,
    email: str,
    user_id: str | None,
    ip_address: str | None,
    attempt_outcome: str,
    failure_reason_code: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO auth_login_attempt (
            login_attempt_id,
            email,
            user_id,
            ip_address,
            attempt_outcome,
            failure_reason_code,
            attempted_at
        )
        VALUES (
            %(login_attempt_id)s,
            %(email)s,
            %(user_id)s,
            %(ip_address)s,
            %(attempt_outcome)s,
            %(failure_reason_code)s,
            %(attempted_at)s
        )
        """,
        {
            "login_attempt_id": new_id("login"),
            "email": email,
            "user_id": user_id,
            "ip_address": ip_address,
            "attempt_outcome": attempt_outcome,
            "failure_reason_code": failure_reason_code,
            "attempted_at": utc_now(),
        },
    )


def get_user_by_email(connection: Connection, email: str) -> dict[str, Any] | None:
    return connection.execute(
        """
        SELECT
            user_id,
            email,
            display_name,
            role,
            account_status,
            password_hash,
            failed_login_count,
            locked_until
        FROM user_account
        WHERE email = %(email)s
        """,
        {"email": normalize_email(email)},
    ).fetchone()


def _count_recent_ip_failures(connection: Connection, *, ip_address: str | None, settings: Settings) -> int:
    if not ip_address:
        return 0

    row = connection.execute(
        """
        SELECT COUNT(*) AS failure_count
        FROM auth_login_attempt
        WHERE ip_address = %(ip_address)s
          AND attempt_outcome IN ('failed', 'rate_limited', 'locked_out')
          AND attempted_at >= %(cutoff)s
        """,
        {
            "ip_address": ip_address,
            "cutoff": utc_now() - timedelta(minutes=settings.login_attempt_window_minutes),
        },
    ).fetchone()
    return int(row["failure_count"]) if row else 0


def _increment_failure(
    connection: Connection,
    *,
    user_id: str,
    current_failed_count: int,
    settings: Settings,
) -> bool:
    next_count = current_failed_count + 1
    locked = next_count >= settings.login_lock_threshold
    connection.execute(
        """
        UPDATE user_account
        SET
            failed_login_count = %(failed_login_count)s,
            last_login_failed_at = %(last_login_failed_at)s,
            locked_until = %(locked_until)s,
            updated_at = %(updated_at)s
        WHERE user_id = %(user_id)s
        """,
        {
            "failed_login_count": next_count,
            "last_login_failed_at": utc_now(),
            "locked_until": (
                utc_now() + timedelta(minutes=settings.login_lock_window_minutes)
                if locked
                else None
            ),
            "updated_at": utc_now(),
            "user_id": user_id,
        },
    )
    return locked


def _reset_failures(connection: Connection, *, user_id: str) -> None:
    connection.execute(
        """
        UPDATE user_account
        SET
            failed_login_count = 0,
            last_login_failed_at = NULL,
            locked_until = NULL,
            last_login_succeeded_at = %(last_login_succeeded_at)s,
            updated_at = %(updated_at)s
        WHERE user_id = %(user_id)s
        """,
        {
            "last_login_succeeded_at": utc_now(),
            "updated_at": utc_now(),
            "user_id": user_id,
        },
    )


def create_session(
    connection: Connection,
    *,
    user: dict[str, Any],
    ip_address: str | None,
    user_agent: str | None,
    settings: Settings,
) -> tuple[dict[str, Any], str]:
    now = utc_now()
    session_token = new_session_token()
    session = {
        "auth_session_id": new_id("sess"),
        "user_id": user["user_id"],
        "session_token_hash": hash_session_token(session_token, settings.session_secret),
        "csrf_token": new_csrf_token() if settings.csrf_enabled else None,
        "session_status": "active",
        "issued_at": now,
        "last_seen_at": now,
        "idle_expires_at": idle_expiry(now, settings.session_idle_timeout_minutes),
        "absolute_expires_at": absolute_expiry(now, settings.session_absolute_timeout_hours),
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    connection.execute(
        """
        INSERT INTO admin_auth_session (
            auth_session_id,
            user_id,
            session_token_hash,
            csrf_token,
            session_status,
            issued_at,
            last_seen_at,
            idle_expires_at,
            absolute_expires_at,
            ip_address,
            user_agent
        )
        VALUES (
            %(auth_session_id)s,
            %(user_id)s,
            %(session_token_hash)s,
            %(csrf_token)s,
            %(session_status)s,
            %(issued_at)s,
            %(last_seen_at)s,
            %(idle_expires_at)s,
            %(absolute_expires_at)s,
            %(ip_address)s,
            %(user_agent)s
        )
        """,
        session,
    )
    return session, session_token


def authenticate_user(
    connection: Connection,
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    normalized_email = normalize_email(email)
    user = get_user_by_email(connection, normalized_email)

    if _count_recent_ip_failures(connection, ip_address=ip_address, settings=settings) >= settings.login_attempt_ip_threshold:
        _record_login_attempt(
            connection,
            email=normalized_email,
            user_id=user["user_id"] if user else None,
            ip_address=ip_address,
            attempt_outcome="rate_limited",
            failure_reason_code="ip_retry_threshold",
        )
        _record_audit_event(
            connection,
            event_type="auth_login_failed",
            actor_type="user",
            actor_id=user["user_id"] if user else None,
            actor_role_snapshot=user["role"] if user else None,
            target_type="auth_session",
            target_id=f"login:{normalized_email}",
            reason_code="ip_retry_threshold",
            reason_text="Recent login failures exceeded the per-IP threshold.",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            payload={"email": normalized_email},
        )
        raise LoginError(status_code=429, code="login_rate_limited", message="Too many recent login attempts. Try again later.")

    if not user:
        _record_login_attempt(
            connection,
            email=normalized_email,
            user_id=None,
            ip_address=ip_address,
            attempt_outcome="failed",
            failure_reason_code="invalid_credentials",
        )
        _record_audit_event(
            connection,
            event_type="auth_login_failed",
            actor_type="user",
            actor_id=None,
            actor_role_snapshot=None,
            target_type="auth_session",
            target_id=f"login:{normalized_email}",
            reason_code="invalid_credentials",
            reason_text="Unknown email or password.",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            payload={"email": normalized_email},
        )
        raise LoginError(status_code=401, code="invalid_credentials", message="Invalid email or password.")

    if user["account_status"] != "active":
        _record_login_attempt(
            connection,
            email=normalized_email,
            user_id=user["user_id"],
            ip_address=ip_address,
            attempt_outcome="locked_out",
            failure_reason_code="account_disabled",
        )
        _record_audit_event(
            connection,
            event_type="auth_login_failed",
            actor_type="user",
            actor_id=user["user_id"],
            actor_role_snapshot=user["role"],
            target_type="user_account",
            target_id=user["user_id"],
            reason_code="account_disabled",
            reason_text="Disabled account attempted to sign in.",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            payload={"email": normalized_email},
        )
        raise LoginError(status_code=403, code="account_disabled", message="This account is not allowed to sign in.")

    if user["locked_until"] and user["locked_until"] > utc_now():
        _record_login_attempt(
            connection,
            email=normalized_email,
            user_id=user["user_id"],
            ip_address=ip_address,
            attempt_outcome="locked_out",
            failure_reason_code="account_locked",
        )
        _record_audit_event(
            connection,
            event_type="auth_login_failed",
            actor_type="user",
            actor_id=user["user_id"],
            actor_role_snapshot=user["role"],
            target_type="user_account",
            target_id=user["user_id"],
            reason_code="account_locked",
            reason_text="Temporarily locked account attempted to sign in.",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            payload={"email": normalized_email},
        )
        raise LoginError(status_code=423, code="account_locked", message="This account is temporarily locked. Try again later.")

    if not verify_password(password, user["password_hash"]):
        locked = _increment_failure(
            connection,
            user_id=user["user_id"],
            current_failed_count=int(user["failed_login_count"]),
            settings=settings,
        )
        _record_login_attempt(
            connection,
            email=normalized_email,
            user_id=user["user_id"],
            ip_address=ip_address,
            attempt_outcome="locked_out" if locked else "failed",
            failure_reason_code="invalid_credentials",
        )
        _record_audit_event(
            connection,
            event_type="auth_login_failed",
            actor_type="user",
            actor_id=user["user_id"],
            actor_role_snapshot=user["role"],
            target_type="user_account",
            target_id=user["user_id"],
            reason_code="invalid_credentials",
            reason_text="Unknown email or password.",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            payload={"email": normalized_email, "locked": locked},
        )
        if locked:
            raise LoginError(status_code=423, code="account_locked", message="This account is temporarily locked. Try again later.")
        raise LoginError(status_code=401, code="invalid_credentials", message="Invalid email or password.")

    _reset_failures(connection, user_id=user["user_id"])
    session, session_token = create_session(
        connection,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        settings=settings,
    )
    _record_login_attempt(
        connection,
        email=normalized_email,
        user_id=user["user_id"],
        ip_address=ip_address,
        attempt_outcome="succeeded",
        failure_reason_code=None,
    )
    _record_audit_event(
        connection,
        event_type="auth_login_succeeded",
        actor_type="user",
        actor_id=user["user_id"],
        actor_role_snapshot=user["role"],
        target_type="auth_session",
        target_id=session["auth_session_id"],
        reason_code=None,
        reason_text="Admin login succeeded.",
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        payload={"email": normalized_email},
    )
    return user, session, session_token


def get_session_by_token(
    connection: Connection,
    *,
    session_token: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    session = connection.execute(
        """
        SELECT
            s.auth_session_id,
            s.user_id,
            s.csrf_token,
            s.session_status,
            s.issued_at,
            s.idle_expires_at,
            s.absolute_expires_at,
            u.email,
            u.role,
            u.display_name,
            u.account_status
        FROM admin_auth_session AS s
        JOIN user_account AS u
          ON u.user_id = s.user_id
        WHERE s.session_token_hash = %(session_token_hash)s
        """,
        {"session_token_hash": hash_session_token(session_token, settings.session_secret)},
    ).fetchone()
    if not session:
        return None

    now = utc_now()
    expired = session["session_status"] != "active" or session["account_status"] != "active"
    expired = expired or session["idle_expires_at"] <= now or session["absolute_expires_at"] <= now
    if expired:
        connection.execute(
            """
            UPDATE admin_auth_session
            SET
                session_status = CASE
                    WHEN session_status = 'active' THEN 'expired'
                    ELSE session_status
                END,
                revoked_reason = CASE
                    WHEN revoked_reason IS NULL THEN 'expired_or_invalidated'
                    ELSE revoked_reason
                END
            WHERE auth_session_id = %(auth_session_id)s
            """,
            {"auth_session_id": session["auth_session_id"]},
        )
        return None

    now = utc_now()
    connection.execute(
        """
        UPDATE admin_auth_session
        SET
            last_seen_at = %(last_seen_at)s,
            idle_expires_at = %(idle_expires_at)s
        WHERE auth_session_id = %(auth_session_id)s
        """,
        {
            "last_seen_at": now,
            "idle_expires_at": idle_expiry(now, settings.session_idle_timeout_minutes),
            "auth_session_id": session["auth_session_id"],
        },
    )

    actor = {
        "user_id": session["user_id"],
        "email": session["email"],
        "role": session["role"],
        "display_name": session["display_name"],
        "issued_at": session["issued_at"].isoformat(),
        "expires_at": session["absolute_expires_at"].isoformat(),
    }
    session_info = {
        "auth_session_id": session["auth_session_id"],
        "csrf_token": session["csrf_token"],
    }
    return actor, session_info


def revoke_session(
    connection: Connection,
    *,
    auth_session_id: str,
    request_id: str,
    actor: dict[str, Any],
    ip_address: str | None,
    user_agent: str | None,
    reason: str = "user_logout",
) -> None:
    connection.execute(
        """
        UPDATE admin_auth_session
        SET
            session_status = 'revoked',
            revoked_at = %(revoked_at)s,
            revoked_reason = %(revoked_reason)s
        WHERE auth_session_id = %(auth_session_id)s
        """,
        {
            "revoked_at": utc_now(),
            "revoked_reason": reason,
            "auth_session_id": auth_session_id,
        },
    )
    _record_audit_event(
        connection,
        event_type="auth_logout",
        actor_type="user",
        actor_id=actor["user_id"],
        actor_role_snapshot=actor["role"],
        target_type="auth_session",
        target_id=auth_session_id,
        reason_code=reason,
        reason_text="Admin session was closed.",
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        payload={"email": actor["email"]},
    )
