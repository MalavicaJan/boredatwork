import random

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sudoku import SudokuPuzzle
from app.services.sudoku_generator import CELLS, EMPTY


def get_puzzle(db: Session, puzzle_id: int) -> SudokuPuzzle | None:
    return (
        db.query(SudokuPuzzle)
        .filter(SudokuPuzzle.id == puzzle_id)
        .first()
    )


def get_random_puzzle(
    db: Session,
    difficulty: str,
    exclude_id: int | None = None,
) -> SudokuPuzzle | None:
    """Pick a random puzzle of a difficulty, avoiding the one just played."""
    query = (
        db.query(SudokuPuzzle)
        .filter(SudokuPuzzle.difficulty == difficulty)
    )

    if exclude_id is not None:
        candidate = query.filter(SudokuPuzzle.id != exclude_id).order_by(
            func.random()
        ).first()

        if candidate:
            return candidate

        # Pool of one: better to repeat than to hand back nothing.

    return query.order_by(func.random()).first()


def is_valid_grid_string(grid: str) -> bool:
    return len(grid) == CELLS and grid.isdigit()


def respects_givens(puzzle: SudokuPuzzle, grid: str) -> bool:
    return all(
        grid[index] == given
        for index, given in enumerate(puzzle.puzzle)
        if given != EMPTY
    )


def incorrect_cells(puzzle: SudokuPuzzle, grid: str) -> list[int]:
    """Indexes of filled cells that don't match the solution."""
    return [
        index
        for index in range(CELLS)
        if grid[index] != EMPTY and grid[index] != puzzle.solution[index]
    ]


def is_complete(grid: str) -> bool:
    return EMPTY not in grid


def next_hint(
    puzzle: SudokuPuzzle,
    grid: str,
    preferred_index: int | None = None,
) -> tuple[int, str] | None:
    """One correct cell the player hasn't got right yet.

    Covers empty cells and wrong ones, so a stuck player always gets
    something useful back. A preferred index wins when it still needs
    solving; otherwise a random unsolved cell is chosen, because the
    player can't tell from the outside whether the cell they picked was
    already correct.
    """
    unsolved = [
        index
        for index in range(CELLS)
        if grid[index] != puzzle.solution[index]
    ]

    if not unsolved:
        return None

    if preferred_index is not None and preferred_index in unsolved:
        return preferred_index, puzzle.solution[preferred_index]

    index = random.choice(unsolved)

    return index, puzzle.solution[index]
