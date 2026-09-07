-- Blackout: a daily Wikipedia lead section, uncovered word by word.
--
-- Article text is stored server-side and only ever leaves redacted.
-- source_url is the CC BY-SA attribution and is shown to the player
-- once the puzzle ends (it contains the title, so not before).

BEGIN;

CREATE TABLE IF NOT EXISTS blackout_articles (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL UNIQUE,
    lead        TEXT NOT NULL,
    source_url  VARCHAR(500) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS blackout_challenges (
    id              SERIAL PRIMARY KEY,
    challenge_date  DATE NOT NULL UNIQUE,
    article_id      INTEGER NOT NULL REFERENCES blackout_articles (id)
);

CREATE INDEX IF NOT EXISTS ix_blackout_challenges_challenge_date
    ON blackout_challenges (challenge_date);

CREATE INDEX IF NOT EXISTS ix_blackout_challenges_article_id
    ON blackout_challenges (article_id);

COMMIT;

-- Then fill the pool:
--   python -m app.seed_blackout_articles
