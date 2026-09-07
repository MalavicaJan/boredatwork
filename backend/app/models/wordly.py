from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WordlyChallenge(Base):
    __tablename__ = "wordly_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)

    challenge_date: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False,
        index=True,
    )

    word: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
