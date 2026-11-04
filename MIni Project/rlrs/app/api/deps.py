"""Shared request dependencies."""
from __future__ import annotations

from datetime import datetime
from typing import Iterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import Role, User


def get_session(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_now() -> datetime:
    """Current time (naive UTC). Tests override this to use a fixed clock."""
    return utcnow()


def get_mailer(request: Request):
    return request.app.state.mailer


def current_user(x_user_id: int | None = Header(default=None),
                 session: Session = Depends(get_session)) -> User:
    """TEMPORARY identity: the X-User-Id header.

    Real sign-in and sessions are RLRS-2 (Deepesh). When that lands, replace the body of this
    function only; every endpoint already depends on it, so nothing else changes.
    """
    if x_user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required (X-User-Id header).")
    user = session.get(User, x_user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user.")
    return user


def require_roles(*roles: Role):
    allowed = {r.value for r in roles}

    def _check(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action.")
        return user

    return _check


staff_only = require_roles(Role.LAB_INCHARGE, Role.ADMIN)
