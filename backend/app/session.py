import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models.session import UserSession
from app.models.user import User


SESSION_DURATION_DAYS = 30


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: int) -> tuple[UserSession, str]:
    raw_token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=SESSION_DURATION_DAYS)
    )

    session = UserSession(
        id=hash_session_token(raw_token),
        user_id=user_id,
        expires_at=expires_at,
    )

    return session, raw_token


def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> User:

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session = (
        db.query(UserSession)
        .filter(UserSession.id == hash_session_token(session_id))
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    now = datetime.now(timezone.utc)

    if session.expires_at <= now:
        db.delete(session)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    user = (
        db.query(User)
        .filter(User.id == session.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_optional_current_user(
    session_id: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> User | None:

    if not session_id:
        return None

    session = (
        db.query(UserSession)
        .filter(UserSession.id == hash_session_token(session_id))
        .first()
    )

    if not session:
        return None

    now = datetime.now(timezone.utc)

    if session.expires_at <= now:
        db.delete(session)
        db.commit()
        return None

    user = (
        db.query(User)
        .filter(User.id == session.user_id)
        .first()
    )

    return user