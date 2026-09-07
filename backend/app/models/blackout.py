from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BlackoutArticle(Base):
    """A Wikipedia lead section to be uncovered word by word.

    The text is stored here and never sent to the client in full: the
    API only ever returns it redacted, or the positions of a word the
    player has actually guessed.

    Wikipedia text is CC BY-SA, so source_url is not optional — it is
    the attribution the licence requires.
    """

    __tablename__ = "blackout_articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    lead: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )


class BlackoutChallenge(Base):
    """Which article is today's."""

    __tablename__ = "blackout_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)

    challenge_date: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False,
        index=True,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey("blackout_articles.id"),
        nullable=False,
        index=True,
    )
