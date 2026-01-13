from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User


@dataclass(frozen=True)
class AuthUser:
    username: str
    display_name: str
    role: str


@dataclass(frozen=True)
class AuthCredential:
    username: str
    password: str
    display_name: str
    role: str


def _parse_auth_users(value: str) -> dict[str, AuthCredential]:
    users: dict[str, AuthCredential] = {}
    if not value:
        return users
    for raw in value.split(","):
        item = raw.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) < 2:
            continue
        username = parts[0]
        password = parts[1]
        display_name = parts[2] if len(parts) >= 3 and parts[2] else username
        role = parts[3] if len(parts) >= 4 and parts[3] else "viewer"
        users[username] = AuthCredential(
            username=username,
            password=password,
            display_name=display_name,
            role=role,
        )
    return users


def has_auth_users() -> bool:
    return bool(_parse_auth_users(settings.auth_users))


def authenticate_credentials(username: str, password: str) -> AuthUser | None:
    users = _parse_auth_users(settings.auth_users)
    credential = users.get(username)
    if not credential:
        return None
    if not hmac.compare_digest(credential.password, password):
        return None
    return AuthUser(
        username=credential.username,
        display_name=credential.display_name,
        role=credential.role,
    )


def get_session_user(request: Request) -> AuthUser | None:
    if "session" not in request.scope:
        return None
    session_user = request.session.get("auth_user")
    if not session_user:
        return None
    return AuthUser(
        username=session_user.get("username", ""),
        display_name=session_user.get("display_name", ""),
        role=session_user.get("role", "viewer"),
    )


def set_session_user(request: Request, user: AuthUser) -> None:
    if not hasattr(request, "session"):
        return
    request.session["auth_user"] = {
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
    }


def clear_session_user(request: Request) -> None:
    if not hasattr(request, "session"):
        return
    request.session.pop("auth_user", None)


def ensure_db_user(db: Session, auth_user: AuthUser) -> User:
    db_user = (
        db.query(User)
        .filter(User.username == auth_user.username)
        .one_or_none()
    )
    if db_user:
        return db_user
    db_user = User(
        username=auth_user.username,
        display_name=auth_user.display_name,
        role=auth_user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
