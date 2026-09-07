-- Wordly: split the word table into a daily pool and a practice pool.
--
-- Practice mode evaluates guesses server-side without limit, so anyone
-- can learn a practice word by hammering the endpoint. Sharing one pool
-- would therefore leak the set the daily answer is drawn from.

BEGIN;

ALTER TABLE wordly_words
    ADD COLUMN IF NOT EXISTS pool VARCHAR(10) NOT NULL DEFAULT 'daily';

CREATE INDEX IF NOT EXISTS ix_wordly_words_pool
    ON wordly_words (pool);

COMMIT;

-- Existing words stay in the daily pool. Fill the practice pool with:
--   python -m app.seed_wordly_practice_words
