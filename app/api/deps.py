from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request, status
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import ensure_db_user, get_session_user
from app.db.models import User
from app.db.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    auth_user = getattr(request.state, "auth_user", None) or get_session_user(request)
    if auth_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return ensure_db_user(db, auth_user)
