from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "qCT Dashboard"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg2://qct:qct@localhost:5432/qct"
    auth_fake_user: str = "demo_user"
    data_source: str = "mock"
    allow_phi: bool = False
    orthanc_url: str = "http://localhost:8042"
    orthanc_username: str = ""
    orthanc_password: str = ""


settings = Settings()
