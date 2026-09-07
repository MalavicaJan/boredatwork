from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.game_result import GameResult
from app.models.sequence_result import SequenceResult


def get_completed_dates(
    db: Session,
    user_id: int,
) -> set[date]:
    game_results = (
        db.query(GameResult.played_at)
        .filter(
            GameResult.user_id == user_id,
            GameResult.completed.is_(True),
        )
        .all()
    )

    sequence_results = (
        db.query(SequenceResult.played_at)
        .filter(
            SequenceResult.user_id == user_id,
            SequenceResult.completed.is_(True),
        )
        .all()
    )

    completed_dates = {
        result.played_at.date()
        for result in game_results
    }

    completed_dates.update(
        result.played_at.date()
        for result in sequence_results
    )

    return completed_dates


def calculate_current_streak(
    completed_dates: set[date],
    today: date,
) -> int:
    if today not in completed_dates:
        return 0

    streak = 0
    current_date = today

    while current_date in completed_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def calculate_longest_streak(
    completed_dates: set[date],
) -> int:
    if not completed_dates:
        return 0

    longest = 0
    current = 0
    previous_date = None

    for completed_date in sorted(completed_dates):
        if (
            previous_date is not None
            and completed_date == previous_date + timedelta(days=1)
        ):
            current += 1
        else:
            current = 1

        longest = max(longest, current)
        previous_date = completed_date

    return longest


def get_streaks(
    db: Session,
    user_id: int,
    today: date | None = None,
) -> dict[str, int]:
    if today is None:
        today = datetime.now(timezone.utc).date()
    completed_dates = get_completed_dates(
        db,
        user_id,
    )

    return {
        "current_streak": calculate_current_streak(
            completed_dates,
            today,
        ),
        "longest_streak": calculate_longest_streak(
            completed_dates,
        ),
    }