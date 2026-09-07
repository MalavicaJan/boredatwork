import pytest

from app.models.sudoku import SudokuPuzzle
from app.services.sudoku_generator import (
    DIFFICULTY_GIVENS,
    carve_puzzle,
    count_givens,
    generate_solution,
)


@pytest.fixture
def puzzle(db_session):
    solution = generate_solution()

    stored = SudokuPuzzle(
        difficulty="easy",
        puzzle=carve_puzzle(solution, DIFFICULTY_GIVENS["easy"]),
        solution=solution,
    )

    db_session.add(stored)
    db_session.commit()
    db_session.refresh(stored)

    return stored


def test_new_puzzle_returns_a_playable_grid(client, puzzle):
    response = client.get("/api/v1/sudoku/new?difficulty=easy")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == puzzle.id
    assert data["difficulty"] == "easy"
    assert len(data["puzzle"]) == 81
    assert data["givens"] == count_givens(puzzle.puzzle)


def test_new_puzzle_never_returns_the_solution(client, puzzle):
    body = client.get("/api/v1/sudoku/new?difficulty=easy").text

    assert puzzle.solution not in body

    body = client.get(f"/api/v1/sudoku/{puzzle.id}").text

    assert puzzle.solution not in body


def test_anonymous_players_have_no_limit(client, puzzle):
    for _ in range(10):
        assert client.get("/api/v1/sudoku/new?difficulty=easy").status_code == 200


def test_unknown_difficulty_is_rejected(client, puzzle):
    response = client.get("/api/v1/sudoku/new?difficulty=impossible")

    assert response.status_code == 422


def test_empty_pool_returns_a_clear_error(client, puzzle):
    response = client.get("/api/v1/sudoku/new?difficulty=expert")

    assert response.status_code == 503
    assert "expert" in response.json()["detail"]


def test_unknown_puzzle_returns_404(client, puzzle):
    response = client.get("/api/v1/sudoku/999999")

    assert response.status_code == 404


def test_check_reports_incorrect_cells(client, puzzle):
    grid = list(puzzle.solution)

    empty_index = puzzle.puzzle.index("0")

    wrong = "1" if puzzle.solution[empty_index] != "1" else "2"
    grid[empty_index] = wrong

    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": "".join(grid)},
    )

    assert response.status_code == 200
    assert response.json() == {
        "complete": True,
        "solved": False,
        "incorrect_cells": [empty_index],
    }


def test_check_accepts_the_solution(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": puzzle.solution},
    )

    assert response.status_code == 200
    assert response.json() == {
        "complete": True,
        "solved": True,
        "incorrect_cells": [],
    }


def test_check_on_a_partial_grid_is_not_solved(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": puzzle.puzzle},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["complete"] is False
    assert data["solved"] is False
    assert data["incorrect_cells"] == []


def test_changing_a_given_is_rejected(client, puzzle):
    grid = list(puzzle.puzzle)

    given_index = next(
        index
        for index, cell in enumerate(puzzle.puzzle)
        if cell != "0"
    )

    grid[given_index] = "1" if puzzle.puzzle[given_index] != "1" else "2"

    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": "".join(grid)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Given cells cannot be changed"


def test_non_digit_grid_is_rejected(client, puzzle):
    grid = "x" + puzzle.puzzle[1:]

    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": grid},
    )

    assert response.status_code == 400


def test_wrong_length_grid_is_rejected(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/check",
        json={"puzzle_id": puzzle.id, "grid": "123"},
    )

    assert response.status_code == 422


def test_hint_fills_one_correct_cell(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/hint",
        json={"puzzle_id": puzzle.id, "grid": puzzle.puzzle},
    )

    assert response.status_code == 200

    data = response.json()

    assert puzzle.puzzle[data["index"]] == "0"
    assert data["value"] == puzzle.solution[data["index"]]
    assert data["remaining"] == puzzle.puzzle.count("0") - 1


def test_hint_on_a_solved_grid_is_rejected(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/hint",
        json={"puzzle_id": puzzle.id, "grid": puzzle.solution},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nothing left to reveal"


def test_exclude_avoids_the_puzzle_just_played(client, db_session, puzzle):
    solution = generate_solution()

    other = SudokuPuzzle(
        difficulty="easy",
        puzzle=carve_puzzle(solution, DIFFICULTY_GIVENS["easy"]),
        solution=solution,
    )

    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    for _ in range(8):
        response = client.get(
            f"/api/v1/sudoku/new?difficulty=easy&exclude={puzzle.id}"
        )

        assert response.json()["id"] == other.id


def test_exclude_falls_back_when_the_pool_has_one_puzzle(client, puzzle):
    response = client.get(
        f"/api/v1/sudoku/new?difficulty=easy&exclude={puzzle.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == puzzle.id


def test_logged_in_players_play_the_same_unlimited_game(client, puzzle):
    """Sudoku has no per-user state: logging in changes nothing, and no
    limit applies to either kind of player."""
    client.post(
        "/api/v1/users/",
        json={"username": "player", "password": "test-password"},
    )

    assert client.post(
        "/api/v1/users/login",
        json={"username": "player", "password": "test-password"},
    ).status_code == 200

    for _ in range(10):
        new_puzzle = client.get("/api/v1/sudoku/new?difficulty=easy")

        assert new_puzzle.status_code == 200

        assert client.post(
            "/api/v1/sudoku/check",
            json={"puzzle_id": puzzle.id, "grid": puzzle.solution},
        ).json()["solved"] is True


def test_hint_reveals_the_requested_cell(client, puzzle):
    target = puzzle.puzzle.index("0")

    response = client.post(
        "/api/v1/sudoku/hint",
        json={"puzzle_id": puzzle.id, "grid": puzzle.puzzle, "index": target},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["index"] == target
    assert data["value"] == puzzle.solution[target]


def test_hint_falls_back_when_the_requested_cell_is_already_right(
    client,
    puzzle,
):
    """The client can't tell whether the cell the player picked is
    already correct, so asking for one is a preference, not a demand."""
    given = next(
        index
        for index, cell in enumerate(puzzle.puzzle)
        if cell != "0"
    )

    response = client.post(
        "/api/v1/sudoku/hint",
        json={"puzzle_id": puzzle.id, "grid": puzzle.puzzle, "index": given},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["index"] != given
    assert puzzle.puzzle[data["index"]] == "0"
    assert data["value"] == puzzle.solution[data["index"]]


def test_hint_index_out_of_range_is_rejected(client, puzzle):
    response = client.post(
        "/api/v1/sudoku/hint",
        json={"puzzle_id": puzzle.id, "grid": puzzle.puzzle, "index": 81},
    )

    assert response.status_code == 422
