from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SequenceChallenge(Base):
    __tablename__ = "sequence_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_date: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False,
        index=True,
    )
    sequence: Mapped[str] = mapped_column(String(100), nullable=False)