from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json
from typing import Any


def _wildcard_list() -> list[str]:
    return ["*"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "backend"
    debug: bool = True
    app_version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Database
    database_url: str = "sqlite:///./app.db"

    # Logging
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"
    log_max_body_bytes: int = 8192
    disable_uvicorn_access: bool = True
    log_request_headers: bool = True
    log_response_headers: bool = True

    # OpenTelemetry
    enable_otel: bool = False
    otel_endpoint: str | None = None  # e.g. "http://localhost:4318"

    # CORS
    cors_origins: list[str] | str = Field(default_factory=list)  # e.g. ["http://localhost:3000", "https://example.com"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] | str = Field(default_factory=_wildcard_list)
    cors_allow_headers: list[str] | str = Field(default_factory=_wildcard_list)

    # Redis (Upstash)
    redis_url: str | None = None  # e.g. rediss://:<password>@<host>:<port>

    # Session cookie (opaque, server-side stored)
    session_cookie_name: str = "sid"
    session_cookie_domain: str | None = None
    session_cookie_path: str = "/"
    session_cookie_secure: bool = True
    session_cookie_samesite: str = "lax"  # "lax" or "strict"
    # Default session lifetime (in minutes)
    session_expires_minutes: int = 60 * 24  # 24 hours

    # HTTPS
    https_port: int = 8443
    ssl_keyfile: str = "certs/api.zara.com-key.pem"
    ssl_certfile: str = "certs/api.zara.com.pem"

    frontend_url: str | None = None

    # Email service (e.g., Resend) API token
    # Maps from env var `EMAIL_SERVICE_TOKEN`
    email_service_token: str | None = None

    email_verification_expires_minutes: str = "5"  # 5 minutes
    default_to_email: str = ""
    default_to_email_flag: bool = True
    default_from_email: str = "onboarding@notifications.sciencearchive.site"

    env: str = "local"

    # Robust parsing for list settings from env strings
    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _parse_list_env(cls, v: Any) -> Any:
        if isinstance(v, list):
            return v
        if v is None:
            return v
        if isinstance(v, str):
            s = v.strip()
            # Accept JSON-style lists
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except Exception:
                    pass
            # Accept comma-separated values
            if "," in s:
                return [part.strip() for part in s.split(",") if part.strip()]
            # Accept single token like "*"
            return [s]
        return v


settings = Settings()
