from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sequence import SequenceChallenge
from app.models.user import User
from app.schemas.sequence import (
    SequenceAnswer,
    SequenceAnswerResponse,
    SequenceStateResponse,
)
from app.services.sequence import (
    ROUND_LENGTHS,
    TOTAL_ROUNDS,
    advance_progress,
    create_daily_challenge,
    finish_progress,
    get_or_create_progress,
    get_progress,
    round_digits,
)
from app.session import get_optional_current_user


router = APIRouter(
    prefix="/api/v1/sequence",
    tags=["sequence"],
)


def today() -> date:
    return datetime.now(timezone.utc).date()


def build_state(
    challenge: SequenceChallenge,
    round_number: int,
    completed: bool,
    score: int | None,
) -> SequenceStateResponse:
    return SequenceStateResponse(
        challenge_id=challenge.id,
        challenge_date=challenge.challenge_date,
        round=round_number,
        total_rounds=TOTAL_ROUNDS,
        digits=None if completed else round_digits(challenge, round_number),
        completed=completed,
        score=score,
    )


@router.get("/state", response_model=SequenceStateResponse)
def get_sequence_state(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    challenge = create_daily_challenge(db, today())

    # Anonymous players get a fresh run every time. Nothing is stored,
    # so there is nothing to resume.
    if not current_user:
        return build_state(challenge, 1, False, None)

    progress = get_progress(db, current_user.id, challenge.id)

    if not progress:
        return build_state(challenge, 1, False, None)

    return build_state(
        challenge,
        progress.current_round,
        progress.completed,
        progress.score,
    )


@router.get("/today", response_model=SequenceStateResponse)
def get_today_sequence(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    return get_sequence_state(current_user, db)


@router.post("/answer", response_model=SequenceAnswerResponse)
def submit_sequence_answer(
    answer: SequenceAnswer,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    challenge = create_daily_challenge(db, today())

    if answer.round not in ROUND_LENGTHS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid round",
        )

    progress = None

    if current_user:
        progress = get_or_create_progress(
            db,
            current_user.id,
            challenge.id,
        )

        if progress.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sequence already completed today",
            )

        # The server decides which round the player is on, not the client.
        if answer.round != progress.current_round:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Expected round {progress.current_round}",
            )

    expected_length = ROUND_LENGTHS[answer.round]
    submitted_answer = answer.answer.strip()

    if (
        len(submitted_answer) != expected_length
        or not submitted_answer.isdigit()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Answer must be exactly {expected_length} digits",
        )

    correct = submitted_answer == round_digits(challenge, answer.round)

    if not correct:
        score = answer.round - 1

        if progress:
            finish_progress(db, progress, score)

        return SequenceAnswerResponse(
            correct=False,
            round=answer.round,
            game_over=True,
            score=score,
        )

    if answer.round == TOTAL_ROUNDS:
        if progress:
            finish_progress(db, progress, TOTAL_ROUNDS)

        return SequenceAnswerResponse(
            correct=True,
            round=answer.round,
            game_over=True,
            score=TOTAL_ROUNDS,
        )

    next_round = answer.round + 1

    if progress:
        advance_progress(db, progress)

    return SequenceAnswerResponse(
        correct=True,
        round=answer.round,
        game_over=False,
        next_round=next_round,
        next_digits=round_digits(challenge, next_round),
    )
