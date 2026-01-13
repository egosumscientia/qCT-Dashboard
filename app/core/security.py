from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class FakeUser:
    username: str
    role: str = "viewer"


def get_current_user() -> FakeUser:
    return FakeUser(username=settings.auth_fake_user)
