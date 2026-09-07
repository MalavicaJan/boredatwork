import random
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.sequence import SequenceChallenge
from app.models.sequence_result import SequenceResult


# Digits shown per round. The daily sequence is generated once and each
# round reveals a longer prefix of it.
ROUND_LENGTHS = {
    1: 3,
    2: 4,
    3: 5,
    4: 6,
    5: 7,
    6: 8,
}

TOTAL_ROUNDS = len(ROUND_LENGTHS)
MAX_SCORE = TOTAL_ROUNDS
SEQUENCE_LENGTH = 20


def generate_sequence() -> str:
    return "".join(
        str(random.randint(0, 9))
        for _ in range(SEQUENCE_LENGTH)
    )


def get_daily_challenge(
    db: Session,
    challenge_date: date,
) -> SequenceChallenge | None:
    return (
        db.query(SequenceChallenge)
        .filter(SequenceChallenge.challenge_date == challenge_date)
        .first()
    )


def create_daily_challenge(
    db: Session,
    challenge_date: date,
) -> SequenceChallenge:
    existing_challenge = get_daily_challenge(db, challenge_date)

    if existing_challenge:
        return existing_challenge

    challenge = SequenceChallenge(
        challenge_date=challenge_date,
        sequence=generate_sequence(),
    )

    db.add(challenge)

    try:
        db.commit()
    except IntegrityError:
        # Another request created today's challenge first.
        db.rollback()

        existing_challenge = get_daily_challenge(db, challenge_date)

        if existing_challenge is None:
            raise

        return existing_challenge

    db.refresh(challenge)

    return challenge


def round_digits(
    challenge: SequenceChallenge,
    round_number: int,
) -> str:
    """The digits the player is shown (and must repeat) for a round."""
    return challenge.sequence[:ROUND_LENGTHS[round_number]]


def get_progress(
    db: Session,
    user_id: int,
    challenge_id: int,
) -> SequenceResult | None:
    return (
        db.query(SequenceResult)
        .filter(
            SequenceResult.user_id == user_id,
            SequenceResult.challenge_id == challenge_id,
        )
        .first()
    )


def get_or_create_progress(
    db: Session,
    user_id: int,
    challenge_id: int,
) -> SequenceResult:
    progress = get_progress(db, user_id, challenge_id)

    if progress:
        return progress

    progress = SequenceResult(
        user_id=user_id,
        challenge_id=challenge_id,
        current_round=1,
        score=0,
        completed=False,
    )

    db.add(progress)

    try:
        db.commit()
    except IntegrityError:
        # Two concurrent requests started the same run.
        db.rollback()

        progress = get_progress(db, user_id, challenge_id)

        if progress is None:
            raise

        return progress

    db.refresh(progress)

    return progress


def advance_progress(
    db: Session,
    progress: SequenceResult,
) -> SequenceResult:
    """Record a cleared round and move the player to the next one."""
    progress.score = progress.current_round
    progress.current_round += 1

    db.commit()
    db.refresh(progress)

    return progress


def finish_progress(
    db: Session,
    progress: SequenceResult,
    score: int,
) -> SequenceResult:
    """End the run and freeze the score."""
    progress.score = score
    progress.completed = True
    progress.played_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(progress)

    return progress
