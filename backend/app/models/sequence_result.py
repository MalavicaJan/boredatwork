from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SequenceResult(Base):
    """One row per user per daily Sequence challenge.

    The row is created when the user answers their first round and is
    updated as they progress. `completed` flips to True when the run
    ends, either by clearing the last round or by getting one wrong.
    """

    __tablename__ = "sequence_results"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "challenge_id",
            name="uq_sequence_results_user_challenge",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("sequence_challenges.id"),
        nullable=False,
        index=True,
    )

    # The round the user is allowed to answer next (1-6).
    current_round: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    # Number of rounds cleared so far.
    score: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    completed: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
