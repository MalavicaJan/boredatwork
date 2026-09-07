from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


DAILY = "daily"
PRACTICE = "practice"


class WordlyWord(Base):
    """A five-letter word, in one of two pools.

    The pools are kept apart on purpose. Practice mode evaluates guesses
    server-side without limit, so its endpoints are an oracle: given
    enough requests you can learn any practice word. If the daily
    challenge drew from the same rows, that would hand out the set the
    daily answer comes from.
    """

    __tablename__ = "wordly_words"

    id: Mapped[int] = mapped_column(primary_key=True)

    word: Mapped[str] = mapped_column(
        String(5),
        unique=True,
        nullable=False,
        index=True,
    )

    pool: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=DAILY,
        index=True,
    )
