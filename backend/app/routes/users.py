from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.security import hash_password,verify_password
from app.database import get_db, settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from fastapi.responses import JSONResponse
from app.models.session import UserSession
from app.models.game_result import GameResult
from app.schemas.streak import StreakResponse
from app.services.streak import get_streaks
from app.rate_limit import (
    client_ip,
    login_ip_limiter,
    login_user_limiter,
    register_ip_limiter,
)
from app.security import password_hasher
from app.session import create_session, get_current_user,  hash_session_token

# Verified against when the username doesn't exist, so a missing user
# costs the same time as a wrong password. Without this, response time
# tells an attacker which usernames are real.
DUMMY_HASH = password_hasher.hash("not-a-real-password")


def enforce(limiter, key: str, what: str) -> None:
    retry_after = limiter.check(key)

    if retry_after is None:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many {what}. Try again in {retry_after} seconds.",
        headers={"Retry-After": str(retry_after)},
    )

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


# NOTE: there was a GET "/" here returning every user in the database,
# unauthenticated. Removed — the site is public and nothing needs it.


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    enforce(register_ip_limiter, client_ip(request), "sign-ups from your network")

    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    new_user = User(
        username=user.username,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(
    user: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    address = client_ip(request)
    username_key = user.username.lower()

    enforce(login_ip_limiter, address, "login attempts from your network")
    enforce(login_user_limiter, username_key, "login attempts for this account")

    existing_user = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )

    # Always verify something, so the response takes the same time
    # whether or not the username exists.
    if existing_user:
        password_matches = verify_password(
            user.password,
            existing_user.password_hash,
        )
    else:
        verify_password(user.password, DUMMY_HASH)
        password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Succeeded, so don't hold the earlier failures against them.
    login_ip_limiter.reset(address)
    login_user_limiter.reset(username_key)

    new_session,raw_token = create_session(existing_user.id)

    db.add(new_session)
    db.commit()

    response = JSONResponse(
        content={
            "id": existing_user.id,
            "username": existing_user.username,
        }
    )

    response.set_cookie(
        key="session_id",
        value=raw_token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        max_age=30 * 24 * 60 * 60,
    )

    return response
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user



@router.post("/logout")
def logout_user(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if session_id:
        existing_session = (
            db.query(UserSession)
            .filter(UserSession.id == hash_session_token(session_id))
            .first()
        )

        if existing_session:
            db.delete(existing_session)
            db.commit()

    response = JSONResponse(
        content={"message": "Logged out successfully"}
    )

    response.delete_cookie(
        key="session_id",
    )

    return response


@router.get(
"/streak",
response_model=StreakResponse,
)
def get_user_streak(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return get_streaks(
            db,
            current_user.id,
        )


@router.get("/daily-progress")
def get_daily_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = (
        db.query(GameResult)
        .filter(
            GameResult.user_id == current_user.id,
            GameResult.completed.is_(True),
        )
        .all()
    )

    return [
        {
            "challenge_id": result.challenge_id,
            "game": result.game,
            "completed": result.completed,
        }
        for result in results
    ]