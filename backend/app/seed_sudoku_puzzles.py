"""Fill the puzzle pool.

    python -m app.seed_sudoku_puzzles
    python -m app.seed_sudoku_puzzles --easy 100 --expert 20

Generation is slow at the hard end (an expert puzzle takes a couple of
seconds), which is exactly why puzzles are generated here and not inside
a request.
"""

import argparse
import time

from app.database import SessionLocal
from app.models.sudoku import SudokuPuzzle
from app.services.sudoku_generator import (
    DIFFICULTIES,
    count_givens,
    generate_puzzle,
)


DEFAULT_COUNTS = {
    "easy": 60,
    "medium": 60,
    "hard": 40,
    "expert": 20,
}


def seed(counts: dict[str, int]) -> None:
    db = SessionLocal()

    try:
        for difficulty in DIFFICULTIES:
            wanted = counts[difficulty]

            existing = (
                db.query(SudokuPuzzle)
                .filter(SudokuPuzzle.difficulty == difficulty)
                .count()
            )

            missing = wanted - existing

            if missing <= 0:
                print(f"{difficulty}: {existing} already there, skipping")
                continue

            print(f"{difficulty}: generating {missing}...")

            started = time.time()

            for number in range(missing):
                puzzle, solution = generate_puzzle(difficulty)

                already_stored = (
                    db.query(SudokuPuzzle)
                    .filter(SudokuPuzzle.puzzle == puzzle)
                    .first()
                )

                if already_stored:
                    continue

                db.add(
                    SudokuPuzzle(
                        difficulty=difficulty,
                        puzzle=puzzle,
                        solution=solution,
                    )
                )

                db.commit()

                print(
                    f"  {number + 1}/{missing}"
                    f" ({count_givens(puzzle)} givens)"
                )

            print(f"{difficulty}: done in {time.time() - started:.1f}s")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()

    for difficulty in DIFFICULTIES:
        parser.add_argument(
            f"--{difficulty}",
            type=int,
            default=DEFAULT_COUNTS[difficulty],
            help=f"target number of {difficulty} puzzles in the pool",
        )

    arguments = parser.parse_args()

    seed({
        difficulty: getattr(arguments, difficulty)
        for difficulty in DIFFICULTIES
    })


if __name__ == "__main__":
    main()
