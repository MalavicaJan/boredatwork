from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.blackout import (
    BlackoutGuessRequest,
    BlackoutGuessResponse,
    BlackoutRevealRequest,
    BlackoutRevealResponse,
    BlackoutStateResponse,
)
from app.services.blackout import (
    create_daily_challenge,
    find_hits,
    get_article,
    redact,
    title_word_count,
    tokenize,
)


router = APIRouter(
    prefix="/api/v1/blackout",
    tags=["blackout"],
)


def today() -> date:
    return datetime.now(timezone.utc).date()


def load_today(db: Session):
    challenge = create_daily_challenge(db, today())

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No articles available yet",
        )

    article = get_article(db, challenge.article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Today's article is missing",
        )

    return challenge, article


def load_challenge(db: Session, challenge_id: int):
    """Only today's challenge is playable: accepting any id would let
    anyone read back every past article, and future ones don't exist."""
    challenge, article = load_today(db)

    if challenge.id != challenge_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That challenge is not today's",
        )

    return challenge, article


@router.get("/today", response_model=BlackoutStateResponse)
def get_today_blackout(db: Session = Depends(get_db)):
    challenge, article = load_today(db)

    return BlackoutStateResponse(
        challenge_id=challenge.id,
        challenge_date=challenge.challenge_date,
        title_tokens=redact(article.title),
        body_tokens=redact(article.lead),
        title_word_count=title_word_count(article.title),
    )


@router.post("/guess", response_model=BlackoutGuessResponse)
def submit_blackout_guess(
    submission: BlackoutGuessRequest,
    db: Session = Depends(get_db),
):
    _, article = load_challenge(db, submission.challenge_id)

    guess = submission.guess.strip().lower()

    if not guess or not guess.replace("'", "").isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guess a single word",
        )

    title_hits = find_hits(article.title, guess)
    body_hits = find_hits(article.lead, guess)

    return BlackoutGuessResponse(
        guess=guess,
        title_hits=title_hits,
        body_hits=body_hits,
        count=len(title_hits) + len(body_hits),
    )


@router.post("/reveal", response_model=BlackoutRevealResponse)
def reveal_blackout(
    submission: BlackoutRevealRequest,
    db: Session = Depends(get_db),
):
    """Give up, or confirm a win. Nothing is stored, so the server can't
    tell the two apart and doesn't try."""
    _, article = load_challenge(db, submission.challenge_id)

    return BlackoutRevealResponse(
        title=article.title,
        # Same token positions as the redacted version the client is
        # holding, so it can swap them in place.
        title_tokens=[
            {"kind": "fixed", "text": token}
            for token in tokenize(article.title)
        ],
        body_tokens=[
            {"kind": "fixed", "text": token}
            for token in tokenize(article.lead)
        ],
        source_url=article.source_url,
    )
