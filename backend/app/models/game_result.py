from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GameResult(Base):
    __tablename__ = "game_results"

    __table_args__ = (
        # One result per player per challenge per game, enforced by the
        # database rather than by remembering to check first.
        UniqueConstraint(
            "user_id",
            "challenge_id",
            "game",
            name="uq_game_results_user_challenge_game",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # NOTE: this points at wordly_challenges, so despite the generic
    # `game` column the table can only hold Wordly results. Sequence has
    # its own table for the same reason. Worth unifying later.
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("wordly_challenges.id"),
        nullable=False,
        index=True,
    )

    game: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Guesses used. A win on the last guess and a loss both score 6,
    # which is why `won` is stored rather than derived from the score.
    score: Mapped[int] = mapped_column(
        nullable=False,
    )

    won: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    completed: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
