from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WordlyGuess(Base):
    __tablename__ = "wordly_guesses"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("wordly_challenges.id"),
        nullable=False,
        index=True,
    )

    guess: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    played_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )