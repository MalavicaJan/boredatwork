-- Sudoku: a pool of pre-generated puzzles.
-- No per-player table: Sudoku stores nothing about who played or how
-- they did, for anonymous and logged-in players alike.

BEGIN;

CREATE TABLE IF NOT EXISTS sudoku_puzzles (
    id          SERIAL PRIMARY KEY,
    difficulty  VARCHAR(10) NOT NULL,
    puzzle      VARCHAR(81) NOT NULL UNIQUE,
    solution    VARCHAR(81) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_sudoku_puzzles_difficulty
    ON sudoku_puzzles (difficulty);

COMMIT;

-- Then fill the pool:
--   python -m app.seed_sudoku_puzzles
