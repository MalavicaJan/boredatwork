from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class SudokuPuzzleResponse(BaseModel):
    id: int
    difficulty: Difficulty
    # 81 characters, "0" for an empty cell. Never the solution.
    puzzle: str
    givens: int


class SudokuGrid(BaseModel):
    puzzle_id: int
    grid: str = Field(min_length=81, max_length=81)


class SudokuHintRequest(SudokuGrid):
    # Which cell to reveal. Falls back to a random unsolved cell when
    # omitted or when the chosen cell is already correct.
    index: int | None = Field(default=None, ge=0, le=80)


class SudokuCheckResponse(BaseModel):
    complete: bool
    solved: bool
    incorrect_cells: list[int]


class SudokuHintResponse(BaseModel):
    index: int
    value: str
    remaining: int
