from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SudokuPuzzle(Base):
    """A pre-generated puzzle and its unique solution.

    Sudoku has no daily challenge and no per-player state: the same pool
    of puzzles serves anonymous and logged-in players, without limit.
    The solution lives here and is never sent to the client.
    """

    __tablename__ = "sudoku_puzzles"

    id: Mapped[int] = mapped_column(primary_key=True)

    difficulty: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    # 81 characters, row by row. "0" is an empty cell.
    puzzle: Mapped[str] = mapped_column(
        String(81),
        nullable=False,
        unique=True,
    )

    solution: Mapped[str] = mapped_column(
        String(81),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
