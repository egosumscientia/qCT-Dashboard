from __future__ import annotations

from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "qCT Dashboard"
    environment: Literal["dev", "demo", "prod"] = "dev"
    database_url: str = "postgresql+psycopg2://qct:qct@localhost:5432/qct"
    auth_fake_user: str = "demo_user"
    auth_users: str = "demo:demo:Demo Viewer:viewer"
    auth_realm: str = "qct-dashboard"
    auth_session_secret: str = "change-me"
    auth_session_cookie: str = "qct_session"
    auth_session_max_age: int = 60 * 60 * 8
    data_source: Literal["mock", "orthanc"] = "mock"
    mock_data: bool = True
    allow_phi: bool = False
    orthanc_url: str = "http://localhost:8042"
    orthanc_username: str = ""
    orthanc_password: str = ""
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"
    cors_allow_origins: list[str] = []
    cors_allow_methods: list[str] = ["GET"]
    cors_allow_headers: list[str] = ["*"]
    cors_allow_credentials: bool = False
    ready_check_db: bool = True
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_connect_timeout: int = 10
    db_statement_timeout_ms: int = 0
    metrics_enabled: bool = False
    metrics_path: str = "/metrics"

    @field_validator("cors_allow_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
