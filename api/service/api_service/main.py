from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api_service.auth import LoginError, authenticate_user, get_session_by_token, revoke_session
from api_service.config import Settings
from api_service.db import open_connection
from api_service.models import LoginRequest


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _meta(request: Request) -> dict[str, Any]:
    return {
        "request_id": request.state.request_id,
        "generated_at": request.state.generated_at,
    }


def _success(data: dict[str, Any], request: Request, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data, "meta": _meta(request)})


def _error(*, status_code: int, code: str, message: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "details": {}},
            "meta": _meta(request),
        },
    )


def _attach_auth_cookies(response: Response, *, settings: Settings, session_token: str, csrf_token: str | None) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path="/",
    )
    if csrf_token:
        response.set_cookie(
            key=settings.csrf_cookie_name,
            value=csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite=settings.cookie_same_site,
            path="/",
        )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


settings = Settings.from_env()
app = FastAPI(
    title="FPDS Admin API",
    docs_url="/docs",
    redoc_url=None,
)
app.state.settings = settings


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", f"req_{uuid4().hex}")
    request.state.generated_at = datetime.now(UTC).isoformat()
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id

    settings: Settings = request.app.state.settings
    if settings.security_headers_enabled:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'"
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(LoginError)
async def login_error_handler(request: Request, exc: LoginError):
    return _error(status_code=exc.status_code, code=exc.code, message=exc.message, request=request)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _error(status_code=422, code="validation_error", message="Invalid request payload.", request=request)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    return _error(status_code=500, code="internal_error", message="Internal server error.", request=request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_admin_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
)


def _resolve_session(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    settings: Settings = request.app.state.settings
    session_token = request.cookies.get(settings.session_cookie_name)
    if not session_token:
        raise LoginError(status_code=401, code="authentication_required", message="Admin session is required.")

    with open_connection(settings) as connection:
        resolved = get_session_by_token(connection, session_token=session_token, settings=settings)
        if not resolved:
            raise LoginError(status_code=401, code="authentication_required", message="Admin session is required.")
    return resolved


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/admin/auth/login")
async def login(request: Request, payload: LoginRequest) -> JSONResponse:
    settings: Settings = request.app.state.settings
    with open_connection(settings) as connection:
        user, session, session_token = authenticate_user(
            connection,
            email=payload.email,
            password=payload.password,
            ip_address=_request_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_id=request.state.request_id,
            settings=settings,
        )

    response = _success(
        {
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "display_name": user["display_name"],
                "issued_at": session["issued_at"].isoformat(),
                "expires_at": session["absolute_expires_at"].isoformat(),
            },
            "csrf_token": session["csrf_token"],
            "redirect_to": "/admin",
        },
        request,
    )
    _attach_auth_cookies(
        response,
        settings=settings,
        session_token=session_token,
        csrf_token=session["csrf_token"],
    )
    return response


@app.post("/api/admin/auth/logout")
async def logout(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        with open_connection(settings) as connection:
            resolved = get_session_by_token(connection, session_token=session_token, settings=settings)
            if resolved:
                actor, session = resolved
                revoke_session(
                    connection,
                    auth_session_id=session["auth_session_id"],
                    request_id=request.state.request_id,
                    actor=actor,
                    ip_address=_request_ip(request),
                    user_agent=request.headers.get("user-agent"),
                )

    response = _success({"logged_out": True}, request)
    _clear_auth_cookies(response, settings)
    return response


@app.get("/api/admin/auth/session")
async def session(request: Request) -> JSONResponse:
    actor, session_info = _resolve_session(request)
    return _success(
        {
            "user": actor,
            "csrf_token": session_info["csrf_token"],
        },
        request,
    )
