BEGIN;

ALTER TABLE sequence_results
    ADD COLUMN IF NOT EXISTS current_round INTEGER NOT NULL DEFAULT 1;

ALTER TABLE sequence_results
    ALTER COLUMN score SET DEFAULT 0,
    ALTER COLUMN completed SET DEFAULT false;

-- Every pre-existing row is a finished run.
UPDATE sequence_results
SET
    current_round = 6,
    completed = true;

ALTER TABLE sequence_results
    ALTER COLUMN played_at TYPE timestamptz
    USING played_at AT TIME ZONE 'UTC';

-- One run per user per challenge, enforced by the database.
DELETE FROM sequence_results a
USING sequence_results b
WHERE a.id > b.id
  AND a.user_id = b.user_id
  AND a.challenge_id = b.challenge_id;

ALTER TABLE sequence_results
    ADD CONSTRAINT uq_sequence_results_user_challenge
    UNIQUE (user_id, challenge_id);

COMMIT;