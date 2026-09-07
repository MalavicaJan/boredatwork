-- Wordly: store whether the game was won.
--
-- Numbered 006 rather than 003 on purpose: 003 was never applied here,
-- and there are already two files numbered 002. Taking the next free
-- number after the highest keeps ordering unambiguous.
--
-- A win on the sixth guess and a loss both score 6, so `won` cannot be
-- derived from the score. Without this column the app raises
-- TypeError: 'won' is an invalid keyword argument for GameResult.

BEGIN;

ALTER TABLE game_results
    ADD COLUMN IF NOT EXISTS won BOOLEAN NOT NULL DEFAULT false;

-- Best-effort backfill using the old (broken) rule. Sixth-guess wins in
-- existing data are indistinguishable from losses, so they stay losses.
UPDATE game_results
SET won = true
WHERE game = 'wordly'
  AND completed
  AND score < 6;

ALTER TABLE game_results
    ALTER COLUMN played_at TYPE timestamptz
    USING played_at AT TIME ZONE 'UTC';

-- Remove duplicates before the constraint can be added.
DELETE FROM game_results a
USING game_results b
WHERE a.id > b.id
  AND a.user_id = b.user_id
  AND a.challenge_id = b.challenge_id
  AND a.game = b.game;

ALTER TABLE game_results
    ADD CONSTRAINT uq_game_results_user_challenge_game
    UNIQUE (user_id, challenge_id, game);

COMMIT;
