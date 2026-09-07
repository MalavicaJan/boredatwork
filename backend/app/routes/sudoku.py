from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sudoku import (
    Difficulty,
    SudokuCheckResponse,
    SudokuGrid,
    SudokuHintRequest,
    SudokuHintResponse,
    SudokuPuzzleResponse,
)
from app.services.sudoku import (
    get_puzzle,
    get_random_puzzle,
    incorrect_cells,
    is_complete,
    is_valid_grid_string,
    next_hint,
    respects_givens,
)
from app.services.sudoku_generator import count_givens


router = APIRouter(
    prefix="/api/v1/sudoku",
    tags=["sudoku"],
)


def to_response(puzzle) -> SudokuPuzzleResponse:
    return SudokuPuzzleResponse(
        id=puzzle.id,
        difficulty=puzzle.difficulty,
        puzzle=puzzle.puzzle,
        givens=count_givens(puzzle.puzzle),
    )


def load_puzzle_or_404(db: Session, puzzle_id: int):
    puzzle = get_puzzle(db, puzzle_id)

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Puzzle not found",
        )

    return puzzle


def validate_submission(puzzle, grid: str) -> None:
    if not is_valid_grid_string(grid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grid must be 81 digits",
        )

    if not respects_givens(puzzle, grid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Given cells cannot be changed",
        )


@router.get("/new", response_model=SudokuPuzzleResponse)
def get_new_puzzle(
    difficulty: Difficulty = Query(default=Difficulty.easy),
    exclude: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """A random puzzle. No limits, no account needed."""
    puzzle = get_random_puzzle(db, difficulty.value, exclude)

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No {difficulty.value} puzzles available yet",
        )

    return to_response(puzzle)


@router.get("/{puzzle_id}", response_model=SudokuPuzzleResponse)
def get_puzzle_by_id(
    puzzle_id: int,
    db: Session = Depends(get_db),
):
    """Reload a puzzle the player already has. Nothing is stored about
    their progress, so the client keeps that itself."""
    return to_response(load_puzzle_or_404(db, puzzle_id))


@router.post("/check", response_model=SudokuCheckResponse)
def check_grid(
    submission: SudokuGrid,
    db: Session = Depends(get_db),
):
    puzzle = load_puzzle_or_404(db, submission.puzzle_id)

    validate_submission(puzzle, submission.grid)

    wrong = incorrect_cells(puzzle, submission.grid)
    complete = is_complete(submission.grid)

    return SudokuCheckResponse(
        complete=complete,
        solved=complete and not wrong,
        incorrect_cells=wrong,
    )


@router.post("/hint", response_model=SudokuHintResponse)
def get_hint(
    submission: SudokuHintRequest,
    db: Session = Depends(get_db),
):
    puzzle = load_puzzle_or_404(db, submission.puzzle_id)

    validate_submission(puzzle, submission.grid)

    hint = next_hint(puzzle, submission.grid, submission.index)

    if not hint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nothing left to reveal",
        )

    index, value = hint

    remaining = sum(
        1
        for cell in range(81)
        if submission.grid[cell] != puzzle.solution[cell]
    ) - 1

    return SudokuHintResponse(
        index=index,
        value=value,
        remaining=remaining,
    )
