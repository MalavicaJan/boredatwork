"""Sudoku puzzle generation.

Grids are 81-character strings read left to right, top to bottom.
A "0" marks an empty cell.

Generation is deliberately kept out of the request path: it is slow
enough (especially for expert) that puzzles are pre-generated into the
sudoku_puzzles table by seed_sudoku_puzzles.py.
"""

import random

SIZE = 9
BOX = 3
CELLS = SIZE * SIZE
EMPTY = "0"

# Target number of filled cells per difficulty. Fewer givens means a
# harder puzzle, though the two are only loosely related.
DIFFICULTY_GIVENS = {
    "easy": 45,
    "medium": 38,
    "hard": 31,
    "expert": 26,
}

DIFFICULTIES = tuple(DIFFICULTY_GIVENS)


def peers(index: int) -> set[int]:
    """Every cell that shares a row, column or box with this one."""
    row, column = divmod(index, SIZE)

    result = set()

    for offset in range(SIZE):
        result.add(row * SIZE + offset)
        result.add(offset * SIZE + column)

    box_row = (row // BOX) * BOX
    box_column = (column // BOX) * BOX

    for r in range(box_row, box_row + BOX):
        for c in range(box_column, box_column + BOX):
            result.add(r * SIZE + c)

    result.discard(index)

    return result


PEERS = [peers(index) for index in range(CELLS)]


def candidates(grid: list[str], index: int) -> list[str]:
    used = {grid[peer] for peer in PEERS[index]}

    return [
        digit
        for digit in "123456789"
        if digit not in used
    ]


def fill_grid(grid: list[str]) -> bool:
    """Fill every empty cell with a valid digit, choosing randomly."""
    try:
        index = grid.index(EMPTY)
    except ValueError:
        return True

    options = candidates(grid, index)
    random.shuffle(options)

    for digit in options:
        grid[index] = digit

        if fill_grid(grid):
            return True

        grid[index] = EMPTY

    return False


def count_solutions(grid: list[str], limit: int = 2) -> int:
    """Count solutions, stopping as soon as `limit` is reached.

    Only ever used to answer 'is this puzzle still unique?', so the
    default limit of 2 is all we need.
    """
    try:
        index = grid.index(EMPTY)
    except ValueError:
        return 1

    total = 0

    for digit in candidates(grid, index):
        grid[index] = digit
        total += count_solutions(grid, limit)
        grid[index] = EMPTY

        if total >= limit:
            break

    return total


def solve(puzzle: str) -> str | None:
    """Return the unique solution of a puzzle, or None if unsolvable."""
    grid = list(puzzle)

    if fill_grid(grid):
        return "".join(grid)

    return None


def generate_solution() -> str:
    grid = [EMPTY] * CELLS

    fill_grid(grid)

    return "".join(grid)


def carve_puzzle(solution: str, target_givens: int) -> str:
    """Remove cells from a solved grid while keeping exactly one solution."""
    grid = list(solution)

    order = list(range(CELLS))
    random.shuffle(order)

    givens = CELLS

    for index in order:
        if givens <= target_givens:
            break

        removed = grid[index]
        grid[index] = EMPTY

        if count_solutions(list(grid)) != 1:
            # Removing this cell would allow a second solution.
            grid[index] = removed
            continue

        givens -= 1

    return "".join(grid)


def generate_puzzle(difficulty: str) -> tuple[str, str]:
    """Return (puzzle, solution) for a difficulty."""
    if difficulty not in DIFFICULTY_GIVENS:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    solution = generate_solution()
    puzzle = carve_puzzle(solution, DIFFICULTY_GIVENS[difficulty])

    return puzzle, solution


def count_givens(puzzle: str) -> int:
    return sum(1 for cell in puzzle if cell != EMPTY)
