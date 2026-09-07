from app.services.sudoku_generator import (
    CELLS,
    DIFFICULTY_GIVENS,
    EMPTY,
    carve_puzzle,
    count_givens,
    count_solutions,
    generate_solution,
    solve,
)


def rows(grid: str):
    return [grid[index:index + 9] for index in range(0, CELLS, 9)]


def columns(grid: str):
    return ["".join(grid[row * 9 + col] for row in range(9)) for col in range(9)]


def boxes(grid: str):
    result = []

    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            result.append(
                "".join(
                    grid[(box_row + r) * 9 + box_col + c]
                    for r in range(3)
                    for c in range(3)
                )
            )

    return result


def test_generated_solution_is_a_valid_grid():
    solution = generate_solution()

    assert len(solution) == CELLS
    assert EMPTY not in solution

    for group in rows(solution) + columns(solution) + boxes(solution):
        assert sorted(group) == list("123456789")


def test_generated_solutions_differ():
    assert generate_solution() != generate_solution()


def test_carved_puzzle_keeps_the_givens_of_the_solution():
    solution = generate_solution()
    puzzle = carve_puzzle(solution, DIFFICULTY_GIVENS["easy"])

    for index, cell in enumerate(puzzle):
        if cell != EMPTY:
            assert cell == solution[index]


def test_carved_puzzle_hits_the_target_number_of_givens():
    solution = generate_solution()
    puzzle = carve_puzzle(solution, DIFFICULTY_GIVENS["easy"])

    # Carving stops early when no further cell can be removed while
    # keeping the puzzle unique, so the target is a floor, not an exact.
    assert count_givens(puzzle) >= DIFFICULTY_GIVENS["easy"]
    assert count_givens(puzzle) < CELLS


def test_carved_puzzle_has_exactly_one_solution():
    solution = generate_solution()
    puzzle = carve_puzzle(solution, DIFFICULTY_GIVENS["medium"])

    assert count_solutions(list(puzzle)) == 1


def test_solving_a_carved_puzzle_returns_the_original_solution():
    solution = generate_solution()
    puzzle = carve_puzzle(solution, DIFFICULTY_GIVENS["medium"])

    assert solve(puzzle) == solution


def test_harder_difficulties_have_fewer_givens():
    values = list(DIFFICULTY_GIVENS.values())

    assert values == sorted(values, reverse=True)
